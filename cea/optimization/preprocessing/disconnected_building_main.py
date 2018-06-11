"""
=====================
Electricity Operation
=====================

All buildings are connected to the grid which completely cover their needs
(as the buying / selling electricity prices are the same and are independent 
from the hour in the day / the day in the year)

"""
import cea.config
import cea.globalvar
import cea.inputlocator
import pandas as pd
from cea.optimization.prices import Prices as Prices
from cea.optimization.preprocessing import disconnected_buildings_heating
from cea.optimization.preprocessing import disconnected_buildings_cooling
from cea.optimization.lca_calculations import lca_calculations



def disconnected_building_main(locator, building_names, config, prices):
    """
    This function computes the parameters for the electrical demand contributing to the pareto optimal alternatives.
    in the future, this aspect should be included in the optimization itself.

    :param locator: locator class
    :param gv: global variables class
    :type locator: class
    :type gv: class
    :return: elecCosts, elecCO2, elecPrim
    :rtype: tuple
    """
    if config.region == 'SIN':
        disconnected_buildings_cooling.disconnected_buildings_cooling_main(locator, building_names, config, prices, lca)
    elif config.region == 'CH':
        disconnected_buildings_heating.disconnected_buildings_heating_main(locator, building_names, config, prices, lca)
    else:
        raise ValueError("the region is not specified correctly")

    print "Run decentralized model for buildings"

def main(config):

    locator = cea.inputlocator.InputLocator(config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    prices = Prices(locator, config)
    lca = lca_calculations(locator, config)


    disconnected_building_main(locator=locator, building_names=building_names, config=config, prices=prices, lca=lca)

if __name__ == '__main__':
    main(cea.config.Configuration())