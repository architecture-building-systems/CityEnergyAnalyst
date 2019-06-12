from __future__ import division
from __future__ import print_function

import numpy as np
import plotly.graph_objs as go
from plotly.offline import plot
import cea.plots.thermal_networks
from cea.plots.variable_naming import LOGO, NAMING, COLOR

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SupplyReturnAmbientCurvePlot(cea.plots.thermal_networks.ThermalNetworksPlotBase):
    """Implement the heat and pressure losses plot"""
    name = "Supply and Return vs. Ambient Temp"

    expected_parameters = {
        'scenario-name': 'general:scenario-name',
        'network-type': 'thermal-network:network-type',
        'network-names': 'thermal-network:network-names',
    }

    def __init__(self, project, parameters, cache):
        super(SupplyReturnAmbientCurvePlot, self).__init__(project, parameters, cache)
        self.network_args = [self.network_type, self.network_name]
        self.input_files = [(self.locator.get_thermal_demand_csv_file, self.network_args),
                            (self.locator.get_thermal_network_layout_pressure_drop_kw_file, self.network_args),
                            (self.locator.get_thermal_network_qloss_system_file, self.network_args)]

    @property
    def layout(self):
        return dict(title=self.title, yaxis=dict(title=self.yaxis_title),
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
        data_frame = self.calc_data_frame()


def supply_return_ambient_temp_plot(data_frame, data_frame_2, analysis_fields, title, output_path):
    traces = []
    for field in analysis_fields:
        y = data_frame[field].values
        # sort by ambient temperature, needs some helper variables
        y_old = np.vstack((np.array(data_frame_2.values.T), y))
        y_new = np.vstack((np.array(data_frame_2.values.T), y))
        y_new[0, :] = y_old[0, :][
            y_old[0, :].argsort()]  # y_old[0, :] is the ambient temperature which we are sorting by
        y_new[1, :] = y_old[1, :][y_old[0, :].argsort()]
        trace = go.Scatter(x=y_new[0], y=y_new[1], name=NAMING[field],
                           marker=dict(color=COLOR[field]),
                           mode='markers')
        traces.append(trace)

    # CREATE FIRST PAGE WITH TIMESERIES
    layout = dict(images=LOGO, title=title, yaxis=dict(title='Temperature [deg C]'),
                  xaxis=dict(title='Ambient Temperature [deg C]'))

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

    LossCurveRelativePlot(config.project, {'network-type': config.thermal_network.network_type,
                                           'scenario-name': config.scenario_name,
                                           'network-names': config.thermal_network.network_names},
                          cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
