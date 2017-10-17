"""
This script calculates the location of substations in case we do not have it.
it is estimated as the centroid of buildings.
"""

from geopandas import GeoDataFrame as gdf
import cea.globalvar
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calc_substation_location(input_buildings_shp, output_substations_shp):

    # GeoDataFrame creation
    poly = gdf.from_file(input_buildings_shp)
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