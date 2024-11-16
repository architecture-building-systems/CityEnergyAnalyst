"""
Read and summarise CEA results over all scenarios in a project.

"""

import os
import pandas as pd
import cea.config
import time
from datetime import datetime
import cea.inputlocator

__author__ = "Zhongming Shi, Reynold Mok"
__copyright__ = "Copyright 2024, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi, Reynold Mok"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def get_hours_start_end(config):

    # get the user-defined dates from config
    date_start = config.result_summary.period_start_date
    date_end = config.result_summary.period_end_date

    def check_user_period_validity(date):
        s = "".join(date)
        # Check for length, alphanumeric, and the presence of both letters and numbers
        return len(s) == 5 and s.isalnum() and any(c.isalpha() for c in s) and any(c.isdigit() for c in s)
    def check_user_period_impossible_date(date):
        list_impossible_dates = ['30Feb', '31Feb', '31Apr', '31Jun', '31Sep', '31Nov',
                                 'Feb30', 'Feb31', 'Apr31', 'Jun31', 'Sep31', 'Nov31']
        s = "".join(date)
        return s in list_impossible_dates

    def check_user_period_leap_date(date):
        list_leap_dates = ['29Feb', 'Feb29']
        s = "".join(date)
        return s in list_leap_dates

    def from_date_string_to_hours(date_str):
        # Define possible date formats to handle both "31Jan" and "Jan31"
        formats = ["%d%b", "%b%d"]

        # Try each format to parse the date
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        else:
            raise ValueError("Check start date or/and end date of the defined period.")

        # Calculate the day of the year (1-365)
        day_of_year = date_obj.timetuple().tm_yday

        # Calculate the Nth hour of the year
        hour_of_year = (day_of_year - 1) * 24  # (day - 1) because days start from hour 0, not 24

        return hour_of_year

    # validate start date
    if not check_user_period_validity(date_start):
        raise ValueError('Check the start date. Select one number and one month only.')

    elif check_user_period_impossible_date(date_start):
        raise ValueError('Check the start date. Ensure the combination is an actual date.')

    elif check_user_period_leap_date(date_start):
        raise ValueError('Check the start date. CEA does not consider 29 Feb in a leap year.')

    # validate end date
    if not check_user_period_validity(date_end):
        raise ValueError('Check the end date. Select one number and one month only.')

    elif check_user_period_impossible_date(date_end):
        raise ValueError('Check the end date. Ensure the combination is an actual date.')

    elif check_user_period_leap_date(date_end):
        raise ValueError('Check the end date. CEA does not consider 29 Feb in a leap year.')

    hour_start = from_date_string_to_hours(date_start) - 24 #Nth hour of the year, starting at 0, inclusive
    hour_end = from_date_string_to_hours(date_end)   #Nth hour of the year, ending at 8760, not-inclusive

    # determine the period
    if hour_end < hour_start:
        print("End date is earlier than Start date. CEA considers the period ending at the End date in the year after.")

    elif hour_end == hour_start:
        print("End date is the same as Start date. CEA considers the 24 hours this date.")

    else:
        print("End date is earlier than Start date. CEA considers the period between the two dates in the same year.")

    return hour_start, hour_end

