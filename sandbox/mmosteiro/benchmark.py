# -*- coding: utf-8 -*-
"""
===========================
Benchmark graphs algorithm
===========================

"""
from __future__ import division
import matplotlib.pyplot as plt
import pandas as pd
from cea import inputlocator
from geopandas import GeoDataFrame as gpdf
import numpy as np
import os
import tempfile

def benchmark(locator_list, gv):
    """
    algorithm to print graphs in PDF concerning the 2000 Watt society benchmark 
    for two scenarios (A and B)

    Parameters
    ----------

    :param locator: an array of InputLocator set to each first scenario to be computed
    :type locator: inputlocator.InputLocator

    Returns
    -------
    Graphs of the embodied and operational emissions and primary energy demand: .Pdf
    """

    # setup-time
    color_palette = ['g', 'r', 'y', 'c', 'b', 'm', 'k']
    legend = []
    graphs = ['embodied', 'operation', 'mobility', 'total']
    old_fields = ['pen_GJ', 'ghg_ton', 'pen_MJm2', 'ghg_kgm2']
    old_suffix = ['_x', '_y', '']
    fields = ['_GJ', '_ton', '_MJm2', '_kgm2']
    new_cols = {}
    for i in range(4):
        for j in range(3):
            new_cols[old_fields[i] + old_suffix[j]] = graphs[j] + fields[i]
    # calculate target values - THIS IS ASSUMING THE FIRST SCENARIO IS ALWAYS THE BASELINE! Need to confirm.
    targets = calc_benchmark_targets(locator_list[0])
    # calculate current values - THIS SHOULD NOT BE HARD CODED AND NEED A SOURCE (other than Inducity)
    today_values = calc_today_values()

    # start graphs
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, figsize=(16, 12))
    fig.text(0.07, 0.5, 'Greenhouse Gas Emissions [kg CO$_2$-eq/m$^2$-yr]', va='center', rotation='vertical')
    fig.text(0.5, 0.07, 'Primary Energy Demand [MJ/m$^2$-yr]', ha='center')  # , rotation='vertical')

    # run for each locator
    for n in range(len(locator_list)):
        locator = locator_list[n]
        # get embodied and operation PEN and GHG for each building from CSV files
        demand = pd.read_csv(locator.get_total_demand())
        df_buildings = pd.read_csv(locator.get_lca_embodied()).merge\
            (pd.read_csv(locator.get_lca_operation()),on = 'Name').merge\
            (pd.read_csv(locator.get_lca_mobility()),on = 'Name')
        df_buildings = df_buildings.rename(columns=new_cols)
        df_buildings = df_buildings.merge(demand[['Name','Af_m2']],on = 'Name')

        for i in range(4):
            col_list = [graphs[0] + fields[i], graphs[1] + fields[i], graphs[2] + fields[i]]
            df_buildings[graphs[3] + fields[i]] = df_buildings[col_list].sum(axis=1)

        # calculate total results for entire scenario
        df_scenario = df_buildings.drop('Name',axis=1).sum(axis=0)
        for i in graphs:
            for j in range(2):
                df_scenario[i + fields[j+2]] = df_scenario[i+fields[j]] / df_scenario['Af_m2'] * 1000

        for i in range(len(graphs)):
            plt.subplot(2,2,i+1)
            plt.plot(df_buildings[graphs[i]+fields[2]], df_buildings[graphs[i]+fields[3]],'o', color = color_palette[n])
            plt.plot(df_scenario[graphs[i]+fields[2]], df_scenario[graphs[i]+fields[3]], 'o', color = color_palette[n],
                     markersize = 15)
        legend.extend(['Scenario '+str(n+1), 'Scenario '+str(n+1)+' total'])
    # complete graphs
    plt.plot()
    for i in range(len(graphs)):
        plt.subplot(2, 2, i + 1)
        plt.plot([0,targets[graphs[i] + fields[2]],targets[graphs[i] + fields[2]]],
                 [targets[graphs[i] + fields[3]],targets[graphs[i] + fields[3]],0], color='k')
        plt.plot([0, today_values[graphs[i] + fields[2]], today_values[graphs[i] + fields[2]]],
                 [today_values[graphs[i] + fields[3]], today_values[graphs[i] + fields[3]], 0], '--', color='k')
        plt.axis([0, today_values[graphs[i] + fields[2]]*1.2, 0, today_values[graphs[i] + fields[3]]*1.2])
        plt.title(graphs[i])

    legend.extend(['Scenario 1 benchmark','Present day values'])
    plt.legend(legend, bbox_to_anchor=(-1.1, -0.2, 2, 0.102), loc=0, ncol=3 , mode="expand", borderaxespad=0,numpoints=1)
    '''
        , bbox_to_anchor=(-1.1, -0.2, 2, 0.102), loc=0, ncol=4, mode="expand", borderaxespad=0,
               fontsize=15, numpoints=1)
    '''
    # save to disk
    plt.savefig(locator_list[0].get_benchmark_plots_file())
    plt.clf()
    plt.close()

def calc_total_scenario(name):
    '''
    Calculates the total ghg_kgm2 and pen_MJm2 for all buildings in a scenario.
    :name = results for each building in the scenario from Total_LCA csv file
    :total_scenario = array with the total pen_MJm2 and ghg_kgm2
    '''
    name = name.sum(axis=0).drop('Name')
    for i in range(0,len(name.ghg_kgm2)):
        total_ghg += name.ghg_ton[i]
        total_pen += name.pen_GJ[i]
        if name.ghg_kgm2[i] > 0:
            total_area += (name.ghg_ton[i]) / name.ghg_kgm2[i]
    total_scenario = [ total_pen / total_area,  total_ghg / total_area ]
    return total_scenario

