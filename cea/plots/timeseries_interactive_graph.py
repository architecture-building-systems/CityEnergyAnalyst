# -*- coding: utf-8 -*-
"""
Dynamic demand graphs algorithm
"""
from __future__ import division

import pandas as pd

import multiprocessing as mp
from plotly.offline import plot
import plotly.graph_objs as go
import cea.config


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def timeseries_graph(locator, analysis_fields):
    """
    algorithm to print graphs in html for easy visualization

    :param locator: an InputLocator set to the scenario to compute
    :type locator: inputlocator.InputLocator

    :param analysis_fields: list of fields (column names in Totals.csv) to analyse
    :type analysis_fields: list[string]

    :returns: - Graphs of each building and total: .Pdf
              - heat map file per variable of interest n.
    """

    # get name of files to map
    building_names = pd.read_csv(locator.get_total_demand()).Name
    num_buildings = building_names.count()
    fields_date = analysis_fields + ['DATE']

    layout = dict(title='Building data timeseries', xaxis=dict(rangeselector=dict( buttons=list([
                    dict(count=1,label='1d',step='day',stepmode='backward'),
                    dict(count=1,label='1w',step='week',stepmode='backward'),
                    dict(count=1,label='1m',step='month',stepmode='backward'),
                    dict(count=6,label='6m',step='month', stepmode='backward'),
                    dict(count=1,label='1y',step='year',stepmode='backward'),
                    dict(step='all') ])),rangeslider=dict(),type='date'))

    config = cea.config.Configuration(locator.scenario_path)
    if config.multiprocessing:
        pool = mp.Pool()
        print("Using %i CPU's" % mp.cpu_count())
        joblist = []
        for name in building_names:
            job = pool.apply_async(create_demand_graph_for_building,
                                   [analysis_fields, fields_date, locator, name, layout])
            joblist.append(job)
        for i, job in enumerate(joblist):
            job.get(60)
            print('Building No. %(bno)i completed out of %(btot)i' % {'bno':i + 1, 'btot':num_buildings})
        pool.close()
    else:
        for i, name in enumerate(building_names):
            create_demand_graph_for_building(analysis_fields, fields_date, locator, name, layout)
            print('Building No. %(bno)i completed out of %(btot)i' % {'bno': i + 1, 'btot': num_buildings})

def create_demand_graph_for_building(analysis_fields, fields_date, locator, name, layout):

    # CREATE FIRST PAGE WITH TIMESERIES
    df = pd.read_csv(locator.get_demand_results_file(name), usecols=fields_date).set_index("DATE")
    counter = 0
    for field in analysis_fields:
        trace = go.Scatter(x= df.index.values, y= df[field].values, name = field)
        if counter == 0:
            data = [trace]
        else:
            data.append(trace)
        counter += 1

    # Plot and embed in ipython notebook!
    fig = dict(data=data, layout=layout)
    plot(fig,  auto_open=False, filename=locator.get_timeseries_plots_file(name))

def run_as_script(scenario_path=None, analysis_fields=["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]):
    # HINTS FOR ARCGIS INTERFACE:
    # the user should see all the column names of the total_demands.csv
    # the user can select a maximum of 4 of those column names to graph (analysis fields!
    import cea.globalvar
    import cea.inputlocator

    gv = cea.globalvar.GlobalVariables()
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
    if scenario_path is None:
        scenario_path = cea.config.Configuration().default_scenario
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

    timeseries_graph(locator=locator, analysis_fields=analysis_fields)
    print('done.')

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    parser.add_argument('-a', '--analysis_fields', default='Ealf_kWh;Qhsf_kWh;Qwwf_kWh;Qcsf_kWh;Qcs_lat_kWh;Qhs_lat_kWh',
                        help='Fields to analyse (separated by ";")')
    args = parser.parse_args()
    run_as_script(scenario_path=args.scenario, analysis_fields=args.analysis_fields.split(';')[:4])