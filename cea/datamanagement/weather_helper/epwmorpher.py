"""
Functions to enable climate morphing for the EPW files based on pyepwmorph

Title: pyepwmorph
Description: This module provides functions to morph EPW files using the pyepwmorph library, a python package authored by Justin McCarty for accessing global climate models and using them to morph time series weather data in EPW files. An independent application can be found at www.morphepw.app. For a peer-reviewed article that uses pyepwmorph, please see https://doi.org/10.1088/1742-6596/2600/8/082005. 
"""

# general import
import os
import shutil

# CEA import
import cea.inputlocator
import cea.config

# pyepwmorph import
# pip install -e pyepwmorph for local dev
from pyepwmorph.tools import workflow as pyepwmorph_workflow
from pyepwmorph.tools import utilities as pyepwmorph_utilities
from pyepwmorph.tools import io as pyepwmorph_io
from pyepwmorph.tools import configuration as pyepwmorph_config

__author__ = "Justin McCarty"
__copyright__ = ["Copyright 2025, Architecture and Building Systems - ETH Zurich"]
__credits__ = ["Justin McCarty"]
__license__ = "GPLv3+"
__version__ = "0.1"
__maintainer__ = ["Justin McCarty"]
__email__ = ["cea@arch.ethz.ch", "mccarty@arch.ethz.ch"]
__status__ = "Production"

def convert_scenario_names(name):
    """
    Convert the scenario names from CEA to the names used in pyepwmorph

    :param string name: name of the scenario in CEA
    :return: name of the scenario in pyepwmorph
    :rtype: string
    """
    if name == "Best Case":
        return "Best Case Scenario"
    elif name == "Moderate":
        return "Middle of the Road"
    elif name == "Upper Middle": 
        return "Upper Middle Scenario"
    elif name == "Worst Case":
        return "Worst Case Scenario"
    else:
        raise ValueError(
            f"Unsupported climate pathway: {name!r}. "
            "Please choose one of: 'Best Case', 'Moderate', 'Upper Middle', or 'Worst Case'."
        )

def morphing_workflow(locator, config):
    """Run the morphing workflow for the specified scenario.

    Args:
        locator (cea.inputlocator.InputLocator): The input locator for the scenario.
        config (cea.config.Configuration): The configuration for the scenario.

    """
    
    # 1. Read the inputs and create a epw_morph_configuration
    # 1.1. project_name and output_directory
    project_name = f"{config.general.project.split(os.sep)[-1]}_{config.general.scenario}"
    # today = datetime.datetime.now().strftime("%Y%m%d")

    output_directory = os.path.dirname(locator.get_weather_file())
    os.makedirs(output_directory, exist_ok=True)

    # 1.2. user_epw_file is specified in the config but defaults to the scenario file
    user_epw_file = locator.get_weather_file()
    if not os.path.exists(user_epw_file):
        raise FileNotFoundError(f"Could not find the specified EPW file: {user_epw_file}")

    # Backup the original weather file only once to preserve the baseline across re-runs
    backup_epw = os.path.join(output_directory, "before_morph_weather.epw")
    if not os.path.exists(backup_epw):
        shutil.copy2(user_epw_file, backup_epw)
    
    user_epw_object = pyepwmorph_io.Epw(user_epw_file)
    
    # 1.3. variable choice is specified in the config but defaults to temperature
    # variables.choices = temperature, radiation, relative_humidity, wind_speed, pressure, dew_point
    user_variables = config.weather_helper.variables
    
    # 1.4 the baseline range against which the calculations are made
    # this the range of years used to calculate the baseline, should be taken from the EPW files
    try:
        baseline_range = user_epw_object.detect_baseline_range()
    except Exception as e:
        print("Could not detect the baseline range from the EPW file, using default of 1985-2014")
        print(f"Error details: {e}")
        baseline_range = (1985, 2014)  # default if the EPW file does not have the years in it
    
    # 1.5 year can be any future year but defaults to 2050
    user_future_year = config.weather_helper.year
    user_future_range = pyepwmorph_utilities.calc_period(user_future_year, baseline_range)
    
    # 1.6 climate pathway can be specified in config but defaults to moderate_case
    user_climate_pathway = config.weather_helper.climate_pathway
    print(f"User pathway is: {user_climate_pathway}")
    
    # 1.7. percentile can be specified in config but defaults to 50 (single choice)
    # percentile.choices = 1, 5, 10, 25, 50, 75, 90, 95, 99
    user_percentile = int(config.weather_helper.percentile)
    
    # 1.8 model_sources is not something the user can change in CEA
    # Sources as of 2025.09.23 using r1i1p1f1
    # 'KACE-1-0-G', 'MRI-ESM2-0', 'GFDL-ESM4', 'INM-CM4-8', 'IPSL-CM6A-LR', 'INM-CM5-0', 'ACCESS-CM2', 'MIROC6', 'EC-Earth3-Veg-LR', 'BCC-CSM2-MR'
    model_sources = [
        'KACE-1-0-G', 'MRI-ESM2-0', 'GFDL-ESM4', 'INM-CM4-8', 'IPSL-CM6A-LR',
        'INM-CM5-0', 'ACCESS-CM2', 'MIROC6', 'EC-Earth3-Veg-LR', 'BCC-CSM2-MR'
    ]

    print(f"User variables are: {user_variables}")
    # 1. create the config object for the morpher
    morph_config = pyepwmorph_config.MorphConfig(project_name, 
                                            user_epw_file, 
                                            user_variables, 
                                            [convert_scenario_names(user_climate_pathway)], 
                                            [user_percentile],
                                            user_future_range, 
                                            output_directory, 
                                            model_sources=model_sources, 
                                            baseline_range=baseline_range)
    
    # # 2. Morph the EPW file
    print(f"Config pathways are: {morph_config.model_pathways}")
    print(f"Config variables are: {morph_config.model_variables}")
    
    # 2.1 get climate model data
    year_model_dict = pyepwmorph_workflow.iterate_compile_model_data(morph_config.model_pathways,
                                                                    morph_config.model_variables,
                                                                    morph_config.model_sources,
                                                                    morph_config.epw.location['longitude'],
                                                                    morph_config.epw.location['latitude'],
                                                                    morph_config.percentiles)
    
    
    # write the new epw file to the output directory
    print("Morphing")
    pathways = [p for p in morph_config.model_pathways if p != "historical"]
    if not pathways:
        raise ValueError(f"No non-historical pathway available in morph_config.model_pathways: {morph_config.model_pathways}")
    selected_pathway = pathways[0]
    morphed_data = pyepwmorph_workflow.morph_epw(
        morph_config.epw,
        morph_config.user_variables,
        morph_config.baseline_range,
        user_future_range,
        year_model_dict,
        selected_pathway,
        user_percentile,
    )
    morphed_data.dataframe['year'] = int(user_future_year)

    # morphed_data.write_to_file(os.path.join(morph_config.output_directory,
    #                                         f"{str(user_future_year)}_{user_climate_pathway}_{percentile_key}.epw"))

    morphed_data.write_to_file(os.path.join(morph_config.output_directory,"weather.epw"))
    
        

def main(config):
    """
    This script uses the pyepwmorph library to morph an EPW file based on user-defined parameters in the config file.
    
    Args:
        config (cea.config.Configuration): The configuration for the scenario.
    """
    assert os.path.exists(
        config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)
    print(f"{'=' * 10} Starting the climate morphing workflow for scenario {config.general.scenario} {'=' * 10}")
    morphing_workflow(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())