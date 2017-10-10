"""
This script caclulates the location of substations in case we do not have it.
it is estimated as the centroid of buildings.
"""

import geopandas as gpd
import cea.globalvar
import cea.inputlocator


def calc_substation_location(input_buildings_shp, output_substations_shp):

    # GeoDataFrame creation
    poly = gpd.read_file(input_buildings_shp)
    points = poly.copy()

    # creation of centroid
    points.geometry = points['geometry'].centroid
    points.crs = poly.crs

    # saving result
    points.to_file(output_substations_shp)


def run_as_script():
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    input_buildings_shp = locator.get_zone_geometry()
    output_substations_shp = locator.get_connection_point()
    calc_substation_location(input_buildings_shp, output_substations_shp)


if __name__ == '__main__':
    run_as_script()