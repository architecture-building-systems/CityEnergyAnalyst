from __future__ import division

import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot

import cea.plots.thermal_networks
from cea.plots.variable_naming import NAMING, LOGO, COLOR
from cea.constants import HOURS_IN_YEAR

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class LoadDurationCurvePlot(cea.plots.thermal_networks.ThermalNetworksPlotBase):
    """Implement the load duration curve of pump plot"""
    name = "Load duration curve of pump"

    def __init__(self, project, parameters, cache):
        super(LoadDurationCurvePlot, self).__init__(project, parameters, cache)
        self.network_args = [self.network_type, self.network_name]
        self.input_files = [(self.locator.get_thermal_demand_csv_file, self.network_args),
                            (self.locator.get_thermal_network_layout_pressure_drop_kw_file, self.network_args),
                            (self.locator.get_thermal_network_qloss_system_file, self.network_args)]

    @property
    def layout(self):
        return go.Layout(title=self.title, xaxis=dict(title='Duration Normalized [%]', domain=[0, 1]),
                         yaxis=dict(title='Load [kW]', domain=[0.0, 0.7]))

    def calc_graph(self):
        analysis_fields = ["P_loss_kWh"]  # data to plot
        data_frame = self.hourly_pressure_loss
        data_frame.columns = analysis_fields
        graph = []
        duration = range(HOURS_IN_YEAR)
        x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]  # calculate relative values
        for field in analysis_fields:
            data_frame = data_frame.sort_values(by=field, ascending=False)
            y = data_frame[field].values
            trace = go.Scatter(x=x, y=y, name=field, fill='tozeroy', opacity=0.8,
                               marker=dict(color=COLOR[field]))
            graph.append(trace)
        return graph

    def calc_table(self):
        # calculate variables for the analysis
        analysis_fields = ["P_loss_kWh"]  # data to plot
        data_frame = self.hourly_pressure_loss
        data_frame.columns = analysis_fields
        loss_peak = data_frame[analysis_fields].max().round(2).tolist()  # save maximum value of loss
        loss_total = (data_frame[analysis_fields].sum() / 1000).round(2).tolist()  # save total loss value

        # calculate graph
        load_utilization = []
        loss_names = []
        # data = ''
        duration = range(HOURS_IN_YEAR)
        x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]
        for field in analysis_fields:
            field_1 = field.split('_')[0]
            field_2 = field.split('_')[1]
            field_3 = field_1 + '_' + field_2
            data_frame_new = data_frame.sort_values(by=field, ascending=False)
            y = data_frame_new[field].values
            load_utilization.append(evaluate_utilization(x, y))
            loss_names.append(NAMING[field] + ' (' + field_3 + ')')
        column_names = ['Name', 'Peak Load [kW]', 'Yearly Demand [MWh]', 'Utilization [-]']
        column_values = [loss_names, loss_peak, loss_total, load_utilization]
        table_df = pd.DataFrame({cn: cv for cn, cv in zip(column_names, column_values)}, columns=column_names)
        return table_df


def loss_duration_curve(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph = calc_graph(analysis_fields, data_frame)

    # CALCULATE TABLE
    traces_table = calc_table(analysis_fields, data_frame)

    # PLOT GRAPH
    traces_graph.append(traces_table)
    layout = go.Layout(images=LOGO, title=title, xaxis=dict(title='Duration Normalized [%]', domain=[0, 1]),
                       yaxis=dict(title='Load [kW]', domain=[0.0, 0.7]))
    fig = go.Figure(data=traces_graph, layout=layout)
    plot(fig, auto_open=False, filename=output_path)
    return {'data': traces_graph, 'layout': layout}


def calc_table(analysis_fields, data_frame):
    # calculate variables for the analysis
    loss_peak = data_frame[analysis_fields].max().round(2).tolist()  # save maximum value of loss
    loss_total = (data_frame[analysis_fields].sum() / 1000).round(2).tolist()  # save total loss value

    # calculate graph
    load_utilization = []
    loss_names = []
    # data = ''
    duration = range(HOURS_IN_YEAR)
    x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]
    for field in analysis_fields:
        field_1 = field.split('_')[0]
        field_2 = field.split('_')[1]
        field_3 = field_1 + '_' + field_2
        data_frame_new = data_frame.sort_values(by=field, ascending=False)
        y = data_frame_new[field].values
        load_utilization.append(evaluate_utilization(x, y))
        loss_names.append(NAMING[field] + ' (' + field_3 + ')')
    table = go.Table(domain=dict(x=[0, 1], y=[0.7, 1.0]),
                     header=dict(
                         values=['Name', 'Peak Load [kW]', 'Yearly Demand [MWh]', 'Utilization [-]']),
                     cells=dict(values=[loss_names, loss_peak, loss_total, load_utilization]))
    return table


def calc_graph(analysis_fields, data_frame):
    graph = []
    duration = range(HOURS_IN_YEAR)
    x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]  # calculate relative values
    for field in analysis_fields:
        data_frame = data_frame.sort_values(by=field, ascending=False)
        y = data_frame[field].values
        trace = go.Scatter(x=x, y=y, name=field, fill='tozeroy', opacity=0.8,
                           marker=dict(color=COLOR[field]))
        graph.append(trace)
    return graph


def evaluate_utilization(x, y):
    dataframe_util = pd.DataFrame({'x': x, 'y': y})
    if 0 in dataframe_util['y'].values:
        index_occurrence = dataframe_util['y'].idxmin(axis=0, skipna=True)
        utilization_perc = round(dataframe_util.loc[index_occurrence, 'x'], 1)
        utilization_days = int(utilization_perc * HOURS_IN_YEAR / (24 * 100))
        return str(utilization_perc) + '% or ' + str(utilization_days) + ' days a year'
    else:
        return 'all year'


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()
    LoadDurationCurvePlot(config.project, {'network-type': config.plots.network_type,
                                           'scenario-name': config.scenario_name,
                                           'network-name': config.plots.network_name},
                          cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
