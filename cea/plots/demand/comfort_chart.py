# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function

import math
import plotly.graph_objs as go
from plotly.offline import plot
import datetime

import cea.inputlocator
import cea.config
from cea.plots.color_code import ColorCodeCEA
from cea.plots.variable_naming import LOGO

COLOR = ColorCodeCEA()
import pandas as pd
import numpy as np

# constants
# visually extracted from graph:
# [https://www.researchgate.net/figure/Psychrometric-chart-with-superimposed-comfort-zones-for-05-and-10-clo-summer-and_fig2_261566668]

VERTICES_WINTER_COMFORT = [(21.5, 0.0), (26.5, 0.0), (24.0, 12.0), (19.5, 12.0)]  # (T, moisture ratio)
VERTICES_SUMMER_COMFORT = [(25.0, 0.0), (28.25, 0.0), (26.75, 12.0), (24.0, 12.0)]  # (T, moisture ratio)


def comfort_chart(data_frame, analysis_fields, title, output_path):
    # Calculate Energy Balance
    dict_graph = calc_data(data_frame)

    # CALCULATE GRAPH
    traces_graph = calc_graph(dict_graph)

    # CALCULATE TABLE
    traces_table = calc_table(dict_graph)


    # LAYOUT IN JSON FOR READABILITY
    trace_layout = go.Scatter(
        x=[23, 26.5],
        y=[3, 3],
        text=['Winter comfort zone',
              'Summer comfort zone'],
        mode='text',
        showlegend=False
    )
    traces_graph.append(trace_layout)



    layout = {
        'images': LOGO,
        'title': title,
        'xaxis': {
            'title': 'Operative Temperature [°C]',
            'range': [5, 35],
            'domain' : [0.3, 1]
        },
        'yaxis': {
            'title': 'Moisture content [g/kg dry air]',
            'side': 'right',
            'range': [0, 25],
            'domain': [0, 1],
            'showgrid': True,
        },
        'legend': {
            'x': 0.35,
            'y': 0.95,
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
                'fillcolor': COLOR.COLORS['green'],
                'opacity' : 0.4,
                'line': {
                    'color': COLOR.COLORS['green'],
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
                'fillcolor': COLOR.COLORS['yellow'],
                'opacity' : 0.4,
                'line': {
                    'color': COLOR.COLORS['yellow'],
                },
            },

        ]
    }

    # PLOT GRAPH
    traces_graph.insert(0, traces_table)


    #layout = go.Layout(images=LOGO, title=title,
                       #yaxis=dict(title='Moisture content [g/kg dry air]', range=[0.0, 30.0], side='right', domain=[0.0, 1.0]),
                      # xaxis=dict(title='Operative Temperature [°C]', range=[0.0, 35.0]),
                       #shapes=[]

                       #)

    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': [traces_graph], 'layout': layout}


def calc_graph(dict_graph):
    """
    draws building heat balance graph

    :param analysis_fields:
    :param data_frame:
    :return:
    """

    graph = []

    # draw scatter of comfort conditions in building
    trace = go.Scatter(x=dict_graph['t_op_occupied_winter'], y=dict_graph['x_int_occupied_winter'],
                       name='occupied hours winter', mode='markers', marker=dict(color=COLOR.COLORS['red']))  # , text = total_perc_txt)
    graph.append(trace)
    trace = go.Scatter(x=dict_graph['t_op_unoccupied_winter'], y=dict_graph['x_int_unoccupied_winter'],
                       name='unoccupied hours winter', mode='markers', marker=dict(color=COLOR.COLORS['blue']))  # , text = total_perc_txt)
    graph.append(trace)
    trace = go.Scatter(x=dict_graph['t_op_occupied_summer'], y=dict_graph['x_int_occupied_summer'],
                       name='occupied hours summer', mode='markers', marker=dict(color=COLOR.COLORS['purple']))  # , text = total_perc_txt)
    graph.append(trace)
    trace = go.Scatter(x=dict_graph['t_op_unoccupied_summer'], y=dict_graph['x_int_unoccupied_summer'],
                       name='unoccupied hours summer', mode='markers', marker=dict(color=COLOR.COLORS['orange']))  # , text = total_perc_txt)
    graph.append(trace)

    # draw lines of constant relative humidity for psychrometric chart
    rh_lines = np.linspace(0.1, 1, 10)
    t_axis = np.linspace(-5,45,50)
    P_ATM = 101325 # kPa, standard atmospheric pressure at sea level

    for rh_line in rh_lines:

        y_data = calc_constant_rh_curve(t_axis, rh_line, P_ATM)
        trace = go.Scatter(x=t_axis, y=y_data, mode='line', name="{:.0%} relative humidity".format(rh_line)
                           , line=dict(color=COLOR.COLORS['grey_light'], width=1),showlegend=False)
        graph.append(trace)


    return graph


