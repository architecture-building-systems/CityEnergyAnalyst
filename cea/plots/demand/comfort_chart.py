# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
import math
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objs as go
from plotly.offline import plot
import cea.inputlocator
import cea.plots.demand
import cea.config
from cea.plots.variable_naming import LOGO, COLORS_TO_RGB


__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

# constants
# vertices of PMV comfort zones visually extracted from graph:
# [https://www.researchgate.net/figure/Psychrometric-chart-with-superimposed-comfort-zones-for-05-and-10-clo-summer-and_fig2_261566668]
VERTICES_WINTER_COMFORT = [(21.5, 0.0), (26.5, 0.0), (24.0, 12.0), (19.5, 12.0)]  # (T, moisture ratio)
VERTICES_SUMMER_COMFORT = [(25.0, 0.0), (28.25, 0.0), (26.75, 12.0), (24.0, 12.0)]  # (T, moisture ratio)

# layout of graph and table
YAXIS_DOMAIN_GRAPH = [0, 0.8]
XAXIS_DOMAIN_GRAPH = [0.2, 0.8]


class ComfortChartPlot(cea.plots.demand.DemandPlotBase):
    name = "Comfort Chart"

    expected_parameters = dict(cea.plots.demand.DemandPlotBase.expected_parameters,
                               region='general:region')

    def __init__(self, project, parameters):
        super(ComfortChartPlot, self).__init__(project, parameters)
        if len(self.buildings) > 1:
            self.buildings = [self.buildings[0]]
        self.data = self.hourly_loads[self.hourly_loads['Name'].isin(self.buildings)]
        self.analysis_fields = None
        self.layout = create_layout(self.title)

    def calc_graph(self):
        # calculate points of comfort in different conditions
        dict_graph = calc_data(self.data, self.parameters['region'], self.locator)

        # create scatter of comfort
        traces_graph = calc_graph(dict_graph)

        # create lines of constant relative humidity
        traces_relative_humidity = create_relative_humidity_lines()
        traces_graph.extend(traces_relative_humidity)

        # add text for winter / summer comfort zones
        trace_layout = go.Scatter(
            x=[23, 26.5],
            y=[3, 3],
            text=['Winter comfort zone',
                  'Summer comfort zone'],
            mode='text',
            showlegend=False
        )
        traces_graph.append(trace_layout)
        return traces_graph

def comfort_chart(data_frame, title, output_path, config, locator):
    """
    Main function of comfort chart plot

    :param data_frame: results from demand calculation
    :type data_frame: pandas.DataFrame
    :param title: title of plot
    :type title: string
    :param output_path: path to output folder
    :type output_path: system path
    :return:
    """

    # calculate points of comfort in different conditions
    dict_graph = calc_data(data_frame, config.region, locator)

    # create scatter of comfort
    traces_graph = calc_graph(dict_graph)

    # create lines of constant relative humidity
    traces_relative_humidity = create_relative_humidity_lines()
    traces_graph.extend(traces_relative_humidity)

    # create layout
    layout = create_layout(title)

    # create table
    traces_table = calc_table(dict_graph)
    # add table in first place of traces
    traces_graph.insert(0, traces_table)

    # create figure
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': [traces_graph], 'layout': layout}


