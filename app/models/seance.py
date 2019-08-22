from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models import Base


class Seance(Base):
    __tablename__ = 'seance'

    id = Column(Integer, primary_key=True)
    weight = Column(String())
    theater = Column(ForeignKey("theater.id"))
    film = Column(ForeignKey("film.id"))
    three_d = Column(Boolean())
    date = Column(String())
    cost = Column(String())
    times = Column(String())

    def __repr__(self):
        return "{}, {}, {}, {}".format(self.film, self.theater, self.date, self.times)
