"""
Import Rhino/Grasshopper-generated files into CEA.

"""

import cea.inputlocator
import os
import subprocess
import sys
import cea.config
import shutil
import time


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


# adding CEA to the environment
# Fix for running in PyCharm for users using micromamba
my_env = os.environ.copy()
my_env['PATH'] = f"{os.path.dirname(sys.executable)}:{my_env['PATH']}"

def exec_import_csv_from_rhino(config, locator):
    """

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return:
    """
    # Acquire the user inputs from config
    input_path = config.from_rhino_gh.input_path
    new_scenario_name = config.from_rhino_gh.new_scenario_name

    # Directory where the files from Rhino/Grasshopper are stored
    input_path = os.path.join(input_path, 'export', 'rhino')
    reference_shapefile_path = os.path.join(input_path, 'reference.shp')
    zone_csv_path = os.path.join(input_path, 'zone_from.csv')
    typology_csv_path = os.path.join(input_path, 'typology_from.csv')
    surroundings_csv_path = os.path.join(input_path, 'surroundings_from.csv')
    streets_csv_path = os.path.join(input_path, 'streets_from.csv')
    trees_csv_path = os.path.join(input_path, 'trees_from.csv')

    # Create the CEA Directory for the new scenario
    project_path = config.general.project
    new_scenario_path = os.path.join(project_path, new_scenario_name, 'inputs')
    building_geometry_path = os.path.join(new_scenario_path, 'building-geometry')
    building_properties_path = os.path.join(new_scenario_path, 'building-properties')
    networks_path = os.path.join(new_scenario_path, 'networks')
    trees_path = os.path.join(new_scenario_path, 'trees')
    os.makedirs(new_scenario_path, exist_ok=True)

    # Remove all files in folder
    for item in os.listdir(new_scenario_path):
        item_path = os.path.join(new_scenario_path, item)
        if os.path.isdir(item_path):
            # Remove the folder and its contents
            shutil.rmtree(item_path)
        else:
            # Remove the file
            os.remove(item_path)

    # Export zone info including typology
    os.makedirs(building_geometry_path, exist_ok=True)
    subprocess.run(['cea', 'shp-to-csv-to-shp',
                        '--input-file', zone_csv_path,
                        '--output-file-name', 'zone.shp',
                        '--output-path', building_geometry_path,
                        '--reference-shapefile', '{reference_shapefile_path}'.format(reference_shapefile_path=reference_shapefile_path),
                        '--polygon', 'true',
                        ], env=my_env, check=True, capture_output=True)

    os.makedirs(building_properties_path, exist_ok=True)
    subprocess.run(['cea', 'dbf-to-csv-to-dbf',
                        '--input-file', typology_csv_path,
                        '--output-file-name', 'typology.dbf',
                        '--output-path', building_properties_path,
                        ], env=my_env, check=True, capture_output=True)

    if os.path.isfile(surroundings_csv_path):
        subprocess.run(['cea', 'shp-to-csv-to-shp',
                        '--input-file', surroundings_csv_path,
                        '--output-file-name', 'surroundings.shp',
                        '--output-path', building_geometry_path,
                        '--reference-shapefile', '{reference_shapefile_path}'.format(reference_shapefile_path=reference_shapefile_path),
                        '--polygon', 'true',
                        ], env=my_env, check=True, capture_output=True)

    if os.path.isfile(streets_csv_path):
        os.makedirs(networks_path, exist_ok=True)
        subprocess.run(['cea', 'shp-to-csv-to-shp',
                        '--input-file', streets_csv_path,
                        '--output-file-name', 'streets.shp',
                        '--output-path', networks_path,
                        '--reference-shapefile', '{reference_shapefile_path}'.format(reference_shapefile_path=reference_shapefile_path),
                        '--polygon', 'false',
                        ], env=my_env, check=True, capture_output=True)

    if os.path.isfile(trees_csv_path):
        os.makedirs(trees_path, exist_ok=True)
        subprocess.run(['cea', 'shp-to-csv-to-shp',
                        '--input-file', trees_csv_path,
                        '--output-file-name', 'trees.shp',
                        '--output-path', trees_path,
                        '--reference-shapefile', '{reference_shapefile_path}'.format(reference_shapefile_path=reference_shapefile_path),
                        '--polygon', 'true',
                        ], env=my_env, check=True, capture_output=True)

def copy_data_from_current_to_new_scenarios(config, locator):

    # Acquire the user inputs from config
    input_path = config.from_rhino_gh.input_path
    new_scenario_name = config.from_rhino_gh.new_scenario_name
    bool_copy_database = config.from_rhino_gh.copy_database
    bool_copy_weather = config.from_rhino_gh.copy_weather
    bool_copy_terrain = config.from_rhino_gh.copy_terrain

    # Directory where the files from Rhino/Grasshopper are stored
    input_path = os.path.join(input_path, 'export', 'rhino')

    # Create the CEA Directory for the new scenario
    project_path = config.general.project
    new_scenario_path = os.path.join(project_path, new_scenario_name, 'inputs')
    new_database_path = os.path.join(new_scenario_path, 'technology')
    new_terrain_path = os.path.join(new_scenario_path, 'topography')
    new_weather_path = os.path.join(new_scenario_path, 'weather')

    # Acquire the paths to the data to copy in the current scenario
    current_database_path = locator.get_databases_folder()
    current_terrain_path = locator.get_terrain_folder()
    current_weather_path = locator.get_weather_folder()

    # Copy if needed
    if bool_copy_database:
        os.makedirs(new_database_path, exist_ok=True)
        copy_folder_contents(current_database_path, new_database_path)

    if bool_copy_terrain:
        os.makedirs(new_terrain_path, exist_ok=True)
        copy_folder_contents(current_terrain_path, new_terrain_path)

    if bool_copy_weather:
        os.makedirs(new_weather_path, exist_ok=True)
        copy_folder_contents(current_weather_path, new_weather_path)


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
            # Recursively copy subfolders
            shutil.copytree(source_item, target_item, dirs_exist_ok=True)
        else:
            # Copy individual files
            shutil.copy2(source_item, target_item)

def main(config):

    # Start the timer
    t0 = time.perf_counter()

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    exec_import_csv_from_rhino(config, locator)
    copy_data_from_current_to_new_scenarios(config,locator)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire import files from Rhino/Grasshopper to CEA is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())