def create_layout(title):
    """
    Creates layout of plot, including polygon comfort areas

    :param title: title of plot
    :type title: string
    :return: trace_layout, layout
    :rtype: plotly.graph_objs.trace, plotly.graph_objs.layout
    """

    layout = {
        'xaxis': {
            'title': 'Operative Temperature [Â°C]',
            'range': [5, 35],
            'domain': XAXIS_DOMAIN_GRAPH
        },
        'yaxis': {
            'title': 'Moisture content [g/kg dry air]',
            'side': 'right',
            'range': [0, 25],
            'domain': YAXIS_DOMAIN_GRAPH,
            'showgrid': True,
        },
        'legend': {
            'x': XAXIS_DOMAIN_GRAPH[0],
            'y': YAXIS_DOMAIN_GRAPH[1] - 0.05,
        },
        'shapes': [
            # Winter comfort zone
            {
                'type': 'path',
                'path': ' M {},{} L{},{} L{},{} L{},{} Z'.format(VERTICES_WINTER_COMFORT[0][0],
                                                                 VERTICES_WINTER_COMFORT[0][1],
                                                                 VERTICES_WINTER_COMFORT[1][0],
                                                                 VERTICES_WINTER_COMFORT[1][1],
                                                                 VERTICES_WINTER_COMFORT[2][0],
                                                                 VERTICES_WINTER_COMFORT[2][1],
                                                                 VERTICES_WINTER_COMFORT[3][0],
                                                                 VERTICES_WINTER_COMFORT[3][1]),
                'fillcolor': COLORS_TO_RGB['green'],
                'opacity': 0.4,
                'line': {
                    'color': COLORS_TO_RGB['green'],
                },
            },
            # Summer comfort zone
            {
                'type': 'path',
                'path': ' M {},{} L{},{} L{},{} L{},{} Z'.format(VERTICES_SUMMER_COMFORT[0][0],
                                                                 VERTICES_SUMMER_COMFORT[0][1],
                                                                 VERTICES_SUMMER_COMFORT[1][0],
                                                                 VERTICES_SUMMER_COMFORT[1][1],
                                                                 VERTICES_SUMMER_COMFORT[2][0],
                                                                 VERTICES_SUMMER_COMFORT[2][1],
                                                                 VERTICES_SUMMER_COMFORT[3][0],
                                                                 VERTICES_SUMMER_COMFORT[3][1]),
                'fillcolor': COLORS_TO_RGB['yellow'],
                'opacity': 0.4,
                'line': {
                    'color': COLORS_TO_RGB['yellow'],
                },
            },

        ]
    }

    return layout


def calc_graph(dict_graph):
    """
    creates scatter of comfort and curves of constant relative humidity

    :param dict_graph: contains comfort conditions to plot, output of comfort_chart.calc_data()
    :type dict_graph: dict
    :return: traces of scatter plot of 4 comfort conditions
    :rtype: list of plotly.graph_objs.Scatter
    """

    traces = []

    # draw scatter of comfort conditions in building
    trace = go.Scatter(x=dict_graph['t_op_occupied_winter'], y=dict_graph['x_int_occupied_winter'],
                       name='occupied hours winter', mode='markers', marker=dict(color=COLORS_TO_RGB['red']))
    traces.append(trace)
    trace = go.Scatter(x=dict_graph['t_op_unoccupied_winter'], y=dict_graph['x_int_unoccupied_winter'],
                       name='unoccupied hours winter', mode='markers', marker=dict(color=COLORS_TO_RGB['blue']))
    traces.append(trace)
    trace = go.Scatter(x=dict_graph['t_op_occupied_summer'], y=dict_graph['x_int_occupied_summer'],
                       name='occupied hours summer', mode='markers', marker=dict(color=COLORS_TO_RGB['purple']))
    traces.append(trace)
    trace = go.Scatter(x=dict_graph['t_op_unoccupied_summer'], y=dict_graph['x_int_unoccupied_summer'],
                       name='unoccupied hours summer', mode='markers', marker=dict(color=COLORS_TO_RGB['orange']))
    traces.append(trace)

    return traces


def create_relative_humidity_lines():
    """
    calculates curves of constant relative humidity for plotting (10% - 100% in steps of 10%)

    :return: list of plotly table trace
    :rtype: list of plotly.graph_objs.Scatter
    """

    traces = []

    # draw lines of constant relative humidity for psychrometric chart
    rh_lines = np.linspace(0.1, 1, 10)  # lines from 10% to 100%
    t_axis = np.linspace(-5, 45, 50)
    P_ATM = 101325  # Pa, standard atmospheric pressure at sea level

    for rh_line in rh_lines:

        y_data = calc_constant_rh_curve(t_axis, rh_line, P_ATM)
        trace = go.Scatter(x=t_axis, y=y_data, mode='line', name="{:.0%} relative humidity".format(rh_line),
                           line=dict(color=COLORS_TO_RGB['grey_light'], width=1), showlegend=False)
        traces.append(trace)

    return traces


