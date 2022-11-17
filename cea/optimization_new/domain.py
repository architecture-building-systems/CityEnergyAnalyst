"""
Domain Class:
defines the geographical zone in which the district energy system is optimised, including parameters like:
- The buildings within the zone (building class element)
- The potential thermal network trenches graph
- The (renewable) energy potential within the zone (based on energy potentials scripts)
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

from os.path import exists
import time
import numpy as np
import pandas as pd
import networkx as nx
import geopandas as gpd

import cea.config
from cea.inputlocator import InputLocator
from cea.optimization_new.energyPotential import EnergyPotential
from cea.optimization_new.building import Building
from cea.optimization_new.network import Network
from cea.optimization_new.energyCarrier import EnergyCarrier
from cea.technologies.supply_systems_database import SupplySystemsDatabase
from cea.technologies.network_layout.connectivity_potential import calc_connectivity_network
from cea.constants import SHAPEFILE_TOLERANCE


class Domain(object):
    def __init__(self, config, locator):
        self.config = config
        self.locator = locator
        self.geography = 'xxx'
        self.buildings = []
        self.potential_network_graph = nx.Graph()
        self.energy_potentials = []
        self.available_energy_carriers = None
        EnergyCarrier._load_energy_carriers(self.locator)

    def load_supply_system_database(self):
        supply_systems = SupplySystemsDatabase(self.locator)

        self.available_energy_carriers = supply_systems.ENERGY_CARRIERS['ENERGY_CARRIERS']

    def load_buildings(self, buildings_in_domain=None):
        """
        Import demand and geometric properties of buildings from the current scenario.

        :param buildings_in_domain: Codes of buildings that should be loaded (e.g. 'B1000', 'B1008' etc.)
        :type buildings_in_domain: pandas.Series or list of strings
        :return self.buildings: list of buildings with their demands and footprints
        :rtype self.buildings: list of <cea.optimization_new.building>-Building objects
        """
        shp_file = gpd.read_file(self.locator.get_zone_geometry())
        if buildings_in_domain is None:
            buildings_in_domain = shp_file.Name

        building_demand_files = np.vectorize(self.locator.get_demand_results_file)(buildings_in_domain)
        for (building_code, demand_file) in zip(buildings_in_domain.values, building_demand_files):
            if exists(demand_file):
                building = Building(building_code, demand_file)
                building.load_demand_profile('DC')
                building.load_building_location(shp_file)
                self.buildings.append(building)

        return self.buildings

    def load_potentials(self, buildings_in_domain=None):
        """
        Import energy potentials from the current scenario.

        :param buildings_in_domain: Codes of buildings that should be loaded (e.g. 'B1000', 'B1008' etc.)
        :type buildings_in_domain: pandas.Series or list of strings
        :return self.energy_potentials: list of energy potentials with the scale they apply to (building or domain)
        :rtype self.energy_potentials: list of <cea.optimization_new.energyPotential>-EnergyPotential objects
        """
        shp_file = gpd.read_file(self.locator.get_zone_geometry())
        if buildings_in_domain is None:
            buildings_in_domain = shp_file.Name

        # building-specific potentials
        pv_potential = EnergyPotential().load_PV_potential(self.locator, buildings_in_domain)
        pvt_potential = EnergyPotential().load_PVT_potential(self.locator, buildings_in_domain)
        scet_potential = EnergyPotential().load_SCET_potential(self.locator, buildings_in_domain)
        scfp_potential = EnergyPotential().load_SCFP_potential(self.locator, buildings_in_domain)

        # domain-wide potentials
        geothermal_potential = EnergyPotential().load_geothermal_potential(self.locator.get_geothermal_potential())
        water_body_potential = EnergyPotential().load_water_body_potential(self.locator.get_water_body_potential())
        sewage_potential = EnergyPotential().load_sewage_potential(self.locator.get_sewage_heat_potential())

        for potential in [pv_potential, pvt_potential, scet_potential, scfp_potential, geothermal_potential, water_body_potential, sewage_potential]:
            if potential:
                self.energy_potentials.append(potential)

        return self.energy_potentials

    def load_pot_network(self):
        """
        Create potential network graph based on streets network .shp-file and the location of the buildings in the
        domain.

        :return self.potential_network_graph: Graph of potential network paths including roads and links to buildings.
        :rtype self.potential_network_graph: <networkx.Graph>-object
        """
        if not self.buildings:
            return self.potential_network_graph

        # join building locations (shapely.POINTS) and the corresponding identifiers in a DataFrame
        building_identifiers = [building.identifier for building in self.buildings]
        building_locations = [building.location for building in self.buildings]
        buildings_df = pd.DataFrame(list(zip(building_locations, building_identifiers)), columns=['geometry', 'Name'])

        # create a potential network grid with orthogonal connections between buildings and their closest street
        network_grid_shp = calc_connectivity_network(self.locator.get_street_network(),
                                                     buildings_df,
                                                     optimisation_flag=True)

        # convert the GeoDataFrame network grid to a Graph
        for (line_string, length) in network_grid_shp.itertuples(index=False):
            line_start = line_string.coords[0]
            line_end = line_string.coords[-1]
            edge_start = (round(line_start[0], SHAPEFILE_TOLERANCE), round(line_start[1], SHAPEFILE_TOLERANCE))
            edge_end = (round(line_end[0], SHAPEFILE_TOLERANCE), round(line_end[1], SHAPEFILE_TOLERANCE))
            self.potential_network_graph.add_edge(edge_start, edge_end, weight=length)

        return self.potential_network_graph

    def optimize_domain(self):
        individual_network = Network(domain=self)

        # calculate status quo
        connected_buildings = self.config.network_layout.connected_buildings
        individual_network.run_steiner_tree_optimisation(connected_buildings)
        individual_network.calculate_operational_conditions()

        # calculate
        optimal_district_cooling_systems = 'xxx'
        return optimal_district_cooling_systems


def main(config):
    """
    run the whole optimization routine
    """
    locator = InputLocator(scenario=config.scenario)
    current_domain = Domain(config, locator)

    start_time = time.time()
    current_domain.load_buildings()
    end_time = time.time()
    print(f"Time elapsed for loading buildings in domain: {end_time - start_time} s")

    start_time = time.time()
    current_domain.load_potentials()
    end_time = time.time()
    print(f"Time elapsed for loading energy potentials: {end_time - start_time} s")

    start_time = time.time()
    current_domain.load_pot_network()
    end_time = time.time()
    print(f"Time elapsed for loading the potential network of the domain: {end_time - start_time} s")

    start_time = time.time()
    current_domain.optimize_domain()
    end_time = time.time()
    print(f"Time elapsed to create and calculate individual network: {end_time - start_time} s")


if __name__ == '__main__':
    main(cea.config.Configuration())
