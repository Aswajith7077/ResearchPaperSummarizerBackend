from fastapi import UploadFile
import secrets

schedule_queue = dict()

def generateKey():
    while True:
        key = secrets.randbelow(10**12)
        if key not in schedule_queue:
            return key

async def schedule(files:list[UploadFile]):

    key = generateKey()
    schedule_queue[key] = files
    return key






