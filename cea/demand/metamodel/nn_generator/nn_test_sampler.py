# coding=utf-8
"""
'nn_test_sampler.py' script generates one random sample for the entire case-study,
to be called sequentially if necessary
"""

__author__ = "Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

from cea.demand.calibration.latin_sampler import latin_sampler
from cea.demand.demand_main import properties_and_schedule
from cea.demand.calibration.bayesian_calibrator.calibration_sampling import apply_sample_parameters
from cea.demand import demand_main
import pickle
import cea.inputlocator
import cea.globalvar
import cea.config
import numpy as np
import pandas as pd
from cea.demand.metamodel.nn_generator.nn_settings import random_variables,\
    target_parameters, boolean_vars
from cea.demand.metamodel.nn_generator.input_prepare import input_prepare_main
from geopandas import GeoDataFrame as Gdf

def sampling_single(locator, random_variables, target_parameters, list_building_names, config,
                    nn_delay, climatic_variables, region, year, use_daysim_radiation,use_stochastic_occupancy):
    size_city = np.shape(list_building_names)
    size_city=size_city[0]

    bld_counter = 0
    # create list of samples with a LHC sampler and save to disk (*.csv)
    samples, samples_norm, pdf_list = latin_sampler(locator, size_city, random_variables, region)
    for building_name in (list_building_names):
        np.save(locator.get_calibration_folder(), samples)
        building_load = config.single_calibration.load
        override_file = Gdf.from_file(locator.get_zone_geometry()).set_index('Name')
        override_file = pd.DataFrame(index=override_file.index)
        problem = {'variables': random_variables,
                   'building_load': target_parameters, 'probabiltiy_vars': pdf_list}
        pickle.dump(problem, file(locator.get_calibration_problem(building_name,building_load), 'w'))
        sample = np.asarray(zip(random_variables, samples[bld_counter, :]))
        apply_sample_parameters(locator, sample, override_file)
        bld_counter = bld_counter + 1
    # read the saved *.csv file and replace Boolean with logical (True/False)
    overwritten = pd.read_csv(locator.get_building_overrides())
    bld_counter = 0
    for building_name in (list_building_names):
        sample = np.asarray(zip(random_variables, samples[bld_counter, :]))
        for boolean_mask in (boolean_vars):
            indices = np.where(sample == boolean_mask)

            if sample[indices[0], 1] == '0.0':
                sample[indices[0], 1] = 'False'
            else:
                sample[indices[0], 1] = 'True'

        overwritten.loc[overwritten.Name == building_name, random_variables] = sample[:, 1]
        bld_counter = bld_counter + 1

    # write to csv format
    overwritten.to_csv(locator.get_building_overrides())

    #   run cea demand
    demand_main.demand_calculation(locator, config)

    #   prepare the inputs for feeding into the neural network
    urban_input_matrix, urban_taget_matrix = input_prepare_main(list_building_names, locator, target_parameters,
                                                                nn_delay, climatic_variables, region, year,
                                                                use_daysim_radiation,use_stochastic_occupancy)

    return urban_input_matrix, urban_taget_matrix


def main(config):
    settings = config.demand
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    building_properties, schedules_dict, date = properties_and_schedule(locator)
    list_building_names = building_properties.list_building_names()
    urban_input_matrix, urban_taget_matrix = sampling_single(locator, random_variables, target_parameters,
                                                             list_building_names, config=config,
                                                             nn_delay=config.neural_network.nn_delay,
                                                             climatic_variables=config.neural_network.climatic_variables,
                                                             region=config.region, year=config.neural_network.year,
                                                             use_daysim_radiation=settings.use_daysim_radiation,
                                                             use_stochastic_occupancy=config.demand.use_stochastic_occupancy)

if __name__ == '__main__':
    main(cea.config.Configuration())
