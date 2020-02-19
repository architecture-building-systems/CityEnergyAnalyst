import pandas as pd
import numpy as np
import math
import os
import wntr
import time

HOURS_IN_YEAR = 8760
PUMP_ETA = 0.8 # Circulating Pump
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

OSMOSE_PROJECT_PATH = "E:\\OSMOSE_projects\\HCS_mk\\results\\N_base"

def main(path_to_case):
    # INITIALIZE TIMER
    t0 = time.clock()
    ## 1. CALCULATE SUBSTATION MASSFLOW
    substation_flow_rate_m3pers_df, T_supply_K, timesteps, substation_A_hex_df = write_cea_demand_from_osmose(path_to_case)
    max_substation_flow_rate_m3pers = substation_flow_rate_m3pers_df.max().to_frame().T

    ## 2. PRE-CALCULATED METADATA
    edge_node_df, all_nodes_df, edge_length_df = get_precalculated_metadata(path_to_case)

    ## 3. PIPE SIZING
    D_ins_m, plant_index, plant_node = get_pipe_sizes(all_nodes_df, edge_node_df, max_substation_flow_rate_m3pers,
                                                      path_to_case)

    ## 4. Piping cost calculation


    ## 5. Substation cost calculation
    substation_A_hex_df['Cinv_hex'] = np.vectorize(calc_Cinv_substation_hex)(substation_A_hex_df)



    ## 5. Calculate Pressure Losses
    # write building flowrates into node_flows_at_substations_df
    node_flowrates_at_substations_df = write_substation_flowrates_into_nodes(all_nodes_df, edge_node_df, plant_node,
                                                                             substation_flow_rate_m3pers_df)
    # calculate flowrate in each edge (Ax = b)
    flows_in_edges_m3pers_df = calculate_flow_in_edges(edge_node_df, node_flowrates_at_substations_df, plant_index)

    # calculate pressure losses in each edge
    pressure_losses_in_edges_Pa = []
    for edge in flows_in_edges_m3pers_df.columns:
        pipe_diameter_m = D_ins_m[edge]
        pipe_length_m = edge_length_df.get_value(edge, 'length_m')
        pressure_losses_in_edges_Pa.append(np.vectorize(calc_pressure_losses)(pipe_diameter_m,
                                                                              flows_in_edges_m3pers_df[edge].values,
                                                                              pipe_length_m, T_supply_K))
    pressure_losses_in_edges_Pa_df = pd.DataFrame(pressure_losses_in_edges_Pa).T
    pressure_losses_in_edges_Pa_df = pd.DataFrame(pressure_losses_in_edges_Pa_df.values, columns=edge_node_df.columns)

    ## 6. Pumping Energy
    # critical path


    # electricity consumption # TODO:add substation head loss at critical building and plant
    plant_pressure_losses_Pa = pressure_losses_in_edges_Pa_df.sum(axis=1)
    plant_flow_rate_m3pers = substation_flow_rate_m3pers_df.sum(axis=1)
    plant_pumping_kW = plant_pressure_losses_Pa.values * plant_flow_rate_m3pers.values / 1000 / PUMP_ETA
    annual_pumping_energy_kWh = sum(plant_pumping_kW)*int(HOURS_IN_YEAR / timesteps) # match yearly hours

    # pump size
    pump_size_kW = max(plant_pumping_kW)
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    # results
    results_dict = {'pumping_kWh': annual_pumping_energy_kWh,
                    'pump_size_kW': pump_size_kW,
                    'Cinv_hex': substation_A_hex_df['Cinv_hex'].sum()}
    import csv
    with open(os.path.join(path_to_case,'pass_to_osmose.csv'), 'w') as f:
        for key in results_dict.keys():
            f.write("%s,%s\n" % (key, str(results_dict[key])))
    return


## ====== Processing ============ #

