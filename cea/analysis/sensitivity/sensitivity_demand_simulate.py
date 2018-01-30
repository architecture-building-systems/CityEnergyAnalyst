"""
Simulate a single sample or a batch of samples from the samples folder using the demand script.

The script `sensitivity_demand_samples.py` creates a samples folder containing a list of samples stored in the NumPy
array `samples.npy`. Each sample is a list of parameter values to set for a list of variables (the names of the
variables are stored in the file `problem.pickle` in the samples folder).

This script runs the samples `--sample-index` through `--sample-index + --number-of-samples` and writes the results
out to the samples folder as files of the form `results.$i.csv` (with `$i` set to the index into the samples array).
"""

from __future__ import division

import os
import sys
import shutil
import pickle
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf

import cea.demand.demand_writers
import cea.globalvar
from cea.demand import demand_main
from cea.inputlocator import InputLocator
import cea.config

__author__ = "Jimeno A. Fonseca; Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def apply_sample_parameters(sample_index, samples_path, scenario_path, simulation_path):
    """
    Copy the scenario from the `scenario_path` to the `simulation_path`. Patch the parameters from
    the problem statement. Return an `InputLocator` implementation that can be used to simulate the demand
    of the resulting scenario.

    The `simulation_path` is modified by the demand calculation. For the purposes of the sensitivity analysis, these
    changes can be viewed as temporary and deleted / overwritten after each simulation.

    :param sample_index: zero-based index into the samples list, which is read from the file `$samples_path/samples.npy`
    :type sample_index: int

    :param samples_path: path to the pre-calculated samples and problem statement (created by
                        `sensitivity_demand_samples.py`)
    :type samples_path: str

    :param scenario_path: path to the scenario template
    :type scenario_path: str

    :param simulation_path: a (temporary) path for simulating a scenario that has been patched with a sample
                            NOTE: When simulating in parallel, special care must be taken that each process has
                            a unique `simulation_path` value. For the Euler cluster, this is solved by ensuring the
                            simulation is done with `multiprocessing = False` and setting the `simulation_path` to
                            the special folder `$TMPDIR` that is set to a local scratch folder for each job by the
                            job scheduler of the Euler cluster. Other setups will need to adopt an equivalent strategy.
    :type simulation_path: str

    :return: InputLocator that can be used to simulate the demand in the `simulation_path`
    """
    if os.path.exists(simulation_path):
        shutil.rmtree(simulation_path)
    shutil.copytree(scenario_path, simulation_path)
    locator = InputLocator(scenario=simulation_path)

    problem = read_problem(samples_path)
    samples = read_samples(samples_path)
    try:
        sample = samples[sample_index]
    except IndexError:
        return None

    prop = Gdf.from_file(locator.get_zone_geometry()).set_index('Name')
    prop_overrides = pd.DataFrame(index=prop.index)
    for i, key in enumerate(problem['names']):
        print("Setting prop_overrides['%s'] to %s" % (key, sample[i]))
        prop_overrides[key] = sample[i]

    sample_locator = InputLocator(scenario=simulation_path)
    prop_overrides.to_csv(sample_locator.get_building_overrides())

    return sample_locator


def read_problem(samples_path):
    with open(os.path.join(samples_path, 'problem.pickle'), 'r') as f:
        problem = pickle.load(f)
    return problem


def read_samples(samples_path):
    samples = np.load(os.path.join(samples_path, 'samples.npy'))
    return samples


def simulate_demand_sample(locator, config, output_parameters):
    """
    Run a demand simulation for a single sample. This function expects a locator that is already initialized to the
    simulation folder, that has already been prepared with `apply_sample_parameters`.

    :param locator: The InputLocator to use for the simulation
    :type locator: InputLocator

    :param weather: The path to the weather file (``*.epw``) to use for simulation. See the `weather_path` parameter in
                    `cea.demand.demand_main.demand_calculation` for more information.
    :type weather: str

    :param output_parameters: The list of output parameters to save to disk. This is a column-wise subset of the
                              output of `cea.demand.demand_main.demand_calculation`.
    :type output_parameters: list of str

    :return: Returns the columns of the results of `cea.demand.demand_main.demand_calculation` as defined in
            `output_parameters`.
    :rtype: pandas.DataFrame
    """

    gv = cea.globalvar.GlobalVariables()

    # MODIFY CONFIG FILE TO RUN THE DEMAND FOR ONLY SPECIFIC QUANTITIES
    config.demand.resolution_output = "monthly"
    config.multiprocessing = False
    config.demand.massflows_output = []
    config.demand.temperatures_output = []
    config.demand.format_output = "csv"

    # force simulation to be sequential
    totals, time_series = demand_main.demand_calculation(locator, gv, config)
    return totals[output_parameters], time_series


