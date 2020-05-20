import pandas as pd
import numpy as np
import networkx as nx
import math
import os
import geopandas as gpd
import time
from cea.osmose import settings

HOURS_IN_YEAR = 8760
PUMP_ETA = 0.8 # Circulating Pump
Pa_to_mH2O = 1/9804  # pressure head
P_WATER_KGPERM3 = 998.0  # water density kg/m3
CP_KJPERKGK = 4.185  # [kJ/kg K]
ROUGHNESS = 0.02 / 1000  # roughness coefficient for heating network pipe in m (for a steel pipe, from Li &
BUILDINGS_DEMANDS_COLUMNS = ['Name', 'Ths_sys_sup_aru_C', 'Ths_sys_sup_ahu_C', 'Ths_sys_sup_shu_C',
                             'Qww_sys_kWh', 'Tww_sys_sup_C', 'Tww_sys_re_C', 'mcpww_sys_kWperC',
                             'Qcdata_sys_kWh', 'Tcdata_sys_sup_C', 'Tcdata_sys_re_C', 'mcpcdata_sys_kWperC',
                             'Qcre_sys_kWh', 'Tcre_sys_sup_C', 'Tcre_sys_re_C', 'mcpcre_sys_kWperC',
                             'Ths_sys_re_aru_C', 'Ths_sys_re_ahu_C', 'Ths_sys_re_shu_C',
                             'Tcs_sys_sup_ahu_C', 'Tcs_sys_sup_aru_C',
                             'Tcs_sys_sup_scu_C', 'Tcs_sys_re_ahu_C', 'Tcs_sys_re_aru_C', 'Tcs_sys_re_scu_C',
                             'Qhs_sys_aru_kWh', 'Qhs_sys_ahu_kWh', 'Qhs_sys_shu_kWh',
                             'Qcs_sys_ahu_kWh', 'Qcs_sys_aru_kWh', 'Qcs_sys_scu_kWh', 'mcphs_sys_aru_kWperC',
                             'mcphs_sys_ahu_kWperC', 'mcphs_sys_shu_kWperC', 'mcpcs_sys_ahu_kWperC',
                             'mcpcs_sys_aru_kWperC', 'mcpcs_sys_scu_kWperC', 'E_sys_kWh']

OSMOSE_PROJECT_PATH = os.path.join(*["E:\\OSMOSE_projects\\HCS_mk\\results\\", settings.TECHS[0]])  # ONLY USED IN calc_builing_substation_dTlm
REPORTING = True
def main(path_to_case):
    # INITIALIZE TIMER
    t0 = time.clock()
    ## 1. TRANSFORM OSMOSE DATA TO CEA FORMAT
    substation_flow_rate_m3pers_df, \
    T_supply_K, \
    op_time, \
    substation_A_hex_df = write_cea_demand_from_osmose(path_to_case)

    ## 2. GET NETWORK INFO
    edge_node_df, all_nodes_df, edge_length_df = get_network_info(path_to_case)
    node_df, edge_df = read_shp(path_to_case)

    ## 3. PIPE SIZING & COSTS
    Pipe_properties_df, Cinv_pipe_perm, \
    plant_index, plant_node = get_pipe_sizes(all_nodes_df, edge_node_df,
                                             substation_flow_rate_m3pers_df, path_to_case)
    Pipe_properties_df = Pipe_properties_df.join(edge_length_df, how='outer')
    Cinv_network_pipes, L_network_m = calc_Cinv_network_pipes(edge_length_df, Cinv_pipe_perm)

    ## 5. SUBSTATION COSTS
    substation_A_hex_df['Cinv_hex'] = np.vectorize(calc_Cinv_substation_hex)(substation_A_hex_df)

    ## 6. PUMPING COSTS
    plant_pressure_losses_Pa, \
    network_operation_info = calc_network_pressure_losses(Pipe_properties_df, T_supply_K, all_nodes_df, node_df, edge_df,
                                                                  edge_length_df, edge_node_df, plant_index, plant_node,
                                                                  substation_flow_rate_m3pers_df)

    # electricity consumption
    plant_flow_rate_m3pers = substation_flow_rate_m3pers_df.sum(axis=1)
    plant_pumping_kW = (plant_pressure_losses_Pa / 1000) * plant_flow_rate_m3pers.values / PUMP_ETA
    annual_pumping_energy_kWh = np.nansum(plant_pumping_kW*op_time) # match yearly hours

    # pump size
    Cinv_pump, pump_size_kW = calc_Cinv_pumps(plant_pumping_kW)
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    # results
    results_dict = {'pumping_kWh': annual_pumping_energy_kWh,
                    'pump_size_kW': pump_size_kW,
                    'network_length_m': L_network_m,
                    'Cinv_pump': Cinv_pump,
                    'Cinv_hex': substation_A_hex_df['Cinv_hex'].sum(),
                    'Cinv_pipes': Cinv_network_pipes}
    results_dict.update(network_operation_info)
    import csv
    with open(os.path.join(path_to_case,'pass_to_osmose.csv'), 'w') as f:
        for key in results_dict.keys():
            f.write("%s,%s\n" % (key, str(results_dict[key])))
    print('save results to ', os.path.join(path_to_case,'pass_to_osmose.csv'))
    return


