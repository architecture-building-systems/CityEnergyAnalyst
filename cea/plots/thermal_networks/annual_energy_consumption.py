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
        name = "Annual energy consumption"

        def __init__(self, project, parameters, cache):
            super(AnnualEnergyConsumptionPlot, self).__init__(project, parameters, cache)
            self.network_args = [self.network_type, self.network_name]
            self.input_files = [
                (self.locator.get_thermal_demand_csv_file, self.network_args),
                (self.locator.get_thermal_network_layout_pressure_drop_kw_file, self.network_args),
                (self.locator.get_thermal_network_edge_list_file, self.network_args)]

        @property
        def layout(self):
            return go.Layout(title=self.title, barmode='stack',  # annotations=annotations,
                             yaxis=dict(title='Energy consumption [MWh/yr]'),
                             xaxis=dict(domain=[0.05, 0.4]),
                             yaxis2=dict(title='Energy consumption per length [MWh/yr/m]', anchor='x2'),
                             xaxis2=dict(domain=[0.5, 0.85]))

        def calc_graph(self):
            analysis_fields = ['Q_dem_kWh', 'P_loss_substations_kWh', 'P_loss_kWh', 'Q_loss_kWh']
            annual_loads = self.hourly_loads.sum()[0]
            Pumping_substations_kWh = self.Pumping_substations_kWh
            Pumping_allpipes_kWh = self.Pumping_allpipes_kWh
            Q_loss_kWh = abs(self.Q_loss_kWh)

            graph = []
            # format demand values
            annual_consumption = {'Q_dem_kWh': annual_loads,
                                  'P_loss_substations_kWh': Pumping_substations_kWh.sum(),
                                  'P_loss_kWh': Pumping_allpipes_kWh.sum(),
                                  'Q_loss_kWh': Q_loss_kWh.sum().sum()}
            total_energy_MWh = sum(annual_consumption.values()) / 1000

            total_pipe_length = self.network_pipe_length
            consumption_per_length = {'Q_dem_kWh': annual_loads / total_pipe_length,
                                      'P_loss_substations_kWh': Pumping_substations_kWh.sum() / total_pipe_length,
                                      'P_loss_kWh': Pumping_allpipes_kWh.sum() / total_pipe_length,
                                      'Q_loss_kWh': Q_loss_kWh.sum().sum() / total_pipe_length}
            total_energy_MWhperm = sum(consumption_per_length.values()) / 1000

            # iterate through annual_consumption to plot
            for field in analysis_fields:
                x = ['annual consumption']
                y = annual_consumption[field] / 1000
                name = field.split('_kWh', 1)[0]
                total_perc = (y / total_energy_MWh * 100).round(2)
                total_perc_txt = [str(y.round(0)) + " MWh (" + str(total_perc) + " %)"]
                trace = go.Bar(x=x, y=[y], name=NAMING[field], text=total_perc_txt, marker=dict(color=COLOR[field]),
                               width=0.4)
                graph.append(trace)

            for field in analysis_fields:
                x = ['consumption per length']
                y = consumption_per_length[field] / 1000
                total_perc = (y / total_energy_MWhperm * 100).round(2)
                total_perc_txt = [str(y.round(0)) + " MWh/m (" + str(total_perc) + " %)"]
                trace = go.Bar(x=x, y=[y], name=field.split('_kWh', 1)[0], text=total_perc_txt,
                               marker=dict(color=COLOR[field]),
                               xaxis='x2', yaxis='y2', width=0.4, showlegend=False)
                graph.append(trace)

            return graph


def annual_energy_consumption_plot(data_frame, analysis_fields, title, output_path):
    # CALCULATE GRAPH
    traces_graph_1, total_energy_MWh = calc_graph(analysis_fields, data_frame)

    # traces_graph_2 = calc_graph(analysis_fields, data_frame, substation_plot_flag)
    # PLOT GRAPH
    splitted_path = os.path.split(output_path)[0]
    network_type_name = os.path.split(output_path)[1].split('annual')[0]
    file_name = network_type_name + 'network_layout.png'
    network_image_path = os.path.join(splitted_path, file_name)
    # image_network = [dict(source=network_image_path, xref="paper", yref="paper",
    # x=0.95, y=0.5, sizex=0.5, sizey=0.5, xanchor="right", yanchor="middle")]
    length_m = str((data_frame[4] / 1000).round(3))
    load_density_kWperm = str((total_energy_MWh / (data_frame[4])).round(1))
    annotations = list(
        [dict(
            text='<b>Summary: </b><br>'
                 'Total network length:<b>' + length_m + '[km]</b><br>'
                                                         'Linear heat density:<b>' + load_density_kWperm + '[MWh/m]</b><br>'
                                                                                                           'See <b>' + str(
                file_name) + '</b> for network layout.'
            , x=0.9, y=0.0, xanchor='left', xref='paper', yref='paper',
            align='left', showarrow=False, bgcolor="rgb(254,220,198)")])

    # traces_graph_1.append(traces_graph_2)
    layout = go.Layout(images=LOGO, title=title, barmode='stack', annotations=annotations,
                       yaxis=dict(title='Energy consumption [MWh/yr]'),
                       xaxis=dict(domain=[0.05, 0.4]),
                       yaxis2=dict(title='Energy consumption per length [MWh/yr/m]', anchor='x2'),
                       xaxis2=dict(domain=[0.5, 0.85]))
    fig = go.Figure(data=traces_graph_1, layout=layout)
    plot(fig, auto_open=False, filename=output_path)

    return {'data': traces_graph_1, 'layout': layout}


def calc_graph(analysis_fields, data_frame):
    # calculate graph
    graph = []
    # format demand values
    data_1 = {}
    data_1['Q_dem_kWh'] = data_frame[0]
    data_1['P_loss_substations_kWh'] = data_frame[1].sum()
    data_1['P_loss_kWh'] = data_frame[2].sum()
    data_1['Q_loss_kWh'] = data_frame[3].sum().sum()
    total_energy_MWh = sum(data_1.values()) / 1000

    data_2 = {}
    total_pipe_length = data_frame[4]
    data_2['Q_dem_kWh'] = data_frame[0] / total_pipe_length
    data_2['P_loss_substations_kWh'] = data_frame[1].sum() / total_pipe_length
    data_2['P_loss_kWh'] = data_frame[2].sum() / total_pipe_length
    data_2['Q_loss_kWh'] = data_frame[3].sum().sum() / total_pipe_length
    total_energy_MWhperm = sum(data_2.values()) / 1000

    # iterate through data_1 to plot
    for field in analysis_fields:
        x = ['annual consumption']
        y = data_1[field] / 1000
        name = field.split('_kWh', 1)[0]
        total_perc = (y / total_energy_MWh * 100).round(2)
        total_perc_txt = [str(y.round(0)) + " MWh (" + str(total_perc) + " %)"]
        trace = go.Bar(x=x, y=[y], name=NAMING[field], text=total_perc_txt, marker=dict(color=COLOR[field]), width=0.4)
        graph.append(trace)

    for field in analysis_fields:
        x = ['consumption per length']
        y = data_2[field] / 1000
        total_perc = (y / total_energy_MWhperm * 100).round(2)
        total_perc_txt = [str(y.round(0)) + " MWh/m (" + str(total_perc) + " %)"]
        trace = go.Bar(x=x, y=[y], name=field.split('_kWh', 1)[0], text=total_perc_txt, marker=dict(color=COLOR[field]),
                       xaxis='x2', yaxis='y2', width=0.4, showlegend=False)
        graph.append(trace)

    return graph, total_energy_MWh


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
