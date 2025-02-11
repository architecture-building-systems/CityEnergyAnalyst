
get_building_typology
---------------------

path: ``inputs/building-properties/typology.dbf``

The following file is used by these scripts: ``archetypes_mapper``, ``demand``, ``emissions``


.. csv-table::
    :header: "Variable", "Description"

    ``use_type1``, "First (Main) Use type of the building"
    ``use_type1r``, "Fraction of gross floor area for first Use Type"
    ``use_type2``, "Second Use type of the building"
    ``use_type2r``, "Fraction of gross floor area for second Use Type"
    ``use_type3``, "Third Use type of the building"
    ``use_type3r``, "Fraction of gross floor area for third Use Type"
    ``name``, "Unique building ID. It must start with a letter."
    ``reference``, "Reference to data (if any)"
    ``const_type``, "Construction Standard (relates to ""code"" in Supply Assemblies)"
    ``year``, "Construction year"
    


get_costs_operation_file
------------------------

path: ``outputs/data/costs/operation_costs.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Aocc_m2``, "Occupied floor area (heated/cooled)"
    ``Capex_a_sys_building_scale_USD``, "Annualized capital expenditures of building-scale systems"
    ``Capex_a_sys_district_scale_USD``, "Annualized capital expenditures of district-scale systems"
    ``COAL_hs_cost_m2yr``, "Operation costs of coal due to space heating per unit conditioned floor area"
    ``COAL_hs_cost_yr``, "Operation costs of coal due to space heating"
    ``COAL_ww_cost_m2yr``, "Operation costs of coal due to hotwater per unit conditioned floor area"
    ``COAL_ww_cost_yr``, "Operation costs of coal due to hotwater"
    ``DC_cdata_cost_m2yr``, "Operation costs of district cooling due to data center cooling per unit conditioned floor area"
    ``DC_cdata_cost_yr``, "Operation costs of district cooling due to data center cooling"
    ``DC_cre_cost_m2yr``, "Operation costs of district cooling due to cool room refrigeration per unit conditioned floor area"
    ``DC_cre_cost_yr``, "Operation costs of district cooling due to cool room refrigeration"
    ``DC_cs_cost_m2yr``, "Operation costs of district cooling due to space cooling per unit conditioned floor area"
    ``DC_cs_cost_yr``, "Operation costs of district cooling due to space cooling"
    ``DH_hs_cost_m2yr``, "Operation costs of district heating due to space heating per unit conditioned floor area"
    ``DH_hs_cost_yr``, "Operation costs of district heating due to space heating"
    ``DH_ww_cost_m2yr``, "Operation costs of district heating due to domestic hot water per unit conditioned floor area"
    ``DH_ww_cost_yr``, "Operation costs of district heating due to domestic hot water"
    ``GRID_cost_m2yr``, "Operation costs due to electricity supply from the grid per unit conditioned floor area"
    ``GRID_cost_yr``, "Operation costs due to electricity supply from the grid"
    ``Name``, "Unique building ID. It must start with a letter."
    ``NG_hs_cost_m2yr``, "Operation costs of natural gas due to space heating per unit conditioned floor area"
    ``NG_hs_cost_yr``, "Operation costs of natural gas due to space heating"
    ``NG_ww_cost_m2yr``, "Operation costs of natural gas due to domestic hot water per unit conditioned floor area"
    ``NG_ww_cost_yr``, "Operation costs of natural gas due to domestic hot water"
    ``OIL_hs_cost_m2yr``, "Operation costs of oil due to space heating per unit conditioned floor area"
    ``OIL_hs_cost_yr``, "Operation costs of oil due to space heating"
    ``OIL_ww_cost_m2yr``, "Operation costs of oil due to domestic hot water per unit conditioned floor area"
    ``OIL_ww_cost_yr``, "Operation costs of oil due to domestic hot water"
    ``Opex_a_sys_building_scale_USD``, "Annual operational expenditures of building-scale systems"
    ``Opex_a_sys_district_scale_USD``, "Annual operational expenditures of district-scale systems"
    ``PV_cost_m2yr``, "Operation costs due to electricity supply from PV per unit conditioned floor area"
    ``PV_cost_yr``, "Operation costs due to electricity supply from PV"
    ``SOLAR_hs_cost_m2yr``, "Operation costs due to solar collectors for space heating per unit conditioned floor area"
    ``SOLAR_hs_cost_yr``, "Operation costs due to solar collectors for space heating"
    ``SOLAR_ww_cost_m2yr``, "Operation costs due to solar collectors for domestic hot water per unit conditioned floor area"
    ``SOLAR_ww_cost_yr``, "Operation costs due to solar collectors for domestic hot water"
    ``WOOD_hs_cost_m2yr``, "Operation costs of wood due to space heating per unit conditioned floor area"
    ``WOOD_hs_cost_yr``, "Operation costs of wood due to space heating"
    ``WOOD_ww_cost_m2yr``, "Operation costs of wood due to domestic hot water per unit conditioned floor area"
    ``WOOD_ww_cost_yr``, "Operation costs of wood due to domestic hot water"
    


get_demand_results_file
-----------------------

path: ``outputs/data/demand/B001.csv``

The following file is used by these scripts: ``decentralized``, ``optimization``, ``sewage_potential``, ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``COAL_hs_kWh``, "Coal requirement for space heating supply"
    ``COAL_ww_kWh``, "Coal requirement for hotwater supply"
    ``DATE``, "Time stamp for each day of the year ascending in hour intervals."
    ``DC_cdata_kWh``, "District cooling for data center cooling demand"
    ``DC_cre_kWh``, "District cooling for refrigeration demand"
    ``DC_cs_kWh``, "Energy consumption of space cooling system (if supplied by District Cooling), DC_cs = Qcs_sys / eff_cs"
    ``DH_hs_kWh``, "Energy requirement by district heating (space heating supply)"
    ``DH_ww_kWh``, "Energy requirement by district heating (hotwater supply)"
    ``E_cdata_kWh``, "Data centre cooling specific electricity consumption."
    ``E_cre_kWh``, "Refrigeration system electricity consumption."
    ``E_cs_kWh``, "Energy consumption of cooling system (if supplied by electricity grid), E_cs = Qcs_sys / eff_cs"
    ``E_hs_kWh``, "Heating system electricity consumption."
    ``E_sys_kWh``, "End-use total electricity consumption  = Ea + El + Edata + Epro + Eaux + Ev + Eve"
    ``E_ww_kWh``, "Hot water system electricity consumption."
    ``Ea_kWh``, "End-use electricity for appliances"
    ``Eal_kWh``, "End-use electricity consumption of appliances and lighting, Eal = El_W + Ea_W"
    ``Eaux_kWh``, "End-use auxiliary electricity consumption, Eaux = Eaux_fw + Eaux_ww + Eaux_cs + Eaux_hs + Ehs_lat_aux"
    ``Edata_kWh``, "End-use data centre electricity consumption."
    ``El_kWh``, "End-use electricity for lights"
    ``Epro_kWh``, "End-use electricity consumption for industrial processes."
    ``Ev_kWh``, "End-use electricity for electric vehicles"
    ``Eve_kWh``, "End-use electricity for ventilation"
    ``GRID_a_kWh``, "Grid electricity consumption for appliances"
    ``GRID_aux_kWh``, "Grid electricity consumption for auxiliary loads"
    ``GRID_cdata_kWh``, "Grid electricity consumption for servers cooling"
    ``GRID_cre_kWh``, "Grid electricity consumption for refrigeration"
    ``GRID_cs_kWh``, "Grid electricity consumption for space cooling"
    ``GRID_data_kWh``, "Grid electricity consumption for servers"
    ``GRID_hs_kWh``, "Grid electricity consumption for space heating"
    ``GRID_kWh``, "Grid total electricity consumption, GRID_a + GRID_l + GRID_v + GRID_ve + GRID_data + GRID_pro + GRID_aux + GRID_ww + GRID_cs + GRID_hs + GRID_cdata + GRID_cre"
    ``GRID_l_kWh``, "Grid electricity consumption for lighting"
    ``GRID_pro_kWh``, "Grid electricity consumption for industrial processes"
    ``GRID_ve_kWh``, "Grid electricity consumption for ventilation"
    ``GRID_ww_kWh``, "Grid electricity consumption for hot water supply"
    ``I_rad_kWh``, "Radiative heat loss"
    ``I_sol_and_I_rad_kWh``, "Net radiative heat gain"
    ``I_sol_kWh``, "Solar heat gain"
    ``mcpcdata_sys_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of the chilled water delivered to data centre."
    ``mcpcre_sys_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to refrigeration."
    ``mcpcs_sys_ahu_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to air handling units (space cooling)."
    ``mcpcs_sys_aru_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to air recirculation units (space cooling)."
    ``mcpcs_sys_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to space cooling."
    ``mcpcs_sys_scu_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the chilled water delivered to sensible cooling units (space cooling)."
    ``mcphs_sys_ahu_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to air handling units (space heating)."
    ``mcphs_sys_aru_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to air recirculation units (space heating)."
    ``mcphs_sys_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to space heating."
    ``mcphs_sys_shu_kWperC``, "Capacity flow rate (mass flow* specific heat Capacity) of the warm water delivered to sensible heating units (space heating)."
    ``mcptw_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of the fresh water"
    ``mcpww_sys_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of domestic hot water"
    ``Name``, "Unique building ID. It must start with a letter."
    ``NG_hs_kWh``, "NG requirement for space heating supply"
    ``NG_ww_kWh``, "NG requirement for hotwater supply"
    ``OIL_hs_kWh``, "OIL requirement for space heating supply"
    ``OIL_ww_kWh``, "OIL requirement for hotwater supply"
    ``people``, "Predicted occupancy: number of people in building"
    ``PV_kWh``, "PV electricity consumption"
    ``Q_gain_lat_peop_kWh``, "Latent heat gain from people"
    ``Q_gain_sen_app_kWh``, "Sensible heat gain from appliances"
    ``Q_gain_sen_base_kWh``, "Sensible heat gain from transmission through the base"
    ``Q_gain_sen_data_kWh``, "Sensible heat gain from data centres"
    ``Q_gain_sen_light_kWh``, "Sensible heat gain from lighting"
    ``Q_gain_sen_peop_kWh``, "Sensible heat gain from people"
    ``Q_gain_sen_pro_kWh``, "Sensible heat gain from industrial processes."
    ``Q_gain_sen_roof_kWh``, "Sensible heat gain from transmission through the roof"
    ``Q_gain_sen_vent_kWh``, "Sensible heat gain from ventilation and infiltration"
    ``Q_gain_sen_wall_kWh``, "Sensible heat gain from transmission through the walls"
    ``Q_gain_sen_wind_kWh``, "Sensible heat gain from transmission through the windows"
    ``Q_loss_sen_ref_kWh``, "Sensible heat loss from refrigeration systems"
    ``QC_sys_kWh``, "Total energy demand for cooling, QC_sys = Qcs_sys + Qcdata_sys + Qcre_sys + Qcpro_sys"
    ``Qcdata_kWh``, "Data centre space cooling demand"
    ``Qcdata_sys_kWh``, "End-use data center cooling demand"
    ``Qcpro_sys_kWh``, "Process cooling demand"
    ``Qcre_kWh``, "Refrigeration space cooling demand"
    ``Qcre_sys_kWh``, "End-use refrigeration demand"
    ``Qcs_dis_ls_kWh``, "Cooling system distribution losses"
    ``Qcs_em_ls_kWh``, "Cooling system emission losses"
    ``Qcs_kWh``, "Specific cooling demand"
    ``Qcs_lat_ahu_kWh``, "AHU latent cooling demand"
    ``Qcs_lat_aru_kWh``, "ARU latent cooling demand"
    ``Qcs_lat_sys_kWh``, "Total latent cooling demand for all systems"
    ``Qcs_sen_ahu_kWh``, "AHU sensible cooling demand"
    ``Qcs_sen_aru_kWh``, "ARU sensible cooling demand"
    ``Qcs_sen_scu_kWh``, "SHU sensible cooling demand"
    ``Qcs_sen_sys_kWh``, "Total sensible cooling demand for all systems"
    ``Qcs_sys_ahu_kWh``, "AHU system cooling demand"
    ``Qcs_sys_aru_kWh``, "ARU system cooling demand"
    ``Qcs_sys_kWh``, "End-use space cooling demand, Qcs_sys = Qcs_sen_sys + Qcs_lat_sys + Qcs_em_ls + Qcs_dis_ls"
    ``Qcs_sys_scu_kWh``, "SCU system cooling demand"
    ``QH_sys_kWh``, "Total energy demand for heating, QH_sys = Qww_sys + Qhs_sys + Qhpro_sys"
    ``Qhpro_sys_kWh``, "Process heating demand"
    ``Qhs_dis_ls_kWh``, "Heating system distribution losses"
    ``Qhs_em_ls_kWh``, "Heating system emission losses"
    ``Qhs_kWh``, "Sensible heating system demand"
    ``Qhs_lat_ahu_kWh``, "AHU latent heating demand"
    ``Qhs_lat_aru_kWh``, "ARU latent heating demand"
    ``Qhs_lat_sys_kWh``, "Total latent heating demand for all systems"
    ``Qhs_sen_ahu_kWh``, "AHU sensible heating demand"
    ``Qhs_sen_aru_kWh``, "ARU sensible heating demand"
    ``Qhs_sen_shu_kWh``, "SHU sensible heating demand"
    ``Qhs_sen_sys_kWh``, "Total sensible heating demand"
    ``Qhs_sys_ahu_kWh``, "Space heating demand in AHU"
    ``Qhs_sys_aru_kWh``, "Space heating demand in ARU"
    ``Qhs_sys_kWh``, "End-use space heating demand, Qhs_sys = Qhs_sen_sys + Qhs_em_ls + Qhs_dis_ls"
    ``Qhs_sys_shu_kWh``, "SHU system heating demand"
    ``Qww_kWh``, "DHW specific heating demand"
    ``Qww_sys_kWh``, "End-use hotwater demand"
    ``SOLAR_hs_kWh``, "Solar thermal energy requirement for space heating supply"
    ``SOLAR_ww_kWh``, "Solar thermal energy requirement for hotwater supply"
    ``T_ext_C``, "Outdoor temperature"
    ``T_int_C``, "Indoor temperature"
    ``Tcdata_sys_re_C``, "Cooling supply temperature of the data centre"
    ``Tcdata_sys_sup_C``, "Cooling return temperature of the data centre"
    ``Tcre_sys_re_C``, "Cooling return temperature of the refrigeration system."
    ``Tcre_sys_sup_C``, "Cooling supply temperature of the refrigeration system."
    ``Tcs_sys_re_ahu_C``, "Return temperature cooling system"
    ``Tcs_sys_re_aru_C``, "Return temperature cooling system"
    ``Tcs_sys_re_C``, "System cooling return temperature."
    ``Tcs_sys_re_scu_C``, "Return temperature cooling system"
    ``Tcs_sys_sup_ahu_C``, "Supply temperature cooling system"
    ``Tcs_sys_sup_aru_C``, "Supply temperature cooling system"
    ``Tcs_sys_sup_C``, "System cooling supply temperature."
    ``Tcs_sys_sup_scu_C``, "Supply temperature cooling system"
    ``theta_o_C``, "Operative temperature in building (RC-model) used for comfort plotting"
    ``Ths_sys_re_ahu_C``, "Return temperature heating system"
    ``Ths_sys_re_aru_C``, "Return temperature heating system"
    ``Ths_sys_re_C``, "Heating system return temperature."
    ``Ths_sys_re_shu_C``, "Return temperature heating system"
    ``Ths_sys_sup_ahu_C``, "Supply temperature heating system"
    ``Ths_sys_sup_aru_C``, "Supply temperature heating system"
    ``Ths_sys_sup_C``, "Heating system supply temperature."
    ``Ths_sys_sup_shu_C``, "Supply temperature heating system"
    ``Tww_sys_re_C``, "Return temperature hotwater system"
    ``Tww_sys_sup_C``, "Supply temperature hotwater system"
    ``WOOD_hs_kWh``, "WOOD requirement for space heating supply"
    ``WOOD_ww_kWh``, "WOOD requirement for hotwater supply"
    ``x_int``, "Internal mass fraction of humidity (water/dry air)"
    


get_geothermal_potential
------------------------

path: ``outputs/data/potentials/Shallow_geothermal_potential.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Area_avail_m2``, "areas available to install ground source heat pumps"
    ``QGHP_kW``, "geothermal heat potential"
    ``Ts_C``, "ground temperature"
    


get_lca_embodied
----------------

path: ``outputs/data/emissions/Total_LCA_embodied.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``GFA_m2``, "Gross floor area"
    ``GHG_sys_embodied_kgCO2m2``, "Embodied emissions per conditioned floor area due to building construction and decommissioning"
    ``GHG_sys_embodied_tonCO2``, "Embodied emissions due to building construction and decommissioning"
    ``Name``, "Unique building ID. It must start with a letter."
    


