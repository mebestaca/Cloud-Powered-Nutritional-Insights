"""
API layer for the Nutritional Insights Function App.

Every endpoint returns the same envelope the Next.js frontend expects
(see frontend/lib/api.ts):

    { "metadata": {...}, "filters": {...}, ...endpoint data }

The dataset is downloaded from Blob Storage once per worker and cached in
memory, so only the first request (or one with refresh=true) pays for the
download. Every request still reports its own execution time.
"""

import threading
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from data_source import load_dataset
from analysis import clean_data, generate_clusters

API_VERSION = "2.0.0"

# Cache lifetime. After this the next request re-downloads the blob.
CACHE_TTL_SECONDS = 15 * 60

# Keeps the scatter payload small enough for a quick chart render.
SCATTER_MAX_POINTS = 1500
CLUSTER_MAX_POINTS = 1500
PIE_MAX_SLICES = 8

SORTABLE = {
    "recipe": "recipe",
    "diet": "diet",
    "cuisine": "cuisine",
    "protein": "protein",
    "carbs": "carbs",
    "fat": "fat",
}

_cache = {"df": None, "source": None, "cleaning": None, "loaded_at": None, "loaded_ts": 0.0}
_cache_lock = threading.Lock()


# --------------------------------------------------------------------------
# Dataset loading and cleaning
# --------------------------------------------------------------------------