def calc_network_pressure_losses(Pipe_properties_df, T_supply_K, all_nodes_df, node_df, edge_df, edge_length_df,
                                 edge_node_df, plant_index,
                                 plant_node, substation_flow_rate_m3pers_df):
    D_int_m = Pipe_properties_df['D_int_m']
    # write building flowrates into node_flows_at_substations_df
    node_flowrates_at_substations_df = write_substation_flowrates_into_nodes(all_nodes_df, edge_node_df, plant_node,
                                                                             substation_flow_rate_m3pers_df)
    # calculate flowrate in each edge (Ax = b)
    flows_in_edges_m3pers_df = calculate_flow_in_edges(edge_node_df, node_flowrates_at_substations_df, plant_index)
    massflows_in_edges_kgpers_df = flows_in_edges_m3pers_df*P_WATER_KGPERM3
    # calculate pressure losses in each edge
    pressure_losses_in_edges_Pa = []
    specific_pressure_loss_Pa_per_m = []
    velocity_edges_ms = []
    for edge in flows_in_edges_m3pers_df.columns:
        pipe_diameter_m = D_int_m[edge]
        pipe_length_m = edge_length_df.loc[edge,'length_m'] * 1.2 # TODO: assumption (turns and fittings)
        pressure_losses_in_edge_Pa, \
        specific_pressure_loss_in_edge_Pa_per_m, \
        velocity_edge_ms = np.vectorize(calc_pressure_losses)(pipe_diameter_m,flows_in_edges_m3pers_df[edge].values,
                                                                              pipe_length_m, T_supply_K)
        pressure_losses_in_edges_Pa.append(pressure_losses_in_edge_Pa)
        specific_pressure_loss_Pa_per_m.append(specific_pressure_loss_in_edge_Pa_per_m)
        velocity_edges_ms.append(velocity_edge_ms)

    pressure_losses_in_edges_Pa_df = pd.DataFrame(pressure_losses_in_edges_Pa).T
    pressure_losses_in_edges_Pa_df = pd.DataFrame(pressure_losses_in_edges_Pa_df.values, columns=edge_node_df.columns)

    pressure_losses_in_critical_path, \
    pressure_losses_in_substations = calc_pressure_loss_critical_path(pressure_losses_in_edges_Pa_df,
                                                                        node_df, edge_df, edge_node_df,
                                                                        Pipe_properties_df, flows_in_edges_m3pers_df,
                                                                        T_supply_K)
    # calculate pump head at plant
    total_pressure_losses_in_pipes_Pa = pressure_losses_in_critical_path.sum(axis=1) * 2  # calculate supply side to approximate return side
    plant_pressure_losses_Pa = total_pressure_losses_in_pipes_Pa + pressure_losses_in_substations.sum(axis=1)


    if REPORTING:
        specific_pressure_losses_in_edges_Pa_df = pd.DataFrame(specific_pressure_loss_Pa_per_m).T
        specific_pressure_losses_in_edges_Pa_df = pd.DataFrame(specific_pressure_losses_in_edges_Pa_df.values,
                                                               columns=edge_node_df.columns)
        specific_pressure_losses_in_edges_Pa_df.to_csv(
            os.path.join(*[path_to_case, 'specific_pressure_losses_Paperm.csv']))

        velocity_edges_ms_df = pd.DataFrame(velocity_edges_ms).T
        velocity_edges_ms_df = pd.DataFrame(velocity_edges_ms_df.values, columns=edge_node_df.columns)
        velocity_edges_ms_df.to_csv(os.path.join(*[path_to_case, 'velocity_edges_ms.csv']))

        massflows_in_edges_kgpers_df.to_csv(os.path.join(*[path_to_case, 'mass_flow_edges_kgs.csv']))
        Pipe_properties_df.to_csv(os.path.join(*[path_to_case, 'Pipe_properties.csv']))

    # gather operation info
    network_operation_info = {}
    network_operation_info['Ploss_max_Paperm'] = np.max(np.array(specific_pressure_loss_Pa_per_m))
    network_operation_info['Ploss_mean_Paperm'] = np.mean(np.array(specific_pressure_loss_Pa_per_m))
    network_operation_info['v_max_ms'] = np.max(np.array(velocity_edges_ms))
    network_operation_info['v_mean_ms'] = np.mean(np.array(velocity_edges_ms))
    network_operation_info['massflow_min_kgs'] = massflows_in_edges_kgpers_df.min().min()
    return plant_pressure_losses_Pa, network_operation_info


## ====== Processing ============ #

