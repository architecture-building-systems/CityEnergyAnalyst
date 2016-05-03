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
import pandas as pd
import numpy as np
import os
import globalvar
import inputlocator
from geopandas import GeoDataFrame as gpdf

gv = globalvar.GlobalVariables()


def lca_embodied(yearcalc, locator, gv):
    """
    algorithm to calculate the embodied energy and grey energy of buildings
    according to the method of Fonseca et al 2015. CISBAT 2015. and Thoma et al
    2014. CUI 2014.

    Parameters
    ----------

    :param yearcalc:  year between 1900 and 2100 indicating when embodied energy is evaluated
        to account for emissions already offset from building construction
        and retrofits more than 60 years ago.
    :type yearcalc: int

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

    # localvariables
    list_uses = gv.list_uses
    architecture_df = gpdf.from_file(locator.get_building_architecture()).drop('geometry', axis=1)
    occupancy_df = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1)
    age_df = gpdf.from_file(locator.get_building_age()).drop('geometry', axis=1)
    geometry_df = gpdf.from_file(locator.get_building_geometry())
    geometry_df['footprint'] = geometry_df.area
    geometry_df['perimeter'] = geometry_df.length
    geometry_df = geometry_df.drop('geometry', axis=1)

    # define main use:
    occupancy_df['mainuse'] = calc_mainuse(occupancy_df, list_uses)

    # dataframe with jonned data for categories
    cat_df = occupancy_df.merge(age_df,on='Name').merge(geometry_df,on='Name').merge(architecture_df,on='Name')

    # calculate building geometry
    cat_df['windows_ag'] = cat_df['win_wall']*cat_df['perimeter']*cat_df['height_ag']
    cat_df['area_walls_ext_ag'] = cat_df['perimeter']*cat_df['height_ag'] - cat_df['windows_ag']
    cat_df['area_walls_ext_bg'] = cat_df['perimeter'] * cat_df['height_bg']
    cat_df['floor_area_ag'] = cat_df['footprint'] * cat_df['floors_ag']
    cat_df['floor_area_bg'] = cat_df['footprint'] * cat_df['floors_bg']
    cat_df['total_area'] = cat_df['floor_area_ag'] + cat_df['floor_area_bg']

    # get categories for each year of construction/retrofit
    cat_df['cat_built'] = cat_df.apply(lambda x: calc_category_construction(x['mainuse'],x['built']), axis=1)
    retro_cat = ['envelope', 'roof', 'windows', 'partitions', 'basement', 'HVAC']
    for cat in retro_cat:
        cat_df['cat_'+cat] = cat_df.apply(lambda x: calc_category_retrofit(x['mainuse'],x[cat]), axis=1)

    # calculate contributions to embodied energy and emissions
    list_of_archetypes = [locator.get_archetypes_embodied_energy(), locator.get_archetypes_embodied_emissions()]
    result = [0, 0]
    counter = 0
    for archetype in list_of_archetypes:
        database_df = pd.read_csv(archetype)
        # merge databases acording to category
        built_df = cat_df.merge(database_df, left_on='cat_built', right_on='Code')
        envelope_df = cat_df.merge(database_df, left_on='cat_envelope', right_on='Code')
        roof_df = cat_df.merge(database_df, left_on='cat_roof', right_on='Code')
        windows_df = cat_df.merge(database_df, left_on='cat_windows', right_on='Code')
        partitions_df = cat_df.merge(database_df, left_on='cat_partitions', right_on='Code')
        basement_df = cat_df.merge(database_df, left_on='cat_basement', right_on='Code')
        HVAC_df = cat_df.merge(database_df, left_on='cat_HVAC', right_on='Code')

        # contributions due to construction
        built_df['delta_year'] =  (built_df['envelope']-yearcalc)*-1
        built_df['confirm'] = built_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_materials), axis=1)
        built_df['contrib'] = ((built_df['Wall_ext_ag']*built_df['area_walls_ext_ag'])+
                               (built_df['Roof']*built_df['footprint'])+
                               (built_df['windows_ag']*built_df['Win_ext']*(built_df['PFloor']-1)) +
                               (built_df['floor_area_ag']*built_df['Floor_int']+
                                built_df['floor_area_ag']*built_df['Wall_int_sup']*(built_df['PFloor']-1)*gv.fwratio +
                                built_df['footprint'] * built_df['Wall_int_nosup']*gv.fwratio)+
                               (basement_df['footprint'] * basement_df['Floor_g'] +
                                basement_df['Wall_ext_bg'] * basement_df['area_walls_ext_bg']) +
                               (built_df['footprint'] * built_df['Excavation']))/gv.sl_materials + \
                               ((HVAC_df['floor_area_ag']+HVAC_df['footprint']) * HVAC_df['Services'])/gv.sl_services

        # contributions due to envelope retrofit
        envelope_df['delta_year'] =  (envelope_df['envelope']-yearcalc)*-1
        envelope_df['confirm'] = envelope_df.apply(lambda x: calc_if_existing(x['delta_year'],gv.sl_materials), axis=1)
        envelope_df['contrib'] = (envelope_df['Wall_ext_ag']*envelope_df['area_walls_ext_ag']*(envelope_df['PFloor']-1))*envelope_df['confirm']/(gv.sl_materials)

        # contributions due to roof retrofit
        roof_df['delta_year'] =  (roof_df['roof']-yearcalc)*-1
        roof_df['confirm'] = roof_df.apply(lambda x: calc_if_existing(x['delta_year'],gv.sl_materials), axis=1)
        roof_df['contrib'] = roof_df['Roof']*roof_df['footprint']*roof_df['confirm']/gv.sl_materials

        # contributions due to windows retrofit
        windows_df['delta_year'] =  (windows_df['windows']-yearcalc)*-1
        windows_df['confirm'] = windows_df.apply(lambda x: calc_if_existing(x['delta_year'],gv.sl_materials), axis=1)
        windows_df['contrib'] = windows_df['windows_ag']*windows_df['Win_ext']*(windows_df['PFloor']-1)*windows_df['confirm']/gv.sl_materials

        # contributions due to partitions retrofit
        partitions_df['delta_year'] =  (partitions_df['partitions']-yearcalc)*-1
        partitions_df['confirm'] = partitions_df.apply(lambda x: calc_if_existing(x['delta_year'],gv.sl_materials), axis=1)
        partitions_df['contrib'] = (partitions_df['floor_area_ag']*partitions_df['Floor_int']+
                                    partitions_df['floor_area_ag']*partitions_df['Wall_int_sup']*gv.fwratio +
                                    partitions_df['footprint'] * partitions_df['Wall_int_nosup']*gv.fwratio) * \
                                    partitions_df['confirm']/gv.sl_materials

        # contributions due to basement_df
        basement_df['delta_year'] = (basement_df['basement'] - yearcalc) * -1
        basement_df['confirm'] = basement_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_materials),
                                                       axis=1)
        basement_df['contrib'] = (basement_df['footprint'] * basement_df['Floor_g'] +
                                  basement_df['Wall_ext_bg'] * basement_df['area_walls_ext_bg'])* \
                                  basement_df['confirm']/gv.sl_materials

        # contributions due to HVAC_df
        HVAC_df['delta_year'] = (HVAC_df['basement'] - yearcalc) * -1
        HVAC_df['confirm'] = HVAC_df.apply(lambda x: calc_if_existing(x['delta_year'], gv.sl_materials),axis=1)
        HVAC_df['contrib'] = ((HVAC_df['floor_area_ag']+HVAC_df['footprint']) * HVAC_df['Services'])*HVAC_df['confirm'] \
                             /gv.sl_services

        if counter is 0:
            built_df['GEN_GJ'] = (HVAC_df['contrib']+basement_df['contrib']+ partitions_df['contrib']+built_df['contrib']+
                                  roof_df['contrib'] + envelope_df['contrib'] + windows_df['contrib'])/1000
            built_df['GEN_MJm2'] = built_df['GEN_GJ']*1000/built_df['total_area']

            result[0] = built_df[['Name','GEN_GJ','GEN_MJm2']]
        else:
            built_df['CO2_ton'] = (HVAC_df['contrib'] + basement_df['contrib'] + partitions_df['contrib'] + built_df['contrib'] +
                                  roof_df['contrib'] + envelope_df['contrib'] + windows_df['contrib']) / 1000
            built_df['CO2_kgm2'] = built_df['CO2_ton'] * 1000 / built_df['total_area']

            result[1] = built_df[['Name','CO2_ton', 'CO2_kgm2']]
        counter += 1

    pd.DataFrame({'Name': result[0].Name, 'pen_GJ': result[0].GEN_GJ, 'pen_MJm2': result[0].GEN_MJm2,
                  'ghg_ton': result[1].CO2_ton, 'ghg_kgm2': result[1].CO2_kgm2}).to_csv(locator.get_lca_embodied(),
                                                                                         index=False, float_format='%.2f')
    print 'done!'

def calc_if_existing(x, y):
    if x <= y:
        return 1
    else:
        return 0

def calc_category_construction(a, x):
    if 0 <= x <= 1920:
        # Database['Qh'] = Database.ADMIN.value * Model.
        result = '1'
    elif x > 1920 and x <= 1970:
        result = '2'
    elif x > 1970 and x <= 1980:
        result = '3'
    elif x > 1980 and x <= 2000:
        result = '4'
    elif x > 2000 and x <= 2020:
        result = '5'
    else:
        result = '6'

    category = a+result
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

    category = a+result
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


def test_lca_embodied():
    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    yearcalc = 2050

    lca_embodied(locator=locator, yearcalc=yearcalc, gv=gv)

if __name__ == '__main__':
    test_lca_embodied()
