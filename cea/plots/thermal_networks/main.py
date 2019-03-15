"""
This file runs all plots of the CEA
"""

from __future__ import division
from __future__ import print_function

import time

import networkx as nx
import numpy as np
import pandas as pd

import cea.config
import cea.inputlocator
from cea.plots.thermal_networks.Supply_Return_Outdoor import supply_return_ambient_temp_plot
from cea.plots.thermal_networks.annual_energy_consumption import annual_energy_consumption_plot
from cea.plots.thermal_networks.energy_loss_bar import energy_loss_bar_plot
from cea.plots.thermal_networks.loss_curve import loss_curve
from cea.plots.thermal_networks.loss_duration_curve import loss_duration_curve
from cea.plots.thermal_networks.network_plot import network_plot

__author__ = "Lennart Rogenhofer"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Lennart Rogenhofer", "Jimeno A. Fonseca", "Shanshan Hsieh"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(locator, config):
    # initialize timer
    t0 = time.clock()

    # local variables
    network_type = config.plots.network_type
    # read in names of thermal networks if various exist
    network_names = config.plots.network_names
    # if no network names are specified, keep empty
    if not network_names:
        network_names = ['']
    # iterate through all networks

    category = "basic//thermal-network"
    for network_name in network_names:
        print('Creating plots for network: ', network_type, network_name)
        # initialize class
        plots = Plots(locator, network_type, network_name)
        # create plots
        plots.loss_curve(category)
        plots.loss_curve_relative(category)
        plots.supply_return_ambient_curve(category)
        plots.loss_duration_curve(category)
        plots.energy_loss_bar_plot(category)
        plots.energy_loss_bar_substation_plot(category)
        plots.heat_network_plot(category)
        plots.pressure_network_plot(category)
        plots.network_layout_plot(category)
        plots.annual_energy_consumption(category)

    # print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    return


