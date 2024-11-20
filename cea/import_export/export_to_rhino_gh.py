"""
Export CEA files into Rhino/Grasshopper-ready format.

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

def exec_export_csv_for_rhino(config, locator):
    """

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return:
    """
    # Acquire the user inputs from config
    output_path = config.to_rhino_gh.output_path
    bool_include_zone = config.to_rhino_gh.include_zone
    bool_include_site = config.to_rhino_gh.include_site
    bool_include_surroundings = config.to_rhino_gh.include_surroundings
    bool_include_streets = config.to_rhino_gh.include_streets
    bool_include_trees = config.to_rhino_gh.include_trees


    # Create the folder to store all the exported files if it doesn't exist
    output_path = os.path.join(output_path, 'export', 'rhino')
    os.makedirs(output_path, exist_ok=True)

    # Remove all files in folder
    for filename in os.listdir(output_path):
        file_path = os.path.join(output_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # Export zone info including typology
    if bool_include_zone:
        subprocess.run(['cea', 'shp-to-csv-to-shp',
                        '--input-file', locator.get_zone_geometry(),
                        '--output-file-name', 'zone_to.csv',
                        '--output-path', output_path,
                        ], env=my_env, check=True, capture_output=True)

        # Create the reference.shp
        # Define the possible extensions for shapefile components
        shp_extensions = ['shp', 'dbf', 'shx', 'prj', 'cpg', 'sbx', 'sbn', 'xml']
        # Copy each associated file to the target directory
        file_to_copy = locator.get_zone_geometry()
        base_name = file_to_copy.rsplit('.', 1)[0]  # Split into the base name and extension
        all_to_copy = [f"{base_name}.{ext}" for ext in shp_extensions]
        new_to_copy = [f"reference.{ext}" for ext in shp_extensions]
        for file, file_new in zip(all_to_copy, new_to_copy):
            target_path = os.path.join(output_path, file_new)
            if os.path.exists(file):
                shutil.copy(file,target_path)

        # Export the typology.dbf
        subprocess.run(['cea', 'dbf-to-csv-to-dbf',
                        '--input-file', locator.get_building_typology(),
                        '--output-file-name', 'typology_to.csv',
                        '--output-path', output_path,
                        ], env=my_env, check=True, capture_output=True)

    if bool_include_site and os.path.isfile(locator.get_site_polygon()):
        subprocess.run(['cea', 'shp-to-csv-to-shp',
                        '--input-file', locator.get_site_polygon(),
                        '--output-file-name', 'site_to.csv',
                        '--output-path', output_path,
                        ], env=my_env, check=True, capture_output=True)

    if bool_include_surroundings and os.path.isfile(locator.get_surroundings_geometry()):
        subprocess.run(['cea', 'shp-to-csv-to-shp',
                        '--input-file', locator.get_surroundings_geometry(),
                        '--output-file-name', 'surroundings_to.csv',
                        '--output-path', output_path,
                        ], env=my_env, check=True, capture_output=True)

    if bool_include_streets and os.path.isfile(locator.get_street_network()):
        subprocess.run(['cea', 'shp-to-csv-to-shp',
                        '--input-file', locator.get_street_network(),
                        '--output-file-name', 'streets_to.csv',
                        '--output-path', output_path,
                        ], env=my_env, check=True, capture_output=True)

    if bool_include_trees and os.path.isfile(locator.get_tree_geometry()):
        subprocess.run(['cea', 'shp-to-csv-to-shp',
                        '--input-file', locator.get_tree_geometry(),
                        '--output-file-name', 'trees_to.csv',
                        '--output-path', output_path,
                        ], env=my_env, check=True, capture_output=True)

def main(config):

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
