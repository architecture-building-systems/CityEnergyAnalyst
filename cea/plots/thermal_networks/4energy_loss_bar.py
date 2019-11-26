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


class EnergyLossBarPlot(cea.plots.thermal_networks.ThermalNetworksPlotBase):
    """Implement the Thermal losses and pumping requirements per pipe plot"""
    name = "Thermal losses and pumping requirements per pipe"

    def __init__(self, project, parameters, cache):
        super(EnergyLossBarPlot, self).__init__(project, parameters, cache)
        self.network_type = parameters['network-type']
        self.network_name = parameters['network-name']
        self.network_args = [self.network_type, self.network_name]
        self.input_files = [(self.locator.get_thermal_network_pressure_losses_edges_file, self.network_args),
                            (self.locator.get_network_thermal_loss_edges_file, self.network_args)]

    @property
    def layout(self):
        return go.Layout(barmode='stack',
                         yaxis=dict(title='Energy [kWh/yr]'),
                         xaxis=dict(title='Name'))

    def calc_graph(self):
        # calculate graph
        graph = []
        # format demand values
        P_loss_kWh = self.P_loss_kWh.fillna(value=0)
        P_loss_kWh = pd.DataFrame(P_loss_kWh.sum(axis=0), columns=['P_loss_kWh'])
        Q_loss_kWh = abs(self.thermal_loss_edges_kWh.fillna(value=0))
        Q_loss_kWh = pd.DataFrame(Q_loss_kWh.sum(axis=0), columns=['Q_loss_kWh'])
        # calculate total_df
        total_df = pd.DataFrame(P_loss_kWh.values + Q_loss_kWh.values, index=Q_loss_kWh.index, columns=['total'])
        # join dataframes
        merged_df = P_loss_kWh.join(Q_loss_kWh).join(total_df)
        merged_df = merged_df.sort_values(by='total',
                                          ascending=False)  # this will get the maximum value to the left

        # iterate through P_loss_kWh to plot
        for field in ['P_loss_kWh', 'Q_loss_kWh']:
            total_percent = (merged_df[field] / merged_df['total'] * 100).round(2)
            total_percent_txt = ["(" + str(x) + " %)" for x in total_percent]
            trace = go.Bar(x=merged_df.index, y=merged_df[field].values, name=NAMING[field],
                           text=total_percent_txt,
                           orientation='v',
                           marker=dict(color=COLOR[field]))
            graph.append(trace)
        return graph

    def calc_table(self):
        P_loss_kWh = self.P_loss_kWh.fillna(value=0)
        P_loss_kWh = pd.DataFrame(P_loss_kWh.sum(axis=0), columns=['P_loss_kWh'])  # format individual loss data
        Q_loss_kWh = abs(self.thermal_loss_edges_kWh).fillna(value=0)
        Q_loss_kWh = pd.DataFrame(Q_loss_kWh.sum(axis=0), columns=['Q_loss_kWh'])  # format individual loss data
        total_df = pd.DataFrame(P_loss_kWh.values + Q_loss_kWh.values, index=Q_loss_kWh.index,
                             columns=['total'])  # calculate total loss
        merged_df = P_loss_kWh.join(Q_loss_kWh).join(total_df)
        anchors = []
        load_names = []
        median = []
        peak = []
        total_perc = []
        for field in ['P_loss_kWh', 'Q_loss_kWh']:
            # calculate graph
            anchors.append(', '.join(calc_top_three_anchor_loads(merged_df, field)))
            load_names.append(NAMING[field])  # get correct name
            median.append(round(merged_df[field].median(), 2))  # calculate median
            peak.append(round(merged_df[field].abs().max(), 2))  # calculate peak value
            local_total = round(merged_df[field].sum(), 2)  # calculate total for this building
            total_perc.append(str(local_total) + " (" + str(
                min(round(local_total / total_df.sum().values * 100, 1),
                    100.0)) + " %)")  # transform value to percentage
        column_names = ['Loss Name', 'Total [kWh/yr]', 'Peak [kWh/yr]', 'Median [kWh/yr]', 'Highest 3 Losses']
        column_values = [load_names, total_perc, peak, median, anchors]
        table_df = pd.DataFrame({cn: cv for cn, cv in zip(column_names, column_values)}, columns=column_names)
        return table_df


def calc_top_three_anchor_loads(data_frame, field):
    # returns list of top three pipes causing losses
    data_frame = data_frame.sort_values(by=field, ascending=False)
    anchor_list = data_frame[:3].index.values
    return anchor_list


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    EnergyLossBarPlot(config.project, {'network-type': config.plots.network_type,
                                       'scenario-name': config.scenario_name,
                                       'network-name': config.plots.network_name},
                      cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
