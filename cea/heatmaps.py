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
import inputlocator


def heatmaps(locator, analysis_field_variables, path_results, path_variables):
    """
    algorithm to calculate heat maps out of n variables of interest

    Parameters
    ----------
    path_variables:
        path to folder with variables to be mapped: the options:
            - .../../../demand
            - .../../../emissions
    analysis_field_variables: array
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
    arcpy.CopyRows_management(path_variables, out_table=tempfile_db, config_keyword="")
    
    arcpy.FeatureToPoint_management(locator.get_building_geometry(),tempfile, "CENTROID")
    arcpy.MakeFeatureLayer_management(tempfile, "lyr", "#", "#")
    for field in analysis_field_variables:
        arcpy.AddField_management("lyr", field, "DOUBLE", "#", "#", "#", "#", "NULLABLE", "NON_REQUIRED", "#")

    # vector.append([])
    arcpy.AddJoin_management("lyr", "Name", tempfile_db, "Name", "KEEP_ALL")
    for field in analysis_field_variables:
        arcpy.CalculateField_management(in_table="lyr", field="%(tempfile_name)s.%(field)s" % locals(),
                                        expression="calc_non_null(!%(tempfile_db_name)s.%(field)s!)" % locals(),
                                        expression_type="PYTHON_9.3",
                                        code_block="def calc_non_null(x):\n     if x is None:\n         return 0\n     elif x == '':\n         return 0\n     else:\n         return x\n")

    # calculate heatmaps
    for field in analysis_field_variables:
        arcpy.gp.Idw_sa(tempfile, field, os.path.join(path_results, field), "1", "2", "VARIABLE 12")

            
def test_heatmaps():

    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    selection = 'Total_Demand.csv'
    path_variables = locator.get_demand_results_file(selection)
    path_results = locator.get_heatmaps_demand_folder()
    analysis_field_variables = ["Qhsf_MWhyr", "Qcsf_MWhyr"]  # noqa
    heatmaps(locator=locator, analysis_field_variables=analysis_field_variables,
             path_results=path_results, path_variables=path_variables)

if __name__ == '__main__':
    test_heatmaps()
