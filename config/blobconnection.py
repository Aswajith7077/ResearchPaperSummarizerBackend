from azure.identity import ClientSecretCredential
from config.config import azure_client_id,azure_client_secret,azure_tenant_id




clientCredentials = ClientSecretCredential(
    client_id = azure_client_id,
    client_secret = azure_client_secret,
    tenant_id = azure_tenant_id
)

