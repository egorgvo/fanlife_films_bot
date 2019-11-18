
from sqlalchemy import Column, Integer, String
from app.models import Base


class Film(Base):
    __tablename__ = 'film'

    id = Column(Integer, primary_key=True)
    url = Column(String())
    name = Column(String(), nullable=False)
    original_name = Column(String())
    poster = Column(String())
    director = Column(String())
    actors = Column(String())
    genres = Column(String())
    countries = Column(String())
    duration = Column(String())
    box_office_from = Column(String())
    IMDB = Column(String())
    description = Column(String())
    video = Column(String())
    images = Column(String())

    def __repr__(self):
        return self.name
