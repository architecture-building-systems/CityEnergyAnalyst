"""
This is the official list of CEA colors to use in plots
"""


__author__ = "Zhongming Shi"
__copyright__ = "Copyright 2025, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


COLOURS_TO_RGB = {"red": "rgb(240,77,91)",
                 "red_light": "rgb(246,149,143)",
                 "red_lighter": "rgb(252,217,210)",
                 "red_dark": "rgb(191,98,96)",
                 "blue": "rgb(63,192,194)",
                 "blue_light": "rgb(151,214,215)",
                 "blue_lighter": "rgb(219,240,239)",
                 "yellow": "rgb(255,209,29)",
                 "yellow_light": "rgb(255,225,133)",
                 "yellow_lighter": "rgb(255,243,211)",
                 "brown": "rgb(174,148,72)",
                 "brown_light": "rgb(201,183,135)",
                 "brown_lighter": "rgb(233,225,207)",
                 "purple": "rgb(171,95,127)",
                 "purple_light": "rgb(198,149,167)",
                 "purple_lighter": "rgb(231,214,219)",
                 "green": "rgb(126,199,143)",
                 "green_light": "rgb(178,219,183)",
                 "green_lighter": "rgb(227,241,228)",
                 "grey": "rgb(127,128,134)",
                 "grey_light": "rgb(162,161,166)",
                 "grey_lighter": "rgb(201,200,203)",
                 "black": "rgb(69,77,84)",
                 "white": "rgb(255,255,255)",
                 "orange": "rgb(245,131,69)",
                 "orange_light": "rgb(250,177,133)",
                 "orange_lighter": "rgb(254,226,207)",
                  "background_grey": "rgb(247,247,247)",
                  }

COLUMNS_TO_COLOURS = {"GRID_kWh": "purple",
                      "GRID_kWh/m2": "purple",
                      "E_sys_kWh": "green",
                      "E_sys_kWh/m2": "green",
                      "QC_sys_kWh": "blue_lighter",
                      "QC_sys_kWh/m2": "blue_lighter",
                      "Qcs_sys_kWh": "blue",
                      "Qcs_sys_kWh/m2": "blue",
                      "QH_sys_kWh/m2": "red_lighter",
                      "QH_sys_kWh": "red_lighter",
                      "Qhs_sys_kWh": "red",
                      "Qhs_sys_kWh/m2": "red",
                      "Qww_kWh": "orange",
                      "Qww_kWh/m2": "orange",
                      }