def write_cea_demand_from_osmose(path_to_district_folder):
    path_to_district_demand_folder = os.path.join(path_to_district_folder, 'outputs\\data\\demand\\')
    building_info = pd.read_csv(os.path.join(path_to_district_demand_folder, 'building_info.csv'), index_col='Name')

    # 1. get osmose results
    district_cooling_demand_df = pd.read_csv(os.path.join(path_to_district_demand_folder, 'district_cooling_demand.csv'), header=None).T
    district_cooling_demand_df.rename(columns=district_cooling_demand_df.iloc[0], inplace=True)
    district_cooling_demand_df.drop(district_cooling_demand_df.index[0], inplace=True)
    network_df = district_cooling_demand_df.filter(like='network')  # reduce
    op_time = district_cooling_demand_df['op_time'].values

    # 2. calculate demand per m2 per function
    cooling_loads = {}
    T_net_df = pd.DataFrame()
    Af_total_m2 = {}
    network_lists = network_df.filter(like='locP').filter(like='Hin').filter(like='return').columns
    for network in network_lists:
        network_name = network.split('_Hin')[0]
        Hin = network_df[network]
        Tout = network_df[network_name + '_Tout']
        Tin = network_df[network_name + '_Tin']
        T_net_df[network_name + '_Ts'] = np.where(Hin >= 0.0, Tout, 0.0)
        T_net_df[network_name + '_Tr'] = np.where(Hin >= 0.0, Tin, 0.0)
    T_net_df['Ts'] = T_net_df.filter(like='Ts').sum(axis=1)
    T_net_df['Tr'] = T_net_df.filter(like='Tr').sum(axis=1)
    T_supply_K = T_net_df['Ts'].mean() + 273.15

    for building_function in ['OFF', 'HOT', 'RET']:
        building_substation_demand_kWh = network_df.filter(like='supply').filter(like=building_function).filter(like='Hout').sum(axis=1)
        Af_m2 = district_cooling_demand_df.filter(like='Af_m2').filter(like=building_function).iloc[0].values[0]
        Af_total_m2[building_function] = Af_m2
        specific_cooling_load = building_substation_demand_kWh / Af_m2
        # cooling_loads[building_function] = specific_cooling_load.rename(columns={building_substation_demand_kWh.columns[0]:building_function})
        cooling_loads[building_function] = specific_cooling_load

    # 3. calculate substation heat exchanger area
    U_substation = 800 # W/m2K # Celine Weber
    # plant
    dTlm_plant = 5.0 # TODO: calculate
    Qmax_plant = network_df.filter(like='locP').filter(like='Hin').values.max()
    A_hex_plant_m2 = (Qmax_plant)/(U_substation * dTlm_plant)
    # building
    dTlm_dict, substation_Qmax_dict = {}, {}
    for building_function in ['HOT', 'OFF', 'RET']:
        Q_substation = network_df.filter(like=building_function).filter(like='Hout').sum(axis=1)
        dTlm_dict[building_function] = 6
        substation_Qmax_dict[building_function] = Q_substation.values.max()
        # dTlm_dict[building_function], substation_Qmax_dict[building_function] = \
        #     calc_builing_substation_dTlm(Q_substation, building_function)  # FIXME: cant use it during optimization, no plots

    # 4. allocate cooling loads and heat exchanger area to buildings
    substation_flow_rate_m3pers_df = pd.DataFrame()
    substation_A_hex = pd.DataFrame(columns=['A_hex_m2'])
    substation_A_hex.loc['plant'] = [A_hex_plant_m2]
    for building in building_info.index:
        building_function = building_info.loc[building][building_info.loc[building]==1].index.values[0]
        bui_func = building_function[:3]
        building_Af_m2 = building_info.loc[building]['Af_m2']
        # initiate building_demand_df
        building_demand_df = pd.DataFrame(columns=BUILDINGS_DEMANDS_COLUMNS)

        # cooling loads
        building_demand_df['Qcs_sys_ahu_kWh'] = (cooling_loads[bui_func] * building_Af_m2)
        building_demand_df['mcpcs_sys_ahu_kWperC'] = building_demand_df['Qcs_sys_ahu_kWh'] / (T_net_df['Tr'] - T_net_df['Ts'])
        substation_flow_rate_m3pers = building_demand_df['mcpcs_sys_ahu_kWperC'] / CP_KJPERKGK / P_WATER_KGPERM3
        substation_flow_rate_m3pers_df[building] = substation_flow_rate_m3pers

        # substation heat exchanger areas
        substation_Qmax = substation_Qmax_dict[bui_func] * (building_Af_m2 / building_Af_m2)
        substation_A_hex.loc[building] = [substation_Qmax / (U_substation * dTlm_dict[bui_func])]

        # fill nan with zeros
        building_demand_df['Name'] = building
        building_demand_df = building_demand_df.replace(np.nan, 0.0)
        annual_demand_kWh = building_demand_df['Qcs_sys_ahu_kWh'].values * op_time
        building_info.loc[building, 'Qcs_sys_MWhyr'] = sum(annual_demand_kWh)/1000.0

        if settings.output_cea_demand:
            building_demand_df['Tcs_sys_sup_ahu_C'] = 7.5  # only used in thermal_network calculation
            building_demand_df['Tcs_sys_re_ahu_C'] = 14.5  # only used in thermal_network calculation
            building_demand_df.to_csv(os.path.join(path_to_district_demand_folder, building + '.csv'))
        

    # 5. match yearly hours
    op_time = district_cooling_demand_df['op_time'].values
    # substation_flow_rate_m3pers_df = multiply_df_to_match_hours(substation_flow_rate_m3pers_df)
    # substation_flow_rate_m3pers_df = substation_flow_rate_m3pers_df.drop(columns=['index'])
    return substation_flow_rate_m3pers_df, T_supply_K, op_time, substation_A_hex

