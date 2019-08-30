#!/usr/bin/env python3
# coding=utf-8

import logging
import os
from os.path import dirname, abspath

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from telegram import ParseMode, Bot, InputMediaPhoto

from app.models import Base
from app.parser import get_films_info
from app.saver import save_films_return_new, get_new_films_info

logger = logging.getLogger(__name__)
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
BASE_DIRECTORY = dirname(abspath(__file__))


def form_messages(film_info):
    info = "*{name}*\n\n" \
           "{original_name}\n" \
           "Режиссёр: {director}\n" \
           "{countries}\n\n" \
           "{genres}\n" \
           "{box_office_from}".format(**film_info)
    if film_info.get('video'):
        video_text = "\n\n[Трейлер]({video})".format(**film_info)
    description = "{description}{video_text}"
    actors = "Актёры:\n{actors}".format(**film_info)
    theaters_seances = []
    for theater, three_d in film_info['theaters'].items():
        for three_d, days in three_d.items():
            _three_d = '3D' if three_d == '3D' else ''
            days_seances = []
            for day, seances in days.items():
                seances_times = []
                for seance in seances:
                    times = ' '.join(seance['times']).ljust(30)
                    cost = ' *{}*'.format(seance['cost']) if seance.get('cost') else ''
                    seances_times.append("{}{}".format(times, cost))
                if not seances_times:
                    continue
                seances_times = '\n'.join(seances_times)
                days_seances.append("*{}*\n{}".format(day, seances_times))
            if not days_seances:
                continue
            days_seances = '\n\n'.join(days_seances)
            theaters_seances.append("*{} {}*\n{}".format(theater, _three_d, days_seances))
    theaters_seances = '\n\n'.join(theaters_seances)
    return info, description, actors, theaters_seances


if __name__ == '__main__':
    # Настройки логирования
    logging.basicConfig(
        format='[%(asctime)s %(levelname)s] %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO)

    bot = Bot(BOT_TOKEN)

    logger.info("Creating database connection.")
    db_file = f'{BASE_DIRECTORY}/database.sqlite'
    engine = create_engine(f'sqlite:///{db_file}', echo=False)
    Base.metadata.create_all(engine)
    session = scoped_session(sessionmaker(bind=engine))

    logger.info("Getting films info.")
    films_info = get_films_info()

    logger.info("Saving films and getting new films.")
    new_films = save_films_return_new(session, films_info)
    logger.info("Getting new films info.")
    films_info = get_new_films_info(session, new_films)

    for film_info in films_info:
        logger.info("Forming {} film messages texts.".format(film_info['name']))
        info, description, actors, theaters_seances = form_messages(film_info)

        logger.info("Sending film messages.")
        bot.send_photo(CHANNEL_ID, photo=film_info['poster'], caption=info, parse_mode=ParseMode.MARKDOWN)
        bot.send_message(CHANNEL_ID, text=description, parse_mode=ParseMode.MARKDOWN)
        media = []
        for i, image in enumerate(film_info['images']):
            params = {'media': image}
            if i == 0:
                params['caption'] = actors
            media.append(InputMediaPhoto(**params))
        bot.send_media_group(CHANNEL_ID, media=media)
        bot.send_message(CHANNEL_ID, text=theaters_seances, parse_mode=ParseMode.MARKDOWN)
    logger.info("All messages sent.")
