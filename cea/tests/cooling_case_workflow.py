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


def main(config):
    if not config.cooling_case_workflow.scenario:
        working_dir = os.path.join(tempfile.gettempdir(),
                                   datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S-cooling-case-workflow'))
        os.mkdir(working_dir)
        cea.api.extract_reference_case(destination=working_dir, case='cooling')
        print('-' * 80)

        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = os.path.join(working_dir, 'reference-case-cooling', 'baseline')
        config.weather = 'Singapore'
        # local variables
        config.optimization.district_cooling_network = True
        config.config.supply_system_simulation.district_cooling_network = True
        config.thermal_network.network_type = 'DC'
        config.data_helper.region = 'SG'
    else:
        # load the saved config
        workflow_scenario = config.cooling_case_workflow.scenario
        config = cea.config.Configuration(os.path.join(workflow_scenario, 'cea.config'))
        config.scenario = workflow_scenario

    # BUGFIX: the user config file contains the proper daysim bin folder for the os / setup
    user_config = cea.config.Configuration()
    config.radiation_daysim.daysim_bin_directory = user_config.radiation_daysim.daysim_bin_directory

    config_file = os.path.join(config.scenario, 'cea.config')
    config.save(config_file)
    print('Configuration file saved to {config_file}'.format(config_file=config_file))

    def run(script, **kwargs):
        print('Running {script} with args {args}'.format(script=script, args=kwargs))
        f = getattr(cea.api, script.replace('-', '_'))
        f(config=config, **kwargs)
        print('-' * 80)

    scripts_to_run = [
        ('data-helper', {}),  # last=0
        ('radiation-daysim', {}),  # last=1
        ('demand', {}),  # last=2
        ('emissions', {}),  # last=3
        ('operation-costs', {}),  # last=4
        ('network-layout', {'network_type': 'DC'}),  # last=5
        ('water-body-potential', {}),  # last=6
        ('sewage-potential', {}),  # last=7
        ('shallow-geothermal-potential', {}),  # last=7
        ('photovoltaic', {}),  # last=8
        ('solar-collector', {'type_scpanel': 'FP'}),  # last=9
        ('solar-collector', {'type_scpanel': 'ET'}),  # last=10
        ('photovoltaic-thermal', {'type_scpanel': 'FP'}),  # last=11
        ('photovoltaic-thermal', {'type_scpanel': 'ET'}),  # last=12
        ('thermal-network', {'network_type': 'DC', 'use_representative_week_per_month': True}),  # last=13
        ('thermal-network-optimization', {'network_type': 'DC', 'use_representative_week_per_month': True,
                                          'yearly_cost_calculations': True}),  # last=14
        ('decentralized', {}),  # last=15
        ('optimization', {'district-heating-network': False,
                          'district-cooling-network' : True,
                          'population-size': 2,
                          'number-of-generations': 2,
                          'random-seed': 1234}),  # last=16
        ('multi-criteria-analysis', {'generation': 2}),  # last=17
        ('plots-optimization', {'multicriteria': True, 'generations': 2}),  # last=18
    ]

    # skip steps already performed
    scripts_to_run = scripts_to_run[config.cooling_case_workflow.last:]

    for script, kwargs in scripts_to_run:
        start_time = datetime.datetime.now()
        run(script, **kwargs)
        config.restricted_to = None
        print("Execution time: %.2fs" % (datetime.datetime.now() - start_time).total_seconds())
        config.cooling_case_workflow.last += 1
        config.save(config_file)

    print('done.')


if __name__ == '__main__':
    main(cea.config.Configuration())
