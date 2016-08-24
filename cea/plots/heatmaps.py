"""
===========================
Heatmapping algorithm
===========================
J. Fonseca  script development          27.08.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox

"""
from __future__ import division

import os

import arcpy

import cea.inputlocator
import cea.globalvar


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"


def heatmaps(locator, analysis_fields, path_results, file_to_analyze):
    """
    algorithm to calculate heat maps out of n variables of interest

    Parameters
    ----------
    file_to_analyze:
        path to the file with the variables to be mapped. This is used as the `in_rows` parameter
        to arcpy.CopyRows_management, so anything supported by that tool could, in theory, work, but
        we use the csv files. Either the Total_Demand.csv file produced by the demand script or one of
        the files in the emissions results folder.
    analysis_fields: array
        when the path variables is selected, an array of n variables 'string'
        will be elaborated based on the selection of n input fields. For this a
        form like the one used in the Arcgis function "merge/FieldMap could
        be used.
    path_results : string
        path to store results: folder heatmaps

    Returns
    -------
    heat map of variable n: .tif
        heat map file per variable of interest n.
    """
    arcpy.env.overwriteOutput = True
    arcpy.CheckOutExtension("Spatial")
    
    # local variables
    # create dbf file
    tempfile_name = "tempfile"
    tempfile = locator.get_temporary_file('tempfile.shp')
    tempfile_db_name = "data"
    tempfile_db = locator.get_temporary_file('data.dbf')
    arcpy.CopyRows_management(file_to_analyze, out_table=tempfile_db, config_keyword="")
    
    arcpy.FeatureToPoint_management(locator.get_building_geometry(),tempfile, "CENTROID")
    arcpy.MakeFeatureLayer_management(tempfile, "lyr", "#", "#")

    gis_field_lookup = {}  # map csv_field -> gis_field
    for csv_field in analysis_fields:
        gis_field = get_gis_field(csv_field, gis_field_lookup)
        arcpy.AddField_management("lyr", gis_field, "DOUBLE", "#", "#", "#", "#", "NULLABLE", "NON_REQUIRED", "#")

    # vector.append([])
    arcpy.AddJoin_management("lyr", "Name", tempfile_db, "Name", "KEEP_ALL")
    for csv_field in analysis_fields:
        gis_field = get_gis_field(csv_field, gis_field_lookup)
        arcpy.CalculateField_management(in_table="lyr", field="%(tempfile_name)s.%(gis_field)s" % locals(),
                                        expression="calc_non_null(!%(tempfile_db_name)s.%(gis_field)s!)" % locals(),
                                        expression_type="PYTHON_9.3",
                                        code_block="def calc_non_null(x):\n     if x is None:\n         return 0\n     elif x == '':\n         return 0\n     else:\n         return x\n")

    # calculate heatmaps
    for csv_field in analysis_fields:
        gis_field = get_gis_field(csv_field, gis_field_lookup)
        arcpy.gp.Idw_sa(tempfile, gis_field, os.path.join(path_results, gis_field), "1", "2", "VARIABLE 12")


def get_gis_field(csv_field, gis_field_lookup):
    """return a (max) 10 character representation of csv_field that is unique to the list of analysis fields"""
    import string
    if csv_field in gis_field_lookup:
        return gis_field_lookup[csv_field]
    gis_field_set = set(gis_field_lookup.values())
    gis_field = csv_field[:10]
    chars = iter(string.ascii_uppercase)
    while gis_field in gis_field_set:
        letters = list(gis_field)
        try:
            letters[-1] = next(chars)
        except StopIteration:
            raise Exception('Too many fields for analysis')
        gis_field = ''.join(letters)
    return gis_field


def test_heatmaps(scenario_path=None):
    gv = cea.globalvar.GlobalVariables()
    if scenario_path is None:
        scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    path_variables = locator.get_total_demand()
    path_results = locator.get_heatmaps_demand_folder()
    analysis_field_variables = ["Qhsf_MWhyr", "Qcsf_MWhyr"]  # noqa
    heatmaps(locator=locator, analysis_fields=analysis_field_variables,
             path_results=path_results, file_to_analyze=path_variables)

if __name__ == '__main__':
    test_heatmaps()
