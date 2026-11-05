
from data_source import load_dataset
from analysis import (
    clean_data,
    generate_insights,
    get_top_protein_recipes,
    generate_clusters
)


def get_health():
    """Return basic API health information."""

    return {
        "status": "healthy",
        "service": "Nutritional Insights API",
    }


def get_insights():
    """Retrieve the dataset and generate nutritional insights."""

    df, metadata = load_dataset()

    insights = generate_insights(df)

    return {
        "success": True,
        "metadata": metadata,
        "insights": insights,
    }


def get_recipes(page: int = 1, page_size: int = 10):
    """Return paginated protein-rich recipe results."""

    if page < 1:
        raise ValueError("Page must be greater than zero.")

    if page_size < 1 or page_size > 100:
        raise ValueError("Page size must be between 1 and 100.")

    df, metadata = load_dataset()

    cleaned_df = clean_data(df)

    recipes = get_top_protein_recipes(
        cleaned_df,
        limit=5
    )

    start = (page - 1) * page_size
    end = start + page_size

    return {
        "success": True,
        "metadata": metadata,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": len(recipes),
            "total_pages": (
                (len(recipes) + page_size - 1) // page_size
            ),
        },
        "recipes": recipes.iloc[start:end].to_dict(
            orient="records"
        ),
    }

def get_clusters(
    k: int = 3,
    diet: str = "all",
    search: str = ""
):
    """Return nutritional clusters for the selected recipes."""

    if k < 1 or k > 10:
        raise ValueError("The number of clusters must be between 1 and 10.")

    df, metadata = load_dataset()

    cleaned_df = clean_data(df)

    # Apply the selected diet filter.
    if diet.lower() != "all":
        cleaned_df = cleaned_df[
            cleaned_df["Diet_type"].str.lower() == diet.lower()
        ]

    # Search recipe names, diet types, and cuisines.
    if search.strip():
        search_term = search.strip().lower()

        matches = (
            cleaned_df["Recipe_name"].str.lower().str.contains(
                search_term, na=False
            )
            | cleaned_df["Diet_type"].str.lower().str.contains(
                search_term, na=False
            )
            | cleaned_df["Cuisine_type"].str.lower().str.contains(
                search_term, na=False
            )
        )

        cleaned_df = cleaned_df[matches]

    result = generate_clusters(cleaned_df, k=k)

    return {
        "success": True,
        "metadata": metadata,
        **result
    }