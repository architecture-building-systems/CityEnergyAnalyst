"""
Show a Pareto curve plot for individuals in a given generation.
"""
from __future__ import division
from __future__ import print_function

import pandas as pd

import cea.inputlocator
import cea.plots.supply_system
from cea.technologies.network_layout.main import network_layout

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class SupplySystemMapPlot(cea.plots.supply_system.SupplySystemPlotBase):
    """Show a pareto curve for a single generation"""
    name = "Supply system map"

    expected_parameters = {
        'generation': 'plots-supply-system:generation',
        'individual': 'plots-supply-system:individual',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(SupplySystemMapPlot, self).__init__(project, parameters, cache)
        self.generation = self.parameters['generation']
        self.individual = self.parameters['individual']
        self.scenario = self.parameters['scenario-name']
        self.config = cea.config.Configuration()

    @property
    def title(self):
        return "Supply system map for system #%s" % (self.individual)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_ind{individual}supply_system_map'.format(individual=self.individual,
                                                                      generation=self.generation),
            self.category_name)

    def calc_graph(self):
        data = self.data_processing()

        ###
        ##
        ##
        # NOW, LET'S MAKE THE GRAPH!!.
        ###
        ###
        ##

        return

    def data_processing(self):
        # get data from generation
        building_connectivity = pd.read_csv(self.locator.get_optimization_slave_building_connectivity(self.generation,
                                                                                                      self.individual))

        # FOR DISTRICT HEATING NETWORK
        if building_connectivity[
            'DH_connectivity'].sum() > 1:  # there are buildings connected and hence we can create the network
            connected_buildings_DH = [x for x, y in zip(building_connectivity['Name'].values,
                                                        building_connectivity['DH_connectivity'].values) if y == 1]
            disconnected_buildings_DH = [x for x in building_connectivity['Name'].values if
                                         x not in connected_buildings_DH]
            network_type = "DH"
            network_name = "gen_" + str(self.generation) + "_ind_" + str(self.individual)
            path_output_edges_DH, path_output_nodes_DH = self.create_network_layout(connected_buildings_DH,
                                                                                    network_type, network_name)
        else:
            connected_buildings_DH = []
            disconnected_buildings_DH = building_connectivity['Name'].values
            path_output_edges_DH = None
            path_output_nodes_DH = None

        # FOR DISTRICT COOLING NETWORK
        if building_connectivity[
            'DC_connectivity'].sum() > 1:  # there are buildings connected and hence we can create the network
            connected_buildings_DC = [x for x in building_connectivity['Name'].values if
                                      building_connectivity.loc[building_connectivity['Name'] == x][
                                          'DC_connectivity'] == 1]
            disconnected_buildings_DC = [x for x in building_connectivity['Name'].values if
                                         x not in connected_buildings_DC]
            network_type = "DC"
            network_name = "gen_" + str(self.generation) + "_ind_" + str(self.individual)
            path_output_edges_DC, path_output_nodes_DC = self.create_network_layout(connected_buildings_DC,
                                                                                    network_type, network_name)
        else:
            connected_buildings_DC = []
            disconnected_buildings_DC = building_connectivity['Name'].values
            path_output_edges_DC = None
            path_output_nodes_DC = None

        data_processed = {
            'connected_buildings_DH': connected_buildings_DH,
            'disconnected_buildings_DH': disconnected_buildings_DH,
            'path_output_edges_DH': path_output_edges_DH,
            'path_output_nodes_DH': path_output_nodes_DH,
            'connected_buildings_DC': connected_buildings_DC,
            'disconnected_buildings_DC': disconnected_buildings_DC,
            'path_output_edges_DC': path_output_edges_DC,
            'path_output_nodes_DC': path_output_nodes_DC,
        }

        return data_processed

    def create_network_layout(self, connected_buildings, network_type, network_name):

        # Modify config inputs for this function
        self.config.network_layout.network_type = network_type
        self.config.network_layout.connected_buildings = connected_buildings
        network_layout(self.config, self.locator, output_name_network=network_name)

        # Output paths
        path_output_edges = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
        path_output_nodes = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)

        return path_output_edges, path_output_nodes


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    SupplySystemMapPlot(config.project,
                        {'scenario-name': config.scenario_name,
                         'generation': config.plots_supply_system.generation,
                         'individual': config.plots_supply_system.individual},
                        cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
