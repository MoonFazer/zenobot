"""
Manages connections with various endpoints - indexes in a dictionary so
duplicate connections are not made
"""

from .mongo import Mongo

conn_map = {
    "mongo": Mongo,
    # "ftx": FTX,
}

global connections
connections = {}


def get_connections(name, *args):
    """adds connections to dictionary and updates if connection is lost"""

    if name not in connections:
        print("NEW CONNECTION")
        connections[name] = conn_map[name](*args)

    return connections[name]