def calc_data(data_frame):

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)

    # read region-specific control parameters (identical for all buildings), i.e. heating and cooling season
    prop_region_specific_control = pd.read_excel(locator.get_archetypes_system_controls(config.region),
                                                 true_values=['True', 'TRUE', 'true'],
                                                 false_values=['False', 'FALSE', 'false', u'FALSE'],
                                                 dtype={'has-heating-season': bool,
                                                        'has-cooling-season': bool})  # read database

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

    def datetime_in_season(dt, season_start, season_end):

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

    t_op_occupied_summer = []
    x_int_occupied_summer = []
    t_op_unoccupied_summer = []
    x_int_unoccupied_summer = []
    t_op_occupied_winter = []
    x_int_occupied_winter = []
    t_op_unoccupied_winter = []
    x_int_unoccupied_winter = []

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

    :param data_frame_month: data frame of monthly building energy balance
    :return:
    """

    # create table arrays

    # check winter comfort
    # equation for lower temp boundary in winter t = m*x + b
    b_low = VERTICES_WINTER_COMFORT[0][0]
    m_low = (VERTICES_WINTER_COMFORT[3][0] - b_low) / (VERTICES_WINTER_COMFORT[3][1] - VERTICES_WINTER_COMFORT[0][1])
    b_high = VERTICES_WINTER_COMFORT[1][0]
    m_high = (VERTICES_WINTER_COMFORT[2][0] - b_high) / (VERTICES_WINTER_COMFORT[2][1] - VERTICES_WINTER_COMFORT[1][1])

    count_winter_comfort = 0

    for t, x in zip(dict_graph['t_op_occupied_winter'], dict_graph['x_int_occupied_winter']):

        if VERTICES_WINTER_COMFORT[0][1] <= x <= VERTICES_WINTER_COMFORT[2][1]:

            if m_low * x + b_low <= t <= m_high * x + b_high:
                count_winter_comfort = count_winter_comfort + 1
            else:
                pass
        else:
            pass

    count_winter_uncomfort = len(dict_graph['t_op_occupied_winter']) - count_winter_comfort

    # check summer comfort
    # equation for lower temp boundary in winter t = m*x + b
    b_low = VERTICES_SUMMER_COMFORT[0][0]
    m_low = (VERTICES_SUMMER_COMFORT[3][0] - b_low) / (VERTICES_SUMMER_COMFORT[3][1] - VERTICES_SUMMER_COMFORT[0][1])
    b_high = VERTICES_SUMMER_COMFORT[1][0]
    m_high = (VERTICES_SUMMER_COMFORT[2][0] - b_high) / (VERTICES_SUMMER_COMFORT[2][1] - VERTICES_SUMMER_COMFORT[1][1])

    count_summer_comfort = 0

    for t, x in zip(dict_graph['t_op_occupied_summer'], dict_graph['x_int_occupied_summer']):

        if VERTICES_SUMMER_COMFORT[0][1] <= x <= VERTICES_SUMMER_COMFORT[2][1]:

            if m_low * x + b_low <= t <= m_high * x + b_high:
                count_summer_comfort = count_summer_comfort + 1
            else:
                pass
        else:
            pass

    count_summer_uncomfort = len(dict_graph['t_op_occupied_summer']) - count_summer_comfort
        # check comfort



    # draw table
    table = go.Table(domain=dict(x=[0.0, 0.3], y=[0, 0.6]),
                     header=dict(values=['condition', 'comfort [h]', 'uncomfort [h]']),
                     cells=dict(values=[['summer occupied','winter occupied'],
                                        [count_summer_comfort,count_winter_comfort],
                                        [count_summer_uncomfort,count_winter_uncomfort]]),
                     visible=True)

    return table


def p_ws_from_t(t_celsius):
    """
    Calculate water vapor saturation pressure over liquid water for the temperature range of 0 to 200°C
    Eq (6) in "CHAPTER 6 - PSYCHROMETRICS" in "2001 ASHRAE Fundamentals Handbook (SI)"

    :param t_celsius: temperature
    :type t_celsius: double
    :return:
    """

    t = t_celsius + 273.15

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

    :param rh:
    :param p_ws:
    :return:
    """

    return rh * p_ws


def hum_ratio_from_p_w_and_p(p_w, p):
    """
    Calculate humidity ratio from water vapor pressure and atmospheric pressure
    Eq(22) in "CHAPTER 6 - PSYCHROMETRICS" in "2001 ASHRAE Fundamentals Handbook (SI)"


    :param p_w:
    :param p:
    :return:
    """

    return 0.62198 * p_w/(p-p_w)


def calc_constant_rh_curve(t_array, rh, p):
    """
    Calculates curves of humidity ratio at different temperatures for a constant relative humidity and pressure

    :param t_array:
    :param rh:
    :param p:
    :return:
    """

    p_ws = np.vectorize(p_ws_from_t)(t_array)
    p_w = p_w_from_rh_p_and_ws(rh, p_ws)

    return hum_ratio_from_p_w_and_p(p_w, p) * 1000