def _prepare(raw: pd.DataFrame):
    """Clean the raw CSV and record what cleaning did."""

    rows_in = int(len(raw))
    df = raw.copy()

    no_diet = df["Diet_type"].isna() | (df["Diet_type"].astype(str).str.strip() == "")
    df = df[~no_diet]

    numeric = ["Protein(g)", "Carbs(g)", "Fat(g)"]
    missing_before = int(
        df[numeric].apply(pd.to_numeric, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .isna().sum().sum()
    )

    df = clean_data(df)

    before_dupes = len(df)
    df = df.drop_duplicates(subset=["Recipe_name", "Diet_type", "Cuisine_type", *numeric])
    duplicates = before_dupes - len(df)

    # Short lowercase column names for the JSON output.
    df = pd.DataFrame({
        "recipe": df["Recipe_name"].fillna("Unknown").astype(str).str.strip(),
        "diet": df["Diet_type"].str.lower(),
        "cuisine": df["Cuisine_type"].str.lower(),
        "protein": df["Protein(g)"].astype(float),
        "carbs": df["Carbs(g)"].astype(float),
        "fat": df["Fat(g)"].astype(float),
    }).reset_index(drop=True)

    cleaning = {
        "rowsIn": rows_in,
        "rowsOut": int(len(df)),
        "rowsWithoutDietDropped": int(no_diet.sum()),
        "missingValuesFilled": missing_before,
        "duplicatesRemoved": int(duplicates),
    }
    return df, cleaning


def _get_dataset(refresh: bool = False):
    """Return (df, source, cleaning, loaded_at, data_load_ms, cache_hit)."""

    with _cache_lock:
        fresh = (
            _cache["df"] is not None
            and time.time() - _cache["loaded_ts"] < CACHE_TTL_SECONDS
        )
        if fresh and not refresh:
            return _cache["df"], _cache["source"], _cache["cleaning"], _cache["loaded_at"], 0.0, True

        started = time.perf_counter()
        raw, source = load_dataset()
        df, cleaning = _prepare(raw)
        load_ms = (time.perf_counter() - started) * 1000

        _cache.update(
            df=df,
            source=source,
            cleaning=cleaning,
            loaded_at=_now_iso(),
            loaded_ts=time.time(),
        )
        return df, source, cleaning, _cache["loaded_at"], load_ms, False


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _data_source_info(source: dict) -> dict:
    info = {"type": source.get("type") or source.get("source", "azure-blob")}
    for key in ("account", "container", "blob", "path", "sizeBytes", "lastModified"):
        if key in source:
            info[key] = source[key]
    return info


# --------------------------------------------------------------------------
# Filtering and the shared response envelope
# --------------------------------------------------------------------------

def _apply_filters(df: pd.DataFrame, diet: str, search: str) -> pd.DataFrame:
    diet = (diet or "all").strip().lower()
    search = (search or "").strip().lower()

    if diet != "all":
        df = df[df["diet"] == diet]

    if search:
        df = df[
            df["recipe"].str.lower().str.contains(search, regex=False, na=False)
            | df["diet"].str.contains(search, regex=False, na=False)
            | df["cuisine"].str.contains(search, regex=False, na=False)
        ]

    return df


def _run(diet: str, search: str, refresh: bool, compute):
    """Load data, filter, call compute(filtered_df, full_df), wrap in the envelope."""

    started = time.perf_counter()
    df, source, cleaning, loaded_at, load_ms, cache_hit = _get_dataset(refresh)

    diet = (diet or "all").strip().lower() or "all"
    search = (search or "").strip()

    compute_started = time.perf_counter()
    filtered = _apply_filters(df, diet, search)
    body = compute(filtered, df)
    compute_ms = (time.perf_counter() - compute_started) * 1000

    return {
        "success": True,
        "metadata": {
            "executionTimeMs": round((time.perf_counter() - started) * 1000, 1),
            "dataLoadMs": round(load_ms, 1),
            "computeMs": round(compute_ms, 1),
            "cacheHit": cache_hit,
            "generatedAt": _now_iso(),
            "datasetLoadedAt": loaded_at,
            "totalRecords": int(len(df)),
            "filteredRecords": int(len(filtered)),
            "cleaning": cleaning,
            "dataSource": _data_source_info(source),
            "apiVersion": API_VERSION,
        },
        "filters": {
            "diet": diet,
            "search": search,
            "availableDiets": sorted(df["diet"].unique().tolist()),
        },
        **body,
    }


def _num(value, digits=2):
    """Float rounded for JSON, or None for NaN/inf."""

    if value is None:
        return None
    value = float(value)
    if not np.isfinite(value):
        return None
    return round(value, digits)


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in ("1", "true", "yes")


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

def get_health():
    """Return basic API health information."""

    return {
        "status": "healthy",
        "service": "Nutritional Insights API",
        "apiVersion": API_VERSION,
        "datasetCached": _cache["df"] is not None,
    }


def get_insights(diet: str = "all", search: str = "", refresh=False):
    """Chart data for the dashboard: bar, scatter, heatmap and pie."""

    def compute(f: pd.DataFrame, _full: pd.DataFrame):
        avg = (
            f.groupby("diet")[["protein", "carbs", "fat"]].mean().reset_index()
            if len(f) else pd.DataFrame(columns=["diet", "protein", "carbs", "fat"])
        )
        average_macros = [
            {"diet": r.diet, "protein": _num(r.protein), "carbs": _num(r.carbs), "fat": _num(r.fat)}
            for r in avg.itertuples()
        ]

        # Pie: diets when showing everything, cuisines inside a single diet.
        group_by = "diet" if diet.strip().lower() in ("", "all") else "cuisine"
        counts = f[group_by].value_counts()
        items = [{"label": k, "count": int(v)} for k, v in counts.items()]
        if len(items) > PIE_MAX_SLICES:
            rest = sum(i["count"] for i in items[PIE_MAX_SLICES - 1:])
            items = items[:PIE_MAX_SLICES - 1] + [{"label": "other", "count": rest}]

        sample = f.sample(SCATTER_MAX_POINTS, random_state=42) if len(f) > SCATTER_MAX_POINTS else f
        scatter = [
            {"recipe": r.recipe, "diet": r.diet, "cuisine": r.cuisine,
             "protein": _num(r.protein, 1), "carbs": _num(r.carbs, 1), "fat": _num(r.fat, 1)}
            for r in sample.itertuples()
        ]

        corr_df = pd.DataFrame({
            "Protein": f["protein"],
            "Carbs": f["carbs"],
            "Fat": f["fat"],
            "Protein:Carbs": f["protein"] / f["carbs"].replace(0, np.nan),
            "Carbs:Fat": f["carbs"] / f["fat"].replace(0, np.nan),
        }).replace([np.inf, -np.inf], np.nan)
        labels = list(corr_df.columns) if len(f) >= 2 else []
        matrix = (
            [[_num(v) for v in row] for row in corr_df.corr().to_numpy()]
            if labels else []
        )

        top_cuisines = []
        for d, g in f.groupby("diet"):
            vc = g["cuisine"].value_counts()
            top_cuisines.append({"diet": d, "cuisine": vc.index[0], "count": int(vc.iloc[0])})

        top_protein = (
            f.sort_values("protein", ascending=False).groupby("diet").head(5)
            .sort_values(["diet", "protein"], ascending=[True, False])
        )
        top_protein_recipes = [
            {"diet": r.diet, "recipe": r.recipe, "cuisine": r.cuisine, "protein": _num(r.protein)}
            for r in top_protein.itertuples()
        ]

        highest = None
        if len(avg):
            best = avg.loc[avg["protein"].idxmax()]
            highest = {"diet": best["diet"], "avgProtein": _num(best["protein"])}

        summary = {
            "recipes": int(len(f)),
            "diets": int(f["diet"].nunique()),
            "cuisines": int(f["cuisine"].nunique()),
        }
        if len(f):
            summary.update(
                avgProtein=_num(f["protein"].mean()),
                avgCarbs=_num(f["carbs"].mean()),
                avgFat=_num(f["fat"].mean()),
            )

        return {
            "averageMacros": average_macros,
            "distribution": {"groupBy": group_by, "items": items},
            "scatter": scatter,
            "correlation": {"labels": labels, "matrix": matrix},
            "topCuisines": top_cuisines,
            "topProteinRecipes": top_protein_recipes,
            "highestProteinDiet": highest,
            "summary": summary,
        }

    return _run(diet, search, _parse_bool(refresh), compute)


def get_recipes(
    page: int = 1,
    page_size: int = 10,
    diet: str = "all",
    search: str = "",
    sort: str = "protein",
    order: str = "desc",
    refresh=False,
):
    """Paginated, filtered, sorted recipe list."""

    if page < 1:
        raise ValueError("Page must be greater than zero.")

    if page_size < 1 or page_size > 100:
        raise ValueError("Page size must be between 1 and 100.")

    sort = (sort or "protein").strip().lower()
    if sort not in SORTABLE:
        raise ValueError(f"sort must be one of: {', '.join(SORTABLE)}.")

    order = (order or "desc").strip().lower()
    if order not in ("asc", "desc"):
        raise ValueError("order must be 'asc' or 'desc'.")

    def compute(f: pd.DataFrame, _full: pd.DataFrame):
        total = int(len(f))
        total_pages = max(1, (total + page_size - 1) // page_size)
        ordered = f.sort_values(SORTABLE[sort], ascending=(order == "asc"), kind="mergesort")
        chunk = ordered.iloc[(page - 1) * page_size: page * page_size]
        items = [
            {"recipe": r.recipe, "diet": r.diet, "cuisine": r.cuisine,
             "protein": _num(r.protein), "carbs": _num(r.carbs), "fat": _num(r.fat)}
            for r in chunk.itertuples()
        ]
        return {
            "items": items,
            "page": page,
            "pageSize": page_size,
            "totalItems": total,
            "totalPages": total_pages,
            "sort": sort,
            "order": order,
        }

    return _run(diet, search, _parse_bool(refresh), compute)


def get_clusters(
    k: int = 3,
    diet: str = "all",
    search: str = "",
    refresh=False,
):
    """K-means clusters of recipes by protein, carbs and fat."""

    if k < 1 or k > 10:
        raise ValueError("The number of clusters must be between 1 and 10.")

    def compute(f: pd.DataFrame, _full: pd.DataFrame):
        if f.empty:
            return {"k": k, "clusters": [], "points": [],
                    "note": "No recipes match the current filters."}

        # analysis.generate_clusters expects the original column names.
        frame = pd.DataFrame({
            "Diet_type": f["diet"].values,
            "Protein(g)": f["protein"].values,
            "Carbs(g)": f["carbs"].values,
            "Fat(g)": f["fat"].values,
        })
        result = generate_clusters(frame, k=k, return_labels=True)
        labels = np.array(result.pop("labels"))

        seen = {}
        for c in result["clusters"]:
            name = _cluster_name(c["centroid"], f)
            seen[name] = seen.get(name, 0) + 1
            c["name"] = name if seen[name] == 1 else f"{name} {seen[name]}"

        idx = np.arange(len(f))
        if len(idx) > CLUSTER_MAX_POINTS:
            idx = np.random.default_rng(42).choice(idx, CLUSTER_MAX_POINTS, replace=False)
        rows = f.iloc[idx]
        points = [
            {"recipe": r.recipe, "diet": r.diet, "cluster": int(labels[i]),
             "protein": _num(r.protein, 1), "carbs": _num(r.carbs, 1), "fat": _num(r.fat, 1)}
            for i, r in zip(idx, rows.itertuples())
        ]

        return {
            "k": k,
            "clusters": result["clusters"],
            "points": points,
            "note": result.get("note"),
        }

    return _run(diet, search, _parse_bool(refresh), compute)


def _cluster_name(centroid: dict, f: pd.DataFrame) -> str:
    """Name a cluster after the macro furthest above the filtered average."""

    scores = {}
    for key in ("protein", "carbs", "fat"):
        std = f[key].std() or 1.0
        scores[key] = (centroid[key] - f[key].mean()) / std
    ranked = sorted(scores, key=scores.get, reverse=True)
    top, second = ranked[0], ranked[1]
    if scores[top] < 0.25:
        return "Balanced / lighter"
    words = {"protein": "protein", "carbs": "carb", "fat": "fat"}
    if scores[second] > 0.5:
        return f"High-{words[top]} & {words[second]}"
    return f"High-{words[top]}"
