from __future__ import division
from __future__ import print_function
from plotly.offline import plot
import plotly.graph_objs as go
from cea.plots.variable_naming import LOGO
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
        trace = go.Bar(x=data_frame["month"], y=y, name=field.split('_kWh', 1)[0])  # , text = total_perc_txt)
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
    data_frame['Qhsf_sys_loss_kWh'] = -abs(data_frame['Qhsf_kWh'] - data_frame['Qhs_kWh'])
    data_frame['Qcsf_sen_kWh'] = -(data_frame['Qcsf_kWh'] - data_frame['Qcsf_lat_kWh'])
    data_frame['Qcsf_sys_loss_kWh'] = abs(data_frame['Qcsf_sen_kWh'] - data_frame['Qcs_sen_kWh'])
    data_frame['Qcsf_lat_kWh'] = -data_frame['Qcsf_lat_kWh']

    # calculate latent heat gains of people that are covered by the cooling system
    data_frame['Qgain_lat_peop_kWh'] = 0.0
    for index, row in data_frame.iterrows():
        # completely covered
        if row['Qcsf_lat_kWh'] < 0 and abs(row['Qcsf_lat_kWh']) >= row['q_cs_lat_peop_kWh']:
            data_frame.set_value(index, 'Qgain_lat_peop_kWh', row['q_cs_lat_peop_kWh'])
        # partially covered (rest is ignored)
        elif row['Qcsf_lat_kWh'] < 0 and abs(row['Qcsf_lat_kWh']) < row['q_cs_lat_peop_kWh']:
            data_frame.set_value(index, 'Qgain_lat_peop_kWh', abs(row['Qcsf_lat_kWh']))
        # no latent gains
        else:
            row['Qgain_lat_peop_kWh'] = 0.0

    data_frame['Qgain_lat_vent_kWh'] = abs(data_frame['Qcsf_lat_kWh']) - data_frame['Qgain_lat_peop_kWh']

    # split up R-C model heat fluxes into heating and cooling contributions
    data_frame['Qloss_wall_kWh'] = data_frame["Qgain_wall_kWh"][data_frame["Qgain_wall_kWh"] < 0]
    data_frame['Qgain_wall_kWh'] = data_frame["Qgain_wall_kWh"][data_frame["Qgain_wall_kWh"] > 0]
    data_frame['Qloss_vent_kWh'] = data_frame["Qgain_vent_kWh"][data_frame["Qgain_vent_kWh"] < 0]
    data_frame['Qgain_vent_kWh'] = data_frame["Qgain_vent_kWh"][data_frame["Qgain_vent_kWh"] > 0]
    data_frame['Qloss_wind_kWh'] = data_frame["Qgain_wind_kWh"][data_frame["Qgain_wind_kWh"] < 0]
    data_frame['Qgain_wind_kWh'] = data_frame["Qgain_wind_kWh"][data_frame["Qgain_wind_kWh"] > 0]
    data_frame['Qloss_roof_kWh'] = data_frame["Qgain_roof_kWh"][data_frame["Qgain_roof_kWh"] < 0]
    data_frame['Qgain_roof_kWh'] = data_frame["Qgain_roof_kWh"][data_frame["Qgain_roof_kWh"] > 0]
    data_frame['Qloss_base_kWh'] = data_frame["Qgain_base_kWh"][data_frame["Qgain_base_kWh"] < 0]
    data_frame['Qgain_base_kWh'] = data_frame["Qgain_base_kWh"][data_frame["Qgain_base_kWh"] > 0]
    data_frame['Qgain_wall_kWh'].fillna(0, inplace=True)
    data_frame['Qloss_wall_kWh'].fillna(0, inplace=True)
    data_frame['Qgain_vent_kWh'].fillna(0, inplace=True)
    data_frame['Qloss_vent_kWh'].fillna(0, inplace=True)
    data_frame['Qgain_wind_kWh'].fillna(0, inplace=True)
    data_frame['Qloss_wind_kWh'].fillna(0, inplace=True)
    data_frame['Qgain_roof_kWh'].fillna(0, inplace=True)
    data_frame['Qloss_roof_kWh'].fillna(0, inplace=True)
    data_frame['Qgain_base_kWh'].fillna(0, inplace=True)
    data_frame['Qloss_base_kWh'].fillna(0, inplace=True)

    # balance of heating
    data_frame['Q_heat_sum'] = data_frame['Qhsf_kWh'] + data_frame['Qgain_wall_kWh'] + data_frame[
        'Qgain_vent_kWh'] + data_frame['Qgain_wind_kWh'] + data_frame['Qgain_roof_kWh'] + \
                               data_frame['Qgain_base_kWh'] + data_frame["Qgain_app_kWh"] + \
                               data_frame['Qgain_light_kWh'] + data_frame['Qgain_pers_kWh'] + data_frame[
                                   'Qgain_data_kWh'] + \
                               data_frame['I_sol_kWh'] + data_frame['Qcsf_sys_loss_kWh'] + data_frame[
                                   'Qgain_lat_peop_kWh'] + data_frame['Qgain_lat_vent_kWh']

    # balance of cooling
    data_frame['Q_cool_sum'] = data_frame['Qcsf_sen_kWh'] + data_frame['Qloss_wall_kWh'] + data_frame[
        'Qloss_vent_kWh'] + data_frame['Qloss_wind_kWh'] + data_frame['Qloss_roof_kWh'] + \
                               data_frame['Qloss_base_kWh'] + data_frame['I_rad_kWh'] + data_frame[
                                   'Qhsf_sys_loss_kWh'] + data_frame['Q_cool_ref_kWh'] + data_frame['Qcsf_lat_kWh']

    # total balance
    data_frame['Q_balance'] = data_frame['Q_heat_sum'] + data_frame['Q_cool_sum']

    # convert to monthly
    data_frame.index = pd.to_datetime(data_frame.index)
    data_frame_month = (data_frame.resample("M").sum() / 1000).round(2)  # to MW
    data_frame_month["month"] = data_frame_month.index.strftime("%B")

    return data_frame_month
