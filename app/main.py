from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from common_settings.config import TITLE, PREFIX
from init_app import create_app
from v1.database.database import init_tables
from v1.main import app as app_v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_tables()
    yield


app = create_app(root_path=PREFIX, title=TITLE, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.mount("/v1", app_v1)
