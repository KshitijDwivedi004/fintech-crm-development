# app/utils/azure_storage.py
from azure.storage.blob import BlobServiceClient, ContentSettings
from app.core.config import settings
import uuid

class AzureImageStorage:
    """
    Utility class for handling image operations with Azure Storage.
    
    This class provides methods for uploading, retrieving, and deleting images
    from Azure Blob Storage with proper content types and direct URLs.
    """
    
    def __init__(self):
        self.connection_string = settings.CONNECTION_STRING
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
    
    async def upload_image(self, file_content, user_id, container_name, filename, content_type):
        """
        Upload an image to Azure Storage and return metadata including direct URL
        
        Args:
            file_content (bytes): The binary content of the file
            user_id (str): The ID of the user the image belongs to
            container_name (str): The Azure container name
            filename (str): Name to use for the file
            content_type (str): MIME type of the file
            
        Returns:
            dict: Metadata about the uploaded image including URL
        """
        # Get container client
        container_client = self.blob_service_client.get_container_client(container_name)
        
        # Set the full path for the blob
        blob_path = f"{user_id}/{filename}"
        
        # Set content settings for proper content type
        content_settings = ContentSettings(content_type=content_type)
        
        # Upload the file
        blob_client = container_client.get_blob_client(blob_path)
        blob_client.upload_blob(file_content, overwrite=True, content_settings=content_settings)
        
        # Get the direct URL
        image_url = f"{settings.AZURE_STORAGE_PUBLIC_URL}/{blob_path}"
        
        return {
            "filepath": blob_path,
            "container": container_name,
            "image_url": image_url
        }
    
    async def delete_image(self, container_name, blob_path):
        """
        Delete an image from Azure Storage
        
        Args:
            container_name (str): The Azure container name
            blob_path (str): Path to the blob to delete
            
        Returns:
            bool: True if deletion successful
        """
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_path)
            blob_client.delete_blob()
            return True
        except Exception as e:
            print(f"Error deleting blob: {str(e)}")
            return False
    async def upload_document(self, file_content, user_id, container_name, filename, content_type):
        """
        Upload a document to Azure Storage and return metadata including direct URL
        
        Args:
            file_content (bytes): The binary content of the file
            user_id (str): The ID of the user the document belongs to
            container_name (str): The Azure container name
            filename (str): Name to use for the file
            content_type (str): MIME type of the file
            
        Returns:
            dict: Metadata about the uploaded document including URL
        """
        # Get container client
        container_client = self.blob_service_client.get_container_client(container_name)
        
        # Set the full path for the blob
        blob_path = f"{user_id}/documents/{filename}"
        
        # Set content settings for proper content type
        content_settings = ContentSettings(content_type=content_type)
        
        # Upload the file
        blob_client = container_client.get_blob_client(blob_path)
        blob_client.upload_blob(file_content, overwrite=True, content_settings=content_settings)
        
        # Get the direct URL
        document_url = f"{settings.AZURE_STORAGE_PUBLIC_URL}/{blob_path}"
        
        return {
            "filepath": blob_path,
            "container": container_name,
            "document_url": document_url
        }
        
    async def download_document(self, document_url):
        """
        Download a document from Azure Storage based on its URL
        
        Args:
            document_url (str): The URL of the document to download
            
        Returns:
            bytes: The content of the document
        """
        try:
            # Extract blob path from the URL
            # Example: if URL is "https://storageaccount.blob.core.windows.net/container/user_id/documents/filename"
            # We need to extract "user_id/documents/filename"
            url_parts = document_url.split(settings.AZURE_STORAGE_PUBLIC_URL + '/')
            if len(url_parts) != 2:
                raise ValueError(f"Invalid document URL format: {document_url}")
                
            blob_path = url_parts[1]
            
            # Extract container name based on URL structure
            # For most Azure Storage URLs, the container name is part of the hostname
            # If you have a specific container, use that instead
            container_name = settings.PROFILEPICTURECONTAINER_NAME  # Using the default container
            
            # Get the blob client
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_path)
            
            # Download the blob
            download_stream = blob_client.download_blob()
            
            # Return the content
            return download_stream.readall()
        except Exception as e:
            print(f"Error downloading document: {str(e)}")
            raise
        
    async def delete_document(self, document_url):
        """
        Delete a document from Azure Storage based on its URL
        
        Args:
            document_url (str): The URL of the document to delete
            
        Returns:
            bool: True if deletion successful
        """
        try:
            # Extract blob path from the URL
            url_parts = document_url.split(settings.AZURE_STORAGE_PUBLIC_URL + '/')
            if len(url_parts) != 2:
                raise ValueError(f"Invalid document URL format: {document_url}")
                
            blob_path = url_parts[1]
            
            # Use the default container
            container_name = settings.PROFILEPICTURECONTAINER_NAME
            
            # Delete the blob
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_path)
            blob_client.delete_blob()
            
            return True
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False

# Create a singleton instance
azure_image_storage = AzureImageStorage()