# -*- coding: utf-8 -*-
"""
===========================
algorithms for manipulation of building geometry
===========================

"""

from __future__ import division
import pandas as pd
import os


__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


"""
=========================================
Windows
=========================================
"""

def load_windows(locator):


    path = locator.get_solar_radiation_folder()
    bui_list = pd.read_csv(os.path.join(path, 'properties_surfaces.csv'))['Name']
    first = True
    for bui in bui_list:
        df_window_path = os.path.join(path, bui+'_window_props.csv')
        if first == True:
            df_window = pd.read_csv(df_window_path)
            first = False
        else:
            df_window = pd.concat((df_window, pd.read_csv(df_window_path)))

    return df_window

"""
=========================================
surfaces for ventilation
=========================================
"""

def get_building_geometry_ventilation(gdf_building_geometry):
    """

    Parameters
    ----------
    gdf_building_geometry : GeoDataFrame contains single building

    Returns
    -------
    building properties for natural ventilation calculation
    """

    # TODO: get real slope of roof in the future
    slope_roof_default = 0

    area_facade_zone = gdf_building_geometry['perimeter'] * gdf_building_geometry['height_ag']
    area_roof_zone = gdf_building_geometry['footprint']
    height_zone = gdf_building_geometry['height_ag']
    slope_roof = slope_roof_default

    return area_facade_zone, area_roof_zone, height_zone, slope_roof
