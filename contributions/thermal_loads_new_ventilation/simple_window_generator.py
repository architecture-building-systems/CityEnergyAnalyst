# -*- coding: utf-8 -*-
"""
Simple window generator for buildings consisting of rectangular surfaces with unknown orientation generated with the
radiation script.
In the future windows will be properties of the geometric representation of buildings.

G. Happle

"""

from __future__ import division
import pandas as pd


# for now get geometric properties of exposed facades from the radiation file
def create_windows(df_prop_surfaces, gdf_building_architecture):
    """

    Parameters
    ----------
    df_prop_surfaces
    gdf_building_architecture

    Returns
    -------

    """
    # TODO: documentation

    # sort dataframe for name of building for default orientation generation
    # FIXME remove this in the future
    df_prop_surfaces.sort(['Name'])

    # default values
    # FIXME use real window angle in the future
    angle_window_default = 90  # (deg), 90° = vertical, 0° = horizontal

    # read relevant columns from dataframe
    free_height = df_prop_surfaces['Freeheight']
    height_ag = df_prop_surfaces['height_ag']
    length_shape = df_prop_surfaces['Shape_Leng']
    name = df_prop_surfaces['Name']

    # calculate number of exposed floors per facade
    num_floors_free_height = (free_height / 3).astype('int')  # floor heigth is 3 m
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
        # win_wall_ratio = gdf_building_architecture.loc[gdf_building_architecture['Name'] == name[i]].iloc[0]['win_wall']
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
