from __future__ import division
from __future__ import print_function

import numpy as np
import pandas as pd
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
        'network-type': 'plots:network-type',
        'network-name': 'plots:network-name',
        'plant-node': 'plots:plant-node',
    }

    def __init__(self, project, parameters, cache):
        super(SupplyReturnAmbientCurvePlot, self).__init__(project, parameters, cache)
        self.network_args = [self.network_type, self.network_name]
        self.plant_node = self.parameters['plant-node']
        self.input_files = [(self.locator.get_thermal_demand_csv_file, self.network_args),
                            (self.locator.get_thermal_network_layout_pressure_drop_kw_file, self.network_args),
                            (self.locator.get_thermal_network_qloss_system_file, self.network_args)]

    @property
    def title(self):
        """Override the version in ThermalNetworksPlotBase"""
        name = "Supply and Return Temp. at Plant {plant_node} vs Ambient Temp.".format(plant_node=self.plant_node)
        if not self.network_name:  # different plot titles if a network name is specified, here without network name
            return '{name} for {network_type}'.format(name=name, network_type=self.network_type)
        else:
            # plot title including network name
            return '{name} for {network_type} in {network_name}'.format(name=name, network_type=self.network_type,
                                                                        network_name=self.network_name)

    @property
    def layout(self):
        return dict(yaxis=dict(title='Temperature [deg C]'),
                    xaxis=dict(title='Ambient Temperature [deg C]'))

    def calc_graph(self):
        traces = []
        data_frame = self.plant_temperatures
        analysis_fields = data_frame.columns
        ambient_temp = self.ambient_temp
        for field in analysis_fields:
            y = data_frame[field].values
            # sort by ambient temperature, needs some helper variables
            y_old = np.vstack((np.array(ambient_temp.values.T), y))
            y_new = np.vstack((np.array(ambient_temp.values.T), y))
            y_new[0, :] = y_old[0, :][
                y_old[0, :].argsort()]  # y_old[0, :] is the ambient temperature which we are sorting by
            y_new[1, :] = y_old[1, :][y_old[0, :].argsort()]
            trace = go.Scattergl(x=y_new[0], y=y_new[1], name=NAMING[field],
                               marker=dict(color=COLOR[field]),
                               mode='markers')
            traces.append(trace)
        return traces

    @property
    def ambient_temp(self):
        """
        Read in ambient temperature data at first building.
        This assumes that all buildings are relatively close to each other and have the same ambient temperature.
        """
        building_name = self.locator.get_zone_building_names()[0]  # read in first building name
        demand_file = pd.read_csv(self.locator.get_demand_results_file(building_name))
        ambient_temp = demand_file["T_ext_C"].values  # read in amb temp
        return pd.DataFrame(ambient_temp)

    @property
    def output_path(self):
        name = 'Tamb_Tsup_Tret_curve_plant'
        file_name = '{network_type}_{network_name}_{name}_{plant}'.format(network_type=self.network_type,
                                                                          network_name=self.network_name,
                                                                          name=name,
                                                                          plant=self.plant_node)
        return self.locator.get_timeseries_plots_file(file_name, self.category_path)

    @property
    def plant_temperatures(self):
        supply_df = pd.read_csv(
            self.locator.get_thermal_network_layout_supply_temperature_file(self.network_type, self.network_name))
        return_df = pd.read_csv(
            self.locator.get_thermal_network_layout_return_temperature_file(self.network_type, self.network_name))

        plant_node_supply = supply_df[self.plant_node]
        plant_node_return = return_df[self.plant_node]

        if plant_node_supply.min() > 200:
            # unit is in deg K, convert to deg C
            plant_node_supply -= 273.15
        if plant_node_return.min() > 200:
            # unit is in deg K, convert to deg C
            plant_node_return -= 273.15

        return pd.DataFrame({'T_sup_C': plant_node_supply, 'T_ret_C': plant_node_return},
                            columns=['T_sup_C', 'T_ret_C'])


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
        trace = go.Scattergl(x=y_new[0], y=y_new[1], name=NAMING[field],
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
    SupplyReturnAmbientCurvePlot(config.project,
                                 {'network-type': config.plots.network_type,
                                  'scenario-name': config.scenario_name,
                                  'network-name': config.plots.network_name,
                                  'plant-node': config.plots.plant_node},
                                 cache).plot(auto_open=True)



if __name__ == '__main__':
    main()
