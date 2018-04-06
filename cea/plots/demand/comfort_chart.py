# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function

import math
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.color_code import ColorCodeCEA
from cea.plots.variable_naming import LOGO

COLOR = ColorCodeCEA()
import pandas as pd
import numpy as np


def comfort_chart(data_frame, analysis_fields, title, output_path):
    # Calculate Energy Balance
    #data_frame_month = calc_monthly_energy_balance(data_frame)

    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    #traces_table = calc_table(data_frame_month)

    # PLOT GRAPH
    #traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title,
                       yaxis=dict(title='Moisture content [g/kg dry air]', range=[0.0, 30.0], side='right', domain=[0.0, 1.0]),
                       xaxis=dict(title='Air Temperature [°C]', range=[0.0, 35.0],))

    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    """
    draws building heat balance graph

    :param analysis_fields:
    :param data_frame:
    :return:
    """

    graph = []

    # draw scatter of comfort conditions in building
    trace = go.Scatter(x=data_frame["T_int_C"], y=data_frame["x_int"], name=[], mode='markers')  # , text = total_perc_txt)
    graph.append(trace)

    # draw lines of constant relative humidity for psychrometric chart
    rh_lines = np.linspace(0.1, 1, 10)
    t_axis = np.linspace(-5,45,50)
    P_ATM = 101325 # kPa, standard atmospheric pressure at sea level

    for rh_line in rh_lines:

        y_data = calc_constant_rh_curve(t_axis, rh_line, P_ATM)
        trace = go.Scatter(x=t_axis, y=y_data, mode='line', name="{:.0%} relative humidity".format(rh_line))
        graph.append(trace)


    return graph


def calc_table(data_frame_month):
    """
    draws table of monthly energy balance

    :param data_frame_month: data frame of monthly building energy balance
    :return:
    """

    # create table arrays
    name_month = np.append(data_frame_month['month'].values, ['YEAR'])
    total_heat = np.append(data_frame_month['Q_heat_sum'].values, data_frame_month['Q_heat_sum'].sum())
    total_cool = np.append(data_frame_month['Q_cool_sum'], data_frame_month['Q_cool_sum'].sum())
    balance = np.append(data_frame_month['Q_balance'], data_frame_month['Q_balance'].sum().round(2))

    # draw table
    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Month', 'Total heat [MWh]', 'Total cool [MWh]', 'Delta [MWh]']),
                     cells=dict(values=[name_month, total_heat, total_cool, balance]))

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