get_lca_mobility
----------------

path: ``outputs/data/emissions/Total_LCA_mobility.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``GFA_m2``, "Gross floor area"
    ``GHG_sys_mobility_kgCO2m2``, "Operational emissions per unit of conditioned floor area due to mobility"
    ``GHG_sys_mobility_tonCO2``, "Operational emissions due to mobility"
    ``Name``, "Unique building ID. It must start with a letter."
    


get_lca_operation
-----------------

path: ``outputs/data/emissions/Total_LCA_operation.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``COAL_hs_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the coal powererd heating system"
    ``COAL_hs_ghg_ton``, "Operational emissions of the coal powered heating system"
    ``COAL_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for coal powered heating system"
    ``COAL_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the coal powered heating system"
    ``COAL_ww_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the coal powered domestic hot water system"
    ``COAL_ww_ghg_ton``, "Operational emissions of the coal powered domestic hot water system"
    ``COAL_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for coal powered domestic hot water system"
    ``COAL_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the coal powered domestic hot water system"
    ``DC_cdata_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the district cooling for the data center"
    ``DC_cdata_ghg_ton``, "Operational emissions of the district cooling for the data center"
    ``DC_cdata_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district cooling system for cool room refrigeration"
    ``DC_cdata_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) for district cooling for cool room refrigeration"
    ``DC_cre_ghg_kgm2``, "Operational emissions per unit of conditioned floor area for district cooling system for cool room refrigeration"
    ``DC_cre_ghg_ton``, "Operational emissions for district cooling system for cool room refrigeration"
    ``DC_cre_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district cooling system for cool room refrigeration"
    ``DC_cre_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable)  for cool room refrigeration"
    ``DC_cs_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the district cooling"
    ``DC_cs_ghg_ton``, "Operational emissions of the district cooling"
    ``DC_cs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district cooling system"
    ``DC_cs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the district cooling"
    ``DH_hs_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the district heating system"
    ``DH_hs_ghg_ton``, "Operational emissions of the district heating system"
    ``DH_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district heating system"
    ``DH_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the district heating system"
    ``DH_ww_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the district heating domestic hot water system"
    ``DH_ww_ghg_ton``, "Operational emissions of the district heating powered domestic hot water system"
    ``DH_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for district heating powered domestic hot water system"
    ``DH_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the district heating domestic hot water system"
    ``GFA_m2``, "Gross floor area"
    ``GHG_sys_kgCO2m2``, "Total operational emissions per unit of conditioned floor area"
    ``GHG_sys_tonCO2``, "Total operational emissions"
    ``GRID_ghg_kgm2``, "Operational emissions per unit of conditioned floor area from grid electricity"
    ``GRID_ghg_ton``, "Operational emissions of the electrictiy from the grid"
    ``GRID_nre_pen_GJ``, "Operational primary energy demand (non-renewable) from the grid"
    ``GRID_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) from grid electricity"
    ``Name``, "Unique building ID. It must start with a letter."
    ``NG_hs_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the natural gas powered heating system"
    ``NG_hs_ghg_ton``, "Operational emissions of the natural gas powered heating system"
    ``NG_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for natural gas powered heating system"
    ``NG_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the natural gas powered heating system"
    ``NG_ww_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the gas powered domestic hot water system"
    ``NG_ww_ghg_ton``, "Operational emissions of the solar powered domestic hot water system"
    ``NG_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for natural gas powered domestic hot water system"
    ``NG_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the natural gas powered domestic hot water system"
    ``OIL_hs_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the oil powered heating system"
    ``OIL_hs_ghg_ton``, "Operational emissions of the oil powered heating system"
    ``OIL_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for oil powered heating system"
    ``OIL_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the oil powered heating system"
    ``OIL_ww_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the oil powered domestic hot water system"
    ``OIL_ww_ghg_ton``, "Operational emissions of the oil powered domestic hot water system"
    ``OIL_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for oil powered domestic hot water system"
    ``OIL_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the oil powered domestic hot water system"
    ``PV_ghg_kgm2``, "Operational emissions per unit of conditioned floor area for PV-System"
    ``PV_ghg_ton``, "Operational emissions of the PV-System"
    ``PV_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for PV-System"
    ``PV_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) for PV System"
    ``SOLAR_hs_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the solar powered heating system"
    ``SOLAR_hs_ghg_ton``, "Operational emissions of the solar powered heating system"
    ``SOLAR_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) of the solar powered heating system"
    ``SOLAR_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the solar powered heating system"
    ``SOLAR_ww_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the solar powered domestic hot water system"
    ``SOLAR_ww_ghg_ton``, "Operational emissions of the solar powered domestic hot water system"
    ``SOLAR_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for solar powered domestic hot water system"
    ``SOLAR_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the solar poweed domestic hot water system"
    ``WOOD_hs_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the wood powered heating system"
    ``WOOD_hs_ghg_ton``, "Operational emissions of the wood powered heating system"
    ``WOOD_hs_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for wood powered heating system"
    ``WOOD_hs_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the wood powered heating system"
    ``WOOD_ww_ghg_kgm2``, "Operational emissions per unit of conditioned floor area of the wood powered domestic hot water system"
    ``WOOD_ww_ghg_ton``, "Operational emissions of the wood powered domestic hot water system"
    ``WOOD_ww_nre_pen_GJ``, "Operational primary energy demand (non-renewable) for wood powered domestic hot water system"
    ``WOOD_ww_nre_pen_MJm2``, "Operational primary energy demand per unit of conditioned floor area (non-renewable) of the wood powered domestic hot water system"
    


get_multi_criteria_analysis
---------------------------

path: ``outputs/data/multicriteria/gen_2_multi_criteria_analysis.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_sys_building_scale_USD``, "Annualized Capital costs of building-scale systems"
    ``Capex_a_sys_district_scale_USD``, "Capital costs of district-scale systems"
    ``Capex_a_sys_USD``, "Capital costs of all systems"
    ``Capex_total_sys_building_scale_USD``, "Capital costs of building-scale systems"
    ``Capex_total_sys_district_scale_USD``, "Capital costs of district-scale systems"
    ``Capex_total_sys_USD``, "Capital costs of all systems"
    ``generation``, "Generation or iteration"
    ``GHG_rank``, "Rank for emissions"
    ``GHG_sys_building_scale_tonCO2``, "Green house gas emissions of building-scale systems"
    ``GHG_sys_district_scale_tonCO2``, "Green house gas emissions of building-scale systems"
    ``GHG_sys_tonCO2``, "Green house gas emissions of all systems"
    ``individual``, "system number"
    ``individual_name``, "Name of system"
    ``normalized_Capex_total``, "normalization of CAPEX"
    ``normalized_emissions``, "normalization of GHG"
    ``normalized_Opex``, "Normalization of OPEX"
    ``normalized_TAC``, "normalization of TAC"
    ``Opex_a_sys_building_scale_USD``, "Operational costs of building-scale systems"
    ``Opex_a_sys_district_scale_USD``, "Operational costs of district-scale systems"
    ``Opex_a_sys_USD``, "Operational costs of all systems"
    ``TAC_rank``, "Rank of TAC"
    ``TAC_sys_building_scale_USD``, "Equivalent annual costs of building-scale systems"
    ``TAC_sys_district_scale_USD``, "Equivalent annual of district-scale systems"
    ``TAC_sys_USD``, "Equivalent annual costs of all systems"
    ``user_MCDA``, "Best system according to user multi-criteria weights"
    ``user_MCDA_rank``, "Rank of Best system according to user mult-criteria weights"
    


get_network_energy_pumping_requirements_file
--------------------------------------------

path: ``outputs/data/thermal-network/DH__plant_pumping_load_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``pressure_loss_return_kW``, "pumping electricity required to overcome pressure losses in the return network"
    ``pressure_loss_substations_kW``, "pumping electricity required to overcome pressure losses in the substations"
    ``pressure_loss_supply_kW``, "pumping electricity required to overcome pressure losses in the supply network"
    ``pressure_loss_total_kW``, "pumping electricity required to overcome pressure losses in the entire network"
    


get_network_layout_edges_shapefile
----------------------------------

path: ``outputs/data/thermal-network/DH/edges.shp``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``geometry``, "Geometry"
    ``length_m``, "length of this edge"
    ``name``, "Unique network pipe ID."
    ``pipe_DN``, "Classifies nominal pipe diameters (DN) into typical bins."
    ``type_mat``, "Material type"
    


get_network_layout_nodes_shapefile
----------------------------------

path: ``outputs/data/thermal-network/DH/nodes.shp``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``building``, "Unique building ID. e.g. ""B01"""
    ``geometry``, "Geometry"
    ``name``, "Unique node ID. e.g. ""NODE1"""
    ``type``, "Type of node."
    


get_network_linear_pressure_drop_edges
--------------------------------------

path: ``outputs/data/thermal-network/DH__linear_pressure_drop_edges_Paperm.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "linear pressure drop in this pipe section"
    


get_network_linear_thermal_loss_edges_file
------------------------------------------

path: ``outputs/data/thermal-network/DH__linear_thermal_loss_edges_Wperm.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "linear thermal losses in this pipe section"
    


get_network_pressure_at_nodes
-----------------------------

path: ``outputs/data/thermal-network/DH__pressure_at_nodes_Pa.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "pressure at this node"
    


get_network_temperature_plant
-----------------------------

path: ``outputs/data/thermal-network/DH__temperature_plant_K.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``temperature_return_K``, "Plant return temperature at each time step"
    ``temperature_supply_K``, "Plant supply temperature at each time step"
    


get_network_temperature_return_nodes_file
-----------------------------------------

path: ``outputs/data/thermal-network/DH__temperature_return_nodes_K.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "Return temperature at node NODE0 (outlet temperature of NODE0) at each time step"
    


get_network_temperature_supply_nodes_file
-----------------------------------------

path: ``outputs/data/thermal-network/DH__temperature_supply_nodes_K.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "Supply temperature at node NODE0 (inlet temperature of NODE0) at each time step"
    


get_network_thermal_loss_edges_file
-----------------------------------

path: ``outputs/data/thermal-network/DH__thermal_loss_edges_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "Thermal losses along pipe PIPE0 at each time step"
    


get_network_total_pressure_drop_file
------------------------------------

path: ``outputs/data/thermal-network/DH__plant_pumping_pressure_loss_Pa.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``pressure_loss_return_Pa``, "Pressure losses in the return network at each time step"
    ``pressure_loss_substations_Pa``, "Pressure losses in all substations at each time step"
    ``pressure_loss_supply_Pa``, "Pressure losses in the supply network at each time step"
    ``pressure_loss_total_Pa``, "Total pressure losses in the entire thermal network at each time step"
    


get_network_total_thermal_loss_file
-----------------------------------

path: ``outputs/data/thermal-network/DH__total_thermal_loss_edges_kW.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``thermal_loss_return_kW``, "Thermal losses in the supply network at each time step"
    ``thermal_loss_supply_kW``, "Thermal losses in the return network at each time step"
    ``thermal_loss_total_kW``, "Thermal losses in the entire thermal network at each time step"
    


get_nominal_edge_mass_flow_csv_file
-----------------------------------

path: ``outputs/data/thermal-network/Nominal_EdgeMassFlow_at_design_{network_type}__kgpers.csv``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "Mass flow rate in pipe PIPE0 at design operating conditions"
    


get_nominal_node_mass_flow_csv_file
-----------------------------------

path: ``outputs/data/thermal-network/Nominal_NodeMassFlow_at_design_{network_type}__kgpers.csv``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "Mass flow rate in node NODE0 at design operating conditions"
    


get_optimization_building_scale_cooling_capacity
------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_0_building_scale_cooling_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_ACH_SC_FP_cool_building_scale_W``, "Thermal Capacity of Absorption Chiller and Solar Collector (Flat Plate) for Decentralized Building"
    ``Capacity_ACHHT_FP_cool_building_scale_W``, "Thermal Capacity of High-Temperature Absorption Chiller and Solar Collector (Flat Plate) for Decentralized Building"
    ``Capacity_BaseVCC_AS_cool_building_scale_W``, "Thermal Capacity of Base load Vapor Compression Chiller for Decentralized Building"
    ``Capacity_DX_AS_cool_building_scale_W``, "Thermal Capacity of Direct Expansion Air-Source for Decentralized Building"
    ``Capacity_VCCHT_AS_cool_building_scale_W``, "Thermal Capacity of High-Temperature Vapor Compression Chiller (Air-Source) for Decentralized Building"
    ``Capaticy_ACH_SC_ET_cool_building_scale_W``, "Thermal Capacity of Absorption Chiller and Solar Collector (Evacuated Tube)for Decentralized Building"
    ``Name``, "Unique building ID. It must start with a letter"
    


get_optimization_building_scale_heating_capacity
------------------------------------------------

path: ``outputs/data/optimization/slave/gen_0/ind_1_building_scale_heating_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_BaseBoiler_NG_heat_building_scale_W``, "Thermal capacity of Base load boiler for Decentralized building"
    ``Capacity_FC_NG_heat_building_scale_W``, "Thermal capacity of Fuel Cell for Decentralized building"
    ``Capacity_GS_HP_heat_building_scale_W``, "Thermal capacity of ground-source heat pump for Decentralized building"
    ``Name``, "Unique building ID. It must start with a letter"
    


get_optimization_checkpoint
---------------------------

path: ``outputs/data/optimization/master/CheckPoint_1``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``difference_generational_distances``, "TODO"
    ``generation``, "TODO"
    ``generational_distances``, "TODO"
    ``selected_population``, "TODO"
    ``tested_population``, "TODO"
    


get_optimization_decentralized_folder_building_result_cooling
-------------------------------------------------------------

path: ``outputs/data/optimization/decentralized/{building}_{configuration}_cooling.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Best configuration``, "Index of best configuration simulated"
    ``Capacity_ACH_SC_FP_W``, "Thermal Capacity of Absorption Chiller connected to Flat-plate Solar Collector"
    ``Capacity_ACHHT_FP_W``, "Thermal Capacity of High Temperature Absorption Chiller connected to Solar Collector (flat Plate)"
    ``Capacity_BaseVCC_AS_W``, "Thermal Capacity of Base Vapor compression chiller (air-source)"
    ``Capacity_DX_AS_W``, "Thermal Capacity of Direct-Expansion Unit Air-source"
    ``Capacity_VCCHT_AS_W``, "Thermal Capacity of High Temperature Vapor compression chiller (air-source)"
    ``Capaticy_ACH_SC_ET_W``, "Thermal Capacity of Absorption Chiller connected to Evacuated-Tube Solar Collector"
    ``Capex_a_USD``, "Annualized Capital Costs"
    ``Capex_total_USD``, "Total Capital Costs"
    ``GHG_tonCO2``, "Annual Green House Gas Emissions"
    ``Nominal heating load``, "Nominal heat load"
    ``Opex_fixed_USD``, "Fixed Annual Operational Costs"
    ``Opex_var_USD``, "Variable Annual Operational Costs"
    ``TAC_USD``, "Total Annualized Costs"
    


get_optimization_decentralized_folder_building_result_cooling_activation
------------------------------------------------------------------------

path: ``outputs/data/optimization/decentralized/{building}_{configuration}_cooling_activation.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``E_ACH_req_W``, "Electricity requirements of Absorption Chillers"
    ``E_BaseVCC_AS_req_W``, "Electricity requirements of Vapor Compression Chillers and refrigeration"
    ``E_cs_cre_cdata_req_W``, "Electricity requirements due to space cooling, servers cooling and refrigeration"
    ``E_CT_req_W``, "Electricity requirements of Cooling Towers"
    ``E_DX_AS_req_W``, "Electricity requirements of Air-Source direct expansion chillers"
    ``E_SC_ET_req_W``, "Electricity requirements of Solar Collectors (evacuated-tubes)"
    ``E_SC_FP_req_W``, "Electricity requirements of Solar Collectors (flat-plate)"
    ``NG_Boiler_req``, "Requirements of Natural Gas for Boilers"
    ``NG_Burner_req``, "Requirements of Natural Gas for Burners"
    ``Q_ACH_gen_directload_W``, "Thermal energy generated by Absorption chillers"
    ``Q_BaseVCC_AS_gen_directload_W``, "Thermal energy generated by Air-Source Vapor-compression chillers"
    ``Q_Boiler_NG_ACH_W``, "Thermal energy generated by Natural gas Boilers to Absorption chillers"
    ``Q_Burner_NG_ACH_W``, "Thermal energy generated by Natural gas Burners to Absorption chillers"
    ``Q_DX_AS_gen_directload_W``, "Thermal energy generated by Air-Source direct expansion chillers"
    ``Q_SC_ET_ACH_W``, "Thermal energy generated by Solar Collectors (evacuated-tubes) to Absorption chillers"
    ``Q_SC_FP_ACH_W``, "Thermal energy generated by Solar Collectors (flat-plate) to Absorption chillers"
    


