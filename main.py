import os
import sqlite3
from typing import Optional
from sqlalchemy.orm import declarative_base, sessionmaker, joinedload
from sqlalchemy import Column, ForeignKey, Integer, String, Text, create_engine, select, insert

import shortuuid
from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

from constants import DB_NAME

app = FastAPI()
Base = declarative_base()


class LongUrl(Base):
    __tablename__ = "long_url"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text)


class ShortUrl(Base):
    __tablename__ = "short_url"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(Text)
    long_url_id = Column(Integer, ForeignKey("long_url.id"))


@app.on_event("startup")
async def startup_event():
    if not os.path.exists(DB_NAME):
        engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)
        Base.metadata.create_all(engine)
        # con = sqlite3.connect(DB_NAME)
        # cur = con.cursor()
        # cur.execute(
        #     """
        #     CREATE TABLE long_url (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         url TEXT
        #     )
        #     """
        # )
        # cur.execute(
        #     """
        #     CREATE TABLE short_url (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         long_url_id INTEGER,
        #         url TEXT,
        #         FOREIGN KEY(long_url_id) REFERENCES long_url(id)
        #     )
        #     """
        # )


class LongShortUrl(BaseModel):
    long_url: HttpUrl
    short_url: Optional[str] = None


class DBManager:
    def __init__(self):
        self._connection = sqlite3.connect(DB_NAME)
        self.cursor = None
        self.engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)
        self.Session = None
        self.session = None

    def __enter__(self):
        self.cursor = self._connection.cursor()
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self._connection.commit()
            self.session.commit()
        else:
            self._connection.rollback()
            self.session.rollback()
        self._connection.close()
        self.session.close()

    def get_long_url(self, long_url: str):
        url = self.session.scalars(select(LongUrl.url).where(LongUrl.url == long_url))
        # self.cursor.execute(
        #     """
        #         SELECT url FROM long_url WHERE url = ?
        #     """,
        #     (long_url,)
        # )
        return url.first()

    def create_long_url(self, long_url: str):
        new_url = LongUrl(url=long_url)
        self.session.add(new_url)
        self.session.commit()
        #url = self.session.scalars(insert(LongUrl).values(url=long_url))
        # self.cursor.execute(
        #     """
        #     INSERT INTO long_url (url)
        #     VALUES (?)
        #     """,
        #     (long_url,)
        # )
        return

    def get_short_by_long_url(self, long_url: str):
        print('here')
        short_url_object = self.session.query(ShortUrl).join(LongUrl, ShortUrl.long_url_id == LongUrl.id).filter(
            LongUrl.url == long_url).first()
        # self.cursor.execute(
        #     """
        #         SELECT su.url
        #         FROM short_url su
        #         JOIN long_url lu
        #           ON su.long_url_id = lu.id
        #         WHERE lu.url = ?
        #     """,
        #     (long_url,)
        # )

        return str(short_url_object.url)

    def get_long_by_short_url(self, short_url):
        long_url_object = self.session.query(LongUrl).join(ShortUrl).options(joinedload(ShortUrl.long_url)).filter(ShortUrl.url == short_url).first()
        # self.cursor.execute(
        #     """
        #         SELECT lu.url
        #         FROM long_url lu
        #         JOIN short_url su
        #         ON lu.id = su.long_url_id
        #         WHERE su.url = ?
        #     """,
        #     (short_url,)
        # )
        print("!!!!!!!!!!!! ", long_url_object)
        return str(long_url_object.url)

    def create_short_url(self, short_url: str, id_long_url: int):
        new_url = ShortUrl(url=short_url, long_url_id=id_long_url)
        self.session.add(new_url)
        self.session.commit()

        # self.cursor.execute(
        #     """
        #     INSERT INTO short_url (long_url_id, url)
        #     VALUES (?, ?)
        #     """,
        #     (short_url, id_long_url)
        # )
        return

    def get_long_url_id(self, long_url):
        long_url_id = self.session.scalars(select(LongUrl.id).where(LongUrl.url == long_url))
        # self.cursor.execute(
        #     """
        #     SELECT id FROM long_url
        #     WHERE url = ?
        #     """,
        #     (long_url,)
        # )
        return long_url_id.first()


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
    return str(short_url)