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
    "red_lightest": "rgb(253,236,233)",
    "red_dark": "rgb(191,98,96)",

    "blue": "rgb(63,192,194)",
    "blue_light": "rgb(151,214,215)",
    "blue_lighter": "rgb(219,240,239)",
    "blue_lightest": "rgb(237,247,247)",

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
    "green_lightest": "rgb(241,248,242)",

    "grey": "rgb(127,128,134)",
    "grey_light": "rgb(162,161,166)",
    "grey_lighter": "rgb(201,200,203)",

    "black": "rgb(0,0,0)",
    "white": "rgb(255,255,255)",

    "orange": "rgb(245,131,69)",
    "orange_light": "rgb(250,177,133)",
    "orange_lighter": "rgb(254,226,207)",
    "orange_lightest": "rgb(255,241,233)",

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


# Base color mapping without units - maps metric prefixes to colors
_BASE_COLUMN_COLORS = {
    # ===== Grid & Demand =====
    "GRID": "purple",
    "E_sys": "green",
    "QC_sys": "blue_lighter",
    "Qcs_sys": "blue",
    "QH_sys": "red_lighter",
    "Qhs_sys": "red",
    "Qww": "orange",

    # ===== Total Generation =====
    "E_PV_gen": "yellow",
    "E_PVT_gen": "yellow",
    "Q_PVT_gen": "yellow_light",
    "Q_SC_gen": "yellow_light",

    # ===== Roof =====
    "PV_roofs_top_E": "red",
    "PVT_ET_roofs_top_E": "red",
    "PVT_ET_roofs_top_Q": "red_light",
    "PVT_FP_roofs_top_E": "red",
    "PVT_FP_roofs_top_Q": "red_light",
    "SC_ET_roofs_top_Q": "red_lighter",
    "SC_FP_roofs_top_Q": "red_lighter",

    # ===== North Wall =====
    "PV_walls_north_E": "orange",
    "PVT_ET_walls_north_E": "orange",
    "PVT_ET_walls_north_Q": "orange_light",
    "PVT_FP_walls_north_E": "orange",
    "PVT_FP_walls_north_Q": "orange_light",
    "SC_ET_walls_north_Q": "orange_light",
    "SC_FP_walls_north_Q": "orange_light",

    # ===== East Wall =====
    "PV_walls_east_E": "blue",
    "PVT_ET_walls_east_E": "blue",
    "PVT_ET_walls_east_Q": "blue_light",
    "PVT_FP_walls_east_E": "blue",
    "PVT_FP_walls_east_Q": "blue_light",
    "SC_ET_walls_east_Q": "blue_light",
    "SC_FP_walls_east_Q": "blue_light",

    # ===== South Wall =====
    "PV_walls_south_E": "green",
    "PVT_ET_walls_south_E": "green",
    "PVT_ET_walls_south_Q": "green_light",
    "PVT_FP_walls_south_E": "green",
    "PVT_FP_walls_south_Q": "green_light",
    "SC_ET_walls_south_Q": "green_light",
    "SC_FP_walls_south_Q": "green_light",

    # ===== West Wall =====
    "PV_walls_west_E": "purple",
    "PVT_ET_walls_west_E": "purple",
    "PVT_ET_walls_west_Q": "purple_light",
    "PVT_FP_walls_west_E": "purple",
    "PVT_FP_walls_west_Q": "purple_light",
    "SC_ET_walls_west_Q": "purple_light",
    "SC_FP_walls_west_Q": "purple_light",

    # ===== Operational Emissions =====
    "heating": "red",
    "hot_water": "orange",
    "cooling": "blue",
    "electricity": "green",
    "Qhs_sys_NATURALGAS": "red_lighter",
    "Qhs_sys_BIOGAS": "red_lighter",
    "Qhs_sys_SOLAR": "red_lighter",
    "Qhs_sys_DRYBIOMASS": "red_lighter",
    "Qhs_sys_WETBIOMASS": "red_lighter",
    "Qhs_sys_GRID": "red_lighter",
    "Qhs_sys_COAL": "red_lighter",
    "Qhs_sys_WOOD": "red_lighter",
    "Qhs_sys_OIL": "red_lighter",
    "Qhs_sys_HYDROGEN": "red_lighter",
    "Qhs_sys_NONE": "red_lighter",
    "Qww_sys_NATURALGAS": "orange_lighter",
    "Qww_sys_BIOGAS": "orange_lighter",
    "Qww_sys_SOLAR": "orange_lighter",
    "Qww_sys_DRYBIOMASS": "orange_lighter",
    "Qww_sys_WETBIOMASS": "orange_lighter",
    "Qww_sys_GRID": "orange_lighter",
    "Qww_sys_COAL": "orange_lighter",
    "Qww_sys_WOOD": "orange_lighter",
    "Qww_sys_OIL": "orange_lighter",
    "Qww_sys_HYDROGEN": "orange_lighter",
    "Qww_sys_NONE": "orange_lighter",
    "Qcs_sys_NATURALGAS": "blue_lighter",
    "Qcs_sys_BIOGAS": "blue_lighter",
    "Qcs_sys_SOLAR": "blue_lighter",
    "Qcs_sys_DRYBIOMASS": "blue_lighter",
    "Qcs_sys_WETBIOMASS": "blue_lighter",
    "Qcs_sys_GRID": "blue_lighter",
    "Qcs_sys_COAL": "blue_lighter",
    "Qcs_sys_WOOD": "blue_lighter",
    "Qcs_sys_OIL": "blue_lighter",
    "Qcs_sys_HYDROGEN": "blue_lighter",
    "Qcs_sys_NONE": "blue_lighter",
    "E_sys_NATURALGAS": "green_lighter",
    "E_sys_BIOGAS": "green_lighter",
    "E_sys_SOLAR": "green_lighter",
    "E_sys_DRYBIOMASS": "green_lighter",
    "E_sys_WETBIOMASS": "green_lighter",
    "E_sys_GRID": "green_lighter",
    "E_sys_COAL": "green_lightert",
    "E_sys_WOOD": "green_lighter",
    "E_sys_OIL": "green_lighter",
    "E_sys_HYDROGEN": "green_lighter",
    "E_sys_NONE": "green_lighter",

    # ===== Lifecycle Emissions =====
    "operation_heating": "red",
    "operation_hot_water": "orange",
    "operation_cooling": "blue",
    "operation_electricity": "green",
    "production_wall_ag": "red_lighter",
    "production_wall_bg": "red_lighter",
    "production_wall_part": "red_lighter",
    "production_win_ag": "red_lighter",
    "production_roof": "red_lighter",
    "production_upperside": "red_lighter",
    "production_underside": "red_lighter",
    "production_floor": "red_lighter",
    "production_base": "red_lighter",
    "production_technical_systems": "red_lighter",
    "biogenic_wall_ag": "blue_lighter",
    "biogenic_wall_bg": "blue_lighter",
    "biogenic_wall_part": "blue_lighter",
    "biogenic_win_ag": "blue_lighter",
    "biogenic_roof": "blue_lighter",
    "biogenic_upperside": "blue_lighter",
    "biogenic_underside": "blue_lighter",
    "biogenic_floor": "blue_lighter",
    "biogenic_base": "blue_lighter",
    "biogenic_technical_systems": "blue_lighter",
    "demolition_wall_ag": "green_lighter",
    "demolition_wall_bg": "green_lighter",
    "demolition_wall_part": "green_lighter",
    "demolition_win_ag": "green_lighter",
    "demolition_roof": "green_lighter",
    "demolition_upperside": "green_lighter",
    "demolition_underside": "green_lighter",
    "demolition_floor": "green_lighter",
    "demolition_base": "green_lighter",
    "demolition_technical_systems": "green_lighter",

}


