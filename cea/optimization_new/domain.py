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

from os.path import exists, join
import time
import numpy as np
import pandas as pd
import geopandas as gpd

from deap import base, creator, tools, algorithms
import openpyxl

import cea.config
from cea.inputlocator import InputLocator
from cea.utilities import epwreader

from cea.optimization_new.building import Building
from cea.optimization_new.network import Network
from cea.optimization_new.component import Component
from cea.optimization_new.supplySystem import SupplySystem
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
        self.optimal_energy_systems = []

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

        toolbox = base.Toolbox()
        toolbox.register("generate", ConnectivityVector.generate)
        toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        toolbox.register("evaluate", DistrictEnergySystem.evaluate_energy_system, district_buildings=self.buildings,
                         energy_potentials=self.energy_potentials)
        toolbox.register("mate", ConnectivityVector.mate, algorithm=algorithm)
        toolbox.register("mutate", ConnectivityVector.mutate, algorithm=algorithm)
        toolbox.register("select", ConnectivityVector.select, population_size=2)  # population_size=algorithm.population

        population = toolbox.population(n=2)  # n=algorithm.population
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

        self.optimal_energy_systems = self._select_final_optimal_systems(population, algorithm.population)
        print(f"District energy system optimisation complete!")

        return self.optimal_energy_systems

    def _select_final_optimal_systems(self, last_population, min_final_selection_size):
        """
        Each solution in the last population of the 'outer' optimisation algorithm consists of:
            a. one set networks & disconnected buildings (given by the ConnectivityVector)
            b. a non-dominate front of SupplySystem-solutions for each of these subsystems
        The point of this method is to determine the best district energy systems configurations among these,
        i.e. with, both, explicit network-connections and a single specified supply system for each of the DES's
        subsystems.
        """
        # build DistrictEnergySystem-objects corresponding to the last population of Connectivity vectors and evaluate
        #   them, i.e. find optimal combinations of each of the subsystems' non-dominated SupplySystem solutions.
        energy_systems_for_best_connectivity_vectors = [DistrictEnergySystem(ind, self.buildings, self.energy_potentials)
                                                        for ind in last_population]
        [energy_system.evaluate(return_full_des=True) for energy_system in energy_systems_for_best_connectivity_vectors]

        # determine the non-dominated solutions across all DistrictEnergySystems of the last population
        #   (with definitive SupplySystem + Connectivity)
        last_gen_energy_system_solutions = [energy_system
                                            for des in energy_systems_for_best_connectivity_vectors
                                            for energy_system in des.best_supsys_combinations]
        best_energy_systems = tools.emo.sortLogNondominated(last_gen_energy_system_solutions,
                                                            min_final_selection_size,
                                                            first_front_only=True)

        # create a list of distinct DistrictEnergySystem-objects (unequivocally defining SupplySystems and Networks)
        final_system_selection = []
        for energy_system in best_energy_systems:
            connectivity = energy_system[0]
            supsys_selection = energy_system[1:]
            district_energy_system = [des for des in energy_systems_for_best_connectivity_vectors
                                      if connectivity == des.connectivity.as_str()][0]
            final_system_selection += [district_energy_system.select_supply_system_combination(supsys_selection)]

        return final_system_selection

    def generate_result_files(self):
        """
        Output all the optimisation results to a series of .geojson-files to display the optimal networks and a set
        of .xlsx-files to summarise the most important information about the near-pareto-optimal district energy systems
        and their corresponding supply systems.
        """
        # save the results for near-pareto-optimal district energy systems one-by-one
        system_type = self.config.optimization_new.network_type
        for des_ind, district_energy_system in enumerate(self.optimal_energy_systems):
            # first save network layouts
            for ntw_ind, network in enumerate(district_energy_system.networks):
                network_layout_file = self.locator.get_new_optimization_optimal_network_layout_file(system_type,
                                                                                                    des_ind + 1,
                                                                                                    network.identifier)
                network_layout = pd.concat([network.network_nodes, network.network_edges]).drop(['coordinates'], axis=1)
                network_layout.to_file(network_layout_file, driver='GeoJSON')

            # then save all information about the selected supply systems
            supsys_results_file = self.locator.get_new_optimization_optimal_supply_systems_file(system_type,
                                                                                                des_ind + 1)
            Domain.write_supsys_to_xlsx(supsys_results_file, district_energy_system.supply_systems)

        return

    @staticmethod
    def write_supsys_to_xlsx(filename, supply_systems):
        """
        Writes information on supply systems of subsystems of a near-pareto-optimal district energy system into
        and xlsx file. The supply systems of each of the subsystems are summarised in a different tab of the file.

        """
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        workbook = writer.book

        for supsys_id, supply_system in supply_systems.items():
            row = 0
            worksheet = workbook.add_worksheet(str(supsys_id))

            # Write the header for the section summarising objective functions
            header_format = workbook.add_format({'bold': True, 'font_size': 14})
            worksheet.write(row, 0, 'Objective function evaluation', header_format)
            row += 1

            # Summarise objective function evaluation
            total_cost = sum(supply_system.annual_cost.values())
            total_ghg_emission = sum(supply_system.greenhouse_gas_emissions.values())
            total_sed = sum(supply_system.system_energy_demand.values())
            total_ah = sum(supply_system.heat_rejection.values())


            worksheet.write_row(row, 0, ['Cost', 'GHG Emissions', 'System Energy Demand', 'Anthropogenic Heat'])
            worksheet.write_row(row + 1, 0, [total_cost, total_ghg_emission, total_sed, total_ah])

            # Insert a blank row between sections
            row += 3

            # Summarise components installed in the supply system
            worksheet.write(row, 0, 'Component capacities', header_format)
            row += 1

            for category, components in supply_system.installed_components.items():
                # Summarise the supply system one category at a time
                worksheet.write(row, 0, str(category), header_format)
                row += 1

                # Write down supply system component capacities
                component_codes = [str(component_code) for component_code in components.keys()]
                component_capacities = [component.capacity for code, component in components.items()]
                worksheet.write_row(row, 0, component_codes)
                worksheet.write_row(row + 1, 0, component_capacities)

                # Insert a blank row between sections
                row += 3

        writer.save()

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

    start_time = time.time()
    current_domain.generate_result_files()
    end_time = time.time()
    print(f"Time elapsed create results-files: {end_time - start_time} s")


if __name__ == '__main__':
    main(cea.config.Configuration())
