"""
Natural Gas Imports Script

This script calculates the imports of natural gas for a neighborhood to provide heating/cooling.
It has two loops: one for each of heating network and cooling network
This is then combined to calculate the total natural gas imports and the corresponding file is saved in the
respective folder
"""




import cea.config
import cea.inputlocator
import numpy as np

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def fuel_imports(master_to_slave_vars, heating_dispatch,
                 cooling_dispatch):

    if master_to_slave_vars.DHN_exists:
        NG_used_CHP_W = heating_dispatch["NG_CHP_req_W"]
        NG_used_BaseBoiler_W = heating_dispatch["NG_BaseBoiler_req_W"]
        NG_used_PeakBoiler_W = heating_dispatch["NG_PeakBoiler_req_W"]
        NG_used_BackupBoiler_W = heating_dispatch["NG_BackupBoiler_req_W"]
    else:
        NG_used_CHP_W = np.zeros(8760)
        NG_used_BaseBoiler_W = np.zeros(8760)
        NG_used_PeakBoiler_W = np.zeros(8760)
        NG_used_BackupBoiler_W = np.zeros(8760)


    if master_to_slave_vars.DCN_exists:
        NG_used_CCGT_W = cooling_dispatch["NG_used_CCGT_W"]
    else:
        NG_used_CCGT_W = np.zeros(8760)

    NG_total_heating_W = [a + b + c + d  for a, b, c, d in
                          zip(NG_used_CHP_W, NG_used_BaseBoiler_W, NG_used_PeakBoiler_W, NG_used_BackupBoiler_W)]

    NG_total_cooling_W = NG_used_CCGT_W

    NG_total_W = NG_total_heating_W + NG_total_cooling_W

    naturalgas_dispatch = {
        "NG_GRID_district_scale_W": NG_total_W,
        "NG_GRID_heating_district_scale_W": NG_total_heating_W,
        "NG_GRID_cooling_district_scale_W": NG_total_cooling_W,
        "NG_CHP_req_W": NG_used_CHP_W,
        "NG_BaseBoiler_req_W": NG_used_BaseBoiler_W,
        "NG_PeakBoiler_req_W": NG_used_PeakBoiler_W,
        "NG_BackupBoiler_req_W": NG_used_BackupBoiler_W,
        "NG_used_CCGT_W": NG_used_CCGT_W
    }
    return naturalgas_dispatch


def main(config: cea.config.Configuration):
    locator = cea.inputlocator.InputLocator(config.scenario)
    generation = 2
    individual = 2
    print("Calculating imports of natural gas of individual" + str(individual) + " of generation " + str(generation))

    fuel_imports(generation, individual, locator)


if __name__ == '__main__':
    main(cea.config.Configuration())
