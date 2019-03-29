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
    config.district_cooling_network = True
    config.thermal_network.network_type = 'DC'

    config_file = os.path.join(config.scenario, 'cea.config')
    config.save(config_file)
    print('Configuration file saved to {config_file}'.format(config_file=config_file))

    def run(script, **kwargs):
        f = getattr(cea.api, script.replace('-', '_'))
        f(config=config, **kwargs)
        print('-' * 80)

    run('data-helper')
    run('radiation-daysim')
    run('demand')
    run('emissions')
    run('operation-costs')
    run('network-layout', network_type='DC')
    run('lake-potential')
    run('sewage-potential')
    run('photovoltaic')
    run('solar-collector', type_scpanel='FP')
    run('solar-collector', type_scpanel='ET')
    run('photovoltaic-thermal', type_scpanel='FP')
    run('photovoltaic-thermal', type_scpanel='ET')
    run('thermal-network')
    run('decentralized')
    run('thermal-network-optimization')  # FIXME: what is this?!
    run('optimization')
    run('multi-criteria-analysis')
    run('plots', network_type='DC')
    run('plots-supply-system', network_type='DC')
    run('plots-optimization', network_type='DC')

    print('done.')


if __name__ == '__main__':
    main()
