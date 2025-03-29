from typing import Annotated
from fastapi import Depends
from sqlmodel import SQLModel,Session
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool

from config.config import db_user, db_password, db_host, db_port, db_name

# Load environment variables from .env
engine = None

try:
    DATABASE_URL = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
    engine = create_engine(DATABASE_URL, poolclass=NullPool)
    print("Database connection established")
except Exception as e:
    print(f"Failed to connect: {e}")



def create_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session


SessionDepends = Annotated[Session,Depends(get_session)]
