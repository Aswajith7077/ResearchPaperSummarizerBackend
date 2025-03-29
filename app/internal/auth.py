from fastapi import APIRouter, HTTPException, status, Header, Body,Query
from datetime import datetime, timezone

from schemas.users import UserDB
from config.dbconnection import SessionDepends
from models.users import UserLogin, Dummy
from typing import Annotated
from services.auth import Authenticate, CurrentUser, check_refresh_token, update_login,signout_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

a = Authenticate()
c = CurrentUser()


@router.post("/signout")
async def signout(session:SessionDepends,user_id:Annotated[str,Query()],sample:Annotated[Dummy,Body()]):
    result_status,result = await signout_user(current_user = user_id,session=session)
    print(sample)
    if not result_status:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail = result)
    return result


@router.get("/refresh")
async def refresh_access_token(refresh_token: str):
    if not await check_refresh_token(refresh_token=refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session Expired")

    user = await c.get_current_user_by_refresh_token(refresh_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid Refresh Token")

    user.update({'lastlogin': datetime.now(timezone.utc).isoformat()})
    access_token = a.generate_access_token(user)
    return {"access_token": access_token, "refresh_token": refresh_token}


@router.get("/check_access_token")
async def check_access_token(authorization=Header()):
    print(authorization.split())


# @router.get("/check_refresh_token")


@router.post("/login")
async def login_user(session:SessionDepends,form_data: Annotated[UserLogin,Body()]):
    global a
    result = await a.authenticate_user(session,form_data.username, form_data.password)
    if result is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Either User not present or Invalid password")

    current_time = datetime.now(timezone.utc)
    user_data = {**result.dict(), "lastlogin": current_time.isoformat(),"is_logged": True}
    access_token = a.generate_access_token(user_data)
    refresh_token = a.generate_refresh_token(user_data)

    result_status,result = await update_login(session,UserDB(**user_data))
    if not result_status:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = result)

    return {"username": form_data.username, "fullname": user_data['fullname'], "access_token": access_token,
            "refresh_token": refresh_token}
