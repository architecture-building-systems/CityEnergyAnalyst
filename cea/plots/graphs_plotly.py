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

from plotly.offline import plot
import plotly.graph_objs as go


import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def graphs_demand(locator, analysis_fields, gv):
    """
    algorithm to print graphs in PDF concerning the dynamics of each and all buildings

    Parameters
    ----------

    :param locator: an InputLocator set to the scenario to compute
    :type locator: inputlocator.InputLocator

    :param analysis_fields: list of fields (column names in Totals.csv) to analyse
    :type analysis_fields: list[string]

    Returns
    -------
    Graphs of each building and total: .Pdf
        heat map file per variable of interest n.
    """

    # get name of files to map
    building_names = pd.read_csv(locator.get_total_demand()).Name
    fields_date = analysis_fields + ['DATE']

    layout = dict(title='Building data timeseries', xaxis=dict(rangeselector=dict( buttons=list([
                    dict(count=1,label='1d',step='day',stepmode='backward'),
                    dict(count=1,label='1w',step='week',stepmode='backward'),
                    dict(count=1,label='1m',step='month',stepmode='backward'),
                    dict(count=6,label='6m',step='month', stepmode='backward'),
                    dict(count=1,label='1y',step='year',stepmode='backward'),
                    dict(step='all') ])),rangeslider=dict(),type='date'))

    for name in building_names[:1]:
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
        plot(fig,  auto_open=False, filename=locator.get_demand_plots_file(name))

def test_graph_demand():
    # HINTS FOR ARCGIS INTERFACE:
    # the user should see all the column names of the total_demands.csv
    # the user can select a maximum of 4 of those column names to graph (analysis fields!
    from cea import globalvar
    analysis_fields = ["Ealf_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]

    locator = cea.inputlocator.InputLocator(scenario_path=r'C:\reference-case-zug\baseline')
    gv = globalvar.GlobalVariables()
    graphs_demand(locator=locator, analysis_fields=analysis_fields, gv=gv)
    print 'test_graph_demand() succeeded'

if __name__ == '__main__':
    test_graph_demand()

