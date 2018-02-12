"""
This script uses libraries in arcgis to create connections from
a series of points (buildings) to the closest street
"""

import os
import cea.globalvar
import cea.inputlocator
from cea.interfaces.arcgis.modules import arcpy
import cea.config
import os

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calc_connectivity_network(path_arcgis_db, path_streets_shp, path_connection_point_buildings_shp, path_potential_network):
    """
    This script outputs a potential network connecting a series of building points to the closest street network
    the street network is assumed to be a good path to the district heating or cooling network

    :param path_arcgis_db: path to default ArcGIS database
    :param path_streets_shp: path to street shapefile
    :param path_connection_point_buildings_shp: path to substations in buildings (or close by)
    :param path_potential_network: output path shapefile
    :return:
    """
    # first add distribution network to each building form the roads

    arcpy.env.overwriteOutput = True
    spatialReference = arcpy.Describe(path_connection_point_buildings_shp).spatialReference
    memorybuildings = path_arcgis_db + "\\" + "points"
    merge = path_arcgis_db + "\\" + "merge"
    Newlines = path_arcgis_db + "\\" + "linesToerase"
    Finallines = path_arcgis_db + "\\" + "final_line"

    arcpy.CopyFeatures_management(path_connection_point_buildings_shp, memorybuildings)
    arcpy.Near_analysis(memorybuildings, path_streets_shp, location=True, angle=True)
    arcpy.MakeXYEventLayer_management(memorybuildings, "NEAR_X", "NEAR_Y", "Line_Points_Layer", spatialReference)
    arcpy.FeatureClassToFeatureClass_conversion("Line_Points_Layer", path_arcgis_db, "Line_points")
    arcpy.Append_management(path_arcgis_db + '\\' + "Line_points", memorybuildings, "No_Test")
    arcpy.MakeFeatureLayer_management(memorybuildings, "POINTS_layer")
    arcpy.env.workspace = path_arcgis_db
    arcpy.PointsToLine_management(memorybuildings, Newlines, "Name", "#", "NO_CLOSE")
    arcpy.Merge_management([path_streets_shp, Newlines], merge)
    arcpy.FeatureToLine_management(merge, path_potential_network)  # necessary to match vertices

def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    path_streets_shp = locator.get_street_network()  # shapefile with the stations
    path_connection_point_buildings_shp = locator.get_connection_point()  # substation, it can be the centroid of the building
    path_potential_network = locator.get_connectivity_potential()  # shapefile, location of output.
    path_default_arcgis_db = os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb'))
    calc_connectivity_network(path_default_arcgis_db, path_streets_shp, path_connection_point_buildings_shp,
                              path_potential_network)

if __name__ == '__main__':
    main(cea.config.Configuration())