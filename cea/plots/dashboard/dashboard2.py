"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator
from plotly import tools
import plotly.plotly as py
from plotly.offline import plot
import plotly.graph_objs as go

import pandas as pd
from cea.utilities import epwreader


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

import re


def dashboard_demand(locator, config):

    #GET LOCAL VARIABLES
    building = "B05"
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
    analysis_fields2 = ["T_int_C", "T_out_dry_C", "T_out_wet_C", "T_sky_C"]
    analysis_fields3 = ["Twwf_sup_C", "Twwf_re_C", "Thsf_sup_C", "Thsf_re_C", "Tcsf_sup_C",	"Tcsf_re_C"]
    analysis_fields4 = ["mcphsf_kWperC","mcpcsf_kWperC","mcpwwf_kWperC"]
    title1 = 'Energy demand'
    title2 = 'Outdoor and indoor temperature'
    title3 = 'HVAC system temperature'
    title4 = 'HVAC system mass flow rates'
    title5 = 'Ideal heating preset schedule'
    title6 = 'Load duration curve'

    #GET TIMESERIES DATA
    df = pd.read_csv(locator.get_demand_results_file(building)).set_index("DATE")

    #GET LOCAL WEATHER CONDITIONS
    weather_data = epwreader.epw_reader(config.weather)[["drybulb_C", "wetbulb_C", "skytemp_C"]]
    df["T_out_dry_C"] = weather_data["drybulb_C"].values
    df["T_out_wet_C"] = weather_data["wetbulb_C"].values
    df["T_sky_C"] = weather_data["skytemp_C"].values

    #GET GRAPHS
    traces_fig_1 = timeseries_plot(df, analysis_fields)
    traces_fig_2 = timeseries_plot(df, analysis_fields2)
    traces_fig_3 = timeseries_plot(df, analysis_fields3)
    traces_fig_4 = timeseries_plot(df, analysis_fields4)
    traces_fig_5 = system_temp_vs_outdoor_temp(df, analysis_fields3)
    traces_fig_6 = load_duration_curve(df, analysis_fields)

    fig = tools.make_subplots(rows=3, cols=2, subplot_titles=(title1, title2,  title3, title4, title5, title6))
    for trace in traces_fig_1:
        fig.append_trace(trace, 1, 1)
    for trace in traces_fig_2:
        fig.append_trace(trace, 1, 2)
    for trace in traces_fig_3:
        fig.append_trace(trace, 2, 1)
    for trace in traces_fig_4:
        fig.append_trace(trace, 2, 2)
    for trace in traces_fig_5:
        fig.append_trace(trace, 3, 1)
    for trace in traces_fig_6:
        fig.append_trace(trace, 3, 2)

    fig['layout'].update(height=1800, width=1200, title='Multiple Subplots' +
                                                      ' with Titles')

    plot(fig, auto_open=False, filename=locator.get_timeseries_plots_file(building))


def timeseries_plot(data_frame, analysis_fields):

    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    x = data_frame.index.values
    for field in analysis_fields:
        y = data_frame[field].values
        trace = go.Scatter(x= x, y= y, name = field)
        traces.append(trace)
    return traces

def system_temp_vs_outdoor_temp(data_frame, analysis_fields):

    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    x = data_frame["T_out_dry_C"].values
    for field in analysis_fields:
        y = data_frame[field].values
        trace = go.Scatter(x= x, y= y, name = field, mode = 'markers')
        traces.append(trace)
    return traces

def load_duration_curve(data_frame, analysis_fields):

    # CREATE FIRST PAGE WITH TIMESERIES
    traces = []
    x = range(8760)
    for field in analysis_fields:
        data_frame.sort_values(by=field, ascending=False, inplace=True)
        y = data_frame[field].values
        trace = go.Scatter(x= x, y= y, name = field)
        traces.append(trace)
    return traces

def main(config):

    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running template with scenario = %s" % config.scenario)
    print("Running template with archetypes = %s" % config.data_helper.archetypes)

    dashboard_demand(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