def get_network_info(path_to_case):
    path_to_thermal_network = os.path.join(path_to_case, 'outputs\\data\\thermal-network\\')
    # get edge node matrix
    path_to_edge_node_matrix = os.path.join('', *[path_to_thermal_network, "DC__EdgeNode.csv"])
    edge_node_df = pd.read_csv(path_to_edge_node_matrix, index_col=0)
    # get all nodes
    path_to_all_nodes = os.path.join('', *[path_to_thermal_network, "DC__metadata_nodes.csv"])
    all_nodes_df = pd.read_csv(path_to_all_nodes).sort_values(by=['Name'])
    # get all edges
    path_to_all_edges = os.path.join('', *[path_to_thermal_network, "DC__metadata_edges.csv"])
    all_edges_df = pd.read_csv(path_to_all_edges)
    edge_length_df = all_edges_df[['Name', 'length_m']].set_index('Name')  # look-up table
    edge_length_df.fillna(0.5, inplace=True) # a very short pipe that connects to the plant
    return edge_node_df, all_nodes_df, edge_length_df

def write_substation_flowrates_into_nodes(all_nodes_df, edge_node_df, plant_node, substation_flow_rate_m3pers_df):
    # paste substation flowrate to the node column
    building_nodes_df = all_nodes_df[['Name', 'Building']].set_index('Building')  # look-up table
    node_flows_at_substations_df = pd.DataFrame(columns=edge_node_df.index)  # empty df
    for building in substation_flow_rate_m3pers_df.columns:
        node = building_nodes_df.loc[building,'Name']  # find node name
        node_flows_at_substations_df[node] = substation_flow_rate_m3pers_df[building]
    node_flows_at_substations_df.fillna(0.0, inplace=True)
    node_flows_at_substations_df.drop(columns=[plant_node], inplace=True)
    return node_flows_at_substations_df

## ====== HEX sizing ===================== ##

def calc_builing_substation_dTlm(Q_substation, building_function):
    Q_max_substation = Q_substation.values.max()
    idx_Qmax = np.where(Q_substation == Q_max_substation)[0][0]
    t_Qmax = idx_Qmax + 1
    run_folder = os.listdir(OSMOSE_PROJECT_PATH)[
        len(os.listdir(OSMOSE_PROJECT_PATH)) - 1]  # pick the last folder (by name)
    print('got OSMOSE result from: ', os.path.join(*[OSMOSE_PROJECT_PATH, run_folder]))
    icc_folder_path = os.path.join(*[OSMOSE_PROJECT_PATH, run_folder, 's_001\\plots\\icc\\models'])
    icc_separated = 'icc_separated_m_network_loc_loc' + building_function + '_t' + str(t_Qmax) + \
                    '_c' + building_function + '_DefaultHeatCascade.txt'
    T_net_list = get_Ts_Tr_from_txt(icc_separated, icc_folder_path)
    icc_base = 'icc_base_m_network_loc_loc' + building_function + '_t' + str(t_Qmax) + \
               '_c' + building_function + '_DefaultHeatCascade.txt'
    T_bui_list = get_Ts_Tr_from_txt(icc_base, icc_folder_path)

    dTlm = calc_dTlm(T_bui_list, T_net_list)
    print(building_function, 'dTlm', dTlm)
    return dTlm, Q_max_substation

def calc_dTlm(T_bui_list, T_net_list):
    dT_A = min(T_bui_list) - min(T_net_list)
    dT_B = max(T_bui_list) - max(T_net_list)
    dTlm = (dT_A - dT_B) / (math.log(dT_A / dT_B))
    return dTlm

