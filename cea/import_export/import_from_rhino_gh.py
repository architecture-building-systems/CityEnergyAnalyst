"""
Import Rhino/Grasshopper-generated files into CEA.

"""

import cea.inputlocator
import os
import cea.config
import shutil
import time
import pandas as pd
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



def generate_network_name(locator, base_name="network-gh"):
    """
    Generate a unique network name by checking existing networks.
    If base_name exists, try network-gh-1, network-gh-2, etc.

    Args:
        locator: InputLocator instance
        base_name: Base name for the network (default: "network-gh")

    Returns:
        str: Unique network name
    """
    thermal_network_folder = locator.get_thermal_network_folder()

    # If thermal-network folder doesn't exist, use base_name
    if not os.path.exists(thermal_network_folder):
        return base_name

    # Check if base_name exists
    existing_networks = [d for d in os.listdir(thermal_network_folder)
                        if os.path.isdir(os.path.join(thermal_network_folder, d))]

    if base_name not in existing_networks:
        return base_name

    # Generate numbered name
    counter = 1
    while f"{base_name}-{counter}" in existing_networks:
        counter += 1

    return f"{base_name}-{counter}"


def exec_import_csv_from_rhino(locator):
    """

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return: network_name if network files were imported, None otherwise
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

    # Check if any network files exist
    network_files_exist = (os.path.isfile(dh_edges_csv_path) or
                          os.path.isfile(dh_nodes_csv_path) or
                          os.path.isfile(dc_edges_csv_path) or
                          os.path.isfile(dc_nodes_csv_path))

    # Only generate network name if network files exist
    if network_files_exist:
        network_name = generate_network_name(locator)
        print(f"Importing network layout as: {network_name}")
    else:
        network_name = None

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

    # Import network edges - merge DH and DC edges into single layout.shp
    # Only proceed if we have a network name (i.e., network files exist)
    if network_name:
        dh_edges_exist = os.path.isfile(dh_edges_csv_path)
        dc_edges_exist = os.path.isfile(dc_edges_csv_path)

        if dh_edges_exist or dc_edges_exist:
            # Network folder (top level - shared between DH and DC)
            network_folder = locator.get_thermal_network_folder_network_name_folder(network_name)
            os.makedirs(network_folder, exist_ok=True)

            if dh_edges_exist and dc_edges_exist:
                # Both exist - merge and remove duplicates
                print("Merging DH and DC edges into shared layout.shp")

                # Read both CSV files
                dh_edges_df = pd.read_csv(dh_edges_csv_path)
                dc_edges_df = pd.read_csv(dc_edges_csv_path)

                # Concatenate
                merged_edges_df = pd.concat([dh_edges_df, dc_edges_df], ignore_index=True)

                # Remove duplicates based on geometry column only
                if 'geometry' in merged_edges_df.columns:
                    merged_edges_df = merged_edges_df.drop_duplicates(subset=['geometry'], keep='first')

                # Rebuild name column to ensure unique names following PIPExxx format
                merged_edges_df['name'] = [f'PIPE{str(i+1).zfill(3)}' for i in range(len(merged_edges_df))]

                # Save merged CSV temporarily
                merged_csv_path = os.path.join(input_path, 'merged_edges_temp.csv')
                merged_edges_df.to_csv(merged_csv_path, index=False)

                # Convert to shapefile as layout.shp
                csv_xlsx_to_shapefile(merged_csv_path, network_folder, 'layout.shp', reference_txt_path, geometry_type="polyline")

                # Clean up temporary file
                os.remove(merged_csv_path)
            elif dh_edges_exist:
                # Only DH edges exist
                print("Importing DH edges as layout.shp")

                # Read and rebuild name column
                dh_edges_df = pd.read_csv(dh_edges_csv_path)
                dh_edges_df['name'] = [f'PIPE{str(i+1).zfill(3)}' for i in range(len(dh_edges_df))]

                # Save temporarily and convert
                temp_csv_path = os.path.join(input_path, 'dh_edges_temp.csv')
                dh_edges_df.to_csv(temp_csv_path, index=False)
                csv_xlsx_to_shapefile(temp_csv_path, network_folder, 'layout.shp', reference_txt_path, geometry_type="polyline")
                os.remove(temp_csv_path)
            else:
                # Only DC edges exist
                print("Importing DC edges as layout.shp")

                # Read and rebuild name column
                dc_edges_df = pd.read_csv(dc_edges_csv_path)
                dc_edges_df['name'] = [f'PIPE{str(i+1).zfill(3)}' for i in range(len(dc_edges_df))]

                # Save temporarily and convert
                temp_csv_path = os.path.join(input_path, 'dc_edges_temp.csv')
                dc_edges_df.to_csv(temp_csv_path, index=False)
                csv_xlsx_to_shapefile(temp_csv_path, network_folder, 'layout.shp', reference_txt_path, geometry_type="polyline")
                os.remove(temp_csv_path)

        # Import DH nodes (type-specific)
        if os.path.isfile(dh_nodes_csv_path):
            dh_layout_folder = os.path.join(
                locator.get_output_thermal_network_type_folder('DH', network_name),
                'layout'
            )
            os.makedirs(dh_layout_folder, exist_ok=True)
            csv_xlsx_to_shapefile(dh_nodes_csv_path, dh_layout_folder, 'nodes.shp', reference_txt_path, geometry_type="point")

        # Import DC nodes (type-specific)
        if os.path.isfile(dc_nodes_csv_path):
            dc_layout_folder = os.path.join(
                locator.get_output_thermal_network_type_folder('DC', network_name),
                'layout'
            )
            os.makedirs(dc_layout_folder, exist_ok=True)
            csv_xlsx_to_shapefile(dc_nodes_csv_path, dc_layout_folder, 'nodes.shp', reference_txt_path, geometry_type="point")

    return network_name


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

    network_name = exec_import_csv_from_rhino(locator)
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
    print('The entire import files from Rhino/Grasshopper to CEA is now completed - time elapsed: %.2f seconds' % time_elapsed)

    if network_name:
        print(f'\nNetwork layout saved as: {network_name}')
        print('You can now run thermal-network simulation using this network name.')


if __name__ == '__main__':
    main(cea.config.Configuration())
