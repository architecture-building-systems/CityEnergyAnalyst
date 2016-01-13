"""
===========================
building properties algorithm
===========================
File history and credits:
J. Fonseca  script development          20.08.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox
"""
from __future__ import division
import pandas as pd
import functions as f
import arcpy
import os
import numpy as np
import globalvar

gv = globalvar.GlobalVariables()
class PropertiesTool(object):

    def __init__(self):
        self.label = 'Properties'
        self.description = 'Query building properties from statistical database'  # noqa
        self.canRunInBackground = False

    def getParameterInfo(self):
        path_buildings = arcpy.Parameter(
            displayName="Buildings file",
            name="path_buildings",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_buildings.filter.list = ['shp']
        path_results = arcpy.Parameter(
            displayName="path to intermediate results folder",
            name="path_results",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        generate_uses = arcpy.Parameter(
            displayName="Generate the uses",
            name="generate_uses",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        generate_envelope = arcpy.Parameter(
            displayName="Generate the envelope",
            name="generate_envelope",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        generate_systems = arcpy.Parameter(
            displayName="Generate the systems",
            name="generate_systems",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        generate_equipment = arcpy.Parameter(
            displayName="Generate the equipment",
            name="generate_equipment",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input")
        return [path_buildings, path_results, generate_uses,
                generate_envelope, generate_systems, generate_equipment]

    def execute(self, parameters, messages):
        path_archetypes = os.path.join(
            os.path.dirname(__file__),
            'db', 'Archetypes', 'Archetypes_HVAC_properties.csv')
        path_buildings = parameters[0]
        path_results = parameters[1]
        generate_uses = parameters[2]
        generate_envelope = parameters[3]
        generate_systems = parameters[4]
        generate_equipment = parameters[5]
        properties(path_archetypes=path_archetypes,
                   path_buildings=path_buildings.valueAsText,
                   path_results=path_results.valueAsText,
                   generate_uses=generate_uses.value,
                   generate_envelope=generate_envelope.value,
                   generate_systems=generate_systems.value,
                   generate_equipment=generate_equipment.value,
                   gv=globalvar.GlobalVariables())


def properties(path_archetypes, path_buildings, path_results, generate_uses,
               generate_envelope, generate_systems, generate_equipment, gv):
    """
    algorithm to query building properties from statistical database
    Archetypes_HVAC_properties.csv. for more info check the integrated demand
    model of Fonseca et al. 2015. Appl. energy.

    Parameters
    ----------
    path_archetypes : string
        path to database of archetypes file Archetypes_HVAC_properties.csv
    path_buildings : string
        path to buildings file buildings.shp
    path_results : string
        path to intermediate results folder
    generate_uses - generate_envelope -generate_systems - generate_equipment
        flags True or False to know which categories of the
        properties file to run. it could be represented by acheck box in the
        form

    Returns
    -------
    properties: .xls
        file recorded in path_results describing the queried properties
        of each building. it contains 5 worksheets: general, uses, systems,
        envelope, and equipment.
    """

    # local variables:
    archetypes = pd.read_csv(path_archetypes)
    list_uses = gv.list_uses
    areas = []
    floors = []
    year_built = []
    year_retrofit = []
    name = []
    height = []
    perimeter = []
    PFloor = []
    xperimeter = []
    yperimeter = []

    # get zperimeter=width building and yperimeter = lenght building
    arcpy.env.overwriteOutput = True
    arcpy.MinimumBoundingGeometry_management(path_buildings,
                                             "in_memory/built",
                                             "RECTANGLE_BY_AREA",
                                             "NONE")

    with arcpy.da.SearchCursor("in_memory/built",
                               ('Height',
                                'SHAPE@AREA',
                                'Floors',
                                'PFloor',
                                'Year_built',
                                'Year_retro',
                                'Name',
                                'SHAPE@LENGTH',
                                'MBG_Width', 'MBG_Length')) as cursor:
        for row in cursor:
            height.append(row[0])
            areas.append(row[1])
            floors.append(row[2])
            PFloor.append(row[3])
            year_built.append(row[4])
            year_retrofit.append(row[5])
            name.append(row[6])
            perimeter.append(row[7])
            xperimeter.append(row[8])
            yperimeter.append(row[9])
    arcpy.Delete_management("in_memory\\built")
    # Generate uses properties
    if generate_uses:
        value = np.zeros(len(areas))
        uses_df = pd.DataFrame({'Name': name, 'ADMIN': value+1, 'SR': value,
                                'REST': value, 'RESTS': value, 'DEPO': value,
                                'COM': value, 'MDU': value, 'SDU': value,
                                'EDU': value, 'CR': value, 'HEALTH': value,
                                'SPORT': value, 'SWIM': value, 'PUBLIC': value,
                                'SUPER': value, 'ICE': value, 'HOT': value,
                                'INDUS': value})
        writer = pd.ExcelWriter(path_results+'\\'+'properties.xls')
        uses_df.to_excel(writer, 'uses', index=False, float_format="%.2f")
        writer.save()
    else:
        uses_df = pd.read_excel(
            path_results +
            '\\' +
            'properties.xls',
            sheetname="uses")

    # Generate general properties
    total_area = [a*b for a, b in zip(floors, areas)]
    general_df = pd.DataFrame({'Name': name,
                               'height': height,
                               'built_area': total_area,
                               'footprint': areas,
                               'floors': floors,
                               'year_built': year_built,
                               'year_retrofit': year_retrofit,
                               'perimeter': perimeter,
                               'xperimeter': xperimeter,
                               'yperimeter': yperimeter})
    general_df['mainuse'] = f.calc_mainuse(uses_df, list_uses)
    general_df.to_excel(writer, 'general', index=False, float_format="%.2f")
    writer.save()

    # Assign the year of each category and create a new code
    general_df['cat'] = general_df.apply(
        lambda x: f.calc_category(
            x['year_built'],
            x['year_retrofit']),
        axis=1)
    general_df['code'] = general_df.mainuse + general_df.cat
    general_df['PFloor'] = PFloor
    # Query all properties
    q = pd.merge(general_df, archetypes, left_on='code', right_on='Code')
    q['Shading_Type'] = gv.shading_type
    q['Shading_Pos'] = gv.shading_position
    q['fwindow'] = gv.window_to_wall_ratio
    q['Generation_heating'] = gv.generation_heating
    q['Generation_hotwater'] = gv.generation_hotwater
    q['Generation_cooling'] = gv.generation_cooling
    q['Generation_electricity'] = gv.generation_electricity

    # Generate envelope properties
    if generate_envelope:
        q.to_excel(writer, 'envelope', cols={'Name', 'Shading_Type',
                   'Shading_Pos', 'fwindow', 'Construction', 'Uwall',
                   'Ubasement', 'Uwindow', 'Uroof', 'Hs', 'Es','PFloor'}, index=False,
                   float_format="%.2f")
        writer.save()

    # generate systems properties
    if generate_systems:
        q.to_excel(
            writer,
            'systems',
            cols={
                'Name',
                'Generation_heating',
                'Generation_hotwater',
                'Generation_cooling',
                'Generation_electricity',
                'Emission_heating',
                'Emission_cooling',
                },
            index=False,
            float_format="%.2f")
        q.to_excel(
            writer,
            'systems_temp',
            cols={
                'Name',
                'tshs0',
                'trhs0',
                'tscs0',
                'trcs0',
                'tsww0',
                'tsice0',
                'trice0',
                'tscp0',
                'trcp0',
                'tshp0',
                'trhp0'},
            index=False,
            float_format="%.2f")
        writer.save()
    if generate_equipment:
        q.to_excel(
            writer,
            'equipment',
            cols={
                'Name',
                'CRFlag',
                'SRFlag',
                'ICEFlag',
                'E4'},
            index=False,
            float_format="%.2f")
        writer.save()

def test_properties():
    path_archetypes = os.path.join(
            os.path.dirname(__file__),
            'db', 'Archetypes', 'Archetypes_HVAC_properties.csv')
    path_buildings = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\101_input files\feature classes'+'\\'+'buildings.shp'  # noqa
    path_results = r'C:\CEA_FS2015_EXERCISE01\01_Scenario one\102_intermediate output\building properties'  # noqa
    generate_uses = True
    generate_envelope = True
    generate_systems = True
    generate_equipment = True
    properties(path_archetypes, path_buildings, path_results, generate_uses,
               generate_envelope, generate_systems, generate_equipment,
               gv)
    print 'done.'

if __name__ == '__main__':
    test_properties()
