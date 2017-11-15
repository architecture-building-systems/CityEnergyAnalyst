# -*- coding: utf-8 -*-
"""
Benchmark plots
"""
from __future__ import division

import os

import matplotlib.pyplot as plt
import pandas as pd
from geopandas import GeoDataFrame as gpdf

import cea.inputlocator
import cea.config

__author__ = "Martin Mosteiro Romero"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Martin Mosteiro Romero"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def benchmark(locator_list, output_file, config):
    """
    Print PDF graphs comparing the selected scenarios to the 2000 Watt society benchmark for construction, operation
    and mobility. The calculation is based on the database read by and described in calc_benchmark_today and
    calc_benchmark_targets.

    The following file is created as a side effect by this script in the specified file path:

    - output_file: .pdf Plot of the embodied and operational emissions and primary energy demand

    :param locator_list: a list of InputLocator instances set to each scenario to be computed. The first element in
                         the array is always considered as the baseline for the comparison.
    :type locator_list: List[cea.inputlocator.InputLocator]
    :param output_file: the filename (pdf) to save the results as.
    :type output_file: str
    """

    # setup: the labels and colors for the graphs are defined
    color_palette = ['g', 'r', 'y', 'c', 'b', 'm', 'k']
    legend = []
    graphs = ['EMBODIED', 'OPERATION', 'MOBILITY', 'TOTAL']
    graph_titles = {'EMBODIED': 'Embodied', 'OPERATION': 'Operation', 'MOBILITY': 'Mobility', 'TOTAL': 'Total'}
    old_fields = ['nre_pen_GJ', 'ghg_ton', 'nre_pen_MJm2', 'ghg_kgm2']
    old_prefix = ['E_', 'O_', 'M_']
    fields = ['_GJ', '_ton', '_MJm2', '_kgm2']
    new_cols = {}
    # prepare a dictionary to contain the results for the maximum primary energy demand and emissions in the comparison
    # these are later used to set the scale of the axes of the plots
    scenario_max = {}
    for i in range(4):
        for j in range(3):
            new_cols[old_prefix[j] + old_fields[i]] = graphs[j] + fields[i]
        scenario_max[graphs[i] + fields[2]] = scenario_max[graphs[i] + fields[3]] = 0

    # calculate target values based on the baseline case
    targets = calc_benchmark_targets(locator_list[0], config)
    # calculate current values based on the baseline case
    values_today = calc_benchmark_today(locator_list[0], config)

    # start graphs
    fig, (ax1, ax2, ax3, ax4, ax5, ax6) = plt.subplots(6, figsize=(16, 12))
    fig.text(0.07, 0.5, 'Greenhouse Gas Emissions [kg CO$_2$-eq/m$^2$-yr]', va='center', rotation='vertical')
    fig.text(0.375, 0.04, 'Non-Renewable Primary Energy Demand [MJ/m$^2$-yr]', ha='center')
    ax3.axis('off')
    ax6.axis('off')
    axes = [1, 2, 4, 5]

    # run for each locator (i.e., for each scenario)
    for n in range(len(locator_list)):
        locator = locator_list[n]
        scenario_name = os.path.basename(locator.scenario)

        # get embodied and operation PEN and GHG for each building from CSV files
        demand = pd.read_csv(locator.get_total_demand())
        df_buildings = pd.read_csv(locator.get_lca_embodied()).merge \
            (pd.read_csv(locator.get_lca_operation()), on='Name').merge \
            (pd.read_csv(locator.get_lca_mobility()), on='Name')
        df_buildings = df_buildings.rename(columns=new_cols)

        for i in range(4):
            col_list = [graphs[0] + fields[i], graphs[1] + fields[i], graphs[2] + fields[i]]
            df_buildings[graphs[3] + fields[i]] = df_buildings[col_list].sum(axis=1)

        # calculate total results for entire scenario
        df_scenario = df_buildings.drop('Name', axis=1).sum(axis=0)
        for graph in graphs:
            for j in range(2):
                df_scenario[graph + fields[j + 2]] = df_scenario[graph + fields[j]] / df_scenario['GFA_m2'] * 1000
                if scenario_max[graph + fields[j + 2]] < df_scenario[graph + fields[j + 2]]:
                    scenario_max[graph + fields[j + 2]] = df_scenario[graph + fields[j + 2]]

        # plot scenario results
        for i in range(len(graphs)):
            plt.subplot(2, 3, axes[i])
            plt.plot(df_buildings[graphs[i] + fields[2]], df_buildings[graphs[i] + fields[3]], 'o',
                     color=color_palette[n])
            plt.plot(df_scenario[graphs[i] + fields[2]], df_scenario[graphs[i] + fields[3]], 'o',
                     color=color_palette[n],
                     markersize=15)
        legend.extend([scenario_name, scenario_name + ' total'])

    # complete graphs
    plt.plot()
    for i in range(len(graphs)):
        # plot today and target values
        plt.subplot(2, 3, axes[i])
        plt.plot([0, targets[graphs[i] + fields[2]], targets[graphs[i] + fields[2]]],
                 [targets[graphs[i] + fields[3]], targets[graphs[i] + fields[3]], 0], color='k')
        plt.plot([0, values_today[graphs[i] + fields[2]], values_today[graphs[i] + fields[2]]],
                 [values_today[graphs[i] + fields[3]], values_today[graphs[i] + fields[3]], 0], '--', color='k')
        # set axis limits
        if values_today[graphs[i] + fields[2]] > df_scenario[graphs[i] + fields[2]]:
            plt.axis([0, values_today[graphs[i] + fields[2]] * 1.2, 0, values_today[graphs[i] + fields[3]] * 1.2])
        else:
            plt.axis([0, scenario_max[graphs[i] + fields[2]] * 1.2, 0, values_today[graphs[i] + fields[3]] *
                      scenario_max[graphs[i] + fields[2]] / values_today[graphs[i] + fields[2]] * 1.2])
        # plot title
        plt.title(graph_titles[graphs[i]])

    legend.extend(['Benchmark targets', 'Present day values'])
    legend_y = 1.2 + 0.05 * (len(locator_list) - 2)
    plt.legend(legend, bbox_to_anchor=(1.3, legend_y, 0.8, 0.102), loc=0, ncol=1, mode="expand", borderaxespad=0,
               numpoints=1)

    # save to disk
    plt.savefig(output_file)
    plt.clf()
    plt.close()


