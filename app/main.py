from fastapi import FastAPI
from app.internal import auth
from app.routers import users,reviewer,history
from fastapi.middleware.cors import CORSMiddleware
from config.dbconnection import create_tables, engine

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth.router,prefix="/api")
app.include_router(users.router,prefix="/api")
app.include_router(reviewer.router,prefix="/api")
app.include_router(history.router,prefix="/api")

@app.on_event("startup")
async def startup():
    create_tables()
    print("Table Creation : Operation Successfull")

@app.on_event("shutdown")
async def shutdown():
    engine.dispose()
    print("Database Connection Closed")
@app.get("/")
async def root():
    return {"message":"CIDAR Welcomes You"}