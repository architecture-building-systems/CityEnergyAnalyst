from __future__ import division
from __future__ import print_function

import pandas as pd
import plotly.graph_objs as go
from plotly.offline import plot

import cea.plots.thermal_networks
from cea.plots.variable_naming import NAMING, LOGO, COLOR

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class LossCurvePlot(cea.plots.thermal_networks.ThermalNetworksPlotBase):
    """Implement the heat and pressure losses plot"""
    name = "Heat and Pressure Losses"

    def __init__(self, project, parameters, cache):
        super(LossCurvePlot, self).__init__(project, parameters, cache)
        self.analysis_fields = ["P_loss_kWh", "Q_loss_kWh"]
        network_args = [self.network_type, self.network_name]
        self.input_files = [(self.locator.get_thermal_demand_csv_file, network_args),
                            (self.locator.get_thermal_network_layout_pressure_drop_kw_file, network_args),
                            (self.locator.get_thermal_network_qloss_system_file, network_args)]

    @property
    def layout(self):
        return dict(title=self.title, yaxis=dict(title='Loss [kWh]'),
                    yaxis2=dict(title='Demand [kWh]', overlaying='y',
                                side='right'), xaxis=dict(rangeselector=dict(buttons=list([
                dict(count=1, label='1d', step='day', stepmode='backward'),
                dict(count=1, label='1w', step='week', stepmode='backward'),
                dict(count=1, label='1m', step='month', stepmode='backward'),
                dict(count=6, label='6m', step='month', stepmode='backward'),
                dict(count=1, label='1y', step='year', stepmode='backward'),
                dict(step='all')])), rangeslider=dict(), type='date', range=[self.date[0],
                                                                             self.date[168]],
                fixedrange=False))

    def calc_graph(self):
        hourly_loads = self.hourly_loads
        analysis_fields = ["P_loss_kWh", "Q_loss_kWh"]  # plot data names
        analysis_fields += [str(column) for column in hourly_loads.columns]
        data_frame = self.hourly_pressure_loss.join(
            pd.DataFrame(self.hourly_heat_loss.sum(axis=1)))  # join pressure and heat loss data
        data_frame.index = hourly_loads.index  # match index
        data_frame = data_frame.join(hourly_loads)  # add demand data
        data_frame.columns = analysis_fields  # format dataframe columns
        data_frame.index = self.date
        traces = []
        x = data_frame.index
        for field in analysis_fields:
            y = data_frame[field].values
            name = NAMING[field]
            if field in ['Q_dem_cool', 'Q_dem_heat']:  # demand data on secondary y axis
                trace = go.Scatter(x=x, y=y, name=name,
                                   marker=dict(color=COLOR[field]),
                                   yaxis='y2', opacity=0.6)
            else:  # primary y_axis
                trace = go.Scatter(x=x, y=y, name=name,
                                   marker=dict(color=COLOR[field]))

            traces.append(trace)
        return traces


def loss_curve(data_frame, analysis_fields, title, output_path):
    traces = []
    x = data_frame.index
    for field in analysis_fields:
        y = data_frame[field].values
        name = NAMING[field]
        if field in ['Q_dem_cool', 'Q_dem_heat']:  # demand data on secondary y axis
            trace = go.Scatter(x=x, y=y, name=name,
                               marker=dict(color=COLOR[field]),
                               yaxis='y2', opacity=0.6)
        else:  # primary y_axis
            trace = go.Scatter(x=x, y=y, name=name,
                               marker=dict(color=COLOR[field]))

        traces.append(trace)

    if 'P_loss_kWh' in analysis_fields:  # used to differentiate between absolute and relative values plot
        y_axis_title = 'Loss [kWh]'
    else:  # relative plot
        y_axis_title = 'Loss [% of Plant Heat Produced]'

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title=y_axis_title),
                  yaxis2=dict(title='Demand [kWh]', overlaying='y',
                              side='right'), xaxis=dict(rangeselector=dict(buttons=list([
            dict(count=1, label='1d', step='day', stepmode='backward'),
            dict(count=1, label='1w', step='week', stepmode='backward'),
            dict(count=1, label='1m', step='month', stepmode='backward'),
            dict(count=6, label='6m', step='month', stepmode='backward'),
            dict(count=1, label='1y', step='year', stepmode='backward'),
            dict(step='all')])), rangeslider=dict(), type='date', range=[data_frame.index[0],
                                                                         data_frame.index[168]],
            fixedrange=False))

    fig = dict(data=traces, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces, 'layout': layout}


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()
    LossCurvePlot(config.project, {'network-type': config.thermal_network.network_type,
                                   'scenario-name': config.scenario_name,
                                   'network-names': config.thermal_network.network_names},
                  cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
