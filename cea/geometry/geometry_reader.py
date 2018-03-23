# -*- coding: utf-8 -*-
"""
algorithms for manipulation of building geometry
"""

from __future__ import division
import pandas as pd

__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# Windows

def create_windows(df_prop_surfaces, gdf_building_architecture):
    """
    Creates windows on exposed building surfaces according to building win-wall-ratio

    :param df_prop_surfaces: DataFrame containing all exposed building surfaces (this is the `properties_surfaces.csv`
        file from the radiation calculation)
    :type df_prop_surfaces: DataFrame

    :param gdf_building_architecture: GeoDataFrame containing building architecture - this is the `architecture.shp`
        file from the scenario input, containing the `win_wall` column with the window to wall ratio.
    :type gdf_building_architecture: GeoDataFrame

    :returns: DataFrame containing all windows of all buildings
    :rtype: DataFrame

    Sample rows of output:::

               angle_window  area_window  height_window_above_ground  \
        0            90     1.910858                         1.5
        1            90     2.276739                         1.5
        2            90     2.276739                         4.5
        3            90     2.276739                         7.5
        4            90     2.276739                        10.5

           height_window_in_zone name_building  orientation_window
        0                    1.5       B140589                   0
        1                    1.5       B140590                 180
        2                    4.5       B140590                 180
        3                    7.5       B140590                 180
        4                   10.5       B140590                 180

        [5 rows x 6 columns]
    """
    # TODO: documentation

    # sort dataframe for name of building for default orientation generation
    # FIXME remove this in the future
    if pd.__version__ == '0.16.1':
        # maintain compatibility with ArcGIS 10.4 pandas
        df_prop_surfaces.sort(['Name'])
    else:
        df_prop_surfaces.sort_values('Name')
    # default values
    # FIXME use real window angle in the future
    angle_window_default = 90  # (deg), 90° = vertical, 0° = horizontal

    # read relevant columns from dataframe
    free_height = df_prop_surfaces['Freeheight']
    height_ag = df_prop_surfaces['height_ag']
    length_shape = df_prop_surfaces['Shape_Leng']
    name = df_prop_surfaces['Name']

    # calculate number of exposed floors per facade
    num_floors_free_height = (free_height / 3).astype('int')  # floor height is 3 m
    num_windows = num_floors_free_height.sum()  # total number of windows in model, not used

    # *** experiment with structured array
    # initialize numpy structured array for results
    # array_windows = np.zeros(num_windows,
    #                          dtype={'names':['name_building','area_window','height_window_above_ground',
    #                                          'orientation_window','angle_window','height_window_in_zone'],
    #                                 'formats':['S10','f2','f2','f2','f2','f2']})

    # initialize lists for results
    col_name_building = []
    col_area_window = []
    col_height_window_above_ground = []
    col_orientation_window = []
    col_angle_window = []
    col_height_window_in_zone = []

    # for all vertical exposed facades
    for i in range(name.size):

        # generate orientation
        # TODO in the future get real orientation
        # FIXME
        if i % 4 == 0:
            orientation_default = 0
        elif i % 4 == 1:
            orientation_default = 180
        elif i % 4 == 2:
            orientation_default = 90
        elif i % 4 == 3:
            orientation_default = 270
        else:
            orientation_default = 0

        # get window-wall ratio of building from architecture geodataframe
        win_wall_ratio = gdf_building_architecture.ix[name[i]]['win_wall']
        win_op_ratio = gdf_building_architecture.ix[name[i]]['win_op']

        # for all levels in a facade
        for j in range(num_floors_free_height[i]):
            window_area = length_shape[
                              i] * 3 * win_wall_ratio * win_op_ratio  # 3m = average floor height
            window_height_above_ground = height_ag[i] - free_height[
                i] + j * 3 + 1.5  # 1.5m = window is placed in the middle of the floor height # TODO: make heights dynamic
            window_height_in_zone = window_height_above_ground  # for now the building is one ventilation zone

            col_name_building.append(name[i])
            col_area_window.append(window_area)
            col_height_window_above_ground.append(window_height_above_ground)
            col_orientation_window.append(orientation_default)
            col_angle_window.append(angle_window_default)
            col_height_window_in_zone.append(window_height_in_zone)

    # create pandas dataframe with table of all windows
    df_windows = pd.DataFrame({'name_building': col_name_building,
                               'area_window': col_area_window,
                               'height_window_above_ground': col_height_window_above_ground,
                               'orientation_window': col_orientation_window,
                               'angle_window': col_angle_window,
                               'height_window_in_zone': col_height_window_in_zone})

    return df_windows


# surfaces for ventilation

def get_building_geometry_ventilation(gdf_building_geometry):
    """
    :param gdf_building_geometry : GeoDataFrame contains single building

    :returns: building properties for natural ventilation calculation
    """

    # TODO: get real slope of roof in the future
    slope_roof_default = 0

    area_facade_zone = gdf_building_geometry['perimeter'] * gdf_building_geometry['height_ag']
    area_roof_zone = gdf_building_geometry['footprint']
    height_zone = gdf_building_geometry['height_ag']
    slope_roof = slope_roof_default

    return area_facade_zone, area_roof_zone, height_zone, slope_roof

