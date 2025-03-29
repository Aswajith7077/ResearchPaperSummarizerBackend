# from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from datetime import datetime, timezone
from fastapi import Header, HTTPException, status
from config.config import jwt_access_token_expiry_time_minutes
from services.auth import CurrentUser

c = CurrentUser()


async def check_access_token(authorization=Header(None)):
    if authorization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No Bearer Token Present")

    header_values = authorization.split()
    if len(header_values) < 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No Bearer Token Present")

    access_token = header_values[1]
    result = await c.get_current_user_by_access_token(access_token.encode())
    if result is None:
        raise ValueError("Invalid Token")
    difference = datetime.now(timezone.utc) - datetime.fromisoformat(result['lastlogin'])
    difference_in_minutes = difference.total_seconds() / 60

    if difference_in_minutes >= jwt_access_token_expiry_time_minutes:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail="Access Token Expired")
    else:
        return result