def get_Ts_Tr_from_txt(icc_file_name, icc_folder_path):
    x, y = get_txt_data(os.path.join(icc_folder_path, icc_file_name))
    if min(np.where(np.diff(x) == 0.0)[0]) == int(0):
        idx_Ts = 1 # for icc_base, the first two numbers are the same
    else:
        idx_Ts = 0 # for icc_separated
    Ts = y[idx_Ts]
    # Q_network_kW = x[idx_Ts]
    # if len(np.where(np.diff(x) > 0.0)[0]) > 0:
    #     idx_Tr = np.where(np.diff(x) > 0.0)[0][-1]
    # else:
    #     idx_Tr = np.where(x == 0.0)[0][0]
    idx_Tr = np.where(x == 0.0)[0][0]
    while y[idx_Tr] > 32.0: # has to be below T_OA
        idx_Tr = idx_Tr - 1
    Tr = y[idx_Tr]
    return [Ts, Tr]

## ========= Cost Calculations ============ ##

def calc_Cinv_network_pipes(edge_length_df, Cinv_pipe_perm):
    # Xiang Li, 2015
    Cinv_network_pipes = sum(edge_length_df['length_m'] * Cinv_pipe_perm * 2)
    L_network_m = sum(edge_length_df['length_m'])
    return Cinv_network_pipes, L_network_m

def calc_Cinv_substation_hex(A_hex_m2):
    # Kermani, 2018
    C_inv_hex_2013 = 7000 + 360 * A_hex_m2 ** 0.8
    C_inv_hex_2018 = (556.8 / 402) * C_inv_hex_2013
    return C_inv_hex_2018

def calc_Cinv_pumps(plant_pumping_kW):
    # Tim Vollrath, 2015
    pump_size_W = max(plant_pumping_kW) * 1000
    # get size per pump
    min_size_W, max_size_W = 500.0, 375000375.0
    if pump_size_W > max_size_W:
        number_of_pumps = math.ceil(pump_size_W/max_size_W)
        size_per_pump_W = pump_size_W / number_of_pumps
    elif pump_size_W < min_size_W:
        number_of_pumps = 1
        size_per_pump_W = min_size_W
    else:
        number_of_pumps = 1
        size_per_pump_W = pump_size_W
    # get price per pump
    if size_per_pump_W <= 4000.0 :
        Cinv_per_pump = 29.314 * size_per_pump_W ** 0.5216
    elif(pump_size_W <= 37000.0) and (4000.0 < pump_size_W):
        Cinv_per_pump = 4.323 * size_per_pump_W ** 0.7464
    elif pump_size_W <= max_size_W:
        Cinv_per_pump = 1.0168 * size_per_pump_W ** 0.8873
    # outputs
    Cinv_pump = Cinv_per_pump * number_of_pumps
    pump_capacity_kW = (size_per_pump_W * number_of_pumps) / 1000
    return Cinv_pump, pump_capacity_kW

##========== Pressure Calculations ======== ##

def calc_pressure_losses(pipe_diameter_m, flow_per_edge_m3pers, pipe_length_m, T_supply_K):
    # for each t, each pipe
    reynolds = calc_reynolds(flow_per_edge_m3pers, T_supply_K, pipe_diameter_m)
    darcy = calc_darcy(pipe_diameter_m, reynolds, ROUGHNESS)

    # calculate the pressure losses through a pipe using the Darcy-Weisbach equation
    mass_flow_rate_kgs = flow_per_edge_m3pers * P_WATER_KGPERM3
    pressure_losses_edge_Paperm = darcy * 8 * mass_flow_rate_kgs ** 2 / (
            math.pi ** 2 * pipe_diameter_m ** 5 * P_WATER_KGPERM3)
    pressure_losses_edge_Pa = pressure_losses_edge_Paperm * pipe_length_m
    velocity_edge_ms = flow_per_edge_m3pers / ((math.pi * pipe_diameter_m ** 2)/4)
    return pressure_losses_edge_Pa, pressure_losses_edge_Paperm, velocity_edge_ms

def calc_kinematic_viscosity(temperature):
    # check if list type, this can cause problems
    if isinstance(temperature, (list,)):
        temperature = np.array(temperature)
    return 2.652623e-8 * math.e ** (557.5447 * (temperature - 140) ** -1)

def calc_reynolds(flow_rate_m3pers, temperature__k, pipe_diameter_m):
    kinematic_viscosity_m2s = calc_kinematic_viscosity(temperature__k)  # m2/s
    reynolds = 4 * abs(flow_rate_m3pers) / (math.pi * kinematic_viscosity_m2s * pipe_diameter_m)
    if math.isnan(reynolds):
        print('some numbers are incorrect:', flow_rate_m3pers, kinematic_viscosity_m2s, pipe_diameter_m)
    return reynolds