get_optimization_decentralized_folder_building_result_heating
-------------------------------------------------------------

path: ``outputs/data/optimization/decentralized/DiscOp_B001_result_heating.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Best configuration``, "Index of best configuration simulated"
    ``Capacity_BaseBoiler_NG_W``, "Thermal capacity of Baseload Boiler NG"
    ``Capacity_FC_NG_W``, "Thermal Capacity of Fuel Cell NG"
    ``Capacity_GS_HP_W``, "Thermal Capacity of Ground Source Heat Pump"
    ``Capex_a_USD``, "Annualized Capital Costs"
    ``Capex_total_USD``, "Total Capital Costs"
    ``GHG_tonCO2``, "Annual Green House Gas Emissions"
    ``Nominal heating load``, "Nominal heat load"
    ``Opex_fixed_USD``, "Fixed Annual Operational Costs"
    ``Opex_var_USD``, "Variable Annual Operational Costs"
    ``TAC_USD``, "Total Annualized Costs"
    


get_optimization_decentralized_folder_building_result_heating_activation
------------------------------------------------------------------------

path: ``outputs/data/optimization/decentralized/DiscOp_B001_result_heating_activation.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``BackupBoiler_Status``, "Status of the BackupBoiler (1=on, 0 =off)"
    ``BG_Boiler_req_W``, "Requirements of Bio-gas for Base load Boiler"
    ``Boiler_Status``, "Status of the Base load Boiler (1=on, 0 =off)"
    ``E_Fuelcell_gen_export_W``, "Electricity generation of fuel cell exported to the grid"
    ``E_hs_ww_req_W``, "Electricity Requirements for heat pump compressor and auxiliary uses (if required)"
    ``Fuelcell_Status``, "Status of the fuel cell (1=on, 0 =off)"
    ``GHP_Status``, "Status of the ground-source heat pump (1=on, 0 =off)"
    ``NG_BackupBoiler_req_W``, "Requirements of Natural Gas for Back-up Boiler"
    ``NG_Boiler_req_W``, "Requirements of Natural Gas for Base load Boiler"
    ``NG_FuelCell_req_W``, "Requirements of Natural Gas for fuel cell"
    ``Q_BackupBoiler_gen_directload_W``, "Thermal generation of Back-up Boiler to direct load"
    ``Q_Boiler_gen_directload_W``, "Thermal generation of Base load Boiler to direct load"
    ``Q_Fuelcell_gen_directload_W``, "Thermal generation of fuel cell to direct load"
    ``Q_GHP_gen_directload_W``, "Thermal generation of ground-source heat pump to direct load"
    


get_optimization_district_scale_cooling_capacity
------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_1_district_scale_cooling_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_ACH_SC_FP_cool_building_scale_W``, "Thermal Capacity of Absorption Chiller and Solar Collector (Flat Plate) for Decentralized Building"
    ``Capacity_ACHHT_FP_cool_building_scale_W``, "Thermal Capacity of High-Temperature Absorption Chiller and Solar Collector (Flat Plate) for Decentralized Building"
    ``Capacity_BaseVCC_AS_cool_building_scale_W``, "Thermal Capacity of Base load Vapor Compression Chiller for Decentralized Building"
    ``Capacity_DX_AS_cool_building_scale_W``, "Thermal Capacity of Direct Expansion Air-Source for Decentralized Building"
    ``Capacity_VCCHT_AS_cool_building_scale_W``, "Thermal Capacity of High-Temperature Vapor Compression Chiller (Air-Source) for Decentralized Building"
    ``Capaticy_ACH_SC_ET_cool_building_scale_W``, "Thermal Capacity of Absorption Chiller and Solar Collector (Evacuated Tube)for Decentralized Building"
    ``Name``, "Unique building ID. It must start with a letter"
    


get_optimization_district_scale_electricity_capacity
----------------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/ind_0_district_scale_electrical_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_GRID_el_district_scale_W``, "Electrical Capacity Required from the local Grid"
    ``Capacity_PV_el_district_scale_m2``, "Area Coverage of PV in central Plant"
    ``Capacity_PV_el_district_scale_W``, "Electrical Capacity of PV in central Plant"
    


get_optimization_district_scale_heating_capacity
------------------------------------------------

path: ``outputs/data/optimization/slave/gen_0/ind_2_district_scale_heating_capacity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_BackupBoiler_NG_heat_district_scale_W``, "Thermal Capacity of Back-up Boiler - Natural Gas in central plant"
    ``Capacity_BaseBoiler_NG_heat_district_scale_W``, "Thermal Capacity of Base Load Boiler - Natural Gas  in central plant"
    ``Capacity_CHP_DB_el_district_scale_W``, "Electrical Capacity of CHP Dry-Biomass in central plant"
    ``Capacity_CHP_DB_heat_district_scale_W``, "ThermalCapacity of CHP Dry-Biomass in central plant"
    ``Capacity_CHP_NG_el_district_scale_W``, "Electrical Capacity of CHP Natural-Gas in central plant"
    ``Capacity_CHP_NG_heat_district_scale_W``, "Thermal Capacity of CHP Natural-Gas in central plant"
    ``Capacity_CHP_WB_el_district_scale_W``, "Electrical Capacity of CHP Wet-Biomass in central plant"
    ``Capacity_CHP_WB_heat_district_scale_W``, "Thermal Capacity of CHP Wet-Biomass in central plant"
    ``Capacity_HP_DS_heat_district_scale_W``, "Thermal Capacity of Heat Pump Server-Source in central plant"
    ``Capacity_HP_GS_heat_district_scale_W``, "Thermal Capacity of Heat Pump Ground-Source in central plant"
    ``Capacity_HP_SS_heat_district_scale_W``, "Thermal Capacity of Heat Pump Sewage-Source in central plant"
    ``Capacity_HP_WS_heat_district_scale_W``, "Thermal Capacity of Heat Pump Water-Source in central plant"
    ``Capacity_PeakBoiler_NG_heat_district_scale_W``, "Thermal Capacity of Peak Boiler - Natural Gas in central plant"
    ``Capacity_PVT_el_district_scale_W``, "Electrical Capacity of PVT Field in central plant"
    ``Capacity_PVT_heat_district_scale_W``, "Thermal Capacity of PVT panels in central plant"
    ``Capacity_SC_ET_heat_district_scale_W``, "Thermal Capacity of Solar Collectors (Evacuated-tube) in central plant"
    ``Capacity_SC_FP_heat_district_scale_W``, "Thermal Capacity of Solar Collectors (Flat-plate) in central plant"
    ``Capacity_SeasonalStorage_WS_heat_district_scale_W``, "Thermal Capacity of Seasonal Thermal Storage in central plant"
    


get_optimization_generation_building_scale_performance
------------------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/gen_2_building_scale_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_cooling_building_scale_USD``, "Annualized Capital Costs of building-scale systems due to cooling"
    ``Capex_a_heating_building_scale_USD``, "Annualized Capital Costs of building-scale systems due to heating"
    ``Capex_total_cooling_building_scale_USD``, "Total Capital Costs of building-scale systems due to cooling"
    ``Capex_total_heating_building_scale_USD``, "Total Capital Costs of building-scale systems due to heating"
    ``generation``, "No. Generation or Iteration (genetic Algorithm)"
    ``GHG_cooling_building_scale_tonCO2``, "Green House Gas Emissions of building-scale systems due to Cooling"
    ``GHG_heating_building_scale_tonCO2``, "Green House Gas Emissions of building-scale systems due to Heating"
    ``individual``, "No. Individual unique ID"
    ``individual_name``, "Name of  Individual unique ID"
    ``Opex_fixed_cooling_building_scale_USD``, "Fixed Operational Costs of building-scale systems due to cooling"
    ``Opex_fixed_heating_building_scale_USD``, "Fixed Operational Costs of building-scale systems due to heating"
    ``Opex_var_cooling_building_scale_USD``, "Variable Operational Costs of building-scale systems due to cooling"
    ``Opex_var_heating_building_scale_USD``, "Variable Operational Costs of building-scale systems due to heating"
    


get_optimization_generation_district_scale_performance
------------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/gen_1_district_scale_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_BackupBoiler_NG_district_scale_USD``, "Annualized Capital Costs of Back-up Boiler Natural Gas in Central Plant"
    ``Capex_a_BaseBoiler_NG_district_scale_USD``, "Annualized Capital Costs of Base Load Boiler Boiler Natural Gas in Central Plant"
    ``Capex_a_CHP_NG_district_scale_USD``, "Annualized Capital Costs of CHP Natural Gas in Central Plant"
    ``Capex_a_DHN_district_scale_USD``, "Annualized Capital Costs of District Heating Network"
    ``Capex_a_Furnace_dry_district_scale_USD``, "Annualized Capital Costs of CHP Dry-Biomass in Central Plant"
    ``Capex_a_Furnace_wet_district_scale_USD``, "Annualized Capital Costs of CHP Wet-Biomass in Central Plant"
    ``Capex_a_GHP_district_scale_USD``, "Annualized Capital Costs of Ground-Source Heat Pump in Central Plant"
    ``Capex_a_GRID_district_scale_USD``, "Annualized Capital Costs of connection to local electrical grid"
    ``Capex_a_HP_Lake_district_scale_USD``, "Annualized Capital Costs of Lake-Source Heat Pump in Central Plant"
    ``Capex_a_HP_Server_district_scale_USD``, "Annualized Capital Costs of Server-Source Heat Pump in Central Plant"
    ``Capex_a_HP_Sewage_district_scale_USD``, "Annualized Capital Costs of Sewage-Source Heat Pump in Central Plant"
    ``Capex_a_PeakBoiler_NG_district_scale_USD``, "Annualized Capital Costs of Peak Load Boiler Boiler Natural Gas in Central Plant"
    ``Capex_a_PV_district_scale_USD``, "Annualized Capital Costs of Photovoltaic Panels in Central Plant"
    ``Capex_a_PVT_district_scale_USD``, "Annualized Capital Costs of PVT Panels in Central Plant"
    ``Capex_a_SC_ET_district_scale_USD``, "Annualized Capital Costs of Solar Collectors (evacuated-Tube) in Central Plant"
    ``Capex_a_SC_FP_district_scale_USD``, "Annualized Capital Costs of Solar Collectors (Flat-Plate) in Central Plant"
    ``Capex_a_SeasonalStorage_WS_district_scale_USD``, "Annualized Capital Costs of Seasonal Thermal Storage in Central Plant"
    ``Capex_a_SubstationsHeating_district_scale_USD``, "Annualized Capital Costs of Thermal Substations "
    ``Capex_total_BackupBoiler_NG_district_scale_USD``, "Total Capital Costs of Back-up Boiler Natural Gas in Central Plant"
    ``Capex_total_BaseBoiler_NG_district_scale_USD``, "Total Capital Costs of Base Load Boiler Boiler Natural Gas in Central Plant"
    ``Capex_total_CHP_NG_district_scale_USD``, "Total Capital Costs of CHP Natural Gas in Central Plant"
    ``Capex_total_DHN_district_scale_USD``, "Total Capital Costs of District Heating Network"
    ``Capex_total_Furnace_dry_district_scale_USD``, "Total Capital Costs of CHP Dry-Biomass in Central Plant"
    ``Capex_total_Furnace_wet_district_scale_USD``, "Total Capital Costs of CHP Wet-Biomass in Central Plant"
    ``Capex_total_GHP_district_scale_USD``, "Total Capital Costs of Ground-Source Heat Pump in Central Plant"
    ``Capex_total_GRID_district_scale_USD``, "Total Capital Costs of connection to local electrical grid"
    ``Capex_total_HP_Lake_district_scale_USD``, "Total Capital Costs of Lake-Source Heat Pump in Central Plant"
    ``Capex_total_HP_Server_district_scale_USD``, "Total Capital Costs of Server-Source Heat Pump in Central Plant"
    ``Capex_total_HP_Sewage_district_scale_USD``, "Total Capital Costs of Sewage-Source Heat Pump in Central Plant"
    ``Capex_total_PeakBoiler_NG_district_scale_USD``, "Total Capital Costs of Peak Load Boiler Boiler Natural Gas in Central Plant"
    ``Capex_total_PV_district_scale_USD``, "Total Capital Costs of Photovoltaic Panels in Central Plant"
    ``Capex_total_PVT_district_scale_USD``, "Total Capital Costs of PVT Panels in Central Plant"
    ``Capex_total_SC_ET_district_scale_USD``, "Total Capital Costs of Solar Collectors (evacuated-Tube) in Central Plant"
    ``Capex_total_SC_FP_district_scale_USD``, "Total Capital Costs of Solar Collectors (Flat-Plate) in Central Plant"
    ``Capex_total_SeasonalStorage_WS_district_scale_USD``, "Total Capital Costs of Seasonal Thermal Storage in Central Plant"
    ``Capex_total_SubstationsHeating_district_scale_USD``, "Total Capital Costs of Thermal Substations "
    ``generation``, "Number of the Generation or Iteration (Genetic algorithm)"
    ``GHG_DB_district_scale_tonCO2yr``, "Green House Gas Emissions of Dry-Biomass of district-scale systems"
    ``GHG_GRID_exports_district_scale_tonCO2yr``, "Green House Gas Emissions of Exports of Electricity"
    ``GHG_GRID_imports_district_scale_tonCO2yr``, "Green House Gas Emissions of Import of Electricity"
    ``GHG_NG_district_scale_tonCO2yr``, "Green House Gas Emissions of Natural Gas of district-scale systems"
    ``GHG_WB_district_scale_tonCO2yr``, "Green House Gas Emissions of Wet-Biomass of district-scale systems"
    ``individual``, "Unique numerical ID of individual"
    ``individual_name``, "Unique alphanumerical ID of individual"
    ``Opex_fixed_BackupBoiler_NG_district_scale_USD``, "Fixed Operation Costs of Back-up Boiler Natural Gas in Central Plant"
    ``Opex_fixed_BaseBoiler_NG_district_scale_USD``, "Fixed Operation Costs of Base Load Boiler Boiler Natural Gas in Central Plant"
    ``Opex_fixed_CHP_NG_district_scale_USD``, "Fixed Operation Costs of CHP Natural Gas in Central Plant"
    ``Opex_fixed_DHN_district_scale_USD``, "Fixed Operation Costs of District Heating Network"
    ``Opex_fixed_Furnace_dry_district_scale_USD``, "Fixed Operation Costs of CHP Dry-Biomass in Central Plant"
    ``Opex_fixed_Furnace_wet_district_scale_USD``, "Fixed Operation Costs of CHP Wet-Biomass in Central Plant"
    ``Opex_fixed_GHP_district_scale_USD``, "Fixed Operation Costs of Ground-Source Heat Pump in Central Plant"
    ``Opex_fixed_GRID_district_scale_USD``, "Fixed Operation Costs of Electricity in Buildings Connected to Central Plant"
    ``Opex_fixed_HP_Lake_district_scale_USD``, "Fixed Operation Costs of Lake-Source Heat Pump in Central Plant"
    ``Opex_fixed_HP_Server_district_scale_USD``, "Fixed Operation Costs of Server-Source Heat Pump in Central Plant"
    ``Opex_fixed_HP_Sewage_district_scale_USD``, "Fixed Operation Costs of Sewage-Source Heat Pump in Central Plant"
    ``Opex_fixed_PeakBoiler_NG_district_scale_USD``, "Fixed Operation Costs of Peak Load Boiler Boiler Natural Gas in Central Plant"
    ``Opex_fixed_PV_district_scale_USD``, "Fixed Operation Costs of Photovoltaic Panels in Central Plant"
    ``Opex_fixed_PVT_district_scale_USD``, "Fixed Operation Costs of PVT Panels in Central Plant"
    ``Opex_fixed_SC_ET_district_scale_USD``, "Fixed Operation Costs of Solar Collectors (evacuated-Tube) in Central Plant"
    ``Opex_fixed_SC_FP_district_scale_USD``, "Fixed Operation Costs of Solar Collectors (Flat-Plate) in Central Plant"
    ``Opex_fixed_SeasonalStorage_WS_district_scale_USD``, "Fixed Operation Costs of Seasonal Thermal Storage in Central Plant"
    ``Opex_fixed_SubstationsHeating_district_scale_USD``, "Fixed Operation Costs of Thermal Substations "
    ``Opex_var_DB_district_scale_USD``, "Variable Operation Costs due to consumption of Dry-Biomass in Central Plant"
    ``Opex_var_GRID_exports_district_scale_USD``, "Variable Operation Costs due to electricity exported"
    ``Opex_var_GRID_imports_district_scale_USD``, "Variable Operation Costs due to electricity imported "
    ``Opex_var_NG_district_scale_USD``, "Variable Operation Costs due to consumption of Natural Gas in Central Plant"
    ``Opex_var_WB_district_scale_USD``, "Variable Operation Costs due to consumption of Wet-Biomass in Central Plant"
    


