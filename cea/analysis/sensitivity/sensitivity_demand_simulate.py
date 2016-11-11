"""
Simulate a single sample from the samples folder using the demand script.
"""
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


def apply_sample_parameters(sample_index, samples_path, scenario_path, simulation_path):
    """
    Copy the reference case from the `scenario_path` to the `simulation_path`. Patch the parameters from
    the problem statement. Return an `InputLocator` implementation that can be used to simulate the demand
    of the resulting scenario.

    :param sample_index: zero-based index into the samples list
    :param samples_path: path to the pre-calculated samples and problem statement
    :param scenario_path: path to the reference case template
    :param simulation_path: a (temporary) path for simulating a scenario that has been patched with a sample
    :return: InputLocator that can be used to simulate the demand in the `simulation_path`
    """
    if os.path.exists(simulation_path):
        shutil.rmtree(simulation_path)
    shutil.copytree(scenario_path, simulation_path)
    locator = InputLocator(scenario_path=simulation_path)

    with open(os.path.join(args.samples_folder, 'problem.pickle'), 'r') as f:
        problem = pickle.load(f)
    samples = np.load(os.path.join(samples_path, 'samples.npy'))
    try:
        sample = samples[sample_index]
    except IndexError:
        return None

    # FIXME: add other variable groups here
    prop_thermal = Gdf.from_file(locator.get_building_thermal())
    for i, key in enumerate(problem['names']):
        print("Setting prop_thermal[%s] to %s" % (key, sample[i]))
        prop_thermal[key] = sample[i]
        # prop_occupancy_df[key] = value
        # list_uses = list(prop_occupancy.drop('PFloor', axis=1).columns)
        # prop_occupancy = prop_occupancy_df.loc[:, (prop_occupancy_df != 0).any(axis=0)]
        # prop_occupancy[list_uses] = prop_occupancy[list_uses].div(prop_occupancy[list_uses].sum(axis=1), axis=0)
    sample_locator = InputLocator(scenario_path=simulation_path)
    prop_thermal.to_file(sample_locator.get_building_thermal())


    return sample_locator


def simulate_demand_sample(locator, weather_path, output_parameters):
    gv = cea.globalvar.GlobalVariables()
    gv.demand_writer = cea.demand.demand_writers.MonthlyDemandWriter(gv)
    gv.multiprocessing = False
    result = demand_main.demand_calculation(locator, weather_path, gv)
    return result[output_parameters]


class SensitivityInputLocator(InputLocator):
    """Overrides `InputLocator` to work with """


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--sample-index', help='Zero-based index into the samples list so simulate', type=int)
    parser.add_argument('-n', '--number-of-simulations', type=int, default=1,
                        help='number of simulations to perform, default 1')
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder (required)', required=True)
    parser.add_argument('-S', '--samples-folder', default='.',
                        help='folder to place the output files (samples.npy, problem.pickle) in')
    parser.add_argument('-t', '--simulation-folder',
                        help='folder to copy the reference case to for simulation')
    parser.add_argument('-w', '--weather', help='Path to the weather file (omit for default)')
    parser.add_argument('-o', '--output-parameters', help='output parameters to use', nargs='+',
                        default=['QHf_MWhyr', 'QCf_MWhyr', 'Ef_MWhyr', 'QEf_MWhyr'])
    args = parser.parse_args()

    for i in range(args.sample_index, args.sample_index + args.number_of_simulations):
        locator = apply_sample_parameters(i, args.samples_folder, args.scenario, args.simulation_folder)
        if not locator:
            # past end of simulations, stop simulating
            break
        if not args.weather:
            args.weather = locator.get_default_weather()
        print("Running demand simulation for sample %i" % i)
        result = simulate_demand_sample(locator, args.weather, args.output_parameters)
        result.to_csv(os.path.join(args.samples_folder, 'result.%i.csv' % i))
