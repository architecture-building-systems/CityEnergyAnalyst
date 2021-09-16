"""
Save multiple files into one hdf5 per folder.
"""

import os
import pandas as pd

import cea.config
import cea.inputlocator


__author__ = "Shanshan Hsieh"
__copyright__ = "Copyright 2021, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Shanshan Hsieh"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    path_to_data_folder = locator.get_outputs_data_folder()
    path_to_hdf5_folder = os.path.join(path_to_data_folder, 'data_in_hdf5')
    if not os.path.exists(path_to_hdf5_folder):
        os.mkdir(path_to_hdf5_folder)

    for result_folder in os.listdir(path_to_data_folder):
        result_folder_path = os.path.join(os.path.join(path_to_data_folder, result_folder))
        if 'hdf5' not in result_folder:
            store = pd.HDFStore(os.path.join(path_to_hdf5_folder, result_folder + '.h5'), complevel=1)
            for csv_file in os.listdir(result_folder_path):
                if '.csv' in csv_file:
                    df = pd.read_csv(os.path.join(result_folder_path, csv_file))
                    store[csv_file.split('.')[0]] = df
            store.close()
            print('files in ', result_folder, 'folder are saved in ', result_folder + '.h5')


if __name__ == '__main__':
    main(cea.config.Configuration())