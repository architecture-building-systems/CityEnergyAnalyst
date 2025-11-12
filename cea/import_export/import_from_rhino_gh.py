"""
Import Rhino/Grasshopper-generated files into CEA.

"""

import cea.inputlocator
import os
import cea.config
import shutil
import time
from cea.datamanagement.archetypes_mapper import archetypes_mapper
from cea.utilities.shapefile import csv_xlsx_to_shapefile



__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"



def exec_import_csv_from_rhino(locator):
    """

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return:
    """
    # Acquire the user inputs from config
    export_folder_path = locator.get_export_folder()

    # Directory where the files from Rhino/Grasshopper are stored
    input_path = os.path.join(export_folder_path, 'rhino', 'to_cea')
    reference_txt_path = os.path.join(input_path, 'reference_crs.txt')
    zone_csv_path = os.path.join(input_path, 'zone_in.csv')
    surroundings_csv_path = os.path.join(input_path, 'surroundings_in.csv')
    streets_csv_path = os.path.join(input_path, 'streets_in.csv')
    trees_csv_path = os.path.join(input_path, 'trees_in.csv')
    dh_edges_csv_path = os.path.join(input_path, 'dh_edges_in.csv')
    dh_nodes_csv_path = os.path.join(input_path, 'dh_nodes_in.csv')
    dc_edges_csv_path = os.path.join(input_path, 'dc_edges_in.csv')
    dc_nodes_csv_path = os.path.join(input_path, 'dc_nodes_in.csv')

    # Create the CEA Directory for the new scenario
    input_path = locator.get_input_folder()
    building_geometry_path = locator.get_building_geometry_folder()
    networks_path = locator.get_networks_folder()
    trees_path = locator.get_tree_geometry_folder()
    # thermal_network_path = locator.get_thermal_network_folder()
    os.makedirs(input_path, exist_ok=True)

    # Remove all files in folder
    for item in os.listdir(input_path):
        item_path = os.path.join(input_path, item)
        if os.path.isdir(item_path):
            # Remove the folder and its contents
            shutil.rmtree(item_path)
        else:
            # Remove the file
            os.remove(item_path)

    # Convert
    if os.path.isfile(zone_csv_path):
        os.makedirs(building_geometry_path, exist_ok=True)
        csv_xlsx_to_shapefile(zone_csv_path, building_geometry_path, 'zone.shp', reference_txt_path)
    else:
        raise ValueError("""The minimum requirement - zone_in.csv is missing. Create the file using Rhino/Grasshopper. CEA attempted to look for the file under this path:{path}.""".format(path=zone_csv_path))

    if os.path.isfile(surroundings_csv_path):
        csv_xlsx_to_shapefile(surroundings_csv_path, building_geometry_path, 'surroundings.shp', reference_txt_path)

    if os.path.isfile(streets_csv_path):
        os.makedirs(networks_path, exist_ok=True)
        csv_xlsx_to_shapefile(streets_csv_path, networks_path, 'streets.shp', reference_txt_path,  geometry_type="polyline")

    if os.path.isfile(trees_csv_path):
        os.makedirs(trees_path, exist_ok=True)
        csv_xlsx_to_shapefile(trees_csv_path, trees_path, 'trees.shp', reference_txt_path)

    if os.path.isfile(dh_edges_csv_path):
        os.makedirs(locator.get_output_thermal_network_type_folder('DH'), exist_ok=True)
        csv_xlsx_to_shapefile(dh_edges_csv_path, locator.get_output_thermal_network_type_folder('DH'), 'edges.shp', reference_txt_path,  geometry_type="polyline")

    if os.path.isfile(dc_edges_csv_path):
        os.makedirs(locator.get_output_thermal_network_type_folder('DC'), exist_ok=True)
        csv_xlsx_to_shapefile(dc_edges_csv_path, locator.get_output_thermal_network_type_folder('DC'), 'edges.shp', reference_txt_path, geometry_type="polyline")

    if os.path.isfile(dh_nodes_csv_path):
        os.makedirs(locator.get_output_thermal_network_type_folder('DH'), exist_ok=True)
        csv_xlsx_to_shapefile(dh_nodes_csv_path, locator.get_output_thermal_network_type_folder('DH'), 'nodes.shp', reference_txt_path, geometry_type="point")

    if os.path.isfile(dc_nodes_csv_path):
        os.makedirs(locator.get_output_thermal_network_type_folder('DC'), exist_ok=True)
        csv_xlsx_to_shapefile(dc_nodes_csv_path, locator.get_output_thermal_network_type_folder('DC'), 'nodes.shp', reference_txt_path, geometry_type="point")


