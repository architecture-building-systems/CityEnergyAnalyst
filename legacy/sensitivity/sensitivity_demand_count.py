"""
Return the count a list of samples in a specified folder as input for the demand sensitivity analysis.

This reads in the `samples.npy` file produced by the script `sensitivity_demand_samples.py` and prints out the number
of samples contained. This can be used for scripting the demand simulations with a load sharing facility system like
the Euler cluster.
"""

import os
import numpy as np

__author__ = "Jimeno A. Fonseca; Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def count_samples(samples_path):
    """
    Read in the `samples.npy` numpy array from disk in the `samples_path` and report the row count (each row
    in the array is a sample to simulate for either the morris or the sobol method.

    :param samples_path: path to folder with the samples - see sensitivity_demand_samples.py
    :type samples_path: str
    :return: number of samples in the samples folder.
    """
    samples = np.load(os.path.join(samples_path, 'samples.npy'))
    return len(samples)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-S', '--samples-folder', default='.',
                        help='folder to place the output files (samples.npy, problem.pickle) in')
    args = parser.parse_args()

    samples_count = count_samples(samples_path=args.samples_folder)
    print(samples_count)
