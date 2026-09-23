"""
This script exchanges one or multiple geometries between zone and surroundings.
"""

import math
import os
from typing import Union

import numpy as np
import osmnx
from geopandas import GeoDataFrame as Gdf
from shapely import Polygon
import pandas as pd

import cea.config
import cea.inputlocator
from cea.datamanagement.databases_verification import COLUMNS_ZONE, MINIMUM_STOREY_HEIGHT_M
from cea.datamanagement.utils import VOID_HEIGHT_COLUMN
from cea.demand import constants
from cea.datamanagement.constants import OSM_BUILDING_CATEGORIES, OTHER_OSM_CATEGORIES_UNCONDITIONED, GRID_SIZE_M, EARTH_RADIUS_M
from cea.utilities.standardize_coordinates import get_projected_coordinate_system, get_geographic_coordinate_system, \
    get_lat_lon_projected_shapefile

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2026, uuen Company"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "shi@uuen.cloud"
__status__ = "Production"
