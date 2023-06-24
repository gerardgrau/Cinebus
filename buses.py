import json
import os
from dataclasses import dataclass
from itertools import pairwise  # <=> pairwise(list) = zip(list, list[1:])
from typing import Iterator

import haversine as hs
import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox
import requests
import staticmap

BusesGraph = nx.DiGraph
RoadGraph = nx.DiGraph

BUS_SPEED = 5  # average speed (m/s) of a bus
BUS_STOP_TIME = 10  # waiting time (s) of a bus in a stop


class PageNotFound(Exception):
    """Class Exception in order to raise error if page is not found."""
    pass


@dataclass(frozen=True)
class Coord:
    """Coordinate of a point on earth. the x-attribute is the longitude and the y-attribute is the latitude."""
    x: float  # longitude
    y: float  # latitude

    def __init__(self, x, y) -> None:
        object.__setattr__(self, 'x', float(x))
        object.__setattr__(self, 'y', float(y))

    @property
    def xy(self) -> tuple[float, float]:
        """Returns the coordinate as a tuple: (x, y)."""
        return (self.x, self.y)


@dataclass(frozen=True)
class Node:
    """General class of the nodes used in buses_graph and city_graph."""
    id: int  # id of either the Parada or the Cruïlla
    coord: Coord


@dataclass(frozen=True)
class Aresta:
    """General class of edges used in buses_grahp and city_graph."""
    distancia: float
    # coordinates of the road/street intersections where the edge goes through (only used for graphical representation)
    coord_list: list[Coord]


@dataclass(frozen=True)
class MultiParada(Node):
    """A general bus stop. Also used in the city graph as a node type indicating a bus stop with multiple lines."""
    nom: str


@dataclass(frozen=True)
class Parada(MultiParada):
    """The node type used un the buses graph indicating a single bus stop.
    It only belongs to one bus line, so there are some stops that differ only in the bus line."""
    linia: str


@dataclass(frozen=True)
class Bus(Aresta):
    """An edge 'info' type used in the buses and the city graphs indicating a connection between two consecutive bus stops."""
    linia: str


def get_data() -> None:
    """Downloads the data of the public transport from OpenData Barcelona and stores it in a json file."""

    LINK = 'https://www.ambmobilitat.cat/OpenData/ObtenirDadesAMB.json'

    try:
        request = requests.get(LINK)
        if request.status_code != 200:
            raise PageNotFound
        data = request.json()

        with open('data_bus.json', 'w') as f:
            json.dump(data, f, indent=4)

    except PageNotFound:
        print("No s'ha pogut obtenir la informació de la pàgina web dels busos. S'està tornant a intentar...")
        return get_data()


def get_orig_dest_parades() -> tuple[set[Parada], list[Parada], list[Parada], dict[str, tuple[int]]]:
    """Returns a set of all the bus stops in the data_bus json file, a list of all the stops that are the start (origin) of one edge,
    a list of all the stops that are at the end (destination) of one edge, and a dicitonary with a random color associated to each line."""

    if not os.path.exists('data_bus.json') or os.path.getsize('data_bus.json') == 0:
        get_data()

    f = open('data_bus.json')
    data = json.load(f)

    parades_set = set()
    orig_parades = []
    dest_parades = []

    for linia in data['ObtenirDadesAMBResult']['Linies']['Linia']:
        def get_parada(elem): return Parada(int(elem['CodAMB']), Coord(
            elem['UTM_Y'], elem['UTM_X']), nom=elem['Nom'], linia=linia['Nom'])
        parades = [get_parada(elem) for elem in linia['Parades']['Parada']]

        parades_set |= set(parades)
        orig_parades.extend(list(parades)[:-1])
        dest_parades.extend(list(parades)[1:])

    colors_gen = generate_colors()
    colors_dict = {linia['Nom']: next(
        colors_gen) for linia in data['ObtenirDadesAMBResult']['Linies']['Linia']}
    return parades_set, orig_parades, dest_parades, colors_dict


