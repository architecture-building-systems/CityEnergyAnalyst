"""
This file runs all plots of the CEA
"""

from __future__ import division
from __future__ import print_function

import time

import pandas as pd
import numpy as np
import networkx as nx

import cea.config
import cea.inputlocator
from cea.plots.thermal_networks.loss_curve import loss_curve
from cea.plots.thermal_networks.loss_curve import loss_curve_relative

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def plots_main(locator, config):
    # initialize timer
    t0 = time.clock()

    # local variables
    network_type = config.dashboard.network_type
    network_name = config.dashboard.network_name

    # initialize class
    plots = Plots(locator, network_type, network_name)

    plots.loss_curve()
    plots.loss_curve_relative()

    # print execution time
    time_elapsed = time.clock() - t0
    print('done - time elapsed: %d.2f seconds' % time_elapsed)

    return


class Plots():

    def __init__(self, locator, network_type, network_name):
        self.locator = locator
        self.demand_analysis_fields = ["Epump_loss_kWh",
                                       "Qnetwork_loss_kWh",
                                       "Epump_loss_%",
                                       "Qnetwork_loss_%",
                                       "Psup_node_Pa",
                                       "Pret_node_Pa",
                                       "Tsup_node_K",
                                       "Tret_node_K"]
        self.network_name = self.preprocess_network_name(network_name)
        self.q_data_processed = self.preprocessing_heat_loss(network_type, self.network_name)
        self.p_data_processed = self.preprocessing_pressure_loss(network_type, self.network_name)
        self.q_data_rel_processed = self.preprocessing_rel_loss(network_type, self.network_name,
                                                                self.q_data_processed['hourly_loss'])
        self.p_data_rel_processed = self.preprocessing_rel_loss(network_type, self.network_name,
                                                                self.p_data_processed['hourly_loss'])
        self.T_data_processed = self.preprocessing_node_pressure(network_type, self.network_name)
        self.p_data_processed = self.preprocessing_node_temperature(network_type, self.network_name)
        self.network_processed = self.preprocessing_network_graph(network_type, self.network_name)
        self.plot_title_tail = self.preprocess_plot_title(network_type, self.network_name)
        self.plot_output_path_header = self.preprocess_plot_outputpath(network_type, self.network_name)


    def preprocess_network_name(self, network_name):
        if network_name == []:  # get network type, default is DH__
            return ""
        else:
            return str(network_name)

    def preprocess_plot_outputpath(self, network_type, network_name):
        if network_type == []:  # get network type, default is DH__
            return "DH_"+str(network_name)+"_"
        elif len(network_type) == 1:
            return str(network_type)+"_"+str(network_name)+"_"
        else: #should never happen / should not be possible
            return "DH_"+str(network_name)+"_"

    def preprocess_plot_title(self, network_type, network_name):
        if not network_name:
            if network_type == []:  # get network type, default is DH
                return " for DH"
            elif len(network_type) == 2:
                return " for " + str(network_type)
            else: #should never happen / should not be possible
                return ""
        else:
            if network_type == []:  # get network type, default is DH
                return " for DH in " + str(network_name)
            elif len(network_type) == 2:
                return " for " + str(network_type) + " in " + str(network_name)
            else: #should never happen / should not be possible
                return " in " + str(network_name)

    def preprocessing_heat_loss(self, network_type, network_name):
        df = pd.read_csv(self.locator.get_qloss(network_name, network_type))
        df1 = df.values.sum()
        return {"hourly_loss": pd.DataFrame(df), "yearly_loss": df1}

    def preprocessing_pressure_loss(self, network_type, network_name):
        df = pd.read_csv(self.locator.get_ploss(network_name, network_type))
        df = df['pressure_loss_total_kW']
        df1 = df.values.sum()
        return {"hourly_loss": pd.DataFrame(df), "yearly_loss": df1}

    def preprocessing_rel_loss(self, network_type, network_name, absolute_loss):
        df = pd.read_csv(self.locator.get_qplant(network_name, network_type)) #read plant heat supply
        rel = absolute_loss.values/df.values *100
        rel[rel==0] = np.nan
        mean_loss = np.nanmean(rel)
        rel = np.round(rel, 2)
        mean_loss = np.round(mean_loss, 2)
        return {"hourly_loss": pd.DataFrame(rel), "average_loss": mean_loss}

    def preprocessing_node_pressure(self, network_type, network_name):
        df_s = pd.read_csv(self.locator.get_pnode_s(network_name, network_type))
        df_r = pd.read_csv(self.locator.get_pnode_r(network_name, network_type))
        df_s[df_s == 0] = np.nan
        df_r[df_r == 0] = np.nan
        df1 = df_s.min()
        df2 = df_s.mean()
        df3 = df_s.max()
        df4 = df_r.min()
        df5 = df_r.mean()
        df6 = df_r.max()
        return {"minimum_sup": pd.DataFrame(df1), "average_sup": pd.DataFrame(df2),
                "maximum_sup": pd.DataFrame(df3), "minimum_ret": pd.DataFrame(df4),
                "average_ret": pd.DataFrame(df5), "maximum_ret": pd.DataFrame(df6)}

    def preprocessing_node_temperature(self, network_type, network_name):
        df_s = pd.read_csv(self.locator.get_Tnode_s(network_name, network_type))
        df_r = pd.read_csv(self.locator.get_Tnode_r(network_name, network_type))
        df_s[df_s == 0] = np.nan
        df_r[df_r == 0] = np.nan
        df1 = df_s.min()
        df2 = df_s.mean()
        df3 = df_s.max()
        df4 = df_r.min()
        df5 = df_r.mean()
        df6 = df_r.max()
        return {"minimum_sup": pd.DataFrame(df1), "average_sup": pd.DataFrame(df2),
                "maximum_sup": pd.DataFrame(df3), "minimum_ret": pd.DataFrame(df4),
                "average_ret": pd.DataFrame(df5), "maximum_ret": pd.DataFrame(df6)}

    def preprocessing_network_graph(self, network_type, network_name):
        # read in edge node matrix
        df = pd.read_csv(self.locator.get_optimization_network_edge_node_matrix_file(network_type, network_name),
                         index_col=0)
        # identify number of plants and nodes
        plant_nodes = []
        for node, node_index in zip(df.index, range(len(df.index))):
            if max(df.ix[node]) <= 0: #only -1 and 0 so plant!
                plant_nodes.append(node_index)
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

        # read in edge lengths
        edge_lengths = pd.read_csv(self.locator.get_optimization_network_edge_list_file(network_type, network_name),
                                   index_col=0)
        edge_lengths=edge_lengths['pipe length']
        # make a list of distances from plant, one row per plant, for all nodes
        plant_distance = np.zeros((len(plant_nodes), len(graph.nodes())))
        for plant_node, plant_index in zip(plant_nodes, range(len(plant_nodes))):
            for node in graph.nodes():
                plant_distance[plant_index, node] = nx.shortest_path_length(graph, plant_node, node, edge_lengths)
        return {"Distances": pd.DataFrame(plant_distance), "Network": graph}

    def loss_curve(self):
        title = "Heat and Pressure Losses" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_losses_curve')
        analysis_fields = ["Epump_loss_kWh", "Qnetwork_loss_kWh"]
        data = self.p_data_processed['hourly_loss'].join(self.q_data_processed['hourly_loss'])
        data.columns=analysis_fields
        plot = loss_curve(data, analysis_fields, title, output_path)
        return plot

    def loss_curve_relative(self):
        title = "Relative Heat and Pressure Losses" + self.plot_title_tail
        output_path = self.locator.get_timeseries_plots_file(self.plot_output_path_header + '_relative_losses_curve')
        analysis_fields = ["Epump_loss_%", "Qnetwork_loss_%"]
        df = self.p_data_rel_processed['hourly_loss']
        df = df.rename(columns={0:1})
        data = df.join(self.q_data_rel_processed['hourly_loss'])
        data.columns=analysis_fields
        plot = loss_curve(data, analysis_fields, title, output_path)
        return plot

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    plots_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
