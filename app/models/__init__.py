from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from app.models.film import Film
from app.models.theater import Theater
from app.models.seance import Seance
