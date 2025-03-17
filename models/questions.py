from pydantic import BaseModel,Field
from datetime import datetime

class Question(BaseModel):

    question:str = Field(title = "Question")
    time:str = Field(title = "Time")