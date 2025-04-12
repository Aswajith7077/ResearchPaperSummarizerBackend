from sqlmodel import SQLModel,Field
import uuid



class History(SQLModel,table = True):

    __tablename__ = 'history'

    id:uuid.UUID = Field(primary_key=True)
    user_id:str = Field(foreign_key='users.username',index=True)
    date:str = Field(title = 'date',nullable=False,index=True)
    title:str = Field(title = 'title',nullable=False,index=True)
    filename:str = Field(title = 'filename',nullable=False)
    timestamp:str = Field(title = 'timestamp',nullable=False)


class AssociatedFiles(SQLModel,table = True):
    __tablename__ = 'associated_files'

    id:uuid.UUID = Field(primary_key=True)
    history_id:uuid.UUID = Field(foreign_key = "history.id",index=True)
    filename:str = Field(title = 'filename',nullable=False)


