"""
Show a Pareto curve plot for individuals in a given generation.
"""

import os

import pandas as pd
import geopandas
import json

import cea.config
import cea.inputlocator
import cea.plots.supply_system
from cea.plots.variable_naming import get_color_array
from cea.technologies.network_layout.main import layout_network, NetworkLayout
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

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
        'system': 'plots-supply-system:system',
        'scenario-name': 'general:scenario-name',
    }

    def __init__(self, project, parameters, cache):
        super(SupplySystemMapPlot, self).__init__(project, parameters, cache)
        self.scenario = self.parameters['scenario-name']
        self.config = cea.config.Configuration()
        self.input_files = [
            (self.locator.get_street_network, []),
            (self.locator.get_optimization_slave_building_connectivity, [self.individual, self.generation])
        ] if self.individual != 'today' else [
            (self.locator.get_street_network, []),
            (self.locator.get_building_supply, [])
        ]

    @property
    def title(self):
        if self.generation is not None:
            return "Supply system map for #{system}".format(system=self.system)
        return "Supply system map for original system"

    @property
    def output_path(self):
        return self.locator.get_timeseries_plots_file(
            '{system}_supply_system_map'.format(system=self.system), self.category_name)

    def _plot_div_producer(self):
        """
        Since this plot doesn't use plotly to plot, we override _plot_div_producer to return a string containing
        the html div to use for this plot. The template ``map_div.html`` expects some parameters:

        Here is some example data (in a YAML-like format for documentation purposes)

        ::

            data:
              DH:
                connected_buildings: ['B1010', 'B1017', 'B1003']
                disconnected_buildings: ['B1000', 'B1009', 'B1016', ..., 'B1015']
                path_output_nodes: "{general:scenario}/inputs/networks/DH/gen_3_ind_1/nodes.shp"
                path_output_edges: "{general:scenario}/inputs/networks/DH/gen_3_ind_1/edges.shp"
              DC: {}  # data does not necessarily contain information for both types of district networks
            colors:
              dc: [63, 192, 194]
              dh: [240, 75, 91]
              disconnected: [68, 76, 83]
              district: [255, 255, 255]
            zone: str serialization of the GeoJSON of the zone.shp
            district: str serialization of the GeoJSON of the district.shp
            dc: str serialization of a GeoJSON containing both the nodes.shp + edges.shp of district cooling network
            dh: str serialization of a GeoJSON containing both the nodes.shp + edges.shp of district heating network

        :return: a str containing a full html ``<div/>`` that includes the js code to display the map.
        """
        import os
        import hashlib
        from jinja2 import Template
        template = os.path.join(os.path.dirname(__file__), "map_div.html")

        data = self.data_processing()

        zone = geopandas.GeoDataFrame.from_file(self.locator.get_zone_geometry()).to_crs(
            get_geographic_coordinate_system()).to_json(show_bbox=True)
        district = geopandas.GeoDataFrame.from_file(self.locator.get_surroundings_geometry()).to_crs(
            get_geographic_coordinate_system()).to_json(show_bbox=True)
        dc = self.get_network_json(data['DC']['path_output_edges'], data['DC']['path_output_nodes'])
        dh = self.get_network_json(data['DH']['path_output_edges'], data['DH']['path_output_nodes'])

        # Generate div id using hash of parameters
        with open(template, "r") as fp:
            div = Template(fp.read()).render(hash=hashlib.md5(repr(sorted(data.items())).encode("utf-8")).hexdigest(),
                                             data=json.dumps(data), colors=json.dumps(COLORS),
                                             zone=zone,
                                             district=district, dc=dc, dh=dh)
        return div

    def get_network_json(self, edges, nodes):
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

        if self.individual != 'today':
            # get data from generation
            building_connectivity = pd.read_csv(self.locator.get_optimization_slave_building_connectivity
                                                (self.individual, self.generation))
            network_name = "gen_" + str(self.generation) + "_ind_" + str(self.individual)
        else:
            building_connectivity = get_building_connectivity(self.locator)
            network_name = "today"

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
        # Make sure that project path is correct
        self.config.project = self.project

        # Set config to scenario of plot
        self.config.scenario_name = self.scenario

        # Modify config inputs for this function
        self.config.network_layout.network_type = network_type
        self.config.network_layout.connected_buildings = connected_buildings

        # Ignore demand and creating plants for layouts in map
        self.config.network_layout.consider_only_buildings_with_demand = False
        self.config.network_layout.create_plant = False

        if network_name != 'today' or network_name == 'today' and newer_network_layout_exists(self.locator,
                                                                                              network_type,
                                                                                              network_name):
            network_layout = NetworkLayout(network_layout=self.config.network_layout)
            layout_network(network_layout, self.locator, output_name_network=network_name)

        # Output paths
        path_output_edges = self.locator.get_network_layout_edges_shapefile(network_type, network_name)
        path_output_nodes = self.locator.get_network_layout_nodes_shapefile(network_type, network_name)

        return path_output_edges, path_output_nodes


def get_building_connectivity(locator):
    supply_systems = pd.read_csv(locator.get_building_supply())
    data_all_in_one_systems = pd.read_excel(locator.get_database_supply_assemblies(), sheet_name=None)
    heating_infrastructure = data_all_in_one_systems['HEATING']
    heating_infrastructure = heating_infrastructure.set_index('code')['scale']

    cooling_infrastructure = data_all_in_one_systems['COOLING']
    cooling_infrastructure = cooling_infrastructure.set_index('code')['scale']

    building_connectivity = supply_systems[['Name']].copy()
    building_connectivity['DH_connectivity'] = (
            supply_systems['type_hs'].map(heating_infrastructure) == 'DISTRICT').astype(int)
    building_connectivity['DC_connectivity'] = (
            supply_systems['type_cs'].map(cooling_infrastructure) == 'DISTRICT').astype(int)
    return building_connectivity


def newer_network_layout_exists(locator, network_type, network_name):
    edges = locator.get_network_layout_edges_shapefile(
        network_type, network_name)
    nodes = locator.get_network_layout_nodes_shapefile(
        network_type, network_name)

    no_network_file = not os.path.isfile(edges) or not os.path.isfile(nodes)

    if no_network_file:
        return True

    network_layout_modified = max(os.path.getmtime(edges), os.path.getmtime(nodes))

    def newer_demand_exists():
        # Only True if demand file exists and is newer than the network layout
        demand = locator.get_total_demand()
        return os.path.isfile(demand) and os.path.getmtime(demand) > network_layout_modified

    def newer_supply_system_configuration():
        # Only True if is newer than the network layout
        supply_system = locator.get_building_supply()
        supply_system_modified = os.path.getmtime(supply_system)

        return supply_system_modified > network_layout_modified

    return newer_supply_system_configuration() or newer_demand_exists()


def main():
    """Test this plot"""
    import cea.config
    import cea.plots.cache
    config = cea.config.Configuration()
    cache = cea.plots.cache.NullPlotCache()
    SupplySystemMapPlot(config.project,
                        {'scenario-name': config.scenario_name,
                         'system': config.plots_supply_system.system},
                        cache).plot(auto_open=True)


if __name__ == '__main__':
    main()
