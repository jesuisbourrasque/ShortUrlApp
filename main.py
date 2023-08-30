import os
from typing import Optional

import shortuuid
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from sqlalchemy import create_engine

from DBmanager import DBManager
from constants import DB_NAME
from models import Base

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    if not os.path.exists(DB_NAME):
        engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)
        Base.metadata.create_all(engine)


class LongShortUrl(BaseModel):
    long_url: HttpUrl
    short_url: Optional[str] = None


@app.get("/")
async def get_long_url(short_url: str):
    with DBManager() as db:
        long_url = db.get_long_by_short_url(short_url)
    return long_url


@app.post("/")
async def add_long_url(body: LongShortUrl) -> str:
    short_url = body.short_url
    long_url = str(body.long_url)
    with DBManager() as db:
        if not db.get_long_url(long_url):
            db.create_long_url(long_url)
            id_long_url = db.get_long_url_id(long_url)
        else:
            id_long_url = db.get_long_url_id(long_url)
        if not short_url or not db.get_short_by_long_url(long_url):
            short_url = shortuuid.random(length=5)
            db.create_short_url(id_long_url, short_url)
    return short_url
