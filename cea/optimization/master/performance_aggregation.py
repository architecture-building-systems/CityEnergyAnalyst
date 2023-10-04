



import numpy as np


def summarize_results_individual(buildings_district_scale_costs,
                                 buildings_district_scale_emissions,
                                 buildings_district_scale_heat,
                                 buildings_district_scale_sed,
                                 buildings_building_scale_costs,
                                 buildings_building_scale_emissions,
                                 buildings_building_scale_heat,
                                 buildings_building_scale_sed):

    # initialize values
    Capex_total_sys_district_scale_USD = 0.0
    Capex_a_sys_district_scale_USD = 0.0
    Opex_a_sys_district_scale_USD = 0.0
    TAC_sys_district_scale_USD = 0.0
    GHG_sys_district_scale_tonCO2 = 0.0
    HR_sys_district_scale_MWh = 0.0
    SED_sys_district_scale_MWh = 0.0

    Opex_a_sys_building_scale_USD = 0.0
    Capex_a_sys_building_scale_USD = 0.0
    Capex_total_sys_building_scale_USD = 0.0
    TAC_sys_building_scale_USD = 0.0
    GHG_sys_building_scale_tonCO2 = 0.0
    HR_sys_building_scale_MWh = 0.0
    SED_sys_building_scale_MWh = 0.0

    # FOR CONNECTED BUILDINGS
    for column in buildings_district_scale_costs.keys():
        if "Capex_total_" in column and "district_scale_USD" in column:
            Capex_total_sys_district_scale_USD += buildings_district_scale_costs[column]
        if "Capex_a_" in column and "district_scale_USD" in column:
            Capex_a_sys_district_scale_USD += buildings_district_scale_costs[column]
            TAC_sys_district_scale_USD += buildings_district_scale_costs[column]
        if "Opex_var_" in column and "district_scale_USD" in column:
            Opex_a_sys_district_scale_USD += buildings_district_scale_costs[column]
            TAC_sys_district_scale_USD += buildings_district_scale_costs[column]
        if "Opex_fixed_" in column and "district_scale_USD" in column:
            Opex_a_sys_district_scale_USD += buildings_district_scale_costs[column]
            TAC_sys_district_scale_USD += buildings_district_scale_costs[column]

    for column in buildings_district_scale_emissions.keys():
        if "GHG_" in column and "district_scale_tonCO2" in column:
            GHG_sys_district_scale_tonCO2 += buildings_district_scale_emissions[column]

    for column in buildings_district_scale_heat.keys():
        if "DC_HR_" in column and "district_scale_Wh" in column:
            HR_sys_district_scale_MWh += 10**(-6) * buildings_district_scale_heat[column]

    for column in buildings_district_scale_sed.keys():
        if "SED_" in column and "district_scale_Wh" in column:
            SED_sys_district_scale_MWh += 10**(-6) * buildings_district_scale_sed[column]

    # FOR DISCONNECTED BUILDINGS
    for column in buildings_building_scale_costs.keys():
        if "Capex_total_" in column and "building_scale_USD" in column:
            Capex_total_sys_building_scale_USD += buildings_building_scale_costs[column]
        if "Capex_a_" in column and "building_scale_USD" in column:
            Capex_a_sys_building_scale_USD += buildings_building_scale_costs[column]
            TAC_sys_building_scale_USD += buildings_building_scale_costs[column]
        if "Opex_var_" in column and "building_scale_USD" in column:
            Opex_a_sys_building_scale_USD += buildings_building_scale_costs[column]
            TAC_sys_building_scale_USD += buildings_building_scale_costs[column]
        if "Opex_fixed_" in column and "building_scale_USD" in column:
            Opex_a_sys_building_scale_USD += buildings_building_scale_costs[column]
            TAC_sys_building_scale_USD += buildings_building_scale_costs[column]

    for column in buildings_building_scale_emissions.keys():
        if "GHG_" in column and "building_scale_tonCO2" in column:
            GHG_sys_building_scale_tonCO2 += buildings_building_scale_emissions[column]

    for column in buildings_building_scale_heat.keys():
        if "DC_HR_" in column and "building_scale_Wh" in column:
            HR_sys_building_scale_MWh += 10**(-6) * buildings_building_scale_heat[column]

    for column in buildings_building_scale_sed.keys():
        if "SED_" in column and "building_scale_Wh" in column:
            SED_sys_building_scale_MWh += 10**(-6) * buildings_building_scale_sed[column]

    Opex_a_sys_USD = Opex_a_sys_district_scale_USD + Opex_a_sys_building_scale_USD
    Capex_a_sys_USD = Capex_a_sys_district_scale_USD + Capex_a_sys_building_scale_USD
    Capex_total_sys_USD = Capex_total_sys_district_scale_USD + Capex_total_sys_building_scale_USD
    TAC_sys_USD = TAC_sys_district_scale_USD + TAC_sys_building_scale_USD
    GHG_sys_tonCO2 = GHG_sys_district_scale_tonCO2 + GHG_sys_building_scale_tonCO2
    HR_sys_MWh = HR_sys_district_scale_MWh + HR_sys_building_scale_MWh
    SED_sys_MWh = SED_sys_district_scale_MWh + SED_sys_building_scale_MWh

    performance_totals = {
        # Total costs (We use all this info to make graphs)

        "Capex_total_sys_USD": Capex_total_sys_USD,
        "Capex_total_sys_district_scale_USD": Capex_total_sys_district_scale_USD,
        "Capex_total_sys_building_scale_USD": Capex_total_sys_building_scale_USD,

        "Capex_a_sys_USD": Capex_a_sys_USD,
        "Capex_a_sys_district_scale_USD": Capex_a_sys_district_scale_USD,
        "Capex_a_sys_building_scale_USD": Capex_a_sys_building_scale_USD,

        "Opex_a_sys_USD": Opex_a_sys_USD,
        "Opex_a_sys_district_scale_USD": Opex_a_sys_district_scale_USD,
        "Opex_a_sys_building_scale_USD": Opex_a_sys_building_scale_USD,

        "TAC_sys_USD": TAC_sys_USD,
        "TAC_sys_district_scale_USD": TAC_sys_district_scale_USD,
        "TAC_sys_building_scale_USD": TAC_sys_building_scale_USD,

        "GHG_sys_tonCO2": GHG_sys_tonCO2,
        "GHG_sys_district_scale_tonCO2": GHG_sys_district_scale_tonCO2,
        "GHG_sys_building_scale_tonCO2": GHG_sys_building_scale_tonCO2,

        "HR_sys_MWh": HR_sys_MWh,
        "HR_sys_district_scale_MWh": HR_sys_district_scale_MWh,
        "HR_sys_building_scale_MWh": HR_sys_building_scale_MWh,

        "SED_sys_MWh": SED_sys_MWh,
        "SED_sys_district_scale_MWh": SED_sys_district_scale_MWh,
        "SED_sys_building_scale_MWh": SED_sys_building_scale_MWh,
    }

    # return objectives and performance totals dict
    TAC_sys_USD = np.float64(TAC_sys_USD)
    GHG_sys_tonCO2 = np.float64(GHG_sys_tonCO2)
    HR_sys_MWh = np.float64(HR_sys_MWh)
    SED_sys_MWh = np.float64(SED_sys_MWh)

    return TAC_sys_USD, GHG_sys_tonCO2, HR_sys_MWh, SED_sys_MWh, performance_totals