def get_column_color(column_name):
    """
    Get color for a column name, handling dynamic units.

    Strips the unit suffix (e.g., _kWh, _MWh, _kgCO2e, _tonCO2e, /m2)
    from the column name and looks up the base color.

    Parameters:
    - column_name (str): Column name with unit (e.g., 'GRID_MWh/m2')

    Returns:
    - str: Color name (e.g., 'purple')
    """
    # Remove common unit patterns
    base_name = column_name

    # Remove /m2 suffix first
    if '/m2' in base_name:
        base_name = base_name.split('/m2')[0]

    # Remove energy units: _Wh, _kWh, _MWh
    for unit in ['_MWh', '_kWh', '_Wh']:
        if base_name.endswith(unit):
            base_name = base_name[:-len(unit)]
            break

    # Remove emission units: _gCO2e, _kgCO2e, _tonCO2e
    for unit in ['_tonCO2e', '_kgCO2e', '_gCO2e']:
        if base_name.endswith(unit):
            base_name = base_name[:-len(unit)]
            break

    # Look up in base color mapping
    return _BASE_COLUMN_COLORS.get(base_name, "grey")


# Generate the full COLUMNS_TO_COLOURS dict for backward compatibility
COLUMNS_TO_COLOURS = {}
for base_name, color in _BASE_COLUMN_COLORS.items():
    # Generate all unit variations
    if any(x in base_name for x in ['_E', '_Q', 'PV', 'PVT', 'SC', 'sys', 'GRID']):
        # Energy metrics
        for unit in ['Wh', 'kWh', 'MWh']:
            COLUMNS_TO_COLOURS[f"{base_name}_{unit}"] = color
            COLUMNS_TO_COLOURS[f"{base_name}_{unit}/m2"] = color

    if 'sys' in base_name or base_name in ['heating', 'hot_water', 'cooling', 'electricity']:
        # Emission metrics
        for unit in ['gCO2e', 'kgCO2e', 'tonCO2e']:
            COLUMNS_TO_COLOURS[f"{base_name}_{unit}"] = color
            COLUMNS_TO_COLOURS[f"{base_name}_{unit}/m2"] = color























