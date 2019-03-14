from __future__ import division
import pandas as pd
import os
from concept import config
from concept.algorithm_planning_and_operation import planning_and_operation_main

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def main(
        scenario_data_path=config.scenario_data_path,
):
    config_df = pd.DataFrame.from_csv(os.path.join(scenario_data_path, 'config.csv'), index_col=None)

    index = 0
    while index < len(config_df.index):
        scenario = os.path.normpath(config_df['scenario'][index])
        beta = float(config_df['beta'][index])
        load_factor = float(config_df['load_factor'][index])

        # Run lp_op_main_integrated
        planning_and_operation_main.main(
            scenario=scenario,
            beta=beta,
            load_factor=load_factor
        )

        index += 1

    print('Completed all iterations.')


if __name__ == '__main__':
    main()
