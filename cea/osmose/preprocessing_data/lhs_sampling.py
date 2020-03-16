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
    'Building': {
        'num_vars': 7,
        'names':['capex_weight', 'dT1', 'dT2', 'dT3', 'dT4', 'dT_sc', 'T5'],
        'bounds':[[0,1],[10,15],[8,10],[2,4],[2,4],[0.01,5],[4,7]]
        },
}

problem_name = 'Building'
number_of_samples = 100
iterations = 100000

def main():
    # get problem
    problem = problem_dict[problem_name]
    # lhs sampling
    lhs_samples = lhs(problem['num_vars'], samples=number_of_samples, criterion='maximin', iterations=iterations)
    scale_samples(lhs_samples, problem['bounds'])  # scale samples in-place
    # output_flat
    df = pd.DataFrame(lhs_samples)
    path_to_osmose_projects = 'E:\\OSMOSE_projects\\HCS_mk\\Projects\\'
    df.to_csv(os.path.join(path_to_osmose_projects,problem_name + '_flat.dat'), index=False, header=False,
              line_terminator=',\n', )
    print('file saved to ', path_to_osmose_projects)
    return

if __name__ == '__main__':
    main()