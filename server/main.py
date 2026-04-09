from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import create_db_tables
from routes.auth import router as auth_router
from routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_tables()
    yield


app = FastAPI(title="TradeMate API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(chat_router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to TradeMate API!"}
