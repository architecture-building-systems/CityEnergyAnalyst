"""
Embodied energy and related grey emissions model algorithm
"""
from __future__ import division

import os

import numpy as np
from geopandas import GeoDataFrame as Gdf
import pandas as pd

import cea.config
import cea.inputlocator
from cea.constants import SERVICE_LIFE_OF_BUILDINGS, SERVICE_LIFE_OF_TECHNICAL_SYSTEMS, \
    CONVERSION_AREA_TO_FLOOR_AREA_RATIO, EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS
from cea.utilities.dbf import dbf_to_dataframe

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Martin Mosteiro"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def lca_embodied(year_to_calculate, locator):
    """
    Algorithm to calculate the embodied emissions and non-renewable primary energy of buildings according to the method
    of [Fonseca et al., 2015] and [Thoma et al., 2014]. The calculation method assumes a 60 year payoff for the embodied
    energy and emissions of a building, after which both values become zero.

    The results are provided in total as well as per square meter:

    - embodied non-renewable primary energy: E_nre_pen_GJ and E_nre_pen_MJm2
    - embodied greenhouse gas emissions: GHG_sys_embodied_tonCO2 and GHG_sys_embodied_kgCO2m2

    As part of the algorithm, the following files are read from InputLocator:

    - architecture.shp: shapefile with the architecture of each building
        locator.get_building_architecture()
    - occupancy.shp: shapefile with the occupancy types of each building
        locator.get_building_occupancy()
    - age.shp: shapefile with the age and retrofit date of each building
        locator.get_building_age()
    - zone.shp: shapefile with the geometry of each building in the zone of study
        locator.get_zone_geometry()
    - Archetypes_properties: csv file with the database of archetypes including embodied energy and emissions
        locator.get_database_construction_standards()

    As a result, the following file is created:

    - Total_LCA_embodied: .csv
        csv file of yearly primary energy and grey emissions per building stored in locator.get_lca_embodied()

    :param year_to_calculate:  year between 1900 and 2100 indicating when embodied energy is evaluated
        to account for emissions already offset from building construction and retrofits more than 60 years ago.
    :type year_to_calculate: int
    :param locator: an instance of InputLocator set to the scenario
    :type locator: InputLocator
    :returns: This function does not return anything
    :rtype: NoneType

    .. [Fonseca et al., 2015] Fonseca et al. (2015) "Assessing the environmental impact of future urban developments at
        neighborhood scale." CISBAT 2015.
    .. [Thoma et al., 2014] Thoma et al. (2014). "Estimation of base-values for grey energy, primary energy, global
        warming potential (GWP 100A) and Umweltbelastungspunkte (UBP 2006) for Swiss constructions from before 1920
        until today." CUI 2014.


    Files read / written from InputLocator:

    get_building_architecture
    get_building_occupancy
    get_building_age
    get_zone_geometry
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
    """

    # local variables
    age_df = dbf_to_dataframe(locator.get_building_typology())
    architecture_df = dbf_to_dataframe(locator.get_building_architecture())
    geometry_df = Gdf.from_file(locator.get_zone_geometry())
    geometry_df['footprint'] = geometry_df.area
    geometry_df['perimeter'] = geometry_df.length
    geometry_df = geometry_df.drop('geometry', axis=1)

    # local variables
    surface_database_windows = pd.read_excel(locator.get_database_envelope_systems(), "WINDOW")
    surface_database_roof = pd.read_excel(locator.get_database_envelope_systems(), "ROOF")
    surface_database_walls = pd.read_excel(locator.get_database_envelope_systems(), "WALL")
    surface_database_floors = pd.read_excel(locator.get_database_envelope_systems(), "FLOOR")

    # querry data
    df = architecture_df.merge(surface_database_windows, left_on='type_win', right_on='code')
    df2 = architecture_df.merge(surface_database_roof, left_on='type_roof', right_on='code')
    df3 = architecture_df.merge(surface_database_walls, left_on='type_wall', right_on='code')
    df4 = architecture_df.merge(surface_database_floors, left_on='type_floor', right_on='code')
    df5 = architecture_df.merge(surface_database_floors, left_on='type_base', right_on='code')
    df5.rename({'GHG_FLOOR_kgCO2m2': 'GHG_BASE_kgCO2m2'}, inplace=True, axis=1)
    df6 = architecture_df.merge(surface_database_walls, left_on='type_part', right_on='code')
    df6.rename({'GHG_WALL_kgCO2m2': 'GHG_PART_kgCO2m2'}, inplace=True, axis=1)
    fields = ['Name', "GHG_WIN_kgCO2m2"]
    fields2 = ['Name', "GHG_ROOF_kgCO2m2"]
    fields3 = ['Name', "GHG_WALL_kgCO2m2"]
    fields4 = ['Name', "GHG_FLOOR_kgCO2m2"]
    fields5 = ['Name', "GHG_BASE_kgCO2m2"]
    fields6 = ['Name', "GHG_PART_kgCO2m2"]
    surface_properties = df[fields].merge(df2[fields2],
                                          on='Name').merge(df3[fields3],
                                          on='Name').merge(df4[fields4],
                                          on='Name').merge(df5[fields5],
                                          on='Name').merge(df6[fields6], on='Name')

    # DataFrame with joined data for all categories
    data_meged_df = geometry_df.merge(age_df, on='Name').merge(surface_properties, on='Name').merge(architecture_df, on='Name')

    # calculate building geometry
    ## total window area
    average_wwr = [np.mean([a, b, c, d]) for a, b, c, d in
                   zip(data_meged_df['wwr_south'], data_meged_df['wwr_north'], data_meged_df['wwr_west'],
                       data_meged_df['wwr_east'])]

    data_meged_df['windows_ag'] = average_wwr * data_meged_df['perimeter'] * data_meged_df['height_ag']

    ## wall area above ground
    data_meged_df['area_walls_ext_ag'] = data_meged_df['perimeter'] * data_meged_df['height_ag'] - data_meged_df[
        'windows_ag']

    # fix according to the void deck
    data_meged_df['empty_envelope_ratio'] = 1 - (
            (data_meged_df['void_deck'] * (data_meged_df['height_ag'] / data_meged_df['floors_ag'])) / (
            data_meged_df['area_walls_ext_ag'] + data_meged_df['windows_ag']))
    data_meged_df['windows_ag'] = data_meged_df['windows_ag'] * data_meged_df['empty_envelope_ratio']
    data_meged_df['area_walls_ext_ag'] = data_meged_df['area_walls_ext_ag'] * data_meged_df['empty_envelope_ratio']

    ## wall area below ground
    data_meged_df['area_walls_ext_bg'] = data_meged_df['perimeter'] * data_meged_df['height_bg']
    ## floor area above ground
    data_meged_df['floor_area_ag'] = data_meged_df['footprint'] * data_meged_df['floors_ag']
    ## floor area below ground
    data_meged_df['floor_area_bg'] = data_meged_df['footprint'] * data_meged_df['floors_bg']
    ## total floor area
    data_meged_df['GFA_m2'] = data_meged_df['floor_area_ag'] + data_meged_df['floor_area_bg']

    result_emissions = calculate_contributions(data_meged_df,
                                               year_to_calculate)

    # export the results for embodied emissions (E_ghg_) and non-renewable primary energy (E_nre_pen_) for each
    # building, both total (in t CO2-eq. and GJ) and per square meter (in kg CO2-eq./m2 and MJ/m2)
    result_emissions.to_csv(locator.get_lca_embodied(),
                            index=False,
                            float_format='%.2f')
    print('done!')


