"""
Energy Mix (yearly total) based on technologies used

This file generates the file with the yearly total of the energy supplied by each system.
This is further used to generate Pie Chart
"""
from __future__ import division
from __future__ import print_function

import os
import pandas as pd
import numpy as np
import cea.config
import cea.inputlocator
from cea.plots.supply_system.optimization_post_processing.electricity_imports_exports_script import electricity_import_and_exports
from cea.plots.supply_system.optimization_post_processing.natural_gas_imports_script import natural_gas_imports

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def energy_mix_based_on_technologies_script(generation, individual, locator, config):
    category = "optimization-detailed"

    if config.multi_criteria.network_type == 'DH':
        print ('Need to do this in future')

    elif config.multi_criteria.network_type == 'DC':
        data_cooling = pd.read_csv(
            os.path.join(locator.get_optimization_slave_cooling_activation_pattern(individual, generation)))

        Q_VCC_total_W = data_cooling['Q_from_VCC_W'].sum()
        Q_Lake_total_W = data_cooling['Q_from_Lake_W'].sum()
        Q_ACH_total_W = data_cooling['Q_from_ACH_W'].sum()
        Q_VCC_backup_total_W = data_cooling['Q_from_VCC_backup_W'].sum()
        Q_thermal_storage_total_W = data_cooling['Q_from_storage_tank_W'].sum()
        Q_cooling_total_W = data_cooling['Q_total_cooling_W'].sum()

        if not os.path.exists(locator.get_optimization_slave_electricity_activation_pattern_processed(individual, generation, category)):
            data_electricity = electricity_import_and_exports(generation, individual, locator, config)
        else:
            data_electricity = pd.read_csv(
                locator.get_optimization_slave_electricity_activation_pattern_processed(individual, generation,
                                                                                        category))

        E_ACH_total_W = data_electricity['E_ACH_W'].sum()
        E_CHP_to_directload_total_W = data_electricity['E_CHP_to_directload_W'].sum()
        E_CHP_to_grid_total_W =  data_electricity['E_CHP_to_grid_W'].sum()
        E_CT_total_W = data_electricity['E_CT_W'].sum()
        E_PV_to_directload_total_W = data_electricity['E_PV_to_directload_W'].sum()
        E_PV_to_grid_total_W = data_electricity['E_PV_to_grid_W'].sum()
        E_VCC_total_W = data_electricity['E_VCC_W'].sum()
        E_VCC_backup_total_W = data_electricity['E_VCC_backup_W'].sum()
        E_hotwater_total_W = data_electricity['E_for_hot_water_demand_W'].sum()
        E_from_grid_total_W = data_electricity['E_from_grid_W'].sum()
        E_required_district_total_W = data_electricity['E_total_req_W'].sum()
        E_building_appliances_total_W = E_required_district_total_W - E_hotwater_total_W - E_VCC_backup_total_W - E_VCC_total_W - \
                                        E_CT_total_W - E_ACH_total_W

        if not os.path.exists(locator.get_optimization_slave_natural_gas_imports(individual, generation, category)):
            data_natural_gas = natural_gas_imports(generation, individual, locator, config)
        else:
            data_natural_gas = pd.read_csv(
                locator.get_optimization_slave_natural_gas_imports(individual, generation, category))

        NG_used_total_W = data_natural_gas['NG_used_CCGT_W'].sum()


        results = pd.DataFrame({"Q_VCC_total_W": [Q_VCC_total_W],
                                "Q_Lake_total_W": [Q_Lake_total_W],
                                "Q_ACH_total_W": [Q_ACH_total_W],
                                "Q_VCC_backup_total_W": [Q_VCC_backup_total_W],
                                "Q_thermal_storage_total_W": [Q_thermal_storage_total_W],
                                "Q_cooling_total_W": [Q_cooling_total_W],
                                "E_ACH_total_W": [E_ACH_total_W],
                                "E_CHP_to_directload_total_W": [E_CHP_to_directload_total_W],
                                "E_CHP_to_grid_total_W": [E_CHP_to_grid_total_W],
                                "E_PV_to_directload_total_W": [E_PV_to_directload_total_W],
                                "E_PV_to_grid_total_W": [E_PV_to_grid_total_W],
                                "E_VCC_total_W": [E_VCC_total_W],
                                "E_VCC_backup_total_W": [E_VCC_backup_total_W],
                                "E_hotwater_total_W": [E_hotwater_total_W],
                                "E_from_grid_total_W": [E_from_grid_total_W],
                                "E_required_district_total_W": [E_required_district_total_W],
                                "E_building_appliances_total_W": [E_building_appliances_total_W],
                                "NG_used_total_W": [NG_used_total_W]})

    results.to_csv(
        locator.get_optimization_slave_energy_mix_based_on_technologies(individual, generation, category), index=False)

    return results

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    generation = 25
    individual = 10
    print("Calculating energy mix based on technologies of individual " + str(individual) + " of generation " + str(generation))

    energy_mix_based_on_technologies_script(generation, individual, locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())