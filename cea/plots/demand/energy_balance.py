from __future__ import division
from __future__ import print_function

import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import LOGO, COLOR, NAMING
import cea.plots.demand
import pandas as pd
import numpy as np


__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "2.8"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class EnergyBalancePlot(cea.plots.demand.DemandPlotBase):
    name = "Energy balance"

    def __init__(self, project, parameters):
        super(EnergyBalancePlot, self).__init__(project, parameters)
        if len(self.buildings) > 1:
            self.buildings = [self.buildings[0]]
        self.analysis_fields = ['I_sol_kWh',
                                'Qhs_tot_sen_kWh',
                                'Qhs_loss_sen_kWh',
                                'Q_gain_lat_peop_kWh',
                                'Q_gain_sen_light_kWh',
                                'Q_gain_sen_app_kWh',
                                'Q_gain_sen_data_kWh',
                                'Q_gain_sen_peop_kWh',
                                'Q_gain_sen_wall_kWh',
                                'Q_gain_sen_base_kWh',
                                'Q_gain_sen_roof_kWh',
                                'Q_gain_sen_wind_kWh',
                                'Q_gain_sen_vent_kWh',
                                'Q_gain_lat_vent_kWh',
                                'I_rad_kWh',
                                'Qcs_tot_sen_kWh',
                                'Qcs_tot_lat_kWh',
                                'Qcs_loss_sen_kWh',
                                'Q_loss_sen_wall_kWh',
                                'Q_loss_sen_base_kWh',
                                'Q_loss_sen_roof_kWh',
                                'Q_loss_sen_wind_kWh',
                                'Q_loss_sen_vent_kWh',
                                'Q_loss_sen_ref_kWh']
        self.layout = go.Layout(barmode='relative',
                                yaxis=dict(title='Energy balance [kWh/m2_GFA]', domain=[0.35, 1.0]))

    def calc_graph(self):
        gfa_m2 = self.yearly_loads.set_index('Name').loc[self.buildings[0]]['GFA_m2']
        self.data = self.hourly_loads[self.hourly_loads['Name'].isin(self.buildings)]
        self.data = calc_monthly_energy_balance(self.data, gfa_m2)
        traces = []
        for field in self.analysis_fields:
            y = self.data[field]
            trace = go.Bar(x=self.data.index, y=y, name=field.split('_kWh', 1)[0],
                           marker=dict(color=COLOR[field]))  # , text = total_perc_txt)
            traces.append(trace)
        return traces


def energy_balance(data_frame, analysis_fields, normalize_value, title, output_path):
    # Calculate Energy Balance
    data_frame_month = calc_monthly_energy_balance(data_frame, normalize_value)

    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame_month)

    # CALCULATE TABLE
    traces_table = calc_table(data_frame_month)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, barmode='relative',
                       yaxis=dict(title='Energy balance [kWh/m2_GFA]', domain=[0.35, 1.0]))
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
        trace = go.Bar(x=data_frame.index, y=y, name=field.split('_kWh', 1)[0],
                       marker=dict(color=COLOR[field]))  # , text = total_perc_txt)
        graph.append(trace)

    return graph


def calc_table(data_frame_month):
    """
    draws table of monthly energy balance

    :param data_frame_month: data frame of monthly building energy balance
    :return:
    """

    # create table arrays
    name_month = np.append(data_frame_month.index, ['YEAR'])
    total_heat = np.append(data_frame_month['Q_heat_sum'].values, data_frame_month['Q_heat_sum'].sum())
    total_cool = np.append(data_frame_month['Q_cool_sum'], data_frame_month['Q_cool_sum'].sum())
    balance = np.append(data_frame_month['Q_balance'], data_frame_month['Q_balance'].sum().round(2))

    # draw table
    table = go.Table(domain=dict(x=[0, 1], y=[0.0, 0.2]),
                     header=dict(values=['Month', 'Total heat [kWh/m2_GFA]', 'Total cool [kWh/m2_GFA]',
                                         'Delta [kWh/m2_GFA]']),
                     cells=dict(values=[name_month, total_heat, total_cool, balance]))

    return table


