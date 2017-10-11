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
import shutil
import pickle
import numpy as np
import pandas as pd
from geopandas import GeoDataFrame as Gdf

import cea.demand.demand_writers
import cea.globalvar
from cea.demand import demand_main
from cea.inputlocator import InputLocator


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
    locator = InputLocator(scenario_path=simulation_path)

    with open(os.path.join(samples_path, 'problem.pickle'), 'r') as f:
        problem = pickle.load(f)
    samples = np.load(os.path.join(samples_path, 'samples.npy'))
    try:
        sample = samples[sample_index]
    except IndexError:
        return None

    prop = Gdf.from_file(locator.get_zone_geometry()).set_index('Name')
    prop_overrides = pd.DataFrame(index=prop.index)
    for i, key in enumerate(problem['names']):
        print("Setting prop_overrides['%s'] to %s" % (key, sample[i]))
        prop_overrides[key] = sample[i]

    sample_locator = InputLocator(scenario_path=simulation_path)
    prop_overrides.to_csv(sample_locator.get_building_overrides())

    return sample_locator


def simulate_demand_sample(locator, weather_path, output_parameters):
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
    gv.demand_writer = cea.demand.demand_writers.MonthlyDemandWriter(gv)
    # force simulation to be sequential
    totals, time_series = demand_main.demand_calculation(locator, weather_path, gv, multiprocessing=False)
    return totals[output_parameters], time_series

def simulate_demand_batch(sample_index, batch_size, samples_folder, scenario, simulation_folder, weather,
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
        if not locator:
            # past end of simulations, stop simulating
            break
        if not weather:
            weather = locator.get_default_weather()
        print("Running demand simulation for sample %i" % i)
        totals, time_series = simulate_demand_sample(locator, weather, output_parameters)

        # save results in samples folder
        totals.to_csv(os.path.join(samples_folder, 'result.%i.csv' % i))
        for j, item in enumerate(time_series):
            item.to_csv(os.path.join(samples_folder, 'result.%i.%i.csv' % (i , j)))

def main():
    """
    Parse the arguments passed to the script and run `simulate_demand_sample` for each sample in the current
    batch.

    The current batch is the list of samples starting at `--sample-index`, up until
    `--sample-index + --number-of-simulations`.

    Run this script with the argument `--help` to get an overview of the parameters.
    """
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--sample-index', help='Zero-based index into the samples list to simulate', type=int)
    parser.add_argument('-n', '--number-of-simulations', type=int, default=1,
                        help='number of simulations to perform, default 1')
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder (required)', required=True)
    parser.add_argument('-S', '--samples-folder', default='.',
                        help='folder to place the output files (samples.npy, problem.pickle) in')
    parser.add_argument('-t', '--simulation-folder',
                        help='folder to copy the reference case to for simulation')
    parser.add_argument('-w', '--weather', help='Path to the weather file (omit for default)')
    parser.add_argument('-o', '--output-parameters', help='output parameters to use', nargs='+',
                        default=['QHf_MWhyr', 'QCf_MWhyr', 'Ef_MWhyr', 'QEf_MWhyr', 'QHf0_kW', 'QCf0_kW', 'Ef0_kW'])
    args = parser.parse_args()

    # save output parameters
    np.save(os.path.join(args.samples_folder, 'output_parameters.npy'), np.array(args.output_parameters))

    simulate_demand_batch(sample_index=args.sample_index, batch_size=args.number_of_simulations,
                          samples_folder=args.samples_folder, scenario=args.scenario,
                          simulation_folder=args.simulation_folder, weather=args.weather,
                          output_parameters=args.output_parameters)



if __name__ == '__main__':
    main()
