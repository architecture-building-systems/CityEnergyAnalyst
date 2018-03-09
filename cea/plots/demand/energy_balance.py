from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.color_code import ColorCodeCEA
from cea.plots.variable_naming import LOGO

COLOR = ColorCodeCEA()
import pandas as pd
import numpy as np


def energy_balance(data_frame, analysis_fields, title, output_path):
    # Calculate Energy Balance
    data_frame_month = calc_monthly_energy_balance(data_frame)

    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame_month)

    # CALCULATE TABLE
    traces_table = calc_table(data_frame_month)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='relative',
                       yaxis=dict(title='Energy balance [MWh]', domain=[0.35, 1.0]))
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
    for field in analysis_fields:
        y = data_frame[field]
        trace = go.Bar(x=data_frame["month"], y=y, name=field.split('_kWh', 1)[0],
                       marker=dict(color=COLOR.get_color_rgb(field)))  # , text = total_perc_txt)
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


def calc_monthly_energy_balance(data_frame):
    """
    calculates heat flux balance for buildings on hourly basis

    :param data_frame:
    :return:
    """

    # calculate losses of heating and cooling system in data frame and adjust signs
    data_frame['Qhs_loss_sen_kWh'] = -abs(data_frame['Qhs_em_ls_kWh'] + data_frame['Qhs_dis_ls_kWh'])
    data_frame['Qhsf_sen_kWh'] = data_frame['Qhs_sen_sys_kWh'] + abs(data_frame['Qhs_loss_sen_kWh'])
    data_frame['Qcs_loss_sen_kWh'] = -data_frame['Qcs_em_ls_kWh'] - data_frame['Qcs_dis_ls_kWh']
    data_frame['Qcsf_sen_kWh'] = data_frame['Qcs_sen_sys_kWh'] - abs(data_frame['Qcs_loss_sen_kWh'])
    data_frame['Qcsf_lat_kWh'] = data_frame['Qcs_lat_sys_kWh']



    # split up R-C model heat fluxes into heating and cooling contributions
    data_frame['Q_loss_sen_env_kWh'] = data_frame["Q_gain_sen_env_kWh"][data_frame["Q_gain_sen_env_kWh"] < 0]
    data_frame['Q_gain_sen_env_kWh'] = data_frame["Q_gain_sen_env_kWh"][data_frame["Q_gain_sen_env_kWh"] > 0]
    data_frame['Q_loss_sen_vent_kWh'] = data_frame["Q_gain_sen_vent_kWh"][data_frame["Q_gain_sen_vent_kWh"] < 0]
    data_frame['Q_gain_sen_vent_kWh'] = data_frame["Q_gain_sen_vent_kWh"][data_frame["Q_gain_sen_vent_kWh"] > 0]
    data_frame['Q_loss_sen_wind_kWh'] = data_frame["Q_gain_sen_wind_kWh"][data_frame["Q_gain_sen_wind_kWh"] < 0]
    data_frame['Q_gain_sen_wind_kWh'] = data_frame["Q_gain_sen_wind_kWh"][data_frame["Q_gain_sen_wind_kWh"] > 0]
    data_frame['Q_gain_sen_env_kWh'].fillna(0, inplace=True)
    data_frame['Q_loss_sen_env_kWh'].fillna(0, inplace=True)
    data_frame['Q_gain_sen_vent_kWh'].fillna(0, inplace=True)
    data_frame['Q_loss_sen_vent_kWh'].fillna(0, inplace=True)
    data_frame['Q_gain_sen_wind_kWh'].fillna(0, inplace=True)
    data_frame['Q_loss_sen_wind_kWh'].fillna(0, inplace=True)



    # convert to monthly
    data_frame.index = pd.to_datetime(data_frame.index)
    data_frame_month = (data_frame.resample("M").sum() / 1000)  # to MW
    data_frame_month["month"] = data_frame_month.index.strftime("%B")

    # calculate latent heat gains of people that are covered by the cooling system
    # FIXME: This is kind of a fake balance, as months are compared (could be a significant share not in heating or cooling season)
    for index, row in data_frame_month.iterrows():
        # completely covered
        if row['Qcsf_lat_kWh'] < 0 and abs(row['Qcsf_lat_kWh']) >= row['Q_gain_lat_peop_kWh']:
            data_frame_month.at[index, 'Q_gain_lat_peop_kWh'] = row['Q_gain_lat_peop_kWh']
        # partially covered (rest is ignored)
        elif row['Qcsf_lat_kWh'] < 0 and abs(row['Qcsf_lat_kWh']) < row['Q_gain_lat_peop_kWh']:
            data_frame_month.at[index, 'Q_gain_lat_peop_kWh'] = abs(row['Qcsf_lat_kWh'])
        # no latent gains
        elif row['Qcsf_lat_kWh'] == 0:
            data_frame_month.at[index, 'Q_gain_lat_peop_kWh'] = 0.0
        else:
            data_frame_month.at[index, 'Q_gain_lat_peop_kWh'] = 0.0

    data_frame_month['Q_gain_lat_vent_kWh'] = abs(data_frame_month['Qcsf_lat_kWh']) - data_frame_month['Q_gain_lat_peop_kWh']

    # balance of heating
    data_frame_month['Q_heat_sum'] = data_frame_month['Qhsf_sen_kWh'] + data_frame_month['Q_gain_sen_env_kWh'] + data_frame_month[
        'Q_gain_sen_vent_kWh'] + data_frame_month['Q_gain_sen_wind_kWh'] + data_frame_month["Q_gain_sen_app_kWh"] + \
                               data_frame_month['Q_gain_sen_light_kWh'] + data_frame_month['Q_gain_sen_peop_kWh'] + data_frame_month[
                                   'Q_gain_sen_data_kWh'] + \
                               data_frame_month['I_sol_kWh'] + data_frame_month['Qcs_loss_sen_kWh'] + data_frame_month[
                                   'Q_gain_lat_peop_kWh'] + data_frame_month['Q_gain_lat_vent_kWh']

    # balance of cooling
    data_frame_month['Q_cool_sum'] = data_frame_month['Qcsf_sen_kWh'] + data_frame_month['Q_loss_sen_env_kWh'] + data_frame_month[
        'Q_loss_sen_vent_kWh'] + data_frame_month['Q_loss_sen_wind_kWh'] + data_frame_month['I_rad_kWh'] + data_frame_month[
                                   'Qhs_loss_sen_kWh'] + data_frame_month['Q_loss_sen_ref_kWh'] + data_frame_month['Qcsf_lat_kWh']

    # total balance
    data_frame_month['Q_balance'] = data_frame_month['Q_heat_sum'] + data_frame_month['Q_cool_sum']

    data_frame_month = data_frame_month.round(2)

    return data_frame_month