class Plots(object):

    def __init__(self, locator, network_type, network_names):
        self.locator = locator
        self.demand_analysis_fields = ["Qhsf_kWh",
                                       "Qww_sys_kWh",
                                       "Qcsf_kWh"]
        self.network_name = self.preprocess_network_name(network_names)
        self.network_type = network_type
        self.plot_title_tail = self.preprocess_plot_title()
        self.plot_output_path_header = self.preprocess_plot_outputpath()
        self.readin_path = self.locator.get_network_layout_edges_shapefile(network_type, self.network_name)
        self.date = self.get_date_from_file()

        self.q_data_processed = self.preprocessing_heat_loss()
        self.p_data_processed = self.preprocessing_pressure_loss()
        self.q_network_data_rel_processed = self.preprocessing_rel_loss(self.q_data_processed['hourly_network_loss'])
        self.p_data_rel_processed = self.preprocessing_rel_loss(self.p_data_processed['hourly_loss'])
        self.network_processed = self.preprocessing_network_graph()
        self.ambient_temp = self.preprocessing_ambient_temp()
        self.plant_temp_data_processed = self.preprocessing_plant_temp()
        self.network_data_processed = self.preprocessing_network_data()
        self.network_pipe_length = self.preprocessing_pipe_length()
        self.demand_data = self.preprocessing_building_demand()
        self.network_pumping = self.preprocessing_network_pumping()

    def preprocess_network_name(self, network_name):
        '''
        Readin network name and format as a string
        '''
        if network_name == []:
            return ""
        else:
            return str(network_name)

    def preprocess_plot_outputpath(self):
        '''
        Define output path for the plots
        '''
        if self.network_type == []:  # get network type, default is DH__
            return "DH_" + str(self.network_name) + "_"
        elif len(self.network_type) >= 1:
            return str(self.network_type) + "_" + str(self.network_name) + "_"
        else:  # should never happen / should not be possible
            return "DH_" + str(self.network_name) + "_"

    def preprocess_plot_title(self):
        '''
        Format plot title ending to include network type and network name
        '''
        if not self.network_name:  # different plot titles if a network name is specified, here without network name
            if self.network_type == []:  # get network type, default is DH
                return " for DH"
            elif len(self.network_type) == 2:  # applies for both DH and DC
                return " for " + str(self.network_type)
            else:  # should never happen / should not be possible
                return ""
        else:  # plot title including network name
            if self.network_type == []:  # get network type, default is DH
                return " for DH in " + str(self.network_name)
            elif len(self.network_type) == 2:
                return " for " + str(self.network_type) + " in " + str(self.network_name)
            else:  # should never happen / should not be possible
                return " in " + str(self.network_name)

    def get_date_from_file(self):
        # get date
        buildings = self.locator.get_zone_building_names()
        df_date = pd.read_csv(self.locator.get_demand_results_file(buildings[0]))
        return df_date["DATE"]

    def preprocessing_building_demand(self):

        # read in aggregated values
        df2 = pd.read_csv(self.locator.get_thermal_demand_csv_file(self.network_type, self.network_name),
                          index_col=0)  # read in yearly total loads
        df2.set_index(self.date)
        df2 = df2 / 1000

        df = df2.sum(axis=1)
        df = pd.DataFrame(df)
        if self.network_type == 'DH':
            df.columns = ['Q_dem_heat']
        else:
            df.columns = ['Q_dem_cool']

        df3 = df.sum()[0]
        return {"hourly_loads": df, "buildings_hourly": df2, "annual_loads": df3}

    def preprocessing_ambient_temp(self):
        '''
        Read in ambient temperature data at first building.
        This assumes that all buildings are relatively close to each other and have the same ambient temperature.
        '''
        building_names = self.locator.get_zone_building_names()
        building_name = building_names[0]  # read in first building name
        demand_file = pd.read_csv(self.locator.get_demand_results_file(building_name))
        ambient_temp = demand_file["T_ext_C"].values  # read in amb temp
        return pd.DataFrame(ambient_temp)

    def preprocessing_pipe_length(self):
        df = pd.read_csv(self.locator.get_optimization_network_edge_list_file(self.network_type, self.network_name))[
            ['Name', 'pipe length']]
        total_pipe_length = df['pipe length'].sum()
        return total_pipe_length

    def preprocessing_plant_temp(self):
        '''
        Read in and format plant supply and return temperatures for each plant in the network.
        '''
        plant_nodes = self.preprocessing_network_graph()["Plants_names"]  # read in all plant nodes
        # read in supply and retun temperature of all nodes
        df_s = pd.read_csv(self.locator.get_Tnode_s(self.network_name, self.network_type))
        df_r = pd.read_csv(self.locator.get_Tnode_r(self.network_name, self.network_type))
        df = pd.DataFrame()
        for i in range(len(plant_nodes)):
            # This segment handles the unit conversion of the given temperatures. In the standard case, they should already be in deg C
            if pd.DataFrame(df_s[str(plant_nodes[i])]).min(axis=0).min() < 200:  # unit is already deg C
                df['Supply_' + str(plant_nodes[i])] = df_s[str(plant_nodes[i])]
            else:
                df['Supply_' + str(plant_nodes[i])] = df_s[str(plant_nodes[i])] - 273.15
            if pd.DataFrame(df_r[str(plant_nodes[i])]).min(axis=0).min() < 200:  # unit is already deg C
                df['Return_' + str(plant_nodes[i])] = df_r[str(plant_nodes[i])]
            else:
                df['Return_' + str(plant_nodes[i])] = df_r[str(plant_nodes[i])] - 273.15
        return {'Data': df, 'Plants': plant_nodes}

    def preprocessing_heat_loss(self):
        '''
        Read in and format edge heat losses for all 8760 time steps
        '''
        df = pd.read_csv(self.locator.get_qloss(self.network_name, self.network_type))
        df = abs(df).sum(axis=1)  # aggregate heat losses of all edges
        df1 = abs(df.values).sum()  # sum over all timesteps
        return {"hourly_network_loss": pd.DataFrame(df), "yearly_loss": df1}

    def preprocessing_pressure_loss(self):
        '''
        Read in pressure loss data for all time steps.
        '''
        df = pd.read_csv(self.locator.get_ploss(self.network_name, self.network_type))
        df = df['pressure_loss_total_kW']
        df1 = df.values.sum()  # sum over all timesteps
        return {"hourly_loss": pd.DataFrame(df), "yearly_loss": df1}

    def preprocessing_rel_loss(self, absolute_loss):
        '''
        Calculate relative heat or pressure loss:
        1. Sum up all plant heat produced in each time step
        2. Divide absolute losses by that value
        '''
        df = pd.read_csv(self.locator.get_qplant(self.network_name, self.network_type))  # read plant heat supply
        df = abs(df)  # make sure values are positive
        if len(df.columns.values) > 1:  # sum of all plants
            df = df.sum(axis=1)
        df[df == 0] = np.nan
        df = np.reshape(df.values, (8760, 1))  # necessary to avoid errors from shape mismatch
        rel = absolute_loss.values / df * 100  # calculate relative value in %
        rel = np.nan_to_num(rel)  # remove nan or inf values to avoid runtime error
        # if relative losses are more than 100% temperature requirements are not met. All produced heat is lost.
        rel[rel > 100] = 100
        # don't show 0 values
        rel[rel == 0] = np.nan
        mean_loss = np.nanmean(rel)  # calculate average loss of nonzero values
        rel = np.round(rel, 2)  # round results
        mean_loss = np.round(mean_loss, 2)
        return {"hourly_loss": pd.DataFrame(rel), "average_loss": mean_loss}

    def preprocessing_network_graph(self):
        '''
        Setup network graph, find shortest path between each plant and each node.
        Identify node coordinates.
        '''
        # read in edge node matrix
        df = pd.read_csv(self.locator.get_optimization_network_edge_node_matrix_file(self.network_type,
                                                                                     self.network_name),
                         index_col=0)
        # read in node data
        node_data = pd.read_csv(self.locator.get_optimization_network_node_list_file(self.network_type,
                                                                                     self.network_name),
                                index_col=0)
        # identify number of plants and nodes
        plant_nodes = []
        plant_nodes_names = []
        for node, node_index in zip(df.index, range(len(df.index))):
            if max(df.ix[node]) <= 0:  # only -1 and 0 so plant!
                plant_nodes.append(node_index)
                plant_nodes_names.append(node)
        # convert df to networkx type graph
        df = np.transpose(df)  # transpose matrix to more intuitively setup graph
        graph = nx.Graph()  # set up networkx type graph
        for i in range(df.shape[0]):
            new_edge = [0, 0]
            for j in range(0, df.shape[1]):
                if df.iloc[i][df.columns[j]] == 1:
                    new_edge[0] = j
                elif df.iloc[i][df.columns[j]] == -1:
                    new_edge[1] = j
            graph.add_edge(new_edge[0], new_edge[1], edge_number=i)  # add edges to graph

        # find node coordinates
        coords = node_data['coordinates']
        node_names = node_data['Name']
        coordinates = {}
        node_numbers = []
        for name in node_names:
            number = int(name.replace('NODE', ''))
            node_numbers.append(number)
        # reformat string
        for node, node_number in zip(coords, node_numbers):
            node = node.replace("(", "")
            node = node.replace(")", "")
            node = node.replace(",", "")
            node = node.split(" ")
            if not node_number in coordinates.keys():  # add node only if doesn't exist in dictionary already
                coordinates[node_number] = float(node[0]), float(node[1])

        return {"Network": graph, "Plants": plant_nodes,
                "Plants_names": plant_nodes_names,
                'edge_node': np.transpose(df), 'coordinates': coordinates}

    def preprocessing_network_data(self):
        '''
        Read in and format network data such as diameters, hourly node temperatures and pressures,
        edge heat and pressure losses
        '''
        # read in edge diameters
        edge_data = pd.read_csv(self.locator.get_optimization_network_edge_list_file(self.network_type,
                                                                                     self.network_name),
                                index_col=0)
        edge_diam = edge_data['D_int_m']  # diameters of each edge
        DN = edge_data['Pipe_DN_y']
        d1 = pd.read_csv(
            self.locator.get_Tnode_s(self.network_name, self.network_type)) - 273.15  # node supply temperature
        d2 = pd.read_csv(self.locator.get_optimization_network_layout_qloss_system_file(self.network_type,
                                                                                        self.network_name))  # edge loss
        d3 = pd.read_csv(self.locator.get_optimization_network_layout_ploss_system_edges_file(self.network_type,
                                                                                              self.network_name))
        d4 = pd.read_csv(self.locator.get_optimization_network_substation_ploss_file(self.network_type,
                                                                                     self.network_name))
        diam = pd.DataFrame(edge_diam)
        return {'Diameters': diam, 'DN': DN, 'Tnode_hourly_C': d1, 'Q_loss_kWh': d2, 'P_loss_kWh': d3,
                'P_loss_substation_kWh': d4}

    def preprocessing_network_pumping(self):
        df_pumping_kW = pd.read_csv(
            self.locator.get_optimization_network_layout_pressure_drop_kw_file(self.network_type, self.network_name))
        df_pumping_supply_kW = df_pumping_kW['pressure_loss_supply_kW']
        df_pumping_return_kW = df_pumping_kW['pressure_loss_return_kW']
        df_pumping_allpipes_kW = df_pumping_supply_kW + df_pumping_return_kW
        df_pumping_substations_kW = df_pumping_kW['pressure_loss_substations_kW']
        return {'Pumping_allpipes_kWh': df_pumping_allpipes_kW, 'Pumping_substations_kWh': df_pumping_substations_kW}

    ''' currently unused
    def preprocessing_costs_scenarios(self):
        data_processed = pd.DataFrame()
        for scenario in self.scenarios:
            locator = cea.inputlocator.InputLocator(scenario)
            scenario_name = os.path.basename(scenario)
            data_raw = 0 #todo: once cost data available, read in here
            data_raw_df = pd.DataFrame({scenario_name: data_raw}, index=data_raw.index).T
            data_processed = data_processed.append(data_raw_df)
        return data_processed
    '''

    # PLOTS

    def loss_curve(self, category):
        title = "Heat and Pressure Losses" + self.plot_title_tail  # title
        output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + 'losses_curve', category)  # desitination path
        analysis_fields = ["P_loss_kWh", "Q_loss_kWh"]  # plot data names
        for column in self.demand_data['hourly_loads'].columns:
            analysis_fields = analysis_fields + [str(column)]  # add demand data to names
        data = self.p_data_processed['hourly_loss'].join(
            pd.DataFrame(self.q_data_processed['hourly_network_loss'].sum(axis=1)))  # join pressure and heat loss data
        data.index = self.demand_data['hourly_loads'].index  # match index
        data = data.join(self.demand_data['hourly_loads'])  # add demand data
        data.columns = analysis_fields  # format dataframe columns
        data = data.set_index(self.date)
        plot = loss_curve(data, analysis_fields, title, output_path)  # call plot
        return plot

    def loss_curve_relative(self, category):
        title = "Relative Heat and Pressure Losses" + self.plot_title_tail  # title
        output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + 'relative_losses_curve', category)  # desitination path
        analysis_fields = ["P_loss_%", "Q_loss_%"]  # data headers
        for column in self.demand_data['hourly_loads'].columns:
            analysis_fields = analysis_fields + [str(column)]  # add demand names to data headers
        df = self.p_data_rel_processed['hourly_loss']  # add relative pressure data
        # format and join dataframes
        df = df.rename(columns={0: 1})
        data = df.join(pd.DataFrame(self.q_network_data_rel_processed['hourly_loss'].sum(axis=1)))
        data.index = self.demand_data['hourly_loads'].index
        data = data.join(self.demand_data['hourly_loads'])
        data.columns = analysis_fields
        data = data.abs()  # make sure all data is positive (relevant for DC)
        data = data.set_index(self.date)
        plot = loss_curve(data, analysis_fields, title, output_path)
        return plot

    def supply_return_ambient_curve(self, category):
        analysis_fields = ["T_sup_C", "T_ret_C"]  # data headers
        data = self.plant_temp_data_processed['Data']  # read in plant supply and return temperatures
        data2 = self.ambient_temp  # read in abient temperatures
        plant_nodes = self.plant_temp_data_processed['Plants']  # plant node names
        for i in range(len(plant_nodes)):  # iterate through all plants
            title = "Supply and Return Temp. at Plant " + str(
                plant_nodes[i]) + " vs Ambient Temp." + self.plot_title_tail
            data_part = pd.DataFrame()
            data_part['0'] = data['Supply_' + str(plant_nodes[i])]
            data_part['1'] = data['Return_' + str(plant_nodes[i])]
            output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header +
                                                                 'Tamb_Tsup_Tret_curve_plant_' + str(
                plant_nodes[i]), category)
            data_part.columns = analysis_fields
            plot = supply_return_ambient_temp_plot(data_part, data2, analysis_fields, title, output_path)
        return plot

    def loss_duration_curve(self, category):
        title = "Load duration curve of pump" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + 'load_duration_curve_of_pump', category)
        analysis_fields = ["P_loss_kWh"]  # data to plot
        data = self.p_data_processed['hourly_loss']
        data.columns = analysis_fields
        plot = loss_duration_curve(data, analysis_fields, title, output_path)
        return plot

    def heat_network_plot(self, category):
        title = " Network Thermal Loss" + self.plot_title_tail
        output_path = self.locator.get_networks_plots_file(self.plot_output_path_header + 'thermal_loss_network',
                                                           category)
        analysis_fields = ['Tnode_hourly_C', 'Q_loss_kWh']  # data to plot
        all_nodes = pd.read_csv(
            self.locator.get_optimization_network_node_list_file(self.network_type, self.network_name))
        data = {'Diameters': self.network_data_processed['Diameters'],  # read diameters
                'coordinates': self.network_processed['coordinates'],  # read node coordinates
                'edge_node': self.network_processed['edge_node'],  # read edge node matrix of node connections
                analysis_fields[0]: self.network_data_processed[analysis_fields[0]],  # read Temperature data
                analysis_fields[1]: self.network_data_processed[analysis_fields[1]]}  # read edge loss data
        building_demand_data = self.demand_data['buildings_hourly']  # read building demand data
        plot = network_plot(data, title, output_path, analysis_fields, building_demand_data, all_nodes)
        return plot

    def pressure_network_plot(self, category):
        title = " Network Pressure Loss" + self.plot_title_tail
        output_path = self.locator.get_networks_plots_file(self.plot_output_path_header + 'pressure_loss_network',
                                                           category)
        analysis_fields = ['P_loss_substation_kWh', 'P_loss_kWh']

        all_nodes = pd.read_csv(
            self.locator.get_optimization_network_node_list_file(self.network_type, self.network_name))
        data = {'Diameters': self.network_data_processed['Diameters'],  # read diameters
                'coordinates': self.network_processed['coordinates'],  # read node coordinates
                'edge_node': self.network_processed['edge_node'],  # read edge node matrix of node connections
                analysis_fields[0]: self.network_data_processed[analysis_fields[0]],  # substation losses
                analysis_fields[1]: self.network_data_processed[analysis_fields[1]]}  # read edge pressure loss data
        building_demand_data = self.demand_data['buildings_hourly']  # read building demands
        plot = network_plot(data, title, output_path, analysis_fields, building_demand_data, all_nodes)
        return plot

    def network_layout_plot(self, category):
        title = " Network Layout" + self.plot_title_tail
        output_path = self.locator.get_networks_plots_file(self.plot_output_path_header + 'network_layout', category)
        all_nodes = pd.read_csv(
            self.locator.get_optimization_network_node_list_file(self.network_type, self.network_name))
        data = {'DN': self.network_data_processed['DN'],
                'Diameters': self.network_data_processed['Diameters'],  # read diameters
                'coordinates': self.network_processed['coordinates'],  # read node coordinates
                'edge_node': self.network_processed['edge_node']}  # read edge node matrix of node connections
        building_demand_data = self.demand_data['buildings_hourly']  # read building demands
        analysis_fields = ['', '']
        plot = network_plot(data, title, output_path, analysis_fields, building_demand_data, all_nodes)
        return plot

    def energy_loss_bar_plot(self, category):
        title = "Thermal losses and pumping requirements per pipe" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + 'energy_loss_bar', category)
        analysis_fields = ['P_loss_kWh', 'Q_loss_kWh']  # data to plot
        data = [self.network_data_processed['P_loss_kWh'], abs(self.network_data_processed['Q_loss_kWh'])]
        plot = energy_loss_bar_plot(data, analysis_fields, title, output_path)
        return plot

    def energy_loss_bar_substation_plot(self, category):
        title = "Pumping requirements per building substation" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(
            self.plot_output_path_header + 'energy_loss_substation_bar', category)
        analysis_fields = ['P_loss_kWh']  # data to plot
        data = [self.network_data_processed['P_loss_substation_kWh']]
        plot = energy_loss_bar_plot(data, analysis_fields, title, output_path)
        return plot

    def annual_energy_consumption(self, category):
        title = "Annual energy consumption " + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + 'annual_energy_consumption',
                                                             category)
        analysis_fields = ['Q_dem_kWh', 'P_loss_substations_kWh', 'P_loss_kWh', 'Q_loss_kWh']
        data = [self.demand_data['annual_loads'], self.network_pumping['Pumping_substations_kWh'],
                self.network_pumping['Pumping_allpipes_kWh'], abs(self.network_data_processed['Q_loss_kWh']),
                self.network_pipe_length, self.demand_data['hourly_loads']]
        plot = annual_energy_consumption_plot(data, analysis_fields, title, output_path)
        return plot


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