def calc_darcy(pipe_diameter_m, reynolds, pipe_roughness_m):
    if reynolds <= 1:
        darcy = 0
    elif reynolds <= 2300:
        # calculate the Darcy-Weisbach friction factor for laminar flow
        darcy = 64 / reynolds
    elif reynolds <= 5000:
        # calculate the Darcy-Weisbach friction factor for transient flow (for pipe roughness of e/D=0.0002,
        # @low reynolds numbers lines for smooth pipe nearl identical in Moody Diagram) so smooth pipe approximation used
        darcy = 0.316 * reynolds ** -0.25
    else:
        # calculate the Darcy-Weisbach friction factor using the Swamee-Jain equation, applicable for Reynolds= 5000 - 10E8; pipe_roughness=10E-6 - 0.05
        darcy = 1.325 * np.log(
            pipe_roughness_m / (3.7 * pipe_diameter_m) + 5.74 / reynolds ** 0.9) ** (-2)

    return darcy

def calc_flow_in_edges(edge_node_df, flow_substation_df, plant_index):
    ## remove one equation (at plant node) to build a well-determined matrix, A.
    # plant_index = np.where(all_nodes_df['Type'] == 'PLANT')[0][0]  # find index of the first plant node
    A = edge_node_df.drop(edge_node_df.index[plant_index])
    b = np.nan_to_num(flow_substation_df.T)
    b = np.delete(b, plant_index)
    flow_in_edges = np.linalg.solve(A.values, b)
    return flow_in_edges

def calculate_flow_in_edges(edge_node_df, node_flowrates_at_substations_df, plant_index):
    flows_in_edges = []
    A = edge_node_df.drop(edge_node_df.index[plant_index]).values  # matrix A
    for index, row in node_flowrates_at_substations_df.iterrows():
        flows_in_edges.append(solve_Ax_b(A, row))
    flows_in_edges_df = pd.DataFrame(flows_in_edges, columns=edge_node_df.columns)
    return flows_in_edges_df

def solve_Ax_b(A, node_flows_at_substations_t):
    b = node_flows_at_substations_t.T
    flow_in_edges = np.linalg.solve(A, b)
    return flow_in_edges

def get_pipe_sizes(all_nodes_df, edge_node_df, substation_flow_rate_m3pers_df, path_to_case):
    max_substation_flow_rate_m3pers = substation_flow_rate_m3pers_df.max().to_frame().T
    # get plant_index
    plant_node = all_nodes_df.loc[all_nodes_df['Type'] == 'PLANT', 'Name'].values[0]
    plant_index = np.where(edge_node_df.index == plant_node)[0][0]
    # maximum flows
    max_flow_at_substations_df = write_substation_values_to_nodes(max_substation_flow_rate_m3pers, all_nodes_df,
                                                                  edge_node_df)
    max_flow_in_edges_m3pers = calc_flow_in_edges(edge_node_df, max_flow_at_substations_df, plant_index)
    # get pipe catalog
    path_to_supply_systems = os.path.join(path_to_case, 'inputs\\technology\\systems\\supply_systems.xls')
    pipe_catalog_df = pd.read_excel(path_to_supply_systems, sheet_name='PIPING')
    # get pipe sizes
    velocity_mpers = 2 #TODO: assumption
    peak_load_percentage = 80 #TODO: assumption
    Pipe_DN, D_ext_m, D_int_m, D_ins_m, Cinv_pipe, A_int_m2 = zip(
        *[calc_max_diameter(flow, pipe_catalog_df, velocity_ms=velocity_mpers,
                            peak_load_percentage=peak_load_percentage) for
          flow in max_flow_in_edges_m3pers])
    # D_ins_m = pd.Series(D_ins_m, index=edge_node_df.columns)
    # A_int_m2 = pd.Series(A_int_m2, index=edge_node_df.columns)
    Pipe_properties_df = pd.DataFrame(index=edge_node_df.columns)
    Pipe_properties_df['D_ins_m'] = D_ins_m
    Pipe_properties_df['A_int_m2'] = A_int_m2
    Pipe_properties_df['D_int_m'] = D_int_m
    Pipe_properties_df['Pipe_DN'] = Pipe_DN
    # Pipe_properties_df['max_velocity_mpers'] = max_flow_in_edges_m3pers / A_int_m2
    Cinv_pipe_perm = pd.Series(Cinv_pipe, index=edge_node_df.columns)
    return Pipe_properties_df, Cinv_pipe_perm, plant_index, plant_node

def calc_max_diameter(volume_flow_m3s, pipe_catalog, velocity_ms, peak_load_percentage):
    """
    from cea.technologies.thermal_network.simplified_thermal_network
    :param volume_flow_m3s:
    :param pipe_catalog:
    :param velocity_ms:
    :param peak_load_percentage:
    :return:
    """
    volume_flow_m3s_corrected_to_design = volume_flow_m3s * peak_load_percentage / 100
    diameter_m = math.sqrt((volume_flow_m3s_corrected_to_design / velocity_ms) * (4 / math.pi))
    selection_of_catalog = pipe_catalog.iloc[(pipe_catalog['D_int_m'] - diameter_m).abs().argsort()[:1],:]
    D_int_m = selection_of_catalog['D_int_m'].values[0]
    A_int_m2 = math.pi * (D_int_m ** 2) / 4
    Pipe_DN = selection_of_catalog['Pipe_DN'].values[0]
    D_ext_m = selection_of_catalog['D_ext_m'].values[0]
    D_ins_m = selection_of_catalog['D_ins_m'].values[0]
    Cinv_pipe = selection_of_catalog['Inv_USD2015perm'].values[0] + 1000 # TODO: fixed cost assumptions from matthais' paper

    return Pipe_DN, D_ext_m, D_int_m, D_ins_m, Cinv_pipe, A_int_m2

