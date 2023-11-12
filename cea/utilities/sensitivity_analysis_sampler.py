"""
Sampling CEA inputs for sensitivity analysis using Sobol Method
"""

import os
import pandas as pd
import cea.config
import cea.inputlocator
from SALib.sample import saltelli

__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Zhongming Shi"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def problem_for_salib(names_vars, bounds_vars):
    """
    creates the problem as the inputs for SALib's sampling functionality.
    :param names_vars: list of the variable names, for example, ['x1', 'x2', 'x3']
    :type names_vars: list
    :param names_vars: list of bounds of each variable, for example, [[-3.14159265359, 3.14159265359],
    [-3.14159265359, 3.14159265359], [-3.14159265359, 3.14159265359]]
    :type names_vars: list

    :return: problem for SALib
    :return type: dictionary
    """

    num_vars = len(names_vars)
    problem = {
        'num_vars': num_vars,
        'names': names_vars,
        'bounds': bounds_vars
    }
    return problem

# Write the results to disk
def write_results(param_values, names_vars, output_path, filename):

    # Make sure directory exists
    os.makedirs(output_path, exist_ok=True)

    sample = pd.DataFrame(param_values, columns=names_vars)
    sample.to_excel(os.path.join(output_path, '{filename}.xlsx'.format(filename=filename)))


def main(config):
    names_vars = ['var_1', 'var_2', 'var_3', 'var_4', 'var_5']

    var_1_l = config.sensitivity_analysis_tools.variable_1_lower_bound
    var_1_u = config.sensitivity_analysis_tools.variable_1_upper_bound
    var_2_l = config.sensitivity_analysis_tools.variable_2_lower_bound
    var_2_u = config.sensitivity_analysis_tools.variable_2_upper_bound
    var_3_l = config.sensitivity_analysis_tools.variable_3_lower_bound
    var_3_u = config.sensitivity_analysis_tools.variable_3_upper_bound
    var_4_l = config.sensitivity_analysis_tools.variable_4_lower_bound
    var_4_u = config.sensitivity_analysis_tools.variable_4_upper_bound
    var_5_l = config.sensitivity_analysis_tools.variable_5_lower_bound
    var_5_u = config.sensitivity_analysis_tools.variable_5_upper_bound

    sample_n = config.sensitivity_analysis_tools.sample_n

    bounds_vars = [[var_1_l, var_1_u],
                   [var_2_l, var_2_u],
                   [var_3_l, var_3_u],
                   [var_4_l, var_4_u],
                   [var_5_l, var_5_u]
                   ]

    filename = config.sensitivity_analysis_tools.file_name
    output_path = config.sensitivity_analysis_tools.file_path

    # Clean the lists when there are less than 5 variables
    nan_idx = next((i for i, v in enumerate(bounds_vars) if sum(v) != sum(v)), -1)
    bounds_vars.pop(nan_idx)
    names_vars.pop(nan_idx)

    # Construct the Problem for SALib
    problem = problem_for_salib(names_vars, bounds_vars)

    # Generate samples
    param_values = saltelli.sample(problem, sample_n, calc_second_order=False)
    # The Saltelli sampler generates samples N*(2D+2), where N is the argument we supplied
    # and D is the number of model inputs.

    # Write the results to disk
    write_results(param_values, names_vars, output_path, filename)


if __name__ == '__main__':
    main(cea.config.Configuration())