def calc_monthly_energy_balance(data_frame, normalize_value):
    """
    calculates heat flux balance for buildings on hourly basis

    :param data_frame:
    :return:
    """

    # calculate losses of heating and cooling system in data frame and adjust signs
    data_frame['Qhs_loss_sen_kWh'] = -abs(data_frame['Qhs_em_ls_kWh'] + data_frame['Qhs_dis_ls_kWh'])
    data_frame['Qhs_tot_sen_kWh'] = data_frame['Qhs_sen_sys_kWh'] + abs(data_frame['Qhs_loss_sen_kWh'])
    data_frame['Qcs_loss_sen_kWh'] = -data_frame['Qcs_em_ls_kWh'] - data_frame['Qcs_dis_ls_kWh']
    data_frame['Qcs_tot_sen_kWh'] = data_frame['Qcs_sen_sys_kWh'] - abs(data_frame['Qcs_loss_sen_kWh'])
    data_frame['Qcs_tot_lat_kWh'] = -data_frame['Qcs_lat_sys_kWh']  # change sign because this variable is now positive in demand



    # split up R-C model heat fluxes into heating and cooling contributions
    data_frame['Q_loss_sen_wall_kWh'] = data_frame["Q_gain_sen_wall_kWh"][data_frame["Q_gain_sen_wall_kWh"] < 0]
    data_frame['Q_gain_sen_wall_kWh'] = data_frame["Q_gain_sen_wall_kWh"][data_frame["Q_gain_sen_wall_kWh"] > 0]
    data_frame['Q_loss_sen_base_kWh'] = data_frame["Q_gain_sen_base_kWh"][data_frame["Q_gain_sen_base_kWh"] < 0]
    data_frame['Q_gain_sen_base_kWh'] = data_frame["Q_gain_sen_base_kWh"][data_frame["Q_gain_sen_base_kWh"] > 0]
    data_frame['Q_loss_sen_roof_kWh'] = data_frame["Q_gain_sen_roof_kWh"][data_frame["Q_gain_sen_roof_kWh"] < 0]
    data_frame['Q_gain_sen_roof_kWh'] = data_frame["Q_gain_sen_roof_kWh"][data_frame["Q_gain_sen_roof_kWh"] > 0]
    data_frame['Q_loss_sen_vent_kWh'] = data_frame["Q_gain_sen_vent_kWh"][data_frame["Q_gain_sen_vent_kWh"] < 0]
    data_frame['Q_gain_sen_vent_kWh'] = data_frame["Q_gain_sen_vent_kWh"][data_frame["Q_gain_sen_vent_kWh"] > 0]
    data_frame['Q_loss_sen_wind_kWh'] = data_frame["Q_gain_sen_wind_kWh"][data_frame["Q_gain_sen_wind_kWh"] < 0]
    data_frame['Q_gain_sen_wind_kWh'] = data_frame["Q_gain_sen_wind_kWh"][data_frame["Q_gain_sen_wind_kWh"] > 0]
    data_frame['Q_gain_sen_wall_kWh'].fillna(0, inplace=True)
    data_frame['Q_gain_sen_base_kWh'].fillna(0, inplace=True)
    data_frame['Q_gain_sen_roof_kWh'].fillna(0, inplace=True)
    data_frame['Q_loss_sen_wall_kWh'].fillna(0, inplace=True)
    data_frame['Q_loss_sen_base_kWh'].fillna(0, inplace=True)
    data_frame['Q_loss_sen_roof_kWh'].fillna(0, inplace=True)
    data_frame['Q_gain_sen_vent_kWh'].fillna(0, inplace=True)
    data_frame['Q_loss_sen_vent_kWh'].fillna(0, inplace=True)
    data_frame['Q_gain_sen_wind_kWh'].fillna(0, inplace=True)
    data_frame['Q_loss_sen_wind_kWh'].fillna(0, inplace=True)



    # convert to monthly
    data_frame.index = pd.to_datetime(data_frame.index)
    data_frame_month = data_frame.resample("M").sum()  # still kWh
    data_frame_month["month"] = data_frame_month.index.strftime("%B")
    data_frame_month.set_index("month", inplace=True)

    # calculate latent heat gains of people that are covered by the cooling system
    # FIXME: This is kind of a fake balance, as months are compared (could be a significant share not in heating or cooling season)
    for index, row in data_frame_month.iterrows():
        # completely covered
        if row['Qcs_tot_lat_kWh'] < 0 and abs(row['Qcs_lat_sys_kWh']) >= row['Q_gain_lat_peop_kWh']:
            data_frame_month.at[index, 'Q_gain_lat_peop_kWh'] = row['Q_gain_lat_peop_kWh']
        # partially covered (rest is ignored)
        elif row['Qcs_tot_lat_kWh'] < 0 and abs(row['Qcs_tot_lat_kWh']) < row['Q_gain_lat_peop_kWh']:
            data_frame_month.at[index, 'Q_gain_lat_peop_kWh'] = abs(row['Qcs_tot_lat_kWh'])
        # no latent gains
        elif row['Qcs_tot_lat_kWh'] == 0:
            data_frame_month.at[index, 'Q_gain_lat_peop_kWh'] = 0.0
        else:
            data_frame_month.at[index, 'Q_gain_lat_peop_kWh'] = 0.0

    data_frame_month['Q_gain_lat_vent_kWh'] = abs(data_frame_month['Qcs_lat_sys_kWh']) - data_frame_month['Q_gain_lat_peop_kWh']

    # balance of heating
    data_frame_month['Q_heat_sum'] = data_frame_month['Qhs_tot_sen_kWh'] + data_frame_month['Q_gain_sen_wall_kWh'] \
        + data_frame_month['Q_gain_sen_base_kWh'] + data_frame_month['Q_gain_sen_roof_kWh'] \
        + data_frame_month['Q_gain_sen_vent_kWh'] + data_frame_month['Q_gain_sen_wind_kWh']\
        + data_frame_month["Q_gain_sen_app_kWh"] + data_frame_month['Q_gain_sen_light_kWh']\
        + data_frame_month['Q_gain_sen_peop_kWh'] + data_frame_month['Q_gain_sen_data_kWh'] \
        + data_frame_month['I_sol_kWh'] + data_frame_month['Qcs_loss_sen_kWh']\
        + data_frame_month['Q_gain_lat_peop_kWh'] + data_frame_month['Q_gain_lat_vent_kWh']

    # balance of cooling
    data_frame_month['Q_cool_sum'] = data_frame_month['Qcs_tot_sen_kWh'] + data_frame_month['Q_loss_sen_wall_kWh'] \
        + data_frame_month['Q_loss_sen_base_kWh']+ data_frame_month['Q_loss_sen_roof_kWh']\
        + data_frame_month['Q_loss_sen_vent_kWh'] + data_frame_month['Q_loss_sen_wind_kWh']\
        + data_frame_month['I_rad_kWh'] + data_frame_month['Qhs_loss_sen_kWh']\
        + data_frame_month['Q_loss_sen_ref_kWh'] + data_frame_month['Qcs_tot_lat_kWh']

    # total balance
    data_frame_month['Q_balance'] = data_frame_month['Q_heat_sum'] + data_frame_month['Q_cool_sum']

    # normalize by GFA
    data_frame_month = data_frame_month / normalize_value

    data_frame_month = data_frame_month.round(2)

    return data_frame_month


if __name__ == '__main__':
    import cea.config
    import cea.inputlocator

    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    EnergyBalancePlot(config, locator, [locator.get_zone_building_names()[0]]).plot(auto_open=True)
    EnergyBalancePlot(config, locator, [locator.get_zone_building_names()[1]]).plot(auto_open=True)
    EnergyBalancePlot(config, locator, [locator.get_zone_building_names()[2]]).plot(auto_open=True)