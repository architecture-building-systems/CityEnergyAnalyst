"""
Analyze the results in the samples folder and write them out to an Excel file. This script assumes:

- all the results have been added to `--samples-folder` in the format `result.%i.csv`, with `%i` replaced by the index
  into the samples array.
- each result file has the same list of columns (the `--output-parameters` for the simulations were the same)
- the `analyze_sensitivity` function is called with the same method and arguments as the sampling routine.
"""
import os
import numpy as np
import pickle

import pandas as pd
from SALib.analyze import sobol
from SALib.analyze import morris


def analyze_sensitivity(samples_path, method, parameters):
    """Run the analysis for each output parameter"""

    with open(os.path.join(args.samples_folder, 'problem.pickle'), 'r') as f:
        problem = pickle.load(f)
    samples = np.load(os.path.join(samples_path, 'samples.npy'))

    samples_count = len(samples)
    simulations = read_results(samples_path, samples_count)
    buildings_num = simulations[0].shape[0]
    writer = pd.ExcelWriter(os.path.join(samples_path, 'analysis_%s_%i.xls' % (method, samples_count)))

    output_parameters = list(simulations[0].columns[1:])
    for parameter in output_parameters:
        results_1 = []
        results_2 = []
        results_3 = []
        for building in range(buildings_num):
            simulations_parameter = np.array([x.loc[building, parameter] for x in simulations])
            if method == 'sobol':
                VAR1, VAR2, VAR3 = 'S1', 'ST', 'ST_conf'
                sobol_result = sobol.analyze(problem, simulations_parameter,
                                             calc_second_order=parameters['calc_second_order'])
                results_1.append(sobol_result['S1'])
                results_2.append(sobol_result['ST'])
                results_3.append(sobol_result['ST_conf'])
            elif method == 'morris':
                VAR1, VAR2, VAR3 = 'mu_star', 'sigma', 'mu_star_conf'
                morris_result = morris.analyze(problem, samples, simulations_parameter,
                                               grid_jump=parameters['grid_jump'],
                                               num_levels=parameters['num_levels'])
                results_1.append(morris_result['mu_star'])
                results_2.append(morris_result['sigma'])
                results_3.append(morris_result['mu_star_conf'])
            else:
                raise ValueError('Invalid sampler method: %s' %s)
        pd.DataFrame(results_1, columns=problem['names']).to_excel(writer, parameter + VAR1)
        pd.DataFrame(results_2, columns=problem['names']).to_excel(writer, parameter + VAR2)
        pd.DataFrame(results_3, columns=problem['names']).to_excel(writer, parameter + VAR3)

    writer.save()


def read_results(samples_folder, samples_count):
    """Read each `results.%i.csv` file into a DataFrame and return them as a list."""
    results = []
    for i in range(samples_count):
        result_file = os.path.join(samples_folder, 'result.%i.csv' % i)
        df = pd.read_csv(result_file)
        results.append(df)
    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-S', '--samples-folder', default='.',
                        help='folder to place the output files (samples.npy, problem.pickle) in')
    parser.add_argument('-m', '--method', help='Method to use valid values: "morris" (default), "sobol"',
                        default='morris')
    parser.add_argument('--calc-second-order', help='(sobol) calc_second_order parameter', type=bool,
                        default=False)
    parser.add_argument('--grid-jump', help='(morris) grid_jump parameter', type=int,
                        default=2)
    parser.add_argument('--num-levels', help='(morris) num_levels parameter', type=int,
                        default=4)
    args = parser.parse_args()

    sampler_params = {}
    if args.method == 'morris':
        sampler_params['grid_jump'] = args.grid_jump
        sampler_params['num_levels'] = args.num_levels
    elif args.method == 'sobol':
        sampler_params['calc_second_order'] = args.calc_second_order

    analyze_sensitivity(samples_path=args.samples_folder, method=args.method, parameters=sampler_params)
