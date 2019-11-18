#!/usr/bin/env python3
# coding=utf-8

import logging
import requests
from requests.exceptions import ConnectionError
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

logger = logging.getLogger(__name__)
BASE_URL = 'https://fanlife.ru'


def get_films_info():
    logger.info("Getting main page.")
    main_url = 'https://fanlife.ru/afisha/cat/1'
    html = get_page_html(main_url)
    links = get_films_links(html)
    links = list(set(links))
    sleep(5)
    films_info = []
    for link in links:
        logger.info("Getting film info from {}.".format(link))
        html = get_page_html(link)
        film_info = get_film_info(html)
        film_info['url'] = link
        films_info.append(film_info)
        sleep(5)
    return films_info


def get_page_html(url):
    try:
        response = requests.get(url)
    except ConnectionError:
        response = None

    if response and response.status_code == 200:
        return response.text

    options = Options()
    options.add_argument('--headless')

    with webdriver.Firefox(options=options) as driver:
        driver.get(url)
        return driver.page_source


def get_films_links(html):
    soup = BeautifulSoup(html, features="html.parser")
    afisha = soup.find('div', attrs={"class": 'b-afisha-page'})
    days = afisha.findAll('div', attrs={'class': 'b-seances'})
    links = []
    for day in days:
        films = day.findAll('div', attrs={'class': 'b-seances__film'})
        for film in films:
            link = film.find('div', attrs={'class': 'b-seances__film-name'}).find('a')
            # TODO Get film without going to page
            if not link:
                continue
            link = link['href']
            if link.startswith('/'):
                continue
            links.append(link)
    return links


def inner_strip(text):
    text = text.replace('\n', ' ')
    while True:
        length = len(text)
        text = text.replace('  ', ' ')
        if len(text) == length:
            return text


def get_film_info(html):
    info = {}
    soup = BeautifulSoup(html, features="html.parser")
    # Title
    parent = soup.find('div', attrs={"class": 'b-review'})
    info['name'] = parent.find('h1', attrs={"class": 'b-h1'}).text
    # Image
    parent = soup.find('div', attrs={"class": 'b-review__cover'})
    info['poster'] = ''.join((BASE_URL, parent.find('a').attrs.get('href')))
    parent = soup.find('div', attrs={"class": 'b-review__meta'})
    metas = parent.findAll('div', attrs={"class": 'b-meta'})
    names_map = {
        'Название на языке оригинала:': 'original_name',
        'Режиссёр:': 'director',
        'Актёры:': 'actors',
        'Оценка IMDb:': 'IMDB',
    }
    for meta in metas:
        name = meta.find('div', attrs={"class": 'b-meta__name'})
        if not name:
            continue
        name = name.text
        value = meta.find('div', attrs={"class": 'b-meta__value'}).text
        value = inner_strip(value)
        info[names_map[name]] = value

    metas = parent.findAll('span', attrs={"class": 'b-meta__token'})
    info['genres'] = metas[0].text
    info['countries'] = metas[1].text
    info['duration'] = metas[2].text
    info['box_office_from'] = metas[3].text
    info['description'] = soup.find('div', attrs={"class": 'b-review__text'}).text
    info['description'] = inner_strip(info['description'])

    video_parent = soup.find('div', attrs={"class": 'b-review__video'}).find('iframe')
    info['video'] = video_parent.attrs.get('src') if video_parent else ''
    info['images'] = []
    images_parent = soup.find('div', attrs={"class": 'b-review__gallery'})
    if images_parent:
        info['images'] = list(images_parent.findAll('a'))
        info['images'] = [''.join((BASE_URL, image.attrs.get('href'))) for image in info['images']]

    parent = soup.find('div', attrs={"class": 'b-seances'})
    movie_theaters = parent.findAll('div', attrs={"class": 'b-seances__film-content'})
    info['theaters'] = []
    for movie_theater in movie_theaters:
        parent = movie_theater.find('div', attrs={"class": 'b-seances__film-name'})
        theater = parent.find('a').text
        three_d = parent.find('span', attrs={"class": 'b-icon_3d'})
        three_d = True if three_d and three_d.text == '3D' else False

        seances = movie_theater.findAll('div', attrs={"class": 'b-seances__seances'})
        theater_seances = []
        for seance_day in seances:
            seance_date = seance_day.find('div', attrs={"class": 'b-seances__organization'}).text
            seance_date = inner_strip(seance_date)
            seance_costs = seance_day.find('div', attrs={"class": 'b-seances__time'}).find('div')
            seance_costs = seance_costs.findAll('span', attrs={"class": 'b-pr'})
            costs = []
            for seance_cost in seance_costs:
                seance_times = [seance_time.text for seance_time in seance_cost.findAll('span')]
                cost = seance_cost.find('small')
                cost = cost.text.strip() if cost else ''
                costs.append({'times': seance_times, 'cost': cost})
            theater_seances.append({'date': seance_date, 'costs': costs})
        info['theaters'].append({'theater': theater, 'seances': theater_seances, '3D': three_d})

    return info