def calc_benchmark_targets(locator, config):
    """
    This function calculates the embodied, operation, mobility and total targets (ghg_kgm2 and pen_MJm2) for all
    buildings in a scenario.

    The current values for the Swiss case and 2000 W target values for each type of occupancy were taken from the
    literature, when available:

    -   [SIA 2040, 2011]: 'MULTI_RES', 'SINGLE_RES', 'SCHOOL', 'OFFICE'
    -   [BFE, 2012]: 'HOTEL', 'RETAIL', 'FOODSTORE', 'RESTAURANT'

    For the following occupancy types, the target values were calculated based on the approach in [SIA Effizienzpfad,
    2011] for the present-day values assumed in ``calc_benchmark_today``: 'INDUSTRY', 'HOSPITAL', 'GYM', 'SWIMMING',
    'SERVERROOM' and 'COOLROOM'.

    :param locator: an InputLocator instance set to the scenario to compute
    :type locator: InputLocator

    :returns target: dict containing pen_MJm2 and ghg_kgm2 target values
    :rtype target: dict


    ..[SIA 2040, 2011]: Swiss Society of Engineers and Architects (SIA). 2011. "SIA Efficiency Path 2040."
    ..[BFE, 2012]: Bundesamt fur Energie (BFE). 2012. "Arealentwicklung fur die 2000-Watt Gesellschaft: Beurteilungsmethode in
    Anlehnung an den SIA-Effizienzpfad Energie."
    ..[SIA Effizienzpfad, 2011] Swiss Society of Engineers and Architects (SIA). 2011. "SIA Effizienzpfad: Bestimmung
    der Ziel- und Richtwerte mit dem Top-Down Approach."
    ..[SIA 2024, 2015]: Swiss Society of Engineers and Architects (SIA). 2015. "Merkblatt 2024: Raumnutzungsdaten fur
    die Energie- und Gebaeudetechnik."
    """

    # local files
    demand = pd.read_csv(locator.get_total_demand())
    prop_occupancy = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1)
    data_benchmark = locator.get_data_benchmark(config.region)
    occupancy = prop_occupancy.merge(demand, on='Name')

    categories = ['EMBODIED', 'OPERATION', 'MOBILITY', 'TOTAL']
    suffix = ['_GJ', '_ton', '_MJm2', '_kgm2']
    targets = {}
    area_study = 0

    factors = pd.read_excel(data_benchmark, sheetname=categories[0])

    for i in range(len(factors['code'])):
        if factors['code'][i] in occupancy:
            if factors['NRE_target_retrofit'][i] > 0 and factors['CO2_target_retrofit'][i] > 0:
                area_study += (occupancy['GFA_m2'] * occupancy[factors['code'][i]]).sum()

    for category in categories:
        # the targets for the area are set for the existing building stock, i.e., retrofit targets are used
        # (instead of new building targets)
        factors = pd.read_excel(data_benchmark, sheetname=category)
        vt = factors['code']
        pt = factors['NRE_target_retrofit']
        gt = factors['CO2_target_retrofit']

        for j in range(len(suffix)):
            targets[category + suffix[j]] = 0
        for i in range(len(vt)):
            targets[category + suffix[0]] += (occupancy['GFA_m2'] * occupancy[vt[i]] * pt[i]).sum() / 1000
            targets[category + suffix[1]] += (occupancy['GFA_m2'] * occupancy[vt[i]] * gt[i]).sum() / 1000
        targets[category + suffix[2]] += targets[category + suffix[0]] / area_study * 1000
        targets[category + suffix[3]] += targets[category + suffix[1]] / area_study * 1000

    return targets


