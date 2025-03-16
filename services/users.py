from sqlmodel import select
from schemas.users import UserDB
from models.users import UserSignIn
from services.auth import Authenticate

a = Authenticate()
async def retrive_users(session,limit:int = 10):

    try:
        result = session.exec(select(UserDB).limit(limit)).all()
        return True,result
    except Exception as e:
        return False,e.args


async def add_user(session,user_data:UserSignIn):
    user_data.password = a.generate_hash(user_data.password)
    try:
        data = UserDB(**user_data.dict())
        session.add(data)
        session.commit()
        session.refresh(data)
        return True,"User Insertion: Operation successful"
    except Exception as e:
        return False,e.args

async def update_users(session,user_name:str,user_data:UserSignIn):

    try:
        data = session.exec(select(UserDB).where(UserDB.username == user_name)).first()
        if not data:
            return False,"User not found"

        insert_data = UserDB(**user_data.dict())
        session.delete(data)
        session.add(insert_data)
        session.commit()
        session.refresh(insert_data)
        return True,"User Updation: Operation successful"
    except Exception as e:
        return False,e.args

async def remove_user(session,user_name:str):
    try:
        data = session.exec(select(UserDB).where(UserDB.username == user_name)).first()
        if not data:
            return False,"User not found"

        session.delete(data)
        session.commit()
        session.refresh(data)
        return True,"User Deletion : Operation successful"
    except Exception as e:
        return False,e.args
