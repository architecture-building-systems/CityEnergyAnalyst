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


COLOURS_TO_RGB = {
    "red": "rgb(240,77,91)",
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

    "uuen_blue": "rgb(20,113,176)",
    "uuen_blue_light": "rgb(124,156,202)",
    "uuen_blue_lighter": "rgb(206,215,234)",

    "background_grey": "rgb(247,247,247)",

    # ✨ Additional Colors
    "teal": "rgb(0,128,128)",
    "teal_light": "rgb(102,205,170)",
    "teal_lighter": "rgb(204,255,229)",

    "cyan": "rgb(0,183,235)",
    "cyan_light": "rgb(132,222,244)",
    "cyan_lighter": "rgb(210,243,255)",

    "magenta": "rgb(255,0,255)",
    "magenta_light": "rgb(255,153,255)",
    "magenta_lighter": "rgb(255,214,255)",

    "pink": "rgb(255,105,180)",
    "pink_light": "rgb(255,182,193)",
    "pink_lighter": "rgb(255,228,235)",

    "indigo": "rgb(75,0,130)",
    "indigo_light": "rgb(138,43,226)",
    "indigo_lighter": "rgb(191,143,255)",

    "olive": "rgb(128,128,0)",
    "olive_light": "rgb(189,183,107)",
    "olive_lighter": "rgb(240,230,140)",

    "navy": "rgb(0,0,128)",
    "navy_light": "rgb(100,149,237)",
    "navy_lighter": "rgb(173,216,230)",
}


