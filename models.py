from sqlalchemy import Column, ForeignKey, Integer, Text
from sqlalchemy.orm import declarative_base

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
