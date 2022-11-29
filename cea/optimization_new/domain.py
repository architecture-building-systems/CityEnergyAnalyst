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
import random
import numpy as np
import pandas as pd
import geopandas as gpd

import cea.config
from cea.inputlocator import InputLocator
from cea.optimization_new.energyPotential import EnergyPotential
from cea.optimization_new.building import Building
from cea.optimization_new.network import Network
from cea.optimization_new.energyCarrier import EnergyCarrier
from cea.optimization_new.energyFlow import EnergyFlow
from cea.optimization_new.supplySystem import SupplySystem
from cea.optimization_new.component import Component
from cea.optimization_new.districtEnergySystem import DistrictEnergySystem
from cea.technologies.supply_systems_database import SupplySystemsDatabase


class Domain(object):
    def __init__(self, config, locator):
        self.config = config
        self.locator = locator
        self.geography = 'xxx'
        self.buildings = []
        self.energy_potentials = []
        self.available_energy_carriers = None

        self._initialise_domain_descriptor_classes()

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

    def optimize_domain(self):
        """
        Build district energy system and...
        TODO: determine for which combinations of connectivity vectors and capacity indicator matrices the best performance is achieved.
        """
        self._initialize_energy_system_descriptor_classes()

        max_nbr_networks = 2  # TODO: make this part of the config
        connectivity = np.array([random.randint(0, max_nbr_networks) for _ in range(len(self.buildings))])
        # impose constraints on connectivity vector
        zeros_profile = pd.Series(0.0, index=np.arange(EnergyFlow.time_frame))
        no_load_buildings = np.array([all(building.demand_flow.profile == zeros_profile) for building in self.buildings])
        connectivity[no_load_buildings] = 0

        new_district_cooling_system = DistrictEnergySystem(connectivity)
        new_district_cooling_system.generate_networks()
        new_district_cooling_system.aggregate_demand(self.buildings)
        new_district_cooling_system.distribute_potentials()
        new_district_cooling_system.generate_supply_systems()

        # calculate
        optimal_district_cooling_systems = 'xxx'
        return optimal_district_cooling_systems

    def _initialise_domain_descriptor_classes(self):
        EnergyCarrier.initialize_class_variables(self)

    def _initialize_energy_system_descriptor_classes(self):
        Component.initialize_class_variables(self)
        Network.initialize_class_variables(self)
        DistrictEnergySystem.initialize_class_variables(self)
        SupplySystem.initialize_class_variables(self)


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
    current_domain.optimize_domain()
    end_time = time.time()
    print(f"Time elapsed to create and calculate individual network: {end_time - start_time} s")


if __name__ == '__main__':
    main(cea.config.Configuration())
