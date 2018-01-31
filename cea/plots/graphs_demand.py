# -*- coding: utf-8 -*-
"""
graphs algorithm
"""
from __future__ import division

import os

import matplotlib.pyplot as plt
import pandas as pd

import cea
import cea.inputlocator
import cea.config
import multiprocessing as mp

MAX_ANALYSIS_FIELDS = 4

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def graphs_demand(locator, analysis_fields, multiprocessing, format_demand_file):
    """
    algorithm to print graphs in PDF concerning the dynamics of each and all buildings

    :param locator: an InputLocator set to the scenario to compute
    :type locator: inputlocator.InputLocator

    :param analysis_fields: list of fields (column names in Totals.csv) to analyse
    :type analysis_fields: list[string]

    :param multiprocessing: if set to True, use multiple CPU' for the calculation
    :type multiprocessing: bool

    :returns: - Graphs of each building and total: .Pdf
              - heat map file per variable of interest n.
    """
    color_palette = 'Set1'
    total_file = pd.read_csv(locator.get_total_demand()).set_index('Name')
    building_names = list(total_file.index)
    fields_MWhyr = [field.split('_')[0] + "_MWhyr" for field in analysis_fields]
    total_demand = total_file[fields_MWhyr]
    area_df = total_file['GFA_m2']
    fields_date = analysis_fields + ['DATE']
    num_buildings = len(building_names)

    print('Storing results in: %s' % locator.get_plots_folder())
    if multiprocessing and mp.cpu_count() > 1:
        pool = mp.Pool()
        print("Using %i CPU's" % mp.cpu_count())
        joblist = []
        for name in building_names:
            job = pool.apply_async(create_demand_graph_for_building,
                                   [analysis_fields, area_df, color_palette, fields_date, locator, name,
                                    total_demand])
            joblist.append(job)
        for i, job in enumerate(joblist):
            job.get(60)
            print('Building No. %(bno)i completed out of %(btot)i: %(bname)s' % {'bno': i + 1, 'btot': num_buildings,
                                                                                 'bname': building_names[i]})
        pool.close()
    else:
        for i, name in enumerate(building_names):
            create_demand_graph_for_building(analysis_fields, area_df, color_palette, fields_date, locator, name,
                                             total_demand)
            print('Building No. %(bno)i completed out of %(btot)i: %(bname)s' % {'bno': i + 1, 'btot': num_buildings,
                                                                                 'bname': building_names[i]})


def create_demand_graph_for_building(analysis_fields, area_df, color_palette, fields_date, locator, name, total_demand):
    # CREATE PDF FILE
    from matplotlib.backends.backend_pdf import PdfPages
    pdf = PdfPages(locator.get_demand_plots_file(name))
    # CREATE FIRST PAGE WITH TIMESERIES
    df = pd.read_csv(locator.get_demand_results_file(name), usecols=fields_date)
    df.index = pd.to_datetime(df.DATE)
    fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, figsize=(12, 16))
    fig.text(0.07, 0.5, 'Demand [kW]', va='center', rotation='vertical')
    df.plot(ax=ax1, y=analysis_fields, title='YEAR', colormap=color_palette, label=' ', legend=False)
    df[408:576].plot(ax=ax2, y=analysis_fields, title='WINTER', legend=False, colormap=color_palette)
    df[4102:4270].plot(ax=ax3, y=analysis_fields, title='SUMMER', legend=False, colormap=color_palette)
    df[3096:3264].plot(ax=ax4, y=analysis_fields, title='SPRING AND FALL', legend=False, colormap=color_palette)
    ax4.legend(bbox_to_anchor=(0, -0.4, 1, 0.102), loc=0, ncol=4, mode="expand", borderaxespad=0, fontsize=15)
    ax1.set_xlabel('')
    ax2.set_xlabel('')
    ax3.set_xlabel('')
    ax4.set_xlabel('')
    fig.subplots_adjust(hspace=0.5)
    pdf.savefig()
    plt.close()
    # CREATE SECOND PAGE WITH PLOTS OF TOTAL VALUES
    fig = plt.figure(figsize=(12, 6))
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)
    dftogether = pd.DataFrame({'TOTAL': total_demand.ix[name]}).T
    dftogether.plot(ax=ax1, kind='bar', title='TOTAL YEARLY CONSUMPTION', legend=False, stacked=True,
                    colormap=color_palette)
    ax1.set_ylabel('Yearly Consumption  [MWh/yr]')
    dftogether2 = pd.DataFrame({'EUI': (total_demand.ix[name] / area_df.ix[name] * 1000)}).T
    dftogether2.plot(ax=ax2, kind='bar', legend=False, title='ENERGY USE INTENSITY', stacked=True,
                     colormap=color_palette)
    ax2.set_ylabel('Energy Use Intensity EUI [kWh/m2.yr]')
    pdf.savefig()
    plt.close()
    plt.clf()
    pdf.close()


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario

    print('Running demand-graphs with scenario = %s' % config.scenario)
    print('Running demand-graphs with multiprocessing = %s' % config.multiprocessing)
    print('Running demand-graphs with analysis-fields = %s' % config.demand_graphs.analysis_fields)

    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    graphs_demand(locator=locator, analysis_fields=config.demand_graphs.analysis_fields,
                  multiprocessing=config.multiprocessing, format_demand_file = config.demand.format_output)

if __name__ == '__main__':
    main(cea.config.Configuration())



