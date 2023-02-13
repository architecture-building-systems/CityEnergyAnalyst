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
from cea.utilities import epwreader
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
        self.weather = self._load_weather(locator)
        self.buildings = []
        self.energy_potentials = []
        self.available_energy_carriers = None

        self._initialise_domain_descriptor_classes()

    def _load_weather(self, locator):
        weather_path = locator.get_weather_file()
        self.weather = epwreader.epw_reader(weather_path)[['year', 'drybulb_C', 'wetbulb_C',
                                                           'relhum_percent', 'windspd_ms', 'skytemp_C']]
        return self.weather

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

        connectivity = np.array([random.randint(0, DistrictEnergySystem.max_nbr_networks) for _ in range(len(self.buildings))])
        # impose constraints on connectivity vector
        zeros_profile = pd.Series(0.0, index=np.arange(EnergyFlow.time_frame))
        no_load_buildings = np.array([all(building.demand_flow.profile == zeros_profile) for building in self.buildings])
        connectivity[no_load_buildings] = 0

        new_district_cooling_system = DistrictEnergySystem(connectivity)
        new_district_cooling_system.generate_networks()
        new_district_cooling_system.aggregate_demand(self.buildings)
        new_district_cooling_system.distribute_potentials(self.energy_potentials)
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
    # initialise variables and define cooling demand
    locator = InputLocator(scenario=config.scenario)
    current_domain = Domain(config, locator)
    # Component.initialize_class_variables(current_domain)

    # cooling_demand_DC = pd.Series([120000 + 50000 * np.sin((i % 6)*2*np.pi/6) for i in range(8760)])
    # cooling_demand_building = pd.Series([3000 + 2000 * np.sin((i % 24)*2*np.pi/24) for i in range(8760)])
    # heating_demand_building = pd.Series([2000 + 1500 * np.sin((i % 12)*2*np.pi/24) for i in range(8760)])
    # cooling_demand_DC = EnergyFlow('primary', 'consumer', 'T10W', cooling_demand_DC)
    # cooling_demand_building = EnergyFlow('primary', 'consumer', 'T25A', cooling_demand_building)
    # heating_demand_building = EnergyFlow('primary', 'consumer', 'T25A', heating_demand_building)

    # build and operate primary energy system components (cooling components)
    # ach = AbsorptionChiller('ACH1', 'primary', 200000)
    # vcc = VapourCompressionChiller('CH2', 'primary', 200000)
    # ac = AirConditioner('AC1', 'primary', 10000)
    # hp = HeatPump('HP2', 'primary', 10000)

    # input_energy_dict_vcc, output_energy_dict_vcc = vcc.operate(cooling_demand_DC)
    # input_energy_dict_ach, output_energy_dict_ach = ach.operate(cooling_demand_DC)
    # input_energy_dict_ac, output_energy_dict_ac = ac.operate(cooling_demand_building)
    # input_energy_dict_hp, output_energy_dict_hp = hp.operate(heating_demand_building)

    # build and operate secondary energy system components (supply components)
    # heating_load = input_energy_dict_ach['T100W']

    # cp = CogenPlant('OEHR2', 'secondary', 400000)
    # blr = Boiler('BO1', 'secondary', 400000)

    # input_energy_dict_cp, output_energy_dict_cp = cp.operate(heating_load)
    # input_energy_dict_blr, output_energy_dict_blr = blr.operate(heating_load)

    # build and operate tertiary energy system components (heat rejection components)
    # heat_rejection_load = output_energy_dict_vcc['T30W']

    # ct = CoolingTower('CT1', 'tertiary', 250000)
    # he = HeatExchanger('HEX2', 'tertiary', 250000)

    # input_energy_dict_ct, output_energy_dict_ct = ct.operate(heat_rejection_load)
    # input_energy_dict_he, output_energy_dict_he = he.operate(heat_rejection_load, heat_sink_temp=14)

    # elec_in = input_energy_dict_vcc['E230AC']
    # elec_in_ach = input_energy_dict_ach['E230AC']
    # elec_in_ac = input_energy_dict_ac['E230AC']
    # print(elec_in.profile.values)
    # print(elec_in_ach.profile.values)
    # print(elec_in_ac.profile.values)

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
