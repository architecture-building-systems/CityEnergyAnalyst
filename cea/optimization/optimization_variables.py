# -*- coding: utf-8 -*-
"""
This file contains the variables used in objective function calculation in optimization
"""
from __future__ import absolute_import
from cea.optimization.optimization_constants import optimization_constants
__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

class optimization_variables(object):
    def __init__(self):

        self.initialind = 2  # number of initial individuals
        self.NGEN = 5  # number of total generations
        self.fCheckPoint = 1  # frequency for the saving of checkpoints
        self.maxTime = 7 * 24 * 3600  # maximum computational time [seconds]

        self.ZernezFlag = 0
        self.FlagBioGasFromAgriculture = 0  # 1 = Biogas from Agriculture, 0 = Biogas normal
        self.HPSew_allowed = 1
        self.HPLake_allowed = 1
        self.GHP_allowed = 1
        self.CC_allowed = 1
        self.Furnace_allowed = 0
        self.DiscGHPFlag = 1  # Is geothermal allowed in disconnected buildings? 0 = NO ; 1 = YES
        self.DiscBioGasFlag = 0  # 1 = use Biogas only in Disconnected Buildings, no Natural Gas; 0so = both possible


        # Emission and Primary energy factors

        ######### Biogas to Agric. Bio Gas emissions
        self.NormalBGToAgriBG_CO2 = 0.127 / 0.754  # Values from Electricity used for comparison
        self.NormalBGToAgriBG_Eprim = 0.0431 / 0.101  # Values from Electricity used for comparison

        ######### CENTRAL HUB PLANT : factor with regard to FINAL ENERGY

        # normalized on their efficiency, including all CO2 emissions (Primary, grey, electricity etc. until exit of Hub)
        # usage : divide by system efficiency and Hub to building-efficiency
        self.ETA_FINAL_TO_USEFUL = 0.9  # assume 90% system efficiency in terms of CO2 emissions and overhead emissions (\

        ######### ELECTRICITY
        self.CC_EL_TO_TOTAL = 4 / 9

        self.EL_TO_OIL_EQ = 2.69  # MJ_oil / MJ_final
        self.EL_TO_CO2 = 0.0385  # kg_CO2 / MJ_final - CH Verbrauchermix nach EcoBau

        self.EL_TO_OIL_EQ_GREEN = 0.0339  # MJ_oil / MJ_final
        self.EL_TO_CO2_GREEN = 0.00398  # kg_CO2 / MJ_final

        self.EL_NGCC_TO_OIL_EQ_STD = 2.94 * 0.78 * self.CC_EL_TO_TOTAL  # MJ_oil / MJ_final
        EL_NGCC_TO_CO2_STD = 0.186 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

        if self.FlagBioGasFromAgriculture == 1:  # Use Biogas from Agriculture
            self.EL_BGCC_TO_OIL_EQ_STD = 0.156 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
            self.EL_BGCC_TO_CO2_STD = 0.0495 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
        else:
            self.EL_BGCC_TO_OIL_EQ_STD = 0.851 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final
            self.EL_BGCC_TO_CO2_STD = 0.114 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

        self.EL_FURNACE_TO_OIL_EQ_STD = 0.141 * 0.78 * self.CC_EL_TO_TOTAL  # MJ_oil / MJ_final
        self.EL_FURNACE_TO_CO2_STD = 0.0285 * 0.78 * self.CC_EL_TO_TOTAL  # kg_CO2 / MJ_final

        # Combined Cycle
        self.CC_sigma = 4 / 5

        self.NG_CC_TO_CO2_STD = (0.0353 + 0.186) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
            1 + self.CC_sigma)  # kg_CO2 / MJ_useful
        self.NG_CC_TO_OIL_STD = (0.6 + 2.94) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
            1 + self.CC_sigma)  # MJ_oil / MJ_useful

        if self.FlagBioGasFromAgriculture == 1:
            self.BG_CC_TO_CO2_STD = (0.00592 + 0.0495) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
                1 + self.CC_sigma)  # kg_CO2 / MJ_useful
            self.BG_CC_TO_OIL_STD = (0.0703 + 0.156) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
                1 + self.CC_sigma)  # MJ_oil / MJ_useful

        else:
            self.BG_CC_TO_CO2_STD = (0.0223 + 0.114) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
                1 + self.CC_sigma)  # kg_CO2 / MJ_useful
            self.BG_CC_TO_OIL_STD = (0.214 + 0.851) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
                1 + self.CC_sigma)  # kg_CO2 / MJ_useful

        # Furnace
        self.FURNACE_TO_CO2_STD = (0.0104 + 0.0285) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
            1 + self.CC_sigma)  # kg_CO2 / MJ_useful
        self.FURNACE_TO_OIL_STD = (0.0956 + 0.141) * 0.78 / self.ETA_FINAL_TO_USEFUL * (
            1 + self.CC_sigma)  # MJ_oil / MJ_useful

        # Boiler
        self.NG_BOILER_TO_CO2_STD = 0.0874 * 0.87 / self.ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
        self.NG_BOILER_TO_OIL_STD = 1.51 * 0.87 / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

        if self.FlagBioGasFromAgriculture == 1:
            self.BG_BOILER_TO_CO2_STD = 0.339 * 0.87 * self.NormalBGToAgriBG_CO2 / (
                1 + optimization_constants.DHNetworkLoss) / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful
            self.BG_BOILER_TO_OIL_STD = 0.04 * 0.87 * self.NormalBGToAgriBG_Eprim / (
                1 + optimization_constants.DHNetworkLoss) / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

        else:
            self.BG_BOILER_TO_CO2_STD = self.NG_BOILER_TO_CO2_STD * 0.04 / 0.0691  # kg_CO2 / MJ_useful
            self.BG_BOILER_TO_OIL_STD = self.NG_BOILER_TO_OIL_STD * 0.339 / 1.16  # MJ_oil / MJ_useful

        # HP Lake
        self.LAKEHP_TO_CO2_STD = 0.0262 * 2.8 / self.ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
        self.LAKEHP_TO_OIL_STD = 1.22 * 2.8 / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

        # HP Sewage
        self.SEWAGEHP_TO_CO2_STD = 0.0192 * 3.4 / self.ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
        self.SEWAGEHP_TO_OIL_STD = 0.904 * 3.4 / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful

        # GHP
        self.GHP_TO_CO2_STD = 0.0210 * 3.9 / self.ETA_FINAL_TO_USEFUL  # kg_CO2 / MJ_useful
        self.GHP_TO_OIL_STD = 1.03 * 3.9 / self.ETA_FINAL_TO_USEFUL  # MJ_oil / MJ_useful