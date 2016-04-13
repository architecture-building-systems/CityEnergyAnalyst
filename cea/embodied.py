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
from geopandas import GeoDataFrame as gpdf

gv = globalvar.GlobalVariables()


def lca_embodied(path_LCA_embodied_energy, path_LCA_embodied_emissions, path_age_shp, path_occupancy_shp, path_geometry_shp, path_results, yearcalc, gv):
    """
    algorithm to calculate the embodied energy and grey energy of buildings
    according to the method of Fonseca et al 2015. CISBAT 2015. and Thoma et al
    2014. CUI 2014.

    Parameters
    ----------
    yearcalc: int
        year between 1900 and 2100 indicating when embodied energy is evaluated
        to account for emissions already offset from building construction
        and retrofits more than 60 years ago.
    path_LCA_embodied_energy:
        path to database of archetypes embodied energy file
        Archetypes_embodied_energy.csv
    path_LCA_embodied_emissions:
        path to database of archetypes grey emissions file
        Archetypes_embodied_emissions.csv
    path_age_shp: string
        path to buildings_age.shp
    path_results : string
        path to demand results folder emissions

    Returns
    -------
    Total_LCA_embodied: .csv
        csv file of yearly primary energy and grey emissions per building stored in path_results
    """

    # localvariables
    geometry_df = gpdf.from_file(path_geometry_shp)
    geometry_df['footprint'] = geometry_df.area
    geometry_df['perimeter'] = geometry_df.length
    geometry_df = geometry_df.drop('geometry', axis=1).set_index('Name')
    occupancy_df = gpdf.from_file(path_occupancy_shp).drop('geometry', axis=1).set_index('Name')
    age_df = gpdf.from_file(path_age_shp).drop('geometry', axis=1).set_index('Name')
    list_uses = gv.list_uses

    # define main use:
    occupancy_df['mainuse'] = calc_mainuse(occupancy_df, list_uses)

    # dataframe with jonned data for categories
    cat_df = occupancy_df.merge(age_df, left_index=True, right_index=True)

    # get categories
    cat_df['cat_built'] = cat_df.apply(lambda x: calc_category_construction(x['mainuse'],x['built']), axis=1)
    cat_df['cat_envelope'] = cat_df.apply(lambda x: calc_category_retrofit(x['mainuse'],x['envelope']), axis=1)
    cat_df['cat_roof'] = cat_df.apply(lambda x: calc_category_retrofit(x['mainuse'],x['roof']), axis=1)
    cat_df['cat_windows'] = cat_df.apply(lambda x: calc_category_retrofit(x['mainuse'],x['windows']), axis=1)
    cat_df['cat_partitions'] = cat_df.apply(lambda x: calc_category_retrofit(x['mainuse'],x['partitions']), axis=1)
    cat_df['cat_basement'] = cat_df.apply(lambda x: calc_category_retrofit(x['mainuse'],x['basement']), axis=1)
    cat_df['cat_HVAC'] = cat_df.apply(lambda x: calc_category_retrofit(x['mainuse'], x['HVAC']), axis=1)

    list_of_archetypes = [path_LCA_embodied_energy, path_LCA_embodied_emissions]
    result = []
    for archetype in list_of_archetypes:
        database_df = pd.read_csv(archetype)

        # create merge with databases
        built_df = cat_df.merge(database_df, left_on='cat_built', right_on='Code')
        envelope_df = cat_df.merge(database_df, left_on='cat_envelope', right_on='Code')
        roof_df = cat_df.merge(database_df, left_on='cat_roof', right_on='Code')
        windows_df = cat_df.merge(database_df, left_on='cat_windows', right_on='Code')
        partitions_df = cat_df.merge(database_df, left_on='cat_partitions', right_on='Code')
        basement_df = cat_df.merge(database_df, left_on='cat_basement', right_on='Code')
        HVAC_df = cat_df.merge(database_df, left_on='cat_HVAC', right_on='Code')
        
        # merging with the category of construction
        df = pd.merge(general_df, database_df, left_on='code', right_on='Code')

        # merging with the category of retrofit
        df2 = pd.merge(general_df, database_df,left_on='code2', right_on='Code')

        # merging both dataframes
        df3 = pd.merge(df,df2,left_on='Name', right_on='Name', suffixes=['','_y'])

        # building construction properties to array
        fp = df3['footprint'].values
        floors = df3['floors'].values
        af = fp*floors*df3['Es'].values
        yearcons = df3['year_built'].values
        yearretro = df3['year_retrofit'].values
        height = df3['height'].values
        fwindow = df3['fwindow'].values
        perimeter = df3['perimeter'].values
        area = df3['built_area'].values
        PFloor = df3['PFloor'].values
        windows = perimeter*height*fwindow

        # computing factors to array of construction
        win_ext_factor = df3['Win_ext'].values
        excavation_factor = df3['Excavation'].values
        wall_int_avg_factor = (
            (df3['Wall_int_nosup'] +
             df3['Wall_int_sup']) *
            gv.fwratio /
            2).values
        walls_ext_bg_factor = df3['Wall_ext_bg'].values
        walls_ext_ag_factor = df3['Wall_ext_ag'].values
        floor_int_factor = df3['Floor_int'].values
        services_factor = df3['Services'].values
        floor_basement_factor = df3['Floor_g'].values
        roof_factor = df3['Roof'].values

        # computing factors to array of retrofit
        win_ext_factor2 = df3['Win_ext_y'].values
        wall_int_avg_factor2 = (
            (df3['Wall_int_nosup_y'] +
             df3['Wall_int_sup_y']) *
            gv.fwratio /
            2).values
        walls_ext_ag_factor2 = df3['Wall_ext_ag_y'].values
        floor_int_factor2 = df3['Floor_int_y'].values
        services_factor2 = df3['Services_y'].values
        floor_basement_factor2 = df3['Floor_g_y'].values
        roof_factor2 = df3['Roof_y'].values

        # computing factor out vectorization
        # windows
        win_ext = win_ext_factor*windows
        win_ext2 = win_ext_factor2*windows
        # external walls
        walls_ext_ag = walls_ext_ag_factor*perimeter*height*(1-fwindow)*PFloor
        walls_ext_ag2 = walls_ext_ag_factor2 * \
            perimeter*height*(1-fwindow)*PFloor
        # external walls basement
        walls_ext_bg = walls_ext_bg_factor*perimeter*gv.hf
        # technical instalations
        services = services_factor*af
        services2 = services_factor2*af
        # floor basement
        floor_basement = floor_basement_factor*fp
        floor_basement2 = floor_basement_factor2*fp
        # roof
        roof = roof_factor*fp
        roof2 = roof_factor2*fp
        # excavation
        excavation = excavation_factor*fp
        # computing individual shares per building component
        result.append(
            np.vectorize(query_embodied)(
                fp,
                floors,
                yearcons,
                yearretro,
                PFloor,
                walls_ext_ag,
                walls_ext_ag2,
                yearcalc,
                windows,
                win_ext,
                win_ext2,
                excavation,
                wall_int_avg_factor,
                wall_int_avg_factor2,
                walls_ext_bg,
                floor_int_factor,
                floor_int_factor2,
                services,
                services2,
                floor_basement,
                floor_basement2,
                roof,
                roof2,
                ''.join(str(int(b)) for b in (
                    retrofit_roof,
                    retrofit_walls,
                    retrofit_partitions,
                    retrofit_windows,
                    retrofit_int_floors,
                    retrofit_installations,
                    retrofit_basement_floor)),
                area,
                gv))

    
    df3['GEN_MJm2'] = 0
    df3['CO2_kgm2'] = 0
    for x in range(df3.Name.count()):
        if af[x] <= 0:
            df3.loc[x,'GEN_MJm2'] = result[0][x]/(fp[x]*floors[x]*0.9)
            df3.loc[x,'CO2_kgm2'] = result[1][x]/(fp[x]*floors[x]*0.9)
        else:
            df3.loc[x,'GEN_MJm2'] = result[0][x]/(af[x])
            df3.loc[x,'CO2_kgm2'] = result[1][x]/(af[x])
            
    
    pd.DataFrame({'Name':df3['Name'],
                    'GEN_GJ': result[0] / 1000,
                    'GEN_MJm2': df3['GEN_MJm2'],
                    'CO2_ton': result[1] / 1000,
                    'CO2_kgm2': df3['CO2_kgm2']}).to_csv(
    os.path.join(path_results, 'Total_LCA_embodied.csv'),
                            index=False, float_format='%.2f')

