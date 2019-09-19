"""
Show a Pareto curve plot for individuals in a given generation.
"""
from __future__ import division
from __future__ import print_function

import pandas as pd
import geopandas
import json

import cea.config
import cea.inputlocator
import cea.plots.supply_system
from cea.plots.variable_naming import get_color_array
from cea.technologies.network_layout.main import layout_network, NetworkLayout
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system
from cea.utilities.dbf import dbf_to_dataframe

__author__ = "Jimeno Fonseca"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# Colors for the networks in the map
COLORS = {
    'district': get_color_array('white'),
    'dh': get_color_array('red'),
    'dc': get_color_array('blue'),
    'disconnected': get_color_array('grey')
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
        self.individual = self.parameters['individual'] if self.generation is not None else 0
        self.scenario = self.parameters['scenario-name']
        self.config = cea.config.Configuration()
        self.input_files = [(self.locator.get_optimization_slave_building_connectivity,
                             [self.individual, self.generation])] if self.generation is not None else []

    @property
    def title(self):
        if self.generation is not None:
            return "Supply system map for system #{individual} of gen{generation}".format(individual=self.individual,
                                                                                          generation=self.generation)
        return "Supply system map for original system"

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

        zone = geopandas.GeoDataFrame.from_file(self.locator.get_zone_geometry()).to_crs(
            get_geographic_coordinate_system()).to_json(show_bbox=True)
        district = geopandas.GeoDataFrame.from_file(self.locator.get_district_geometry()).to_crs(
            get_geographic_coordinate_system()).to_json(show_bbox=True)
        dc = self.get_newtork_json(data['DC']['path_output_edges'], data['DC']['path_output_nodes'])
        dh = self.get_newtork_json(data['DH']['path_output_edges'], data['DH']['path_output_nodes'])

        # Generate div id using hash of parameters
        div = Template(open(template).read()).render(hash=hashlib.md5(repr(sorted(data.items()))).hexdigest(),
                                                     data=json.dumps(data), colors=COLORS,
                                                     zone=zone, district=district, dc=dc, dh=dh)
        return div

    def get_newtork_json(self, edges, nodes):
        if not edges or not nodes:
            return {}
        edges_df = geopandas.GeoDataFrame.from_file(edges)
        nodes_df = geopandas.GeoDataFrame.from_file(nodes)
        network_json = json.loads(edges_df.to_crs(get_geographic_coordinate_system()).to_json())
        network_json['features'].extend(
            json.loads(nodes_df.to_crs(get_geographic_coordinate_system()).to_json())['features'])
        return json.dumps(network_json)

    def data_processing(self):
        building_connectivity = None
        data_processed = {}

        if self.generation is not None:
            # get data from generation
            building_connectivity = pd.read_csv(self.locator.get_optimization_slave_building_connectivity
                                                (self.individual, self.generation))
            network_name = "gen_" + str(self.generation) + "_ind_" + str(self.individual)
        else:
            building_connectivity = self.get_building_connectivity(self.locator)
            network_name = "base"

        for network in ['DH', 'DC']:
            data_processed[network] = {}
            connectivity = building_connectivity['{}_connectivity'.format(network)]
            # there are buildings connected and hence we can create the network
            if connectivity.sum() > 1:
                data_processed[network]['connected_buildings'] = building_connectivity[connectivity == 1][
                    'Name'].values.tolist()
                data_processed[network]['disconnected_buildings'] = building_connectivity[connectivity == 0][
                    'Name'].values.tolist()
                data_processed[network]['path_output_edges'], data_processed[network][
                    'path_output_nodes'] = self.create_network_layout(data_processed[network]['connected_buildings'],
                                                                      network, network_name)
            else:
                data_processed[network]['connected_buildings'] = []
                data_processed[network]['disconnected_buildings'] = building_connectivity['Name'].values.tolist()
                data_processed[network]['path_output_edges'] = None
                data_processed[network]['path_output_nodes'] = None

        return data_processed

    def create_network_layout(self, connected_buildings, network_type, network_name):

        # Modify config inputs for this function
        self.config.network_layout.network_type = network_type
        self.config.network_layout.connected_buildings = connected_buildings
        network_layout = NetworkLayout(network_layout=self.config.network_layout)
        layout_network(network_layout, self.locator, output_name_network=network_name)

        # Output paths
        path_output_edges = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
        path_output_nodes = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)

        return path_output_edges, path_output_nodes


def get_building_connectivity(locator):
    supply_systems = dbf_to_dataframe(locator.get_building_supply())
    heating_infrastructure = pd.read_excel(locator.get_life_cycle_inventory_supply_systems(),
                                           sheet_name='HEATING').set_index('code')['scale_hs']
    cooling_infrastructure = pd.read_excel(locator.get_life_cycle_inventory_supply_systems(),
                                           sheet_name='COOLING').set_index('code')['scale_cs']
    building_connectivity = supply_systems[['Name']].copy()
    building_connectivity['DH_connectivity'] = (
            supply_systems['type_hs'].map(heating_infrastructure) == 'DISTRICT').astype(int)
    building_connectivity['DC_connectivity'] = (
            supply_systems['type_cs'].map(cooling_infrastructure) == 'DISTRICT').astype(int)
    return building_connectivity


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
