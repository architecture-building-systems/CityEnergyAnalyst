# -*- coding: utf-8 -*-
"""
===========================
2000 Watt graphs algorithm
===========================

"""
from __future__ import division
import matplotlib.pyplot as plt
import pandas as pd
import inputlocator

def graphs_2000W(locatorA, locatorB, gv):
    """
    algorithm to print graphs in PDF concerning the 2000 Watt society benchmark 
    for two scenarios (A and B)

    Parameters
    ----------

    :param locatorA: an InputLocator set to the first scenario to compute
    :type locatorA: inputlocator.InputLocator

    :param locatorB: an InputLocator set to the first scenario to compute
    :type locatorB: inputlocator.InputLocator

    Returns
    -------
    Graphs of the embodied and operational emissions and primary energy demand: .Pdf
    """

    '''# get name of files to map
    building_names = pd.read_csv(locator.get_total_demand()).Name
    num_buildings = len(building_names)'''
    # setup-time
    # color_palette = ['g', 'r', 'y', 'c']
    scenarios = ['Scenario A', 'Scenario B', 'Scenario A total', 'Scenario B total']
    fields = ['ghg_kgm2','ghg_ton','pen_GJ','pen_MJm2']
    analysis_fields = ['ghg_kgm2','pen_MJm2']

    # get embodied and operation PEN and GHG for each building from CSV files
    df_embodied_A = pd.read_csv(locatorA.get_lca_embodied(), usecols=fields)
    df_embodied_B = pd.read_csv(locatorB.get_lca_embodied(), usecols=fields)
    df_operation_A = pd.read_csv(locatorA.get_lca_operation(), usecols=fields)
    df_operation_B = pd.read_csv(locatorB.get_lca_operation(), usecols=fields)
    # calculate total results for each scenario
    total_embodied_A = calc_total_scenario(df_embodied_A)
    total_embodied_B = calc_total_scenario(df_embodied_B)
    total_operation_A = calc_total_scenario(df_operation_A)
    total_operation_B = calc_total_scenario(df_operation_B)
    '''
    df_embodied_A.index = df_embodied_A.pen_MJm2
    df_embodied_B.index = df_embodied_B.pen_MJm2
    df_operation_A.index = df_operation_A.pen_MJm2
    df_operation_B.index = df_operation_B.pen_MJm2
    '''

    fig, (ax1, ax2) = plt.subplots(2,figsize=(12,16))
    fig.text(0.07, 0.5, 'Greenhouse Gas Emissions [kg CO$_2$-eq/m$^2$-yr]', va='center', rotation='vertical')
    fig.text(0.5, 0.07, 'Primary Energy Demand [MJ/m$^2$-yr]', ha='center') #, rotation='vertical')

    plt.subplot(2,1,1)
    plt.plot(df_embodied_A.pen_MJm2, df_embodied_A.ghg_kgm2, 'ro')
    plt.plot(df_embodied_B.pen_MJm2, df_embodied_B.ghg_kgm2, 'bo')
    plt.plot(total_embodied_A[0],total_embodied_A[1], 'ro', markersize = 15)
    plt.plot(total_embodied_B[0],total_embodied_B[1], 'bo', markersize = 15)
    plt.title('EMBODIED')
    plt.subplot(2,1,2)
    plt.plot(df_operation_A.pen_MJm2, df_operation_A.ghg_kgm2, 'ro')
    plt.plot(df_operation_B.pen_MJm2, df_operation_B.ghg_kgm2, 'bo')
    plt.plot(total_operation_A[0],total_operation_A[1], 'ro', markersize = 15)
    plt.plot(total_operation_B[0],total_operation_B[1], 'bo', markersize = 15)
    plt.title('OPERATION')
    plt.legend(scenarios,bbox_to_anchor=(0, -0.2, 1, 0.102), loc=0, ncol=4, mode="expand", borderaxespad=0, fontsize=15)
    
    # save to disk
    plt.savefig(locatorA.get_lca_plots_file())
    plt.clf()
    plt.close()


def calc_total_scenario(name):
    '''
    Calculates the total ghg_kgm2 and pen_MJm2 for all buildings in a scenario.
    :name = results for each building in the scenario from Total_LCA csv file
    :total_scenario = array with the total pen_MJm2 and ghg_kgm2
    '''
    total_ghg = total_pen = total_area = 0
    for i in range(0,len(name.ghg_kgm2)):
        total_ghg += name.ghg_ton[i]
        total_pen += name.pen_GJ[i]
        if name.ghg_kgm2[i] > 0:
            total_area += (name.ghg_ton[i]) / name.ghg_kgm2[i]
    total_scenario = [ total_pen / total_area,  total_ghg / total_area ]
    return total_scenario

def test_graphs_2000W():
    # HINTS FOR ARCGIS INTERFACE:
    # the user can select a maximum of 2 scenarios to graph (analysis fields!)

    locatorA = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    locatorB = inputlocator.InputLocator(scenario_path=r'C:\reference-case\scenario')
    import globalvar
    gv = globalvar.GlobalVariables()
    graphs_2000W(locatorA=locatorA, locatorB=locatorB, gv=gv)

if __name__ == '__main__':
    test_graphs_2000W()
