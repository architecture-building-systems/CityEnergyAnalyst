from __future__ import division
from __future__ import print_function

import os

import cea.plots.thermal_networks
import plotly.graph_objs as go
from plotly.offline import plot

from cea.plots.variable_naming import NAMING, LOGO, COLOR

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class AnnualEnergyConsumptionPlot(cea.plots.thermal_networks.ThermalNetworksPlotBase):
        """Implement the Annual energy consumption plot"""
        name = "Yearly energy consumption"

        def __init__(self, project, parameters, cache):
            super(AnnualEnergyConsumptionPlot, self).__init__(project, parameters, cache)
            self.network_type = parameters['network-type']
            self.network_name = parameters['network-name']
            self.network_args = [self.network_type, self.network_name]
            self.input_files = [
                (self.locator.get_thermal_demand_csv_file, self.network_args),
                (self.locator.get_network_energy_pumping_requirements_file, self.network_args),
                (self.locator.get_network_total_thermal_loss_file, self.network_args)]

        @property
        def layout(self):
            return go.Layout(barmode='stack',  # annotations=annotations,
                             yaxis=dict(title='Energy consumption [MWh/yr]', domain=[0, 1]),
                             xaxis=dict(domain=[0.05, 0.4]),
                             yaxis2=dict(title='Energy consumption per length [MWh/yr/m]', anchor='x2', domain=[0, 1]),
                             xaxis2=dict(domain=[0.5, 0.85]))

        def calc_graph(self):
            analysis_fields = ['Q_dem_kWh', 'P_loss_kWh', 'Q_loss_kWh']
            annual_loads = self.hourly_loads.sum()[0]
            Pumping_kWh = self.plant_pumping_requirement_kWh.sum()[0]
            Q_loss_kWh = self.total_thermal_losses_kWh.sum()[0]

            graph = []
            # format demand values
            annual_consumption = {'Q_dem_kWh': annual_loads,
                                  'P_loss_kWh': Pumping_kWh,
                                  'Q_loss_kWh': Q_loss_kWh}
            total_energy_MWh = sum(annual_consumption.values()) / 1000

            total_pipe_length = self.network_pipe_length
            consumption_per_length = {'Q_dem_kWh': annual_loads / total_pipe_length,
                                      'P_loss_kWh': Pumping_kWh / total_pipe_length,
                                      'Q_loss_kWh': Q_loss_kWh / total_pipe_length}
            total_energy_MWhperm = sum(consumption_per_length.values()) / 1000

            # iterate through annual_consumption to plot
            for field in analysis_fields:
                x = ['annual consumption']
                y = annual_consumption[field] / 1000
                total_perc = (y / total_energy_MWh * 100).round(2)
                total_perc_txt = [str(y.round(1)) + " MWh (" + str(total_perc) + " %)"]
                trace = go.Bar(x=x, y=[y], name=NAMING[field], text=total_perc_txt, marker=dict(color=COLOR[field]),
                               width=0.4)
                graph.append(trace)

            for field in analysis_fields:
                x = ['consumption per length']
                y = consumption_per_length[field] / 1000
                total_perc = (y / total_energy_MWhperm * 100).round(2)
                total_perc_txt = [str(y.round(1)) + " MWh/m (" + str(total_perc) + " %)"]
                trace = go.Bar(x=x, y=[y], name=field.split('_kWh', 1)[0], text=total_perc_txt,
                               marker=dict(color=COLOR[field]),
                               xaxis='x2', yaxis='y2', width=0.4, showlegend=False)
                graph.append(trace)

            return graph

def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.PlotCache(config.project)
    cache = cea.plots.cache.NullPlotCache()
    AnnualEnergyConsumptionPlot(config.project, {'network-type': config.plots.network_type,
                                                 'scenario-name': config.scenario_name,
                                                 'network-name': config.plots.network_name},
                                cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
