
import pandas as pd
import pytest

from analysis import (
    clean_data,
    calculate_average_macros,
    get_top_protein_recipes,
    get_highest_protein_diet,
    get_common_cuisines,
    calculate_nutritional_ratios,
    generate_insights,
)


@pytest.fixture
def sample_data():

    return pd.DataFrame({
        "Diet_type": [
            "paleo",
            "PALEO",
            "vegan",
            "vegan",
        ],
        "Cuisine_type": [
            "italian",
            "Italian",
            "asian",
            "asian",
        ],
        "Recipe_name": [
            "Recipe A",
            "Recipe B",
            "Recipe C",
            "Recipe D",
        ],
        "Protein(g)": [
            20,
            40,
            None,
            30,
        ],
        "Carbs(g)": [
            30,
            50,
            40,
            60,
        ],
        "Fat(g)": [
            10,
            20,
            15,
            20,
        ],
    })


def test_clean_data(sample_data):

    original = sample_data.copy()

    cleaned = clean_data(sample_data)

    assert cleaned["Diet_type"].tolist() == [
        "Paleo",
        "Paleo",
        "Vegan",
        "Vegan",
    ]

    assert cleaned["Cuisine_type"].tolist() == [
        "Italian",
        "Italian",
        "Asian",
        "Asian",
    ]

    assert cleaned["Protein(g)"].iloc[2] == 30

    assert not cleaned[
        ["Protein(g)", "Carbs(g)", "Fat(g)"]
    ].isnull().any().any()

    pd.testing.assert_frame_equal(
        sample_data,
        original
    )


def test_average_macros(sample_data):

    cleaned = clean_data(sample_data)

    result = calculate_average_macros(cleaned)

    assert len(result) == 2

    paleo = result[
        result["Diet_type"] == "Paleo"
    ].iloc[0]

    assert paleo["Protein(g)"] == 30


def test_top_protein_recipes(sample_data):

    cleaned = clean_data(sample_data)

    result = get_top_protein_recipes(
        cleaned,
        limit=1
    )

    assert len(result) == 2

    assert result["Protein(g)"].tolist() == [
        40,
        30,
    ]


def test_highest_protein_diet(sample_data):

    cleaned = clean_data(sample_data)

    result = get_highest_protein_diet(cleaned)

    assert result["diet_type"] == "Paleo"

    assert result["average_protein"] == 30


def test_common_cuisines(sample_data):

    cleaned = clean_data(sample_data)

    result = get_common_cuisines(cleaned)

    assert len(result) == 2


def test_nutritional_ratios(sample_data):

    cleaned = clean_data(sample_data)

    result = calculate_nutritional_ratios(cleaned)

    assert "Protein_to_Carbs_ratio" in result.columns

    assert "Carbs_to_Fat_ratio" in result.columns


def test_generate_insights(sample_data):

    result = generate_insights(sample_data)

    assert result["total_recipes"] == 4

    assert len(result["diet_types"]) == 2

    assert "average_macros" in result

    assert "highest_protein_diet" in result