def query_embodied(fp, floors, yearcons, yearretro, PFloor, walls_ext_ag, walls_ext_ag2, yearcalc, windows, win_ext,
                   win_ext2, excavation, wall_int_avg_factor, wall_int_avg_factor2, walls_ext_bg, floor_int_factor,
                   floor_int_factor2, services, services2, floor_basement, floor_basement2, roof, roof2, retrofit,
                   area, gv):
    flagroof, flag_ext_wall, flag_int_wall, flag_windows, flag_int, flag_services, flagbasement = [bool(int(c)) for c in retrofit]  # noqa
    # internal walls
    # it means that part is a parking lot or storage in the building so
    # internal partitions are considered and services od storage
    if PFloor < 1:
        walls_int = wall_int_avg_factor*area*PFloor
        walls_int2 = wall_int_avg_factor2*area*PFloor
    else:
        walls_int = wall_int_avg_factor*floors*fp
        walls_int2 = wall_int_avg_factor2*floors*fp
    # internal floors
    if floors > 1:
        floor_int = (floors-1)*fp*floor_int_factor
        floor_int2 = (floors-1)*fp*floor_int_factor2
    else:
        floor_int = 0
        floor_int2 = 0
    # first it is assumed like the building was built
    construction = (
        1 / gv.sl_materials) * (
        floor_basement + roof + walls_ext_bg + walls_ext_ag + walls_int
        + win_ext + floor_int + excavation) + services / gv.sl_installations
    if yearretro > yearcons:
        period = yearcalc - yearretro
        if period > gv.sl_materials:
            result = 0
        else:
            retrofit = (
                (1/gv.sl_materials)*(
                    floor_basement2*flagbasement +
                    roof2*flagroof +
                    walls_ext_ag2*flag_ext_wall +
                    walls_int2*flag_int_wall +
                    win_ext2*flag_windows +
                    floor_int2*flag_int) +
                services2 * flag_services / gv.sl_installations)
            if yearcalc-yearcons < gv.sl_materials:
                result = retrofit + construction
            else:
                result = retrofit
    else:
        period = yearcalc - yearcons
        # if building is older thatn gv.sl_materials years it already offset
        # all its emissions.
        if period > gv.sl_materials:
            result = 0
        else:
            result = construction
    return result


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
    path_results = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\103_final output\emissions'  # noqa
    path_LCA_embodied_energy = os.path.join(os.path.dirname(__file__), 'db', 'Archetypes', 'Archetypes_embodied_energy.csv')  # noqa
    path_LCA_embodied_emissions = os.path.join(os.path.dirname(__file__), 'db', 'Archetypes', 'Archetypes_embodied_emissions.csv')  # noqa
    path_properties = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\102_intermediate output\building properties\properties.xls'  # noqa
    yearcalc = 2050
    retrofit_windows = True
    retrofit_roof = True
    retrofit_walls = True
    retrofit_partitions = True
    retrofit_int_floors = True
    retrofit_installations = True
    retrofit_basement_floor = True
    lca_embodied(
        path_LCA_embodied_energy,
        path_LCA_embodied_emissions,
        path_properties,
        path_results,
        yearcalc,
        retrofit_windows,
        retrofit_roof,
        retrofit_walls,
        retrofit_partitions,
        retrofit_int_floors,
        retrofit_installations,
        retrofit_basement_floor,
        gv)
    print 'done!'

if __name__ == '__main__':
    test_lca_embodied()
