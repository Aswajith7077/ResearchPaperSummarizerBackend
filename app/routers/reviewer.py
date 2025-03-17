from fastapi import APIRouter,File,UploadFile,Body,Query
from typing import Annotated

from models.questions import Question

router = APIRouter(
    prefix="/reviewer",
    tags=["File Upload"]
)


@router.post("/upload_files")
async def upload_files(files:Annotated[list[UploadFile],File()]):

    # data = await files[0].read()
    # print(data[:10])
    return "Success"


@router.post("/add_question")
async def add_question(question:Annotated[Question,Body()]):
    print(question)
    return "Success"
