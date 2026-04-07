from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.database import create_db_tables
from routes.auth import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    yield


app = FastAPI(title="TradeMate API", lifespan=lifespan)

app.include_router(auth_router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to TradeMate API!"}
