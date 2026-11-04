
import numpy as np
import pandas as pd


# Columns used throughout the nutritional analysis
NUMERIC_COLUMNS = [
    "Protein(g)",
    "Carbs(g)",
    "Fat(g)"
]

RECIPE_COLUMNS = [
    "Recipe_name",
    "Cuisine_type",
    "Protein(g)"
]


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the nutritional dataset.

    - Validate required columns.
    - Standardize diet and cuisine names.
    - Convert nutritional values to numeric types.
    - Replace missing nutritional values with column averages.
    """

    required_columns = [
        "Diet_type",
        "Cuisine_type",
        "Recipe_name",
        *NUMERIC_COLUMNS
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Dataset is missing required columns: {missing_columns}"
        )

    df = df.copy()

    # Standardize text columns
    for column in ["Diet_type", "Cuisine_type"]:
        df[column] = (
            df[column]
            .fillna("Unknown")
            .astype(str)
            .str.strip()
            .str.title()
        )

    # Clean nutritional values
    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )

        df[column] = df[column].replace(
            [np.inf, -np.inf],
            np.nan
        )

        column_mean = df[column].mean()

        if pd.notna(column_mean):
            df[column] = df[column].fillna(column_mean)
        else:
            df[column] = df[column].fillna(0)

    return df


def calculate_average_macros(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate average protein, carbohydrates,
    and fat for each diet type.
    """

    return (
        df.groupby("Diet_type")[NUMERIC_COLUMNS]
        .mean()
        .round(2)
        .reset_index()
    )


def get_top_protein_recipes(
    df: pd.DataFrame,
    limit: int = 5
) -> pd.DataFrame:
    """
    Retrieve the highest-protein recipes for each diet type.
    """

    return (
        df.sort_values(
            "Protein(g)",
            ascending=False
        )
        .groupby("Diet_type")
        .head(limit)
        .sort_values(
            ["Diet_type", "Protein(g)"],
            ascending=[True, False]
        )[RECIPE_COLUMNS]
        .reset_index(drop=True)
    )


def get_highest_protein_diet(df: pd.DataFrame) -> dict:
    """
    Identify the diet type with the highest
    average protein content.
    """

    average_protein = (
        df.groupby("Diet_type")["Protein(g)"]
        .mean()
    )

    if average_protein.empty:
        return {
            "diet_type": None,
            "average_protein": None
        }

    highest_diet = average_protein.idxmax()

    return {
        "diet_type": highest_diet,
        "average_protein": round(
            float(average_protein.max()),
            2
        )
    }


def get_common_cuisines(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify the most common cuisine for each diet type.
    """

    return (
        df.groupby("Diet_type")["Cuisine_type"]
        .agg(
            lambda values:
                values.mode().iloc[0]
                if not values.mode().empty
                else "Unknown"
        )
        .reset_index(name="most_common_cuisine")
    )


def calculate_nutritional_ratios(
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate protein-to-carbohydrate and
    carbohydrate-to-fat ratios.
    """

    result = df.copy()

    result["Protein_to_Carbs_ratio"] = (
        result["Protein(g)"]
        / result["Carbs(g)"].replace(0, np.nan)
    )

    result["Carbs_to_Fat_ratio"] = (
        result["Carbs(g)"]
        / result["Fat(g)"].replace(0, np.nan)
    )

    return result


def generate_insights(df: pd.DataFrame) -> dict:
    """
    Run the complete nutritional analysis and
    return the results in a JSON-friendly dictionary.
    """

    cleaned_df = clean_data(df)

    average_macros = calculate_average_macros(cleaned_df)

    top_recipes = get_top_protein_recipes(cleaned_df)

    highest_protein = get_highest_protein_diet(cleaned_df)

    common_cuisines = get_common_cuisines(cleaned_df)

    ratios_df = calculate_nutritional_ratios(cleaned_df)

    # Convert missing ratio values into None for JSON compatibility
    ratios = ratios_df[
        [
            "Recipe_name",
            "Protein_to_Carbs_ratio",
            "Carbs_to_Fat_ratio"
        ]
    ].astype(object)

    ratios = ratios.where(pd.notna(ratios), None)

    return {
        "total_recipes": int(len(cleaned_df)),

        "diet_types": sorted(
            cleaned_df["Diet_type"].unique().tolist()
        ),

        "average_macros": average_macros.to_dict(
            orient="records"
        ),

        "top_protein_recipes": top_recipes.to_dict(
            orient="records"
        ),

        "highest_protein_diet": highest_protein,

        "most_common_cuisines": common_cuisines.to_dict(
            orient="records"
        ),

        "nutritional_ratios": ratios.to_dict(
            orient="records"
        )
    }
