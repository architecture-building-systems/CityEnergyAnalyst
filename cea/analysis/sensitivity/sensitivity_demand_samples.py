"""
Create a list of samples in a specified folder as input for the demand sensitivity analysis.
"""
import os

import numpy as np
import pandas as pd
from SALib.sample.saltelli import sample as sampler_sobol
from SALib.sample.morris import sample as sampler_morris
from cea.inputlocator import InputLocator


def create_demand_samples(method='morris', num_samples=1000, variable_groups=('THERMAL',), sampler_parameters={}):
    """
    :param sampler_parameters: additional, sampler-specific parameters. For `method='morris'` these are: [grid_jump,
                           num_levels], for `method='sobol'` these are: [calc_second_order]
    :param method: The method to use. Valid values are 'morris' (default) and 'sobol'.
    :param num_samples: The number of samples `N` to make
    :param variable_groups: list of names of groups of variables to analyse. Possible values are:
        'THERMAL', 'ARCHITECTURE', 'INDOOR_COMFORT', 'INTERNAL_LOADS'. This list links to the probability density
        functions of the variables contained in locator.get_uncertainty_db() and refers to the Excel worksheet name.
    :return: (samples, problem) - samples is a list of configurations for each simulation to run, a configuration being
        a list of values for each variable in the problem. The problem is a dictionary with the keys 'num_vars',
        'names' and 'bounds' and describes the variables being sampled: 'names' is list of variable names of length
        'num_vars' and 'bounds' is a list of tuples(lower-bound, upper-bound) for each of these variables.
    """
    locator = InputLocator(None)

    # get probability density functions of all variable_groups
    pdf = pd.concat([pd.read_excel(locator.get_uncertainty_db(), group, axis=1) for group in variable_groups])
    num_vars = pdf.name.count()  # integer with number of variables
    names = pdf.name.values  # [,,] with names of each variable
    bounds = []  # a list of two-tuples containing the lower-bound and upper-bound of each variable
    for var in range(num_vars):
        limits = [pdf.loc[var, 'min'], pdf.loc[var, 'max']]
        bounds.append(limits)

    # define the problem
    problem = {'num_vars': num_vars, 'names': names, 'bounds': bounds, 'groups': None}

    return sampler(method, problem, num_samples, sampler_parameters), problem

# create samples (combinations of variables)
def sampler(method, problem, num_samples, sampler_parameters):
    if method == 'sobol':
        return sampler_sobol(problem, N=num_samples, **sampler_parameters)
    elif method == 'morris':
        return sampler_morris(problem, N=num_samples, **sampler_parameters)
    else:
        raise ValueError("Sampler method unknown: %s" % method)

if __name__ == '__main__':
    import argparse
    import pickle

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--method', help='Method to use valid values: "morris" (default), "sobol"',
                        default='morris')
    parser.add_argument('-n', '--num-samples', help='number of samples (generally 1000 or until it converges',
                        default=1000, type=int)
    parser.add_argument('--calc-second-order', help='(sobol) calc_second_order parameter', type=bool,
                        default=False)
    parser.add_argument('--grid-jump', help='(morris) grid_jump parameter', type=int,
                        default=2)
    parser.add_argument('--num-levels', help='(morris) num_levels parameter', type=int,
                        default=4)
    parser.add_argument('-S', '--samples-folder', default='.',
                        help='folder to place the output files (samples.npy, problem.pickle) in')
    parser.add_argument('-V', '--variable-groups', default=['THERMAL'], nargs='+',
                        help=('list of variable groups. Valid values: THERMAL, ARCHITECTURE, ' +
                              'INDOOR_COMFORT, INTERNAL_LOADS'))
    args = parser.parse_args()

    sampler_params = {}
    if args.method == 'morris':
        sampler_params['grid_jump'] = args.grid_jump
        sampler_params['num_levels'] = args.num_levels
    elif args.method == 'sobol':
        sampler_params['calc_second_order'] = args.calc_second_order

    samples, problem_dict = create_demand_samples(method=args.method, num_samples=args.num_samples,
                                                  variable_groups=args.variable_groups,
                                                  sampler_parameters=sampler_params)

    # save out to disk
    np.save(os.path.join(args.samples_folder, 'samples.npy'), samples)
    with open(os.path.join(args.samples_folder, 'problem.pickle'), 'w') as f:
        pickle.dump(problem_dict, f)
    print('created %i samples in %s' % (samples.shape[0], args.samples_folder))