def calc_pressure_loss_critical_path(pressure_losses_in_edges_Pa_df, node_df, edge_df, edge_node_df,
                                     Pipe_properties_df, flows_in_edges_m3pers_df, T_supply_K):
    plant_node = node_df[node_df['Type'] == 'PLANT'].index[0]
    pressure_losses_in_critical_path = np.zeros(np.shape(pressure_losses_in_edges_Pa_df.values))
    pressure_losses_in_substations = np.zeros([len(pressure_losses_in_edges_Pa_df.values), 2])
    for time, dP_time in enumerate(pressure_losses_in_edges_Pa_df.values):
        if max(dP_time) > 0.0:
            G = nx.Graph()
            G.add_nodes_from(node_df.index)
            for ix, edge_name in enumerate(edge_df.index):
                start_node = edge_df.loc[edge_name, 'start node']
                end_node = edge_df.loc[edge_name, 'end node']
                dP_Pa = dP_time[ix]
                G.add_edge(start_node, end_node, weight=dP_Pa, name=edge_name, ix=str(ix))
            # find the path with the highest pressure drop
            _, distances_dict = nx.dijkstra_predecessor_and_distance(G, source=plant_node)
            critical_node = max(distances_dict, key=distances_dict.get)
            path_to_critical_node = nx.shortest_path(G, source=plant_node)[critical_node]
            # calculate pressure losses along the critical path
            for i in range(len(path_to_critical_node)):
                if i < len(path_to_critical_node) - 1:
                    start_node = path_to_critical_node[i]
                    end_node = path_to_critical_node[i+1]
                    dP_Pa = G[start_node][end_node]['weight']
                    ix_edge = int(G[start_node][end_node]['ix'])
                    pressure_losses_in_critical_path[time][ix_edge] = dP_Pa
            # substations
            pipe_plant = edge_node_df.columns[edge_node_df.loc[plant_node, :] == -1.0].values[0]
            D_int_plant_m = Pipe_properties_df.loc[pipe_plant, 'D_int_m']
            plant_flow_m3pers = flows_in_edges_m3pers_df.loc[time, pipe_plant]
            dP_plant_Pa, _, _ = calc_pressure_losses(D_int_plant_m, plant_flow_m3pers, D_int_plant_m * 9, T_supply_K)
            pipe_end = edge_node_df.columns[edge_node_df.loc[critical_node, :] == 1.0].values[0]
            D_int_end_m = Pipe_properties_df.loc[pipe_end,'D_int_m']
            end_flow_m3pers = flows_in_edges_m3pers_df.loc[time, pipe_end]
            dP_end_Pa, _, _ = calc_pressure_losses(D_int_end_m, end_flow_m3pers, D_int_end_m * 9, T_supply_K)
            pressure_losses_in_substations[time] = [dP_plant_Pa, dP_end_Pa]

    return pressure_losses_in_critical_path, pressure_losses_in_substations


##========== UTILITY FUNCTIONS ============ ##
def read_shp(path_to_case):
    path_to_thermal_network = os.path.join(path_to_case, 'outputs\\data\\thermal-network\\DC')
    # import shapefiles containing the network's edges and nodes
    network_edges_df = gpd.read_file(os.path.join('', *[path_to_thermal_network, "edges.shp"]))
    network_nodes_df = gpd.read_file(os.path.join('', *[path_to_thermal_network, "nodes.shp"]))

    # get node and pipe information
    node_df, edge_df = extract_network_from_shapefile(network_edges_df, network_nodes_df)
    return node_df, edge_df

