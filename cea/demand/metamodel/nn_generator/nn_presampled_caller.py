# coding=utf-8
"""
'nn_trainer.py' script fits a neural net on inputs and targets
"""

__author__ = "Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

import os
import numpy as np
import pandas as pd
from cea.demand.metamodel.nn_generator.nn_random_sampler import input_dropout
from cea.demand.metamodel.nn_generator.nn_settings import number_samples

def presampled_collector(locator,collect_count):
    nn_presample_path = locator.get_minmaxscaler_folder()
    i=0
    j=0
    for i in range(number_samples):
        i = collect_count + i
        file_path_inputs = os.path.join(nn_presample_path, "input%(i)s.csv" % locals())
        file_path_targets = os.path.join(nn_presample_path, "target%(i)s.csv" % locals())
        batch_input_matrix = np.asarray(pd.read_csv(file_path_inputs))
        batch_taget_matrix = np.asarray(pd.read_csv(file_path_targets))
        batch_input_matrix, batch_taget_matrix = input_dropout(batch_input_matrix, batch_taget_matrix)
        if j < 1:
            urban_input_matrix = batch_input_matrix
            urban_taget_matrix = batch_taget_matrix
        else:
            urban_input_matrix = np.concatenate((urban_input_matrix, batch_input_matrix), axis=0)
            urban_taget_matrix = np.concatenate((urban_taget_matrix, batch_taget_matrix), axis=0)
        j=j+1
        print(i)

    collect_count=i+1


    return urban_input_matrix, urban_taget_matrix, collect_count