def map_metrics_cea_features(list_metrics):

    dict = {
    "demand": ['conditioned_floor_area[m2]','roof_area[m2]','gross_floor_area[m2]','nominal_occupancy[-]',
               'grid_electricity_consumption[MWh]','enduse_electricity_consumption[MWh]',
               'enduse_cooling_demand[MWh]','enduse_space_cooling_demand[MWh]','enduse_heating_demand[MWh]',
               'enduse_space_heating_demand[MWh]','enduse_dhw_demand[MWh]'],
    "embodied_emissions": ['embodied_emissions_building_construction[tonCO2-eq/yr]'],
    "operation_emissions": ['operation_emissions[tonCO2-eq/yr]', 'operation_emissions_grid[tonCO2-eq/yr]'],
    "pv": ['pv_installed_area_total[m2]','pv_electricity_total[kWh]','pv_installed_area_roof[m2]',
           'pv_electricity_roof[kWh]','pv_installed_area_north[m2]','pv_electricity_north[kWh]',
           'pv_installed_area_south[m2]','pv_electricity_south[kWh]','pv_installed_area_east[m2]',
           'pv_electricity_east[kWh]','pv_installed_area_west[m2]','pv_electricity_west[kWh]'],
    "pvt": ['pvt_installed_area_total[m2]','pvt_electricity_total[kWh]','pvt_heat_total[kWh]',
            'pvt_installed_area_roof[m2]','pvt_electricity_roof[kWh]','pvt_heat_roof[kWh]',
            'pvt_installed_area_north[m2]','pvt_electricity_north[kWh]','pvt_heat_north[kWh]',
            'pvt_installed_area_south[m2]','pvt_electricity_south[kWh]','pvt_installed_area_east[m2]',
            'pvt_electricity_east[kWh]','pvt_heat_east[kWh]','pvt_installed_area_west[m2]',
            'pvt_electricity_west[kWh]','pvt_heat_west[kWh]'],
    "sc_et": ['sc_et_installed_area_total[m2]','sc_et_electricity_total[kWh]','sc_et_heat_total[kWh]',
              'sc_et_installed_area_roof[m2]','sc_et_electricity_roof[kWh]','sc_et_heat_roof[kWh]',
              'sc_et_installed_area_north[m2]','sc_et_electricity_north[kWh]','sc_et_heat_north[kWh]',
              'sc_et_installed_area_south[m2]','sc_et_electricity_south[kWh]','sc_et_installed_area_east[m2]',
              'sc_et_electricity_east[kWh]','sc_et_heat_east[kWh]','sc_et_installed_area_west[m2]',
              'sc_et_electricity_west[kWh]','sc_et_heat_west[kWh]'],
    "sc_fp": ['sc_fp_installed_area_total[m2]','sc_fp_electricity_total[kWh]','sc_fp_heat_total[kWh]',
              'sc_fp_installed_area_roof[m2]','sc_fp_electricity_roof[kWh]','sc_fp_heat_roof[kWh]',
              'sc_fp_installed_area_north[m2]','sc_fp_electricity_north[kWh]','sc_fp_heat_north[kWh]',
              'sc_fp_installed_area_south[m2]','sc_fp_electricity_south[kWh]','sc_fp_installed_area_east[m2]',
              'sc_fp_electricity_east[kWh]','sc_fp_heat_east[kWh]','sc_fp_installed_area_west[m2]',
              'sc_fp_electricity_west[kWh]','sc_fp_heat_west[kWh]'],
    "other_renewables": ['geothermal_heat_potential[kWh]','area_for_ground_source_heat_pump[m2]',
                         'sewage_heat_potential[kWh]','water_body_heat_potential[kWh]'],
    "district_heating": ['DH_plant_thermal_load[kWh]','DH_plant_power[kW]',
                         'DH_electricity_consumption_for_pressure_loss[kWh]','DH_plant_pumping_power[kW]'],
    "district_cooling": ['DC_plant_thermal_load[kWh]','DC_plant_power[kW]',
                         'DC_electricity_consumption_for_pressure_loss[kWh]','DC_plant_pumping_power[kW]'],
    }

    for cea_feature, attached_list in dict.items():
        if set(list_metrics).issubset(set(attached_list)):
            return cea_feature
    return None

