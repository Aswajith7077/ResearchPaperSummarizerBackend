from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
from config.config import azure_client_id,azure_client_secret,azure_tenant_id,azure_storage_url,azure_container_name




clientCredentials = ClientSecretCredential(
    client_id = azure_client_id,
    client_secret = azure_client_secret,
    tenant_id = azure_tenant_id
)
blob_service_client = BlobServiceClient(account_url = azure_storage_url, credentials = clientCredentials)
container_client = blob_service_client.get_container_client(container = azure_container_name)
