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
import geopandas as gpd
import numpy as np
import time

import pandas as pd

import cea.config
from cea.inputlocator import InputLocator
from cea.optimization_new.energyPotential import EnergyPotential
from cea.optimization_new.building import Building
from cea.technologies.supply_systems_database import SupplySystemsDatabase


class Domain(object):
    def __init__(self, config, locator):
        self.config = config
        self.locator = locator
        self._available_energy_carriers = None
        self.geography = 'xxx'
        self.buildings = []
        self.network_grid = 'xxx'
        self.energy_potentials = None

    @property
    def available_energy_carriers(self):

        return self._available_energy_carriers

    @available_energy_carriers.setter
    def available_energy_carriers(self, new_energy_carriers):
        if not isinstance(new_energy_carriers, pd.DataFrame):
            raise TypeError("The available energy carriers database does not seem to be provided in the correct format.")
        if any(new_energy_carriers.columns != ['description', 'code', 'type', 'qualifier', 'unit_qual', 'mean_qual',
                                               'unit_cost_USD.kWh', 'unit_ghg_kgCO2.kWh', 'reference']):
            raise AttributeError("The attributes of the energy carriers database does not seem to correspond to the "
                                 "required list: \n'description', 'code', 'type', 'qualifier', 'unit_qual', "
                                 "'mean_qual', 'unit_cost_USD.kWh', 'unit_ghg_kgCO2.kWh', 'reference'")
        if not all(i in ['thermal', 'electrical', 'combustible', 'radiation'] for i in new_energy_carriers.type):
            raise ValueError("The energy carrier data base contains an invalid energy type. Valid energy carrier "
                             "types are: \n 'thermal', 'electrical', 'combustible', 'radiation'")
        self._available_energy_carriers = new_energy_carriers

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
        start_time = time.time()
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

        end_time = time.time()
        print(f"Time elapsed for loading buildings in domain: {end_time - start_time} s")
        return self.buildings

    def load_potentials(self, buildings_in_domain=None):
        """
        Import energy potentials from the current scenario.

        :param buildings_in_domain: Codes of buildings that should be loaded (e.g. 'B1000', 'B1008' etc.)
        :type buildings_in_domain: pandas.Series or list of strings
        :return self.energy_potentials: list of energy potentials with the scale they apply to (building or domain)
        :rtype self.energy_potentials: list of <cea.optimization_new.energyPotential>-EnergyPotential objects
        """
        start_time = time.time()
        shp_file = gpd.read_file(self.locator.get_zone_geometry())
        if buildings_in_domain is None:
            buildings_in_domain = shp_file.Name
        if self.available_energy_carriers is None:
            self.load_supply_system_database()
        thermal_ec = self.available_energy_carriers[self.available_energy_carriers.type == 'thermal']

        # building-specific potentials
        pv_potential = EnergyPotential().load_PV_potential(self.locator, buildings_in_domain)
        pvt_potential = EnergyPotential().load_PVT_potential(self.locator, buildings_in_domain, thermal_ec)
        scet_potential = EnergyPotential().load_SCET_potential(self.locator, buildings_in_domain, thermal_ec)
        scfp_potential = EnergyPotential().load_SCFP_potential(self.locator, buildings_in_domain, thermal_ec)

        # domain-wide potentials
        geothermal_potential = EnergyPotential().load_geothermal_potential(self.locator.get_geothermal_potential(), thermal_ec)
        water_body_potential = EnergyPotential().load_water_body_potential(self.locator.get_water_body_potential(), thermal_ec)
        sewage_potential = EnergyPotential().load_sewage_potential(self.locator.get_sewage_heat_potential(), thermal_ec)

        end_time = time.time()
        print(f"Time elapsed for loading energy potentials: {end_time - start_time} s")

        self.energy_potentials = [pv_potential, pvt_potential, scet_potential, scfp_potential, geothermal_potential, water_body_potential, sewage_potential]
        return self.energy_potentials

    def load_pot_network(self):

        return self.network_grid

    def optimize_domain(self):
        optimal_district_cooling_systems = 'xxx'

        return optimal_district_cooling_systems


def main(config):
    """
    run the whole optimization routine
    """
    locator = InputLocator(scenario=config.scenario)
    current_domain = Domain(config, locator)
    # current_domain.load_supply_system_database()
    # current_domain.load_buildings()
    current_domain.load_potentials()
    current_domain.optimize_domain()

    print(locator.PV_results('B1000'))


if __name__ == '__main__':
    main(cea.config.Configuration())