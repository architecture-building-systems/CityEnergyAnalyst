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

    # Based on the slave data, capacities corresponding to the centralized network are calculated in the following
    # script. Note that irrespective of the number of technologies used in an individual, the length of the dict
    # is constant
    for i, ind in enumerate(slavedata_list):
        if ind.Furn_Moist_type == "wet":
            Furnace_wet = ind.Furnace_on
            Furnace_wet_capacity_W = ind.Furnace_Q_max
        elif ind.Furn_Moist_type == "dry":
            Furnace_dry = ind.Furnace_on
            Furnace_dry_capacity_W = ind.Furnace_Q_max
        if ind.gt_fuel == "NG":
            CHP_NG = ind.CC_on
            CHP_NG_capacity_W = ind.CC_GT_SIZE
            Base_boiler_NG = ind.Boiler_on
            Base_boiler_NG_capacity_W = ind.Boiler_Q_max
            Peak_boiler_NG = ind.BoilerPeak_on
            Peak_boiler_NG_capacity_W = ind.BoilerPeak_Q_max
        elif ind.gt_fuel == "BG":
            CHP_BG = ind.CC_on
            CHP_BG_capacity_W = ind.CC_GT_SIZE
            Base_boiler_BG = ind.Boiler_on
            Base_boiler_BG_capacity_W = ind.Boiler_Q_max
            Peak_boiler_BG = ind.BoilerPeak_on
            Peak_boiler_BG_capacity_W = ind.BoilerPeak_Q_max

        HP_Lake = ind.HP_Lake_on
        HP_Lake_capacity_W = ind.HPLake_maxSize
        HP_Sewage = ind.HP_Sew_on
        HP_Sewage_capacity_W = ind.HPSew_maxSize
        GHP = ind.GHP_on
        GHP_capacity_W = ind.GHP_number * GHP_HMAX_SIZE
        PV = pop[i][N_HEAT * 2 + N_HR]
        PV_capacity_W = ind.SOLAR_PART_PV * solar_features.A_PV_m2 * N_PV * 1000
        if config.district_heating_network:
            PVT = pop[i][N_HEAT * 2 + N_HR + 2]
            PVT_capacity_W = ind.SOLAR_PART_PVT * solar_features.A_PVT_m2 * N_PVT * 1000
        else:
            PVT = 0
            PVT_capacity_W = 0

        SC_ET = pop[i][N_HEAT * 2 + N_HR + 4]
        SC_ET_capacity_W = ind.SOLAR_PART_SC_ET * solar_features.A_SC_ET_m2 * 1000
        SC_FP = pop[i][N_HEAT * 2 + N_HR + 6]
        SC_FP_capacity_W = ind.SOLAR_PART_SC_FP * solar_features.A_SC_FP_m2 * 1000

        VCC = ind.VCC_on
        VCC_capacity_W = ind.VCC_cooling_size
        Absorption_Chiller = ind.Absorption_Chiller_on
        Absorption_Chiller_capacity_W = ind.Absorption_chiller_size
        Lake_cooling = ind.Lake_cooling_on
        Lake_cooling_capacity_W = ind.Lake_cooling_size
        storage_cooling = ind.storage_cooling_on
        storage_cooling_capacity_W = ind.Storage_cooling_size

        capacity = dict(ind=i, generation=genCP,
                        Furnace_wet=Furnace_wet, Furnace_wet_capacity_W=Furnace_wet_capacity_W,
                        Furnace_dry=Furnace_dry, Furnace_dry_capacity_W=Furnace_dry_capacity_W,
                        CHP_NG=CHP_NG, CHP_NG_capacity_W=CHP_NG_capacity_W,
                        CHP_BG=CHP_BG, CHP_BG_capacity_W=CHP_BG_capacity_W,
                        Base_boiler_BG=Base_boiler_BG, Base_boiler_BG_capacity_W=Base_boiler_BG_capacity_W,
                        Base_boiler_NG=Base_boiler_NG, Base_boiler_NG_capacity_W=Base_boiler_NG_capacity_W,
                        Peak_boiler_BG=Peak_boiler_BG, Peak_boiler_BG_capacity_W=Peak_boiler_BG_capacity_W,
                        Peak_boiler_NG=Peak_boiler_NG, Peak_boiler_NG_capacity_W=Peak_boiler_NG_capacity_W,
                        HP_Lake=HP_Lake, HP_Lake_capacity_W=HP_Lake_capacity_W,
                        HP_Sewage=HP_Sewage, HP_Sewage_capacity_W=HP_Sewage_capacity_W,
                        GHP=GHP, GHP_capacity_W=GHP_capacity_W,
                        PV=PV, PV_capacity_W=PV_capacity_W,
                        PVT=PVT, PVT_capacity_W=PVT_capacity_W,
                        SC_ET=SC_ET, SC_ET_capacity_W=SC_ET_capacity_W,
                        SC_FP=SC_FP, SC_FP_capacity_W=SC_FP_capacity_W,
                        VCC=VCC, VCC_capacity_W=VCC_capacity_W,
                        Absorption_Chiller=Absorption_Chiller,
                        Absorption_Chiller_capacity_W=Absorption_Chiller_capacity_W,
                        Lake_cooling=Lake_cooling, Lake_cooling_capacity_W=Lake_cooling_capacity_W,
                        storage_cooling=storage_cooling, storage_cooling_capacity_W=storage_cooling_capacity_W)
        capacities.append(capacity)