"""Misc. functions."""
import time


def create_node_name():
    """Creates a UNIQUE (time in seconds since the Epoch) node name for the current account."""
    return int(round(time.time()))
