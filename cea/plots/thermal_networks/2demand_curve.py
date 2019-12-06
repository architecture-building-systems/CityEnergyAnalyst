from __future__ import division
from __future__ import print_function

import pandas as pd
import plotly.graph_objs as go

import cea.plots.thermal_networks
from cea.plots.variable_naming import NAMING, COLOR

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
    name = "Load curve of Heat and Pressure Losses"

    def __init__(self, project, parameters, cache):
        super(LossCurvePlot, self).__init__(project, parameters, cache)
        self.network_type = parameters['network-type']
        self.network_name = parameters['network-name']
        self.yaxis_title = 'Demand [kWh]'
        self.network_args = [self.network_type, self.network_name]
        self.input_files = [(self.locator.get_thermal_demand_csv_file, self.network_args),
                            (self.locator.get_network_energy_pumping_requirements_file, self.network_args),
                            (self.locator.get_network_thermal_loss_edges_file, self.network_args)]

    @property
    def layout(self):
        return dict(yaxis=dict(title=self.yaxis_title), xaxis=dict(rangeselector=dict(buttons=list([
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
        traces = []
        x = data_frame.index
        for field in data_frame.columns:
            y = data_frame[field].values
            name = NAMING[field]
            trace = go.Scattergl(x=x, y=y, name=name,
                                 marker=dict(color=COLOR[field]))
            traces.append(trace)
        return traces

    def calc_data_frame(self):
        hourly_loads = self.hourly_loads
        analysis_fields = ["P_loss_kWh", "Q_loss_kWh"]  # plot data names
        analysis_fields += [str(column) for column in hourly_loads.columns]
        data_frame = self.plant_pumping_requirement_kWh.join(
            pd.DataFrame(self.hourly_heat_loss.sum(axis=1)))  # join pressure and heat loss data
        data_frame.index = hourly_loads.index  # match index
        data_frame = data_frame.join(hourly_loads)  # add demand data
        data_frame.columns = analysis_fields  # format dataframe columns
        data_frame.index = self.date
        return data_frame


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    LossCurvePlot(config.project, {'network-type': config.plots.network_type,
                                   'scenario-name': config.scenario_name,
                                   'network-name': config.plots.network_name},
                  cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