get_optimization_generation_total_performance
---------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/gen_2_total_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_sys_building_scale_USD``, "Annualized Capital Costs of building-scale systems"
    ``Capex_a_sys_district_scale_USD``, "Annualized Capital Costs of district-scale systems"
    ``Capex_a_sys_USD``, "Annualized Capital Costs of all systems"
    ``Capex_total_sys_building_scale_USD``, "Total Capital Costs of building-scale systems"
    ``Capex_total_sys_district_scale_USD``, "Total Capital Costs of district-scale systems"
    ``Capex_total_sys_USD``, "Total Capital Costs of district-scale systems and  Decentralized Buildings"
    ``generation``, "No. Generation or Iteration (genetic Algorithm)"
    ``GHG_sys_building_scale_tonCO2``, "Green House Gas Emissions of building-scale systems"
    ``GHG_sys_district_scale_tonCO2``, "Green House Gas Emissions Central Plant"
    ``GHG_sys_tonCO2``, "Green House Gas Emissions of all systems"
    ``individual``, "No. Individual unique ID"
    ``individual_name``, "Name of  Individual unique ID"
    ``Opex_a_sys_building_scale_USD``, "Operation Costs of building-scale systems"
    ``Opex_a_sys_district_scale_USD``, "Operation Costs of district-scale systems "
    ``Opex_a_sys_USD``, "Operation Costs of all systems"
    ``TAC_sys_building_scale_USD``, "Total Anualized Costs of building-scale systems"
    ``TAC_sys_district_scale_USD``, "Total Anualized Costs of district-scale systems"
    ``TAC_sys_USD``, "Total Anualized Costs of all systems"
    


get_optimization_generation_total_performance_pareto
----------------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/gen_2_total_performance_pareto.csv``

The following file is used by these scripts: ``multi_criteria_analysis``


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_sys_building_scale_USD``, "Annualized Capital Costs of building-scale systems"
    ``Capex_a_sys_district_scale_USD``, "Annualized Capital Costs of district-scale systems"
    ``Capex_a_sys_USD``, "Annualized Capital Costs of all systems"
    ``Capex_total_sys_building_scale_USD``, "Total Capital Costs of building-scale systems"
    ``Capex_total_sys_district_scale_USD``, "Total Capital Costs of district-scale systems"
    ``Capex_total_sys_USD``, "Total Capital Costs of district-scale systems and  Decentralized Buildings"
    ``generation``, "No. Generation or Iteration (genetic Algorithm)"
    ``GHG_sys_building_scale_tonCO2``, "Green House Gas Emissions of building-scale systems"
    ``GHG_sys_district_scale_tonCO2``, "Green House Gas Emissions Central Plant"
    ``GHG_sys_tonCO2``, "Green House Gas Emissions of all systems"
    ``individual``, "No. Individual unique ID"
    ``individual_name``, "Name of  Individual unique ID"
    ``Opex_a_sys_building_scale_USD``, "Operation Costs of building-scale systems"
    ``Opex_a_sys_district_scale_USD``, "Operation Costs of district-scale systems "
    ``Opex_a_sys_USD``, "Operation Costs of all systems"
    ``TAC_sys_building_scale_USD``, "Total Anualized Costs of building-scale systems"
    ``TAC_sys_district_scale_USD``, "Total Anualized Costs of district-scale systems"
    ``TAC_sys_USD``, "Total Anualized Costs of all systems"
    


get_optimization_individuals_in_generation
------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/generation_2_individuals.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``B01_DH``, "TODO"
    ``B02_DH``, "TODO"
    ``B03_DH``, "TODO"
    ``B04_DH``, "TODO"
    ``B05_DH``, "TODO"
    ``B06_DH``, "TODO"
    ``B07_DH``, "TODO"
    ``B08_DH``, "TODO"
    ``B09_DH``, "TODO"
    ``DB_Cogen``, "TODO"
    ``DS_HP``, "TODO"
    ``generation``, "TODO"
    ``GS_HP``, "TODO"
    ``individual``, "TODO"
    ``NG_BaseBoiler``, "TODO"
    ``NG_Cogen``, "TODO"
    ``NG_PeakBoiler``, "TODO"
    ``PV``, "TODO"
    ``PVT``, "TODO"
    ``SC_ET``, "TODO"
    ``SC_FP``, "TODO"
    ``SS_HP``, "TODO"
    ``WB_Cogen``, "TODO"
    ``WS_HP``, "TODO"
    


get_optimization_network_results_summary
----------------------------------------

path: ``outputs/data/optimization/network/DH_Network_summary_result_0x1be.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``DATE``, "Time stamp (hourly) for one year"
    ``mcpdata_netw_total_kWperC``, "Capacity mass flow rate for server cooling of this network"
    ``mdot_DH_netw_total_kgpers``, "Total mass flow rate in this district heating network"
    ``Q_DH_losses_W``, "Thermal losses of this district heating network"
    ``Q_DHNf_W``, "Total thermal demand of district heating network"
    ``Qcdata_netw_total_kWh``, "Thermal Demand  for server cooling in this network"
    ``T_DHNf_re_K``, "Average Temperature of return of this district heating network"
    ``T_DHNf_sup_K``, "Average Temperature of supply of this district heating network"
    


get_optimization_slave_building_connectivity
--------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/ind_1_building_connectivity.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``DC_connectivity``, "Flag to know if building is connected to District Heating or not"
    ``DH_connectivity``, "Flag to know if building is connected to District Cooling or not"
    ``Name``, "Unique building ID. It must start with a letter.)"
    


get_optimization_slave_building_scale_performance
-------------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/ind_0_buildings_building_scale_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_cooling_building_scale_USD``, "Annualized Capital Costs of building-scale systems due to cooling"
    ``Capex_a_heating_building_scale_USD``, "Annualized Capital Costs of building-scale systems due to heating"
    ``Capex_total_cooling_building_scale_USD``, "Total Capital Costs of building-scale systems due to cooling"
    ``Capex_total_heating_building_scale_USD``, "Total Capital Costs of building-scale systems due to heating"
    ``GHG_cooling_building_scale_tonCO2``, "Green House Gas Emissions of building-scale systems due to Cooling"
    ``GHG_heating_building_scale_tonCO2``, "Green House Gas Emissions of building-scale systems due to Heating"
    ``Opex_fixed_cooling_building_scale_USD``, "Fixed Operational Costs of building-scale systems due to cooling"
    ``Opex_fixed_heating_building_scale_USD``, "Fixed Operational Costs of building-scale systems due to heating"
    ``Opex_var_cooling_building_scale_USD``, "Variable Operational Costs of building-scale systems due to cooling"
    ``Opex_var_heating_building_scale_USD``, "Variable Operational Costs of building-scale systems due to heating"
    


get_optimization_slave_cooling_activation_pattern
-------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_2_Cooling_Activation_Pattern.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Capacity_DailyStorage_WS_cool_district_scale_W``, "Installed capacity of the short-term thermal storage"
    ``Capex_a_DailyStorage_WS_cool_district_scale_USD``, "Annualized capital costs of the short-term thermal storage"
    ``Capex_total_DailyStorage_WS_cool_district_scale_USD``, "Total capital costs of the short-term thermal storage"
    ``Opex_fixed_DailyStorage_WS_cool_district_scale_USD``, "Fixed operational costs of the short-term thermal storage"
    ``Q_DailyStorage_content_W``, "Thermal energy content of the short-term thermal storage"
    ``Q_DailyStorage_gen_directload_W``, "Thermal energy supplied from the short-term thermal storage"
    


get_optimization_slave_district_scale_performance
-------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_2_buildings_district_scale_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_BackupBoiler_NG_district_scale_USD``, "Annualized Capital Costs of Back-up Boiler Natural Gas in Central Plant"
    ``Capex_a_BaseBoiler_NG_district_scale_USD``, "Annualized Capital Costs of Base load Boiler Natural Gas in Central Plant"
    ``Capex_a_CHP_NG_district_scale_USD``, "Annualized Capital Costs of CHP Natural Gas in Central Plant"
    ``Capex_a_DHN_district_scale_USD``, "Annualized Capital Costs of District Heating Network"
    ``Capex_a_Furnace_dry_district_scale_USD``, "Annualized Capital Costs of CHP Dry-Biomass in Central Plant"
    ``Capex_a_Furnace_wet_district_scale_USD``, "Annualized Capital Costs of CHP Wet-Biomass in Central Plant"
    ``Capex_a_GHP_district_scale_USD``, "Annualized Capital Costs of Ground-Source Heat-Pump in Central Plant"
    ``Capex_a_GRID_district_scale_USD``, "Annualized Capital Costs of connection to local grid"
    ``Capex_a_HP_Lake_district_scale_USD``, "Annualized Capital Costs of Lake-Source Heat Pump in Central Plant"
    ``Capex_a_HP_Server_district_scale_USD``, "Annualized Capital Costs of Server-Source Heat Pump in Central Plant"
    ``Capex_a_HP_Sewage_district_scale_USD``, "Annualized Capital Costs of Sewage-Source Heat Pump in Central Plant"
    ``Capex_a_PeakBoiler_NG_district_scale_USD``, "Annualized Capital Costs of Peak Boiler in Central Plant"
    ``Capex_a_PV_district_scale_USD``, "Annualized Capital Costs of PV panels"
    ``Capex_a_PVT_district_scale_USD``, "Annualized Capital Costs of PVT panels"
    ``Capex_a_SC_ET_district_scale_USD``, "Annualized Capital Costs of Solar collectors (evacuated Tubes)"
    ``Capex_a_SC_FP_district_scale_USD``, "Annualized Capital Costs of Solar collectors (Flat-Plate)"
    ``Capex_a_SeasonalStorage_WS_district_scale_USD``, "Annualized Capital Costs of Seasonal Thermal Storage in Central Plant"
    ``Capex_a_SubstationsHeating_district_scale_USD``, "Annualized Capital Costs of Heating Substations"
    ``Capex_total_BackupBoiler_NG_district_scale_USD``, "Total Capital Costs of Back-up Boiler Natural Gas in Central Plant"
    ``Capex_total_BaseBoiler_NG_district_scale_USD``, "Total Capital Costs of Base load Boiler Natural Gas in Central Plant"
    ``Capex_total_CHP_NG_district_scale_USD``, "Total Capital Costs of CHP Natural Gas in Central Plant"
    ``Capex_total_DHN_district_scale_USD``, "Total Capital Costs of District Heating Network"
    ``Capex_total_Furnace_dry_district_scale_USD``, "Total Capital Costs of CHP Dry-Biomass in Central Plant"
    ``Capex_total_Furnace_wet_district_scale_USD``, "Total Capital Costs of CHP Wet-Biomass in Central Plant"
    ``Capex_total_GHP_district_scale_USD``, "Total Capital Costs of Ground-Source Heat-Pump in Central Plant"
    ``Capex_total_GRID_district_scale_USD``, "Total Capital Costs of connection to local grid"
    ``Capex_total_HP_Lake_district_scale_USD``, "Total Capital Costs of Lake-Source Heat Pump in Central Plant"
    ``Capex_total_HP_Server_district_scale_USD``, "Total Capital Costs of Server-Source Heat Pump in Central Plant"
    ``Capex_total_HP_Sewage_district_scale_USD``, "Total Capital Costs of Sewage-Source Heat Pump in Central Plant"
    ``Capex_total_PeakBoiler_NG_district_scale_USD``, "Total Capital Costs of Peak Boiler in Central Plant"
    ``Capex_total_PV_district_scale_USD``, "Total Capital Costs of PV panels"
    ``Capex_total_PVT_district_scale_USD``, "Total Capital Costs of PVT panels"
    ``Capex_total_SC_ET_district_scale_USD``, "Total Capital Costs of Solar collectors (evacuated Tubes)"
    ``Capex_total_SC_FP_district_scale_USD``, "Total Capital Costs of Solar collectors (Flat-Plate)"
    ``Capex_total_SeasonalStorage_WS_district_scale_USD``, "Total Capital Costs of Seasonal Thermal Storage"
    ``Capex_total_SubstationsHeating_district_scale_USD``, "Total Capital Costs of Heating Substations"
    ``GHG_DB_district_scale_tonCO2yr``, "Green House Gas Emissions of Dry-Biomass in Central plant"
    ``GHG_GRID_exports_district_scale_tonCO2yr``, "Green House Gas Emissions of  Electricity Exports in Central Plant"
    ``GHG_GRID_imports_district_scale_tonCO2yr``, "Green House Gas Emissions of  Electricity Import in Central Plant"
    ``GHG_NG_district_scale_tonCO2yr``, "Green House Gas Emissions of Natural Gas in Central plant"
    ``GHG_WB_district_scale_tonCO2yr``, "Green House Gas Emissions of Wet-Biomass in Central plant"
    ``Opex_fixed_BackupBoiler_NG_district_scale_USD``, "Fixed Operation Costs of Back-up Boiler Natural Gas in Central Plant"
    ``Opex_fixed_BaseBoiler_NG_district_scale_USD``, "Fixed Operation Costs of Base load Boiler Natural Gas in Central Plant"
    ``Opex_fixed_CHP_NG_district_scale_USD``, "Fixed Operation Costs of CHP Natural Gas in Central Plant"
    ``Opex_fixed_DHN_district_scale_USD``, "Fixed Operation Costs of District Heating Network"
    ``Opex_fixed_Furnace_dry_district_scale_USD``, "Fixed Operation Costs of CHP Dry-Biomass in Central Plant"
    ``Opex_fixed_Furnace_wet_district_scale_USD``, "Fixed Operation Costs of CHP Wet-Biomass in Central Plant"
    ``Opex_fixed_GHP_district_scale_USD``, "Fixed Operation Costs of Ground-Source Heat-Pump in Central Plant"
    ``Opex_fixed_GRID_district_scale_USD``, "Fixed Operation Costs of connection to local grid"
    ``Opex_fixed_HP_Lake_district_scale_USD``, "Fixed Operation Costs of Lake-Source Heat Pump in Central Plant"
    ``Opex_fixed_HP_Server_district_scale_USD``, "Fixed Operation Costs of Server-Source Heat Pump in Central Plant"
    ``Opex_fixed_HP_Sewage_district_scale_USD``, "Fixed Operation Costs of Sewage-Source Heat Pump in Central Plant"
    ``Opex_fixed_PeakBoiler_NG_district_scale_USD``, "Fixed Operation Costs of Peak Boiler in Central Plant"
    ``Opex_fixed_PV_district_scale_USD``, "Fixed Operation Costs of PV panels"
    ``Opex_fixed_PVT_district_scale_USD``, "Fixed Operation Costs of PVT panels"
    ``Opex_fixed_SC_ET_district_scale_USD``, "Fixed Operation Costs of Solar collectors (evacuated Tubes)"
    ``Opex_fixed_SC_FP_district_scale_USD``, "Fixed Operation Costs of Solar collectors (Flat-Plate)"
    ``Opex_fixed_SeasonalStorage_WS_district_scale_USD``, "Fixed Operation Costs of Seasonal Thermal Storage"
    ``Opex_fixed_SubstationsHeating_district_scale_USD``, "Fixed Operation Costs of Heating Substations"
    ``Opex_var_DB_district_scale_USD``, "Variable Operation Costs"
    ``Opex_var_GRID_exports_district_scale_USD``, "Variable Operation Costs"
    ``Opex_var_GRID_imports_district_scale_USD``, "Variable Operation Costs"
    ``Opex_var_NG_district_scale_USD``, "Variable Operation Costs"
    ``Opex_var_WB_district_scale_USD``, "Variable Operation Costs"
    


get_optimization_slave_electricity_activation_pattern
-----------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_1_Electricity_Activation_Pattern.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``DATE``, "Time stamp (hourly) for one year"
    ``E_CHP_gen_directload_W``, "Electricity Generated to direct load by CHP Natural Gas"
    ``E_CHP_gen_export_W``, "Electricity Exported by CHP Natural Gas"
    ``E_Furnace_dry_gen_directload_W``, "Electricity Generated to direct load by CHP Dry Biomass"
    ``E_Furnace_dry_gen_export_W``, "Electricity Exported by CHP Dry Biomass"
    ``E_Furnace_wet_gen_directload_W``, "Electricity Generated to direct load by CHP Wet Biomass"
    ``E_Furnace_wet_gen_export_W``, "Electricity Exported by CHP Wet Biomass"
    ``E_GRID_directload_W``, "Electricity Imported from the local grid"
    ``E_PV_gen_directload_W``, "Electricity Generated to direct load by PV panels"
    ``E_PV_gen_export_W``, "Electricity Exported by PV panels"
    ``E_PVT_gen_directload_W``, "Electricity Generated to direct load by PVT panels"
    ``E_PVT_gen_export_W``, "Electricity Exported by PVT panels"
    ``E_Trigen_gen_directload_W``, "Electricity Generated to direct load by Trigen CHP Natural Gas"
    ``E_Trigen_gen_export_W``, "Electricity Exported by Trigen CHP Natural Gas"
    


