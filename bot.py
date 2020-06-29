#!/usr/bin/env python3
# coding=utf-8

import logging
import os
from os.path import dirname, abspath
from tempfile import NamedTemporaryFile
from time import sleep

import requests
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
    video_text = "\n\n[Трейлер]({})".format(film_info['video']) if film_info.get('video') else ''
    description = "{}{}".format(film_info.get('description'), video_text)
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


def get_temporary_file(content):
    temp_file = NamedTemporaryFile(delete=False)
    temp_file.write(content)
    opened_file = open(temp_file.name, 'rb')
    return temp_file, opened_file


def close_files(temp_file, opened_file):
    opened_file.close()
    temp_file.close()
    os.unlink(temp_file.name)


if __name__ == '__main__':
    # Настройки логирования
    logging.basicConfig(
        format='[%(asctime)s %(levelname)s] %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO)

    bot = Bot(BOT_TOKEN)

    logger.info("Creating database connection.")
    db_file = '{}/database.sqlite'.format(BASE_DIRECTORY)
    engine = create_engine('sqlite:///{}'.format(db_file), echo=False)
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
        logger.info("Sending poster.")
        pos = film_info['poster'].find('?')
        if not pos == -1:
            film_info['poster'] = film_info['poster'][:pos]
        try:
            bot.send_photo(CHANNEL_ID, photo=film_info['poster'], caption=info, parse_mode=ParseMode.MARKDOWN,
                           timeout=120)
        except Exception as exc:
            logger.error(f"Error while sending film poster: {exc}")
        logger.info("Sending description and video.")
        bot.send_message(CHANNEL_ID, text=description, parse_mode=ParseMode.MARKDOWN, timeout=120)
        logger.info("Sending photos and actors.")
        media = []
        temporaries = []
        for i, image in enumerate(film_info['images']):
            sleep(1)
            file_content = requests.get(image)
            temp_file, media_file = get_temporary_file(file_content.content)
            temporaries.append((temp_file, media_file))
            params = {'media': media_file}
            if i == 0:
                params['caption'] = actors
            media.append(InputMediaPhoto(**params))
        if media:
            bot.send_media_group(CHANNEL_ID, media=media, timeout=120)
            for temp_file, media_file in temporaries:
                close_files(temp_file, media_file)
        else:
            bot.send_message(CHANNEL_ID, text=actors, timeout=120)
        logger.info("Sending seances.")
        try:
            bot.send_message(CHANNEL_ID, text=theaters_seances, parse_mode=ParseMode.MARKDOWN, timeout=120)
        except Exception as exc:
            sleep(2)
        logger.info("Sending link.")
        try:
            bot.send_message(CHANNEL_ID, text=film_info['url'], parse_mode=ParseMode.MARKDOWN, timeout=120)
        except Exception:
            sleep(3)
            continue
        # break
    logger.info("All messages sent.")
