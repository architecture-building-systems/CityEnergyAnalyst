"""
The capacities of the individual are saved in this file
"""
from __future__ import division

import time
import json
from cea.optimization.constants import PROBA, SIGMAP, GHP_HMAX_SIZE, N_HR, N_HEAT, N_PV, N_PVT
import cea.optimization.master.crossover as cx
import cea.optimization.master.evaluation as evaluation
import random
from deap import base
from deap import creator
from deap import tools
import cea.optimization.master.generation as generation
import cea.optimization.master.mutations as mut
import cea.optimization.master.selection as sel
import numpy as np
import pandas as pd
import cea.optimization.supportFn as sFn
import itertools
import multiprocessing


__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna", "Thuy-An Nguyen", "Tim Vollrath", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

for (index, network) in enumerate(network_list):
    intermediate_capacities = []
    for i in range(len(network)):
        # if a building is connected, which corresponds to '1' then the disconnected shares are linked to the
        # number of units the DHN/DCN is supplying. A building can be supplied AHU demand from the centralized
        # plant whereas the remaining load corresponding to ARU and SHU/SCU be supplied by the decentralized option
        # if a building is disconnected, which corresponds to '0' then disconnected shares are imported from csv files
        Disconnected_Boiler_BG_share_heating = 0
        Disconnected_Boiler_BG_capacity_heating_W = 0
        Disconnected_Boiler_NG_share_heating = 0
        Disconnected_Boiler_NG_capacity_heating_W = 0
        Disconnected_FC_share_heating = 0
        Disconnected_FC_capacity_heating_W = 0
        Disconnected_GHP_share_heating = 0
        Disconnected_GHP_capacity_heating_W = 0

        Disconnected_VCC_to_AHU_share_cooling = 0
        Disconnected_VCC_to_AHU_capacity_cooling_W = 0
        Disconnected_VCC_to_ARU_share_cooling = 0
        Disconnected_VCC_to_ARU_capacity_cooling_W = 0
        Disconnected_VCC_to_SCU_share_cooling = 0
        Disconnected_VCC_to_SCU_capacity_cooling_W = 0
        Disconnected_VCC_to_AHU_ARU_share_cooling = 0
        Disconnected_VCC_to_AHU_ARU_capacity_cooling_W = 0
        Disconnected_VCC_to_AHU_SCU_share_cooling = 0
        Disconnected_VCC_to_AHU_SCU_capacity_cooling_W = 0
        Disconnected_VCC_to_ARU_SCU_share_cooling = 0
        Disconnected_VCC_to_ARU_SCU_capacity_cooling_W = 0
        Disconnected_VCC_to_AHU_ARU_SCU_share_cooling = 0
        Disconnected_VCC_to_AHU_ARU_SCU_capacity_cooling_W = 0

        Disconnected_single_effect_ACH_to_AHU_share_FP_cooling = 0
        Disconnected_single_effect_ACH_to_AHU_capacity_FP_cooling_W = 0
        Disconnected_single_effect_ACH_to_AHU_share_ET_cooling = 0
        Disconnected_single_effect_ACH_to_AHU_capacity_ET_cooling_W = 0
        Disconnected_single_effect_ACH_to_ARU_share_FP_cooling = 0
        Disconnected_single_effect_ACH_to_ARU_capacity_FP_cooling_W = 0
        Disconnected_single_effect_ACH_to_ARU_share_ET_cooling = 0
        Disconnected_single_effect_ACH_to_ARU_capacity_ET_cooling_W = 0
        Disconnected_single_effect_ACH_to_SCU_share_FP_cooling = 0
        Disconnected_single_effect_ACH_to_SCU_capacity_FP_cooling_W = 0
        Disconnected_single_effect_ACH_to_SCU_share_ET_cooling = 0
        Disconnected_single_effect_ACH_to_SCU_capacity_ET_cooling_W = 0
        Disconnected_single_effect_ACH_to_AHU_ARU_share_FP_cooling = 0
        Disconnected_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W = 0
        Disconnected_single_effect_ACH_to_AHU_ARU_share_ET_cooling = 0
        Disconnected_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W = 0
        Disconnected_single_effect_ACH_to_AHU_SCU_share_FP_cooling = 0
        Disconnected_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W = 0
        Disconnected_single_effect_ACH_to_AHU_SCU_share_ET_cooling = 0
        Disconnected_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W = 0
        Disconnected_single_effect_ACH_to_ARU_SCU_share_FP_cooling = 0
        Disconnected_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W = 0
        Disconnected_single_effect_ACH_to_ARU_SCU_share_ET_cooling = 0
        Disconnected_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W = 0
        Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling = 0
        Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W = 0
        Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling = 0
        Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W = 0

        Disconnected_direct_expansion_to_AHU_share_cooling = 0
        Disconnected_direct_expansion_to_AHU_capacity_cooling_W = 0
        Disconnected_direct_expansion_to_ARU_share_cooling = 0
        Disconnected_direct_expansion_to_ARU_capacity_cooling_W = 0
        Disconnected_direct_expansion_to_SCU_share_cooling = 0
        Disconnected_direct_expansion_to_SCU_capacity_cooling_W = 0
        Disconnected_direct_expansion_to_AHU_SCU_share_cooling = 0
        Disconnected_direct_expansion_to_AHU_SCU_capacity_cooling_W = 0
        Disconnected_direct_expansion_to_AHU_ARU_share_cooling = 0
        Disconnected_direct_expansion_to_AHU_ARU_capacity_cooling_W = 0
        Disconnected_direct_expansion_to_ARU_SCU_share_cooling = 0
        Disconnected_direct_expansion_to_ARU_SCU_capacity_cooling_W = 0
        Disconnected_direct_expansion_to_AHU_ARU_SCU_share_cooling = 0
        Disconnected_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W = 0

        if network[i] == "0":
            if config.district_heating_network:
                df = pd.read_csv(
                    locator.get_optimization_disconnected_folder_building_result_heating(building_names[i]))
                dfBest = df[df["Best configuration"] == 1]
                Disconnected_Boiler_BG_share_heating = dfBest["BoilerBG Share"].iloc[0]
                Disconnected_Boiler_NG_share_heating = dfBest["BoilerNG Share"].iloc[0]
                Disconnected_FC_share_heating = dfBest["FC Share"].iloc[0]
                Disconnected_GHP_share_heating = dfBest["GHP Share"].iloc[0]

                if Disconnected_Boiler_BG_share_heating == 1:
                    Disconnected_Boiler_BG_capacity_heating_W = dfBest["Nominal Power"].iloc[0]

                if Disconnected_Boiler_NG_share_heating == 1:
                    Disconnected_Boiler_NG_capacity_heating_W = dfBest["Nominal Power"].iloc[0]

                if Disconnected_FC_share_heating == 1:
                    Disconnected_FC_capacity_heating_W = dfBest["Nominal Power"].iloc[0]

                if Disconnected_GHP_share_heating == 1:
                    Disconnected_GHP_capacity_heating_W = dfBest["Nominal Power"].iloc[0]

                if (
                                Disconnected_FC_share_heating == 0 and Disconnected_Boiler_BG_share_heating == 0 and Disconnected_GHP_share_heating != 0 and Disconnected_Boiler_NG_share_heating != 0):
                    Disconnected_Boiler_NG_capacity_heating_W = dfBest["Nominal Power"].iloc[
                                                                    0] / Disconnected_Boiler_NG_share_heating
                    Disconnected_GHP_capacity_heating_W = dfBest["Nominal Power"].iloc[
                                                              0] / Disconnected_GHP_share_heating

                disconnected_capacity = dict(building_name=building_names[i],
                                             Disconnected_Boiler_BG_share=Disconnected_Boiler_BG_share_heating,
                                             Disconnected_Boiler_BG_capacity_W=Disconnected_Boiler_BG_capacity_heating_W,
                                             Disconnected_Boiler_NG_share=Disconnected_Boiler_NG_share_heating,
                                             Disconnected_Boiler_NG_capacity_W=Disconnected_Boiler_NG_capacity_heating_W,
                                             Disconnected_FC_share=Disconnected_FC_share_heating,
                                             Disconnected_FC_capacity_W=Disconnected_FC_capacity_heating_W,
                                             Disconnected_GHP_share=Disconnected_GHP_share_heating,
                                             Disconnected_GHP_capacity_W=Disconnected_GHP_capacity_heating_W,
                                             Disconnected_VCC_to_AHU_share_cooling=Disconnected_VCC_to_AHU_share_cooling,
                                             Disconnected_VCC_to_AHU_capacity_cooling_W=Disconnected_VCC_to_AHU_capacity_cooling_W,
                                             Disconnected_VCC_to_ARU_share_cooling=Disconnected_VCC_to_ARU_share_cooling,
                                             Disconnected_VCC_to_ARU_capacity_cooling_W=Disconnected_VCC_to_ARU_capacity_cooling_W,
                                             Disconnected_VCC_to_SCU_share_cooling=Disconnected_VCC_to_SCU_share_cooling,
                                             Disconnected_VCC_to_SCU_capacity_cooling_W=Disconnected_VCC_to_SCU_capacity_cooling_W,
                                             Disconnected_VCC_to_AHU_ARU_share_cooling=Disconnected_VCC_to_AHU_ARU_share_cooling,
                                             Disconnected_VCC_to_AHU_ARU_capacity_cooling_W=Disconnected_VCC_to_AHU_ARU_capacity_cooling_W,
                                             Disconnected_VCC_to_AHU_SCU_share_cooling=Disconnected_VCC_to_AHU_SCU_share_cooling,
                                             Disconnected_VCC_to_AHU_SCU_capacity_cooling_W=Disconnected_VCC_to_AHU_SCU_capacity_cooling_W,
                                             Disconnected_VCC_to_ARU_SCU_share_cooling=Disconnected_VCC_to_ARU_SCU_share_cooling,
                                             Disconnected_VCC_to_ARU_SCU_capacity_cooling_W=Disconnected_VCC_to_ARU_SCU_capacity_cooling_W,
                                             Disconnected_VCC_to_AHU_ARU_SCU_share_cooling=Disconnected_VCC_to_AHU_ARU_SCU_share_cooling,
                                             Disconnected_VCC_to_AHU_ARU_SCU_capacity_cooling_W=Disconnected_VCC_to_AHU_ARU_SCU_capacity_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_ARU_share_FP_cooling=Disconnected_single_effect_ACH_to_ARU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_ARU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_ARU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_ARU_share_ET_cooling=Disconnected_single_effect_ACH_to_ARU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_ARU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_ARU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_SCU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_SCU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_SCU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_SCU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_SCU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_SCU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_ARU_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_ARU_SCU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_ARU_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_ARU_SCU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W,
                                             Disconnected_direct_expansion_to_AHU_share_cooling=Disconnected_direct_expansion_to_AHU_share_cooling,
                                             Disconnected_direct_expansion_to_AHU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_ARU_share_cooling=Disconnected_direct_expansion_to_ARU_share_cooling,
                                             Disconnected_direct_expansion_to_ARU_capacity_cooling_W=Disconnected_direct_expansion_to_ARU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_SCU_share_cooling=Disconnected_direct_expansion_to_SCU_share_cooling,
                                             Disconnected_direct_expansion_to_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_SCU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_AHU_SCU_share_cooling=Disconnected_direct_expansion_to_AHU_SCU_share_cooling,
                                             Disconnected_direct_expansion_to_AHU_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_SCU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_AHU_ARU_share_cooling=Disconnected_direct_expansion_to_AHU_ARU_share_cooling,
                                             Disconnected_direct_expansion_to_AHU_ARU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_ARU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_ARU_SCU_share_cooling=Disconnected_direct_expansion_to_ARU_SCU_share_cooling,
                                             Disconnected_direct_expansion_to_ARU_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_ARU_SCU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_AHU_ARU_SCU_share_cooling=Disconnected_direct_expansion_to_AHU_ARU_SCU_share_cooling,
                                             Disconnected_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W)

            elif config.district_cooling_network:

                df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result_cooling(building_names[i],
                                                                                                      cooling_all_units))
                dfBest = df[df["Best configuration"] == 1]
                Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling = \
                dfBest["single effect ACH to AHU_ARU_SCU Share (FP)"].iloc[0]
                Disconnected_single_effect_ACH_to_SCU_share_FP_cooling = \
                dfBest["single effect ACH to SCU Share (FP)"].iloc[0]
                Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling = \
                dfBest["single effect ACH to AHU_ARU_SCU Share (ET)"].iloc[0]
                Disconnected_direct_expansion_to_AHU_ARU_SCU_share_cooling = dfBest["DX to AHU_ARU_SCU Share"].iloc[0]
                Disconnected_VCC_to_AHU_ARU_share_cooling = dfBest["VCC to AHU_ARU Share"].iloc[0]
                Disconnected_VCC_to_AHU_ARU_SCU_share_cooling = dfBest["VCC to AHU_ARU_SCU Share"].iloc[0]
                Disconnected_VCC_to_SCU_share_cooling = dfBest["VCC to SCU Share"].iloc[0]

                if Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling == 1:
                    Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W = \
                    dfBest["Nominal Power single effect ACH to AHU_ARU_SCU (FP) [W]"].iloc[0]

                if Disconnected_single_effect_ACH_to_SCU_share_FP_cooling == 1:
                    Disconnected_single_effect_ACH_to_SCU_capacity_FP_cooling_W = \
                    dfBest["Nominal Power single effect ACH to SCU (FP) [W]"].iloc[0]

                if Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling == 1:
                    Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W = \
                    dfBest["Nominal Power single effect ACH to AHU_ARU_SCU (ET) [W]"].iloc[0]

                if Disconnected_direct_expansion_to_AHU_ARU_SCU_share_cooling == 1:
                    Disconnected_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W = \
                    dfBest["Nominal Power DX to AHU_ARU_SCU [W]"].iloc[0]

                if Disconnected_VCC_to_AHU_ARU_share_cooling == 1:
                    Disconnected_VCC_to_AHU_ARU_capacity_cooling_W = dfBest["Nominal Power VCC to AHU_ARU [W]"].iloc[0]

                if Disconnected_VCC_to_AHU_ARU_SCU_share_cooling == 1:
                    Disconnected_VCC_to_AHU_ARU_SCU_capacity_cooling_W = \
                    dfBest["Nominal Power VCC to AHU_ARU_SCU [W]"].iloc[0]

                if Disconnected_VCC_to_SCU_share_cooling == 1:
                    Disconnected_VCC_to_SCU_capacity_cooling_W = dfBest["Nominal Power VCC to SCU [W]"].iloc[0]

                disconnected_capacity = dict(building_name=building_names[i],
                                             Disconnected_Boiler_BG_share=Disconnected_Boiler_BG_share_heating,
                                             Disconnected_Boiler_BG_capacity_W=Disconnected_Boiler_BG_capacity_heating_W,
                                             Disconnected_Boiler_NG_share=Disconnected_Boiler_NG_share_heating,
                                             Disconnected_Boiler_NG_capacity_W=Disconnected_Boiler_NG_capacity_heating_W,
                                             Disconnected_FC_share=Disconnected_FC_share_heating,
                                             Disconnected_FC_capacity_W=Disconnected_FC_capacity_heating_W,
                                             Disconnected_GHP_share=Disconnected_GHP_share_heating,
                                             Disconnected_GHP_capacity_W=Disconnected_GHP_capacity_heating_W,
                                             Disconnected_VCC_to_AHU_share_cooling=Disconnected_VCC_to_AHU_share_cooling,
                                             Disconnected_VCC_to_AHU_capacity_cooling_W=Disconnected_VCC_to_AHU_capacity_cooling_W,
                                             Disconnected_VCC_to_ARU_share_cooling=Disconnected_VCC_to_ARU_share_cooling,
                                             Disconnected_VCC_to_ARU_capacity_cooling_W=Disconnected_VCC_to_ARU_capacity_cooling_W,
                                             Disconnected_VCC_to_SCU_share_cooling=Disconnected_VCC_to_SCU_share_cooling,
                                             Disconnected_VCC_to_SCU_capacity_cooling_W=Disconnected_VCC_to_SCU_capacity_cooling_W,
                                             Disconnected_VCC_to_AHU_ARU_share_cooling=Disconnected_VCC_to_AHU_ARU_share_cooling,
                                             Disconnected_VCC_to_AHU_ARU_capacity_cooling_W=Disconnected_VCC_to_AHU_ARU_capacity_cooling_W,
                                             Disconnected_VCC_to_AHU_SCU_share_cooling=Disconnected_VCC_to_AHU_SCU_share_cooling,
                                             Disconnected_VCC_to_AHU_SCU_capacity_cooling_W=Disconnected_VCC_to_AHU_SCU_capacity_cooling_W,
                                             Disconnected_VCC_to_ARU_SCU_share_cooling=Disconnected_VCC_to_ARU_SCU_share_cooling,
                                             Disconnected_VCC_to_ARU_SCU_capacity_cooling_W=Disconnected_VCC_to_ARU_SCU_capacity_cooling_W,
                                             Disconnected_VCC_to_AHU_ARU_SCU_share_cooling=Disconnected_VCC_to_AHU_ARU_SCU_share_cooling,
                                             Disconnected_VCC_to_AHU_ARU_SCU_capacity_cooling_W=Disconnected_VCC_to_AHU_ARU_SCU_capacity_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_ARU_share_FP_cooling=Disconnected_single_effect_ACH_to_ARU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_ARU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_ARU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_ARU_share_ET_cooling=Disconnected_single_effect_ACH_to_ARU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_ARU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_ARU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_SCU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_SCU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_SCU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_SCU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_SCU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_SCU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_ARU_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_ARU_SCU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_ARU_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_ARU_SCU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling,
                                             Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W,
                                             Disconnected_direct_expansion_to_AHU_share_cooling=Disconnected_direct_expansion_to_AHU_share_cooling,
                                             Disconnected_direct_expansion_to_AHU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_ARU_share_cooling=Disconnected_direct_expansion_to_ARU_share_cooling,
                                             Disconnected_direct_expansion_to_ARU_capacity_cooling_W=Disconnected_direct_expansion_to_ARU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_SCU_share_cooling=Disconnected_direct_expansion_to_SCU_share_cooling,
                                             Disconnected_direct_expansion_to_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_SCU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_AHU_SCU_share_cooling=Disconnected_direct_expansion_to_AHU_SCU_share_cooling,
                                             Disconnected_direct_expansion_to_AHU_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_SCU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_AHU_ARU_share_cooling=Disconnected_direct_expansion_to_AHU_ARU_share_cooling,
                                             Disconnected_direct_expansion_to_AHU_ARU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_ARU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_ARU_SCU_share_cooling=Disconnected_direct_expansion_to_ARU_SCU_share_cooling,
                                             Disconnected_direct_expansion_to_ARU_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_ARU_SCU_capacity_cooling_W,
                                             Disconnected_direct_expansion_to_AHU_ARU_SCU_share_cooling=Disconnected_direct_expansion_to_AHU_ARU_SCU_share_cooling,
                                             Disconnected_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W)

            else:
                raise ValueError("the region is not specified correctly")
        else:
            DCN_unit_configuration = saved_dataframe_for_each_generation['DCN unit configuration'][index]

            if DCN_unit_configuration == 1:  # corresponds to AHU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'ARU_SCU'
                df = pd.read_csv(
                    locator.get_optimization_disconnected_folder_building_result_cooling(building_names[i],
                                                                                         decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Disconnected_direct_expansion_to_ARU_SCU_share_cooling = dfBest["DX to ARU_SCU Share"].iloc[0]
                Disconnected_single_effect_ACH_to_ARU_SCU_share_FP_cooling = \
                dfBest["single effect ACH to ARU_SCU Share (FP)"].iloc[0]
                Disconnected_single_effect_ACH_to_ARU_SCU_share_ET_cooling = \
                dfBest["single effect ACH to ARU_SCU Share (ET)"].iloc[0]
                Disconnected_VCC_to_ARU_SCU_share_cooling = dfBest["VCC to ARU_SCU Share"].iloc[0]

                if Disconnected_single_effect_ACH_to_ARU_SCU_share_FP_cooling == 1:
                    Disconnected_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W = \
                    dfBest["Nominal Power single effect ACH to ARU_SCU (FP) [W]"].iloc[0]

                if Disconnected_single_effect_ACH_to_ARU_SCU_share_ET_cooling == 1:
                    Disconnected_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W = \
                    dfBest["Nominal Power single effect ACH to ARU_SCU (ET) [W]"].iloc[0]

                if Disconnected_direct_expansion_to_ARU_SCU_share_cooling == 1:
                    Disconnected_direct_expansion_to_ARU_SCU_capacity_cooling_W = \
                    dfBest["Nominal Power DX to ARU_SCU [W]"].iloc[0]

                if Disconnected_VCC_to_ARU_SCU_share_cooling == 1:
                    Disconnected_VCC_to_ARU_SCU_capacity_cooling_W = dfBest["Nominal Power VCC to ARU_SCU [W]"].iloc[0]

            if DCN_unit_configuration == 2:  # corresponds to ARU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'AHU_SCU'
                df = pd.read_csv(
                    locator.get_optimization_disconnected_folder_building_result_cooling(building_names[i],
                                                                                         decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Disconnected_direct_expansion_to_AHU_SCU_share_cooling = dfBest["DX to AHU_SCU Share"].iloc[0]
                Disconnected_single_effect_ACH_to_AHU_SCU_share_FP_cooling = \
                dfBest["single effect ACH to AHU_SCU Share (FP)"].iloc[0]
                Disconnected_single_effect_ACH_to_AHU_SCU_share_ET_cooling = \
                dfBest["single effect ACH to AHU_SCU Share (ET)"].iloc[0]
                Disconnected_VCC_to_ARU_SCU_share_cooling = dfBest["VCC to AHU_SCU Share"].iloc[0]

                if Disconnected_single_effect_ACH_to_AHU_SCU_share_FP_cooling == 1:
                    Disconnected_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W = \
                    dfBest["Nominal Power single effect ACH to AHU_SCU (FP) [W]"].iloc[0]

                if Disconnected_single_effect_ACH_to_AHU_SCU_share_ET_cooling == 1:
                    Disconnected_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W = \
                    dfBest["Nominal Power single effect ACH to AHU_SCU (ET) [W]"].iloc[0]

                if Disconnected_direct_expansion_to_AHU_SCU_share_cooling == 1:
                    Disconnected_direct_expansion_to_AHU_SCU_capacity_cooling_W = \
                    dfBest["Nominal Power DX to AHU_SCU [W]"].iloc[0]

                if Disconnected_VCC_to_AHU_SCU_share_cooling == 1:
                    Disconnected_VCC_to_AHU_SCU_capacity_cooling_W = dfBest["Nominal Power VCC to AHU_SCU [W]"].iloc[0]

            if DCN_unit_configuration == 3:  # corresponds to SCU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'AHU_ARU'

                df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result_cooling(building_names[i],
                                                                                                      decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Disconnected_direct_expansion_to_AHU_ARU_share_cooling = dfBest["DX to AHU_ARU Share"].iloc[0]
                Disconnected_single_effect_ACH_to_AHU_ARU_share_FP_cooling = \
                    dfBest["single effect ACH to AHU_ARU Share (FP)"].iloc[0]
                Disconnected_single_effect_ACH_to_AHU_ARU_share_ET_cooling = \
                    dfBest["single effect ACH to AHU_ARU Share (ET)"].iloc[0]
                Disconnected_VCC_to_AHU_ARU_share_cooling = dfBest["VCC to AHU_ARU Share"].iloc[0]

                if Disconnected_single_effect_ACH_to_AHU_ARU_share_FP_cooling == 1:
                    Disconnected_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W = \
                        dfBest["Nominal Power single effect ACH to AHU_ARU (FP) [W]"].iloc[0]

                if Disconnected_single_effect_ACH_to_AHU_ARU_share_ET_cooling == 1:
                    Disconnected_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W = \
                        dfBest["Nominal Power single effect ACH to AHU_ARU (ET) [W]"].iloc[0]

                if Disconnected_direct_expansion_to_AHU_ARU_share_cooling == 1:
                    Disconnected_direct_expansion_to_AHU_ARU_capacity_cooling_W = \
                        dfBest["Nominal Power DX to AHU_ARU [W]"].iloc[0]

                if Disconnected_VCC_to_AHU_ARU_share_cooling == 1:
                    Disconnected_VCC_to_AHU_ARU_capacity_cooling_W = \
                        dfBest["Nominal Power VCC to AHU_ARU [W]"].iloc[0]

            if DCN_unit_configuration == 4:  # corresponds to AHU + ARU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'SCU'

                df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result_cooling(building_names[i],
                                                                                                      decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Disconnected_direct_expansion_to_SCU_share_cooling = dfBest["DX to SCU Share"].iloc[0]
                Disconnected_single_effect_ACH_to_SCU_share_FP_cooling = \
                    dfBest["single effect ACH to SCU Share (FP)"].iloc[0]
                Disconnected_single_effect_ACH_to_SCU_share_ET_cooling = \
                    dfBest["single effect ACH to SCU Share (ET)"].iloc[0]
                Disconnected_VCC_to_SCU_share_cooling = dfBest["VCC to SCU Share"].iloc[0]

                if Disconnected_single_effect_ACH_to_SCU_share_FP_cooling == 1:
                    Disconnected_single_effect_ACH_to_SCU_capacity_FP_cooling_W = \
                        dfBest["Nominal Power single effect ACH to SCU (FP) [W]"].iloc[0]

                if Disconnected_single_effect_ACH_to_SCU_share_ET_cooling == 1:
                    Disconnected_single_effect_ACH_to_SCU_capacity_ET_cooling_W = \
                        dfBest["Nominal Power single effect ACH to SCU (ET) [W]"].iloc[0]

                if Disconnected_direct_expansion_to_SCU_share_cooling == 1:
                    Disconnected_direct_expansion_to_SCU_capacity_cooling_W = \
                        dfBest["Nominal Power DX to SCU [W]"].iloc[0]

                if Disconnected_VCC_to_SCU_share_cooling == 1:
                    Disconnected_VCC_to_SCU_capacity_cooling_W = \
                        dfBest["Nominal Power VCC to SCU [W]"].iloc[0]

            if DCN_unit_configuration == 5:  # corresponds to AHU + SCU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'ARU'

                df = pd.read_csv(locator.get_optimization_disconnected_folder_building_result_cooling(building_names[i],
                                                                                                      decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Disconnected_direct_expansion_to_ARU_share_cooling = dfBest["DX to ARU Share"].iloc[0]
                Disconnected_single_effect_ACH_to_ARU_share_FP_cooling = \
                    dfBest["single effect ACH to ARU Share (FP)"].iloc[0]
                Disconnected_single_effect_ACH_to_ARU_share_ET_cooling = \
                    dfBest["single effect ACH to ARU Share (ET)"].iloc[0]
                Disconnected_VCC_to_ARU_share_cooling = dfBest["VCC to ARU Share"].iloc[0]

                if Disconnected_single_effect_ACH_to_ARU_share_FP_cooling == 1:
                    Disconnected_single_effect_ACH_to_ARU_capacity_FP_cooling_W = \
                        dfBest["Nominal Power single effect ACH to ARU (FP) [W]"].iloc[0]

                if Disconnected_single_effect_ACH_to_ARU_share_ET_cooling == 1:
                    Disconnected_single_effect_ACH_to_ARU_capacity_ET_cooling_W = \
                        dfBest["Nominal Power single effect ACH to ARU (ET) [W]"].iloc[0]

                if Disconnected_direct_expansion_to_ARU_share_cooling == 1:
                    Disconnected_direct_expansion_to_ARU_capacity_cooling_W = \
                        dfBest["Nominal Power DX to ARU [W]"].iloc[0]

                if Disconnected_VCC_to_ARU_share_cooling == 1:
                    Disconnected_VCC_to_ARU_capacity_cooling_W = \
                        dfBest["Nominal Power VCC to ARU [W]"].iloc[0]

            if DCN_unit_configuration == 6:  # corresponds to ARU + SCU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'AHU'

                df = pd.read_csv(
                    locator.get_optimization_disconnected_folder_building_result_cooling(building_names[i],
                                                                                         decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Disconnected_direct_expansion_to_AHU_share_cooling = dfBest["DX to AHU Share"].iloc[0]
                Disconnected_single_effect_ACH_to_AHU_share_FP_cooling = \
                    dfBest["single effect ACH to AHU Share (FP)"].iloc[0]
                Disconnected_single_effect_ACH_to_AHU_share_ET_cooling = \
                    dfBest["single effect ACH to AHU Share (ET)"].iloc[0]
                Disconnected_VCC_to_AHU_share_cooling = dfBest["VCC to AHU Share"].iloc[0]

                if Disconnected_single_effect_ACH_to_AHU_share_FP_cooling == 1:
                    Disconnected_single_effect_ACH_to_AHU_capacity_FP_cooling_W = \
                        dfBest["Nominal Power single effect ACH to AHU (FP) [W]"].iloc[0]

                if Disconnected_single_effect_ACH_to_AHU_share_ET_cooling == 1:
                    Disconnected_single_effect_ACH_to_AHU_capacity_ET_cooling_W = \
                        dfBest["Nominal Power single effect ACH to AHU (ET) [W]"].iloc[0]

                if Disconnected_direct_expansion_to_AHU_share_cooling == 1:
                    Disconnected_direct_expansion_to_AHU_capacity_cooling_W = \
                        dfBest["Nominal Power DX to AHU [W]"].iloc[0]

                if Disconnected_VCC_to_AHU_share_cooling == 1:
                    Disconnected_VCC_to_AHU_capacity_cooling_W = \
                        dfBest["Nominal Power VCC to AHU [W]"].iloc[0]

            disconnected_capacity = dict(building_name=building_names[i],
                                         Disconnected_Boiler_BG_share=Disconnected_Boiler_BG_share_heating,
                                         Disconnected_Boiler_BG_capacity_W=Disconnected_Boiler_BG_capacity_heating_W,
                                         Disconnected_Boiler_NG_share=Disconnected_Boiler_NG_share_heating,
                                         Disconnected_Boiler_NG_capacity_W=Disconnected_Boiler_NG_capacity_heating_W,
                                         Disconnected_FC_share=Disconnected_FC_share_heating,
                                         Disconnected_FC_capacity_W=Disconnected_FC_capacity_heating_W,
                                         Disconnected_GHP_share=Disconnected_GHP_share_heating,
                                         Disconnected_GHP_capacity_W=Disconnected_GHP_capacity_heating_W,
                                         Disconnected_VCC_to_AHU_share_cooling=Disconnected_VCC_to_AHU_share_cooling,
                                         Disconnected_VCC_to_AHU_capacity_cooling_W=Disconnected_VCC_to_AHU_capacity_cooling_W,
                                         Disconnected_VCC_to_ARU_share_cooling=Disconnected_VCC_to_ARU_share_cooling,
                                         Disconnected_VCC_to_ARU_capacity_cooling_W=Disconnected_VCC_to_ARU_capacity_cooling_W,
                                         Disconnected_VCC_to_SCU_share_cooling=Disconnected_VCC_to_SCU_share_cooling,
                                         Disconnected_VCC_to_SCU_capacity_cooling_W=Disconnected_VCC_to_SCU_capacity_cooling_W,
                                         Disconnected_VCC_to_AHU_ARU_share_cooling=Disconnected_VCC_to_AHU_ARU_share_cooling,
                                         Disconnected_VCC_to_AHU_ARU_capacity_cooling_W=Disconnected_VCC_to_AHU_ARU_capacity_cooling_W,
                                         Disconnected_VCC_to_AHU_SCU_share_cooling=Disconnected_VCC_to_AHU_SCU_share_cooling,
                                         Disconnected_VCC_to_AHU_SCU_capacity_cooling_W=Disconnected_VCC_to_AHU_SCU_capacity_cooling_W,
                                         Disconnected_VCC_to_ARU_SCU_share_cooling=Disconnected_VCC_to_ARU_SCU_share_cooling,
                                         Disconnected_VCC_to_ARU_SCU_capacity_cooling_W=Disconnected_VCC_to_ARU_SCU_capacity_cooling_W,
                                         Disconnected_VCC_to_AHU_ARU_SCU_share_cooling=Disconnected_VCC_to_AHU_ARU_SCU_share_cooling,
                                         Disconnected_VCC_to_AHU_ARU_SCU_capacity_cooling_W=Disconnected_VCC_to_AHU_ARU_SCU_capacity_cooling_W,
                                         Disconnected_single_effect_ACH_to_AHU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_share_FP_cooling,
                                         Disconnected_single_effect_ACH_to_AHU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_capacity_FP_cooling_W,
                                         Disconnected_single_effect_ACH_to_AHU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_share_ET_cooling,
                                         Disconnected_single_effect_ACH_to_AHU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_capacity_ET_cooling_W,
                                         Disconnected_single_effect_ACH_to_ARU_share_FP_cooling=Disconnected_single_effect_ACH_to_ARU_share_FP_cooling,
                                         Disconnected_single_effect_ACH_to_ARU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_ARU_capacity_FP_cooling_W,
                                         Disconnected_single_effect_ACH_to_ARU_share_ET_cooling=Disconnected_single_effect_ACH_to_ARU_share_ET_cooling,
                                         Disconnected_single_effect_ACH_to_ARU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_ARU_capacity_ET_cooling_W,
                                         Disconnected_single_effect_ACH_to_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_SCU_share_FP_cooling,
                                         Disconnected_single_effect_ACH_to_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_SCU_capacity_FP_cooling_W,
                                         Disconnected_single_effect_ACH_to_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_SCU_share_ET_cooling,
                                         Disconnected_single_effect_ACH_to_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_SCU_capacity_ET_cooling_W,
                                         Disconnected_single_effect_ACH_to_AHU_ARU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_share_FP_cooling,
                                         Disconnected_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W,
                                         Disconnected_single_effect_ACH_to_AHU_ARU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_share_ET_cooling,
                                         Disconnected_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W,
                                         Disconnected_single_effect_ACH_to_AHU_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_SCU_share_FP_cooling,
                                         Disconnected_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W,
                                         Disconnected_single_effect_ACH_to_AHU_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_SCU_share_ET_cooling,
                                         Disconnected_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W,
                                         Disconnected_single_effect_ACH_to_ARU_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_ARU_SCU_share_FP_cooling,
                                         Disconnected_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W,
                                         Disconnected_single_effect_ACH_to_ARU_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_ARU_SCU_share_ET_cooling,
                                         Disconnected_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W,
                                         Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling,
                                         Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W,
                                         Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling,
                                         Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W=Disconnected_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W,
                                         Disconnected_direct_expansion_to_AHU_share_cooling=Disconnected_direct_expansion_to_AHU_share_cooling,
                                         Disconnected_direct_expansion_to_AHU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_capacity_cooling_W,
                                         Disconnected_direct_expansion_to_ARU_share_cooling=Disconnected_direct_expansion_to_ARU_share_cooling,
                                         Disconnected_direct_expansion_to_ARU_capacity_cooling_W=Disconnected_direct_expansion_to_ARU_capacity_cooling_W,
                                         Disconnected_direct_expansion_to_SCU_share_cooling=Disconnected_direct_expansion_to_SCU_share_cooling,
                                         Disconnected_direct_expansion_to_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_SCU_capacity_cooling_W,
                                         Disconnected_direct_expansion_to_AHU_SCU_share_cooling=Disconnected_direct_expansion_to_AHU_SCU_share_cooling,
                                         Disconnected_direct_expansion_to_AHU_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_SCU_capacity_cooling_W,
                                         Disconnected_direct_expansion_to_AHU_ARU_share_cooling=Disconnected_direct_expansion_to_AHU_ARU_share_cooling,
                                         Disconnected_direct_expansion_to_AHU_ARU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_ARU_capacity_cooling_W,
                                         Disconnected_direct_expansion_to_ARU_SCU_share_cooling=Disconnected_direct_expansion_to_ARU_SCU_share_cooling,
                                         Disconnected_direct_expansion_to_ARU_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_ARU_SCU_capacity_cooling_W,
                                         Disconnected_direct_expansion_to_AHU_ARU_SCU_share_cooling=Disconnected_direct_expansion_to_AHU_ARU_SCU_share_cooling,
                                         Disconnected_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W=Disconnected_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W)

        intermediate_capacities.append(disconnected_capacity)
    disconnected_capacities.append(dict(network=network, disconnected_capacity=intermediate_capacities))