get_optimization_slave_electricity_requirements_data
----------------------------------------------------

path: ``outputs/data/optimization/slave/gen_1/ind_1_Electricity_Requirements_Pattern.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``DATE``, "Time stamp (hourly) for one year"
    ``E_BackupBoiler_req_W``, "Electricity (auxiliary) Required by Back-up Boiler"
    ``E_BackupVCC_AS_req_W``, "Electricity Required by Back-up Vapor Compression Chiller (Air-Source)"
    ``E_BaseBoiler_req_W``, "Electricity (auxiliary) Required by Base Load Boiler"
    ``E_BaseVCC_AS_req_W``, "Electricity Required by Base Load Vapor Compression Chiller (Air-Source)"
    ``E_BaseVCC_WS_req_W``, "Electricity Required by Base Load Vapor Compression Chiller (Water-Source)"
    ``E_cs_cre_cdata_req_building_scale_W``, "Electricity Required for space cooling, server cooling and refrigeration of building-scale systems"
    ``E_cs_cre_cdata_req_district_scale_W``, "Electricity Required for space cooling, server cooling and refrigeration of Buildings Connected to Network"
    ``E_DCN_req_W``, "Electricity Required for Chilled water Pumping in District Cooling Network"
    ``E_DHN_req_W``, "Electricity Required for Chilled water Pumping in District Heating Network"
    ``E_electricalnetwork_sys_req_W``, "Total Electricity Requirements"
    ``E_GHP_req_W``, "Electricity Required by Ground-Source Heat Pumps"
    ``E_HP_Lake_req_W``, "Electricity Required by Lake-Source Heat Pumps"
    ``E_HP_PVT_req_W``, "Electricity Required by Auxiliary Heat Pumps of PVT panels"
    ``E_HP_SC_ET_req_W``, "Electricity Required by Auxiliary Heat Pumps of Solar collectors (Evacuated tubes)"
    ``E_HP_SC_FP_req_W``, "Electricity Required by Auxiliary Heat Pumps of Solar collectors (Evacuated Flat Plate)"
    ``E_HP_Server_req_W``, "Electricity Required by Server-Source Heat Pumps"
    ``E_HP_Sew_req_W``, "Electricity Required by Sewage-Source Heat Pumps"
    ``E_hs_ww_req_building_scale_W``, "Electricity Required for space heating and hotwater of building-scale systems"
    ``E_hs_ww_req_district_scale_W``, "Electricity Required for space heating and hotwater of Buildings Connected to Network"
    ``E_PeakBoiler_req_W``, "Electricity (auxiliary) Required by Peak-Boiler"
    ``E_PeakVCC_AS_req_W``, "Electricity Required by Peak Vapor Compression Chiller (Air-Source)"
    ``E_PeakVCC_WS_req_W``, "Electricity Required by Peak Vapor Compression Chiller (Water-Source)"
    ``E_Storage_charging_req_W``, "Electricity Required by Auxiliary Heatpumps for charging Seasonal Thermal Storage"
    ``E_Storage_discharging_req_W``, "Electricity Required by Auxiliary Heatpumps for discharging Seasonal Thermal Storage"
    ``Eal_req_W``, "Electricity Required for Appliances and Lighting in all Buildings"
    ``Eaux_req_W``, "Electricity Required for Fans and others in all Buildings"
    ``Edata_req_W``, "Electricity Required for Servers in all Buildings"
    ``Epro_req_W``, "Electricity Required for Industrial Processes in all Buildings"
    


get_optimization_slave_heating_activation_pattern
-------------------------------------------------

path: ``outputs/data/optimization/slave/gen_2/ind_0_Heating_Activation_Pattern.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``DATE``, "Time stamp (hourly) for one year"
    ``E_CHP_gen_W``, "Electricity Generation by CHP Natural Gas"
    ``E_Furnace_dry_gen_W``, "Electricity Generation by CHP Dry-Biomass"
    ``E_Furnace_wet_gen_W``, "Electricity Generation by CHP Wet-Biomass"
    ``E_PVT_gen_W``, "Electricity Generation by PVT"
    ``Q_BackupBoiler_gen_directload_W``, "Thermal generation of Back-up Boiler to direct load"
    ``Q_BaseBoiler_gen_directload_W``, "Thermal generation of Base load Boiler to direct load"
    ``Q_CHP_gen_directload_W``, "Thermal generation of CHP Natural Gas to direct load"
    ``Q_districtheating_sys_req_W``, "Thermal requirements of District Heating Network"
    ``Q_Furnace_dry_gen_directload_W``, "Thermal generation of CHP Dry-Biomass to direct load"
    ``Q_Furnace_wet_gen_directload_W``, "Thermal generation of CHP Wet-Biomass to direct load"
    ``Q_GHP_gen_directload_W``, "Thermal generation of ground-source heat pump to direct load"
    ``Q_HP_Lake_gen_directload_W``, "Thermal generation of Lake-Source Heatpump to direct load"
    ``Q_HP_Server_gen_directload_W``, "Thermal generation of Server-Source Heatpump to direct load"
    ``Q_HP_Server_storage_W``, "Thermal generation of Server-Source Heatpump to Seasonal Thermal Storage"
    ``Q_HP_Sew_gen_directload_W``, "Thermal generation of Sewage-Source Heatpump to direct load"
    ``Q_PeakBoiler_gen_directload_W``, "Thermal generation of Peak Boiler to direct load"
    ``Q_PVT_gen_directload_W``, "Thermal generation of PVT  to direct load"
    ``Q_PVT_gen_storage_W``, "Thermal generation of PVT  to Seasonal Thermal Storage"
    ``Q_SC_ET_gen_directload_W``, "Thermal generation of Solar Collectors (Evacuated Tubes) to direct load"
    ``Q_SC_ET_gen_storage_W``, "Thermal generation of Solar Collectors (Evacuated Tubes)  to Seasonal Thermal Storage"
    ``Q_SC_FP_gen_directload_W``, "Thermal generation of Solar Collectors (Flat Plate) to direct load"
    ``Q_SC_FP_gen_storage_W``, "Thermal generation of Solar Collectors (Flat Plate)  to Seasonal Thermal Storage"
    ``Q_Storage_gen_directload_W``, "Discharge from Storage to Direct Load"
    


get_optimization_slave_total_performance
----------------------------------------

path: ``outputs/data/optimization/slave/gen_0/ind_2_total_performance.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Capex_a_sys_building_scale_USD``, "Annualized Capital Costs of building-scale systems"
    ``Capex_a_sys_district_scale_USD``, "Annualized Capital Costs of district-scale systems"
    ``Capex_a_sys_USD``, "Annualized Capital Costs of all systems"
    ``Capex_total_sys_building_scale_USD``, "Total Capital Costs of building-scale systems"
    ``Capex_total_sys_district_scale_USD``, "Total Capital Costs of district-scale systems"
    ``Capex_total_sys_USD``, "Total Capital Costs of all systems"
    ``GHG_sys_building_scale_tonCO2``, "Green House Gas Emissions of building-scale systems"
    ``GHG_sys_district_scale_tonCO2``, "Green House Gas Emissions Central Plant"
    ``GHG_sys_tonCO2``, "Green House Gas Emissions of all systems"
    ``Opex_a_sys_building_scale_USD``, "Operation Costs of building-scale systems"
    ``Opex_a_sys_district_scale_USD``, "Operation Costs of district-scale systems"
    ``Opex_a_sys_USD``, "Operation Costs of all systems"
    ``TAC_sys_building_scale_USD``, "Total Anualized Costs of building-scale systems"
    ``TAC_sys_district_scale_USD``, "Total Anualized Costs of district-scale systems"
    ``TAC_sys_USD``, "Total Anualized Costs of all systems"
    


get_optimization_substations_results_file
-----------------------------------------

path: ``outputs/data/optimization/substations/110011011DH_B001_result.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``A_hex_dhw_design_m2``, "Substation heat exchanger area to supply domestic hot water"
    ``A_hex_heating_design_m2``, "Substation heat exchanger area to supply space heating"
    ``mdot_DH_result_kgpers``, "Substation flow rate on the DH side."
    ``Q_dhw_W``, "Substation heat requirement to supply domestic hot water"
    ``Q_heating_W``, "Substation heat requirement to supply space heating"
    ``T_return_DH_result_K``, "Substation return temperature of the district heating network"
    ``T_supply_DH_result_K``, "Substation supply temperature of the district heating network."
    


get_optimization_substations_total_file
---------------------------------------

path: ``outputs/data/optimization/substations/Total_DH_111111111.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Af_m2``, "Conditioned floor area (heated/cooled)"
    ``Aocc_m2``, "Occupied floor area (heated/cooled)"
    ``Aroof_m2``, "Roof area"
    ``COAL_hs0_kW``, "Nominal Coal requirement for space heating supply"
    ``COAL_hs_MWhyr``, "Coal requirement for space heating supply"
    ``COAL_ww0_kW``, "Nominal Coal requirement for hotwater supply"
    ``COAL_ww_MWhyr``, "Coal requirement for hotwater supply"
    ``DC_cdata0_kW``, "Nominal district cooling for final data center cooling demand"
    ``DC_cdata_MWhyr``, "District cooling for data center cooling demand"
    ``DC_cre0_kW``, "Nominal district cooling for refrigeration demand"
    ``DC_cre_MWhyr``, "District cooling for refrigeration demand"
    ``DC_cs0_kW``, "Nominal district cooling for space cooling demand"
    ``DC_cs_MWhyr``, "Energy consumption of space cooling system (if supplied by District Cooling), DC_cs = Qcs_sys / eff_cs"
    ``DH_hs0_kW``, "Nominal energy requirement by district heating (space heating supply)"
    ``DH_hs_MWhyr``, "Energy requirement by district heating (space heating supply)"
    ``DH_ww0_kW``, "Nominal Energy requirement by district heating (hotwater supply)"
    ``DH_ww_MWhyr``, "Energy requirement by district heating (hotwater supply)"
    ``E_cdata0_kW``, "Nominal Data centre cooling specific electricity consumption."
    ``E_cdata_MWhyr``, "Electricity consumption due to data center cooling"
    ``E_cre0_kW``, "Nominal Refrigeration system electricity consumption."
    ``E_cre_MWhyr``, "Electricity consumption due to refrigeration"
    ``E_cs0_kW``, "Nominal Cooling system electricity consumption."
    ``E_cs_MWhyr``, "Energy consumption of cooling system (if supplied by electricity grid), E_cs = Qcs_sys / eff_cs"
    ``E_hs0_kW``, "Nominal Heating system electricity consumption."
    ``E_hs_MWhyr``, "Electricity consumption due to space heating"
    ``E_sys0_kW``, "Nominal end-use electricity demand"
    ``E_sys_MWhyr``, "End-use total electricity consumption, E_sys =  Eve + Ea + El + Edata + Epro + Eaux + Ev"
    ``E_ww0_kW``, "Nominal Domestic hot water electricity consumption."
    ``E_ww_MWhyr``, "Electricity consumption due to hot water"
    ``Ea0_kW``, "Nominal end-use electricity for appliances"
    ``Ea_MWhyr``, "End-use electricity for appliances"
    ``Eal0_kW``, "Nominal Total net electricity for all sources and sinks."
    ``Eal_MWhyr``, "End-use electricity consumption of appliances and lighting, Eal = El_W + Ea_W"
    ``Eaux0_kW``, "Nominal Auxiliary electricity consumption."
    ``Eaux_MWhyr``, "End-use auxiliary electricity consumption, Eaux = Eaux_fw + Eaux_ww + Eaux_cs + Eaux_hs + Ehs_lat_aux"
    ``Edata0_kW``, "Nominal Data centre electricity consumption."
    ``Edata_MWhyr``, "Electricity consumption for data centers"
    ``El0_kW``, "Nominal end-use electricity for lights"
    ``El_MWhyr``, "End-use electricity for lights"
    ``Epro0_kW``, "Nominal Industrial processes electricity consumption."
    ``Epro_MWhyr``, "Electricity supplied to industrial processes"
    ``Ev0_kW``, "Nominal end-use electricity for electric vehicles"
    ``Ev_MWhyr``, "End-use electricity for electric vehicles"
    ``Eve0_kW``, "Nominal end-use electricity for ventilation"
    ``Eve_MWhyr``, "End-use electricity for ventilation"
    ``GFA_m2``, "Gross floor area"
    ``GRID0_kW``, "Nominal Grid electricity consumption"
    ``GRID_a0_kW``, "Nominal grid electricity requirements for appliances"
    ``GRID_a_MWhyr``, "Grid electricity requirements for appliances"
    ``GRID_aux0_kW``, "Nominal grid electricity requirements for auxiliary loads"
    ``GRID_aux_MWhyr``, "Grid electricity requirements for auxiliary loads"
    ``GRID_cdata0_kW``, "Nominal grid electricity requirements for servers cooling"
    ``GRID_cdata_MWhyr``, "Grid electricity requirements for servers cooling"
    ``GRID_cre0_kW``, "Nominal grid electricity requirements for refrigeration"
    ``GRID_cre_MWhyr``, "Grid electricity requirements for refrigeration"
    ``GRID_cs0_kW``, "Nominal grid electricity requirements for space cooling"
    ``GRID_cs_MWhyr``, "Grid electricity requirements for space cooling"
    ``GRID_data0_kW``, "Nominal grid electricity requirements for servers"
    ``GRID_data_MWhyr``, "Grid electricity requirements for servers"
    ``GRID_hs0_kW``, "Nominal grid electricity requirements for space heating"
    ``GRID_hs_MWhyr``, "Grid electricity requirements for space heating"
    ``GRID_l0_kW``, "Nominal grid electricity consumption for lights"
    ``GRID_l_MWhyr``, "Grid electricity requirements for lights"
    ``GRID_MWhyr``, "Grid electricity consumption, GRID = GRID_a + GRID_l + GRID_v + GRID_ve + GRID_data + GRID_pro + GRID_aux + GRID_ww + GRID_cs + GRID_hs + GRID_cdata + GRID_cre"
    ``GRID_pro0_kW``, "Nominal grid electricity requirements for industrial processes"
    ``GRID_pro_MWhyr``, "Grid electricity requirements for industrial processes"
    ``GRID_v0_kW``, "Nominal grid electricity consumption for electric vehicles"
    ``GRID_v_MWhyr``, "Grid electricity requirements for electric vehicles"
    ``GRID_ve0_kW``, "Nominal grid electricity consumption for ventilatioon"
    ``GRID_ve_MWhyr``, "Grid electricity requirements for ventilatioon"
    ``GRID_ww0_kW``, "Nominal grid electricity requirements for hot water supply"
    ``GRID_ww_MWhyr``, "Grid electricity requirements for hot water supply"
    ``Name``, "Unique building ID. It must start with a letter."
    ``NG_hs0_kW``, "Nominal NG requirement for space heating supply"
    ``NG_hs_MWhyr``, "NG requirement for space heating supply"
    ``NG_ww0_kW``, "Nominal NG requirement for hotwater supply"
    ``NG_ww_MWhyr``, "NG requirement for hotwater supply"
    ``OIL_hs0_kW``, "Nominal OIL requirement for space heating supply"
    ``OIL_hs_MWhyr``, "OIL requirement for space heating supply"
    ``OIL_ww0_kW``, "Nominal OIL requirement for hotwater supply"
    ``OIL_ww_MWhyr``, "OIL requirement for hotwater supply"
    ``people0``, "Nominal occupancy"
    ``PV0_kW``, "Nominal PV electricity consumption"
    ``PV_MWhyr``, "PV electricity consumption"
    ``QC_sys0_kW``, "Nominal Total system cooling demand."
    ``QC_sys_MWhyr``, "Total system cooling demand, QC_sys = Qcs_sys + Qcdata_sys + Qcre_sys + Qcpro_sys"
    ``Qcdata0_kW``, "Nominal Data centre cooling demand."
    ``Qcdata_MWhyr``, "Data centre cooling demand"
    ``Qcdata_sys0_kW``, "Nominal end-use data center cooling demand"
    ``Qcdata_sys_MWhyr``, "End-use data center cooling demand"
    ``Qcpro_sys0_kW``, "Nominal process cooling demand."
    ``Qcpro_sys_MWhyr``, "Yearly processes cooling demand."
    ``Qcre0_kW``, "Nominal Refrigeration cooling demand."
    ``Qcre_MWhyr``, "Refrigeration cooling demand for the system"
    ``Qcre_sys0_kW``, " Nominal refrigeration cooling demand"
    ``Qcre_sys_MWhyr``, "End-use refrigeration demand"
    ``Qcs0_kW``, "Nominal Total cooling demand."
    ``Qcs_dis_ls0_kW``, "Nominal Cooling distribution losses."
    ``Qcs_dis_ls_MWhyr``, "Cooling distribution losses"
    ``Qcs_em_ls0_kW``, "Nominal Cooling emission losses."
    ``Qcs_em_ls_MWhyr``, "Cooling emission losses"
    ``Qcs_lat_ahu0_kW``, "Nominal AHU latent cooling demand."
    ``Qcs_lat_ahu_MWhyr``, "AHU latent cooling demand"
    ``Qcs_lat_aru0_kW``, "Nominal ARU latent cooling demand."
    ``Qcs_lat_aru_MWhyr``, "ARU latent cooling demand"
    ``Qcs_lat_sys0_kW``, "Nominal System latent cooling demand."
    ``Qcs_lat_sys_MWhyr``, "System latent cooling demand"
    ``Qcs_MWhyr``, "Total cooling demand"
    ``Qcs_sen_ahu0_kW``, "Nominal AHU system cooling demand."
    ``Qcs_sen_ahu_MWhyr``, "Sensible cooling demand in AHU"
    ``Qcs_sen_aru0_kW``, "Nominal ARU system cooling demand."
    ``Qcs_sen_aru_MWhyr``, "ARU system cooling demand"
    ``Qcs_sen_scu0_kW``, "Nominal SCU system cooling demand."
    ``Qcs_sen_scu_MWhyr``, "SCU system cooling demand"
    ``Qcs_sen_sys0_kW``, "Nominal Sensible system cooling demand."
    ``Qcs_sen_sys_MWhyr``, "Total sensible cooling demand"
    ``Qcs_sys0_kW``, "Nominal end-use space cooling demand"
    ``Qcs_sys_ahu0_kW``, "Nominal AHU system cooling demand."
    ``Qcs_sys_ahu_MWhyr``, "AHU system cooling demand"
    ``Qcs_sys_aru0_kW``, "Nominal ARU system cooling demand."
    ``Qcs_sys_aru_MWhyr``, "ARU system cooling demand"
    ``Qcs_sys_MWhyr``, "End-use space cooling demand, Qcs_sys = Qcs_sen_sys + Qcs_lat_sys + Qcs_em_ls + Qcs_dis_ls"
    ``Qcs_sys_scu0_kW``, "Nominal SCU system cooling demand."
    ``Qcs_sys_scu_MWhyr``, "SCU system cooling demand"
    ``QH_sys0_kW``, "Nominal total building heating demand."
    ``QH_sys_MWhyr``, "Total building heating demand"
    ``Qhpro_sys0_kW``, "Nominal process heating demand."
    ``Qhpro_sys_MWhyr``, "Yearly processes heating demand."
    ``Qhs0_kW``, "Nominal space heating demand."
    ``Qhs_dis_ls0_kW``, "Nominal Heating system distribution losses."
    ``Qhs_dis_ls_MWhyr``, "Heating system distribution losses"
    ``Qhs_em_ls0_kW``, "Nominal Heating emission losses."
    ``Qhs_em_ls_MWhyr``, "Heating system emission losses"
    ``Qhs_lat_ahu0_kW``, "Nominal AHU latent heating demand."
    ``Qhs_lat_ahu_MWhyr``, "AHU latent heating demand"
    ``Qhs_lat_aru0_kW``, "Nominal ARU latent heating demand."
    ``Qhs_lat_aru_MWhyr``, "ARU latent heating demand"
    ``Qhs_lat_sys0_kW``, "Nominal System latent heating demand."
    ``Qhs_lat_sys_MWhyr``, "System latent heating demand"
    ``Qhs_MWhyr``, "Total space heating demand."
    ``Qhs_sen_ahu0_kW``, "Nominal AHU sensible heating demand."
    ``Qhs_sen_ahu_MWhyr``, "AHU sensible heating demand"
    ``Qhs_sen_aru0_kW``, "ARU sensible heating demand"
    ``Qhs_sen_aru_MWhyr``, "ARU sensible heating demand"
    ``Qhs_sen_shu0_kW``, "Nominal SHU sensible heating demand."
    ``Qhs_sen_shu_MWhyr``, "SHU sensible heating demand"
    ``Qhs_sen_sys0_kW``, "Nominal HVAC systems sensible heating demand."
    ``Qhs_sen_sys_MWhyr``, "SHU sensible heating demand"
    ``Qhs_sys0_kW``, "Nominal end-use space heating demand"
    ``Qhs_sys_ahu0_kW``, "Nominal AHU sensible heating demand."
    ``Qhs_sys_ahu_MWhyr``, "AHU system heating demand"
    ``Qhs_sys_aru0_kW``, "Nominal ARU sensible heating demand."
    ``Qhs_sys_aru_MWhyr``, "ARU sensible heating demand"
    ``Qhs_sys_MWhyr``, "End-use space heating demand, Qhs_sys = Qhs_sen_sys + Qhs_em_ls + Qhs_dis_ls"
    ``Qhs_sys_shu0_kW``, "Nominal SHU sensible heating demand."
    ``Qhs_sys_shu_MWhyr``, "SHU sensible heating demand"
    ``Qww0_kW``, "Nominal DHW heating demand."
    ``Qww_MWhyr``, "DHW heating demand"
    ``Qww_sys0_kW``, "Nominal end-use hotwater demand"
    ``Qww_sys_MWhyr``, "End-use hotwater demand"
    ``SOLAR_hs0_kW``, "Nominal solar thermal energy requirement for space heating supply"
    ``SOLAR_hs_MWhyr``, "Solar thermal energy requirement for space heating supply"
    ``SOLAR_ww0_kW``, "Nominal solar thermal energy requirement for hotwater supply"
    ``SOLAR_ww_MWhyr``, "Solar thermal energy requirement for hotwater supply"
    ``WOOD_hs0_kW``, "Nominal WOOD requirement for space heating supply"
    ``WOOD_hs_MWhyr``, "WOOD requirement for space heating supply"
    ``WOOD_ww0_kW``, "Nominal WOOD requirement for hotwater supply"
    ``WOOD_ww_MWhyr``, "WOOD requirement for hotwater supply"
    


