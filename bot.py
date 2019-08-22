#!/usr/bin/env python3
# coding=utf-8

import os
from os.path import dirname, abspath

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from app.models import Base
from app.parser import get_films_info
from app.saver import save_films_return_new, get_new_films_info

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
BASE_DIRECTORY = dirname(abspath(__file__))


if __name__ == '__main__':
    db_file = f'{BASE_DIRECTORY}/database.sqlite'
    engine = create_engine(f'sqlite:///{db_file}', echo=False)
    Base.metadata.create_all(engine)
    session = scoped_session(sessionmaker(bind=engine))

    films_info = get_films_info()

    new_films = save_films_return_new(session, films_info)
    films_info = get_new_films_info(session, new_films)

    # TODO send to telegram chat
