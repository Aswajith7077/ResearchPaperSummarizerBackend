from fastapi import APIRouter,File,UploadFile,Body,Depends,Path,HTTPException
from datetime import datetime,timezone
from typing import Annotated
from app.dependencies import check_access_token
from config.dbconnection import SessionDepends
from models.questions import Question
from services.history import insert_history
from services.reviewer import generate_markdown

router = APIRouter(
    prefix="/reviewer",
    tags=["File Upload"],
    dependencies=[Depends(check_access_token)]
)





@router.post("/upload_files/{user_id}")
async def upload_files(session:SessionDepends,files:Annotated[list[UploadFile],File()],user_id:Annotated[str,Path()]):
    print(user_id)
    time = datetime.now(timezone.utc).isoformat()


    file_data = await files[0].read()

    content = await generate_markdown(file_data)
    print("content : ",content)

    # result_status,result = await insert_history(session = session,user_id = user_id,title = files[0].filename,files = [file.filename for file in files],summary = content)
    # if not result_status:
    #     print(result)
    #     raise HTTPException(status_code=400, detail=result)

    return {"message":"Success","result":content}

@router.get("/list_history_today")
async def list_history_today():
    current_date = datetime.now(timezone.utc).isoformat()
    
    print(current_date)
    return "Success"


@router.post("/add_question")
async def add_question(question:Annotated[Question,Body()]):

    print(question)
    return "Success"
