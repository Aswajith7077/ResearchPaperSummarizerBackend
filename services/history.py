from config.blobconnection import clientCredentials
from config.config import azure_storage_url,azure_container_name
from azure.storage.blob import BlobServiceClient
from sqlmodel import select
from datetime import datetime,timedelta,timezone
from schemas.history import History, AssociatedFiles
import uuid


blob_service_client = BlobServiceClient(account_url=azure_storage_url, credential=clientCredentials)
container_client = blob_service_client.get_container_client(container=azure_container_name)


async def insert_history(session,user_id:str,title:str,files:list[str],summary):

    try:

        date = datetime.now(timezone.utc).strftime("%d-%m-%Y")
        time = datetime.now(timezone.utc).isoformat()
        key = uuid.uuid4()
        filename = f"{user_id}/{date}/{title}/{time}.md"
        h_record = History(id=key, user_id=user_id, date=date, title=title, filename=filename, timestamp=time)


        # Blob insertion

        container_client.upload_blob(name=filename, data=summary)

        # Insert the History Record


        session.add(h_record)
        session.commit()
        session.refresh(h_record)

        # Insert the AssociatedFiles Record

        for file in files:
            k = uuid.uuid4()
            record = AssociatedFiles(id = k,history_id = key,filename = file)
            session.add(record)

        session.commit()

        # Insertion into the files Blob




        return True,"Success"
    except Exception as e:
        return False,e.args




async def get_history_file(session,id):

    try:

        result = session.exec(select(History).where(History.id == id)).first()
        if result is None:
            raise Exception(f"History with id {id} not found.")

        data = container_client.get_blob_client(blob = result.filename).download_blob().readall()

        return True,data
    except Exception as e:
        return False,e.args




async def retrive_today(session,username:str):

    try:

        date = datetime.now(timezone.utc).strftime('%d-%m-%Y')
        result = session.exec(select(History).where(History.user_id == username and History.date == date)).all()

        return True,[[f.filename,str(f.id),f.title] for f in result[::-1]]

    except Exception as e:
        return False,e.args


async def retrive_yesterday(session,username:str):

    try:

        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        yest = yesterday.strftime('%d-%m-%Y')
        result = session.exec(select(History).where(History.user_id == username and History.date == yest)).all()


        return True,[[f.filename,str(f.id),f.title] for f in result[::-1]]
    except Exception as e:
        return False,e.args


async def retrive_history(session,username:str):

    try:
        today = datetime.now(timezone.utc).strftime('%d-%m-%Y')
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime('%d-%m-%Y')

        result = session.exec(select(History).where(History.user_id == username and History.date != today and History.date != yesterday)).all()

        return True,[[f.filename[:15],str(f.id),f.title] for f in result[::-1]]
    except Exception as e:
        return False,e.args