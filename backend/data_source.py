
import os
from io import BytesIO

import pandas as pd
from azure.storage.blob import BlobServiceClient


def load_dataset():
    """
    Retrieve All_Diets.csv from Azure Blob Storage.

    Required environment variables:
        AZURE_STORAGE_CONNECTION_STRING
        AZURE_STORAGE_CONTAINER
        AZURE_STORAGE_BLOB
    """

    connection_string = os.getenv(
        "AZURE_STORAGE_CONNECTION_STRING"
    )

    container_name = os.getenv(
        "AZURE_STORAGE_CONTAINER",
        "datasets"
    )

    blob_name = os.getenv(
        "AZURE_STORAGE_BLOB",
        "All_Diets.csv"
    )

    if not connection_string:
        raise RuntimeError(
            "AZURE_STORAGE_CONNECTION_STRING is not configured."
        )

    if not container_name or not blob_name:
        raise RuntimeError(
            "Azure container or blob name is missing."
        )

    blob_service = BlobServiceClient.from_connection_string(
        connection_string
    )

    blob_client = blob_service.get_blob_client(
        container=container_name,
        blob=blob_name
    )

    try:
        download = blob_client.download_blob()
        file_bytes = download.readall()

        df = pd.read_csv(BytesIO(file_bytes))

        metadata = {
            "source": "azure-blob",
            "container": container_name,
            "blob": blob_name,
            "rows": len(df),
            "columns": len(df.columns),
        }

        return df, metadata

    except Exception as error:
        raise RuntimeError(
            f"Unable to retrieve dataset from Azure Blob Storage: {error}"
        ) from error
