import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)

from database.database import create_db_tables
from routes.admin import router as admin_router
from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.conversations import router as conversations_router
from routes.routes import router as routes_router
from routes.voice import router as voice_router
from routes.recommendations import router as recommendations_router
from routes.data_pipeline import router as data_pipeline_router
from routes.knowledge_graph import router as knowledge_graph_router
from routes.tipp_scraper import router as tipp_scraper_router
from routes.upload import router as upload_router
from routes.share import router as share_router


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
        "http://localhost:3002",     
        "http://192.168.1.116:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(conversations_router)
app.include_router(routes_router)
app.include_router(voice_router)
app.include_router(recommendations_router)
app.include_router(data_pipeline_router)
app.include_router(knowledge_graph_router)
app.include_router(tipp_scraper_router)
app.include_router(upload_router)
app.include_router(share_router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to TradeMate API!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
