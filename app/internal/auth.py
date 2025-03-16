from fastapi import APIRouter, HTTPException, status, Header, Body
from datetime import datetime, timezone

from config.connection import SessionDepends
from models.users import UserLogin
from typing import Annotated
from services.auth import Authenticate, CurrentUser, check_refresh_token

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

a = Authenticate()
c = CurrentUser()


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
    user_data = {**result.dict(), "lastlogin": current_time.isoformat()}
    access_token = a.generate_access_token(user_data)
    refresh_token = a.generate_refresh_token(user_data)
    return {"username": form_data.username, "fullname": user_data['fullname'], "access_token": access_token,
            "refresh_token": refresh_token}
