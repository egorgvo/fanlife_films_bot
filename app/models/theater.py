
from sqlalchemy import Column, Integer, String
from app.models import Base


class Theater(Base):
    __tablename__ = 'theater'

    id = Column(Integer, primary_key=True)
    weight = Column(String())
    name = Column(String())

    def __repr__(self):
        return self.name
