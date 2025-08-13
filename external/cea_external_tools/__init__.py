# TODO: Add functions to help fetch external tools

__version__ = "0.1.0"


import os

def get_bin_path() -> str:
    """
    Returns the path to the external tools binary directory.
    This is typically where compiled C++ tools like DAYSIM and CRAX are located.
    """

    return os.path.join(os.path.dirname(__file__), "bin")
