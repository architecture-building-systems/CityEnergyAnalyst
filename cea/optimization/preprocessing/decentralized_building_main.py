"""
Disconnected buildings

This computes the close-to-optimal supply system for single buildings.

"""
import cea.config
import cea.globalvar
import cea.inputlocator
import pandas as pd
from cea.optimization.prices import Prices as Prices
from cea.optimization.preprocessing import decentralized_buildings_heating
from cea.optimization.preprocessing import decentralized_buildings_cooling
from cea.optimization.lca_calculations import LcaCalculations
from cea.optimization.preprocessing.preprocessing_main import get_building_names_connected_according_to_load
import cea.technologies.substation as substation


def disconnected_building_main(locator, building_names, total_demand, config, prices, lca):
    """
    This functions optimizes disconnected buildings individually

    :param locator: locator class
    :param gv: global variables class
    :type locator: class
    :type gv: class
    :return: elecCosts, elecCO2, elecPrim
    :rtype: tuple
    """

    # local variables
    buildings_name_with_heating = get_building_names_connected_according_to_load(total_demand, load_name='QH_sys_MWhyr')
    buildings_name_with_cooling = get_building_names_connected_according_to_load(total_demand, load_name='QC_sys_MWhyr')

    # calculate substations

    if buildings_name_with_heating != []:
        substation.substation_main_heating(locator,
                                           total_demand,
                                           buildings_name_with_heating,
                                           heating_configuration=7,
                                           Flag=False)
        decentralized_buildings_heating.disconnected_buildings_heating_main(locator, building_names,
                                                                            config, prices, lca)

    if buildings_name_with_cooling != []:
        substation.substation_main_cooling(locator, total_demand,
                                           buildings_name_with_heating,
                                           cooling_configuration=1,
                                           Flag=False)
        decentralized_buildings_cooling.disconnected_buildings_cooling_main(locator, building_names,
                                                                            config, prices, lca)
    print "Run decentralized model for buildings"


def main(config):
    print('Running decentralized model for buildings with scenario = %s' % config.scenario)
    locator = cea.inputlocator.InputLocator(config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    prices = Prices(locator, config)
    detailed_electricity_pricing = config.decentralized.detailed_electricity_pricing
    lca = LcaCalculations(locator, detailed_electricity_pricing)

    disconnected_building_main(locator=locator, building_names=building_names, total_demand=total_demand,
                               config=config, prices=prices, lca=lca)


if __name__ == '__main__':
    main(cea.config.Configuration())
