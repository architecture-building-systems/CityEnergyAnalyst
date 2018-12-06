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
from cea.optimization.preprocessing import decentralized_buildings_heating
from cea.optimization.preprocessing import decentralized_buildings_cooling
from cea.optimization.lca_calculations import lca_calculations



def disconnected_building_main(locator, building_names, config, prices, lca):
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
    controls = pd.read_excel(locator.get_archetypes_system_controls(config.region))
    if controls['has-cooling-season'].item() or controls['has-heating-season'].item():
        if controls['has-cooling-season'].item():
            decentralized_buildings_cooling.disconnected_buildings_cooling_main(locator, building_names, config, prices, lca)
        if controls['has-heating-season'].item():
            decentralized_buildings_heating.disconnected_buildings_heating_main(locator, building_names, config, prices, lca)
    else:
        raise ValueError("The case study has neither a heating nor a cooling season, please specify in system_controls.xlsx")

    print "Run decentralized model for buildings"

def main(config):
    print('Running decentralized model for buildings with scenario = %s' % config.scenario)
    locator = cea.inputlocator.InputLocator(config.scenario)
    total_demand = pd.read_csv(locator.get_total_demand())
    building_names = total_demand.Name.values
    prices = Prices(locator, config)
    lca = lca_calculations(locator, config)

    disconnected_building_main(locator=locator, building_names=building_names, config=config, prices=prices, lca=lca)

if __name__ == '__main__':
    main(cea.config.Configuration())