"""
Export CEA files into Rhino/Grasshopper-ready format.

"""

import cea.inputlocator
import os
import cea.config
import time
import geopandas as gpd


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.utilities.shapefile import shapefile_to_csv_xlsx
from cea.utilities.standardize_coordinates import get_lat_lon_projected_shapefile, get_projected_coordinate_system

def exec_export_csv_for_rhino(config, locator):
    """

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return:
    """

    # Acquire the user inputs from config
    bool_include_zone = config.to_rhino_gh.include_zone
    bool_include_site = config.to_rhino_gh.include_site
    bool_include_surroundings = config.to_rhino_gh.include_surroundings
    bool_include_streets = config.to_rhino_gh.include_streets
    bool_include_trees = config.to_rhino_gh.include_trees
    bool_include_district_heating_network = config.to_rhino_gh.include_district_heating_network
    bool_include_district_cooling_network = config.to_rhino_gh.include_district_cooling_network

    # Create the folder to store all the exported files if it doesn't exist
    output_path = locator.get_export_to_rhino_from_cea_folder()
    os.makedirs(output_path, exist_ok=True)

    # Remove all files in folder
    for filename in os.listdir(output_path):
        file_path = os.path.join(output_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    gdf = gpd.read_file(locator.get_zone_geometry())
    lat, lon = get_lat_lon_projected_shapefile(gdf)  # Ensure this function is implemented
    new_crs = get_projected_coordinate_system(lat=lat, lon=lon)

    # Export zone info including typology
    if bool_include_zone:
        shapefile_to_csv_xlsx(locator.get_zone_geometry(), locator.get_export_to_rhino_from_cea_zone_to_csv(), new_crs)

    if bool_include_site and os.path.isfile(locator.get_site_polygon()):
        shapefile_to_csv_xlsx(locator.get_site_polygon(), locator.get_export_to_rhino_from_cea_site_to_csv(), new_crs)

    if bool_include_surroundings and os.path.isfile(locator.get_surroundings_geometry()):
        shapefile_to_csv_xlsx(locator.get_surroundings_geometry(), locator.get_export_to_rhino_from_cea_surroundings_to_csv(), new_crs)

    if bool_include_streets and os.path.isfile(locator.get_street_network()):
        shapefile_to_csv_xlsx(locator.get_street_network(), locator.get_export_to_rhino_from_cea_streets_to_csv(), new_crs)

    if bool_include_trees and os.path.isfile(locator.get_tree_geometry()):
        shapefile_to_csv_xlsx(locator.get_tree_geometry(), locator.get_export_to_rhino_from_cea_trees_to_csv(), new_crs)

    if bool_include_district_heating_network and os.path.isfile(locator.get_network_layout_edges_shapefile('DH')):
        shapefile_to_csv_xlsx(locator.get_network_layout_edges_shapefile('DH'), locator.get_export_to_rhino_from_cea_district_heating_network_edges_to_csv(), new_crs)

    if bool_include_district_cooling_network and os.path.isfile(locator.get_network_layout_edges_shapefile('DC')):
        shapefile_to_csv_xlsx(locator.get_network_layout_edges_shapefile('DC'), locator.get_export_to_rhino_from_cea_district_cooling_network_edges_to_csv(), new_crs)

    if bool_include_district_heating_network and os.path.isfile(locator.get_network_layout_nodes_shapefile('DH')):
        shapefile_to_csv_xlsx(locator.get_network_layout_nodes_shapefile('DH'), locator.get_export_to_rhino_from_cea_district_heating_network_nodes_to_csv(), new_crs)

    if bool_include_district_cooling_network and os.path.isfile(locator.get_network_layout_nodes_shapefile('DC')):
        shapefile_to_csv_xlsx(locator.get_network_layout_nodes_shapefile('DC'), locator.get_export_to_rhino_from_cea_district_cooling_network_nodes_to_csv(), new_crs)


def main(config: cea.config.Configuration):

    # Start the timer
    t0 = time.perf_counter()

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    exec_export_csv_for_rhino(config, locator)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire export to the current CEA Scenario to Rhino/Grasshopper-ready files is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())
