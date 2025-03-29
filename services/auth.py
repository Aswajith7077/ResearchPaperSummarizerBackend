import datetime
from config.config import (
    jwt_encode_algorithm,
    jwt_access_token_secret_key,
    jwt_refresh_token_secret_key,
)
from schemas.users import UserDB
from sqlmodel import select,Session
from passlib.context import CryptContext
from config.config import jwt_refresh_token_expiry_time_minutes
import jwt

from config.dbconnection import SessionDepends

pwd_context = CryptContext(schemes=['bcrypt'])


class CurrentUser:

    async def get_current_user_by_access_token(self, token: bytes):
        result = jwt.decode(token, key=jwt_access_token_secret_key, algorithms=[jwt_encode_algorithm])
        return result

    async def get_current_user_by_refresh_token(self, token: bytes):
        result = jwt.decode(token, key=jwt_refresh_token_secret_key, algorithms=[jwt_encode_algorithm])
        return result

async def signout_user(current_user:str,session:Session):
    try:
        result = session.exec(select(UserDB).where(UserDB.username == current_user)).first()
        if not result:
            raise Exception("User not found")

        result_dict = dict(result)
        result_dict.update({"is_logged":False})

        new_one = UserDB(**result_dict)
        session.delete(result)
        session.add(new_one)
        session.commit()
        session.refresh(new_one)
        return True,"Signout Successful"
    except Exception as error:
        return False,error.args

async def check_refresh_token(refresh_token: str):
    c = CurrentUser()
    result = await c.get_current_user_by_refresh_token(refresh_token.encode())
    if result is None:
        return False
    difference = datetime.now(datetime.timezone.utc) - datetime.fromisoformat(result['lastlogin'])
    difference_in_minutes = difference.total_seconds() / 60

    if difference_in_minutes >= jwt_refresh_token_expiry_time_minutes:
        return True
    else:
        return False


async def update_login(session,user_data: UserDB):
    try:
        temp = session.exec(select(UserDB).where(UserDB.username == user_data.username)).one()
        session.delete(temp)
        session.add(user_data)
        session.commit()
        session.refresh(user_data)

        return True,"Updation Successful"
    except Exception as e:
        return False,e.args

class Authenticate:

    def generate_access_token(self, data: dict):
        return jwt.encode(data, key=jwt_access_token_secret_key, algorithm=jwt_encode_algorithm)

    def generate_refresh_token(self, data: dict):
        return jwt.encode(data, key=jwt_refresh_token_secret_key, algorithm=jwt_encode_algorithm)

    async def user_in_db(self, session,username):
        try:
            result = session.exec(select(UserDB).where(UserDB.username == username)).one()
            if not result:
                return None
            return result
        except Exception as e:
            return None

    def check_password(self, login_password, actual_password):
        return pwd_context.verify(login_password, actual_password)

    def generate_hash(self, text: str):
        return pwd_context.hash(text)

    async def authenticate_user(self,session, username: str, password: str):

        result = await self.user_in_db(session,username)
        print(result)
        if result is None:
            return None
        elif not self.check_password(password, result.password):
            return None
        else:
            return result


