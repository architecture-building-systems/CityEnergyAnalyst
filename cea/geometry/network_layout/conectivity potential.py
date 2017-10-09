"""
This script uses libraries in arcgis to create connections from
a series of points (buildings) to the closest street
"""

import os
import cea.globalvar
import cea.inputlocator
from cea.interfaces.arcgis.modules import arcpy


def calc_connectivity_network(path_arcgis_db, streets_shp, connection_point_buildings_shp, potential_network):
    # first add distribution network to each building form the roads

    arcpy.env.overwriteOutput = True
    spatialReference = arcpy.Describe(connection_point_buildings_shp).spatialReference
    memorybuildings = path_arcgis_db + "\\" + "points"
    merge = path_arcgis_db + "\\" + "merge"
    Newlines = path_arcgis_db + "\\" + "linesToerase"
    Finallines = path_arcgis_db + "\\" + "final_line"
    memorystreets = path_arcgis_db + "\\" + "streets"

    arcpy.CopyFeatures_management(connection_point_buildings_shp, memorybuildings)
    arcpy.CopyFeatures_management(streets_shp, memorystreets)
    arcpy.Near_analysis(memorybuildings,  memorystreets, location=True, angle=True)
    arcpy.MakeXYEventLayer_management(memorybuildings, "NEAR_X", "NEAR_Y", "Line_Points_Layer", spatialReference)
    arcpy.FeatureClassToFeatureClass_conversion("Line_Points_Layer", path_arcgis_db, "Line_points")
    arcpy.Append_management(path_arcgis_db + '\\' + "Line_points", memorybuildings, "No_Test")
    arcpy.MakeFeatureLayer_management(memorybuildings, "POINTS_layer")
    arcpy.env.workspace = path_arcgis_db
    arcpy.PointsToLine_management(memorybuildings, Newlines, "Name", "#", "NO_CLOSE")
    arcpy.Merge_management([memorystreets, Newlines], merge)
    arcpy.FeatureToLine_management(merge, Finallines)  # necessary to match vertices
    arcpy.CopyFeatures_management(Finallines, potential_network)
    print potential_network

def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

    streets_shp = locator.get_street_network()  # shapefile with the stations
    connection_point_buildings_shp = locator.get_connection_point()  # substation, it can be the centroid of the building
    potential_network = locator.get_connectivity_potential()  # shapefile, location of output.
    path_default_arcgis_db = os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb'))
    calc_connectivity_network(path_default_arcgis_db, streets_shp, connection_point_buildings_shp,
                              potential_network)


if __name__ == '__main__':
    run_as_script()
