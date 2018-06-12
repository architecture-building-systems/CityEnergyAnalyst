"""
Make sure that all the databases for the selected region are copied to the scenario.

The InputLocator does this automatically when a database path is requested, but this script allows to request them
all in one go - as a start to editing the scenario.

.. NOTE: Only databases that aren't present in the scenario yet are copied - delete any you want replaced and re-run the
         tool.
"""
from __future__ import division
from __future__ import print_function

import os
import time
import cea.config
import cea.inputlocator

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def copy_default_databases(locator, region):
    """For each database, "touch" it, by getting the path from the InputLocator.

    The list of databases was found by (manually) checking the :py:class:`cea.inputlocator.InputLocator` for any
    methods that calls the :py:meth:`cea.inputlocator.InputLocator._get_region_specific_db_file` method.

    :param cea.inputlocator.InputLocator locator: The locator to use
    :param str region: The region to use for copying these databases
    """
    locator_methods = [
        locator.get_archetypes_properties,
        locator.get_archetypes_schedules,
        locator.get_archetypes_system_controls,
        locator.get_supply_systems,
        locator.get_life_cycle_inventory_supply_systems,
        locator.get_life_cycle_inventory_building_systems,
        locator.get_technical_emission_systems,
        locator.get_envelope_systems,
        locator.get_thermal_networks,
        locator.get_data_benchmark,
        locator.get_uncertainty_db,
    ]
    before_copy = time.time()
    for method in locator_methods:
        # call the method and discard the results...
        file_path = method(region)
        file_modification_date = os.path.getmtime(file_path)
        if before_copy < file_modification_date:
            print("Copied file: %s" % file_path)


def main(config):
    """
    This is the main entry point to the script.

    :param config:
    :type config: cea.config.Configuration

    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running template with scenario = %s" % config.scenario)
    print("Running template with reagion = %s" % config.region)

    if config.region == 'custom':
        print("WARNING: Custom region specified - no databases copied.")
    else:
        copy_default_databases(locator, config.region)


if __name__ == '__main__':
    main(cea.config.Configuration())
