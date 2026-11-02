
import numpy as np
import pandas as pd


# Nutritional columns used throughout the analysis
NUMERIC_COLUMNS = ["Protein(g)", "Carbs(g)", "Fat(g)"]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and standardize the nutritional dataset.

    - Standardizes diet and cuisine names.
    - Converts nutritional columns to numeric values.
    - Replaces missing nutritional values with column means.
    - Returns a cleaned copy of the original DataFrame.
    """

    # Work with a copy to preserve the original DataFrame.
    df = df.copy()

    # Standardize text columns.
    df["Diet_type"] = df["Diet_type"].str.strip().str.title()
    df["Cuisine_type"] = df["Cuisine_type"].str.strip().str.title()

    # Convert nutritional columns to numeric values.
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    # Replace missing nutritional values with column means.
    for column in NUMERIC_COLUMNS:
        column_mean = df[column].mean()
        df[column] = df[column].fillna(column_mean)

    return df
