"""
===========================
building properties algorithm
===========================
File history and credits:
J. A. Fonseca  script development          22.03.15

"""
from __future__ import division

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as gpdf

from cea import inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def properties(locator, prop_thermal_flag, prop_architecture_flag,
               prop_hvac_flag, prop_comfort_flag, prop_internal_loads_flag, gv):
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

    - building_comfort: .shp
        describes the queried thermal properties of buildings

    - building_loads: .shp
        describes the queried thermal properties of buildings
    """

    # get occupancy and age files
    building_occupancy_df = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1)
    list_uses = list(building_occupancy_df.drop(['PFloor','Name'], axis=1).columns) #parking excluded in U-Values
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
        thermal_DB = get_database(locator.get_archetypes_properties(), 'THERMAL')

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
        df = categories_df.merge(thermal_DB, left_on='cat_wall', right_on='Code')
        df2 = categories_df.merge(thermal_DB, left_on='cat_roof', right_on='Code')
        df3 = categories_df.merge(thermal_DB, left_on='cat_windows', right_on='Code')
        df4 = categories_df.merge(thermal_DB, left_on='cat_basement', right_on='Code')
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
        architecture_DB = get_database(locator.get_archetypes_properties(), 'ARCHITECTURE')

        categories_df['cat_architecture'] = categories_df.apply(lambda x: calc_category(x['mainuse'], x['built'],  x['envelope']),axis=1)

        # define architectural characteristics
        prop_architecture_df = categories_df.merge(architecture_DB, left_on='cat_architecture', right_on='Code')

        # write to shapefile
        prop_architecture_df_merged = names_shp.merge(prop_architecture_df, on="Name")
        fields = ['win_wall', 'type_shade', 'Occ_m2p', 'n50', 'win_op', 'f_cros']  # added ventilation properties to architecture
        prop_architecture_shp = names_shp.copy()
        for field in fields:
            prop_architecture_shp[field] = prop_architecture_df_merged[field].copy()
        prop_architecture_shp.to_file(locator.get_building_architecture())


    # get properties about types of HVAC systems
    if prop_hvac_flag:
        HVAC_DB = get_database(locator.get_archetypes_properties(), 'HVAC')

        categories_df['cat_HVAC'] = categories_df.apply(lambda x: calc_category(x['mainuse'], x['built'],  x['HVAC']),axis=1)

        # define HVAC systems types
        prop_HVAC_df = categories_df.merge(HVAC_DB, left_on='cat_HVAC', right_on='Code')

        # write to shapefile
        prop_HVAC_df_merged = names_shp.merge(prop_HVAC_df, on="Name")
        fields = ['type_cs', 'type_hs', 'type_dhw', 'type_ctrl']
        prop_HVAC_shp = names_shp.copy()
        for field in fields:
            prop_HVAC_shp[field] = prop_HVAC_df_merged[field].copy()
        prop_HVAC_shp.to_file(locator.get_building_hvac())

    if prop_comfort_flag:
        comfort_DB = get_database(locator.get_archetypes_properties(), 'INDOOR_COMFORT')

        # define comfort
        prop_comfort_df = categories_df.merge(comfort_DB, left_on='mainuse', right_on='Code')

        # write to shapefile
        prop_comfort_df_merged = names_shp.merge(prop_comfort_df, on="Name")
        fields = ['Tcs_set_C', 'Ths_set_C','Tcs_setb_C', 'Ths_setb_C', 'Ve_lps']
        prop_comfort_shp = names_shp.copy()
        for field in fields:
            prop_comfort_shp[field] = prop_comfort_df_merged[field].copy()
        prop_comfort_shp.to_file(locator.get_building_comfort())

    if prop_internal_loads_flag:
        internal_DB = get_database(locator.get_archetypes_properties(), 'INTERNAL_LOADS')

        # define comfort
        prop_internal_df = categories_df.merge(internal_DB, left_on='mainuse', right_on='Code')

        # write to shapefile
        prop_internal_df_merged = names_shp.merge(prop_internal_df, on="Name")
        fields = ['Qs_Wp', 'X_ghp', 'Ea_Wm2', 'El_Wm2',	'Epro_Wm2',	'Ere_Wm2', 'Ed_Wm2', 'Vww_lpd',	'Vw_lpd']
        prop_internal_shp = names_shp.copy()
        for field in fields:
            prop_internal_shp[field] = prop_internal_df_merged[field].copy()
        prop_internal_shp.to_file(locator.get_building_internal())


def calc_mainuse(uses_df, uses):

    databaseclean = uses_df[uses].transpose()
    array_min = np.array(databaseclean[databaseclean[:] > 0].idxmin(skipna=True), dtype='S10')
    array_max = np.array(databaseclean[databaseclean[:] > 0].idxmax(skipna=True), dtype='S10')
    mainuse = np.array(map(calc_comparison, array_min, array_max))

    return mainuse


def get_database(path_database, sheet):
    database = pd.read_excel(path_database, sheet)
    return database


def calc_comparison(array_min, array_max):
    if array_max == 'PARKING':
        if array_min != 'PARKING':
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
    import cea.globalvar
    gv = cea.globalvar.GlobalVariables()
    locator = inputlocator.InputLocator(scenario_path=gv.scenario_reference)
    properties(locator=locator, prop_thermal_flag=True, prop_architecture_flag=True, prop_hvac_flag=True,
               prop_comfort_flag=True, prop_internal_loads_flag=True, gv=gv)
    print 'test_properties() succeeded'


def is_dataframe_equal(dfa, dfb):
    comparison = dfa == dfb
    return all((comparison[c].all() for c in comparison.columns))

if __name__ == '__main__':
    test_properties()
