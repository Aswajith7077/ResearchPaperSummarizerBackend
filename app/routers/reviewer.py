from fastapi import APIRouter,File,UploadFile,Body,Depends
from datetime import datetime,timezone
from typing import Annotated
from app.dependencies import check_access_token
from models.questions import Question

router = APIRouter(
    prefix="/reviewer",
    tags=["File Upload"],
    dependencies=[Depends(check_access_token)]
)


@router.post("/upload_files")
async def upload_files(files:Annotated[list[UploadFile],File()]):
    time = datetime.now(timezone.utc).isoformat()
    return {"message":"Success","result":"Success"}

@router.get("/list_history_today")
async def list_history_today():
    current_date = datetime.now(timezone.utc).isoformat()
    
    print(current_date)
    return "Success"


@router.post("/add_question")
async def add_question(question:Annotated[Question,Body()]):
    print(question)
    return "Success"
