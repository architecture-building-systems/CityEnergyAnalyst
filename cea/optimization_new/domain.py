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
import geopandas as gpd

from deap import base, creator, tools, algorithms

import cea.config
from cea.inputlocator import InputLocator
from cea.utilities import epwreader

from cea.optimization_new.building import Building
from cea.optimization_new.network import Network
from cea.optimization_new.component import Component
from cea.optimization_new.supplySystem import SupplySystem
from cea.technologies.supply_systems_database import SupplySystemsDatabase
from cea.optimization_new.districtEnergySystem import DistrictEnergySystem
from cea.optimization_new.containerclasses.energysystems.supplySystemStructure import SupplySystemStructure
from cea.optimization_new.containerclasses.energysystems.energyPotential import EnergyPotential
from cea.optimization_new.containerclasses.energysystems.energyCarrier import EnergyCarrier
from cea.optimization_new.containerclasses.optimization.connectivityVector import Connection, ConnectivityVector
from cea.optimization_new.containerclasses.optimization.algorithm import Algorithm


class Domain(object):
    def __init__(self, config, locator):
        self.config = config
        self.locator = locator
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
        Optimise the chosen domain's energy system by:

        A. Using a first genetic algorithm to iteratively improve on the selected connectivity vectors (specifying which
           buildings are connected by thermal networks), and at each iteration:

            i. Use a steiner-tree-optimisation to identify optimal network layouts for given connectivity vectors.

            ii. Aggregate demands of the buildings connected to each network and use a second genetic algorithm to find
                supply system configurations that are near-pareto optimal for the respective networks.
        """
        self._initialize_energy_system_descriptor_classes()

        print(f"Starting optimisation of district energy systems (i.e. networks + supply systems).")

        algorithm = DistrictEnergySystem.optimisation_algorithm

        creator.create("FitnessMin", base.Fitness, weights=(-1.0,)*algorithm.nbr_objectives)
        creator.create("Individual", ConnectivityVector, fitness=creator.FitnessMin)
        ref_points = tools.uniform_reference_points(algorithm.nbr_objectives, 12)

        toolbox = base.Toolbox()
        toolbox.register("generate", ConnectivityVector.generate)
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        toolbox.register("evaluate", DistrictEnergySystem.evaluate_energy_system, district_buildings=self.buildings,
                         energy_potentials=self.energy_potentials)
        toolbox.register("mate", ConnectivityVector.mate, algorithm=algorithm)
        toolbox.register("mutate", ConnectivityVector.mutate, algorithm=algorithm)
        toolbox.register("select", ConnectivityVector.select, population_size=algorithm.population)

        population = toolbox.population(n=algorithm.population)
        non_dominated_fronts = toolbox.map(toolbox.evaluate, population)
        optimal_supply_system_combinations = {ind.as_str(): non_dominated_front for ind, non_dominated_front
                                              in zip(population, non_dominated_fronts)}

        for generation in range(1, algorithm.generations):
            offspring = algorithms.varAnd(population, toolbox, cxpb=algorithm.cx_prob, mutpb=algorithm.mut_prob)

            new_ind = [ind for ind in offspring if not (ind.as_str() in optimal_supply_system_combinations.keys())]
            non_dominated_fronts = toolbox.map(toolbox.evaluate, new_ind)
            optimal_supply_system_combinations.update({ind.as_str(): non_dominated_front for ind, non_dominated_front
                                                       in zip(new_ind, non_dominated_fronts)})

            population = toolbox.select(population + offspring, optimal_supply_system_combinations)
            print(f"DES: gen {generation}")

        optimal_district_energy_systems = [DistrictEnergySystem(ind, self.buildings, self.energy_potentials)
                                           for ind in population]
        [energy_system.evaluate() for energy_system in optimal_district_energy_systems]
        print(f"District energy system optimisation complete!")

        return optimal_district_energy_systems

    def _initialise_domain_descriptor_classes(self):
        EnergyCarrier.initialize_class_variables(self)
        Algorithm.initialize_class_variables(self)

    def _initialize_energy_system_descriptor_classes(self):
        Component.initialize_class_variables(self)
        Network.initialize_class_variables(self)
        DistrictEnergySystem.initialize_class_variables(self)
        SupplySystemStructure.initialize_class_variables(self)
        SupplySystem.initialize_class_variables(self)
        Connection.initialize_class_variables(self)


def main(config):
    """
    run the whole optimization routine
    """
    # initialise variables and define cooling demand
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
    print(f"Time elapsed to optimise domain, including networks and supply systems: {end_time - start_time} s")


if __name__ == '__main__':
    main(cea.config.Configuration())
