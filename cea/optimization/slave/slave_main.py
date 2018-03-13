"""
===========================
Mixed-integer algorithm main
===========================

"""

import time

import cea.optimization.slave.seasonal_storage.storage_main as storage_main

import cea.optimization.slave.least_cost as least_cost

__author__ = "Tim Vollrath"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Tim Vollrath", "Thuy-An Nguyen", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def slave_main(locator, master_to_slave_vars, solar_features, gv, config, prices):
    """
    This function calls the storage optimization and a least cost optimization function.
    Both functions aim at selecting the dispatch pattern of the technologies selected by the evolutionary algorithm.

    :param locator: locator class
    :param network_file_name: name of the network file
    :param master_to_slave_vars: class MastertoSlaveVars containing the value of variables to be passed to the slave
                                 optimization for each individual
    :param solar_features: class solar_features
    :param gv: global variables class
    :type locator: class
    :type network_file_name: string
    :type master_to_slave_vars: class
    :type solar_features: class
    :type gv: class
    :return: E_oil_eq_MJ: primary energy
             CO2_kg_eq: co2 emissions
             cost_sum: accumualted costs during operation
             QUncoveredDesign: part of the design load not covered
             QUncoveredAnnual: part of the total load not covered
    :rtype: float, float, float, float, float

    """
    t0 = time.time()
    
    # run storage optimization
    storage_main.storage_optimization(locator, master_to_slave_vars, gv)
    
    # run activation pattern
    E_oil_eq_MJ, CO2_kg_eq, cost_sum,\
    Q_uncovered_design_W, Q_uncovered_annual_W = least_cost.least_cost_main(locator, master_to_slave_vars,
                                                                    solar_features, gv, prices)

    print " Slave Optimization done (", round(time.time()-t0, 1), " seconds used for this task)"

    return E_oil_eq_MJ, CO2_kg_eq, cost_sum, Q_uncovered_design_W, Q_uncovered_annual_W
    
    