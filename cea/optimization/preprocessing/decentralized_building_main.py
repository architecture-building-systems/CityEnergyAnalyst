"""
Disconnected buildings

This computes the close-to-optimal supply system for single buildings.

"""



import cea.config
import cea.inputlocator
import pandas as pd
from cea.optimization.prices import Prices as Prices
from cea.optimization.preprocessing import decentralized_buildings_heating
from cea.optimization.preprocessing import decentralized_buildings_cooling
from cea.optimization.lca_calculations import LcaCalculations
from cea.optimization.preprocessing.preprocessing_main import get_building_names_with_load
from cea.technologies.supply_systems_database import SupplySystemsDatabase


def disconnected_building_main(locator, total_demand, config, prices, lca):
    """
    This functions optimizes disconnected buildings individually

    :param locator: locator class
    :type locator: class
    :return: elecCosts, elecCO2, elecPrim
    :rtype: tuple
    """

    # local variables
    buildings_name_with_heating = get_building_names_with_load(total_demand, load_name='QH_sys_MWhyr')
    buildings_name_with_space_heating = get_building_names_with_load(total_demand, load_name='Qhs_sys_MWhyr')
    buildings_name_with_cooling = get_building_names_with_load(total_demand, load_name='QC_sys_MWhyr')

    if buildings_name_with_heating and buildings_name_with_space_heating:
        decentralized_buildings_heating.disconnected_buildings_heating_main(locator, total_demand,
                                                                            buildings_name_with_heating,
                                                                            config, prices, lca)

    if buildings_name_with_cooling:
        decentralized_buildings_cooling.disconnected_buildings_cooling_main(locator,
                                                                            buildings_name_with_cooling,
                                                                            total_demand,
                                                                            config, prices, lca)
    print("done.")


def main(config: cea.config.Configuration):
    print('Running decentralized model for buildings with scenario = %s' % config.scenario)
    locator = cea.inputlocator.InputLocator(config.scenario)
    supply_systems = SupplySystemsDatabase(locator)
    total_demand = pd.read_csv(locator.get_total_demand())
    prices = Prices(supply_systems)
    lca = LcaCalculations(supply_systems)
    disconnected_building_main(locator=locator,  total_demand=total_demand,
                               config=config, prices=prices, lca=lca)


if __name__ == '__main__':
    main(cea.config.Configuration())