def calc_data(data_frame, region, locator):
    """
    split up operative temperature and humidity points into 4 categories for plotting
    (1) occupied in heating season
    (2) un-occupied in heating season
    (3) occupied in cooling season
    (4) un-occupied in cooling season

    :param data_frame: results from demand calculation
    :type data_frame: pandas.DataFrame
    :param config: cea config
    :type config: cea.config.Configuration
    :param locator: cea input locator
    :type locator: cea.inputlocator.InputLocator
    :return: dict of lists with operative temperatures and moistures
     \for 4 conditions (summer (un)occupied, winter (un)occupied)
    :rtype: dict
    """

    # read region-specific control parameters (identical for all buildings), i.e. heating and cooling season
    prop_region_specific_control = pd.read_excel(locator.get_archetypes_system_controls(region),
                                                 true_values=['True', 'TRUE', 'true'],
                                                 false_values=['False', 'FALSE', 'false', u'FALSE'],
                                                 dtype={'has-heating-season': bool,
                                                        'has-cooling-season': bool})  # read database
    # extract data from df
    has_winter = prop_region_specific_control['has-heating-season'][0]
    has_summer = prop_region_specific_control['has-cooling-season'][0]
    winter_end = prop_region_specific_control['heating-season-end'][0]
    winter_start = prop_region_specific_control['heating-season-start'][0]
    summer_end = prop_region_specific_control['cooling-season-end'][0]
    summer_start = prop_region_specific_control['cooling-season-start'][0]

    # split up operative temperature and humidity points into 4 categories
    # (1) occupied in heating season
    # (2) un-occupied in heating season
    # (3) occupied in cooling season
    # (4) un-occupied in cooling season

    t_op_occupied_summer = []
    x_int_occupied_summer = []
    t_op_unoccupied_summer = []
    x_int_unoccupied_summer = []
    t_op_occupied_winter = []
    x_int_occupied_winter = []
    t_op_unoccupied_winter = []
    x_int_unoccupied_winter = []

    # convert index from string to datetime (because someone changed the type)
    data_frame.index = pd.to_datetime(data_frame.index)

    # find indexes of the 4 categories
    for index, row in data_frame.iterrows():

        # occupied in winter
        if row['people'] > 0 and has_winter and datetime_in_season(index, winter_start, winter_end):
            t_op_occupied_winter.append(row['theta_o_C'])
            x_int_occupied_winter.append(row['x_int'])
        # unoccupied in winter
        elif row['people'] == 0 and has_winter and datetime_in_season(index, winter_start, winter_end):
            t_op_unoccupied_winter.append(row['theta_o_C'])
            x_int_unoccupied_winter.append(row['x_int'])
        # occupied in summer
        elif row['people'] > 0 and has_summer and datetime_in_season(index, summer_start, summer_end):
            t_op_occupied_summer.append(row['theta_o_C'])
            x_int_occupied_summer.append(row['x_int'])
        # unoccupied in summer
        elif row['people'] == 0 and has_summer and datetime_in_season(index, summer_start, summer_end):
            t_op_unoccupied_summer.append(row['theta_o_C'])
            x_int_unoccupied_summer.append(row['x_int'])

    return {'t_op_occupied_winter': t_op_occupied_winter, 'x_int_occupied_winter': x_int_occupied_winter,
            't_op_unoccupied_winter': t_op_unoccupied_winter, 'x_int_unoccupied_winter': x_int_unoccupied_winter,
            't_op_occupied_summer': t_op_occupied_summer, 'x_int_occupied_summer': x_int_occupied_summer,
            't_op_unoccupied_summer': t_op_unoccupied_summer, 'x_int_unoccupied_summer': x_int_unoccupied_summer}