def generate_colors() -> Iterator[tuple[int]]:
    """Generates apparently random colors which take values from 0 to 255."""
    i = 1
    while True:
        red = ((i * 17) % 256)
        green = ((i * 29) % 256)
        blue = ((i * 41) % 256)
        yield (red, green, blue)
        i += 1


def get_buses_graph() -> BusesGraph:
    """Loads the json file of the data, and returns the graph with bus stops as nodes and the distance between them as edges.
    It correctly Sets the distance and path from to bus stops to be the distance and path following the shortest road there is."""

    parades_set, orig_parades, dest_parades, colors_dict = get_orig_dest_parades()

    road_graph = ox.graph_from_place(
        'Barcelona, Spain', network_type='drive', simplify=True)

    parades_x = [p.coord.x for p in parades_set]
    parades_y = [p.coord.y for p in parades_set]
    nearest_nodes, nearest_dist = ox.distance.nearest_nodes(
        road_graph, parades_x, parades_y, return_dist=True)

    nearest_node_of = {parada: (nearest_node, dist_to_nearest) for parada, nearest_node, dist_to_nearest in
                       zip(parades_set, nearest_nodes, nearest_dist)}

    orig_nodes = [nearest_node_of[p][0] for p in orig_parades]
    dest_nodes = [nearest_node_of[p][0] for p in dest_parades]
    shortests_paths = ox.distance.shortest_path(
        road_graph, orig_nodes, dest_nodes, cpus=None)

    return build_buses_graph(road_graph, orig_parades, dest_parades, nearest_node_of, shortests_paths, colors_dict)


def build_buses_graph(road_graph: RoadGraph, orig_parades: list[Parada], dest_parades: list[Parada], nearest_node_of: dict[Parada, tuple[int, float]],
                      shortests_paths: list[list[int]], colors_dict: Iterator[tuple[int]]) -> BusesGraph:
    """Builds and returns the bus graph from the given attributes, savindg the geometry of each bus edge as
    the shortest path from the nearest nodes of the origin bus stop to the nearest nodes of destination bus stop"""

    buses_graph = BusesGraph()
    for orig_parada, dest_parada, path in zip(orig_parades, dest_parades, shortests_paths):
        if orig_parada == dest_parada:
            continue
        if max(nearest_node_of[orig_parada][1], nearest_node_of[dest_parada][1]) > 200:
            continue

        if path is None:
            path = []
        coord_list = [orig_parada.coord] + [Coord(road_graph.nodes[node]['x'],
                                                  road_graph.nodes[node]['y']) for node in path] + [dest_parada.coord]

        dist = sum(get_distance(coord1, coord2)
                   for coord1, coord2 in pairwise(coord_list))
        bus = Bus(dist, coord_list, linia=orig_parada.linia)
        buses_graph.add_edge(orig_parada, dest_parada, time=BUS_STOP_TIME + dist/BUS_SPEED,
                             color=colors_dict[orig_parada.linia], info=bus)

    return buses_graph


def get_distance(loc1: Coord, loc2: Coord) -> float:
    """Returns the distance between two points, taking into account Earth's curvature"""
    return hs.haversine((loc1.y, loc1.x), (loc2.y, loc2.x), unit=hs.Unit.METERS)


def show_buses(buses_graph: BusesGraph) -> None:
    """Shows the graph of the buses interactively."""
    positions = {parada: (parada.coord.x, parada.coord.y)
                 for parada in buses_graph.nodes}

    colors = [[c/255 for c in col]
              for col in nx.get_edge_attributes(buses_graph, 'color').values()]
    nx.draw(buses_graph, pos=positions, node_size=0, edge_color=colors)
    plt.show()


def plot_buses(g: BusesGraph, nom_fitxer: str) -> None:
    """Saves the graph as an image with the background city map."""
    m = staticmap.StaticMap(800, 600)

    for _, _, attrs in g.edges(data=True):
        color = '#%02x%02x%02x' % attrs['color']
        coords = [(coord.x, coord.y) for coord in attrs['info'].coord_list]
        m.add_line(staticmap.Line(coords, color, 1))

    image = m.render()
    image.save(nom_fitxer)