def copy_data_from_reference_to_new_scenarios(config, locator):

    # Acquire the user inputs from config
    project_path = config.general.project
    reference_scenario_name = config.from_rhino_gh.reference_scenario_name
    reference_scenario_path = os.path.join(project_path, reference_scenario_name)
    bool_copy_database = config.from_rhino_gh.copy_database
    bool_copy_weather = config.from_rhino_gh.copy_weather
    bool_copy_terrain = config.from_rhino_gh.copy_terrain

    # Create the CEA Directory for the new scenario
    reference_database_path = os.path.join(reference_scenario_path, 'inputs', 'database')
    reference_terrain_path = os.path.join(reference_scenario_path, 'inputs', 'topography')
    reference_weather_path = os.path.join(reference_scenario_path, 'inputs', 'weather')

    # Acquire the paths to the data to copy in the current scenario
    current_database_path = locator.get_db4_folder()
    current_terrain_path = locator.get_terrain_folder()
    current_weather_path = locator.get_weather_folder()

    # Copy if needed
    if bool_copy_database:
        os.makedirs(current_database_path, exist_ok=True)
        copy_folder_contents(reference_database_path, current_database_path)

    if bool_copy_terrain:
        os.makedirs(current_terrain_path, exist_ok=True)
        copy_folder_contents(reference_terrain_path, current_terrain_path)

    if bool_copy_weather:
        os.makedirs(current_weather_path, exist_ok=True)
        copy_folder_contents(reference_weather_path, current_weather_path)


def copy_folder_contents(source_path, target_path):
    """
    Copies everything in a folder, including subfolders and their contents, to a new folder.

    Parameters:
    - source_path (str): The path of the source folder to copy from.
    - target_path (str): The path of the target folder to copy to.

    Returns:
    - None
    """

    # Copy contents
    for item in os.listdir(source_path):
        source_item = os.path.join(source_path, item)
        target_item = os.path.join(target_path, item)

        if os.path.isdir(source_item):
            # Recursively copy sub-folders
            shutil.copytree(source_item, target_item, dirs_exist_ok=True)
        else:
            # Copy individual files
            shutil.copy2(source_item, target_item)


def main(config: cea.config.Configuration):

    # Start the timer
    t0 = time.perf_counter()

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    exec_import_csv_from_rhino(locator)
    copy_data_from_reference_to_new_scenarios(config, locator)
    list_buildings = locator.get_zone_building_names()

    # Execute Archetypes Mapper
    update_architecture_dbf = True
    update_air_conditioning_systems_dbf = True
    update_indoor_comfort_dbf = True
    update_internal_loads_dbf = True
    update_supply_systems_dbf = True
    update_schedule_operation_cea = True

    archetypes_mapper(locator=locator,
                      update_architecture_dbf=update_architecture_dbf,
                      update_air_conditioning_systems_dbf=update_air_conditioning_systems_dbf,
                      update_indoor_comfort_dbf=update_indoor_comfort_dbf,
                      update_internal_loads_dbf=update_internal_loads_dbf,
                      update_supply_systems_dbf=update_supply_systems_dbf,
                      update_schedule_operation_cea=update_schedule_operation_cea,
                      list_buildings=list_buildings
                      )

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire import files from Rhino/Grasshopper to CEA is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())
