    
import pandas as pd

from analysis import clean_data


def test_clean_data():
    data = {
        "Diet_type": ["paleo", "PALEO", "vegan"],
        "Cuisine_type": ["italian", "Italian", "asian"],
        "Protein(g)": [20, 40, None],
        "Carbs(g)": [30, 50, 40],
        "Fat(g)": [10, 20, 15],
    }

    original_df = pd.DataFrame(data)
    cleaned_df = clean_data(original_df)

    # Check text standardization.
    assert cleaned_df["Diet_type"].tolist() == [
        "Paleo", "Paleo", "Vegan"
    ]

    assert cleaned_df["Cuisine_type"].tolist() == [
        "Italian", "Italian", "Asian"
    ]

    # Check missing-value replacement.
    assert cleaned_df["Protein(g)"].iloc[2] == 30

    # Check that nutritional columns contain no missing values.
    assert cleaned_df[["Protein(g)", "Carbs(g)", "Fat(g)"]].isnull().sum().sum() == 0

    # Check that the original DataFrame was not modified.
    assert original_df["Diet_type"].iloc[0] == "paleo"

    print("All data-cleaning checks passed!")


if __name__ == "__main__":
    test_clean_data()
