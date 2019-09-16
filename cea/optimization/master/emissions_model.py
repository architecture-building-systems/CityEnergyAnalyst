from cea.constants import WH_TO_J

def calc_emissions_Whyr_to_tonCO2yr(E_Wh_yr, factor_kgCO2_to_MJ):
    return (E_Wh_yr * WH_TO_J / 1.0E6) * (factor_kgCO2_to_MJ / 1E3)


def calc_pen_Whyr_to_MJoilyr(E_Wh_yr, factor_MJ_to_MJ):
    return (E_Wh_yr * WH_TO_J / 1.0E6) * factor_MJ_to_MJ