get_radiation_building
----------------------

path: ``outputs/data/solar-radiation/{building}_radiation.csv``

The following file is used by these scripts: ``demand``, ``photovoltaic``, ``photovoltaic_thermal``, ``solar_collector``


.. csv-table::
    :header: "Variable", "Description"

    ``Date``, "Date and time in hourly steps"
    ``roofs_top_kW``, "solar incident on the roof tops"
    ``roofs_top_m2``, "roof top area"
    ``walls_east_kW``, "solar incident on the east facing facades excluding windows"
    ``walls_east_m2``, "area of the east facing facades excluding windows"
    ``walls_north_kW``, "solar incident on the north facing facades excluding windows"
    ``walls_north_m2``, "area of the north facing facades excluding windows"
    ``walls_south_kW``, "solar incident on the south facing facades excluding windows"
    ``walls_south_m2``, "area of the south facing facades excluding windows"
    ``walls_west_kW``, "solar incident on the west facing facades excluding windows"
    ``walls_west_m2``, "area of the south facing facades excluding windows"
    ``windows_east_kW``, "solar incident on windows on the south facing facades"
    ``windows_east_m2``, "window area on the east facing facades"
    ``windows_north_kW``, "solar incident on windows on the south facing facades"
    ``windows_north_m2``, "window area on the north facing facades"
    ``windows_south_kW``, "solar incident on windows on the south facing facades"
    ``windows_south_m2``, "window area on the south facing facades"
    ``windows_west_kW``, "solar incident on windows on the west facing facades"
    ``windows_west_m2``, "window area on the west facing facades"
    


get_radiation_building_sensors
------------------------------

path: ``outputs/data/solar-radiation/B001_insolation_Whm2.json``

The following file is used by these scripts: ``demand``, ``photovoltaic``, ``photovoltaic_thermal``, ``solar_collector``


.. csv-table::
    :header: "Variable", "Description"

    ``srf0``, "TODO"
    


get_radiation_materials
-----------------------

path: ``outputs/data/solar-radiation/buidling_materials.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``G_win``, "Solar heat gain coefficient. Defined according to ISO 13790."
    ``Name``, "Unique building ID. It must start with a letter."
    ``r_roof``, "Reflectance in the Red spectrum. Defined according Radiance. (long-wave)"
    ``r_wall``, "Reflectance in the Red spectrum. Defined according Radiance. (long-wave)"
    ``type_base``, "Basement floor construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_floor``, "Internal floor construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_roof``, "Roof construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_wall``, "External wall construction assembly (relates to ""code"" in ENVELOPE assemblies)"
    ``type_win``, "Window assembly (relates to ""code"" in ENVELOPE assemblies)"
    


get_radiation_metadata
----------------------

path: ``outputs/data/solar-radiation/B001_geometry.csv``

The following file is used by these scripts: ``demand``, ``photovoltaic``, ``photovoltaic_thermal``, ``solar_collector``


.. csv-table::
    :header: "Variable", "Description"

    ``AREA_m2``, "Surface area."
    ``BUILDING``, "Unique building ID. It must start with a letter."
    ``intersection``, "flag to indicate whether this surface is intersecting with another surface (0: no intersection, 1: intersected)"
    ``orientation``, "Orientation of the surface (north/east/south/west/top)"
    ``SURFACE``, "Unique surface ID for each building exterior surface."
    ``TYPE``, "Surface typology."
    ``Xcoor``, "Describes the position of the x vector."
    ``Xdir``, "Directional scalar of the x vector."
    ``Ycoor``, "Describes the position of the y vector."
    ``Ydir``, "Directional scalar of the y vector."
    ``Zcoor``, "Describes the position of the z vector."
    ``Zdir``, "Directional scalar of the z vector."
    


get_schedule_model_file
-----------------------

path: ``outputs/data/occupancy/B001.csv``

The following file is used by these scripts: ``demand``


.. csv-table::
    :header: "Variable", "Description"

    ``DATE``, "Time stamp for each day of the year ascending in hourly intervals"
    ``Ea_W``, "Electrical load due to processes"
    ``Ed_W``, "Electrical load due to servers/data centers"
    ``El_W``, "Electrical load due to lighting"
    ``Epro_W``, "Electrical load due to processes"
    ``people_p``, "Number of people in the building"
    ``Qcpro_W``, "Process cooling load"
    ``Qcre_W``, "Cooling load due to cool room refrigeration"
    ``Qhpro_W``, "Process heat load"
    ``Qs_W``, "Sensible heat load of people"
    ``Tcs_set_C``, "Set point temperature of space cooling system"
    ``Ths_set_C``, "Set point temperature of space heating system"
    ``Ve_lps``, "Ventilation rate"
    ``Vw_lph``, "Fresh water consumption (includes cold and hot water)"
    ``Vww_lph``, "Domestic hot water consumption"
    ``X_gh``, "Moisture released by occupants"
    


get_sewage_heat_potential
-------------------------

path: ``outputs/data/potentials/Sewage_heat_potential.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``mww_zone_kWperC``, "heat capacity of total sewage in a zone"
    ``Qsw_kW``, "heat extracted from sewage flows"
    ``T_in_HP_C``, "Inlet temperature of the sweage heapump"
    ``T_in_sw_C``, "Inlet temperature of sewage flows"
    ``T_out_HP_C``, "Outlet temperature of the sewage heatpump"
    ``T_out_sw_C``, "Outlet temperature of sewage flows"
    ``Ts_C``, "Average temperature of sewage flows"
    


get_thermal_demand_csv_file
---------------------------

path: ``outputs/data/thermal-network/DH__thermal_demand_per_building_W.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``B01``, "Thermal demand for building B01 at each simulation time step"
    


get_thermal_network_edge_list_file
----------------------------------

path: ``outputs/data/thermal-network/DH__metadata_edges.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``D_int_m``, "Internal pipe diameter for the nominal diameter"
    ``length_m``, "Length of each pipe in the network"
    ``name``, "Unique network pipe ID."
    ``pipe_DN``, "Nominal pipe diameter (e.g. DN100 refers to pipes of approx. 100 mm in diameter)"
    ``type_mat``, "Material of the pipes"
    


get_thermal_network_edge_node_matrix_file
-----------------------------------------

path: ``outputs/data/thermal-network/{network_type}__EdgeNode.csv``

The following file is used by these scripts: ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``NODE``, "Names of the nodes in the network"
    ``PIPE0``, "Indicates the direction of flow of PIPE0 with respect to each node NODEn: if equal to PIPE0 and NODEn are not connected / if equal to 1 PIPE0 enters NODEn / if equal to -1 PIPE0 leaves NODEn"
    


get_thermal_network_layout_massflow_edges_file
----------------------------------------------

path: ``outputs/data/thermal-network/DH__massflow_edges_kgs.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "Mass flow rate in pipe PIPE0 at each time step"
    


get_thermal_network_layout_massflow_nodes_file
----------------------------------------------

path: ``outputs/data/thermal-network/DH__massflow_nodes_kgs.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``NODE0``, "Mass flow rate in node NODE0 at each time step"
    


get_thermal_network_node_types_csv_file
---------------------------------------

path: ``outputs/data/thermal-network/DH__metadata_nodes.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Building``, "Unique building ID. It must start with a letter."
    ``Name``, "Unique network node ID."
    ``Type``, "Type of node: ""PLANT"" / ""CONSUMER"" / ""NONE"" (if it is neither)"
    


get_thermal_network_plant_heat_requirement_file
-----------------------------------------------

path: ``outputs/data/thermal-network/DH__plant_thermal_load_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``thermal_load_kW``, "Thermal load supplied by the plant at each time step"
    


get_thermal_network_pressure_losses_edges_file
----------------------------------------------

path: ``outputs/data/thermal-network/DH__pressure_losses_edges_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "Pressure losses at pipe PIPE0 at each time step"
    


get_thermal_network_substation_ploss_file
-----------------------------------------

path: ``outputs/data/thermal-network/DH__pumping_load_due_to_substations_kW.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``B01``, "Pumping load at building substation B01 for each timestep"
    


get_thermal_network_velocity_edges_file
---------------------------------------

path: ``outputs/data/thermal-network/DH__velocity_edges_mpers.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``PIPE0``, "Flow velocity of heating/cooling medium in pipe PIPE0"
    


get_total_demand
----------------

path: ``outputs/data/demand/Total_demand.csv``