def get_results_path(locator, config, cea_feature):

    selected_buildings = config.result_summary.buildings
    network_names_DH = config.result_summary.networks_heating
    network_names_DC = config.result_summary.networks_cooling

    list_paths = []

    if cea_feature == 'demand':
        for building in selected_buildings:
            path = locator.get_demand_results_file(building)
            list_paths.append(path)

    elif cea_feature == 'embodied_emissions':
        path = locator.get_lca_embodied()
        list_paths.append(path)

    elif cea_feature == 'operation_emissions':
        path = locator.get_lca_operation()
        list_paths.append(path)

    if cea_feature == 'pv':
        for building in selected_buildings:
            path = locator.PV_results(building, panel_type)
            list_paths.append(path)

    if cea_feature == 'pvt':
        for building in selected_buildings:
            path = locator.PVT_results(building)
            list_paths.append(path)

    if cea_feature == 'sc-et':
        for building in selected_buildings:
            path = locator.SC_results(building, 'ET')
            list_paths.append(path)

    if cea_feature == 'sc-fp':
        for building in selected_buildings:
            path = locator.SC_results(building, 'FP')
            list_paths.append(path)

    if cea_feature == 'other_renewables':
        path_geothermal = locator.get_geothermal_potential()
        list_paths.append(path_geothermal)
        path_sewage_heat = locator.get_sewage_heat_potential()
        list_paths.append(path_sewage_heat)
        path_water_body = locator.get_water_body_potential()
        list_paths.append(path_water_body)

    if cea_feature == 'district_heating':
        for network in network_names_DH:
            path_thermal = locator.get_thermal_network_plant_heat_requirement_file('DH', network, representative_week=False)
            list_paths.append(path_thermal)
            path_pump = locator.get_network_energy_pumping_requirements_file('DH', network, representative_week=False)
            list_paths.append(path_pump)

    if cea_feature == 'district_cooling':
        for network in network_names_DC:
            path_thermal = locator.get_thermal_network_plant_heat_requirement_file('DC', network, representative_week=False)
            list_paths.append(path_thermal)
            path_pump = locator.get_network_energy_pumping_requirements_file('DC', network, representative_week=False)
            list_paths.append(path_pump)

    return list_paths

