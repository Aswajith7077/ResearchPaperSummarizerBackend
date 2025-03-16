from sqlmodel import SQLModel,Field
from datetime import datetime
from typing import Optional

class UserDB(SQLModel,table = True):

    __tablename__ = 'users'

    email: str = Field(unique=True,nullable=False)
    username: str = Field(primary_key = True)
    password: str = Field(nullable=False)
    fullname: str = Field( default="GuestUser",nullable=False)
    is_logged: bool = Field( default=False)
    lastlogin:Optional[datetime] = Field( default=None)
    role: str = Field( default="customer")