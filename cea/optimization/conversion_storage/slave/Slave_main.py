"""
===========================
Mixed-integer algorithm main
===========================

"""

import time
import cea.optimization.conversion_storage.slave.least_cost as Least_Cost
import cea.optimization.conversion_storage.slave.seasonal_storage.storage_main as Storage_Opt

def slave_main(pathX, fName_NetworkData, context, solarFeat, gV):
    """
    This function calls the optimization storage and a least cost optimization fucntion.
    Both functions aim at selecting the dispatch pattern of the technologies selected by the evolutionary algorithm.

    :param pathX:
    :param fName_NetworkData:
    :param context:
    :param solarFeat:
    :param gV:
    :return:
    """
    t0 = time.time()
    
    # run storage optimization
    Storage_Opt.Storage_Optimization(pathX, fName_NetworkData, context, gV)
    
    # run activation pattern
    E_oil_eq_MJ, CO2_kg_eq, cost_sum, QUncoveredDesign, QUncoveredAnnual = Least_Cost.Least_Cost_Optimization(pathX, context, solarFeat, gV)

    print " Slave Optimization done (", round(time.time()-t0,1)," seconds used for this task)"

    return E_oil_eq_MJ, CO2_kg_eq, cost_sum, QUncoveredDesign, QUncoveredAnnual
    
    