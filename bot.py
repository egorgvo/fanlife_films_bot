#!/usr/bin/env python3
# coding=utf-8

import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')


def get_page_html(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.content.decode(response.encoding)

    options = Options()
    options.add_argument('--headless')

    with webdriver.Firefox(options=options) as driver:
        driver.get(url)
        return driver.page_source


def get_films_links(html):
    soup = BeautifulSoup(html)
    afisha = soup.find('div', attrs={"class": 'b-afisha-page'})
    days = afisha.findAll('div', attrs={'class': 'b-seances'})
    links = []
    for day in days:
        films = day.findAll('div', attrs={'class': 'b-seances__film'})
        for film in films:
            links.append(film.find('div', attrs={'class': 'b-seances__film-name'}).find('a')['href'])
    return links


if __name__ == '__main__':
    main_url = 'https://fanlife.ru/afisha/cat/1'

    html = get_page_html(main_url)
    links = get_films_links(html)
    for link in links:
        html = get_page_html(link)
