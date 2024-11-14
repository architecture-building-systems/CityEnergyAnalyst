"""
Read and summarise CEA results over all scenarios in a project.

"""

import os
import pandas as pd
import cea.config
import time

__author__ = "Zhongming Shi, Reynold Mok"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi, Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def exec_read_and_summarise(cea_scenario):
    """
    read and summarise the "useful" CEA results one after another: demand, emissions, potentials, thermal-network

    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return:
    :param summary_df: dataframe of the summarised results, indicating not found when not available
    :type summary_df: DataFrame
    """

    # create an empty DataFrame to store all the results
    summary_df = pd.DataFrame([cea_scenario], columns=['scenario_name'])

    # not found message to be reflected in the summary DataFrame
    na = float('Nan')
    # read and summarise: demand
    try:
        demand_path = os.path.join(cea_scenario, 'outputs/data/demand/Total_demand.csv')
        cea_result_df = pd.read_csv(demand_path)
        summary_df['conditioned_floor_area[Af_m2]'] = cea_result_df['Af_m2'].sum()
        summary_df['roof_area[Aroof_m2]'] = cea_result_df['Aroof_m2'].sum()
        summary_df['gross_floor_area[GFA_m2]'] = cea_result_df['GFA_m2'].sum()
        summary_df['occupied_floor_area[Aocc_m2]'] = cea_result_df['Aocc_m2'].sum()
        summary_df['nominal_occupancy[people0]'] = cea_result_df['people0'].sum()
        summary_df['grid_electricity_consumption[GRID_MWhyr]'] = cea_result_df['GRID_MWhyr'].sum()
        summary_df['enduse_electricity_consumption[E_sys_MWhyr]'] = cea_result_df['E_sys_MWhyr'].sum()
        summary_df['enduse_cooling_demand[QC_sys_MWhyr]'] = cea_result_df['QC_sys_MWhyr'].sum()
        summary_df['enduse_space_cooling_demand[Qcs_sys_MWhyr]'] = cea_result_df['Qcs_sys_MWhyr'].sum()
        summary_df['enduse_heating_demand[QH_sys_MWhyr]'] = cea_result_df['QH_sys_MWhyr'].sum()
        summary_df['enduse_space_heating_demand[Qhs_MWhyr]'] = cea_result_df['Qhs_MWhyr'].sum()
        summary_df['enduse_dhw_demand[Qww_MWhyr]'] = cea_result_df['Qww_MWhyr'].sum()

    except FileNotFoundError:
        summary_df['conditioned_floor_area[Af_m2]'] = na
        summary_df['roof_area[Aroof_m2]'] = na
        summary_df['gross_floor_area[GFA_m2]'] = na
        summary_df['occupied_floor_area[Aocc_m2]'] = na
        summary_df['nominal_occupancy[people0]'] = na
        summary_df['grid_electricity_consumption[GRID_MWhyr]'] = na
        summary_df['enduse_electricity_consumption[E_sys_MWhyr]'] = na
        summary_df['enduse_cooling_demand[QC_sys_MWhyr]'] = na
        summary_df['enduse_space_cooling_demand[Qcs_sys_MWhyr]'] = na
        summary_df['enduse_heating_demand[QH_sys_MWhyr]'] = na
        summary_df['enduse_space_heating_demand[Qhs_MWhyr]'] = na
        summary_df['enduse_dhw_demand[Qww_MWhyr]'] = na

    # read and summarise: emissions-embodied
    try:
        lca_embodied_path = os.path.join(cea_scenario, 'outputs/data/emissions/Total_LCA_embodied.csv')
        cea_result_df = pd.read_csv(lca_embodied_path)
        summary_df['embodied_emissions_building_construction[GHG_sys_embodied_tonCO2yr]'] = cea_result_df['GHG_sys_embodied_tonCO2yr'].sum()
        summary_df['embodied_emissions_building_construction_per_gross_floor_area[GHG_sys_embodied_kgCO2m2yr]'] = summary_df['embodied_emissions_building_construction[GHG_sys_embodied_tonCO2yr]']/cea_result_df['GFA_m2'].sum()*1000

    except FileNotFoundError:
        summary_df['embodied_emissions_building_construction[GHG_sys_embodied_tonCO2yr]'] = na
        summary_df['embodied_emissions_building_construction_per_gross_floor_area[GHG_sys_embodied_kgCO2m2yr]'] = na

    # read and summarise: emissions-operation
    try:
        lca_operation_path = os.path.join(cea_scenario, 'outputs/data/emissions/Total_LCA_operation.csv')
        cea_result_df = pd.read_csv(lca_operation_path)
        summary_df['operation_emissions[GHG_sys_tonCO2]'] = cea_result_df['GHG_sys_tonCO2'].sum()
        summary_df['operation_emissions_per_gross_floor_area[GHG_sys_kgCO2m2yr]'] = summary_df['operation_emissions[GHG_sys_tonCO2]']/cea_result_df['GFA_m2'].sum()*1000
        summary_df['operation_emissions_grid[GHG_sys_tonCO2]'] = cea_result_df['GRID_tonCO2'].sum()
        summary_df['operation_emissions_grid_per_gross_floor_area[GHG_sys_kgCO2m2yr]'] = summary_df['operation_emissions_grid[GHG_sys_tonCO2]']/cea_result_df['GFA_m2'].sum()*1000

    except FileNotFoundError:
        summary_df['operation_emissions[GHG_sys_tonCO2]'] = na
        summary_df['operation_emissions_per_gross_floor_area[GHG_sys_kgCO2m2yr]'] = na
        summary_df['operation_emissions_grid[GHG_sys_tonCO2]'] = na
        summary_df['operation_emissions_grid_per_gross_floor_area[GHG_sys_kgCO2m2yr]'] = na

    # read and summarise: pv
    pv_database_path = os.path.join(cea_scenario, 'inputs/technology/components/CONVERSION.xlsx')
    pv_database_df = pd.read_excel(pv_database_path, sheet_name="PHOTOVOLTAIC_PANELS")
    panel_types = list(set(pv_database_df['code']))
    for panel_type in panel_types:
        pv_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/PV_{panel_type}_total_buildings.csv'.format(panel_type=panel_type))

        try:
            cea_result_df = pd.read_csv(pv_path)
            summary_df[f'PV_{panel_type}_surface_area[Area_SC_m2]'.format(panel_type=panel_type)] = cea_result_df['Area_PV_m2'].sum()
            summary_df[f'PV_{panel_type}_electricity_generated[E_PV_gen_kWh]'.format(panel_type=panel_type)] = cea_result_df['E_PV_gen_kWh'].sum()

        except FileNotFoundError:
            summary_df[f'PV_{panel_type}_surface_area[Area_SC_m2]'.format(panel_type=panel_type)] = na
            summary_df[f'PV_{panel_type}_electricity_generated[E_PV_gen_kWh]'.format(panel_type=panel_type)] = na

    # read and summarise: pvt
    try:
        pvt_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/PVT_total_buildings.csv')
        cea_result_df = pd.read_csv(pvt_path)
        summary_df['PVT_surface_area[Area_PVT_m2]'] = cea_result_df['Area_PVT_m2'].sum()
        summary_df['PVT_electricity_generated[E_PVT_gen_kWh]'] = cea_result_df['E_PVT_gen_kWh'].sum()
        summary_df['PVT_heat_generated[Q_PVT_gen_kWh]'] = cea_result_df['Q_PVT_gen_kWh'].sum()

    except FileNotFoundError:
        summary_df['PVT_surface_area[Area_PVT_m2]'] = na
        summary_df['PVT_electricity_generated[E_PVT_gen_kWh]'] = na
        summary_df['PVT_heat_generated[Q_PVT_gen_kWh]'] = na

    # read and summarise: sc-et
    try:
        sc_et_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/SC_ET_total_buildings.csv')
        cea_result_df = pd.read_csv(sc_et_path)
        summary_df['SC_evacuated_tube_surface_area[Area_SC_m2]'] = cea_result_df['Area_SC_m2'].sum()
        summary_df['SC_evacuated_tube_heat_generated[Q_SC_gen_kWh]'] = cea_result_df['Q_SC_gen_kWh'].sum()

    except FileNotFoundError:
        summary_df['SC_evacuated_tube_surface_area[Area_SC_m2]'] = na
        summary_df['SC_evacuated_tube_heat_generated[Q_SC_gen_kWh]'] = na

    # read and summarise: sc-fp
    try:
        sc_fp_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/SC_FP_total_buildings.csv')
        cea_result_df = pd.read_csv(sc_fp_path)
        summary_df['SC_flat_plate_surface_area[Area_SC_m2]'] = cea_result_df['Area_SC_m2'].sum()
        summary_df['SC_flat_plate_tube_heat_generated[Q_SC_gen_kWh]'] = cea_result_df['Q_SC_gen_kWh'].sum()

    except FileNotFoundError:
        summary_df['SC_flat_plate_surface_area[Area_SC_m2]'] = na
        summary_df['SC_flat_plate_heat_generated[Q_SC_gen_kWh]'] = na

    # read and summarise: potentials shallow-geothermal
    try:
        shallow_geothermal_path = os.path.join(cea_scenario, 'outputs/data/potentials/Shallow_geothermal_potential.csv')
        cea_result_df = pd.read_csv(shallow_geothermal_path)
        summary_df['geothermal_heat_potential[QGHP_kWh]'] = cea_result_df['QGHP_kW'].sum()
        summary_df['area_for_ground_source_heat_pump[Area_avail_m2]'] = cea_result_df['Area_avail_m2'].mean()

    except FileNotFoundError:
        summary_df['geothermal_heat_potential[QGHP_kWh]'] = na
        summary_df['area_for_ground_source_heat_pump[Area_avail_m2]'] = na

    # read and summarise: potentials sewage heat
    try:
        sewage_heat_path = os.path.join(cea_scenario, 'outputs/data/potentials/Sewage_heat_potential.csv')
        cea_result_df = pd.read_csv(sewage_heat_path)
        summary_df['sewage_heat_potential[Qsw_kWh]'] = cea_result_df['Qsw_kW'].sum()

    except FileNotFoundError:
        summary_df['sewage_heat_potential[Qsw_kWh]'] = na

    # read and summarise: potentials water body
    try:
        water_body_path = os.path.join(cea_scenario, 'outputs/data/potentials/Water_body_potential.csv')
        cea_result_df = pd.read_csv(water_body_path)
        summary_df['water_body_heat_potential[QLake_kWh]'] = cea_result_df['QLake_kW'].sum()

    except FileNotFoundError:
        summary_df['water_body_heat_potential[QLake_kWh]'] = na

    # read and summarise: district heating plant - thermal
    try:
        dh_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DH__plant_thermal_load_kW.csv')
        cea_result_df = pd.read_csv(dh_plant_thermal_path)
        summary_df['DH_plant_thermal_load[thermal_load_kWh]'] = cea_result_df['thermal_load_kW'].sum()
        summary_df['DH_plant_power[thermal_load_kW]'] = cea_result_df['thermal_load_kW'].max()

    except FileNotFoundError:
        summary_df['DH_plant_thermal_load[thermal_load_kWh]'] = na
        summary_df['DH_plant_power[thermal_load_kW]'] = na

    # read and summarise: district heating plant - pumping
    try:
        dh_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DH__plant_pumping_load_kW.csv')
        cea_result_df = pd.read_csv(dh_plant_pumping_path)
        summary_df['DH_electricity_consumption_for_pressure_loss[pressure_loss_total_kWh]'] = cea_result_df['pressure_loss_total_kW'].sum()
        summary_df['DH_plant_pumping_power[pressure_loss_total_kW]'] = cea_result_df['pressure_loss_total_kW'].max()

    except FileNotFoundError:
        summary_df['DH_electricity_consumption_for_pressure_loss[pressure_loss_total_kWh]'] = na
        summary_df['DH_plant_pumping_power[pressure_loss_total_kW]'] = na

    # read and summarise: district cooling plant - thermal
    try:
        dc_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DC__plant_thermal_load_kW.csv')
        cea_result_df = pd.read_csv(dc_plant_thermal_path)
        summary_df['DC_plant_thermal_load[thermal_load_kWh]'] = cea_result_df['thermal_load_kW'].sum()
        summary_df['DC_plant_power[thermal_load_kW]'] = cea_result_df['thermal_load_kW'].max()

    except FileNotFoundError:
        summary_df['DC_plant_thermal_load[thermal_load_kWh]'] = na
        summary_df['DC_plant_power[thermal_load_kW]'] = na

    # read and summarise: district cooling plant - pumping
    try:
        dc_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/DC__plant_pumping_load_kW.csv')
        cea_result_df = pd.read_csv(dc_plant_pumping_path)
        summary_df['DC_electricity_consumption_for_pressure_loss[pressure_loss_total_kWh]'] = cea_result_df['pressure_loss_total_kW'].sum()
        summary_df['DC_plant_pumping_power[pressure_loss_total_kW]'] = cea_result_df['pressure_loss_total_kW'].max()

    except FileNotFoundError:
        summary_df['DC_electricity_consumption_for_pressure_loss[pressure_loss_total_kWh]'] = na
        summary_df['DC_plant_pumping_power[pressure_loss_total_kW]'] = na

    # return the summary DataFrame
    return summary_df

