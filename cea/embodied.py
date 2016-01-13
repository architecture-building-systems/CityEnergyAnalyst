"""
===========================
embodied energy and related grey emissions model algorithm
===========================
J. Fonseca  script development          26.08.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox

"""
from __future__ import division
import pandas as pd
import numpy as np
import os
import arcpy
import globalvar
reload(globalvar)
gv = globalvar.GlobalVariables()


class EmbodiedEnergyTool(object):

    def __init__(self):
        self.label = 'Embodied Energy'
        self.description = 'Calculate the Emissions for operation'
        self.canRunInBackground = False

    def getParameterInfo(self):
        yearcalc = arcpy.Parameter(
            displayName="Year to calculate",
            name="yearcalc",
            datatype="GPLong",
            parameterType="Required",
            direction="Input")

        path_properties = arcpy.Parameter(
            displayName="Path to properties file (properties.xls)",
            name="path_properties",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_properties.filter.list = ['xls']

        path_results = arcpy.Parameter(
            displayName="Path to emissions results folder",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")

        retrofit_windows = arcpy.Parameter(
            displayName="retrofit windows",
            name="retrofit_windows",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_roof = arcpy.Parameter(
            displayName="retrofit roof",
            name="retrofit_roof",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_walls = arcpy.Parameter(
            displayName="retrofit walls",
            name="retrofit_walls",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_partitions = arcpy.Parameter(
            displayName="retrofit partitions",
            name="retrofit_partitions",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_int_floors = arcpy.Parameter(
            displayName="retrofit int floors",
            name="retrofit_int_floors",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_installations = arcpy.Parameter(
            displayName="retrofit installations",
            name="retrofit_installations",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        retrofit_basement_floor = arcpy.Parameter(
            displayName="retrofit basement floor",
            name="retrofit_basement_floor",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")

        return [path_properties,
                path_results,
                yearcalc,
                retrofit_windows,
                retrofit_roof,
                retrofit_walls,
                retrofit_partitions,
                retrofit_int_floors,
                retrofit_installations,
                retrofit_basement_floor]

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        path_LCA_embodied_energy = os.path.join(
            os.path.dirname(__file__),
            'db', 'Archetypes', 'Archetypes_embodied_energy.csv')
        path_LCA_embodied_emissions = os.path.join(
            os.path.dirname(__file__),
            'db', 'Archetypes', 'Archetypes_embodied_emissions.csv')

        path_properties = parameters[0]
        path_results = parameters[1]
        yearcalc = parameters[2]
        retrofit_windows = parameters[3]
        retrofit_roof = parameters[4]
        retrofit_walls = parameters[5]
        retrofit_partitions = parameters[6]
        retrofit_int_floors = parameters[7]
        retrofit_installations = parameters[8]
        retrofit_basement_floor = parameters[9]

        lca_embodied(
            path_LCA_embodied_energy=path_LCA_embodied_energy,
            path_LCA_embodied_emissions=path_LCA_embodied_emissions,
            path_properties=path_properties.valueAsText,
            path_results=path_results.valueAsText,
            yearcalc=int(yearcalc.valueAsText),
            retrofit_windows=bool(retrofit_windows),
            retrofit_roof=bool(retrofit_roof),
            retrofit_walls=bool(retrofit_walls),
            retrofit_partitions=bool(retrofit_partitions),
            retrofit_int_floors=bool(retrofit_int_floors),
            retrofit_installations=bool(retrofit_installations),
            retrofit_basement_floor=bool(retrofit_basement_floor),
            gv=gv)


def lca_embodied(
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
        gv):
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
    path_properties: string
        path to properties file properties.xls
    path_results : string
        path to demand results folder emissions
    retrofit_windows, retrofit_roof, retrofit_walls, retrofit_partitions,
    retrofit_int_floors, retrofit_installation, retrofit_basement_floor
       flags True or False to know which building compoenents have been
       retrofited properties file to run. it could be represented by a
       check box in the form

    Returns
    -------
    Total_LCA_embodied: .csv
        csv file of yearly primary energy and grey emissions per building
    """

    # localfiles
    general = pd.read_excel(path_properties, sheetname='general')
    envelope = pd.read_excel(path_properties, sheetname='envelope')
    general_df = general.merge(envelope, on='Name')
    general_df['cat'] = general_df['year_built'].apply(
        lambda x: calc_category_construction(x))
    general_df['cat2'] = general_df['year_retrofit'].apply(
        lambda x: calc_category_retrofit(x))
    general_df['code'] = general_df.mainuse + general_df.cat
    general_df['code2'] = general_df.mainuse + general_df.cat2

    list_embodied = [path_LCA_embodied_energy, path_LCA_embodied_emissions]
    result = []
    for var in list_embodied:
        embodied_LCA = pd.read_csv(var)
        df = pd.merge(
            general_df,
            embodied_LCA,
            left_on='code',
            right_on='Code')
        df2 = pd.merge(
            general_df,
            embodied_LCA,
            left_on='code2',
            right_on='Code')

        # building construction properties to array
        fp = df['footprint'].values
        floors = df['floors'].values
        af = fp*floors*df['Hs'].values
        yearcons = df['year_built'].values
        yearretro = df['year_retrofit'].values
        height = df['height'].values
        fwindow = df['fwindow'].values
        perimeter = df['perimeter'].values
        area = df['built_area'].values
        PFloor = df['PFloor'].values
        windows = perimeter*height*fwindow

        # computing factors to array of construction
        win_ext_factor = df['Win_ext'].values
        excavation_factor = df['Excavation'].values
        wall_int_avg_factor = (
            (df['Wall_int_nosup'] +
             df['Wall_int_sup']) *
            gv.fwratio /
            2).values
        walls_ext_bg_factor = df['Wall_ext_bg'].values
        walls_ext_ag_factor = df['Wall_ext_ag'].values
        floor_int_factor = df['Floor_int'].values
        services_factor = df['Services'].values
        floor_basement_factor = df['Floor_g'].values
        roof_factor = df['Roof'].values

        # computing factors to array of retrofit
        win_ext_factor2 = df2['Win_ext'].values
        wall_int_avg_factor2 = (
            (df2['Wall_int_nosup'] +
             df2['Wall_int_sup']) *
            gv.fwratio /
            2).values
        walls_ext_ag_factor2 = df2['Wall_ext_ag'].values
        floor_int_factor2 = df2['Floor_int'].values
        services_factor2 = df2['Services'].values
        floor_basement_factor2 = df2['Floor_g'].values
        roof_factor2 = df2['Roof'].values

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
        # computing individual shares per buildign component
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

    pd.DataFrame({'GEN_GJ': result[0] / 1000,
                  'GEN_MJm2': result[0] / af,
                  'CO2_ton': result[1] / 1000,
                  'CO2_kgm2': result[1] / af}).to_csv(
        os.path.join(path_results, 'Total_LCA_embodied.csv'),
        index=False, float_format='%.2f')


def query_embodied(
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
        retrofit,
        area,
        gv):
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


def calc_category_construction(x):
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
    elif x > 2020:
        result = '6'
    return result


def calc_category_retrofit(y):
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
    elif y > 2020:
        result = '12'
    return result


def test_lca_embodied():
    path_results = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\103_final output\emissions'  # noqa
    path_LCA_embodied_energy = os.path.join(os.path.dirname(__file__), 'db', 'Archetypes', 'Archetypes_embodied_energy.csv')  # noqa
    path_LCA_embodied_emissions = os.path.join(os.path.dirname(__file__), 'db', 'Archetypes', 'Archetypes_embodied_emissions.csv')  # noqa
    path_properties = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\102_intermediate output\building properties\properties.xls'  # noqa
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
