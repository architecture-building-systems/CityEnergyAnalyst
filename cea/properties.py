"""
===========================
building properties algorithm
===========================
File history and credits:
J. A. Fonseca  script development          22.03.15

"""
from __future__ import division
import pandas as pd
import os
import numpy as np
import globalvar
from geopandas import GeoDataFrame as gpdf
import inputlocator

gv = globalvar.GlobalVariables()


def properties(locator, prop_thermal_flag, prop_architecture_flag,
               prop_hvac_flag, gv):
    """
    algorithm to query building properties from statistical database
    Archetypes_HVAC_properties.csv. for more info check the integrated demand
    model of Fonseca et al. 2015. Appl. energy.

    Parameters
    ----------
    :param InputLocator locator: an InputLocator instance set to the scenario to work on
    :param boolean prop_thermal_flag: if True, get properties about thermal properties of the building envelope.
    :param boolean prop_architecture_flag: if True, get properties about the construction and architecture.
    :param boolean prop_hvac_flag: if True, get properties about types of HVAC systems, otherwise False.
    :param GlobalVariables gv: an instance of globalvar.GlobalVariables with the constants  to use
        (like `list_uses` etc.)

    Side effects:
    -------------

    The following files are created by this script, depending on which flags were set:

    - building_HVAC: .shp
        describes the queried properties of HVAC systems.

    - building_architecture: .shp
        describes the queried properties of architectural features

    - building_thermal: .shp
        describes the queried thermal properties of buildings
    """
    # local variables:
    archetypes = pd.read_csv(locator.get_archetypes_hvac_properties())
    list_uses = gv.list_uses
    building_occupancy_df = gpdf.from_file(locator.get_building_occupancy())
    building_age_df = gpdf.from_file(locator.get_building_age())

    # prepare shapefile to store results (a shapefile with only names of buildings
    fields_drop = ['envelope', 'roof', 'windows', 'partitions', 'basement', 'HVAC', 'built']  # FIXME: this hardcodes the field names!!
    names_shp = gpdf.from_file(locator.get_building_age()).drop(fields_drop, axis=1)

    # define main use:
    building_occupancy_df['mainuse'] = calc_mainuse(building_occupancy_df, list_uses)

    # dataframe with jonned data for categories
    categories_df = building_occupancy_df.merge(building_age_df, on='Name')

    # get properties about thermal properties of the building envelope
    if prop_thermal_flag:


        categories_df['cat_wall'] = categories_df.apply(lambda x: calc_category(x['mainuse'],
                                                                                          x['built'],
                                                                                          x['envelope']),axis=1)
        categories_df['cat_roof'] = categories_df.apply(lambda x: calc_category(x['mainuse'],
                                                                                      x['built'],
                                                                                      x['roof']),axis=1)
        categories_df['cat_windows'] = categories_df.apply(lambda x: calc_category(x['mainuse'],
                                                                                         x['built'],
                                                                                         x['windows']),axis=1)
        categories_df['cat_basement'] = categories_df.apply(lambda x: calc_category(x['mainuse'],
                                                                                          x['built'],
                                                                                          x['basement']),axis=1)

        # define U-values, construction
        df = categories_df.merge(archetypes, left_on='cat_wall', right_on='Code')
        df2 = categories_df.merge(archetypes, left_on='cat_roof', right_on='Code')
        df3 = categories_df.merge(archetypes, left_on='cat_windows', right_on='Code')
        df4 = categories_df.merge(archetypes, left_on='cat_basement', right_on='Code')
        fields = ['Name','U_wall','th_mass','Es','Hs']
        fields2 = ['Name','U_roof']
        fields3 = ['Name','U_win']
        fields4 = ['Name','U_base']
        prop_thermal_df = df[fields].merge(df2[fields2], on='Name').merge(df3[fields3],on='Name').merge(df4[fields4],on='Name')

        # write to shapefile
        prop_thermal_df_merged = names_shp.merge(prop_thermal_df, on="Name")
        fields = ['U_base', 'U_roof', 'U_win', 'U_wall', 'th_mass', 'Es', 'Hs']
        prop_thermal_shp = names_shp.copy()
        for field in fields:
            prop_thermal_shp[field] = prop_thermal_df_merged[field].copy()
        prop_thermal_shp.to_file(locator.get_building_thermal())

    # get properties about the construction and architecture
    if prop_architecture_flag:

        categories_df['cat_architecture'] = categories_df.apply(lambda x: calc_category(x['mainuse'], x['built'],  x['envelope']),axis=1)

        # define architectural characteristics
        prop_architecture_df = categories_df.merge(archetypes, left_on='cat_architecture', right_on='Code')

        # write to shapefile
        prop_architecture_df_merged = names_shp.merge(prop_architecture_df, on="Name")
        fields = ['win_wall','type_shade']
        prop_architecture_shp = names_shp.copy()
        for field in fields:
            prop_architecture_shp[field] = prop_architecture_df_merged[field].copy()
        prop_architecture_shp.to_file(locator.get_building_architecture())


    # get properties about types of HVAC systems
    if prop_hvac_flag:

        categories_df['cat_HVAC'] = categories_df.apply(lambda x: calc_category(x['mainuse'], x['built'],  x['HVAC']),axis=1)

        # define HVAC systems types
        prop_HVAC_df = categories_df.merge(archetypes, left_on='cat_HVAC', right_on='Code')

        # write to shapefile
        prop_HVAC_df_merged = names_shp.merge(prop_HVAC_df, on="Name")
        fields = ['type_cs', 'type_hs', 'type_dhw', 'type_ctrl']
        prop_HVAC_shp = names_shp.copy()
        for field in fields:
            prop_HVAC_shp[field] = prop_HVAC_df_merged[field].copy()
        prop_HVAC_shp.to_file(locator.get_building_hvac())

def calc_mainuse(uses_df, uses):

    databaseclean = uses_df[uses].transpose()
    array_min = np.array(databaseclean[databaseclean[:] > 0].idxmin(skipna=True), dtype='S10')
    array_max = np.array(databaseclean[databaseclean[:] > 0].idxmax(skipna=True), dtype='S10')
    mainuse = np.array(map(calc_comparison, array_min, array_max))

    return mainuse

def calc_comparison(array_min, array_max):
    if array_max == 'DEPO':
        if array_min != 'DEPO':
            array_max = array_min
    return array_max

def calc_category(a, x, y):
    if 0 < x <= 1920:
        result = '1'
    elif x > 1920 and x <= 1970:
        result = '2'
    elif x > 1970 and x <= 1980:
        result = '3'
    elif x > 1980 and x <= 2000:
        result = '4'
    elif x > 2000 and x <= 2020:
        result = '5'
    elif x > 2020:
        result = '6'

    if 0 < y <= 1920:
        result = '7'
    elif 1920 < y <= 1970:
        result = '8'
    elif 1970 < y <= 1980:
        result = '9'
    elif 1980 < y <= 2000:
        result = '10'
    elif 2000 < y <= 2020:
        result = '11'
    elif y > 2020:
        result = '12'

    category = a+result
    return category

def test_properties():
    """
    Run the properties script with input from the reference case and compare the results. This ensures that changes
    made to this script (e.g. refactorings) do not stop the script from working and also that the results stay the same.
    """
    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    properties(locator=locator, prop_thermal_flag=True, prop_architecture_flag=True, prop_hvac_flag=True, gv=gv)
    print 'test_properties() succeeded'


def is_dataframe_equal(dfa, dfb):
    comparison = dfa == dfb
    return all((comparison[c].all() for c in comparison.columns))

if __name__ == '__main__':
    test_properties()
