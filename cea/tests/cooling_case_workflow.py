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
    else:
        # load the saved config
        workflow_scenario = config.cooling_case_workflow.scenario
        config = cea.config.Configuration(os.path.join(workflow_scenario, 'cea.config'))
        config.scenario = workflow_scenario

    config_file = os.path.join(config.scenario, 'cea.config')
    config.save(config_file)
    print('Configuration file saved to {config_file}'.format(config_file=config_file))

    def run(script, **kwargs):
        f = getattr(cea.api, script.replace('-', '_'))
        f(config=config, **kwargs)
        print('-' * 80)

    scripts_to_run = [
        ('data-helper', {}),
        ('radiation-daysim', {}),
        ('demand', {}),
        ('emissions', {}),
        ('operation-costs', {}),
        ('network-layout', {'network_type': 'DC'}),
        ('lake-potential', {}),
        ('sewage-potential', {}),
        ('photovoltaic', {}),
        ('solar-collector', {'type_scpanel': 'FP'}),
        ('solar-collector', {'type_scpanel': 'ET'}),
        ('photovoltaic-thermal', {'type_scpanel': 'FP'}),
        ('photovoltaic-thermal', {'type_scpanel': 'ET'}),
        ('thermal-network', {'network_type': 'DC'}),
        ('decentralized', {}),
        ('thermal-network-optimization', {'network_type': 'DC'}),
        ('optimization', {'initialind': 2, 'ngen': 2, 'halloffame': 5, 'random-seed': 1234}),
        ('multi-criteria-analysis', {}),
        ('plots', {'network_type': 'DC'}),
        ('plots-supply-system', {'network_type': 'DC'}),
        ('plots-optimization', {'network_type': 'DC'}),
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
