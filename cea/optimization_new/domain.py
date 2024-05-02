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
import geopandas as gpd
import multiprocessing
import sys
import inspect
from random import seed

from deap import base, tools, algorithms

import cea.config
from cea.inputlocator import InputLocator
from cea.utilities import epwreader
from cea.utilities.date import get_date_range_hours_from_year
from cea.utilities.standardize_coordinates import get_geographic_coordinate_system

import cea.optimization_new.component as component_module
from cea.optimization_new.building import Building
from cea.optimization_new.network import Network
from cea.optimization_new.component import Component
from cea.optimization_new.supplySystem import SupplySystem
from cea.optimization_new.districtEnergySystem import DistrictEnergySystem
from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure
from cea.optimization_new.containerclasses.energyPotential import EnergyPotential
from cea.optimization_new.containerclasses.energyCarrier import EnergyCarrier
from cea.optimization_new.helpercalsses.optimization.connectivity import Connection, ConnectivityVector
from cea.optimization_new.helpercalsses.optimization.algorithm import Algorithm
from cea.optimization_new.helpercalsses.optimization.tracker import optimizationTracker
from cea.optimization_new.helpercalsses.optimization.fitness import Fitness
from cea.optimization_new.helpercalsses.multiprocessing.memoryPreserver import MemoryPreserver


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
        Import demand, geometric properties and base supply systems of buildings from the current scenario.

        :param buildings_in_domain: Codes of buildings that should be loaded (e.g. 'B1000', 'B1008' etc.)
        :type buildings_in_domain: pandas.Series or list of strings
        :return self.buildings: list of buildings with their demands and footprints
        :rtype self.buildings: list of <cea.optimization_new.building>-Building objects
        """
        shp_file = gpd.read_file(self.locator.get_zone_geometry())
        if buildings_in_domain is None:
            buildings_in_domain = shp_file.Name

        building_demand_files = np.vectorize(self.locator.get_demand_results_file)(buildings_in_domain)
        network_type = self.config.optimization_new.network_type
        for (building_code, demand_file) in zip(buildings_in_domain.values, building_demand_files):
            if exists(demand_file):
                building = Building(building_code, demand_file)
                building.load_demand_profile(network_type)
                if not max(building.demand_flow.profile) > 0:
                    continue
                building.load_building_location(shp_file)
                building.load_base_supply_system(self.locator, network_type)
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
        if buildings_in_domain is None:
            buildings_in_domain = pd.Series([building.identifier for building in self.buildings])

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
        print("\nInitializing domain:")
        self._initialize_energy_system_descriptor_classes()

        # Calculate base-case supply systems for all buildings
        print("\nCalculating operation of buildings' base-supply systems...")
        building_energy_potentials = Building.distribute_building_potentials(self.energy_potentials, self.buildings)
        [building.calculate_supply_system(building_energy_potentials[building.identifier])
            for building in self.buildings]

        # Optimise district energy systems
        print("Starting optimisation of district energy systems (i.e. networks + supply systems)...")

        algorithm = DistrictEnergySystem.optimisation_algorithm
        if self.config.general.debug:
            nbr_networks = self.config.optimization_new.maximum_number_of_networks
            building_ids = [building.identifier for building in self.buildings]
            tracker = optimizationTracker(algorithm.objectives, nbr_networks, building_ids, self.locator)
        else:
            tracker = None

        toolbox = base.Toolbox()
        main_process_memory = MemoryPreserver()
        if algorithm.parallelize_computation:
            component_classes = [cls[1] for cls in inspect.getmembers(component_module, inspect.isclass)]
            initialised_classes = [cls[1] for cls in inspect.getmembers(sys.modules[__name__], inspect.isclass)
                                   if cls[0] not in ['InputLocator', 'Domain', 'EnergyPotential']] \
                                  + component_classes
            main_process_memory = MemoryPreserver(algorithm.parallelize_computation, initialised_classes)

            pool = multiprocessing.get_context('spawn').Pool(algorithm.parallel_cores)
            toolbox.register("map", pool.map)

        toolbox.register("generate", ConnectivityVector.generate)
        toolbox.register("individual", tools.initIterate, ConnectivityVector, toolbox.generate)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        toolbox.register("evaluate", DistrictEnergySystem.evaluate_energy_system, district_buildings=self.buildings,
                         energy_potentials=self.energy_potentials, optimization_tracker=tracker,
                         process_memory=main_process_memory)
        toolbox.register("mate", ConnectivityVector.mate, algorithm=algorithm)
        toolbox.register("mutate", ConnectivityVector.mutate, algorithm=algorithm)
        toolbox.register("select", ConnectivityVector.select, population_size=algorithm.population,
                         optimization_tracker=tracker)

        # Create initial population and evaluate it
        population = set(toolbox.population(n=algorithm.population))
        non_dominated_fronts = toolbox.map(toolbox.evaluate, population)
        optimal_supply_system_combinations = {ind.as_str(): non_dominated_front[0] for ind, non_dominated_front
                                              in zip(population, non_dominated_fronts)}

        # Consolidate certain objects in the child processes' memory and make them available to the main process
        for non_dominated_front in non_dominated_fronts:
            main_process_memory.consolidate(non_dominated_front[1])
        toolbox.evaluate.keywords['process_memory'] = main_process_memory

        # If parallel processing and detailed outputs are both enabled
        if algorithm.parallelize_computation and tracker:
            # ... consolidate the tracker objects in the main process' memory
            tracker.consolidate([non_dominated_front[2] for non_dominated_front in non_dominated_fronts])

        for generation in range(1, algorithm.generations_networks + 1):
            offspring = set(algorithms.varAnd(population, toolbox, cxpb=algorithm.cx_prob, mutpb=algorithm.mut_prob))

            # Evaluate the individuals in the offspring, unless they are an exact copy of one of the parents
            new_ind = set(ind for ind in offspring if ind.as_str() not in optimal_supply_system_combinations.keys())
            non_dominated_fronts = toolbox.map(toolbox.evaluate, new_ind)
            optimal_supply_system_combinations.update({ind.as_str(): non_dominated_front[0] for ind, non_dominated_front
                                                       in zip(new_ind, non_dominated_fronts)})

            # Consolidate certain objects in the child processes' memory and make them available to the main process
            main_process_memory.clear_variables()
            [main_process_memory.consolidate(non_dominated_front[1]) for non_dominated_front in non_dominated_fronts]
            toolbox.evaluate.keywords['process_memory'] = main_process_memory

            # If parallel processing and detailed outputs are both enabled...
            if algorithm.parallelize_computation and tracker:
                # ...consolidate the tracker objects of each of the child processes
                tracker.consolidate([non_dominated_front[2] for non_dominated_front in non_dominated_fronts])

            population = set(toolbox.select(population.union(offspring), optimal_supply_system_combinations))
            print(f"\n\nDES: gen {generation}")

        main_process_memory.recall_class_variables()
        self.optimal_energy_systems = self._select_final_optimal_systems(population, algorithm.population)
        if tracker:
            tracker.print_evolutions()
        print("\nDistrict energy system optimisation complete!")

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
        [energy_system.evaluate(return_full_des=True)
         for energy_system in energy_systems_for_best_connectivity_vectors]

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
            connectivity = energy_system.encoding[0]
            supsys_selection = energy_system.encoding[1:]
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
        for des in self.optimal_energy_systems:
            # first save network layouts
            for ntw_ind, network in enumerate(des.networks):
                network_layout_file = self.locator.get_new_optimization_optimal_network_layout_file(des.identifier,
                                                                                                    network.identifier)
                network_layout = pd.concat([network.network_nodes, network.network_edges]).drop(['coordinates'], axis=1)
                network_layout = network_layout.to_crs(get_geographic_coordinate_system())
                network_layout.to_file(network_layout_file, driver='GeoJSON')

            # then save all information about the selected supply systems
            self._write_supply_systems_to_csv(des)

            # if prompted, generate detailed outputs
            if self.config.optimization_new.generate_detailed_outputs:
                self._write_detailed_results_to_csv(des)

        return

    def _write_supply_systems_to_csv(self, district_energy_system):
        """
        Writes information on supply systems of subsystems of a near-pareto-optimal district energy system into
        csv files. Information on each of the supply systems is written in a separate file.
        """
        # Create general values
        des_id = district_energy_system.identifier
        supply_system_summary = {'Supply_System': [],
                                 'Heat_Emissions_kWh': [],
                                 'System_Energy_Demand_kWh': [],
                                 'GHG_Emissions_kgCO2': [],
                                 'Cost_USD': []}

        # FOR STAND-ALONE BUILDINGS
        stand_alone_buildings = Domain._get_building_from_consumers(district_energy_system.consumers,
                                                                    district_energy_system.stand_alone_buildings)
        for building in stand_alone_buildings:
            supply_system_id = building.identifier
            supply_system = building.stand_alone_supply_system

            # Summarise structure of the supply system & print to file
            building_file = self.locator.get_new_optimization_optimal_supply_system_file(des_id, supply_system_id)
            Domain._write_system_structure(building_file, supply_system)

            # Calculate supply system fitness-values and add them to the summary of all supply systems
            supply_system_summary = Domain._add_to_systems_summary(supply_system_id, supply_system,
                                                                   supply_system_summary)

        # FOR NETWORKS
        for network_id, supply_system in district_energy_system.supply_systems.items():
            # Summarise structure of the supply system & print to file
            network_file = self.locator.get_new_optimization_optimal_supply_system_file(des_id, network_id)
            Domain._write_system_structure(network_file, supply_system)

            # Calculate supply system fitness-values and add them to the summary of all supply systems
            supply_system_summary = Domain._add_to_systems_summary(network_id, supply_system,
                                                                   supply_system_summary)

        # WRITE SUMMARY
        supply_system_summary['Supply_System'] += ['Total']
        supply_system_summary['Heat_Emissions_kWh'] += [sum(supply_system_summary['Heat_Emissions_kWh'])]
        supply_system_summary['System_Energy_Demand_kWh'] += [sum(supply_system_summary['System_Energy_Demand_kWh'])]
        supply_system_summary['GHG_Emissions_kgCO2'] += [sum(supply_system_summary['GHG_Emissions_kgCO2'])]
        supply_system_summary['Cost_USD'] += [sum(supply_system_summary['Cost_USD'])]

        summary_file = self.locator.get_new_optimization_optimal_supply_systems_summary_file(des_id)
        pd.DataFrame(supply_system_summary).to_csv(summary_file, index=False)

        return

    @staticmethod
    def _write_system_structure(results_file, supply_system):
        """Summarise supply system structure and write it to the indicated results file"""
        supply_system_info = [{'Component_category': component_category,
                               'Component_type': component.technology,
                               'Component_code': component_code,
                               'Capacity_kW': round(component.capacity, 3)}
                              for component_category, components in supply_system.installed_components.items()
                              for component_code, component in components.items()]

        # Write supply system structure to file
        pd.DataFrame(supply_system_info).to_csv(results_file, index=False)

        return

    @staticmethod
    def _add_to_systems_summary(supply_system_id, supply_system, supply_system_fitness_summary):
        """Add a given supply system to the summary of fitness values of all supply systems in the DES"""
        # Calculate overall system fitness values
        annual_heat_rejection = sum([sum(heat) for heat in supply_system.heat_rejection.values()])
        annual_energy_demand = sum([sum(demand) for demand in supply_system.system_energy_demand.values()])
        annual_ghg_emissions = sum([sum(emission) for emission in supply_system.greenhouse_gas_emissions.values()])
        annualised_cost = sum([cost for cost in supply_system.annual_cost.values()])

        # Save system fitness values in common dictionary
        supply_system_fitness_summary['Supply_System'] += [supply_system_id]
        supply_system_fitness_summary['Heat_Emissions_kWh'] += [annual_heat_rejection]
        supply_system_fitness_summary['System_Energy_Demand_kWh'] += [annual_energy_demand]
        supply_system_fitness_summary['GHG_Emissions_kgCO2'] += [annual_ghg_emissions]
        supply_system_fitness_summary['Cost_USD'] += [annualised_cost]

        return supply_system_fitness_summary

    def _write_detailed_results_to_csv(self, district_energy_system):
        """
        Writes csv-files with full time series of the key objective functions for each supply system.
        """
        # Set general variables
        des_id = district_energy_system.identifier
        year = self.weather['year'][0]
        date_range = get_date_range_hours_from_year(year)

        # FOR STAND-ALONE BUILDINGS
        stand_alone_buildings = Domain._get_building_from_consumers(district_energy_system.consumers,
                                                                    district_energy_system.stand_alone_buildings)
        for building in stand_alone_buildings:
            supply_system_id = building.identifier
            supply_system = building.stand_alone_supply_system

            # Summarise the objective function profiles (i.e. full time series) of the supply system & print to file
            building_file = self.locator.get_new_optimization_supply_systems_detailed_operation_file(des_id,
                                                                                                     supply_system_id)
            Domain._write_combined_objective_function_profiles(date_range, supply_system, building_file)

        # FOR NETWORKS
        for network_id, supply_system in district_energy_system.supply_systems.items():
            # Summarise the objective function profiles (i.e. full time series) of the supply system & print to file
            network_file = self.locator.get_new_optimization_supply_systems_detailed_operation_file(des_id, network_id)
            Domain._write_combined_objective_function_profiles(date_range, supply_system, network_file)
            # Create a breakdown of annual energy demand, cost, GHG- and heat-emissions and print to file
            breakdown_file = self.locator.get_new_optimization_supply_systems_annual_breakdown_file(des_id, network_id)
            Domain._write_annual_breakdown(supply_system, breakdown_file)

        # FOR DES AS A WHOLE
        # Summarise performance metrics of the networks and print to file
        if district_energy_system.networks:
            network_perf_file = self.locator.get_new_optimization_detailed_network_performance_file(des_id)
            Domain._write_detailed_network_performance(district_energy_system, network_perf_file)

        return

    @staticmethod
    def _get_building_from_consumers(consumers, building_codes):
        """ Get full building object based of list of consumers in domain and building code """
        buildings = []
        for consumer in consumers:
            if consumer.identifier in building_codes:
                buildings += [consumer]
        return buildings

    @staticmethod
    def _write_combined_objective_function_profiles(date_time, supply_system, results_file):
        """Write the central objective function profiles of a supply system to the indicated csv file."""
        if supply_system.heat_rejection.values():
            combined_heat_rejection_profile = pd.concat([heat_rejection_profile
                                                         for heat_rejection_profile
                                                         in supply_system.heat_rejection.values()],
                                                        axis=1).sum(1)
        else:
            combined_heat_rejection_profile = pd.Series(0, index=range(len(date_time)))

        if supply_system.greenhouse_gas_emissions.values():
            combined_ghg_emission_profile = pd.concat([ghg_emission_profile
                                                       for ghg_emission_profile
                                                       in supply_system.greenhouse_gas_emissions.values()],
                                                      axis=1).sum(1)
        else:
            combined_ghg_emission_profile = pd.Series(0, index=range(len(date_time)))

        if supply_system.system_energy_demand.values():
            combined_system_energy_demand_profile = pd.concat([system_demand_profile
                                                               for system_demand_profile
                                                               in supply_system.system_energy_demand.values()],
                                                              axis=1).sum(1)
        else:
            combined_system_energy_demand_profile = pd.Series(0, index=range(len(date_time)))

        # combine the profiles into one data frame and write to file
        combined_objective_function_timelines = pd.concat([date_time.to_series(index=range(len(date_time))),
                                                           combined_system_energy_demand_profile,
                                                           combined_heat_rejection_profile,
                                                           combined_ghg_emission_profile],
                                                          axis=1)
        combined_objective_function_timelines.to_csv(results_file, index=False,
                                                     header=['Date', 'System_energy_demand_kWh', 'Heat_rejection_kWh',
                                                             'GHG_emissions_kgCO2'])

        return

    @staticmethod
    def _write_annual_breakdown(supply_system, results_file):
        """Write the annual breakdown of the objective functions of a supply system to the indicated csv file."""
        # break down annual cost, energy demand, GHG and heat-emissions by energy carrier
        annual_energy_demand_by_ec = {energy_carrier: sum(demand_profile)
                                      for energy_carrier, demand_profile in supply_system.system_energy_demand.items()}
        annual_cost_by_ec =  {energy_carrier: supply_system.annual_cost[energy_carrier]
                              for energy_carrier in annual_energy_demand_by_ec.keys()}
        annual_ghg_emissions_by_ec = {energy_carrier: sum(emissions_profile)
                                      for energy_carrier, emissions_profile
                                      in supply_system.greenhouse_gas_emissions.items()}
        annual_heat_rejection_by_ec = {energy_carrier: sum(heat_profile)
                                       for energy_carrier, heat_profile in supply_system.heat_rejection.items()}

        # break down cost by component
        possible_components = [ci.code for ci in supply_system.structure.capacity_indicators.capacity_indicators]
        annual_cost_by_component = {component: cost
                                    for component, cost in supply_system.annual_cost.items()
                                    if component in possible_components}

        # write to DataFrame
        annual_breakdown = pd.DataFrame.from_records([annual_energy_demand_by_ec,
                                                      annual_cost_by_ec,
                                                      annual_ghg_emissions_by_ec,
                                                      annual_heat_rejection_by_ec,
                                                      annual_cost_by_component]).T
        annual_breakdown.columns = ['Annual_energy_demand_kWh', 'Annual_energy_carrier_cost_USD',
                                    'Annual_GHG_emissions_kgCO2', 'Annual_heat_rejection_kWh',
                                    'Annual_cost_by_component_USD']

        # write to file
        annual_breakdown.to_csv(results_file)

        return

    @staticmethod
    def _write_detailed_network_performance(district_energy_system, results_file):
        """
        Write network performance parameters, i.e. length of network, cost & average hourly and annual heat losses,
        to a file.
        """
        # Summarise performance metrics of the networks
        average_hourly_network_losses = {network.identifier: network.network_losses.mean()
                                         for network in district_energy_system.networks}
        std_dev_hourly_network_losses = {network.identifier: network.network_losses.std()
                                         for network in district_energy_system.networks}
        yearly_network_losses = {network.identifier: network.network_losses.sum()
                                 for network in district_energy_system.networks}
        network_lengths = {network.identifier: sum(network.network_piping['length_m'])
                           for network in district_energy_system.networks}
        network_costs = {network.identifier: network.annual_piping_cost *
                                             network.configuration_defaults['network_lifetime_yrs']
                         for network in district_energy_system.networks}

        # write to DataFrame
        network_performance = pd.DataFrame.from_records([average_hourly_network_losses,
                                                         std_dev_hourly_network_losses,
                                                         yearly_network_losses,
                                                         network_lengths,
                                                         network_costs]).T
        network_performance.columns = ['Average hourly network losses [kWh]',
                                       'Std. deviation of hourly network losses [kWh]',
                                       'Yearly network losses [kWh]',
                                       'Network length [m]',
                                       'Network cost [USD]']

        # write to file
        network_performance.to_csv(results_file)

        return


    def _initialise_domain_descriptor_classes(self):
        EnergyCarrier.initialize_class_variables(self)
        Algorithm.initialize_class_variables(self)
        Fitness.initialize_class_variables(self)

    def _initialize_energy_system_descriptor_classes(self):
        print("1. Creating available supply system components...")
        Component.initialize_class_variables(self)
        print("2. Finding possible network paths (this may take a while)...")
        Network.initialize_class_variables(self)
        print("3. Establishing district energy system structure...")
        DistrictEnergySystem.initialize_class_variables(self)
        SupplySystemStructure.initialize_class_variables(self)
        SupplySystem.initialize_class_variables(self)
        print("4. Defining possible connectivity vectors...")
        Connection.initialize_class_variables(self)


def main(config):
    """
    run the whole optimization routine
    """
    # initialise variables and define cooling demand
    locator = InputLocator(scenario=config.scenario)
    current_domain = Domain(config, locator)
    seed(100)

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
