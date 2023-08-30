import os
import sqlite3
from typing import Optional

import shortuuid
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

app = FastAPI()
DB_NAME = "db.sql"


@app.on_event("startup")
async def startup_event():
    if not os.path.exists(DB_NAME):
        con = sqlite3.connect(DB_NAME)
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE long_url (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE short_url (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                long_url_id INTEGER,
                url TEXT,
                FOREIGN KEY(long_url_id) REFERENCES long_url(id)
            )
            """
        )


class LongShortUrl(BaseModel):
    long_url: HttpUrl
    short_url: Optional[str] = None


class DBManager:
    def __init__(self):
        self._connection = sqlite3.connect(DB_NAME)
        self.cursor = None

    def __enter__(self):
        self.cursor = self._connection.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self._connection.commit()
        else:
            self._connection.rollback()
        self._connection.close()

    def get_long_url(self, long_url: str):
        self.cursor.execute(
            """
                SELECT url FROM long_url WHERE url = ?
            """,
            (long_url,)
        )
        return self.cursor.fetchone()

    def create_long_url(self, long_url: str):
        self.cursor.execute(
            """
            INSERT INTO long_url (url)
            VALUES (?)
            """,
            (long_url,)
        )
        return

    def get_short_by_long_url(self, long_url: str):
        self.cursor.execute(
            """
                SELECT su.url
                FROM short_url su
                JOIN long_url lu
                  ON su.long_url_id = lu.id
                WHERE lu.url = ?
            """,
            (long_url,)
        )
        return self.cursor.fetchone()

    def get_long_by_short_url(self, short_url):
        self.cursor.execute(
            """
                SELECT lu.url
                FROM long_url lu
                JOIN short_url su
                ON lu.id = su.long_url_id
                WHERE su.url = ?
            """,
            (short_url,)
        )
        return self.cursor.fetchone()

    def create_short_url(self, short_url: str, id_long_url: int):
        self.cursor.execute(
            """
            INSERT INTO short_url (long_url_id, url)
            VALUES (?, ?)
            """,
            (short_url, id_long_url)
        )
        return

    def get_long_url_id(self, long_url):
        self.cursor.execute(
            """
            SELECT id FROM long_url
            WHERE url = ?
            """,
            (long_url,)
        )
        return self.cursor.fetchone()


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
            db.create_short_url(*id_long_url, short_url)
    return short_url
