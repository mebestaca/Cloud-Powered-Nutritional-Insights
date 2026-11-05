import numpy as np
import pandas as pd

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


CLUSTER_COLUMNS = [
    "Protein(g)",
    "Carbs(g)",
    "Fat(g)"
]


def generate_clusters(
    df: pd.DataFrame,
    k: int = 3
) -> dict:
    """
    Group recipes into nutritional clusters using K-means.

    Nutritional values are standardized before clustering so
    differences in scale do not unfairly influence the results.
    """

    if k < 1 or k > 10:
        raise ValueError("The number of clusters must be between 1 and 10.")

    if df.empty:
        return {
            "clusters": [],
            "note": "No recipes are available for clustering."
        }

    # Avoid requesting more clusters than available recipes.
    actual_k = min(k, len(df))

    features = df[CLUSTER_COLUMNS].astype(float)

    # Standardize the nutritional measurements.
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    # Perform K-means clustering.
    model = KMeans(
        n_clusters=actual_k,
        random_state=42,
        n_init=10
    )

    labels = model.fit_predict(scaled_features)

    # Convert cluster centres back to grams.
    centroids = scaler.inverse_transform(model.cluster_centers_)

    results = []

    for cluster_id in range(actual_k):
        cluster_df = df.loc[labels == cluster_id].copy()

        if cluster_df.empty:
            continue

        # Count the diet types represented in this cluster.
        diet_mix = (
            cluster_df["Diet_type"]
            .value_counts()
            .rename_axis("diet")
            .reset_index(name="count")
        )

        results.append({
            "id": cluster_id + 1,
            "name": f"Cluster {cluster_id + 1}",
            "size": int(len(cluster_df)),
            "centroid": {
                "protein": round(float(centroids[cluster_id][0]), 2),
                "carbs": round(float(centroids[cluster_id][1]), 2),
                "fat": round(float(centroids[cluster_id][2]), 2)
            },
            "dietMix": diet_mix.to_dict(orient="records")
        })

    return {
        "clusters": results,
        "note": None
    }