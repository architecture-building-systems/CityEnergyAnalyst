def summarize_results_individual(performance_storage,
                                 performance_heating,
                                 performance_cooling,
                                 performance_disconnected,
                                 performance_fuels,
                                 performance_electricity):
    # TODO:CALCULATE CAPEX TOTAL, OPEX TOTAL and RENEWABLE ERNGY SHARE (to be used in multicriteria.
    # SUMMARIZE TOTALS OF THIS SYSTEM
    Capex_total_sys_connected_USD = Capex_DHN_USD + Capex_SubstationsHeating_USD
    Capex_a_sys_connected_USD = Capex_a_DHN_USD + Capex_a_SubstationsHeating_USD
    Opex_fixed_sys_connected_USD = Opex_fixed_DHN_USD + Opex_fixed_SubstationsHeating_USD

    for column in performance_costs.keys():
        if "Capex_total_" in column and "connected_USD" in column:
            Capex_total_sys_connected_USD += performance_costs[column]
        elif "Capex_a_" in column and "connected_USD" in column:
            Capex_a_sys_connected_USD += performance_costs[column]
        elif "Opex_fixed_" in column and "connected_USD" in column:
            Opex_fixed_sys_connected_USD += performance_costs[column]

    Opex_var_sys_connected_USD = Opex_var_HP_Sewage_USD + Opex_var_HP_Lake_USD + Opex_var_GHP_USD + Opex_var_CHP_BG_USD + \
                                 Opex_var_CHP_NG_USD + Opex_var_Furnace_wet_USD + Opex_var_Furnace_dry_USD + \
                                 Opex_var_BaseBoiler_BG_USD + Opex_var_BaseBoiler_NG_USD + Opex_var_PeakBoiler_BG_USD + \
                                 Opex_var_PeakBoiler_NG_USD + Opex_var_BackupBoiler_BG_USD + Opex_var_BackupBoiler_NG_USD + \
                                 Opex_var_DHN_USD + Opex_var_SubstationsHeating_USD

    Opex_a_sys_connected_USD = Opex_fixed_sys_connected_USD + Opex_var_sys_connected_USD
    TAC_sys_connected_USD = Capex_a_sys_connected_USD + Opex_a_sys_connected_USD

    GHG_sys_connected_USD = 0.0
    PEN_sys_connected_USD = 0.0
    for column in performance_emissions_pen.keys():
        if "GHG_" in column and "connected_tonCO2" in column:
            GHG_sys_connected_USD += performance_emissions_pen[column].values
        elif "PEN_" in column and "connected_MJoil" in column:
            PEN_sys_connected_USD += performance_emissions_pen[column].values

    # totals for this system
    pern ={
    "Capex_total_Heating_sys_connected_USD": [Capex_total_sys_connected_USD],
    "Capex_a_Heating_sys_connected_USD": [Capex_a_sys_connected_USD],
    "Opex_a_Heating_sys_connected_USD": [Opex_a_sys_connected_USD],
    "TAC_Heating_sys_connected_USD": [TAC_sys_connected_USD],
    "GHG_Heating_sys_connected_tonCO2": [GHG_sys_connected_USD],
    "PEN_Heating_sys_connected_MJoil": [PEN_sys_connected_USD],}

    TAC_sys_USD = np.float64(TAC_sys_USD)
    GHG_sys_tonCO2 = np.float64(GHG_sys_tonCO2)
    PEN_sys_MJoil = np.float64(PEN_sys_MJoil)

    return
