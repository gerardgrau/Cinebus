# city.py
from __future__ import annotations

import datetime as dt
import os
import pickle
from dataclasses import dataclass
from itertools import pairwise  # pairwise(list) = zip(list, list[1:])
from typing import Iterable

import matplotlib.pyplot as plt
import networkx as nx
import osmnx as ox
import staticmap

from buses import *

OsmnxGraph = nx.MultiDiGraph
StreetGraph = nx.Graph
CityGraph = nx.DiGraph

WALKING_SPEED = 1.5  # average walking speed (m/s) of a person
BUS_WAITING_TIME = 300  # waiting time (s) for the bus


@dataclass(frozen=True)
class Cruilla(Node):
    """A node type used in the city graph."""
    pass


@dataclass(frozen=True)
class Carrer(Aresta):
    """An edge 'info' type used in the city graph indicating a walkable street."""
    nom: str


@dataclass(frozen=True)
class Transbord(Aresta):
    """An edge 'info' type used in the city graph indicating either a change between walking and taking the bus
    or a transfer between two different bus lines ."""
    nom: str


@dataclass(frozen=True)
class Path:
    """Stores all the useful information when computing the shortest path from one position to another."""
    source: Coord
    destination: Coord
    route: list[Node]
    duration: dt.timedelta
    distance: float
    walking_distance: float


def get_osmnx_graph() -> OsmnxGraph:
    """Gets the graph osmnx from Barcelona."""
    return ox.graph_from_place('Barcelona, Spain', network_type='walk', simplify=True)


def save_graph(graph: nx.Graph, filename: str) -> None:
    """Saves the given graph in a file."""
    with open(filename, 'wb') as f:
        pickle.dump(graph, f)


def load_graph(filename: str) -> nx.Graph:
    """Loads the graph in the file."""
    with open(filename, 'rb') as f:
        return pickle.load(f)


def build_city_graph(osmnx_graph: OsmnxGraph, buses_graph: BusesGraph) -> CityGraph:
    """Combines the osmnx graph from barcelona and the buses graph from the buses module, joins them using Transbord edges,
    and return the complete city graph from barcelona."""

    street_graph = build_street_graph(osmnx_graph)

    city_graph = street_graph.to_directed()
    city_graph.add_edges_from(buses_graph.edges(data=True))

    X = [parada.coord.x for parada in buses_graph.nodes]
    Y = [parada.coord.y for parada in buses_graph.nodes]

    nearest_nodes, nearest_dist = ox.distance.nearest_nodes(
        osmnx_graph, X, Y, return_dist=True)

    for id, dist, parada in zip(nearest_nodes, nearest_dist, buses_graph.nodes):
        cruilla = Cruilla(
            id, Coord(osmnx_graph.nodes[id]['x'], osmnx_graph.nodes[id]['y']))
        multiparada = MultiParada(parada.id, parada.coord, nom=parada.nom)
        carrer = Carrer(
            dist, [cruilla.coord, multiparada.coord], nom=parada.nom)
        edges = [(cruilla, multiparada), (multiparada, cruilla)]
        city_graph.add_edges_from(
            edges, time=dist/WALKING_SPEED, color=(127, 127, 127), info=carrer)

        transbord = Transbord(0, [], nom=parada.nom)
        city_graph.add_edge(
            multiparada, parada, time=BUS_WAITING_TIME, color=(0, 0, 0), info=transbord)
        city_graph.add_edge(parada, multiparada, time=0,
                            color=(0, 0, 0), info=transbord)

    return city_graph


def build_street_graph(osmnx_graph: OsmnxGraph) -> StreetGraph:
    """Returns a undirected simple graph with a Cruilla in each of the nodes of the osmnx graph."""

    street_graph = StreetGraph()

    for id1, id2, attrs in osmnx_graph.edges(data=True):
        node1 = osmnx_graph.nodes[id1]
        node2 = osmnx_graph.nodes[id2]

        cruilla1 = Cruilla(id1, Coord(node1['x'], node1['y']))
        cruilla2 = Cruilla(id2, Coord(node2['x'], node2['y']))

        dist = attrs['length']
        if 'name' not in attrs:
            name = ''
        elif isinstance(attrs['name'], str):
            name = attrs['name']
        else:
            name = ', '.join(attrs['name'])

        carrer = Carrer(dist, [cruilla1.coord, cruilla2.coord], nom=name)
        street_graph.add_edge(cruilla1, cruilla2, time=dist/WALKING_SPEED,
                              color=(127, 127, 127), info=carrer)

    return street_graph


def build_and_save_graphs() -> None:
    """Builds and saves all the graphs (osmnx, buses and barcelona) if they don't exist already."""

    def file_exists_and_not_empty(filename: str) -> bool:
        """Checks if a file exists and it is not empty."""
        return os.path.exists(filename) and os.path.getsize(filename) > 0

    if not file_exists_and_not_empty('osmnx.grf'):
        print("S'està creant el graf osmnx.")
        save_graph(get_osmnx_graph(), 'osmnx.grf')

    if not file_exists_and_not_empty('buses.grf'):
        print("S'està creant el graf de busos.")
        save_graph(get_buses_graph(), 'buses.grf')

    if not file_exists_and_not_empty('barcelona.grf'):
        city_graph = build_city_graph(load_graph(
            'osmnx.grf'), load_graph('buses.grf'))
        save_graph(city_graph, 'barcelona.grf')


