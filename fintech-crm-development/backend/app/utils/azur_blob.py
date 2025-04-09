from azure.storage.blob import BlobServiceClient

from app.core.config import settings

# Create the BlobServiceClient object which will be used to create a container client
blob_service_client = BlobServiceClient.from_connection_string(settings.CONNECTION_STRING)

container_client = blob_service_client.get_container_client(settings.CONTAINER_NAME)
