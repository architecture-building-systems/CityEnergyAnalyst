"""
Read and summarise CEA results over all scenarios in a project.

"""

import os
import pandas as pd
import subprocess
import sys

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



def exec_read_and_summarise(config, cea_scenario):
    """
    read and summarise the "useful" CEA results one after another: demand, emissions, costs, potentials, thermal-network

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return:
    """

    # paths to results
    demand_path = os.path.join(cea_scenario, 'outputs/data/demand/Total_demand.csv')

    lca_embodied_path = os.path.join(cea_scenario, 'outputs/data/emissions/Total_LCA_embodied.csv')
    lca_operation_path = os.path.join(cea_scenario, 'outputs/data/emissions/Total_LCA_operation.csv')

    cost_path = os.path.join(cea_scenario, 'outputs/data/costs/supply_system_costs_today.csv')

    shallow_geothermal_path = os.path.join(cea_scenario, 'outputs/data/potentials/Shallow_geothermal_potential.csv')
    sewage_heat_path = os.path.join(cea_scenario, 'outputs/data/potentials/Sewage_heat_potential.csv')
    water_body_path = os.path.join(cea_scenario, 'outputs/data/potentials/Water_body_potential.csv')

    pv_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/PV_PV1_total_buildings.csv')
    pvt_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/PVT_total_buildings.csv')
    sc_et_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/SC_ET_total_buildings.csv')
    sc_fp_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/SC_FP_total_buildings.csv')

    dc_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/solar/DC__plant_thermal_load_kW.csv')
    dc_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/solar/DC__plant_pumping_load_kW.csv')
    dh_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/solar/DH__plant_thermal_load_kW.csv')
    dh_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/solar/DH__plant_pumping_load_kW.csv')

    # create an empty DataFrame to store all the results
    summary_df = pd.DataFrame([cea_scenario], columns=['scenario_name'])

    # read and summarise: demand
    demand_df = pd.read_csv(demand_path)
    summary_df['conditioned_floor_area[Af_m2]'] = demand_df['Af_m2'].sum()
    summary_df['roof_area[Aroof_m2]'] = demand_df['Aroof_m2'].sum()
    summary_df['gross_floor_area[GFA_m2]'] = demand_df['GFA_m2'].sum()
    summary_df['occupied_floor_area[Aocc_m2]'] = demand_df['Aocc_m2'].sum()
    summary_df['nominal_occupancy[people0]'] = demand_df['people0'].sum()
    summary_df['grid_electricity_consumption[GRID_MWhyr]'] = demand_df['GRID_MWhyr'].sum()
    summary_df['enduse_total_electricity_consumption[E_sys_MWhyr]'] = demand_df['E_sys_MWhyr'].sum()
    summary_df['enduse_total_cooling_demand[QC_sys_MWhyr]'] = demand_df['QC_sys_MWhyr'].sum()
    summary_df['enduse_total_space_cooling_demand[Qcs_sys_MWhyr]'] = demand_df['Qcs_sys_MWhyr'].sum()
    summary_df['enduse_total_heating_demand[QH_sys_MWhyr]'] = demand_df['QH_sys_MWhyr'].sum()
    summary_df['enduse_total_space_heating_demand[Qhs_MWhyr]'] = demand_df['Qhs_MWhyr'].sum()
    summary_df['enduse_total_dhw_demand[Qww_MWhyr]'] = demand_df['Qww_MWhyr'].sum()

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
    project_boolean = config.result_reader_summary.all_scenarios

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
        summary_scenario_df = exec_read_and_summarise(config, cea_scenario)
        summary_scenario_df['scenario_name'] = scenario
        summary_project_df = pd.concat([summary_project_df, summary_scenario_df])

    # write the results
    summary_project_df = summary_project_df.reset_index(drop=True)
    summary_project_path = os.path.join(config.general.project, 'project_result_summary.csv')
    summary_project_df.to_csv(summary_project_path)

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of read-and-summarise is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())