def calc_table(dict_graph):
    """
    draws table of monthly energy balance

    :param dict_graph: dict containing the lists of summer, winter, occupied and unoccupied operative temperatures and
     \moisture ratios, i.e. the results of comfort_chart.calc_data
    :type dict_graph: dict
    :return: plotly table trace
    :rtype: plotly.graph_objs.Table
    """

    # create table arrays
    # check winter comfort
    count_winter_comfort, count_winter_uncomfort = check_comfort(dict_graph['t_op_occupied_winter'],
                                                                 dict_graph['x_int_occupied_winter'],
                                                                 VERTICES_WINTER_COMFORT)
    winter_hours = len(dict_graph['t_op_occupied_winter'])
    perc_winter_comfort = count_winter_comfort/winter_hours if winter_hours > 0 else 0
    cell_winter_comfort = "{} ({:.0%})".format(count_winter_comfort, perc_winter_comfort)
    perc_winter_uncomfort = count_winter_uncomfort / winter_hours if winter_hours > 0 else 0
    cell_winter_uncomfort = "{} ({:.0%})".format(count_winter_uncomfort, perc_winter_uncomfort)

    # check summer comfort
    count_summer_comfort, count_summer_uncomfort = check_comfort(dict_graph['t_op_occupied_summer'],
                                                                 dict_graph['x_int_occupied_summer'],
                                                                 VERTICES_SUMMER_COMFORT)
    summer_hours = len(dict_graph['t_op_occupied_summer'])
    perc_summer_comfort = count_summer_comfort / summer_hours if summer_hours > 0 else 0
    cell_summer_comfort = "{} ({:.0%})".format(count_summer_comfort, perc_summer_comfort)
    perc_summer_uncomfort = count_summer_uncomfort / summer_hours if summer_hours > 0 else 0
    cell_summer_uncomfort = "{} ({:.0%})".format(count_summer_uncomfort, perc_summer_uncomfort)

    # draw table
    table = go.Table(domain=dict(x=[0.0, 1], y=[YAXIS_DOMAIN_GRAPH[1], 1.0]),
                     header=dict(values=['condition', 'comfort [h]', 'uncomfort [h]']),
                     cells=dict(values=[['summer occupied', 'winter occupied'],
                                        [cell_summer_comfort, cell_winter_comfort],
                                        [cell_summer_uncomfort, cell_winter_uncomfort]]),
                     visible=True)

    return table


def check_comfort(temperature, moisture, vertices_comfort_area):
    """
    checks if a point of operative temperature and moisture ratio is inside the polygon of comfort defined by its
     vertices, the function only works if the polygon has constant moisture ratio edges

    :param temperature: operative temperature [Â°C]
    :type temperature: list
    :param moisture: moisture ratio [g/kg dry air]
    :type moisture: list
    :param vertices_comfort_area: vertices of operative temperature and moisture ratio ([Â°C],[g/kg dry air])
    :type vertices_comfort_area: list of tuples
    :return: hours of comfort, hours of uncomfort
    :rtype: double, double
    """
    # check winter comfort
    # equation for lower temp boundary in winter t = m*x + b
    b_low = vertices_comfort_area[0][0]
    m_low = (vertices_comfort_area[3][0] - b_low) / (vertices_comfort_area[3][1] - vertices_comfort_area[0][1])
    b_high = vertices_comfort_area[1][0]
    m_high = (vertices_comfort_area[2][0] - b_high) / (vertices_comfort_area[2][1] - vertices_comfort_area[1][1])

    count_winter_comfort = 0
    for t, x in zip(temperature, moisture):

        if vertices_comfort_area[0][1] <= x <= vertices_comfort_area[2][1]:

            if m_low * x + b_low <= t <= m_high * x + b_high:
                count_winter_comfort = count_winter_comfort + 1
            else:
                pass
        else:
            pass

    count_winter_uncomfort = len(temperature) - count_winter_comfort

    return count_winter_comfort, count_winter_uncomfort


