from fastapi import APIRouter,HTTPException,Depends,Query,Path
from typing import Annotated
from config.dbconnection import SessionDepends
from app.dependencies import check_access_token
from services.history import retrive_today,retrive_history,retrive_yesterday,get_history_file


router = APIRouter(
    prefix="/history",
    # dependencies = [Depends(check_access_token)],
    tags=["History"]
)


@router.get("/get_history")
async def get_history(session:SessionDepends,id:Annotated[str,Query()]):

    result_status,result = await get_history_file(session,id)
    if not result_status:
        print(result)
        raise HTTPException(status_code=400,detail=result)
    return result

@router.get("/today/{user_id}")
async def get_today(session:SessionDepends,user_id:Annotated[str,Path()]):

    result_status,result = await retrive_today(session,user_id)
    if not result_status:
        raise HTTPException(status_code=404, detail=result)

    return result

@router.get("/yesterday/{user_id}")
async def get_yesterday(session:SessionDepends,user_id: Annotated[str,Path()]):

    result_status,result = await retrive_yesterday(session,user_id)
    if not result_status:
        raise HTTPException(status_code=404, detail=result)
    return result


@router.get("/all/{user_id}")
async def history(session:SessionDepends,user_id:Annotated[str,Path()]):
    result_status,result = await retrive_history(session,user_id)
    if not result_status:
        raise HTTPException(status_code=404, detail=result)
    return result