COLUMNS_TO_COLOURS = {
    # ===== Grid & Demand =====
    "GRID_kWh": "purple",
    "GRID_kWh/m2": "purple",
    "E_sys_kWh": "green",
    "E_sys_kWh/m2": "green",
    "QC_sys_kWh": "blue_lighter",
    "QC_sys_kWh/m2": "blue_lighter",
    "Qcs_sys_kWh": "blue",
    "Qcs_sys_kWh/m2": "blue",
    "QH_sys_kWh": "red_lighter",
    "QH_sys_kWh/m2": "red_lighter",
    "Qhs_sys_kWh": "red",
    "Qhs_sys_kWh/m2": "red",
    "Qww_kWh": "orange",
    "Qww_kWh/m2": "orange",

    # ===== Total Generation =====
    "E_PV_gen_kWh": "yellow",
    "E_PV_gen_kWh/m2": "yellow",
    "E_PVT_gen_kWh": "yellow",
    "E_PVT_gen_kWh/m2": "yellow",
    "Q_PVT_gen_kWh": "yellow_lighter",
    "Q_PVT_gen_kWh/m2": "yellow_lighter",
    "Q_SC_gen_kWh": "yellow_lighter",
    "Q_SC_gen_kWh/m2": "yellow_lighter",

    # ===== Roof =====
    "PV_roofs_top_E_kWh": "red",
    "PV_roofs_top_E_kWh/m2": "red",
    "PVT_ET_roofs_top_E_kWh": "red",
    "PVT_ET_roofs_top_E_kWh/m2": "red",
    "PVT_ET_roofs_top_Q_kWh": "red_lighter",
    "PVT_ET_roofs_top_Q_kWh/m2": "red_lighter",
    "PVT_FP_roofs_top_E_kWh": "red",
    "PVT_FP_roofs_top_E_kWh/m2": "red",
    "PVT_FP_roofs_top_Q_kWh": "red_lighter",
    "PVT_FP_roofs_top_Q_kWh/m2": "red_lighter",
    "SC_ET_roofs_top_Q_kWh": "red_lighter",
    "SC_ET_roofs_top_Q_kWh/m2": "red_lighter",
    "SC_FP_roofs_top_Q_kWh": "red_lighter",
    "SC_FP_roofs_top_Q_kWh/m2": "red_lighter",

    # ===== North Wall =====
    "PV_walls_north_E_kWh": "orange",
    "PV_walls_north_E_kWh/m2": "orange",
    "PVT_ET_walls_north_E_kWh": "orange",
    "PVT_ET_walls_north_E_kWh/m2": "orange",
    "PVT_ET_walls_north_Q_kWh": "orange_lighter",
    "PVT_ET_walls_north_Q_kWh/m2": "orange_lighter",
    "PVT_FP_walls_north_E_kWh": "orange",
    "PVT_FP_walls_north_E_kWh/m2": "orange",
    "PVT_FP_walls_north_Q_kWh": "orange_lighter",
    "PVT_FP_walls_north_Q_kWh/m2": "orange_lighter",
    "SC_ET_walls_north_Q_kWh": "orange_lighter",
    "SC_ET_walls_north_Q_kWh/m2": "orange_lighter",
    "SC_FP_walls_north_Q_kWh": "orange_lighter",
    "SC_FP_walls_north_Q_kWh/m2": "orange_lighter",

    # ===== East Wall =====
    "PV_walls_east_E_kWh": "blue",
    "PV_walls_east_E_kWh/m2": "blue",
    "PVT_ET_walls_east_E_kWh": "blue",
    "PVT_ET_walls_east_E_kWh/m2": "blue",
    "PVT_ET_walls_east_Q_kWh": "blue_lighter",
    "PVT_ET_walls_east_Q_kWh/m2": "blue_lighter",
    "PVT_FP_walls_east_E_kWh": "blue",
    "PVT_FP_walls_east_E_kWh/m2": "blue",
    "PVT_FP_walls_east_Q_kWh": "blue_lighter",
    "PVT_FP_walls_east_Q_kWh/m2": "blue_lighter",
    "SC_ET_walls_east_Q_kWh": "blue_lighter",
    "SC_ET_walls_east_Q_kWh/m2": "blue_lighter",
    "SC_FP_walls_east_Q_kWh": "blue_lighter",
    "SC_FP_walls_east_Q_kWh/m2": "blue_lighter",

    # ===== South Wall =====
    "PV_walls_south_E_kWh": "green",
    "PV_walls_south_E_kWh/m2": "green",
    "PVT_ET_walls_south_E_kWh": "green",
    "PVT_ET_walls_south_E_kWh/m2": "green",
    "PVT_ET_walls_south_Q_kWh": "green_lighter",
    "PVT_ET_walls_south_Q_kWh/m2": "green_lighter",
    "PVT_FP_walls_south_E_kWh": "green",
    "PVT_FP_walls_south_E_kWh/m2": "green",
    "PVT_FP_walls_south_Q_kWh": "green_lighter",
    "PVT_FP_walls_south_Q_kWh/m2": "green_lighter",
    "SC_ET_walls_south_Q_kWh": "green_lighter",
    "SC_ET_walls_south_Q_kWh/m2": "green_lighter",
    "SC_FP_walls_south_Q_kWh": "green_lighter",
    "SC_FP_walls_south_Q_kWh/m2": "green_lighter",

    # ===== West Wall =====
    "PV_walls_west_E_kWh": "purple",
    "PV_walls_west_E_kWh/m2": "purple",
    "PVT_ET_walls_west_E_kWh": "purple",
    "PVT_ET_walls_west_E_kWh/m2": "purple",
    "PVT_ET_walls_west_Q_kWh": "purple_lighter",
    "PVT_ET_walls_west_Q_kWh/m2": "purple_lighter",
    "PVT_FP_walls_west_E_kWh": "purple",
    "PVT_FP_walls_west_E_kWh/m2": "purple",
    "PVT_FP_walls_west_Q_kWh": "purple_lighter",
    "PVT_FP_walls_west_Q_kWh/m2": "purple_lighter",
    "SC_ET_walls_west_Q_kWh": "purple_lighter",
    "SC_ET_walls_west_Q_kWh/m2": "purple_lighter",
    "SC_FP_walls_west_Q_kWh": "purple_lighter",
    "SC_FP_walls_west_Q_kWh/m2": "purple_lighter",
}





















