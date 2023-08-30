from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from constants import DB_NAME
from models import LongUrl, ShortUrl


class DBManager:
    def __init__(self):
        self.engine = create_engine(f"sqlite:///{DB_NAME}", echo=True)
        self.Session = None
        self.session = None

    def __enter__(self):
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not exc_type:
            self.session.commit()
        else:
            self.session.rollback()
        self.session.close()

    def get_long_url(self, long_url: str):
        url = self.session.scalars(select(LongUrl.url).where(LongUrl.url == long_url))
        return url.first()

    def create_long_url(self, long_url: str):
        new_url = LongUrl(url=long_url)
        self.session.add(new_url)
        self.session.commit()
        return

    def get_short_by_long_url(self, long_url: str):
        print('here')
        short_url_object = self.session.query(ShortUrl).join(LongUrl, ShortUrl.long_url_id == LongUrl.id).filter(
            LongUrl.url == long_url).first()
        return str(short_url_object.url)

    def get_long_by_short_url(self, short_url):
        long_url_object = self.session.query(LongUrl). \
            join(ShortUrl, ShortUrl.long_url_id == LongUrl.id). \
            filter_by(url=short_url).first()
        return str(long_url_object.url)

    def create_short_url(self, short_url: str, id_long_url: int):
        new_url = ShortUrl(url=id_long_url, long_url_id=short_url)
        self.session.add(new_url)
        self.session.commit()
        return

    def get_long_url_id(self, long_url):
        long_url_id = self.session.scalars(select(LongUrl.id).filter(LongUrl.url == long_url))
        return long_url_id.first()