The following file is used by these scripts: ``decentralized``, ``emissions``, ``network_layout``, ``system_costs``, ``optimization``, ``sewage_potential``, ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``Af_m2``, "Conditioned floor area (heated/cooled)"
    ``Aocc_m2``, "Occupied floor area (heated/cooled)"
    ``Aroof_m2``, "Roof area"
    ``COAL_hs0_kW``, "Nominal Coal requirement for space heating supply"
    ``COAL_hs_MWhyr``, "Coal requirement for space heating supply"
    ``COAL_ww0_kW``, "Nominal Coal requirement for hotwater supply"
    ``COAL_ww_MWhyr``, "Coal requirement for hotwater supply"
    ``DC_cdata0_kW``, "Nominal district cooling for final data center cooling demand"
    ``DC_cdata_MWhyr``, "District cooling for data center cooling demand"
    ``DC_cre0_kW``, "Nominal district cooling for refrigeration demand"
    ``DC_cre_MWhyr``, "District cooling for refrigeration demand"
    ``DC_cs0_kW``, "Nominal district cooling for space cooling demand"
    ``DC_cs_MWhyr``, "Energy consumption of space cooling system (if supplied by District Cooling), DC_cs = Qcs_sys / eff_cs"
    ``DH_hs0_kW``, "Nominal energy requirement by district heating (space heating supply)"
    ``DH_hs_MWhyr``, "Energy requirement by district heating (space heating supply)"
    ``DH_ww0_kW``, "Nominal Energy requirement by district heating (hotwater supply)"
    ``DH_ww_MWhyr``, "Energy requirement by district heating (hotwater supply)"
    ``E_cdata0_kW``, "Nominal Data centre cooling specific electricity consumption."
    ``E_cdata_MWhyr``, "Electricity consumption due to data center cooling"
    ``E_cre0_kW``, "Nominal Refrigeration system electricity consumption."
    ``E_cre_MWhyr``, "Electricity consumption due to refrigeration"
    ``E_cs0_kW``, "Nominal Cooling system electricity consumption."
    ``E_cs_MWhyr``, "Energy consumption of cooling system (if supplied by electricity grid), E_cs = Qcs_sys / eff_cs"
    ``E_hs0_kW``, "Nominal Heating system electricity consumption."
    ``E_hs_MWhyr``, "Electricity consumption due to space heating"
    ``E_sys0_kW``, "Nominal end-use electricity demand"
    ``E_sys_MWhyr``, "End-use total electricity consumption, E_sys =  Eve + Ea + El + Edata + Epro + Eaux + Ev"
    ``E_ww0_kW``, "Nominal Domestic hot water electricity consumption."
    ``E_ww_MWhyr``, "Electricity consumption due to hot water"
    ``Ea0_kW``, "Nominal end-use electricity for appliances"
    ``Ea_MWhyr``, "End-use electricity for appliances"
    ``Eal0_kW``, "Nominal Total net electricity for all sources and sinks."
    ``Eal_MWhyr``, "End-use electricity consumption of appliances and lighting, Eal = El_W + Ea_W"
    ``Eaux0_kW``, "Nominal Auxiliary electricity consumption."
    ``Eaux_MWhyr``, "End-use auxiliary electricity consumption, Eaux = Eaux_fw + Eaux_ww + Eaux_cs + Eaux_hs + Ehs_lat_aux"
    ``Edata0_kW``, "Nominal Data centre electricity consumption."
    ``Edata_MWhyr``, "Electricity consumption for data centers"
    ``El0_kW``, "Nominal end-use electricity for lights"
    ``El_MWhyr``, "End-use electricity for lights"
    ``Epro0_kW``, "Nominal Industrial processes electricity consumption."
    ``Epro_MWhyr``, "Electricity supplied to industrial processes"
    ``Ev0_kW``, "Nominal end-use electricity for electric vehicles"
    ``Ev_MWhyr``, "End-use electricity for electric vehicles"
    ``Eve0_kW``, "Nominal end-use electricity for ventilation"
    ``Eve_MWhyr``, "End-use electricity for ventilation"
    ``GFA_m2``, "Gross floor area"
    ``GRID0_kW``, "Nominal Grid electricity consumption"
    ``GRID_a0_kW``, "Nominal grid electricity requirements for appliances"
    ``GRID_a_MWhyr``, "Grid electricity requirements for appliances"
    ``GRID_aux0_kW``, "Nominal grid electricity requirements for auxiliary loads"
    ``GRID_aux_MWhyr``, "Grid electricity requirements for auxiliary loads"
    ``GRID_cdata0_kW``, "Nominal grid electricity requirements for servers cooling"
    ``GRID_cdata_MWhyr``, "Grid electricity requirements for servers cooling"
    ``GRID_cre0_kW``, "Nominal grid electricity requirements for refrigeration"
    ``GRID_cre_MWhyr``, "Grid electricity requirements for refrigeration"
    ``GRID_cs0_kW``, "Nominal grid electricity requirements for space cooling"
    ``GRID_cs_MWhyr``, "Grid electricity requirements for space cooling"
    ``GRID_data0_kW``, "Nominal grid electricity requirements for servers"
    ``GRID_data_MWhyr``, "Grid electricity requirements for servers"
    ``GRID_hs0_kW``, "Nominal grid electricity requirements for space heating"
    ``GRID_hs_MWhyr``, "Grid electricity requirements for space heating"
    ``GRID_l0_kW``, "Nominal grid electricity consumption for lights"
    ``GRID_l_MWhyr``, "Grid electricity requirements for lights"
    ``GRID_MWhyr``, "Grid electricity consumption, GRID_a + GRID_l + GRID_v + GRID_ve + GRID_data + GRID_pro + GRID_aux + GRID_ww + GRID_cs + GRID_hs + GRID_cdata + GRID_cre"
    ``GRID_pro0_kW``, "Nominal grid electricity requirements for industrial processes"
    ``GRID_pro_MWhyr``, "Grid electricity requirements for industrial processes"
    ``GRID_v0_kW``, "Nominal grid electricity consumption for electric vehicles"
    ``GRID_v_MWhyr``, "Grid electricity requirements for electric vehicles"
    ``GRID_ve0_kW``, "Nominal grid electricity consumption for ventilation"
    ``GRID_ve_MWhyr``, "Grid electricity requirements for ventilation"
    ``GRID_ww0_kW``, "Nominal grid electricity requirements for hot water supply"
    ``GRID_ww_MWhyr``, "Grid electricity requirements for hot water supply"
    ``Name``, "Unique building ID. It must start with a letter."
    ``NG_hs0_kW``, "Nominal NG requirement for space heating supply"
    ``NG_hs_MWhyr``, "NG requirement for space heating supply"
    ``NG_ww0_kW``, "Nominal NG requirement for hotwater supply"
    ``NG_ww_MWhyr``, "NG requirement for hotwater supply"
    ``OIL_hs0_kW``, "Nominal OIL requirement for space heating supply"
    ``OIL_hs_MWhyr``, "OIL requirement for space heating supply"
    ``OIL_ww0_kW``, "Nominal OIL requirement for hotwater supply"
    ``OIL_ww_MWhyr``, "OIL requirement for hotwater supply"
    ``people0``, "Nominal occupancy"
    ``PV0_kW``, "Nominal PV electricity consumption"
    ``PV_MWhyr``, "PV electricity consumption"
    ``QC_sys0_kW``, "Nominal Total system cooling demand."
    ``QC_sys_MWhyr``, "Total energy demand for cooling, QC_sys = Qcs_sys + Qcdata_sys + Qcre_sys + Qcpro_sys"
    ``Qcdata0_kW``, "Nominal Data centre cooling demand."
    ``Qcdata_MWhyr``, "Data centre cooling demand"
    ``Qcdata_sys0_kW``, "Nominal end-use data center cooling demand"
    ``Qcdata_sys_MWhyr``, "End-use data center cooling demand"
    ``Qcpro_sys0_kW``, "Nominal process cooling demand."
    ``Qcpro_sys_MWhyr``, "Yearly processes cooling demand."
    ``Qcre0_kW``, "Nominal Refrigeration cooling demand."
    ``Qcre_MWhyr``, "Refrigeration cooling demand for the system"
    ``Qcre_sys0_kW``, " Nominal refrigeration cooling demand"
    ``Qcre_sys_MWhyr``, "End-use refrigeration demand"
    ``Qcs0_kW``, "Nominal Total cooling demand."
    ``Qcs_dis_ls0_kW``, "Nominal Cooling distribution losses."
    ``Qcs_dis_ls_MWhyr``, "Cooling distribution losses"
    ``Qcs_em_ls0_kW``, "Nominal Cooling emission losses."
    ``Qcs_em_ls_MWhyr``, "Cooling emission losses"
    ``Qcs_lat_ahu0_kW``, "Nominal AHU latent cooling demand."
    ``Qcs_lat_ahu_MWhyr``, "AHU latent cooling demand"
    ``Qcs_lat_aru0_kW``, "Nominal ARU latent cooling demand."
    ``Qcs_lat_aru_MWhyr``, "ARU latent cooling demand"
    ``Qcs_lat_sys0_kW``, "Nominal System latent cooling demand."
    ``Qcs_lat_sys_MWhyr``, "Latent cooling demand"
    ``Qcs_MWhyr``, "Total cooling demand"
    ``Qcs_sen_ahu0_kW``, "Nominal AHU system cooling demand."
    ``Qcs_sen_ahu_MWhyr``, "AHU system cooling demand"
    ``Qcs_sen_aru0_kW``, "Nominal ARU system cooling demand."
    ``Qcs_sen_aru_MWhyr``, "ARU system cooling demand"
    ``Qcs_sen_scu0_kW``, "Nominal SCU system cooling demand."
    ``Qcs_sen_scu_MWhyr``, "SCU system cooling demand"
    ``Qcs_sen_sys0_kW``, "Nominal Sensible system cooling demand."
    ``Qcs_sen_sys_MWhyr``, "Sensible system cooling demand"
    ``Qcs_sys0_kW``, "Nominal end-use space cooling demand"
    ``Qcs_sys_ahu0_kW``, "Nominal AHU system cooling demand."
    ``Qcs_sys_ahu_MWhyr``, "AHU system cooling demand"
    ``Qcs_sys_aru0_kW``, "Nominal ARU system cooling demand."
    ``Qcs_sys_aru_MWhyr``, "ARU system cooling demand"
    ``Qcs_sys_MWhyr``, "End-use space cooling demand, Qcs_sys = Qcs_sen_sys + Qcs_lat_sys + Qcs_em_ls + Qcs_dis_ls"
    ``Qcs_sys_scu0_kW``, "Nominal SCU system cooling demand."
    ``Qcs_sys_scu_MWhyr``, "SCU system cooling demand"
    ``QH_sys0_kW``, "Nominal total building heating demand."
    ``QH_sys_MWhyr``, "Total energy demand for heating"
    ``Qhpro_sys0_kW``, "Nominal process heating demand."
    ``Qhpro_sys_MWhyr``, "Yearly processes heating demand."
    ``Qhs0_kW``, "Nominal Total heating demand."
    ``Qhs_dis_ls0_kW``, "Nominal Heating system distribution losses."
    ``Qhs_dis_ls_MWhyr``, "Heating system distribution losses"
    ``Qhs_em_ls0_kW``, "Nominal Heating emission losses."
    ``Qhs_em_ls_MWhyr``, "Heating system emission losses"
    ``Qhs_lat_ahu0_kW``, "Nominal AHU latent heating demand."
    ``Qhs_lat_ahu_MWhyr``, "AHU latent heating demand"
    ``Qhs_lat_aru0_kW``, "Nominal ARU latent heating demand."
    ``Qhs_lat_aru_MWhyr``, "ARU latent heating demand"
    ``Qhs_lat_sys0_kW``, "Nominal System latent heating demand."
    ``Qhs_lat_sys_MWhyr``, "System latent heating demand"
    ``Qhs_MWhyr``, "Total heating demand"
    ``Qhs_sen_ahu0_kW``, "Nominal AHU sensible heating demand."
    ``Qhs_sen_ahu_MWhyr``, "Sensible heating demand in AHU"
    ``Qhs_sen_aru0_kW``, "ARU sensible heating demand"
    ``Qhs_sen_aru_MWhyr``, "ARU sensible heating demand"
    ``Qhs_sen_shu0_kW``, "Nominal SHU sensible heating demand."
    ``Qhs_sen_shu_MWhyr``, "SHU sensible heating demand"
    ``Qhs_sen_sys0_kW``, "Nominal HVAC systems sensible heating demand."
    ``Qhs_sen_sys_MWhyr``, "Sensible heating demand"
    ``Qhs_sys0_kW``, "Nominal end-use space heating demand"
    ``Qhs_sys_ahu0_kW``, "Nominal AHU sensible heating demand."
    ``Qhs_sys_ahu_MWhyr``, "AHU system heating demand"
    ``Qhs_sys_aru0_kW``, "Nominal ARU sensible heating demand."
    ``Qhs_sys_aru_MWhyr``, "ARU sensible heating demand"
    ``Qhs_sys_MWhyr``, "End-use space heating demand, Qhs_sys = Qhs_sen_sys + Qhs_em_ls + Qhs_dis_ls"
    ``Qhs_sys_shu0_kW``, "Nominal SHU sensible heating demand."
    ``Qhs_sys_shu_MWhyr``, "SHU sensible heating demand"
    ``Qww0_kW``, "Nominal DHW heating demand."
    ``Qww_MWhyr``, "DHW heating demand"
    ``Qww_sys0_kW``, "Nominal end-use hotwater demand"
    ``Qww_sys_MWhyr``, "End-use hotwater demand"
    ``SOLAR_hs0_kW``, "Nominal solar thermal energy requirement for space heating supply"
    ``SOLAR_hs_MWhyr``, "Solar thermal energy requirement for space heating supply"
    ``SOLAR_ww0_kW``, "Nominal solar thermal energy requirement for hotwater supply"
    ``SOLAR_ww_MWhyr``, "Solar thermal energy requirement for hotwater supply"
    ``WOOD_hs0_kW``, "Nominal WOOD requirement for space heating supply"
    ``WOOD_hs_MWhyr``, "WOOD requirement for space heating supply"
    ``WOOD_ww0_kW``, "Nominal WOOD requirement for hotwater supply"
    ``WOOD_ww_MWhyr``, "WOOD requirement for hotwater supply"
    


get_water_body_potential
------------------------

path: ``outputs/data/potentials/Water_body_potential.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``QLake_kW``, "thermal potential from water body"
    ``Ts_C``, "average temperature of the water body"
    


get_weather_file
----------------

path: ``inputs/weather/weather.epw``

The following file is used by these scripts: ``decentralized``, ``demand``, ``optimization``, ``photovoltaic``, ``photovoltaic_thermal``, ``radiation``, ``schedule_maker``, ``shallow_geothermal_potential``, ``solar_collector``, ``thermal_network``


.. csv-table::
    :header: "Variable", "Description"

    ``aerosol_opt_thousandths (index = 29)``, "TODO"
    ``Albedo (index = 32)``, "TODO"
    ``atmos_Pa (index = 9)``, "TODO"
    ``ceiling_hgt_m (index = 25)``, "TODO"
    ``datasource (index = 5)``, "TODO"
    ``day (index = 2)``, "TODO"
    ``days_last_snow (index = 31)``, "TODO"
    ``dewpoint_C (index = 7)``, "TODO"
    ``difhorillum_lux (index = 18)``, "TODO"
    ``difhorrad_Whm2 (index = 15)``, "TODO"
    ``dirnorillum_lux (index = 17)``, "TODO"
    ``dirnorrad_Whm2 (index = 14)``, "TODO"
    ``drybulb_C (index = 6)``, "TODO"
    ``extdirrad_Whm2 (index = 11)``, "TODO"
    ``exthorrad_Whm2 (index = 10)``, "TODO"
    ``glohorillum_lux (index = 16)``, "TODO"
    ``glohorrad_Whm2 (index = 13)``, "TODO"
    ``horirsky_Whm2 (index = 12)``, "TODO"
    ``hour (index = 3)``, "TODO"
    ``liq_precip_depth_mm (index = 33)``, "TODO"
    ``liq_precip_rate_Hour (index = 34)``, "TODO"
    ``minute (index = 4)``, "TODO"
    ``month (index = 1)``, "TODO"
    ``opaqskycvr_tenths (index = 23)``, "TODO"
    ``precip_wtr_mm (index = 28)``, "TODO"
    ``presweathcodes (index = 27)``, "TODO"
    ``presweathobs (index = 26)``, "TODO"
    ``relhum_percent (index = 8)``, "TODO"
    ``snowdepth_cm (index = 30)``, "TODO"
    ``totskycvr_tenths (index = 22)``, "TODO"
    ``visibility_km (index = 24)``, "TODO"
    ``winddir_deg (index = 20)``, "TODO"
    ``windspd_ms (index = 21)``, "TODO"
    ``year (index = 0)``, "TODO"
    ``zenlum_lux (index = 19)``, "TODO"
    


PV_metadata_results
-------------------

path: ``outputs/data/potentials/solar/B001_PV_sensors.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``area_installed_module_m2``, "The area of the building surface covered by one solar panel"
    ``AREA_m2``, "Surface area."
    ``array_spacing_m``, "Spacing between solar arrays."
    ``B_deg``, "Tilt angle of the installed solar panels"
    ``BUILDING``, "Unique building ID. It must start with a letter."
    ``CATB``, "Category according to the tilt angle of the panel"
    ``CATGB``, "Category according to the annual radiation on the panel surface"
    ``CATteta_z``, "Category according to the surface azimuth of the panel"
    ``intersection``, "flag to indicate whether this surface is intersecting with another surface (0: no intersection, 1: intersected)"
    ``orientation``, "Orientation of the surface (north/east/south/west/top)"
    ``SURFACE``, "Unique surface ID for each building exterior surface."
    ``surface``, "Unique surface ID for each building exterior surface."
    ``surface_azimuth_deg``, "Azimuth angle of the panel surface e.g. south facing = 180 deg"
    ``tilt_deg``, "Tilt angle of roof or walls"
    ``total_rad_Whm2``, "Total radiatiative potential of a given surfaces area."
    ``TYPE``, "Surface typology."
    ``type_orientation``, "Concatenated surface type and orientation."
    ``Xcoor``, "Describes the position of the x vector."
    ``Xdir``, "Directional scalar of the x vector."
    ``Ycoor``, "Describes the position of the y vector."
    ``Ydir``, "Directional scalar of the y vector."
    ``Zcoor``, "Describes the position of the z vector."
    ``Zdir``, "Directional scalar of the z vector."
    


PV_results
----------

path: ``outputs/data/potentials/solar/B001_PV.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Area_PV_m2``, "Total area of investigated collector."
    ``Date``, "Date and time in hourly steps."
    ``E_PV_gen_kWh``, "Total electricity generated by the collector."
    ``PV_roofs_top_E_kWh``, "Electricity production from photovoltaic panels on roof tops"
    ``PV_roofs_top_m2``, "Collector surface area on roof tops."
    ``PV_walls_east_E_kWh``, "Electricity production from photovoltaic panels on east facades"
    ``PV_walls_east_m2``, "Collector surface area on east facades."
    ``PV_walls_north_E_kWh``, "Electricity production from photovoltaic panels on north facades"
    ``PV_walls_north_m2``, "Collector surface area on north facades."
    ``PV_walls_south_E_kWh``, "Electricity production from photovoltaic panels on south facades"
    ``PV_walls_south_m2``, "Collector surface area on south facades."
    ``PV_walls_west_E_kWh``, "Electricity production from photovoltaic panels on west facades"
    ``PV_walls_west_m2``, "West facing wall collector surface area."
    ``radiation_kWh``, "Total radiatiative potential."
    


