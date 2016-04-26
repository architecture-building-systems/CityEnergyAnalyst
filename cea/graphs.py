# -*- coding: utf-8 -*-
"""
===========================
graphs algorithm
===========================
J. Fonseca  script development          18.09.15
D. Thomas   formatting and cleaning
D. Thomas   integration in toolbox

"""
from __future__ import division
import matplotlib.pyplot as plt
import pandas as pd
import inputlocator


def graphs_demand(locator, analysis_fields):
    """
    algorithm to print graphs in PDF concerning the dynamics of each and all buildings

    Parameters
    ----------
    path_buildings : string
        path to buildings file buildings.shp

    Returns
    -------
    Graphs of each building and total: .Pdf
        heat map file per variable of interest n.
    """

    # get name of files to map
    building_names = pd.read_csv(locator.get_total_demand()).Name
    num_buildings = len(building_names)
    # setup-time
    color_palette = ['g','r','y','c']
    fields = analysis_fields.append('DATE')

    # create figure for every name
    counter = 0
    for name in building_names:
        df = pd.read_csv(locator.get_demand_results_file(name), usecols=fields)
        df.index = pd.to_datetime(df.DATE)
        fig, (ax1, ax2, ax3, ax4) = plt.subplots(4,figsize=(12,16))
        fig.text(0.07, 0.5, 'Demand [kWh]', va='center', rotation='vertical')

        df.plot(ax=ax1, y=analysis_fields, title='YEAR', color=color_palette, label=' ', legend=False)
        df[408:576].plot(ax=ax2, y=analysis_fields, title='WINTER', legend=False, color=color_palette)
        df[4102:4270].plot(ax=ax3, y=analysis_fields, title='SUMMER', legend=False, color=color_palette)
        df[3096:3264].plot(ax=ax4, y=analysis_fields, title='SPRING AND FALL', legend=False, color=color_palette)

        ax4.legend(bbox_to_anchor=(0, -0.4, 1, 0.102), loc=0, ncol=4, mode="expand", borderaxespad=0, fontsize=15)
        fig.subplots_adjust(hspace=0.4)

        # save to disc
        plt.savefig(locator.get_demand_plots_file(name))
        plt.close()
        plt.clf()

        print 'Building No. ' + str(counter + 1) + ' completed out of ' + str(num_buildings)
        counter += 1


def test_graph_demand():
    # HINTS FOR ARCGIS INTERFACE:
    # the user should see all the column names of the total_demands.csv
    # the user can select a maximum of 4 of those column names to graph (analysis fields!
    analysis_fields = ["Ealf_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]

    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    graphs_demand(locator=locator, analysis_fields=analysis_fields)

if __name__ == '__main__':
    test_graph_demand()