def extract_network_from_shapefile(edge_shapefile_df, node_shapefile_df):
    """
    Extracts network data into DataFrames for pipes and nodes in the network

    :param edge_shapefile_df: DataFrame containing all data imported from the edge shapefile
    :param node_shapefile_df: DataFrame containing all data imported from the node shapefile
    :type edge_shapefile_df: DataFrame
    :type node_shapefile_df: DataFrame
    :return node_df: DataFrame containing all nodes and their corresponding coordinates
    :return edge_df: list of edges and their corresponding lengths and start and end nodes
    :rtype node_df: DataFrame
    :rtype edge_df: DataFrame

    """
    # set precision of coordinates
    decimals = 6
    # create node dictionary with plant and consumer nodes
    node_dict = {}
    node_shapefile_df.set_index("Name", inplace=True)
    node_shapefile_df = node_shapefile_df.astype('object')
    node_shapefile_df['coordinates'] = node_shapefile_df['geometry'].apply(lambda x: x.coords[0])
    # sort node_df by index number
    node_sorted_index = node_shapefile_df.index.to_series().str.split('NODE', expand=True)[1].apply(int).sort_values(
        ascending=True)
    node_shapefile_df = node_shapefile_df.reindex(index=node_sorted_index.index)
    # assign node properties (plant/consumer/none)
    node_shapefile_df['plant'] = ''
    node_shapefile_df['consumer'] = ''
    node_shapefile_df['none'] = ''

    for node, row in node_shapefile_df.iterrows():
        coord_node = row['geometry'].coords[0]
        if row['Type'] == "PLANT":
            node_shapefile_df.loc[node, 'plant'] = node
        elif row['Type'] == "CONSUMER":
            node_shapefile_df.loc[node, 'consumer'] = node
        else:
            node_shapefile_df.loc[node, 'none'] = node
        coord_node_round = (round(coord_node[0], decimals), round(coord_node[1], decimals))
        node_dict[coord_node_round] = node

    # create edge dictionary with pipe lengths and start and end nodes
    # complete node dictionary with missing nodes (i.e., joints)
    edge_shapefile_df.set_index("Name", inplace=True)
    edge_shapefile_df = edge_shapefile_df.astype('object')
    edge_shapefile_df['coordinates'] = edge_shapefile_df['geometry'].apply(lambda x: x.coords[0])
    # sort edge_df by index number
    edge_sorted_index = edge_shapefile_df.index.to_series().str.split('PIPE', expand=True)[1].apply(int).sort_values(
        ascending=True)
    edge_shapefile_df = edge_shapefile_df.reindex(index=edge_sorted_index.index)
    # assign edge properties
    edge_shapefile_df['pipe length'] = 0
    edge_shapefile_df['start node'] = ''
    edge_shapefile_df['end node'] = ''

    for pipe, row in edge_shapefile_df.iterrows():
        # get the length of the pipe and add to dataframe
        edge_shapefile_df.loc[pipe, 'pipe length'] = row['geometry'].length
        # get the start and end notes and add to dataframe
        edge_coords = row['geometry'].coords
        start_node = (round(edge_coords[0][0], decimals), round(edge_coords[0][1], decimals))
        end_node = (round(edge_coords[1][0], decimals), round(edge_coords[1][1], decimals))
        if start_node in node_dict.keys():
            edge_shapefile_df.loc[pipe, 'start node'] = node_dict[start_node]
        else:
            print('The start node of ', pipe, 'has no match in node_dict, check precision of the coordinates.')
        if end_node in node_dict.keys():
            edge_shapefile_df.loc[pipe, 'end node'] = node_dict[end_node]
        else:
            print('The end node of ', pipe, 'has no match in node_dict, check precision of the coordinates.')

    # # If a consumer node is not connected to the network, find the closest node and connect them with a new edge
    # # this part of the code was developed for a case in which the node and edge shapefiles were not defined
    # # consistently. This has not been a problem after all, but it could eventually be a useful feature.
    # for node in node_dict:
    #     if node not in pipe_nodes:
    #         min_dist = 1000
    #         closest_node = pipe_nodes[0]
    #         for pipe_node in pipe_nodes:
    #             dist = ((node[0] - pipe_node[0])**2 + (node[1] - pipe_node[1])**2)**.5
    #             if dist < min_dist:
    #                 min_dist = dist
    #                 closest_node = pipe_node
    #         j += 1
    #         edge_dict['EDGE' + str(j)] = [min_dist, node_dict[closest_node][0], node_dict[node][0]]

    return node_shapefile_df, edge_shapefile_df

def write_substation_values_to_nodes(substation_flow_df, all_nodes_df, edge_node_df):
    node_flows_at_substations_df = np.nan_to_num(
        [substation_flow_df[all_nodes_df.loc[all_nodes_df['Name'] == node, 'Building'].values[0]][0]
         if all_nodes_df.loc[all_nodes_df['Name'] == node, 'Building'].values[0] != 'NONE' else 0
         for node in edge_node_df.index])
    return node_flows_at_substations_df

def get_txt_data(file_path):
    data = np.genfromtxt(file_path, delimiter=' ')
    # x and y axes
    x = data[:, 0]
    y = data[:, 1]
    return x, y

def multiply_df_to_match_hours(reduced_df):
    HOURS_IN_YEAR = 8760
    hours_osmose = len(reduced_df.index)
    list_with_reduced_dfs = [reduced_df] * int(HOURS_IN_YEAR / hours_osmose)
    yearly_df = pd.concat(list_with_reduced_dfs)
    yearly_df.reset_index(inplace=True)
    return yearly_df

if __name__ == '__main__':
    path_to_case = 'C:\\SG_cases\\SDC_small'
    main(path_to_case)
