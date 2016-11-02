"""
Create a list of samples in a specified folder as input for the demand sensitivity analysis.
"""
import os

import numpy as np
import pandas as pd
from SALib.sample.saltelli import sample as sampler_sobol
from SALib.sample.morris import sample as sampler_morris
from cea.inputlocator import InputLocator


def create_demand_samples(method='morris', num_samples=1000, variable_groups=['THERMAL']):
    """

    :param output_folder: Folder to place the output file 'samples.npy' (FIXME: should this be part of the
                          InputLocator?)
    :param method:
    :param num_samples:
    :param variable_groups: list of names of groups of variables to analyse. Possible values are:
        'THERMAL', 'ARCHITECTURE', 'INDOOR_COMFORT', 'INTERNAL_LOADS'. This list links to the probability density
        functions of the variables contained in locator.get_uncertainty_db().
    :return:
    """
    locator = InputLocator(None)

    pdf = pd.concat([pd.read_excel(locator.get_uncertainty_db(), group, axis=1) for group in variable_groups])
    num_vars = pdf.name.count()  # integer with number of variables
    names = pdf.name.values  # [,,] with names of each variable
    bounds = []  # a list of two-tuples containing the lower-bound and upper-bound of each variable
    for var in range(num_vars):
        limits = [pdf.loc[var, 'min'], pdf.loc[var, 'max']]
        bounds.append(limits)

    # define the problem
    problem = {'num_vars': num_vars, 'names': names, 'bounds': bounds, 'groups': None}

    # create samples (combinations of variables)
    def sampler():
        if method is 'sobol':
            second_order = False
            return sampler_sobol(problem, N=num_samples, calc_second_order=second_order)
        else:
            grid = 2
            levels = 4
            return sampler_morris(problem, N=num_samples, grid_jump=grid, num_levels=levels)

    return sampler(), problem


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--method', help='Method to use {morris, sobol}', default='morris')
    parser.add_argument('-n', '--num-samples', help='number of samples (generally 1000 or until it converges',
                        default=1000)
    parser.add_argument('-o', '--output-folder', help='folder to place the output file (samples.npy) in',
                        default='.')
    args = parser.parse_args()

    samples, problem = create_demand_samples(method=args.method, num_samples=args.num_samples)

    # save out to disk
    np.save(os.path.join(args.output_folder, 'samples.npy'), samples)
