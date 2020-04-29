import pandas as pd
import numpy as np
import os
from pyDOE import *
from SALib.util import scale_samples

problem_dict = {
    'Network': {
        'num_vars': 9,
        'names':['capex_weight', 'dT1', 'dT2', 'dT3', 'dT4', 'dT_sc', 'dTn', 'dTn_r', 'T5'],
        'bounds':[[0,1],[10,15],[8,10],[2,4],[2,4],[0,1],[3,4],[7,9],[4,7]]
        },
    "Networks": {
        'num_vars': 9,
        'names':['capex_weight', 'dT1', 'dT2', 'dT3', 'dT4', 'dTn_1', 'dTn_2', 'dTn_3', 'T5'],
        'bounds':[[0,1],[10,15],[8,10],[2,4],[2,4],[5,15],[5,15],[5,15],[4,7]]
    },
    "Networks_fixed": {
        'num_vars': 9,
        'names': ['capex_weight', 'dT1', 'dT2', 'dT3', 'dT4', 'dTn_1', 'dTn_2', 'dTn_3', 'T5'],
        'bounds': [[0, 1], [20, 21], [8, 9], [2, 3], [2, 3], [10, 11], [10, 11], [5, 6], [4, 10]]
    },
    "d_Networks_LT": {
        'num_vars': 20,
        'names': ['capex_weight', 'dT1', 'dT2', 'dT3', 'dT4', 'dT_sc', 'dTn_1', 'dTn_2', 'dTn_3',
                  'HOT_dT1', 'HOT_dT2', 'HOT_dTsc', 'HOT_T3', 'OFF_dT1', 'OFF_dT2', 'OFF_T3',
                  'RET_dT1', 'RET_dT2', 'RET_T3','T5'],
        'bounds': [[0,1], [10,15], [8,10], [2,4], [2,4], [0, 30], [5,15], [5,15], [5,15],
                   [10,30], [5,15], [0.01, 30], [15,20], [10,30], [5,15], [15,20],
                   [10, 30], [5, 15], [15, 20], [4, 7]]
    },
    "d_Networks_HT": {
        'num_vars': 20,
        'names': ['capex_weight', 'dT1', 'dT2', 'dT3', 'dT4', 'dT_sc', 'dTn_1', 'dTn_2', 'dTn_3',
                  'HOT_dT1', 'HOT_dT2', 'HOT_dTsc', 'HOT_T3', 'OFF_dT1', 'OFF_dT2', 'OFF_T3',
                  'RET_dT1', 'RET_dT2', 'RET_T3', 'T5'],
        'bounds': [[0, 1], [10, 15], [8, 10], [2, 4], [2, 4], [0, 30], [5, 15], [5, 15], [5, 15],
                   [4, 10], [10, 30], [0.01, 30], [10, 25], [4, 10], [10, 30], [10, 25],
                   [4, 10], [10, 30], [10, 25], [4, 7]]
    },
    'Buildings': {
        'num_vars': 7,
        'names':['capex_weight', 'dT1', 'dT2', 'dT3', 'dT4', 'dT_sc', 'T5'],
        'bounds':[[0, 1], [10, 20], [8, 10], [2, 4], [2, 4], [0.01, 5], [4, 7]]
        },
    'Buildings_dhw': {
        'num_vars': 7,
        'names': ['capex_weight', 'dT1', 'dT2', 'dT3', 'dT4', 'dT_sc', 'dT5'],
        'bounds': [[0, 1], [20, 25], [10, 20], [2, 6], [2, 6], [0.01, 30], [4, 7]]
    },
}

problem_name = 'd_Networks_HT'
number_of_samples = 300
iterations = 50000   #10000 from Steffen

def main():
    # get problem
    problem = problem_dict[problem_name]
    # get number of variables
    num_names = len(problem['names'])
    num_bounds = len(problem['bounds'])
    if num_bounds == num_names:
        num_vars = problem['num_vars']
        if num_vars == num_names:
            # lhs sampling
            lhs_samples = lhs(problem['num_vars'], samples=number_of_samples, criterion='maximin', iterations=iterations)
            scale_samples(lhs_samples, problem['bounds'])  # scale samples in-place
            # output_flat
            df = pd.DataFrame(lhs_samples)
            # path_to_osmose_projects = 'E:\\OSMOSE_projects\\HCS_mk\\Projects\\'
            path_to_osmose_projects = 'C:\\Users\\Zhongming\\Documents\\HCS_mk\\Projects'
            df.to_csv(os.path.join(path_to_osmose_projects,
                                   problem_name + '_' + str(number_of_samples) + '_flat.dat'),
                      index=False, header=False, line_terminator=',\n', )
            print('file saved to ', path_to_osmose_projects)
        else:
            raise ValueError('number of variables (', num_vars,') does not match number of names {', num_names,')')
    else:
        raise ValueError('number of names (', num_names ,'} does not match number of bounds {', num_bounds,')')
    return

def main2():
    samples = []
    for T5 in np.arange(4,11,0.5):
        for capex_weight in np.arange(0,1,0.2):
            dTn_1 = 12 - (T5-4)
            row = [capex_weight, 0.0, 0.0, 0.0, 0.0, dTn_1, 30, 30, T5]
            samples.append(row)
    df = pd.DataFrame(samples)
    # path_to_osmose_projects = 'E:\\OSMOSE_projects\\HCS_mk\\Projects\\'
    path_to_osmose_projects = 'C:\\Users\\Zhongming\\Documents\\HCS_mk\\Projects'
    df.to_csv(os.path.join(path_to_osmose_projects, 'T5_flat.dat'), index=False, header=False,
              line_terminator=',\n', )
    print('file saved to ', path_to_osmose_projects)
    # 'names': ['capex_weight', 'dT1', 'dT2', 'dT3', 'dT4', 'dTn_1', 'dTn_2', 'dTn_3', 'T5'],

    return

if __name__ == '__main__':
    main()

