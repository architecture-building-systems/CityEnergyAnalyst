"""
Natural Gas imports script

This file takes in the values of the electricity activation pattern (which is only considering buildings present in
network and corresponding district energy systems) and adds in the electricity requirement of decentralized buildings
and recalculates the imports from grid and exports to the grid
"""
from __future__ import division
from __future__ import print_function

import os
import pandas as pd
import numpy as np
import cea.config
import cea.inputlocator
from cea.optimization.lca_calculations import lca_calculations
from cea.constants import WH_TO_J

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def natural_gas_imports(generation, individual, locator, config):


    if config.optimization.iscooling:
        data_cooling = pd.read_csv(
            os.path.join(locator.get_optimization_slave_cooling_activation_pattern(individual, generation)))

        # Natural Gas supply for the CCGT plant
        lca = lca_calculations(locator, config)
        co2_CCGT = data_cooling['CO2_from_using_CCGT']
        E_gen_CCGT_W = data_cooling['E_gen_CCGT_associated_with_absorption_chillers_W']
        NG_used_CCGT_W = np.zeros(8760)
        for hour in range(8760):
            NG_used_CCGT_W[hour] = (co2_CCGT[hour] + E_gen_CCGT_W[hour] * lca.EL_TO_CO2 * 3600E-6) * 1.0E6 / (lca.NG_CC_TO_CO2_STD * WH_TO_J)

        date = data_cooling.DATE.values

        results = pd.DataFrame({"DATE": date,
                                "NG_used_CCGT_W": NG_used_CCGT_W,
                                "CO2_from_using_CCGT": co2_CCGT,
                                "E_gen_CCGT_associated_with_absorption_chillers_W": E_gen_CCGT_W})

        results.to_csv(locator.get_optimization_slave_natural_gas_imports(individual, generation), index=False)

    return  results

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    generation = 25
    individual = 10
    print("Calculating imports of natural gas of individual" + str(individual) + " of generation " + str(generation))

    natural_gas_imports(generation, individual, locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())