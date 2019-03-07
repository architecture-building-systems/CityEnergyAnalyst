"""
Run all the scripts for the cooling case, using the cea.api interface.
"""
from __future__ import division
from __future__ import print_function

import os
import datetime
import tempfile
import cea.config
import cea.inputlocator
import cea.api

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main():
    working_dir = os.path.join(tempfile.gettempdir(),
                               datetime.datetime.now().strftime('%Y-%d-%m-%H-%M-%S-cooling-case-workflow'))
    os.mkdir(working_dir)
    cea.api.extract_reference_case(destination=working_dir, case='cooling')
    print('-' * 80)

    config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
    config.scenario = os.path.join(working_dir, 'reference-case-cooling', 'baseline')
    config.region = 'SG'
    config.weather = 'Singapore'

    cea.api.data_helper(config=config)
    print('-' * 80)

    cea.api.radiation_daysim(config=config)
    print('-' * 80)

    cea.api.demand(config=config)
    print('-' * 80)

    config_file = os.path.join(config.scenario, 'cea.config')
    config.save(config_file)
    print('Configuration file saved to {config_file}'.format(config_file=config_file))
    print('done.')


if __name__ == '__main__':
    main()
