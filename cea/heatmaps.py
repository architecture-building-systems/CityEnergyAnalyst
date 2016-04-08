"""
===========================
Heatmapping algorithm
===========================
J. Fonseca  script development          27.08.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox

"""
from __future__ import division
import pandas as pd
import os
import arcpy
import tempfile




def heatmaps(analysis_field_variables, path_variables, path_buildings, path_results, path_temporary_folder,
             file_variable):
    """
    algorithm to calculate heat maps out of n variables of interest

    Parameters
    ----------
    path_variables:
        path to folder with variables to be mapped: the options:
            - .../../../demand
            - .../../../emissions
    file_variable:
        file name in folder to do the calculation
            - Total_demand.csv
            - cooling_LCA.csv
            - ../../../emissions/heating_LCA.csv
            - ../../../emissions/electricity_LCA.csv
            - ../../../emissions/Total_LCA_embodied.csv
            - ../../../emissions/Total_LCA_operation.csv.
    analysis_field_variables: array
        when the path variables is selected, an array of n variables 'string'
        will be elaborated based on the selection of n input fields. For this a
        form like the one used in the Arcgis function "merge/FieldMap could
        be used.
    path_buildings : string
        path to buildings file buildings.shp
    path_temporary_folder : string
        folder to store temporal files
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
    #create dbf file
    tempfile_name = "tempfile"
    tempfile = os.path.join(path_temporary_folder, 'tempfile.shp')
    tempfile_db_name = "data"
    tempfile_db = os.path.join(path_temporary_folder, 'data.dbf')
    arcpy.CopyRows_management(os.path.join(path_variables, file_variable), out_table=tempfile_db, config_keyword="")
    
    arcpy.FeatureToPoint_management(path_buildings,tempfile, "CENTROID")
    arcpy.MakeFeatureLayer_management(tempfile,"lyr","#","#")
    for field in analysis_field_variables:
        arcpy.AddField_management("lyr", field, "DOUBLE", "#", "#", "#", "#", "NULLABLE", "NON_REQUIRED", "#")

    # vector.append([])
    arcpy.AddJoin_management("lyr","Name",tempfile_db,"Name","KEEP_ALL")
    for field in  analysis_field_variables:              
        arcpy.CalculateField_management(in_table="lyr", field="%(tempfile_name)s.%(field)s" % locals(),
                                        expression="calc_non_null(!%(tempfile_db_name)s.%(field)s!)" % locals(),
                                        expression_type="PYTHON_9.3",
                                        code_block="def calc_non_null(x):\n     if x is None:\n         return 0\n     elif x == '':\n         return 0\n     else:\n         return x\n")

    # calculate heatmaps
    for field in analysis_field_variables:
        arcpy.gp.Idw_sa(tempfile, field, os.path.join(path_results, field), "1", "2", "VARIABLE 12")
            
def test_heatmaps():
    analysis_field_variables = ["Qhsf", "Qcsf"]  # noqa
    path_buildings = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\101_input files\feature classes'+'\\'+'buildings.shp'  # noqa
    path_variables = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\103_final output\demand'  # noqa
    path_results = r'C:\CEA_FS2015_EXERCISE02\01_Scenario one\103_final output\heatmaps'  # noqa
    path_temporary_folder = tempfile.gettempdir()
    file_variable = 'Total_demand.csv'
    heatmaps(
        analysis_field_variables,
        path_variables,
        path_buildings,
        path_results,
        path_temporary_folder,
        file_variable)

if __name__ == '__main__':
    test_heatmaps()