def calc_benchmark_today(locator, config):
    '''
    This function calculates the embodied, operation, mobility and total targets (ghg_kgm2 and pen_MJm2)
    for the area for the current national trend.

    The current values for the Swiss case for each type of occupancy were taken from the literature, when available:

    -   [SIA 2040, 2011]: 'MULTI_RES', 'SINGLE_RES', 'SCHOOL', 'OFFICE'
    -   [BFE, 2012]: 'HOTEL', 'RETAIL', 'FOODSTORE', 'RESTAURANT'

    For the following occupancy types, the values for construction and operation were calculated based on the approach
    in [SIA Effizienzpfad, 2011]: 'INDUSTRY' and 'HOSPITAL'.

    For the following occupancy types, the current for operation were estimating by obtaining the final energy demand
    for each use from [SIA 2024, 2015] and extrapolating the corresponding primary energy and emissions from the values
    for the other occupancy types: 'GYM', 'SWIMMING', 'SERVERROOM' and 'COOLROOM'.

    Finally, due to a lack of data, multiple values had to be assumed. The embodied energy for the following uses was
    assumed as follows:

    -   'GYM', 'SWIMMING': assumed to be equal to the value for use type 'RETAIL'
    -   'SERVERROOM': assumed to be equal to the value for the use type 'OFFICE'
    -   'COOLROOM': assumed to be equal to the value for the use type 'HOSPITAL'

    Due to lacking mobility data, the following values were assumed:

    -   'INDUSTRY': assumed to be equal to the value for the use type 'OFFICE'
    -   'HOSPITAL': assumed to be equal to the value for the use type 'HOTEL'
    -   'GYM', 'SWIMMING': assumed to be equal to the value for use type 'RETAIL'
    -   'SERVERROOM', 'COOLROOM': assumed negligible


    :param locator: an InputLocator instance set to the scenario to compute
    :type locator: InputLocator

    :returns target: dict containing pen_MJm2 and ghg_kgm2 target values
    :rtype target: dict

    ..[SIA 2040, 2011]: Swiss Society of Engineers and Architects (SIA). 2011. "SIA Efficiency Path 2040."
    ..[BFE, 2012]: Bundesamt fur Energie (BFE). 2012. "Arealentwicklung fur die 2000-Watt Gesellschaft: Beurteilungsmethode in
    Anlehnung an den SIA-Effizienzpfad Energie."
    ..[SIA Effizienzpfad, 2011] Swiss Society of Engineers and Architects (SIA). 2011. "SIA Effizienzpfad: Bestimmung
    der Ziel- und Richtwerte mit dem Top-Down Approach."
    ..[SIA 2024, 2015]: Swiss Society of Engineers and Architects (SIA). 2015. "Merkblatt 2024: Raumnutzungsdaten fur
    die Energie- und Gebaeudetechnik."

    '''

    # local files
    demand = pd.read_csv(locator.get_total_demand())
    prop_occupancy = gpdf.from_file(locator.get_building_occupancy()).drop('geometry', axis=1)
    data_benchmark_today = locator.get_data_benchmark(config.region)
    occupancy = prop_occupancy.merge(demand, on='Name')

    fields = ['Name', 'pen_GJ', 'ghg_ton', 'pen_MJm2', 'ghg_kgm2']
    categories = ['EMBODIED', 'OPERATION', 'MOBILITY', 'TOTAL']
    suffix = ['_GJ', '_ton', '_MJm2', '_kgm2']
    values_today = {}
    area_study = 0

    factors = pd.read_excel(data_benchmark_today, sheetname=categories[0])
    for i in range(len(factors['code'])):
        if factors['code'][i] in occupancy:
            if factors['NRE_today'][i] > 0 and factors['CO2_today'][i] > 0:
                area_study += (occupancy['GFA_m2'] * occupancy[factors['code'][i]]).sum()

    for category in categories:
        factors = pd.read_excel(data_benchmark_today, sheetname=category)
        vt = factors['code']
        pt = factors['NRE_today']
        gt = factors['CO2_today']

        for j in range(len(suffix)):
            values_today[category + suffix[j]] = 0
        for i in range(len(vt)):
            values_today[category + suffix[0]] += (occupancy['GFA_m2'] * occupancy[vt[i]] * pt[i]).sum() / 1000
            values_today[category + suffix[1]] += (occupancy['GFA_m2'] * occupancy[vt[i]] * gt[i]).sum() / 1000
        values_today[category + suffix[2]] += values_today[category + suffix[0]] / area_study * 1000
        values_today[category + suffix[3]] += values_today[category + suffix[1]] / area_study * 1000

    return values_today


def main(config):
    assert os.path.exists(config.benchmark_graphs.project), 'Project not found: %s' % config.benchmark_graphs.project

    print("Running benchmark-graphs with project = %s" % config.benchmark_graphs.project)
    print("Running benchmark-graphs with scenarios = %s" % config.benchmark_graphs.scenarios)
    print("Running benchmark-graphs with output-file = %s" % config.benchmark_graphs.output_file)

    locator_list = [cea.inputlocator.InputLocator(scenario=os.path.join(config.benchmark_graphs.project, scenario)) for
                    scenario in config.benchmark_graphs.scenarios]

    benchmark(locator_list=locator_list, output_file=config.benchmark_graphs.output_file, config=config)


if __name__ == '__main__':
    main(cea.config.Configuration())

