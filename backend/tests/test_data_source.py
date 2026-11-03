
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from data_source import load_dataset


def test_load_dataset_from_blob():

    csv_content = (
        b"Recipe_name,Diet_type,Cuisine_type,"
        b"Protein(g),Carbs(g),Fat(g)\n"
        b"Test Recipe,Vegan,Asian,20,30,10\n"
    )

    mock_blob = MagicMock()
    mock_blob.download_blob.return_value.readall.return_value = (
        csv_content
    )

    mock_service = MagicMock()
    mock_service.get_blob_client.return_value = mock_blob

    with patch.dict(
        "os.environ",
        {
            "AZURE_STORAGE_CONNECTION_STRING": "fake-connection",
            "AZURE_STORAGE_CONTAINER": "datasets",
            "AZURE_STORAGE_BLOB": "All_Diets.csv",
        },
    ):

        with patch(
            "data_source.BlobServiceClient.from_connection_string",
            return_value=mock_service,
        ):

            df, metadata = load_dataset()

    assert len(df) == 1

    assert df.iloc[0]["Recipe_name"] == "Test Recipe"

    assert metadata["source"] == "azure-blob"

    assert metadata["container"] == "datasets"


def test_load_dataset_requires_connection_string():

    with patch.dict(
        "os.environ",
        {},
        clear=True
    ):

        with pytest.raises(RuntimeError):
            load_dataset()
