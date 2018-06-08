from __future__ import division
import multiprocessing

__author__ = "Lennart Rogenhofer, Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def get_number_of_processes(config):
    '''
    Returns the number of processes to use for multiprocessing.
    :param config: Configuration file.
    :return number_of_processes: Number of processes to use.
    '''
    if multiprocessing.cpu_count() == 1:
        number_of_processes = 1
    elif config.max_processes < 1:
        number_of_processes = multiprocessing.cpu_count() + config.max_processes
    else:
        number_of_processes = config.max_processes
    return number_of_processes
