"""
This is the dashboard of CEA
"""
from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator
import plotly.dashboard_objs as dashboard
import plotly
import plotly.graph_objs as go
import plotly.plotly as py
import pandas as pd
from cea.utilities import epwreader
plotly.tools.set_credentials_file(username='duplicado', api_key='c90e0u1bmtuJYipEerPb')


__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

import re

def fileId_from_url(url):
    """Return fileId from a url."""
    raw_fileId = re.findall("~[A-z]+/[0-9]+", url)[0][1: ]
    return raw_fileId.replace('/', ':')

def initialize_dashboard(building , fileId_1, fileId_2, fileId_3):
    my_dboard = dashboard.Dashboard()

    #ADD TITLE, LOGO, LINKS
    my_dboard['settings']['title'] = 'Timeseries data for building '+ building
    my_dboard['settings']['logoUrl'] = 'https://static1.squarespace.com/static/587d65bdbebafb893ba24447/t/587d845d29687f2d2febee75/1492591264954/?format=1500w'
    my_dboard['settings']['links'] = []

    #ADD BOXES
    box_a = {'type': 'box','boxType': 'plot','fileId': fileId_1, 'title': 'scatter-for-dashboard'}
    box_b = {'type': 'box', 'boxType': 'plot', 'fileId': fileId_2, 'title': 'scatter-for-dashboard'}
    box_c = {'type': 'box', 'boxType': 'plot', 'fileId': fileId_3, 'title': 'scatter-for-dashboard'}

    my_dboard.insert(box_a)
    my_dboard.insert(box_b, 'below', 1)
    my_dboard.insert(box_c, 'left', 1)

    py.dashboard_ops.upload(my_dboard, 'test')

def dashboard_demand(locator, config):

    #GET LOCAL VARIABLES
    building = "B04"
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
    analysis_fields2 = ["T_int_C", "T_out_dry_C", "T_out_wet_C", "T_sky_C"]
    analysis_fields3 = ["Twwf_sup_C", "Twwf_re_C", "Thsf_sup_C", "Thsf_re_C", "Tcsf_sup_C",	"Tcsf_re_C"]
    title1 = 'Energy demand'
    title2 = 'Environmental temperature'
    title3 = 'HVAC system temperature'

    #GET TIMESERIES DATA
    df = pd.read_csv(locator.get_demand_results_file(building)).set_index("DATE")

    #GET LOCAL WEATHER CONDITIONS
    weather_data = epwreader.epw_reader(config.weather)[["drybulb_C", "wetbulb_C", "skytemp_C"]]
    df["T_out_dry_C"] = weather_data["drybulb_C"].values
    df["T_out_wet_C"] = weather_data["wetbulb_C"].values
    df["T_sky_C"] = weather_data["skytemp_C"].values

    #GET GRAPHS
    url_fig_1 = timeseries_plot(df, analysis_fields,  title1)
    url_fig_2 = timeseries_plot(df, analysis_fields2, title2)
    url_fig_3 = timeseries_plot(df, analysis_fields3, title3)
    fileId_1 = fileId_from_url(url_fig_1)
    fileId_2 = fileId_from_url(url_fig_2)
    fileId_3 = fileId_from_url(url_fig_3)

    # GET DASHBOARD
    initialize_dashboard(building, fileId_1, fileId_2, fileId_3)

def timeseries_plot(data_frame, analysis_fields, title):

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(title=title, xaxis=dict(rangeselector=dict( buttons=list([
                    dict(count=1,label='1d',step='day',stepmode='backward'),
                    dict(count=1,label='1w',step='week',stepmode='backward'),
                    dict(count=1,label='1m',step='month',stepmode='backward'),
                    dict(step='all')])),type='date'))

    counter = 0
    x = data_frame.index.values
    for field in analysis_fields:
        y = data_frame[field].values
        trace = go.Scatter(x= x, y= y, name = field)
        if counter == 0:
            data = [trace]
        else:
            data.append(trace)
        counter += 1

    # Plot and embed in ipython notebook!
    fig = dict(data=data, layout=layout)
    return py.plot(fig,  auto_open=False, filename=title)


def main(config):

    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    # print out all configuration variables used by this script
    print("Running template with scenario = %s" % config.scenario)
    print("Running template with archetypes = %s" % config.data_helper.archetypes)

    dashboard_demand(locator, config)

if __name__ == '__main__':
    main(cea.config.Configuration())
