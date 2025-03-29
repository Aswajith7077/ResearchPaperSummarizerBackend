import uuid

from sqlmodel import SQLModel,Field
from datetime import datetime
import uuid


class History(SQLModel,table = True):


    __tablename__ = 'history'

    history_id:uuid.UUID = Field(default_factory = uuid.uuid4,primary_key = True)
    user_id:str = Field(nullable = False)
    timestamp:datetime = Field(nullable = False)
    response_file_name:str = Field(nullable = False)