PV_total_buildings
------------------

path: ``outputs/data/potentials/solar/PV_total_buildings.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Area_PV_m2``, "Total area of investigated collector."
    ``E_PV_gen_kWh``, "Total electricity generated by the collector."
    ``Name``, "Unique building ID. It must start with a letter."
    ``PV_roofs_top_E_kWh``, "Electricity production from photovoltaic panels on roof tops"
    ``PV_roofs_top_m2``, "Collector surface area on roof tops."
    ``PV_walls_east_E_kWh``, "Electricity production from photovoltaic panels on east facades"
    ``PV_walls_east_m2``, "Collector surface area on east facades."
    ``PV_walls_north_E_kWh``, "Electricity production from photovoltaic panels on north facades"
    ``PV_walls_north_m2``, "Collector surface area on north facades."
    ``PV_walls_south_E_kWh``, "Electricity production from photovoltaic panels on south facades"
    ``PV_walls_south_m2``, "Collector surface area on south facades."
    ``PV_walls_west_E_kWh``, "Electricity production from photovoltaic panels on west facades"
    ``PV_walls_west_m2``, "West facing wall collector surface area."
    ``radiation_kWh``, "Total radiatiative potential."
    


PV_totals
---------

path: ``outputs/data/potentials/solar/PV_total.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Area_PV_m2``, "Total area of investigated collector."
    ``Date``, "Date and time in hourly steps."
    ``E_PV_gen_kWh``, "Total electricity generated by the collector."
    ``PV_roofs_top_E_kWh``, "Electricity production from photovoltaic panels on roof tops"
    ``PV_roofs_top_m2``, "Collector surface area on roof tops."
    ``PV_walls_east_E_kWh``, "Electricity production from photovoltaic panels on east facades"
    ``PV_walls_east_m2``, "Collector surface area on east facades."
    ``PV_walls_north_E_kWh``, "Electricity production from photovoltaic panels on north facades"
    ``PV_walls_north_m2``, "Collector surface area on north facades."
    ``PV_walls_south_E_kWh``, "Electricity production from photovoltaic panels on south facades"
    ``PV_walls_south_m2``, "Collector surface area on south facades."
    ``PV_walls_west_E_kWh``, "Electricity production from photovoltaic panels on west facades"
    ``PV_walls_west_m2``, "West facing wall collector surface area."
    ``radiation_kWh``, "Total radiatiative potential."
    


PVT_metadata_results
--------------------

path: ``outputs/data/potentials/solar/B001_PVT_sensors.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``area_installed_module_m2``, "The area of the building surface covered by one solar panel"
    ``AREA_m2``, "Surface area."
    ``array_spacing_m``, "Spacing between solar arrays."
    ``B_deg``, "Tilt angle of the installed solar panels"
    ``BUILDING``, "Unique building ID. It must start with a letter."
    ``CATB``, "Category according to the tilt angle of the panel"
    ``CATGB``, "Category according to the annual radiation on the panel surface"
    ``CATteta_z``, "Category according to the surface azimuth of the panel"
    ``intersection``, "flag to indicate whether this surface is intersecting with another surface (0: no intersection, 1: intersected)"
    ``orientation``, "Orientation of the surface (north/east/south/west/top)"
    ``SURFACE``, "Unique surface ID for each building exterior surface."
    ``surface``, "Unique surface ID for each building exterior surface."
    ``surface_azimuth_deg``, "Azimuth angle of the panel surface e.g. south facing = 180 deg"
    ``tilt_deg``, "Tilt angle of roof or walls"
    ``total_rad_Whm2``, "Total radiatiative potential of a given surfaces area."
    ``TYPE``, "Surface typology."
    ``type_orientation``, "Concatenated surface type and orientation."
    ``Xcoor``, "Describes the position of the x vector."
    ``Xdir``, "Directional scalar of the x vector."
    ``Ycoor``, "Describes the position of the y vector."
    ``Ydir``, "Directional scalar of the y vector."
    ``Zcoor``, "Describes the position of the z vector."
    ``Zdir``, "Directional scalar of the z vector."
    


PVT_results
-----------

path: ``outputs/data/potentials/solar/B001_PVT.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Area_PVT_m2``, "Total area of investigated collector."
    ``Date``, "Date and time in hourly steps."
    ``E_PVT_gen_kWh``, "Total electricity generated by the collector."
    ``Eaux_PVT_kWh``, "Auxiliary electricity consumed by the collector."
    ``mcp_PVT_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector."
    ``PVT_roofs_top_E_kWh``, "Electricity production from photovoltaic-thermal panels on roof tops"
    ``PVT_roofs_top_m2``, "Collector surface area on roof tops."
    ``PVT_roofs_top_Q_kWh``, "Heat production from photovoltaic-thermal panels on roof tops"
    ``PVT_walls_east_E_kWh``, "Electricity production from photovoltaic-thermal panels on east facades"
    ``PVT_walls_east_m2``, "Collector surface area on east facades."
    ``PVT_walls_east_Q_kWh``, "Heat production from photovoltaic-thermal panels on east facades"
    ``PVT_walls_north_E_kWh``, "Electricity production from photovoltaic-thermal panels on north facades"
    ``PVT_walls_north_m2``, "Collector surface area on north facades."
    ``PVT_walls_north_Q_kWh``, "Heat production from photovoltaic-thermal panels on north facades"
    ``PVT_walls_south_E_kWh``, "Electricity production from photovoltaic-thermal panels on south facades"
    ``PVT_walls_south_m2``, "Collector surface area on south facades."
    ``PVT_walls_south_Q_kWh``, "Heat production from photovoltaic-thermal panels on south facades"
    ``PVT_walls_west_E_kWh``, "Electricity production from photovoltaic-thermal panels on west facades"
    ``PVT_walls_west_m2``, "West facing wall collector surface area."
    ``PVT_walls_west_Q_kWh``, "Heat production from photovoltaic-thermal panels on west facades"
    ``Q_PVT_gen_kWh``, "Total heat generated by the collector."
    ``Q_PVT_l_kWh``, "Collector heat loss."
    ``radiation_kWh``, "Total radiatiative potential."
    ``T_PVT_re_C``, "Collector hot water return temperature."
    ``T_PVT_sup_C``, "Collector heating supply temperature."
    


PVT_total_buildings
-------------------

path: ``outputs/data/potentials/solar/PVT_total_buildings.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Area_PVT_m2``, "Total area of investigated collector."
    ``E_PVT_gen_kWh``, "Total electricity generated by the collector."
    ``Eaux_PVT_kWh``, "Auxiliary electricity consumed by the collector."
    ``Name``, "Unique building ID."
    ``PVT_roofs_top_E_kWh``, "Electricity production from photovoltaic-thermal panels on roof tops"
    ``PVT_roofs_top_m2``, "Collector surface area on roof tops."
    ``PVT_roofs_top_Q_kWh``, "Heat production from photovoltaic-thermal panels on roof tops"
    ``PVT_walls_east_E_kWh``, "Electricity production from photovoltaic-thermal panels on east facades"
    ``PVT_walls_east_m2``, "Collector surface area on east facades."
    ``PVT_walls_east_Q_kWh``, "Heat production from photovoltaic-thermal panels on east facades"
    ``PVT_walls_north_E_kWh``, "Electricity production from photovoltaic-thermal panels on north facades"
    ``PVT_walls_north_m2``, "Collector surface area on north facades."
    ``PVT_walls_north_Q_kWh``, "Heat production from photovoltaic-thermal panels on north facades"
    ``PVT_walls_south_E_kWh``, "Electricity production from photovoltaic-thermal panels on south facades"
    ``PVT_walls_south_m2``, "Collector surface area on south facades."
    ``PVT_walls_south_Q_kWh``, "Heat production from photovoltaic-thermal panels on south facades"
    ``PVT_walls_west_E_kWh``, "Electricity production from photovoltaic-thermal panels on west facades"
    ``PVT_walls_west_m2``, "West facing wall collector surface area."
    ``PVT_walls_west_Q_kWh``, "Heat production from photovoltaic-thermal panels on west facades"
    ``Q_PVT_gen_kWh``, "Total heat generated by the collector."
    ``Q_PVT_l_kWh``, "Collector heat loss."
    ``radiation_kWh``, "Total radiatiative potential."
    


PVT_totals
----------

path: ``outputs/data/potentials/solar/PVT_total.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Area_PVT_m2``, "Total area of investigated collector."
    ``Date``, "Date and time in hourly steps."
    ``E_PVT_gen_kWh``, "Total electricity generated by the collector."
    ``Eaux_PVT_kWh``, "Auxiliary electricity consumed by the collector."
    ``mcp_PVT_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector."
    ``PVT_roofs_top_E_kWh``, "Electricity production from photovoltaic-thermal panels on roof tops"
    ``PVT_roofs_top_m2``, "Collector surface area on roof tops."
    ``PVT_roofs_top_Q_kWh``, "Heat production from photovoltaic-thermal panels on roof tops"
    ``PVT_walls_east_E_kWh``, "Electricity production from photovoltaic-thermal panels on east facades"
    ``PVT_walls_east_m2``, "Collector surface area on east facades."
    ``PVT_walls_east_Q_kWh``, "Heat production from photovoltaic-thermal panels on east facades"
    ``PVT_walls_north_E_kWh``, "Electricity production from photovoltaic-thermal panels on north facades"
    ``PVT_walls_north_m2``, "Collector surface area on north facades."
    ``PVT_walls_north_Q_kWh``, "Heat production from photovoltaic-thermal panels on north facades"
    ``PVT_walls_south_E_kWh``, "Electricity production from photovoltaic-thermal panels on south facades"
    ``PVT_walls_south_m2``, "Collector surface area on south facades."
    ``PVT_walls_south_Q_kWh``, "Heat production from photovoltaic-thermal panels on south facades"
    ``PVT_walls_west_E_kWh``, "Electricity production from photovoltaic-thermal panels on west facades"
    ``PVT_walls_west_m2``, "West facing wall collector surface area."
    ``PVT_walls_west_Q_kWh``, "Heat production from photovoltaic-thermal panels on west facades"
    ``Q_PVT_gen_kWh``, "Total heat generated by the collector."
    ``Q_PVT_l_kWh``, "Collector heat loss."
    ``radiation_kWh``, "Total radiatiative potential."
    ``T_PVT_re_C``, "Collector heating supply temperature."
    ``T_PVT_sup_C``, "Collector heating supply temperature."
    


SC_metadata_results
-------------------

path: ``outputs/data/potentials/solar/B001_SC_ET_sensors.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``area_installed_module_m2``, "The area of the building surface covered by one solar panel"
    ``AREA_m2``, "Surface area."
    ``array_spacing_m``, "Spacing between solar arrays."
    ``B_deg``, "Tilt angle of the installed solar panels"
    ``BUILDING``, "Unique building ID. It must start with a letter."
    ``CATB``, "Category according to the tilt angle of the panel"
    ``CATGB``, "Category according to the annual radiation on the panel surface"
    ``CATteta_z``, "Category according to the surface azimuth of the panel"
    ``intersection``, "flag to indicate whether this surface is intersecting with another surface (0: no intersection, 1: intersected)"
    ``orientation``, "Orientation of the surface (north/east/south/west/top)"
    ``SURFACE``, "Unique surface ID for each building exterior surface."
    ``surface``, "Unique surface ID for each building exterior surface."
    ``surface_azimuth_deg``, "Azimuth angle of the panel surface e.g. south facing = 180 deg"
    ``tilt_deg``, "Tilt angle of roof or walls"
    ``total_rad_Whm2``, "Total radiatiative potential of a given surfaces area."
    ``TYPE``, "Surface typology."
    ``type_orientation``, "Concatenated surface type and orientation."
    ``Xcoor``, "Describes the position of the x vector."
    ``Xdir``, "Directional scalar of the x vector."
    ``Ycoor``, "Describes the position of the y vector."
    ``Ydir``, "Directional scalar of the y vector."
    ``Zcoor``, "Describes the position of the z vector."
    ``Zdir``, "Directional scalar of the z vector."
    


SC_results
----------

path: ``outputs/data/potentials/solar/B001_SC_ET.csv``

The following file is used by these scripts: ``decentralized``


.. csv-table::
    :header: "Variable", "Description"

    ``Area_SC_m2``, "Total area of investigated collector."
    ``Date``, "Date and time in hourly steps."
    ``Eaux_SC_kWh``, "Auxiliary electricity consumed by the collector."
    ``mcp_SC_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector."
    ``Q_SC_gen_kWh``, "Total heat generated by the collector."
    ``Q_SC_l_kWh``, "Collector heat loss."
    ``radiation_kWh``, "Total radiatiative potential."
    ``SC_ET_roofs_top_m2``, "Collector surface area on roof tops."
    ``SC_ET_roofs_top_Q_kWh``, "Heat production from solar collectors on roof tops"
    ``SC_ET_walls_east_m2``, "Collector surface area on east facades."
    ``SC_ET_walls_east_Q_kWh``, "Heat production from solar collectors on east facades"
    ``SC_ET_walls_north_m2``, "Collector surface area on north facades."
    ``SC_ET_walls_north_Q_kWh``, "Heat production from solar collectors on north facades"
    ``SC_ET_walls_south_m2``, "Collector surface area on south facades."
    ``SC_ET_walls_south_Q_kWh``, "Heat production from solar collectors on south facades"
    ``SC_ET_walls_west_m2``, "Collector surface area on west facades."
    ``SC_ET_walls_west_Q_kWh``, "Heat production from solar collectors on west facades"
    ``T_SC_re_C``, "Collector hot water return temperature."
    ``T_SC_sup_C``, "Collector hot water supply temperature."
    


SC_total_buildings
------------------

path: ``outputs/data/potentials/solar/SC_ET_total_buildings.csv``

The following file is used by these scripts: 


.. csv-table::
    :header: "Variable", "Description"

    ``Area_SC_m2``, "Total area of investigated collector."
    ``Eaux_SC_kWh``, "Auxiliary electricity consumed by the collector."
    ``Name``, "Unique building ID."
    ``Q_SC_gen_kWh``, "Total heat generated by the collector."
    ``Q_SC_l_kWh``, "Collector heat loss."
    ``radiation_kWh``, "Total radiatiative potential."
    ``SC_ET_roofs_top_m2``, "Roof top collector surface area."
    ``SC_ET_roofs_top_Q_kWh``, "Heat production from solar collectors on roof tops"
    ``SC_ET_walls_east_m2``, "East facing wall collector surface area."
    ``SC_ET_walls_east_Q_kWh``, "Heat production from solar collectors on east facades"
    ``SC_ET_walls_north_m2``, "North facing wall collector surface area."
    ``SC_ET_walls_north_Q_kWh``, "Heat production from solar collectors on west facades"
    ``SC_ET_walls_south_m2``, "South facing wall collector surface area."
    ``SC_ET_walls_south_Q_kWh``, "Heat production from solar collectors on south facades"
    ``SC_ET_walls_west_m2``, "West facing wall collector surface area."
    ``SC_ET_walls_west_Q_kWh``, "Heat production from solar collectors on west facades"
    


SC_totals
---------

path: ``outputs/data/potentials/solar/SC_FP_total.csv``

The following file is used by these scripts: ``optimization``


.. csv-table::
    :header: "Variable", "Description"

    ``Area_SC_m2``, "Collector surface area on south facades."
    ``Date``, "Date and time in hourly steps."
    ``Eaux_SC_kWh``, "Auxiliary electricity consumed by the collector."
    ``mcp_SC_kWperC``, "Capacity flow rate (mass flow* specific heat capacity) of the hot water delivered by the collector."
    ``Q_SC_gen_kWh``, "Total heat generated by the collector."
    ``Q_SC_l_kWh``, "Collector heat loss."
    ``radiation_kWh``, "Total radiatiative potential."
    ``SC_FP_roofs_top_m2``, "Collector surface area on roof tops."
    ``SC_FP_roofs_top_Q_kWh``, "Heat production from solar collectors on roof tops"
    ``SC_FP_walls_east_m2``, "Collector surface area on east facades."
    ``SC_FP_walls_east_Q_kWh``, "Heat production from solar collectors on east facades"
    ``SC_FP_walls_north_m2``, "Collector surface area on north facades."
    ``SC_FP_walls_north_Q_kWh``, "Heat production from solar collectors on north facades"
    ``SC_FP_walls_south_m2``, "Collector surface area on south facades."
    ``SC_FP_walls_south_Q_kWh``, "Heat production from solar collectors on south facades"
    ``SC_FP_walls_west_m2``, "Collector surface area on west facades."
    ``SC_FP_walls_west_Q_kWh``, "Heat production from solar collectors on west facades"
    ``T_SC_re_C``, "Collector hot water return temperature."
    ``T_SC_sup_C``, "Collector hot water supply temperature."
    