def show(graph: nx.Graph) -> None:
    """Shows the graph's nodes and edges in a pop-up window."""
    positions = {node: node.coord.xy for node in graph.nodes}
    colors = [[c/255 for c in col]
              for col in nx.get_edge_attributes(graph, 'color').values()]

    nx.draw(graph, pos=positions, node_size=0, edge_color=colors)
    plt.show()


def plot(graph: nx.Graph, nom_fitxer: str) -> None:
    """Saves an image of the graph with the map of the city in the background."""
    m = staticmap.StaticMap(800, 600)

    for _, _, attrs in graph.edges(data=True):
        if attrs['info'].coord_list == []:
            continue
        color = '#%02x%02x%02x' % attrs['color']
        coords = [coord.xy for coord in attrs['info'].coord_list]
        m.add_line(staticmap.Line(coords, color, 1))

    image = m.render()
    image.save(nom_fitxer)


def find_path(osmnx_graph: OsmnxGraph, city_graph: CityGraph, src: Coord, dst: Coord) -> Path:
    """Returns the shotest path to go from a source point to a destination point."""

    (src_id, dst_id), (dist_start, dist_end) = ox.distance.nearest_nodes(
        osmnx_graph, [src.x, dst.x], [src.y, dst.y], return_dist=True)

    src_node = osmnx_graph.nodes[src_id]
    src_cruilla = Cruilla(src_id, Coord(src_node['x'], src_node['y']))

    dst_node = osmnx_graph.nodes[dst_id]
    dst_cruilla = Cruilla(dst_id, Coord(dst_node['x'], dst_node['y']))

    distance = dist_start + dist_end
    walking_dist = distance
    time = distance / WALKING_SPEED

    route = ox.distance.shortest_path(
        city_graph, src_cruilla, dst_cruilla, cpus=None, weight='time')

    for node1, node2 in pairwise(route):
        edge = city_graph[node1][node2]
        time += edge['time']
        distance += edge['info'].distancia

        if isinstance(edge['info'], Carrer):
            walking_dist += edge['info'].distancia

    duration = dt.timedelta(0, time)
    return Path(src, dst, route, duration, distance, walking_dist)


def show_path(city_graph: CityGraph, p: Path) -> None:
    """Shows the path to follow to reach destination interactively in a window."""
    path_graph = city_graph.subgraph(p.route)
    show(path_graph)


def plot_path(city_graph: CityGraph, p: Path, filename: str) -> None:
    """Shows as a picture the route in the file filename."""
    m = staticmap.StaticMap(800, 600)
    bus_colors = get_color()

    m.add_marker(staticmap.CircleMarker(p.source.xy, 'green', 10))
    m.add_marker(staticmap.CircleMarker(p.destination.xy, 'black', 10))

    for node1, node2 in pairwise(p.route):
        info = city_graph.get_edge_data(node1, node2)['info']

        if isinstance(info, Transbord):
            bus_color = next(bus_colors)
            m.add_marker(staticmap.CircleMarker(node1.coord.xy, 'gray', 6))

        else:
            if isinstance(info, Bus):
                color = bus_color
            else:
                color = 'deepskyblue'

            coords = [coord.xy for coord in info.coord_list]
            m.add_line(staticmap.Line(coords, color, 4))

    image = m.render()
    image.save(filename)


def get_color() -> Iterable[str | None]:
    """Returns a different color to represent the bus route. If there is a bus transfer, it changes the color."""
    while True:
        yield 'red'
        yield None
        yield 'orange'
        yield None


def obtenir_indicacions(city_graph: CityGraph, path: Path, dest_name: str = 'casa', hora_inici: dt.datetime | None = None, hora_fi: dt.datetime | None = None, anada=True) -> str:
    """Returns the indications that the person should follow in order to arrive to the path destination from the path origin.
    Also returns useful information about the journey."""
    message = ''
    carrer_previ = ''

    for node1, node2 in pairwise(path.route):
        info = city_graph.get_edge_data(node1, node2)['info']

        if isinstance(info, Carrer) and carrer_previ != info.nom and info.nom != '':
            message += "Camina pel carrer " + info.nom + '\n'
            carrer_previ = info.nom

        elif isinstance(info, Transbord):
            if isinstance(node1, Parada):  # acabes de baixar del bus
                message += "Baixa del bus a la parada " + node1.nom + '\n'
            else:
                message += "Agafa la línia " + node2.linia + " a la parada " + node2.nom + '\n'

    message += "Ja has arribat a " + dest_name + '!\n\n'
    message += "Distancia total: " + \
        str(round(path.distance)) + "m, Distancia caminant: " + \
        str(round(path.walking_distance)) + "m" + '\n'
    message += "Temps total de trajecte: " + \
        get_time(dt.datetime(1, 1, 1) + path.duration) + '\n\n'

    if anada:
        message += "Si surts ara, arribaràs a les: " + \
            get_time(dt.datetime.now() + path.duration) + '\n'
        message += "Hora límit de sortida per arribar a temps: " + \
            get_time(hora_inici - path.duration) + '\n'
        message += "La durada de la pel·lícula és de " + \
            get_time(hora_fi - hora_inici + dt.datetime(1, 1, 1)) + '\n'
    else:
        message += "La pel·lícula acabarà a les " + get_time(hora_fi) + '\n'
        message += "Si marxes a l'acabar, tornarás aquí a les " + \
            get_time(hora_fi + path.duration)

    return message


def get_time(datetime: dt.datetime) -> str:
    """Returns the time of the datetime in fortmat HH:MM."""
    return '{:%H:%M}'.format(datetime)