def datetime_in_season(dt, season_start, season_end):
    """
    small function to determine if a datetime index of the results dataframe is in heating season (winter)
     or cooling season (summer)

    :param dt: datetime, index of resulting csv of cea.demand_main
    :type dt: datetime.datetime
    :param season_start: start of season ["MM-DD"]
    :type season_start: string
    :param season_end: end of season ["MM-DD"]
    :type season_end: string
    :return: True or False
    :rtype: bool
    """

    month_start, day_start = map(int, season_start.split('-'))
    season_start_dt = datetime.datetime(dt.year, month_start, day_start, 0)
    month_end, day_end = map(int, season_end.split('-'))
    season_end_dt = datetime.datetime(dt.year, month_end, day_end, 23)

    if season_start_dt < season_end_dt:

        if season_start_dt <= dt <= season_end_dt:
            return True
        else:
            return False

    elif season_start_dt > season_end_dt:
        if dt <= season_end_dt or dt >= season_start_dt:
            return True
        else:
            return False


def p_ws_from_t(t_celsius):
    """
    Calculate water vapor saturation pressure over liquid water for the temperature range of 0 to 200Â°C
    Eq (6) in "CHAPTER 6 - PSYCHROMETRICS" in "2001 ASHRAE Fundamentals Handbook (SI)"

    :param t_celsius: temperature [Â°C]
    :type t_celsius: double
    :return: water vapor saturation pressure [Pa]
    :rtype: double
    """

    # convert temperature
    t = t_celsius + 273.15

    # constants
    C8 = -5.8002206E+03
    C9 = 1.3914993E+00
    C10 = -4.8640239E-02
    C11 = 4.1764768E-05
    C12 = -1.4452093E-08
    C13 = 6.5459673E+00

    return math.exp(C8/t+C9+C10*t+C11*t**2+C12*t**3+C13*math.log1p(t))


def p_w_from_rh_p_and_ws(rh, p_ws):
    """
    Calculate water vapor pressure from relative humidity and water vapor saturation pressure
    Eq(6) in "CHAPTER 6 - PSYCHROMETRICS" in "2001 ASHRAE Fundamentals Handbook (SI)"

    :param rh: relative humidity [-]
    :type rh: double
    :param p_ws: water vapor saturation pressure [Pa]
    :type p_ws: double
    :return: water vapor pressure [Pa]
    :rtype: double
    """

    return rh * p_ws


def hum_ratio_from_p_w_and_p(p_w, p):
    """
    Calculate humidity ratio from water vapor pressure and atmospheric pressure
    Eq(22) in "CHAPTER 6 - PSYCHROMETRICS" in "2001 ASHRAE Fundamentals Handbook (SI)"

    :param p_w: water vapor pressure [Pa]
    :type p_w: double
    :param p: atmospheric pressure [Pa]
    :type p: double
    :return: humidity ratio [g / kg dry air]
    :rtype: double
    """

    return 0.62198 * p_w/(p-p_w)


def calc_constant_rh_curve(t_array, rh, p):
    """
    Calculates curves of humidity ratio at different temperatures for a constant relative humidity and pressure

    :param t_array: array pf temperatures [Â°C]
    :type t_array: numpy.array
    :param rh: relative humidity [-]
    :type rh: double
    :param p: atmospheric pressure [Pa]
    :type p: double
    :return: humidity ratio [g / kg dry air]
    :rtype: numpy.array
    """

    p_ws = np.vectorize(p_ws_from_t)(t_array)
    p_w = p_w_from_rh_p_and_ws(rh, p_ws)

    return hum_ratio_from_p_w_and_p(p_w, p) * 1000


if __name__ == '__main__':
    def main():
        import cea.config
        import cea.inputlocator

        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(config.scenario)

        ComfortChartPlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)
        ComfortChartPlot(config, locator, [locator.get_zone_building_names()[1]]).plot(auto_open=True)
        ComfortChartPlot(config, locator, [locator.get_zone_building_names()[2]]).plot(auto_open=True)
    main()