def simulate_demand_batch(sample_index, batch_size, samples_folder, scenario, simulation_folder, config,
                          output_parameters):
    """
    Run the simulations for a whole batch of samples and write the results out to the samples folder.

    Each simulation result is saved to the samples folder as `result.$i.csv` with `$i` representing the index into
    the samples array.

    :param sample_index: The index into the first sample of the batch as defined in the `samples.npy` NumPy array in
                         the samples folder.
    :type sample_index: int

    :param batch_size: The number of simulations to perform, starting at `sample_index`. When computing on a cluster
                       such as Euler, the batch size should be chosen to minimize overhead of starting up a node
                       on the cluster. For our test purposes, the batch size 100 has proven to be a good default, but
                       you might need to test this for your case.
    :type batch_size: int

    :param samples_folder: The path to the samples folder, containing the `samples.npy` and `problem.pickle` files, as
                           generated by the `sensitivity_demand_samples.py` script. This is the folder where the output
                           of the simulations is written to. It also contains information necessary for applying sample
                           parameters to the input files.
    :type samples_folder: str

    :param scenario: The path to the scenario. This argument corresponds to the `scenario_path` parameter of the
                     InputLocator constructor. For the sensitivity simulations, the scenario is used as a template
                     that is copied to a simulation folder and then modified using the override mechanism to add the
                     sample parameter values. See the function `apply_sample_parameters` for the details of copying
                     the scenario to the simulation folder.
    :type scenario: str

    :param simulation_folder: The path to the folder to use for simulation. The scenario is copied to the simulation
                              folder and updated with the sample parameter values using the function
                              `apply_sample_parameters`.
    :type simulation_folder: str

    :param weather: The path to the weather file (``*.epw``) to use for simulation. See the `weather_path` parameter in
                    `cea.demand.demand_main.demand_calculation` for more information.
    :type weather: str

    :param output_parameters: The list of output parameters to save to disk. This is a column-wise subset of the
                              output of `cea.demand.demand_main.demand_calculation`.
    :type output_parameters: list of str


    :return: None
    """
    for i in range(sample_index, sample_index + batch_size):
        locator = apply_sample_parameters(i, samples_folder, scenario, simulation_folder)
        print("Running demand simulation for sample %i" % i)
        totals, time_series = simulate_demand_sample(locator, config, output_parameters)

        # save results in samples folder
        totals.to_csv(os.path.join(samples_folder, 'result.%i.csv' % i))
        for j, item in enumerate(time_series):
            item.to_csv(os.path.join(samples_folder, 'result.%i.%i.csv' % (i, j)))


def main(config):
    """
    Parse the arguments passed to the script and run `simulate_demand_sample` for each sample in the current
    batch.

    The current batch is the list of samples starting at `--sample-index`, up until
    `--sample-index + --number-of-simulations`.

    Run this script with the argument `--help` to get an overview of the parameters.
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario

    print("Running sensitivity-demand-simulate for scenario = %s" % config.scenario)
    print("Running sensitivity-demand-simulate with weather = %s" % config.weather)
    print("Running sensitivity-demand-simulate with sample-index = %s" % config.sensitivity_demand.sample_index)
    print("Running sensitivity-demand-simulate with number-of-simulations = %s" %
          config.sensitivity_demand.number_of_simulations)
    print("Running sensitivity-demand-simulate with samples-folder = %s" % config.sensitivity_demand.samples_folder)
    print("Running sensitivity-demand-simulate with simulation-folder = %s" %
          config.sensitivity_demand.simulation_folder)
    print("Running sensitivity-demand-simulate with output-parameters = %s" %
          config.sensitivity_demand.output_parameters)

    # save output parameters
    np.save(os.path.join(config.sensitivity_demand.samples_folder, 'output_parameters.npy'),
            np.array(config.sensitivity_demand.output_parameters))

    samples = read_samples(config.sensitivity_demand.samples_folder)
    if config.sensitivity_demand.number_of_simulations is None:
        # simulate all remaining...
        config.sensitivity_demand.number_of_simulations = len(samples) - config.sensitivity_demand.sample_index
    else:
        # ensure batch-size does not exceed number of remaining simulations
        config.sensitivity_demand.number_of_simulations = min(
            config.sensitivity_demand.number_of_simulations,
            len(samples) - config.sensitivity_demand.sample_index)


    simulate_demand_batch(sample_index=config.sensitivity_demand.sample_index,
                          batch_size=config.sensitivity_demand.number_of_simulations,
                          samples_folder=config.sensitivity_demand.samples_folder,
                          scenario=config.scenario,
                          simulation_folder=config.sensitivity_demand.simulation_folder,
                          config=config,
                          output_parameters=config.sensitivity_demand.output_parameters)


if __name__ == '__main__':
    config = cea.config.Configuration()
    config.apply_command_line_args(sys.argv[1:], ['general', 'sensitivity-demand'])
    main(config)
