import os

from azure.identity import ClientSecretCredential
from azure.storage.blob import BlobServiceClient
from datetime import datetime,timezone
from dotenv import load_dotenv

load_dotenv()


azure_client_id = os.getenv("AZURE_CLIENT_ID")
azure_tenant_id = os.getenv("AZURE_TENANT_ID")
azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")
azure_storage_url = os.getenv("AZURE_STORAGE_URL")
azure_container_name = os.getenv("AZURE_CONTAINER_NAME")

print(azure_container_name)
print(azure_storage_url)
print(azure_client_id)
print(azure_tenant_id)
print(azure_client_secret)


clientCredentials = ClientSecretCredential(
    client_id = azure_client_id,
    client_secret = azure_client_secret,
    tenant_id = azure_tenant_id
)







def get_data(time:str,user_id:str,file_name:str):

    try:
        blob_name = f"{user_id}/{file_name}/{time.strip()}.md"
        print(blob_name)
        blob_service_client = BlobServiceClient(account_url=azure_storage_url, credential=clientCredentials)
        container_client = blob_service_client.get_container_client(container=azure_container_name)

        blob_client = container_client.get_blob_client(blob = blob_name)
        data = blob_client.download_blob().readall()

        print(data)
        return data
    except Exception as error:
        print(error)


def upload_data():

    content = """utpat at
        + Facilisis in pretium nisl aliquet
        - Nulla volutpat aliquam velit
    + Very easy!"""

    time = datetime.now(timezone.utc).isoformat()
    user_id = "voicedaswa"
    filename = "Evaluating_word_embedding_models_Methods_and_exper"

    blob_name = f"{user_id}/{filename}/{time}.md"
    blob_service_client = BlobServiceClient(account_url=azure_storage_url, credential = clientCredentials)
    container_client = blob_service_client.get_container_client(container=azure_container_name)

    container_client.upload_blob(name = blob_name,data = content)

time = "2025-03-29T10:54:02.704178+00:00"
user_id = "voicedaswa"
filename = "Evaluating_word_embedding_models_Methods_and_exper"

get_data(time,user_id,filename)
