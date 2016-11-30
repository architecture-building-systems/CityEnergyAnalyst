"""
===========================
embodied energy and related grey emissions model algorithm
===========================
J. Fonseca  script development          26.08.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox
J. Fonseca  new development             13.04.16

"""
from __future__ import division

import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as gpdf

import cea.globalvar
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def lca_embodied(year_to_calculate, locator, gv):
    """
    algorithm to calculate the embodied energy and grey energy of buildings
    according to the method of Fonseca et al 2015. CISBAT 2015. and Thoma et al
    2014. CUI 2014.

    Parameters
    ----------

    :param year_to_calculate:  year between 1900 and 2100 indicating when embodied energy is evaluated
        to account for emissions already offset from building construction
        and retrofits more than 60 years ago.
    :type year_to_calculate: int

    :param locator: an instance of InputLocator set to the scenario
    :type locator: inputlocator.InputLocator


    Files read / written from InputLocator:

    get_building_architecture
    get_building_occupancy
    get_building_age
    get_building_geometry
    get_archetypes_embodied_energy
    get_archetypes_embodied_emissions

    path_LCA_embodied_energy:
        path to database of archetypes embodied energy file
        Archetypes_embodied_energy.csv
    path_LCA_embodied_emissions:
        path to database of archetypes grey emissions file
        Archetypes_embodied_emissions.csv
    path_age_shp: string
        path to building_age.shp
    path_occupancy_shp:
        path to building_occupancyshp
    path_geometry_shp:
        path to building_geometrys.hp
    path_architecture_shp:
        path to building_architecture.shp
    path_results : string
        path to demand results folder emissions

    Returns
    -------
    Total_LCA_embodied: .csv
        csv file of yearly primary energy and grey emissions per building stored in path_results
    """

    # local variables
    architecture_df = gpdf.from_file(locator.get_building_architecture()).drop('geometry', axis=1)
    prop_occupancy_df = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1)
    occupancy_df = pd.DataFrame(prop_occupancy_df.loc[:, (prop_occupancy_df != 0).any(axis=0)])
    age_df = gpdf.from_file(locator.get_building_age()).drop('geometry', axis=1)
    geometry_df = gpdf.from_file(locator.get_building_geometry())
    geometry_df['footprint'] = geometry_df.area
    geometry_df['perimeter'] = geometry_df.length
    geometry_df = geometry_df.drop('geometry', axis=1)

    # get list of uses
    list_uses = list(occupancy_df.drop({'PFloor', 'Name'}, axis=1).columns)

    # define main use:
    occupancy_df['mainuse'] = calc_mainuse(occupancy_df, list_uses)

    # DataFrame with joined data for categories
    cat_df = occupancy_df.merge(age_df, on='Name').merge(geometry_df, on='Name').merge(architecture_df, on='Name')

    # calculate building geometry
    cat_df['windows_ag'] = cat_df['win_wall'] * cat_df['perimeter'] * (cat_df['height_ag'] * cat_df['PFloor'])
    cat_df['area_walls_ext_ag'] = cat_df['perimeter'] * (cat_df['height_ag'] * cat_df['PFloor']) - cat_df['windows_ag']
    cat_df['area_walls_ext_bg'] = cat_df['perimeter'] * cat_df['height_bg']
    cat_df['floor_area_ag'] = cat_df['footprint'] * cat_df['floors_ag']
    cat_df['floor_area_bg'] = cat_df['footprint'] * cat_df['floors_bg']
    cat_df['total_area'] = cat_df['floor_area_ag'] + cat_df['floor_area_bg']

    # get categories for each year of construction/retrofit
    cat_df['cat_built'] = cat_df.apply(lambda x: calc_category_construction(x['mainuse'], x['built']), axis=1)
    retro_cat = ['envelope', 'roof', 'windows', 'partitions', 'basement', 'HVAC']
    for cat in retro_cat:
        cat_df['cat_' + cat] = cat_df.apply(lambda x: calc_category_retrofit(x['mainuse'], x[cat]), axis=1)

    # calculate contributions to embodied energy and emissions
    result_energy = calculate_contributions('EMBODIED_ENERGY', cat_df, gv, locator, year_to_calculate,
                                            total_column='GEN_GJ', specific_column='GEN_MJm2')
    result_emissions = calculate_contributions('EMBODIED_EMISSIONS', cat_df, gv, locator, year_to_calculate,
                                               total_column='CO2_ton', specific_column='CO2_kgm2')

    fields_to_plot = ['Name', 'GFA_m2', 'E_nre_pen_GJ', 'E_nre_pen_MJm2', 'E_ghg_ton', 'E_ghg_kgm2']
    pd.DataFrame(
        {'Name': result_energy.Name, 'E_nre_pen_GJ': result_energy.GEN_GJ, 'E_nre_pen_MJm2': result_energy.GEN_MJm2,
         'E_ghg_ton': result_emissions.CO2_ton, 'E_ghg_kgm2': result_emissions.CO2_kgm2,
         'GFA_m2': result_energy.total_area}).to_csv(locator.get_lca_embodied(),
                                                     columns=fields_to_plot, index=False, float_format='%.2f')
    print('done!')


