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
from arcpyhelpers import index_cursor

reload(f)

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
        path_generation = arcpy.Parameter(
            displayName="Genearation systems file",
            name="path_generation",
            datatype="DEFile",
            parameterType="Required",
            direction="Input")
        path_generation.filter.list = ['shp']
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
        return [path_buildings, path_generation, path_results, generate_uses,
                generate_envelope, generate_systems, generate_equipment]

    def execute(self, parameters, messages):
        path_archetypes = os.path.join(
            os.path.dirname(__file__),
            'db', 'Archetypes', 'Archetypes_HVAC_properties.csv')
        path_buildings = parameters[0]
        path_generation = parameters[1]
        path_results = parameters[2]
        generate_uses = parameters[3]
        generate_envelope = parameters[4]
        generate_systems = parameters[5]
        generate_equipment = parameters[6]
        properties(path_archetypes=path_archetypes,
                   path_buildings=path_buildings.valueAsText,
                   path_generation=path_generation.valueAsText,
                   path_results=path_results.valueAsText,
                   generate_uses=generate_uses.value,
                   generate_envelope=generate_envelope.value,
                   generate_systems=generate_systems.value,
                   generate_equipment=generate_equipment.value,
                   gv=globalvar.GlobalVariables())


def properties(path_archetypes, path_buildings, path_generation, path_results, generate_uses,
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
    path_generation : string
        path to generation file generation.shp
    path_results : string
        path to intermediate results folder
    generate_uses_flag: boolean
        True, if the building uses are to be generated, otherwise False.
    generate_envelope_flag: boolean
        True, if the envelope is to be generated, otherwise False.
    generate_systems_flag: boolean
        True, if the systems are to be generated, otherwise False.
    generate_equipment_flag: boolean
        True, if equipment is to be generated, otherwise False.

    Returns
    -------
    properties: .xls
        file recorded in path_results describing the queried properties
        of each building. it contains 5 worksheets: general, uses, systems,
        envelope, and equipment.
    """

    # local variables:
    archetypes = pd.read_csv(path_archetypes) #the file is separated by commas now.
    list_uses = gv.list_uses
    areas = []
    floors_bg = []
    floors_ag = []
    height_bg = []
    height_ag = []
    year_built = []
    year_retrofit = []
    name = []
    perimeter = []
    PFloor = []
    xperimeter = []
    yperimeter = []
    generation_heating = []
    generation_cooling = []
    generation_electricity = []
    ADMIN = []
    SR = []
    INDUS = []
    REST = []
    RESTS = []
    DEPO = []
    COM = []
    MDU = []
    SDU = []
    EDU = []
    CR = []
    HEALTH = []
    SPORT = []
    SWIM = []
    PUBLIC = []
    SUPER = []
    ICE = []
    HOT = []

    # get zperimeter=width building and yperimeter = length building
    arcpy.env.overwriteOutput = True
    arcpy.MinimumBoundingGeometry_management(path_buildings, "in_memory/built", "RECTANGLE_BY_AREA", "NONE", "#",
                                             "MBG_FIELDS")
    # assign values of the shapefiles to the lists of local variables.
    fields = ['Height_bg', 'Height_ag', 'SHAPE@AREA', 'Floors_bg', 'Floors_ag', 'PFloor', 'Year_built', 'Year_retro',
              'Name', 'SHAPE@LENGTH', 'MBG_Width', 'MBG_Length']
    fields.extend(list_uses)# better this way as the name of uses can change in another case study.
    with arcpy.da.SearchCursor("in_memory/built", fields) as cursor:
        for row in index_cursor(cursor, fields):
            height_bg.append(row['Height_bg'])
            height_ag.append(row['Height_ag'])
            areas.append(row['SHAPE@AREA'])
            floors_bg.append(row['Floors_bg'])
            floors_ag.append(row['Floors_ag'])
            PFloor.append(row['PFloor'])
            year_built.append(row['Year_built'])
            year_retrofit.append(row['Year_retro'])
            name.append(row['Name'])
            perimeter.append(row['SHAPE@LENGTH'])
            xperimeter.append(row['MBG_Width'])
            yperimeter.append(row['MBG_Length'])
            ADMIN.append(row['ADMIN'])
            SR.append(row['SR'])
            INDUS.append(row['INDUS'])
            REST.append(row['REST'])
            RESTS.append(row['RESTS'])
            DEPO.append(row['DEPO'])
            COM.append(row['COM'])
            MDU.append(row['MDU'])
            SDU.append(row['SDU'])
            EDU.append(row['EDU'])
            CR.append(row['CR'])
            HEALTH.append(row['HEALTH'])
            SPORT.append(row['SPORT'])
            SWIM.append(row['SWIM'])
            PUBLIC.append(row['PUBLIC'])
            SUPER.append(row['SUPER'])
            ICE.append(row['ICE'])
            HOT.append(row['HOT'])
    arcpy.Delete_management("in_memory/built")
    # Generate uses properties
    if generate_uses:
        value = np.zeros(len(areas))
        uses_df = pd.DataFrame({'Name': name, 'ADMIN': ADMIN, 'SR': SR,
                                'REST': REST, 'RESTS': RESTS, 'DEPO': DEPO,
                                'COM': COM, 'MDU': MDU, 'SDU': SDU,
                                'EDU': EDU, 'CR': CR, 'HEALTH': HEALTH,
                                'SPORT': SPORT, 'SWIM': SWIM, 'PUBLIC': PUBLIC,
                                'SUPER': SUPER, 'ICE': ICE, 'HOT': HOT,
                                'INDUS': INDUS})
        writer = pd.ExcelWriter(path_results + '\\' + 'properties.xls')
        uses_df.to_excel(writer, 'uses', index=False, float_format="%.2f")
        writer.save()
    else:
        uses_df = pd.read_excel(
            path_results +
            '\\' +
            'properties.xls',
            sheetname="uses")

    # Generate general properties
    total_floors = [a + b for a, b in zip(floors_bg, floors_ag)]
    total_area = [a * b for a, b in zip(total_floors, areas)]
    total_height = [a + b for a, b in zip(height_bg, height_ag)]
    general_df = pd.DataFrame({'Name': name,
                               'height': total_height,
                               'height_bg': height_bg,
                               'height_ag': height_ag,
                               'built_area': total_area,
                               'footprint': areas,
                               'floors_bg': floors_bg,
                               'floors_ag': floors_ag,
                               'floors': total_floors,
                               'year_built': year_built,
                               'year_retrofit': year_retrofit,
                               'perimeter': perimeter,
                               'xperimeter': xperimeter,
                               'yperimeter': yperimeter})
    general_df['mainuse'] = f.calc_mainuse(uses_df, list_uses)
    general_df.to_excel(writer, 'general', index=False, float_format="%.2f")
    writer.save()

    # Extract data from Archetypes
    # Assign the year of each category and create a new code
    general_df['cat'] = general_df.apply(lambda x: f.calc_category(x['year_built'],x['year_retrofit']),axis=1)
    general_df['code'] = general_df.mainuse + general_df.cat
    general_df['PFloor'] = PFloor
    # Query all properties
    q = pd.merge(general_df, archetypes, left_on='code', right_on='Code')
    q['Shading_Type'] = gv.shading_type
    q['Shading_Pos'] = gv.shading_position
    q['fwindow'] = gv.window_to_wall_ratio

    # extract from generation file
    name = []
    with arcpy.da.SearchCursor(path_generation,
                               ('Gen_hs',
                                'Gen_cs',
                                'Gen_e',
                                'Name')) as cursor:
        for row in cursor:
            generation_heating.append(row[0])
            generation_cooling.append(row[1])
            generation_electricity.append(row[2])
            name.append(row[3])
    qgen = pd.DataFrame({'Generation_heating': generation_heating,
                         'Generation_cooling': generation_cooling,
                         'Generation_electricity': generation_electricity,
                         'Name': name})
    q1 = pd.merge(q, qgen, left_on='Name', right_on='Name')

    # Generate envelope properties
    if generate_envelope:
        q1.to_excel(writer, 'envelope', cols={'Name', 'Shading_Type',
                                              'Shading_Pos', 'fwindow', 'Construction', 'Uwall',
                                              'Ubasement', 'Uwindow', 'Uroof', 'Hs', 'Es', 'PFloor'}, index=False,
                    float_format="%.2f")
        writer.save()

    # generate systems properties
    if generate_systems:
        q1['Generation_cooling'] = 2
        q1.to_excel( writer, 'systems', cols={'Name', 'Generation_heating', 'Generation_cooling',
                                              'Generation_electricity', 'Emission_heating', 'Emission_cooling'},
                     index=False, float_format="%.2f")
        q1.to_excel(
            writer,
            'systems_temp',
            cols={'Name', 'tshs0', 'trhs0', 'tscs0', 'trcs0', 'tsww0', 'tsice0',
                  'trice0', 'tscp0', 'trcp0', 'tshp0', 'trhp0'},
            index=False,
            float_format="%.2f")
        writer.save()

    # if generate equipment
    if generate_equipment:
        q1.to_excel(
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
    """
    Run the properties script with input from the reference case and compare the results. This ensures that changes
    made to this script (e.g. refactorings) do not stop the script from working and also that the results stay the same.
    """
    import tempfile

    path_test = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test'))
    path_archetypes = os.path.join(
        os.path.dirname(__file__),
        'db', 'Archetypes', 'Archetypes_HVAC_properties.csv')
    path_buildings = os.path.join(path_test, 'reference-case', 'feature-classes', 'buildings.shp')
    path_generation = os.path.join(path_test, 'reference-case', 'feature-classes', 'generation.shp')
    path_results = tempfile.mkdtemp(prefix='CEAforArcGIS_')
    generate_uses = True
    generate_envelope = True
    generate_systems = True
    generate_equipment = True
    properties(path_archetypes, path_buildings, path_generation, path_results, generate_uses,
               generate_envelope, generate_systems, generate_equipment,
               gv)

    # read in the output and compare to reference output
    expected_output_path = os.path.join(path_test, 'reference-case', 'expected-output', 'properties.xls')
    computed_output_path = os.path.join(path_results, 'properties.xls')
    for sheet in ('uses', 'general', 'envelope', 'systems', 'systems_temp', 'equipment'):
        expected = pd.read_excel(expected_output_path, sheetname=sheet)
        computed = pd.read_excel(computed_output_path, sheetname=sheet)
        assert is_dataframe_equal(expected, computed), 'Difference found in sheet %s' % sheet
    # tidy up
    import shutil
    shutil.rmtree(path_results)
    print 'test_properties() succeeded'


def is_dataframe_equal(dfa, dfb):
    comparison = dfa == dfb
    return all((comparison[c].all() for c in comparison.columns))

if __name__ == '__main__':
    test_properties()