def calc_benchmark_targets(locator):
    '''
    Calculates the embodied, operation, mobility and total targets (ghg_kgm2
    and pen_MJm2) for all buildings in a scenario.
    :param locator: an InputLocator set to the scenario to compute
    :array embodied_target: embodied pen_MJm2 and ghg_kgm2 target
    :array operation_target: operational pen_MJm2 and ghg_kgm2 target
    :array mobility_target: mobility pen_MJm2 and ghg_kgm2 target
    :array total_target: total pen_MJm2 and ghg_kgm2 target
    '''

    # local files
    demand = pd.read_csv(locator.get_total_demand())
    prop_occupancy = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1)
    data_benchmark = locator.get_data_benchmark()
    occupancy = prop_occupancy.merge(demand,on='Name')

    fields = ['Name', 'pen_GJ', 'ghg_ton', 'pen_MJm2', 'ghg_kgm2']
    categories = ['embodied', 'operation', 'mobility', 'total']
    suffix = ['_GJ', '_ton','_MJm2', '_kgm2']
    targets = {}
    area_study = 0

    factors = pd.read_excel(data_benchmark, sheetname=categories[0])
    for i in range(len(factors['code'])):
        if factors['PEN'][i] > 0 and factors['CO2'][i] > 0:
            area_study += (occupancy['Af_m2'] * occupancy[factors['code'][i]]).sum()

    for category in categories:
        factors = pd.read_excel(data_benchmark, sheetname = category)
        vt = factors['code']
        pt = factors['PEN']
        gt = factors['CO2']

        for j in range(len(suffix)):
            targets[category + suffix[j]] = 0
        for i in range(len(vt)):
            targets[category+suffix[0]] += (occupancy['Af_m2'] * occupancy[vt[i]] * pt[i]).sum() / 1000
            targets[category+suffix[1]] += (occupancy['Af_m2'] * occupancy[vt[i]] * gt[i]).sum() / 1000
        targets[category + suffix[2]] += targets[category+suffix[0]] / area_study * 1000
        targets[category + suffix[3]] += targets[category + suffix[1]] / area_study * 1000

    return targets

def calc_today_values():
    '''
    Calculates the embodied, operation, mobility and total targets (ghg_kgm2
    and pen_MJm2) for the entire country.
    CURRENTLY BASED ON INDUCITY! Need a better source. CURRENTLY HARD CODED! Need to change this.
    :param locator: an InputLocator set to the scenario to compute
    :array embodied_target: embodied pen_MJm2 and ghg_kgm2 target
    :array operation_target: operational pen_MJm2 and ghg_kgm2 target
    :array mobility_target: mobility pen_MJm2 and ghg_kgm2 target
    :array total_target: total pen_MJm2 and ghg_kgm2 target
    '''

    today_values = { 'embodied_MJm2' : 145,
                     'embodied_kgm2' : 11,
                     'operation_MJm2': 2138,
                     'operation_kgm2': 101,
                     'mobility_MJm2': 551,
                     'mobility_kgm2': 33,
                     }
    today_values['total_MJm2'] = today_values['embodied_MJm2'] + today_values['operation_MJm2'] + \
                                 today_values['mobility_MJm2']
    today_values['total_kgm2'] = today_values['embodied_kgm2'] + today_values['operation_kgm2'] + \
                                 today_values['mobility_kgm2']
    return today_values

def test_benchmark():
    # HINTS FOR ARCGIS INTERFACE:
    # the user can select a maximum of 2 scenarios to graph (analysis fields!)

    locatorA = ExtendInputLocator(scenario_path=r'C:\reference-case\baseline')
    locatorB = ExtendInputLocator(scenario_path=r'C:\reference-case\scenario')
    locator_list = [locatorA,locatorB]
    from cea import globalvar
    gv = globalvar.GlobalVariables()
    benchmark(locator_list = locator_list, gv=gv)

def test_benchmark_targets():
    # HINTS FOR ARCGIS INTERFACE:
    # the user can select a maximum of 2 scenarios to graph (analysis fields!)

    locator = ExtendInputLocator(scenario_path=r'C:\reference-case\baseline')
    from cea import globalvar
    gv = globalvar.GlobalVariables()
    calc_benchmark_targets(locator)

class ExtendInputLocator(inputlocator.InputLocator):
    def __init__(self, scenario_path):
        super(ExtendInputLocator, self).__init__(scenario_path)
    def get_lca_mobility(self):
        """scenario/2-results/3-emissions/1-timeseries/Total_LCA_mobility.csv"""
        return os.path.join(self.get_lca_emissions_results_folder(), 'Total_LCA_mobility.csv')
    def get_data_benchmark(self):
        """cea/db/Benchmarks/Switzerland/benchmark_targets.xls"""
        return os.path.join(self.db_path, 'Benchmarks', 'Switzerland', 'benchmark_targets.xls')
    def get_benchmark_plots_file(self):
        """scenario/2-results/3-emissions/2-plots/"""
        import time
        demand_plots_folder = self.get_benchmark_plots_folder()
        return os.path.join(demand_plots_folder, 'Benchmark_plot_' + time.strftime("%Y%m%d_%H%M%S.pdf"))
    def get_benchmark_plots_folder(self):
        """scenario/2-results/3-emissions/2-plots"""
        benchmark_plots_folder = os.path.join(self.scenario_path, '2-results', '3-emissions', '2-plots')
        if not os.path.exists(benchmark_plots_folder):
            os.makedirs(benchmark_plots_folder)
        return benchmark_plots_folder


if __name__ == '__main__':
    test_benchmark()
    test_benchmark_targets()
