
import pandas as pd

from unittest.mock import patch

from api import get_health, get_insights, get_recipes


def sample_dataset():

    return pd.DataFrame({
        "Recipe_name": [
            "Recipe A",
            "Recipe B",
            "Recipe C",
        ],
        "Diet_type": [
            "Vegan",
            "Paleo",
            "Vegan",
        ],
        "Cuisine_type": [
            "Asian",
            "Italian",
            "Asian",
        ],
        "Protein(g)": [
            20,
            40,
            30,
        ],
        "Carbs(g)": [
            30,
            50,
            40,
        ],
        "Fat(g)": [
            10,
            20,
            15,
        ],
    })


def test_health():

    result = get_health()

    assert result["status"] == "healthy"


@patch("api.load_dataset")
def test_get_insights(mock_load):

    mock_load.return_value = (
        sample_dataset(),
        {
            "source": "azure-blob",
            "container": "datasets",
            "blob": "All_Diets.csv",
        },
    )

    result = get_insights()

    assert result["success"] is True

    assert result["metadata"]["source"] == "azure-blob"

    assert result["insights"]["total_recipes"] == 3


@patch("api.load_dataset")
def test_get_recipes(mock_load):

    mock_load.return_value = (
        sample_dataset(),
        {"source": "azure-blob"},
    )

    result = get_recipes(page=1, page_size=2)

    assert result["success"] is True

    assert len(result["recipes"]) == 2


def test_invalid_pagination():

    try:
        get_recipes(page=0)

        assert False, "Expected ValueError"

    except ValueError:
        pass
