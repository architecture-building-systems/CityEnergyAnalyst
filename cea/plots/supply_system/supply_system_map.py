"""
Show a Pareto curve plot for individuals in a given generation.
"""
from __future__ import division
from __future__ import print_function

import pandas as pd
import geopandas
import json

import cea.inputlocator
import cea.plots.supply_system
from cea.plots.variable_naming import COLORS_TO_RGB
from cea.technologies.network_layout.main import network_layout
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def get_color(color):
    return [int(x) for x in COLORS_TO_RGB[color].split('(')[1].split(')')[0].split(',')]


# Colors for the networks in the map
COLORS = {
    'dh': get_color('red'),
    'dc': get_color('blue'),
    'disconnected': get_color('grey')
}


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
        self.input_files = [(self.locator.get_optimization_slave_building_connectivity, [self.individual, self.generation])]

    @property
    def title(self):
        return "Supply system map for system #%s" % (self.individual)

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            'gen{generation}_ind{individual}supply_system_map'.format(individual=self.individual,
                                                                      generation=self.generation),
            self.category_name)

    def _plot_div_producer(self):
        import os
        import hashlib
        from jinja2 import Template
        template = os.path.join(os.path.dirname(__file__), "map_div.html")

        data = self.data_processing()

        zone = geopandas.GeoDataFrame.from_file(self.locator.get_zone_geometry())\
            .to_crs(get_geographic_coordinate_system()).to_json(show_bbox=True)
        dc = self.get_newtork_json(data['path_output_edges_DC'], data['path_output_nodes_DC'])
        dh = self.get_newtork_json(data['path_output_edges_DH'], data['path_output_nodes_DH'])

        # Generate div id using hash of parameters
        div = Template(open(template).read())\
            .render(hash=hashlib.md5(repr(sorted(data.items()))).hexdigest(), data=json.dumps(data), colors=COLORS,
                    zone=zone, dc=dc, dh=dh)
        return div

    def get_newtork_json(self, edges, nodes):
        if not edges or not nodes:
            return {}
        edges_df = geopandas.GeoDataFrame.from_file(edges)
        nodes_df = geopandas.GeoDataFrame.from_file(nodes)
        network_json = json.loads(edges_df.to_crs(get_geographic_coordinate_system()).to_json())
        network_json['features']\
            .extend(json.loads(nodes_df.to_crs(get_geographic_coordinate_system()).to_json())['features'])
        return json.dumps(network_json)

    def data_processing(self):
        # get data from generation
        building_connectivity = pd.read_csv(self.locator.get_optimization_slave_building_connectivity(self.individual,
                                                                                                      self.generation))

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
            disconnected_buildings_DH = building_connectivity['Name'].values.tolist()
            path_output_edges_DH = None
            path_output_nodes_DH = None

        # FOR DISTRICT COOLING NETWORK
        if building_connectivity[
            'DC_connectivity'].sum() > 1:  # there are buildings connected and hence we can create the network
            connected_buildings_DC = [x for x, y in zip(building_connectivity['Name'].values,
                                                        building_connectivity['DC_connectivity'].values) if y == 1]
            disconnected_buildings_DC = [x for x in building_connectivity['Name'].values if
                                         x not in connected_buildings_DC]
            network_type = "DC"
            network_name = "gen_" + str(self.generation) + "_ind_" + str(self.individual)
            path_output_edges_DC, path_output_nodes_DC = self.create_network_layout(connected_buildings_DC,
                                                                                    network_type, network_name)
        else:
            connected_buildings_DC = []
            disconnected_buildings_DC = building_connectivity['Name'].values.tolist()
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