def calculate_contributions(df, year_to_calculate):
    """
    Calculate the embodied energy/emissions for each building based on their construction year, and the area and 
    renovation year of each building component.

    :param archetype: String that defines whether the 'EMBODIED_ENERGY' or 'EMBODIED_EMISSIONS' are being calculated.
    :type archetype: str
    :param df: DataFrame with joined data of all categories for each building, that is: occupancy, age, geometry,
        architecture, building component area, construction category and renovation category for each building component
    :type df: DataFrame
    :param locator: an InputLocator instance set to the scenario to work on
    :type locator: InputLocator
    :param year_to_calculate: year in which the calculation is done; since the embodied energy and emissions are
        calculated over 60 years, if the year of calculation is more than 60 years after construction, the results
        will be 0
    :type year_to_calculate: int
    :param total_column: label for the column with the total results (e.g., 'GEN_GJ')
    :type total_column: str
    :param specific_column: label for the column with the results per square meter (e.g., 'GEN_MJm2')
    :type specific_column: str

    :return result: DataFrame with the calculation results (i.e., the total and specific embodied energy or emisisons
        for each building)
    :rtype result: DataFrame
    """

    # calculate the embodied energy/emissions due to construction
    total_column = 'saver'
    ## calculate how many years before the calculation year the building was built in
    df['delta_year'] = year_to_calculate - df['YEAR']
    ## if it was built more than 60 years before, the embodied energy/emissions have been "paid off" and are set to 0
    df['confirm'] = df.apply(lambda x: calc_if_existing(x['delta_year'], SERVICE_LIFE_OF_BUILDINGS), axis=1)
    ## if it was built less than 60 years before, the contribution from each building component is calculated
    df[total_column] = ((df['GHG_WALL_kgCO2m2'] * (df['area_walls_ext_ag'] + df['area_walls_ext_bg']) +
                         df['GHG_WIN_kgCO2m2'] * df['windows_ag'] +
                         df['GHG_FLOOR_kgCO2m2'] * df['floor_area_ag'] +
                         df['GHG_BASE_kgCO2m2'] * df['floor_area_bg'] +
                         df['GHG_PART_kgCO2m2'] * (df['floor_area_ag']+df['floor_area_bg']) * CONVERSION_AREA_TO_FLOOR_AREA_RATIO +
                         df['GHG_ROOF_kgCO2m2'] * df['footprint']) / SERVICE_LIFE_OF_BUILDINGS) * df['confirm']

    df[total_column] += (((df['floor_area_ag'] + df['floor_area_bg']) * EMISSIONS_EMBODIED_TECHNICAL_SYSTEMS) / SERVICE_LIFE_OF_TECHNICAL_SYSTEMS) * df['confirm']

    # the total embodied energy/emissions are calculated as a sum of the contributions from construction and retrofits
    df['GHG_sys_embodied_tonCO2'] = df[total_column] / 1000  # kG-CO2 eq to ton
    df['GHG_sys_embodied_kgCO2m2'] = df[total_column] / df['GFA_m2']

    # the total and specific embodied energy/emissions are returned
    result = df[['Name', 'GHG_sys_embodied_tonCO2', 'GHG_sys_embodied_kgCO2m2', 'GFA_m2']]

    return result


def calc_if_existing(x, y):
    """
    Function to verify if one value is greater than or equal to another (then return 1) or not (return 0). This is used
    to verify whether a building's construction or retrofits happened more than 60 years before the year to calculate.
    Since the embodied energy and emissions are calculated over 60 years, if the year of calculation is more than 60 
    years after construction, the results will be 0.
    
    :param x: Number of years since construction/retrofit
    :type x: long
    :param y: Number of years over which the embodied energy/emissions calculation is carried out (i.e., 60)
    :type y: int

    :return value: 1 if x <= y; 0 otherwise
    :rtype value: int

    """

    if x <= y:
        return 1
    else:
        return 0


def calc_code(code1, code2, code3, code4):
    return str(code1) + str(code2) + str(code3) + str(code4)


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    print('Running embodied-energy with scenario = %s' % config.scenario)
    print('Running embodied-energy with year-to-calculate = %s' % config.emissions.year_to_calculate)

    lca_embodied(locator=locator, year_to_calculate=config.emissions.year_to_calculate)


if __name__ == '__main__':
    main(cea.config.Configuration())