def main(config):
    """
    Read through and summarise CEA results for all scenarios under a project.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """

    # Start the timer
    t0 = time.perf_counter()

    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    project_path = config.general.project
    scenario_name = config.general.scenario_name
    project_boolean = config.result_summary.all_scenarios

    # deciding to run all scenarios or the current the scenario only
    if project_boolean:
        scenarios_list = os.listdir(project_path)
    else:
        scenarios_list = [scenario_name]

    # loop over one or all scenarios under the project
    summary_project_df = pd.DataFrame()
    for scenario in scenarios_list:
        # Ignore hidden directories
        if scenario.startswith('.') or os.path.isfile(os.path.join(project_path, scenario)):
            continue

        cea_scenario = os.path.join(project_path, scenario)
        print(f'Reading and summarising the CEA results for Scenario {cea_scenario}.')
        # executing CEA commands
        summary_scenario_df = exec_read_and_summarise(cea_scenario)
        summary_scenario_df['scenario_name'] = scenario
        summary_project_df = pd.concat([summary_project_df, summary_scenario_df])

    # write the results
    if project_boolean:
        summary_project_path = os.path.join(config.general.project, 'result_summary.csv')
        summary_project_df.to_csv(summary_project_path, index=False, float_format='%.2f')

    else:
        summary_scenario_path = os.path.join(project_path, scenario_name, '{scenario_name}_result_summary.csv'.format(scenario_name=scenario_name))
        summary_project_df.to_csv(summary_scenario_path, index=False, float_format='%.2f')


    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of read-and-summarise is now completed - time elapsed: %d.2 seconds' % time_elapsed)



if __name__ == '__main__':
    main(cea.config.Configuration())
