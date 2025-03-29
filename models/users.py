from pydantic import BaseModel, Field
from typing import Optional
import datetime
from services.auth import Authenticate

a = Authenticate()


class UserDB(BaseModel):
    email: str = Field(title="email")
    username: str = Field(title="username")
    password: str = Field(title="password")
    fullname: str = Field(title="fullname", default="GuestUser")
    is_logged: bool = Field(title="is_logged", default=False)
    lastlogin: datetime.datetime = Field(title="lastlogin", default_factory=datetime.datetime.now)
    role: str = Field(title="role", default="customer")

    @classmethod
    def hash_password(cls, value: str) -> str:
        return a.generate_hash(value)


class UserSignIn(BaseModel):
    email: str = Field(title="email")
    username: str = Field(title="username")
    fullname: Optional[str] = Field(title="fullname", default="GuestUser")
    password: str = Field(title="password")
    role: Optional[str] = Field(title="role", default="customer")


class UserLogin(BaseModel):
    username: str = Field(title='username')
    password: str = Field(title='password')

class Dummy(BaseModel):
    sample_string:str = Field(title="sample_string")