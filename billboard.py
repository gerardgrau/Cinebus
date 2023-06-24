from __future__ import annotations

import datetime as dt
import json
import operator
from dataclasses import dataclass, field
from functools import reduce

import requests
from bs4 import BeautifulSoup, Tag
from unidecode import unidecode

from buses import Coord


class PageNotFound(Exception):
    """Class Exception in order to raise error if page is not found."""
    pass


@dataclass
class Film:
    title: str
    genres: list[str]
    directors: list[str]
    actors: list[str]
    projections: list[Projection] = field(default_factory=list)


@dataclass
class Cinema:
    name: str
    address: str
    loc: Coord
    projections: list[Projection] = field(default_factory=list)

    def get_projections_in_1_day(self) -> list[Projection]:
        def starts_in_1_day(proj) -> bool: return dt.timedelta(
        ) < proj.start_time - dt.datetime.now() < dt.timedelta(days=1)
        return [proj for proj in self.projections if starts_in_1_day(proj)]


@dataclass
class Projection:
    film: Film
    cinema: Cinema
    start_time: dt.datetime
    end_time: dt.datetime
    language: str


@dataclass
class Billboard:
    cinemas: list[Cinema]
    films: list[Film]
    projections: list[Projection]

    def __init__(self) -> None:
        """ Reads the information from the sensacine webpage and returns a Billbord element with all the cinemas, films and projections"""
        try:
            url = 'https://www.sensacine.com/cines/cines-en-72480/?page='
            pages = [requests.get(url + str(i)) for i in range(1, 4)]

            if any(200 != p.status_code for p in pages):
                raise PageNotFound

            contents = reduce(operator.add, map(lambda p: p.content, pages))
            soup = BeautifulSoup(contents, 'html.parser')

            self.read_cinemas(soup)
            cinema_dict = {cinema.name: cinema for cinema in self.cinemas}

            self.films = []
            self.projections = []
            self.read_films_and_projections(soup, cinema_dict)

        except PageNotFound:
            print(
                "No s'ha pogut obtenir la informació de la pàgina web. S'està tornant a intentar...")
            return self.__init__()

    def read_cinemas(self, soup: BeautifulSoup) -> None:
        """ Reads all the cinemas in the soup."""
        def get_text(x) -> str: return x.text.strip()

        cinema_names = [get_text(name)
                        for name in soup.find_all('h2', class_='tt_18')]
        addresses = [get_text(addr) for addr in soup.find_all(
            'span', class_='lighten') if get_text(addr)[-2:] != 'Km']

        f = open('coord_cines.json', encoding='utf-8')
        cinema_coords = json.load(f)

        self.cinemas = [Cinema(name, addr, Coord(*cinema_coords[name].values()))
                        for (name, addr) in zip(cinema_names, addresses) if name in cinema_coords]

    def read_films_and_projections(self, soup: BeautifulSoup, cinema_dict: dict[str, Cinema]) -> None:
        """ Reads all the films and projections in the soup."""
        film_titles: dict[str, Film] = {}

        movie_segments = soup.find_all('div', class_='item_resa')
        for movie_segment in movie_segments:

            film, cinema_name = self.get_current_film_and_cinema(movie_segment)

            cinema = cinema_dict.get(cinema_name)
            if cinema is None:
                continue

            if film.title not in film_titles:
                self.films.append(film)
                film_titles[film.title] = film

            self.read_projections(
                movie_segment, film_titles[film.title], cinema)

    def get_current_film_and_cinema(self, movie_segment: Tag) -> tuple[Film, str]:
        """ Returns the film and the cinema name in the current movie segment."""
        movie = movie_segment.find('div', class_='j_w')
        movie_data = json.loads(movie['data-movie'])
        film = Film(*[movie_data[attr]
                    for attr in ('title', 'genre', 'directors', 'actors')])

        theater_data = json.loads(movie['data-theater'])
        cinema_name = theater_data['name'].strip()

        return film, cinema_name

    def read_projections(self, movie_segment: Tag, film: Film, cinema: Cinema) -> None:
        """ Reads all the projections on the given movie segment."""
        language = movie_segment.find('span', class_='bold').text
        if language == 'Digital':
            language = 'Castellano'

        item = movie_segment.parent['class'][-1]
        num_item = int(item.split('-')[-1])

        day = dt.date.today() + dt.timedelta(days=num_item)

        for time_segment in movie_segment.find_all('em'):
            time = json.loads(time_segment['data-times'])

            start_h_m = map(int, time[0].split(':'))
            start_time = dt.datetime.combine(day, dt.time(*start_h_m))

            end_h_m = map(int, time[2].split(':'))
            end_time = dt.datetime.combine(day, dt.time(*end_h_m))

            if start_time < dt.datetime.now():
                continue  # the film has already been projected
            if start_time > end_time:
                end_time += dt.timedelta(days=1)

            projection = Projection(
                film, cinema, start_time, end_time, language)
            self.projections.append(projection)
            film.projections.append(projection)
            cinema.projections.append(projection)

    def search_film_title(self, title: str) -> list[Film]:
        """Returns films whose title contains substring title."""
        return [film for film in self.films if lower_ASCII(title) in lower_ASCII(film.title)]

    def search_projections(self, title='', cinema_name='', genre='', director='', actor='') -> list[Projection]:
        return [projection for projection in self.projections
                if lower_ASCII(title) in lower_ASCII(projection.film.title)
                and lower_ASCII(cinema_name) in lower_ASCII(projection.cinema.name)
                and is_str_in_any(genre, projection.film.genres)
                and is_str_in_any(director, projection.film.directors)
                and is_str_in_any(actor, projection.film.actors)]


def is_str_in_any(string: str, str_list: list[str]) -> bool:
    """Returns a boolean indicating wether the given string is inside any of the strings in the list."""
    return any(lower_ASCII(string) in lower_ASCII(str_item) for str_item in str_list)


def lower_ASCII(s: str) -> str:
    """Returns the string in lowercase and replacing non-ASCII characters bye th closest ASCII character."""
    return unidecode(s).lower()
