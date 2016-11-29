"""
Simulate a single sample from the samples folder using the demand script.
"""
import os
import shutil
import pickle
import numpy as np
import pandas as pd
import simpledbf
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

    # get problem and samples
    if os.path.exists(simulation_path):
        shutil.rmtree(simulation_path)
    shutil.copytree(scenario_path, simulation_path)
    sample_locator = InputLocator(scenario_path=simulation_path)

    with open(os.path.join(samples_path, 'problem.pickle'), 'r') as f:
        problem = pickle.load(f)
    samples = np.load(os.path.join(samples_path, 'samples.npy'))
    try:
        sample = samples[sample_index]
    except IndexError:
        return None

    # create dataframe with length equal to all buildings
    prop_thermal = simpledbf.Dbf5(sample_locator.get_building_thermal()).to_dataframe().set_index('Name')
    prop_overrides = pd.DataFrame(index=prop_thermal.index)

    for i, key in enumerate(problem['names']):
        print("Setting prop_overrides['%s'] to %s" % (key, sample[i]))
        prop_overrides[key] = sample[i]

    # save in disc
    prop_overrides.to_csv(sample_locator.get_building_overrides())

    return sample_locator


def simulate_demand_sample(locator, weather_path, output_parameters):
    # force simulation to be sequential
    gv = cea.globalvar.GlobalVariables()
    gv.demand_writer = cea.demand.demand_writers.MonthlyDemandWriter(gv)
    gv.multiprocessing = False
    gv.sensitivity_analysis = True
    result = demand_main.demand_calculation(locator, weather_path, gv)
    return result[output_parameters]

def main():
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
                                 'Ef0_kW'])
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


if __name__ == '__main__':
    main()