def write_cea_demand_from_osmose(path_to_district_folder):
    path_to_district_demand_folder = os.path.join(path_to_district_folder, 'outputs\\data\\demand\\')
    building_info = pd.read_csv(os.path.join(path_to_district_demand_folder, 'building_info.csv'), index_col='Name')

    # 1. get osmose results
    district_cooling_demand_df = pd.read_csv(os.path.join(path_to_district_demand_folder, 'district_cooling_demand.csv'), header=None).T
    district_cooling_demand_df.rename(columns=district_cooling_demand_df.iloc[0], inplace=True)
    district_cooling_demand_df.drop(district_cooling_demand_df.index[0], inplace=True)
    network_df = district_cooling_demand_df.filter(like='network')  # reduce

    # 2. calculate demand per m2 per function
    cooling_loads = {}
    Af_total_m2 = {}
    T_supply_C = network_df.filter(like='locP').filter(like='Tout').max().values[0]
    T_supply_K = network_df.filter(like='locP').filter(like='Tout').max().values[0] + 273.15
    cooling_loads['Ts'] = T_supply_C
    cooling_loads['Tr'] = network_df.filter(like='locP').filter(like='Tin').max().values[0]
    for building_function in ['OFF', 'HOT', 'RET']:
        building_substation_demand_kWh = network_df.filter(like='supply').filter(like=building_function).filter(like='Hout')
        Af_m2 = district_cooling_demand_df.filter(like='Af_m2').filter(like=building_function).iloc[0].values[0]
        Af_total_m2[building_function] = Af_m2
        specific_cooling_load = building_substation_demand_kWh / Af_m2
        cooling_loads[building_function] = specific_cooling_load.rename(columns={building_substation_demand_kWh.columns[0]:building_function})

    # 3. calculate substation heat exchanger area
    U_substation = 1000 # W/m2K # TODO: calculate
    # plant
    dTlm_plant = 5.0 # TODO: calculate
    Qmax_plant = network_df.filter(like='locP').filter(like='Hin').values.max()
    A_hex_plant_m2 = (Qmax_plant)/(U_substation * dTlm_plant)
    # building
    dTlm_dict, substation_Qmax_dict = {}, {}
    for building_function in ['HOT', 'OFF', 'RET']:
        Q_substation = network_df.filter(like=building_function).filter(like='Hout')
        dTlm_dict[building_function], substation_Qmax_dict[building_function] = \
            calc_builing_substation_dTlm(Q_substation, building_function)

    # 4. allocate cooling loads and heat exchanger area to buildings
    substation_flow_rate_m3pers_df = pd.DataFrame()
    substation_A_hex = pd.DataFrame(columns=['A_hex_m2'])
    substation_A_hex.loc['plant'] = [A_hex_plant_m2]
    for building in building_info.index:
        building_function = building_info.loc[building][building_info.loc[building]==1].index.values[0]
        bui_func = building_function[:3]
        building_Af_m2 = building_info.loc[building]['Af_m2']
        building_demand_df = pd.DataFrame(columns=BUILDINGS_DEMANDS_COLUMNS)

        # cooling loads
        building_demand_df['Qcs_sys_ahu_kWh'] = (cooling_loads[bui_func] * building_Af_m2)[bui_func] # TODO: check unit
        building_demand_df['mcpcs_sys_ahu_kWperC'] = building_demand_df['Qcs_sys_ahu_kWh'] / (cooling_loads['Tr'] - cooling_loads['Ts'])
        substation_flow_rate_m3pers = building_demand_df['mcpcs_sys_ahu_kWperC'] / CP_KJPERKGK / P_WATER_KGPERM3
        substation_flow_rate_m3pers_df[building] = substation_flow_rate_m3pers

        # substation heat exchanger areas
        substation_Qmax = substation_Qmax_dict[bui_func] * (building_Af_m2 / building_Af_m2)
        substation_A_hex.loc[building] = [substation_Qmax / (U_substation * dTlm_dict[bui_func])]

        # fill nan with zeros
        building_demand_df['Name'] = building
        building_demand_df = building_demand_df.replace(np.nan, 0.0)
        building_info.loc[building, 'Qcs_sys_MWhyr'] = sum(building_demand_df['Qcs_sys_ahu_kWh'])/1000.0


    # 5. match yearly hours
    timesteps = len(substation_flow_rate_m3pers_df.index)
    # substation_flow_rate_m3pers_df = multiply_df_to_match_hours(substation_flow_rate_m3pers_df)
    # substation_flow_rate_m3pers_df = substation_flow_rate_m3pers_df.drop(columns=['index'])
    return substation_flow_rate_m3pers_df, T_supply_K, timesteps, substation_A_hex

def get_precalculated_metadata(path_to_case):
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
        node = building_nodes_df.get_value(building, 'Name')  # find node name
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
    icc_folder_path = os.path.join(*[OSMOSE_PROJECT_PATH, run_folder, 's_001\\plots\\icc\\models'])
    icc_base = 'icc_base_m_network_loc_loc' + building_function + '_t' + str(t_Qmax) + \
               '_c' + building_function + '_DefaultHeatCascade.txt'
    T_bui_list = get_Ts_Tr_from_txt(icc_base, icc_folder_path)
    icc_separated = 'icc_separated_m_network_loc_loc' + building_function + '_t' + str(t_Qmax) + \
                    '_c' + building_function + '_DefaultHeatCascade.txt'
    T_net_list = get_Ts_Tr_from_txt(icc_separated, icc_folder_path)
    dTlm = calc_dTlm(T_bui_list, T_net_list)

    return dTlm, Q_max_substation

def calc_dTlm(T_bui_list, T_net_list):
    dT_A = min(T_bui_list) - min(T_net_list)
    dT_B = max(T_bui_list) - max(T_net_list)
    dTlm = (dT_A - dT_B) / (math.log(dT_A / dT_B))
    return dTlm

