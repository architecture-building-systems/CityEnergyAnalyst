from __future__ import division

import matplotlib
import matplotlib.cm as cmx
import matplotlib.pyplot as plt
import pickle
import deap
import cea.globalvar
import pandas as pd
import numpy as np
import json
import os
import csv
import cea.inputlocator
from cea.optimization import supportFn as sFn

def pareto_activation_curve(data_frame, analysis_fields, renewable_sources_fields, title, output_path):

    #CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    #CALCULATE TABLE
    traces_table = calc_table(analysis_fields, renewable_sources_fields, data_frame)

    #PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO,title=title, barmode='stack',
                       yaxis=dict(title='Power Capacity [MW]', domain=[.35, 1]),
                       xaxis=dict(title='Point in the Pareto Curve'))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

def load_profile_plot(locator, generation, individual, week, yearly):
    """
    This function plots the hourly load profile
    """
    # Determine buildings that are connected
    total_demand = pd.read_csv(locator.get_total_demand()).set_index('Name')
    building_names = list(total_demand.index)
    building_total = pd.DataFrame(np.zeros((8760,4)), columns=['QEf_kWh', 'QHf_kWh', 'QCf_kWh', 'Ef_kWh'])
    for i in xrange(len(building_names)):
        building_demand_results = 'building' + str(i)
        building_demand_results = pd.read_csv(locator.get_demand_results_folder() + '\\' + building_names[i] + '.csv')
        for name in ['QEf_kWh', 'QHf_kWh', 'QCf_kWh', 'Ef_kWh']:
            building_total[name] = building_total[name] + building_demand_results[name]

    # print (building_total['QEf_kWh'])
    building_total['index'] = xrange(8760)

    with open(locator.get_optimization_master_results_folder() + "\CheckPoint_" + str(generation), "rb") as fp:
        data = json.load(fp)

    pop = data['population']
    ntwList = data['networkList']
    pop_individual = []
    for i in xrange(len(pop[individual])):
        if type(pop[individual][i]) is float:
            pop_individual.append((str(pop[individual][i])[0:4]))
        else:
            pop_individual.append(str(pop[individual][i]))

    # Read individual and transform into a barcode of hegadecimal characters
    individual_barcode = sFn.individual_to_barcode(pop_individual)
    length_network = len(individual_barcode)
    length_unit_activation =  len(pop_individual) - length_network
    unit_activation_barcode = "".join(pop_individual[0:length_unit_activation])
    pop_individual_to_Hcode = hex(int(str(individual_barcode), 2))
    pop_name_hex = unit_activation_barcode + pop_individual_to_Hcode


    data_activation_path = os.path.join(locator.get_optimization_slave_results_folder(), pop_name_hex+ '_PPActivationPattern.csv')
    df_PPA = pd.read_csv(data_activation_path)
    df_PPA['index'] = xrange(8760)

    data_storage_path = os.path.join(locator.get_optimization_slave_results_folder(),
                                        pop_name_hex + '_StorageOperationData.csv')
    df_SO = pd.read_csv(data_storage_path)
    df_SO['index'] = xrange(8760)
    index = df_PPA['index']

    #  yearly

    network_demand = df_SO['Q_DH_networkload_W']
    Q_from_storage = df_SO['Q_DH_networkload_W'] - df_SO['Q_missing_W']
    Q_from_base_boiler = df_PPA['Q_BoilerBase_W']
    Q_from_peak_boiler = df_PPA['Q_BoilerPeak_W']
    Q_from_additional_boiler = df_PPA['Q_AddBoiler_W']
    Q_from_CC = df_PPA['Q_CC_W']
    Q_from_furnace = df_PPA['Q_Furnace_W']
    Q_from_GHP = df_PPA['Q_GHP_W']
    Q_from_lake = df_PPA['Q_HPLake_W']
    Q_from_sewage = df_PPA['Q_HPSew_W']
    Q_from_PV = df_SO['Q_SCandPVT_gen_Wh']


    plt.subplot(2, 1, 1)
    plt.plot([], [], color='b', label='Storage', linewidth=5)
    plt.plot([], [], color='tab:orange', label='Solar', linewidth=5)
    plt.plot([], [], color='c', label='Boiler', linewidth=5)
    plt.plot([], [], color='m', label='CC', linewidth=5)
    plt.plot([], [], color='y', label='Furnace', linewidth=5)
    plt.plot([], [], color='k', label='GHP', linewidth=5)
    plt.plot([], [], color='r', label='Lake', linewidth=5)
    plt.plot([], [], color='g', label='Sewage', linewidth=5)


    plt.stackplot(index / 24, Q_from_storage / 1E6, Q_from_PV / 1E6, (Q_from_additional_boiler + Q_from_base_boiler + Q_from_peak_boiler) / 1E6,
                  Q_from_CC / 1E6, Q_from_furnace / 1E6, Q_from_GHP / 1E6, Q_from_lake / 1E6, Q_from_sewage / 1E6,
                  colors=['b', 'tab:orange', 'c', 'm', 'y', 'k', 'r', 'g'])

    plt.xlabel('Day in year', fontsize = 14, fontweight = 'bold')
    plt.ylabel('Thermal Energy in MW', fontsize = 14, fontweight = 'bold')
    plt.legend()

    #  electricity
    E_from_CC = df_PPA['E_CC_gen_W']
    E_from_solar = df_PPA['E_solar_gen_W']
    E_without_buildings = df_PPA['E_consumed_without_buildingdemand_W']
    E_from_buildings = building_total['Ef_kWh'] * 1000
    E_zeros = np.zeros(8760)
    E_from_grid = (E_without_buildings + E_from_buildings - E_from_CC - E_from_solar)
    E_from_grid[E_from_grid < 0] = 0


    plt.subplot(2, 1, 2)
    plt.plot([], [], color='m', label='CC', linewidth=5)
    plt.plot([], [], color='tab:orange', label='Solar', linewidth=5)
    plt.plot([], [], color='tab:brown', label='Grid', linewidth=5)
    plt.stackplot(index / 24, E_from_CC / 1E6, E_from_solar / 1E6, E_from_grid / 1E6,
                  colors=['m', 'tab:orange', 'tab:brown'])


    plt.xlabel('Day in year', fontsize = 14, fontweight = 'bold')
    plt.ylabel('Electricity in MW', fontsize = 14, fontweight = 'bold')
    plt.legend()
    axes = plt.gca()
    # axes.set_ylim([0, 7])
    plt.show()

    #  weekly

    df1_PPA = df_PPA[(df_PPA['index'] >= week * 7 * 24) & (df_PPA['index'] <= (week + 1) * 7 * 24)]
    df1_SO = df_SO[(df_SO['index'] >= week * 7 * 24) & (df_SO['index'] <= (week + 1) * 7 * 24)]
    building_total_1 = building_total[(building_total['index'] >= week * 7 * 24) & (building_total['index'] <= (week + 1) * 7 * 24)]

    index = df1_PPA['index']

    network_demand = df1_SO['Q_DH_networkload_W']
    Q_from_storage = df1_SO['Q_DH_networkload_W'] - df1_SO['Q_missing_W']
    Q_from_base_boiler = df1_PPA['Q_BoilerBase_W']
    Q_from_peak_boiler = df1_PPA['Q_BoilerPeak_W']
    Q_from_additional_boiler = df1_PPA['Q_AddBoiler_W']
    Q_from_CC = df1_PPA['Q_CC_W']
    Q_from_furnace = df1_PPA['Q_Furnace_W']
    Q_from_GHP = df1_PPA['Q_GHP_W']
    Q_from_lake = df1_PPA['Q_HPLake_W']
    Q_from_sewage = df1_PPA['Q_HPSew_W']
    Q_from_PV = df1_SO['Q_SCandPVT_gen_Wh']

    fig, ax = plt.subplots()
    plt.subplot(2, 1, 1)
    plt.plot([], [], color='b', label='Storage', linewidth=5)
    plt.plot([], [], color='tab:orange', label='Solar', linewidth=5)
    plt.plot([], [], color='c', label='Boiler', linewidth=5)
    plt.plot([], [], color='m', label='CC', linewidth=5)
    plt.plot([], [], color='y', label='Furnace', linewidth=5)
    plt.plot([], [], color='k', label='GHP', linewidth=5)
    plt.plot([], [], color='r', label='Lake', linewidth=5)
    plt.plot([], [], color='g', label='Sewage', linewidth=5)


    plt.stackplot(index / 24, Q_from_storage / 1E6, Q_from_PV / 1E6, (Q_from_additional_boiler + Q_from_base_boiler + Q_from_peak_boiler) / 1E6,
                  Q_from_CC / 1E6, Q_from_furnace / 1E6, Q_from_GHP / 1E6, Q_from_lake / 1E6, Q_from_sewage / 1E6,
                  colors=['b', 'tab:orange', 'c', 'm', 'y', 'k', 'r', 'g'])

    plt.xlabel('Day in year', fontsize = 14, fontweight = 'bold')
    plt.ylabel('Thermal Energy in MW', fontsize = 14, fontweight = 'bold')
    plt.legend()

    E_from_CC = df1_PPA['E_CC_gen_W']
    E_from_solar = df1_PPA['E_solar_gen_W']
    E_without_buildings = df1_PPA['E_consumed_without_buildingdemand_W']
    E_from_buildings = building_total_1['Ef_kWh'] * 1000
    E_zeros = np.zeros(8760)
    E_from_grid = (E_without_buildings + E_from_buildings - E_from_CC - E_from_solar)
    print (E_from_grid)
    # E_from_grid[E_from_grid < 0] = 0

    plt.subplot(2, 1, 2)
    plt.plot([], [], color='m', label='CC', linewidth=5)
    plt.plot([], [], color='tab:orange', label='Solar', linewidth=5)
    plt.plot([], [], color='tab:brown', label='Grid', linewidth=5)
    plt.stackplot(index / 24, E_from_CC / 1E6, E_from_solar / 1E6, E_from_grid / 1E6,
                  colors=['m', 'tab:orange', 'tab:brown'])

    plt.xlabel('Day in year', fontsize = 14, fontweight = 'bold')
    plt.ylabel('Electricity in MW', fontsize = 14, fontweight = 'bold')
    plt.legend()
    axes = plt.gca()
    axes.set_ylim([-7, 7])
    plt.show()

    print (''.join(str(pop_individual[i]) for i in xrange(len(pop_individual))))


    return

def main(config):
    # print out all configuration variables used by this script
    print("Running dashboard with scenario = %s" % config.dashboard.scenario)

    locator = cea.inputlocator.InputLocator(config.dashboard.scenario)
    gv = cea.globalvar.GlobalVariables()

    generation = 3
    individual = 2
    yearly = True
    week = 15

    individual = individual - 1
    load_profile_plot(locator, generation, individual, week, yearly)

if __name__ == '__main__':
    main(cea.config.Configuration())
