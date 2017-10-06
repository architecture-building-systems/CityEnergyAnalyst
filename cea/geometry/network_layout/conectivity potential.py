"""
This script uses libraries in arcgis to create connections from
a series of points (buildings) to the closest street
"""

import pandas as pd
import os
import cea.globalvar
import cea.inputlocator
from cea.interfaces.arcgis.modules import arcpy

def calc_connectivity_network(locator, path_arcgis_db, streets_shp, connection_point_buildings_shp, potential_network):

    # first add distribution network to each building form the roads
    memorybuildings = locator.get_temporary_file("points")
    merge = locator.get_temporary_file("merge")
    Newlines = path_arcgis_db + "\\" + "linesToerase"
    arcpy.CopyFeatures_management(connection_point_buildings_shp, memorybuildings)
    arcpy.Near_analysis(memorybuildings, streets_shp, location=True, angle=True)
    arcpy.MakeXYEventLayer_management(memorybuildings, "Near_X", "Near_Y", "Line_Points_Layer")
    arcpy.FeatureClassToFeatureClass_conversion("Line_Points_Layer", path_arcgis_db, "Line_points")
    arcpy.Append_management(path_arcgis_db + '\\' + "Line_points", memorybuildings, "No_Test")
    arcpy.MakeFeatureLayer_management(memorybuildings, "POINTS_layer")
    arcpy.env.workspace = path_arcgis_db
    arcpy.PointsToLine_management(memorybuildings, Newlines, "ID", "#", "NO_CLOSE")
    arcpy.Merge_management((streets_shp, Newlines), merge)
    arcpy.FeatureToLine_management(merge + "\\" + "merge", potential_network)  # necessary to match vertices

def run_as_script():

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

    streets_shp = locator.get_street_network() # shapefile with the stations
    connection_point_buildings_shp = locator.get_connection_point() #substation, it can be the centroid of the building
    potential_network = locator.get_connectivity_potential() #shapefile, location of output.
    path_default_arcgis_db = os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb'))
    calc_connectivity_network(locator, path_default_arcgis_db, streets_shp, connection_point_buildings_shp, potential_network)

if __name__ == '__main__':
    run_as_script()