def get_Ts_Tr_from_txt(icc_file_name, icc_folder_path):
    x, y = get_txt_data(os.path.join(icc_folder_path, icc_file_name))
    if min(np.where(np.diff(x) == 0.0)[0]) == int(0):
        Ts = y[1]  # for icc_base, the first two numbers are the same
    else:
        Ts = y[0]  # for icc_separated
    if len(np.where(np.diff(x) > 0.0)[0]) > 0:
        idx_Tr = np.where(np.diff(x) > 0.0)[0][0]
    else:
        idx_Tr = np.where(x == 0.0)[0][0]
    Tr = y[idx_Tr]
    return [Ts, Tr]

## ========= Cost Calculations ============ ##

def pipe_costs(self, locator, network_name, network_type):
    edges_file = pd.read_csv(locator.get_thermal_network_edge_list_file(network_type, network_name))
    piping_cost_data = pd.read_excel(locator.get_database_supply_systems(), sheet_name="PIPING")
    merge_df = edges_file.merge(piping_cost_data, left_on='Pipe_DN', right_on='Pipe_DN')
    merge_df['Inv_USD2015'] = merge_df['Inv_USD2015perm'] * merge_df['length_m']
    pipe_costs = merge_df['Inv_USD2015'].sum()
    return pipe_costs

def calc_Cinv_substation_hex(A_hex_m2):

    C_inv_hex = 7000 + 260 * A_hex_m2 ** 0.8

    return C_inv_hex

##========== Pressure Calculations ======== ##

def calc_pressure_losses(pipe_diameter_m, flow_per_edge_m3pers, pipe_length_m, T_supply_K):
    # for each t, each pipe
    reynolds = calc_reynolds(flow_per_edge_m3pers, T_supply_K, pipe_diameter_m)
    darcy = calc_darcy(pipe_diameter_m, reynolds, ROUGHNESS)

    # calculate the pressure losses through a pipe using the Darcy-Weisbach equation
    mass_flow_rate_kgs = flow_per_edge_m3pers * P_WATER_KGPERM3
    pressure_losses_edges_Paperm = darcy * 8 * mass_flow_rate_kgs ** 2 / (
            math.pi ** 2 * pipe_diameter_m ** 5 * P_WATER_KGPERM3)
    pressure_losses_edge_Pa = pressure_losses_edges_Paperm * pipe_length_m
    return pressure_losses_edge_Pa

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

def get_pipe_sizes(all_nodes_df, edge_node_df, max_substation_flow_rate_m3pers, path_to_case):
    # get plant_index
    plant_node = all_nodes_df.loc[all_nodes_df['Type'] == 'PLANT', 'Name'].values[0]
    plant_index = np.where(edge_node_df.index == plant_node)[0][0]
    # maximum flows
    max_flow_at_substations_df = write_substation_values_to_nodes(max_substation_flow_rate_m3pers, all_nodes_df,
                                                                  edge_node_df)
    max_flow_in_edges_m3pers = calc_flow_in_edges(edge_node_df, max_flow_at_substations_df, plant_index)
    # get pipe catalog
    path_to_pipe_catalog = os.path.join(path_to_case, 'inputs\\technology\\systems\\supply_systems.xls')
    pipe_catalog_df = pd.read_excel(path_to_pipe_catalog, sheet_name='PIPING')
    # get pipe sizes
    velocity_mpers = 2
    peak_load_percentage = 70
    Pipe_DN, D_ext_m, D_int_m, D_ins_m = zip(
        *[calc_max_diameter(flow, pipe_catalog_df, velocity_ms=velocity_mpers,
                            peak_load_percentage=peak_load_percentage) for
          flow in max_flow_in_edges_m3pers])
    D_ins_m = pd.Series(D_ins_m, index=edge_node_df.columns)
    return D_ins_m, plant_index, plant_node

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
    slection_of_catalog = pipe_catalog.ix[(pipe_catalog['D_int_m'] - diameter_m).abs().argsort()[:1]]
    D_int_m = slection_of_catalog['D_int_m'].values[0]
    Pipe_DN = slection_of_catalog['Pipe_DN'].values[0]
    D_ext_m = slection_of_catalog['D_ext_m'].values[0]
    D_ins_m = slection_of_catalog['D_ins_m'].values[0]

    return Pipe_DN, D_ext_m, D_int_m, D_ins_m


##========== UTILITY FUNCTIONS ============ ##
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
    # TODO: change to the actual weight
    HOURS_IN_YEAR = 8760
    hours_osmose = len(reduced_df.index)
    list_with_reduced_dfs = [reduced_df] * int(HOURS_IN_YEAR / hours_osmose)
    yearly_df = pd.concat(list_with_reduced_dfs)
    yearly_df.reset_index(inplace=True)
    return yearly_df

if __name__ == '__main__':
    path_to_case = 'C:\\SG_cases\\SDC'
    main(path_to_case)