def from_metrics_to_cea_column_names(list_metrics):

    mapping_dict = {'conditioned_floor_area[m2]':[],
                    'roof_area[m2]':[],
                    'gross_floor_area[m2]':[],
                    'nominal_occupancy[-]':[],
                    'grid_electricity_consumption[MWh]':[],
                    'enduse_electricity_consumption[MWh]':[],
                    'enduse_cooling_demand[MWh]':[],
                    'enduse_space_cooling_demand[MWh]':[],
                    'enduse_heating_demand[MWh]':[],
                    'enduse_space_heating_demand[MWh]':[],
                    'enduse_dhw_demand[MWh]':[],

                    'embodied_emissions_building_construction[tonCO2-eq/yr]':[],

                    'operation_emissions[tonCO2-eq/yr]':[],
                    'operation_emissions_grid[tonCO2-eq/yr]':[],

                    'pv_installed_area_total[m2]':[],
                    'pv_electricity_total[kWh]':[],
                    'pv_installed_area_roof[m2]':[],
                    'pv_electricity_roof[kWh]':[],
                    'pv_installed_area_north[m2]':[],
                    'pv_electricity_north[kWh]':[],
                    'pv_installed_area_south[m2]':[],
                    'pv_electricity_south[kWh]':[],
                    'pv_installed_area_east[m2]':[],
                    'pv_electricity_east[kWh]':[],
                    'pv_installed_area_west[m2]':[],
                    'pv_electricity_west[kWh]':[],

                    'pvt_installed_area_total[m2]':[],
                    'pvt_electricity_total[kWh]':[],
                    'pvt_heat_total[kWh]':[],
                    'pvt_installed_area_roof[m2]':[],
                    'pvt_electricity_roof[kWh]':[],
                    'pvt_heat_roof[kWh]':[],
                    'pvt_installed_area_north[m2]':[],
                    'pvt_electricity_north[kWh]':[],
                    'pvt_heat_north[kWh]':[],
                    'pvt_installed_area_south[m2]':[],
                    'pvt_electricity_south[kWh]':[],
                    'pvt_installed_area_east[m2]':[],
                    'pvt_electricity_east[kWh]':[],
                    'pvt_heat_east[kWh]':[],
                    'pvt_installed_area_west[m2]':[],
                    'pvt_electricity_west[kWh]':[],
                    'pvt_heat_west[kWh]':[],

                    'sc_et_installed_area_total[m2]':[],
                    'sc_et_electricity_total[kWh]':[],
                    'sc_et_heat_total[kWh]':[],
                    'sc_et_installed_area_roof[m2]':[],
                    'sc_et_electricity_roof[kWh]':[],
                    'sc_et_heat_roof[kWh]':[],
                    'sc_et_installed_area_north[m2]':[],
                    'sc_et_electricity_north[kWh]':[],
                    'sc_et_heat_north[kWh]':[],
                    'sc_et_installed_area_south[m2]':[],
                    'sc_et_electricity_south[kWh]':[],
                    'sc_et_installed_area_east[m2]':[],
                    'sc_et_electricity_east[kWh]':[],
                    'sc_et_heat_east[kWh]':[],
                    'sc_et_installed_area_west[m2]':[],
                    'sc_et_electricity_west[kWh]':[],
                    'sc_et_heat_west[kWh]':[],

                    'sc_fp_installed_area_total[m2]':[],
                    'sc_fp_electricity_total[kWh]':[],
                    'sc_fp_heat_total[kWh]':[],
                    'sc_fp_installed_area_roof[m2]':[],
                    'sc_fp_electricity_roof[kWh]':[],
                    'sc_fp_heat_roof[kWh]':[],
                    'sc_fp_installed_area_north[m2]':[],
                    'sc_fp_electricity_north[kWh]':[],
                    'sc_fp_heat_north[kWh]':[],
                    'sc_fp_installed_area_south[m2]':[],
                    'sc_fp_electricity_south[kWh]':[],
                    'sc_fp_installed_area_east[m2]':[],
                    'sc_fp_electricity_east[kWh]':[],
                    'sc_fp_heat_east[kWh]':[],
                    'sc_fp_installed_area_west[m2]':[],
                    'sc_fp_electricity_west[kWh]':[],
                    'sc_fp_heat_west[kWh]':[],

                    'geothermal_heat_potential[kWh]':[],
                    'area_for_ground_source_heat_pump[m2]':[],
                    'sewage_heat_potential[kWh]':[],
                    'water_body_heat_potential[kWh]':[],

                    'DH_plant_thermal_load[kWh]':[],
                    'DH_plant_power[kW]':[],
                    'DH_electricity_consumption_for_pressure_loss[kWh]':[],
                    'DH_plant_pumping_power[kW]':[],

                    'DC_plant_thermal_load[kWh]':[],
                    'DC_plant_power[kW]':[],
                    'DC_electricity_consumption_for_pressure_loss[kWh]':[],
                    'DC_plant_pumping_power[kW]':[],

    }
    cea_column_names_set = set()

    for metric in list_metrics:
        if metric in mapping_dict:
            # Add the corresponding output strings (handle single or multiple values)
            cea_column_name = mapping_dict[metric]
            if isinstance(cea_column_name, list):
                cea_column_names_set.update(cea_column_name)  # Add all items from the list
            else:
                cea_column_names_set.add(cea_column_name)  # Add single value
        else:
            # Optionally handle unmapped strings (e.g., log a warning or ignore)
            raise ValueError("There might be a CEA bug here. Post an issue on GitHub or CEA Forum to report it.")

    return list(cea_column_names_set)

def exec_read_and_summarise(config, locator, hour_start, hour_end, list_metrics):

    # create an empty DataFrame to store all the results
    summary_df = pd.DataFrame()

    # not found message to be reflected in the summary DataFrame
    na = float('Nan')

    # map the CEA Feature for the selected metrics
    cea_feature = map_metrics_cea_features(list_metrics)

    # locate the path(s) to the results of the CEA Feature
    list_paths = get_results_path(locator, config, cea_feature)

    return


    

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
    # get the start (inclusive) and end (not-inclusive) hours
    hour_start, hour_end = get_hours_start_end(config)

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