def calculate_contributions(archetype, cat_df, gv, locator, year_to_calculate, total_column, specific_column):
    """calculate contributions to embodied energy and emissions"""
    database_df = pd.read_excel(locator.get_archetypes_properties(), archetype)
    # merge databases according to category
    built_df = cat_df.merge(database_df, left_on='cat_built', right_on='Code')
    envelope_df = cat_df.merge(database_df, left_on='cat_envelope', right_on='Code')
    roof_df = cat_df.merge(database_df, left_on='cat_roof', right_on='Code')
    windows_df = cat_df.merge(database_df, left_on='cat_windows', right_on='Code')
    partitions_df = cat_df.merge(database_df, left_on='cat_partitions', right_on='Code')
    basement_df = cat_df.merge(database_df, left_on='cat_basement', right_on='Code')
    HVAC_df = cat_df.merge(database_df, left_on='cat_HVAC', right_on='Code')
    # contributions due to construction
    built_df['delta_year'] = year_to_calculate - built_df['built']
    built_df['confirm'] = built_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_materials), axis=1)
    built_df['contrib'] = (((built_df['Wall_ext_ag'] * built_df['area_walls_ext_ag']) +
                            (built_df['Roof'] * built_df['footprint']) +
                            (built_df['windows_ag'] * built_df['Win_ext']) +
                            (built_df['floor_area_ag'] * built_df['Floor_int'] +
                             built_df['floor_area_ag'] * built_df['Wall_int_sup'] * gv.fwratio +
                             built_df['footprint'] * built_df['Wall_int_nosup'] * gv.fwratio) +
                            (basement_df['footprint'] * basement_df['Floor_g'] +
                             basement_df['Wall_ext_bg'] * basement_df['area_walls_ext_bg']) +
                            (built_df['footprint'] * built_df['Excavation'])) / gv.sl_materials + \
                           ((HVAC_df['floor_area_ag'] + HVAC_df['footprint']) * HVAC_df[
                               'Services']) / gv.sl_services) * built_df['confirm']
    # contributions due to envelope retrofit
    envelope_df['delta_year'] = year_to_calculate - envelope_df['envelope']
    envelope_df['confirm'] = envelope_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_materials), axis=1)
    envelope_df['contrib'] = (envelope_df['Wall_ext_ag'] * envelope_df['area_walls_ext_ag']) * envelope_df[
        'confirm'] / (gv.sl_materials)
    # contributions due to roof retrofit
    roof_df['delta_year'] = year_to_calculate - roof_df['roof']
    roof_df['confirm'] = roof_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_materials), axis=1)
    roof_df['contrib'] = roof_df['Roof'] * roof_df['footprint'] * roof_df['confirm'] / gv.sl_materials
    # contributions due to windows retrofit
    windows_df['delta_year'] = year_to_calculate - windows_df['windows']
    windows_df['confirm'] = windows_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_materials), axis=1)
    windows_df['contrib'] = windows_df['windows_ag'] * windows_df['Win_ext'] * windows_df[
        'confirm'] / gv.sl_materials
    # contributions due to partitions retrofit
    partitions_df['delta_year'] = year_to_calculate - partitions_df['partitions']
    partitions_df['confirm'] = partitions_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_materials),
                                                   axis=1)
    partitions_df['contrib'] = (partitions_df['floor_area_ag'] * partitions_df['Floor_int'] +
                                partitions_df['floor_area_ag'] * partitions_df['Wall_int_sup'] * gv.fwratio +
                                partitions_df['footprint'] * partitions_df['Wall_int_nosup'] * gv.fwratio) * \
                               partitions_df['confirm'] / gv.sl_materials
    # contributions due to basement_df
    basement_df['delta_year'] = year_to_calculate - basement_df['basement']
    basement_df['confirm'] = basement_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_materials), axis=1)
    basement_df['contrib'] = ((basement_df['footprint'] * basement_df['Floor_g'] +
                               basement_df['Wall_ext_bg'] * basement_df['area_walls_ext_bg'])
                              * basement_df['confirm'] / gv.sl_materials)
    # contributions due to HVAC_df
    HVAC_df['delta_year'] = year_to_calculate - HVAC_df['HVAC']
    HVAC_df['confirm'] = HVAC_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_services), axis=1)
    HVAC_df['contrib'] = ((HVAC_df['floor_area_ag'] + HVAC_df['footprint']) * HVAC_df['Services']) * HVAC_df[
        'confirm'] / gv.sl_services

    built_df[total_column] = (HVAC_df['contrib'] + basement_df['contrib'] + partitions_df['contrib']
                              + built_df['contrib'] + roof_df['contrib'] + envelope_df['contrib']
                              + windows_df['contrib']) / 1000
    built_df[specific_column] = built_df[total_column] * 1000 / built_df['total_area']

    result = built_df[['Name', total_column, specific_column, 'total_area']]
    return result


def calc_if_existing(x, y):
    if x <= y:
        return 1
    else:
        return 0


def calc_category_construction(a, x):
    if 0 <= x <= 1920:
        # Database['Qh'] = Database.ADMIN.value * Model.
        result = '1'
    elif 1920 < x <= 1970:
        result = '2'
    elif 1970 < x <= 1980:
        result = '3'
    elif 1980 < x <= 2000:
        result = '4'
    elif 2000 < x <= 2020:
        result = '5'
    else:
        result = '6'

    category = a + result
    return category


def calc_category_retrofit(a, y):
    if 0 <= y <= 1920:
        result = '7'
    elif 1920 < y <= 1970:
        result = '8'
    elif 1970 < y <= 1980:
        result = '9'
    elif 1980 < y <= 2000:
        result = '10'
    elif 2000 < y <= 2020:
        result = '11'
    else:
        result = '12'

    category = a + result
    return category


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


def run_as_script(scenario_path=None, year_to_calculate=2050):
    gv = cea.globalvar.GlobalVariables()
    if not scenario_path:
        scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    lca_embodied(locator=locator, year_to_calculate=year_to_calculate, gv=gv)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    parser.add_argument('-y', '--year', default=2020, help='Year to calculate')
    args = parser.parse_args()
    run_as_script(scenario_path=args.scenario, year_to_calculate=args.year)
