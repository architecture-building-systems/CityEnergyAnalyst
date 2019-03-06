import cea.globalvar
import cea.inputlocator
from cea.technologies.thermal_network.network_layout.connectivity_potential import calc_connectivity_network
from cea.technologies.thermal_network.network_layout.substations_location import calc_substation_location
from cea.technologies.thermal_network.network_layout.steiner_spanning_tree import calc_steiner_spanning_tree
import cea.config
import os

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def get_default_arcgis_db(self):
    """Returns the ArcGIS Default.gdb path to use."""
    from cea.interfaces.arcgis.modules import arcpy
    if not arcpy.env.workspace:
        out_folder_path, out_name = os.path.split(tempfile.mktemp(suffix='.gdb'))
        arcpy.CreateFileGDB_management(out_folder_path, out_name)
        arcpy.env.workspace = os.path.join(out_folder_path, out_name)
    return arcpy.env.workspace


def network_layout(config, locator, plant_building_names, output_name_network="", optimization_flag=False):
    # Local variables
    weight_field = 'Shape_Leng'
    type_mat_default = config.network_layout.type_mat
    pipe_diameter_default = config.network_layout.pipe_diameter
    type_network = config.network_layout.network_type
    create_plant = config.network_layout.create_plant
    input_buildings_shp = locator.get_zone_geometry()
    connected_buildings = config.network_layout.buildings
    output_substations_shp = locator.get_temporary_file("nodes_buildings.shp")
    path_streets_shp = locator.get_street_network()  # shapefile with the stations
    path_potential_network = locator.get_temporary_file("potential_network.shp") # shapefile, location of output.
    total_demand_location = locator.get_total_demand()

    path_default_arcgis_db = locator.get_default_arcgis_db()
    print('Path to ArcGIS workspace: %s' % path_default_arcgis_db)

    # Calculate points where the substations will be located
    calc_substation_location(input_buildings_shp, output_substations_shp, connected_buildings)

    # Calculate potential network
    calc_connectivity_network(path_default_arcgis_db, path_streets_shp, output_substations_shp,
                              path_potential_network)

    # calc minimum spanning tree and save results to disk
    output_edges = locator.get_network_layout_edges_shapefile(type_network, output_name_network)
    output_nodes = locator.get_network_layout_nodes_shapefile(type_network, output_name_network)
    output_network_folder = locator.get_input_network_folder(type_network, output_name_network)
    # calc_minimum_spanning_tree(path_potential_network, output_network_folder, output_substations_shp, output_edges,
    #                            output_nodes, weight_field, type_mat_default, pipe_diameter_default)
    disconnected_building_names = config.thermal_network.disconnected_buildings
    calc_steiner_spanning_tree(path_potential_network, output_network_folder, output_substations_shp, output_edges,
                               output_nodes, weight_field, type_mat_default, pipe_diameter_default, type_network,
                               total_demand_location, create_plant, config.network_layout.allow_looped_networks,
                               optimization_flag, plant_building_names, disconnected_building_names)


def main(config):
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(scenario=config.scenario)
    plant_building_names = []  # Placeholder, this is only used in Network optimization
    network_layout(config, locator, plant_building_names)


if __name__ == '__main__':
    main(cea.config.Configuration())
