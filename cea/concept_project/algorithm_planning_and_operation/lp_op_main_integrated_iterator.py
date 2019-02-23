from lp_op_config import *
import pandas as pd
import os
import subprocess

if __name__ == '__main__':
    lp_op_config_iterator_df = pd.DataFrame.from_csv(os.path.join(LOCATOR, 'lp_op_config_iterator.csv'), index_col=None)

    # Set initial configuration
    lp_op_config_iterator_df['current_id'][0] = lp_op_config_iterator_df['init_id'][0] - 1
    lp_op_config_iterator_df.to_csv(os.path.join(LOCATOR, 'lp_op_config_iterator.csv'), index=False)

    while lp_op_config_iterator_df['current_id'][0] < lp_op_config_iterator_df['max_id'][0]:
        # Iterate configuration
        lp_op_config_iterator_df['current_id'][0] += 1
        lp_op_config_iterator_df.to_csv(os.path.join(LOCATOR, 'lp_op_config_iterator.csv'), index=False)

        # Run lp_op_main_integrated
        subprocess.call([
            'python',
            os.path.join(os.path.dirname(os.path.normpath(__file__)), 'lp_op_main_integrated.py')
        ])

    print('Completed all iterations.')
