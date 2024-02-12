"""
Read CEA results over all scenarios in a project and produce commonly used UBEM metrics.
The list of UBEM metrics include:

    EUI: grid electricity / GFA [MWh/m2/yr]
    EUI: end-use electricity /GFA [MWh/m2/yr]
    EUI: end-use cooling / GFA [MWh/m2/yr] (for example, there is a data centre)
    EUI: end-use space cooling / GFA [MWh/m2/yr]
    EUI: end-use heating / GFA [MWh/m2/yr]
    EUI: end-use space heating / GFA [MWh/m2/yr]
    EUI: end-use domestic hot water / GFA [MWh/m2/yr]
    Solar energy penetration [-]
    Self-consumption [-]
    Self-sufficiency [-]
    Capacity factor: PV [-]
    Capacity factor: plant for DC or DH [-]
    Capacity factor: pump for DC or DH [-]
    ...
    (This list continues to grow as we are adding in more metrics.)

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


def calc_capacity_factor(sum_kWh, max_kW):
    """
    caculate the capacity factor of a device

    :param sum_kWh: sum of actual energy output over 8'760 hours
    :type sum_kWh: float
    :param max_kWh: max of power over 8760 hours
    :type max_kWh: float
    :return:
    :param capactiy_factor: the unitless ratio of actual energy output over a year to the theoretical maximum energy output over that period.
    :type capactiy_factor: float
    """
    capacity_factor = sum_kWh/ (max_kW * 8760)

    return capacity_factor


def calc_self_consumption(gen_kWh, demand_kWh):
    """
    caculate the capacity factor of a device

    :param gen_kWh_df: energy generation [kWh] by 8'760 rows (hours)
    :type gen_kWh_df: Series
    :param demand_kWh_df: energy load [kWh] by 8'760 rows (hours)
    :type demand_kWh_df: Series
    :return:
    :param self_consumption: the unitless ratio describing how much of the generated electricity can be consumed instantaneously on-site
    :type self_consumption: float
    """
    use = []
    for t in range(10):
        use.append(min(gen_kWh[t], demand_kWh[t]))

    self_consumption = sum(use) / gen_kWh.sum()

    return self_consumption


def calc_self_sufficiency(gen_kWh, demand_kWh):
    """
    caculate the capacity factor of a device

    :param gen_kWh_df:  energy generation [kWh] by 8'760 rows (hours)
    :type gen_kWh_df: Series
    :param demand_kWh_df: energy load [kWh] by 8'760 rows (hours)
    :type demand_kWh_df: Series
    :return:
    :param self_sufficiency: the unitless ratio describing how much of the electricity demand can be instantaneously met on-site
    :type self_sufficiency: float
    """
    use = []
    for t in range(10):
        use.append(min(gen_kWh[t], demand_kWh[t]))

    self_sufficiency = sum(use) / demand_kWh[t]

    return self_sufficiency


def exec_read_and_analyse(cea_scenario):
    """
    read the CEA results and calculates the UBEM metrics listed at the top of this script

    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return:
    :param analysis_df: dataframe of the metrics at the top of this script
    :type analysis_df: DataFrame
    """

    # create an empty DataFrame to store all the results
    analysis_df = pd.DataFrame([cea_scenario], columns=['scenario_name'])

    # not found message to be reflected in the analysis DataFrame
    na = 'missing CEA results'

    # metrics: EUI or energy demand-related
    try:
        demand_path = os.path.join(cea_scenario, 'outputs/data/demand/Total_demand.csv')
        cea_result_demand_df = pd.read_csv(demand_path)
        analysis_df['EUI - grid electricity [kWh/m2/yr]'] = cea_result_demand_df['GRID_MWhyr'].sum() / cea_result_demand_df['GFA_m2'].sum() * 1000
        analysis_df['EUI - enduse electricity [kWh/m2/yr]'] = cea_result_demand_df['E_sys_MWhyr'].sum().sum() / cea_result_demand_df['GFA_m2'].sum() * 1000
        analysis_df['EUI - cooling demand [kWh/m2/yr]'] = cea_result_demand_df['QC_sys_MWhyr'].sum() / cea_result_demand_df['GFA_m2'].sum() * 1000
        analysis_df['EUI - space cooling demand [kWh/m2/yr]'] = cea_result_demand_df['Qcs_sys_MWhyr'].sum() / cea_result_demand_df['GFA_m2'].sum() * 1000
        analysis_df['EUI - heating demand [kWh/m2/yr]'] = cea_result_demand_df['QH_sys_MWhyr'].sum() / cea_result_demand_df['GFA_m2'].sum() * 1000
        analysis_df['EUI - space heating demand [kWh/m2/yr]'] = cea_result_demand_df['Qhs_MWhyr'].sum() / cea_result_demand_df['GFA_m2'].sum() * 1000
        analysis_df['EUI - domestic hot water demand [kWh/m2/yr]'] = cea_result_demand_df['Qww_MWhyr'].sum() / cea_result_demand_df['GFA_m2'].sum() * 1000

        # metrics (excluding capacity factor): on-site solar energy use
        pv_database_path = os.path.join(cea_scenario, 'inputs/technology/components/CONVERSION.xlsx')
        pv_database_df = pd.read_excel(pv_database_path, sheet_name="PV")
        panel_types = list(set(pv_database_df['code']))
        for panel_type in panel_types:
            pv_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/PV_{panel_type}_total_buildings.csv'.format(panel_type=panel_type))

            try:
                cea_result_df = pd.read_csv(pv_path)
                analysis_df[f'PV_{panel_type}_energy_penetration[-]'.format(panel_type=panel_type)] = cea_result_df['E_PV_gen_kWh'].sum() / cea_result_demand_df['GRID_MWhyr'].sum()
                analysis_df[f'PV_{panel_type}_self_consumption[-]'.format(panel_type=panel_type)] = calc_self_consumption(cea_result_df['E_PV_gen_kWh'], cea_result_demand_df['GRID_MWhyr'])
                analysis_df[f'PV_{panel_type}_energy_sufficiency[-]'.format(panel_type=panel_type)] = calc_self_sufficiency(cea_result_df['E_PV_gen_kWh'], cea_result_demand_df['GRID_MWhyr'])

            except FileNotFoundError:
                analysis_df[f'PV_{panel_type}_energy_penetration[-]'.format(panel_type=panel_type)] = na
                analysis_df[f'PV_{panel_type}_self_consumption[-]'.format(panel_type=panel_type)] = na
                analysis_df[f'PV_{panel_type}_energy_sufficiency[-]'.format(panel_type=panel_type)] = na

    except FileNotFoundError:
        analysis_df['EUI - grid electricity [kWh/m2/yr]'] = na
        analysis_df['EUI - enduse electricity [kWh/m2/yr]'] = na
        analysis_df['EUI - cooling demand [kWh/m2/yr]'] = na
        analysis_df['EUI - space cooling demand [kWh/m2/yr]'] = na
        analysis_df['EUI - heating demand [kWh/m2/yr]'] = na
        analysis_df['EUI - space heating demand [kWh/m2/yr]'] = na
        analysis_df['EUI - domestic hot water demand [kWh/m2/yr]'] = na

        pv_database_path = os.path.join(cea_scenario, 'inputs/technology/components/CONVERSION.xlsx')
        pv_database_df = pd.read_excel(pv_database_path, sheet_name="PV")
        panel_types = list(set(pv_database_df['code']))
        for panel_type in panel_types:
            analysis_df[f'PV_{panel_type}_energy_penetration[-]'.format(panel_type=panel_type)] = na
            analysis_df[f'PV_{panel_type}_self_consumption[-]'.format(panel_type=panel_type)] = na
            analysis_df[f'PV_{panel_type}_energy_sufficiency[-]'.format(panel_type=panel_type)] = na

    # metric - capacity factor: on-site solar energy use
    pv_database_path = os.path.join(cea_scenario, 'inputs/technology/components/CONVERSION.xlsx')
    pv_database_df = pd.read_excel(pv_database_path, sheet_name="PV")
    panel_types = list(set(pv_database_df['code']))
    panel_effiency = list(set(pv_database_df['PV_n']))
    for n in range(len(panel_types)):
        panel_type=panel_types[n]
        pv_path = os.path.join(cea_scenario, 'outputs/data/potentials/solar/PV_{panel_type}_total_buildings.csv'.format(panel_type=panel_type))

        try:
            cea_result_df = pd.read_csv(pv_path)
            max_kW = cea_result_df['Area_PV_m2'] * panel_effiency[n]
            analysis_df[f'PV_{panel_type}_capacity_factor[-]'.format(panel_type=panel_type)] = calc_capacity_factor(cea_result_df['E_PV_gen_kWh'].sum(), max_kW)

        except FileNotFoundError:
            analysis_df[f'PV_{panel_type}_capacity_factor[-]'.format(panel_type=panel_type)] = na

    # metrics: district heating plant - thermal
    try:
        dh_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/solar/DH__plant_thermal_load_kW.csv')
        cea_result_df = pd.read_csv(dh_plant_thermal_path)
        analysis_df['DH_plant_capacity_factor[-]'] = calc_capacity_factor(cea_result_df['thermal_load_kW'].sum(), cea_result_df['thermal_load_kW'].max())

    except FileNotFoundError:
        analysis_df['DH_plant_capacity_factor[-]'] = na


    # metrics: district heating plant - pumping
    try:
        dh_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/solar/DH__plant_pumping_load_kW.csv')
        cea_result_df = pd.read_csv(dh_plant_pumping_path)
        analysis_df['DH_pump_capacity_factor[-]'] = calc_capacity_factor( cea_result_df['pressure_loss_total_kW'].sum(), cea_result_df['pressure_loss_total_kW'].max())

    except FileNotFoundError:
        analysis_df['DH_pump_capacity_factor[-]'] = na


    # metrics: district cooling plant - thermal
    try:
        dc_plant_thermal_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/solar/DC__plant_thermal_load_kW.csv')
        cea_result_df = pd.read_csv(dc_plant_thermal_path)
        analysis_df['DC_plant_capacity_factor[-]'] = calc_capacity_factor(cea_result_df['thermal_load_kW'].sum(), cea_result_df['thermal_load_kW'].max())

    except FileNotFoundError:
        analysis_df['DC_plant_capacity_factor[-]'] = na


    # metrics: district cooling plant - pumping
    try:
        dc_plant_pumping_path = os.path.join(cea_scenario, 'outputs/data/thermal-network/solar/DC__plant_pumping_load_kW.csv')
        cea_result_df = pd.read_csv(dc_plant_pumping_path)
        analysis_df['DC_pump_capacity_factor[-]'] = calc_capacity_factor(cea_result_df['pressure_loss_total_kW'].sum(), cea_result_df['pressure_loss_total_kW'].max())

    except FileNotFoundError:
        analysis_df['DC_pump_capacity_factor[-]'] = na


    # return analysis DataFrame
    return analysis_df


def main(config):
    """
    Read through CEA results for all scenarios under a project and generate UBEM metrics for quick analysis.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """

    # Start the timer
    t0 = time.perf_counter()

    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    project_path = config.general.project
    scenario_name = config.general.scenario_name
    project_boolean = config.result_reader_analysis.all_scenarios

    # deciding to run all scenarios or the current the scenario only
    if project_boolean:
        scenarios_list = os.listdir(project_path)
    else:
        scenarios_list = [scenario_name]

    # loop over one or all scenarios under the project
    analysis_project_df = pd.DataFrame()
    for scenario in scenarios_list:
        # Ignore hidden directories
        if scenario.startswith('.') or os.path.isfile(os.path.join(project_path, scenario)):
            continue

        cea_scenario = os.path.join(project_path, scenario)
        print(f'Reading and analysing the CEA results for Scenario {cea_scenario}.')
        # executing CEA commands
        analysis_scenario_df = exec_read_and_analyse(cea_scenario)
        analysis_scenario_df['scenario_name'] = scenario
        analysis_project_df = pd.concat([analysis_project_df, analysis_scenario_df])

    # write the results
    if project_boolean:
        analysis_project_path = os.path.join(config.general.project, 'result_analysis.csv')
        analysis_project_df.to_csv(analysis_project_path, index=False, float_format='%.2f')

    else:
        analysis_scenario_path = os.path.join(project_path, scenario_name, '{scenario_name}_result_analysis.csv'.format(scenario_name=scenario_name))
        analysis_project_df.to_csv(analysis_scenario_path, index=False, float_format='%.2f')


    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire process of read-and-analyse is now completed - time elapsed: %d.2 seconds' % time_elapsed)



if __name__ == '__main__':
    main(cea.config.Configuration())
