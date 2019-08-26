#!/usr/bin/env python3
# coding=utf-8

from collections import OrderedDict
from copy import copy
from json import dumps, loads

from app.db_functions import get_or_create, get_or_default, create, find
from app.models import Film, Theater, Seance


def save_films_return_new(session, films_info):
    new_films = []

    for film_info in films_info:
        theaters = film_info.pop('theaters')
        film = get_or_default(session, Film,
                       name=film_info['name'],
                       original_name=film_info['original_name'],
                       director=film_info['director'])

        if True or not film:
            film_info['images'] = dumps(film_info['images'])
            film = create(session, Film, **film_info)
            new_films.append(film)

        for i, theater_info in enumerate(theaters):
            seances = theater_info.pop('seances', [])
            if not seances:
                continue
            three_d = theater_info.pop('3D', False)
            theater = get_or_create(session, Theater, name=theater_info['theater'])

            s = 0
            for seance_info in seances:
                for cost in seance_info['costs']:
                    s += 1
                    cost['times'] = dumps(cost['times'])
                    seance = get_or_create(session, Seance,
                                           film=film.id, theater=theater.id, weight=s, three_d=three_d,
                                           date=seance_info['date'], cost=cost['cost'], times=cost['times'])
    return new_films


def get_new_films_info(session, new_films):
    new_films_ids = [film.id for film in new_films]
    seances = find(session, Seance, Seance.film.in_(new_films_ids))
    theaters = find(session, Theater, Theater.id.in_(list(set([seance.theater for seance in seances]))))
    films_info = []
    for film in new_films:
        film_info = copy(film.__dict__)
        film_info.pop('_sa_instance_state', None)
        film_info.pop('id', None)
        film_info['images'] = loads(film_info['images'])
        film_info['theaters'] = {}
        for theater in theaters:
            seances = find(session, Seance, theater=theater.id, film=film.id)
            film_info['theaters'][theater.name] = {'2D': OrderedDict(), '3D': OrderedDict()}
            for seance in seances:
                seance_info = copy(seance.__dict__)
                seance_info.pop('_sa_instance_state', None)
                seance_info.pop('id', None)
                seance_info.pop('film', None)
                seance_info.pop('theater', None)
                seance_info.pop('weight', None)
                seance_info['times'] = loads(seance_info['times'])
                date = seance_info.pop('date')
                three_d = seance_info.pop('three_d')
                three_d = '3D' if three_d else '2D'
                film_info['theaters'][theater.name][three_d].setdefault(date, [])
                film_info['theaters'][theater.name][three_d][date].append(seance_info)
        films_info.append(film_info)
    return films_info
