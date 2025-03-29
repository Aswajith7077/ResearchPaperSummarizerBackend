from typing import Annotated

from fastapi import APIRouter, HTTPException,status,Query,Body
from models.users import UserSignIn

from config.dbconnection import SessionDepends
from services.users import retrive_users, add_user, remove_user,update_users

router = APIRouter(
    prefix = "/users",
    tags = ["Users"]
)



@router.get("/list_users")
async def list_users(session:SessionDepends):
    result_status,result = await retrive_users(session)
    if not result_status:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = result)
    return result


@router.post("/create_user")
async def create_user(session:SessionDepends, data:Annotated[UserSignIn,Body()]):
    result_status,result = await add_user(session,data)
    if not result_status:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = result)
    return result


@router.put("/update_user")
async def update_user(session:SessionDepends,user_name:Annotated[str,Query()], data:UserSignIn):
    result_status,result = await update_users(session,user_name,data)
    if not result_status:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = result)
    return result

@router.delete("/delete_user")
async def delete_user(session:SessionDepends,user_name:Annotated[str,Query()]):
    result_status,result = await remove_user(session,user_name)
    if not result_status:
        raise HTTPException(status_code = status.HTTP_400_BAD_REQUEST, detail = result)
    return result