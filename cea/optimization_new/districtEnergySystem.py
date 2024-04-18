"""
District Cooling System Class:
defines all properties of a district cooling system regard both its structure and its operation:
STRUCTURE
- Connectivity vector (identifying connections to networks and stand-alone buildings)
- List of the networks (network objects) found in the DCS
OPERATION
- Demands of the individual subsystems (networks and stand-alone buildings)
- Distributed energy potentials (allocated to each of the subsystems)
MIX (STRUCTURE & OPERATION)
- List of supply systems (supplySystem objects)
PERFORMANCE
- Total annualised cost
- Total annualised heat release
- Total annualised system energy demand
- Total annualised greenhouse gas emissions
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

import numpy as np
import pandas as pd
import time
import multiprocessing

from copy import copy
from deap import algorithms, base, tools

from cea.optimization_new.network import Network
from cea.optimization_new.supplySystem import SupplySystem
from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
from cea.optimization_new.containerclasses.systemCombination import SystemCombination
from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure
from cea.optimization_new.helpercalsses.optimization.algorithm import GeneticAlgorithm
from cea.optimization_new.helpercalsses.optimization.capacityIndicator import CapacityIndicatorVector, CapacityIndicatorVectorMemory
from cea.optimization_new.helpercalsses.multiprocessing.memoryPreserver import MemoryPreserver


class DistrictEnergySystem(object):
    _max_nbr_networks = 0
    _number_of_selected_DES = 0
    _network_type = ""
    _civ_memory = CapacityIndicatorVectorMemory()
    optimisation_algorithm = GeneticAlgorithm()

    def __init__(self, connectivity, buildings, energy_potentials):
        self._identifier = 'xxx'
        self.connectivity = connectivity

        self.consumers = buildings
        self.stand_alone_buildings = []
        self.networks = []

        self.energy_potentials = energy_potentials
        self.distributed_potentials = {}

        self.subsystem_demands = {}
        self.supply_systems = {}
        self.best_supsys_combinations = []

    @property
    def identifier(self):

        return self._identifier

    @identifier.setter
    def identifier(self, new_identifier):
        if isinstance(new_identifier, str):
            self._identifier = new_identifier
        else:
            print("Please set a valid identifier.")

    def __copy__(self):
        """ Create a copy of the district energy system object. """
        # Initialize a new object
        object_copy = DistrictEnergySystem(self.connectivity, self.consumers, self.energy_potentials)

        # Assign the same values to the new object
        #  First, all attributes that are shared between the original and the new object (same memory address)
        object_copy.identifier = self.identifier
        object_copy.stand_alone_buildings = self.stand_alone_buildings
        object_copy.networks = self.networks

        object_copy.energy_potentials = self.energy_potentials
        object_copy.distributed_potentials = self.distributed_potentials
        object_copy.subsystem_demands = self.subsystem_demands

        #  Then, all attributes that are unique to the original object and need to be copied (new memory address)
        object_copy.supply_systems = {network: [copy(supply_system) for supply_system in supply_systems]
                                      for network, supply_systems in self.supply_systems.items()}

        return object_copy

    @staticmethod
    def evaluate_energy_system(connectivity_vector, district_buildings, energy_potentials, optimization_tracker=None,
                               process_memory=None):
        """
        Identify optimal district energy systems. The selected district energy systems represent an optimal combination
        of the most favourable supply systems for each of the networks in the district (i.e. the best combinations of
        pareto-optimal solutions for the subsystems' supply systems).

        :param connectivity_vector: connectivity vector specifying which buildings are connected by a thermal network.
        :type connectivity_vector: <cea.optimization_new.containerclasses.optimization.connectivityVector>-
                                   ConnectivityVector class object
        :param district_buildings: all buildings in the selected district
        :type district_buildings: list of <cea.optimization_new.building>-Building class objects
        :param energy_potentials: renewable energy potentials in the district
        :type energy_potentials: list of <cea.optimization_new.containerclasses.energysystems.energyPotential>-
                                 EnergyPotential class objects
        :param optimization_tracker: object tracking the progress of the optimization
        :type optimization_tracker: <cea.optimization_new.helperclasses.optimization.tracker>-OptimizationTracker class
                                    object
        :param process_memory: Memory from the parent process to be transferred to the child process in multiprocessing
        :type process_memory: <cea.optimization_new.helperclasses.multiprocessing.memoryPreserver>-MemoryPreserver class
                              object
        """
        if process_memory.multiprocessing:
            process_memory.recall_class_variables()

        if optimization_tracker:
            optimization_tracker.set_current_individual(connectivity_vector)

        if not DistrictEnergySystem._civ_memory.max_district_energy_demand:
            max_district_demand = max(sum([building.demand_flow.profile for building in district_buildings]))
            DistrictEnergySystem._civ_memory = CapacityIndicatorVectorMemory(max_district_demand)

        # build a new district cooling system including its networks
        new_district_cooling_system = DistrictEnergySystem(connectivity_vector,
                                                           district_buildings,
                                                           energy_potentials)

        non_dominated_systems, optimization_tracker \
            = new_district_cooling_system.evaluate(optimization_tracker)

        process_memory.update(['DistrictEnergySystem'])

        return non_dominated_systems, process_memory, optimization_tracker

    def evaluate(self, optimization_tracker=None, return_full_des=False):
        """
        Evaluate the possible district energy system configurations (based on buildings, potentials and connectivity) by:

        1. Generating networks between buildings corresponding to the selected connectivity vector.
        2. Determine demand and potentials for each subsystem's supply system.
        3. Generate as list of pareto-optimal supply systems for each subsystem.
        4. Find the best combinations of the subsystem's supply systems (with respect to selected objectives).

        :return self.best_supsys_combinations: the best district energy system configurations
                                               (i.e. combinations of subsystems' supply systems)
        :rtype self.best_supsyst_combinations: list of lists of the following structure
                    [['connectivty', 'subsys_1-supsys_x', 'subsys_id_2-supsys_y', ...],
                     ['connectivty', 'subsys_1-supsys_z', 'subsys_id_2-supsys_m', ...],
                     ...
                    ]
        """
        print(f"Starting evaluation of connectivity vector: {self.connectivity.values}")

        # build networks to fit the district energy system's connectivity
        self.generate_networks()

        # aggregate demands and distribute potentials for each network
        self.aggregate_demand()
        self.distribute_potentials()

        # optimise supply systems for each network
        self.generate_optimal_supply_systems()

        # aggregate objective functions for all subsystems across the entire district energy system
        self.combine_supply_systems_and_networks()

        # if prompted, track certain core characteristics of the district energy system
        if optimization_tracker:
            optimization_tracker.add_candidate_individual(self)

        # return the entire district-energy-system object
        if return_full_des:
            return self

        return self.best_supsys_combinations, optimization_tracker

    def generate_networks(self):
        """
        Generate networks according to the connectivity-vector. Generate list of stand-alone buildings and a list
        of networks (Network-objects).

        :return self.networks: thermal networks placed in the domain
        :rtype self.networks: list of <cea.optimization_new.network>-Network objects
        """
        network_ids = np.unique(np.array(self.connectivity.values))
        building_ids = [building.identifier for building in self.consumers]
        for network_id in network_ids:
            if network_id == 0:
                buildings_are_disconnected = [connection == network_id for connection in self.connectivity]
                self.stand_alone_buildings = [building_id for [building_id, is_disconnected]
                                              in zip(building_ids, buildings_are_disconnected)
                                              if is_disconnected]
            else:
                buildings_are_connected_to_network = [connection == network_id for connection in self.connectivity]
                connected_buildings = [building_id for [building_id, is_connected]
                                       in zip(building_ids, buildings_are_connected_to_network)
                                       if is_connected]
                full_network_identifier = 'N' + str(1000 + network_id)
                network = Network(self.connectivity, full_network_identifier, connected_buildings)
                network.run_steiner_tree_optimisation()
                network.calculate_operational_conditions()
                self.networks.append(network)
        return self.networks

    def aggregate_demand(self):
        """
        Calculate aggregated thermal energy demand profiles of the district energy system's subsystems, i.e. thermal
        networks. This includes the connected building's thermal energy demand and network losses.

        :return self.subsystem_demands: aggregated demand profiles of subsystems
        :rtype self.subsystem_demands: dict of pd.Series (keys are network.identifiers)
        """
        building_energy_carriers = np.array([building.demand_flow.energy_carrier.code for building in self.consumers])
        required_energy_carriers = np.unique(building_energy_carriers)
        if len(required_energy_carriers) != 1:
            raise ValueError(f"The building energy demands require {len(required_energy_carriers)} different energy "
                             f"carriers to be produced. "
                             f"The optimisation algorithm can not handle more than one at the moment.")
        else:
            energy_carrier = required_energy_carriers[0]

        network_ids = [network.identifier for network in self.networks]
        self.subsystem_demands = dict([(network_id,
                                        EnergyFlow('primary', 'consumer', energy_carrier,
                                                   pd.Series(0.0, index=np.arange(EnergyFlow.time_frame)))
                                        )
                                       for network_id in network_ids])

        for network in self.networks:
            building_demand_flows = [building.demand_flow for building in self.consumers
                                     if building.identifier in network.connected_buildings]
            aggregated_demand = EnergyFlow.aggregate(building_demand_flows)[0]
            # subtract network losses (losses are negative, therefore subtracting them increases the demand requirement)
            aggregated_demand.profile -= network.network_losses
            self.subsystem_demands[network.identifier] = aggregated_demand

        return self.subsystem_demands

    def distribute_potentials(self):
        """
        Distribute the total domain's energy potentials depending on the buildings within each of networks (for
        building-scale potentials) or on the share of the domain's total demand each network makes out (for domain-scale
        potentials).
        """
        network_demand_shares = None
        network_identifiers = [network.identifier for network in self.networks]
        self.distributed_potentials = {network_id: {} for network_id in network_identifiers}

        for energy_potential in self.energy_potentials:
            main_energy_carrier = energy_potential.main_potential.energy_carrier.code
            # distribute building-scale energy potentials
            if energy_potential.scale == 'Building':
                for network in self.networks:
                    main_network_pot_profile = sum([energy_potential.main_building_profiles[building]
                                                    for building in network.connected_buildings])
                    if main_energy_carrier in self.distributed_potentials[network.identifier].keys():
                        self.distributed_potentials[network.identifier][main_energy_carrier] += main_network_pot_profile
                    else:
                        main_network_pot_flow = EnergyFlow('source', 'secondary',
                                                           main_energy_carrier, main_network_pot_profile)
                        self.distributed_potentials[network.identifier][main_energy_carrier] = main_network_pot_flow

                    if energy_potential.auxiliary_potential.energy_carrier:
                        aux_energy_carrier = energy_potential.auxiliary_potential.energy_carrier.code
                        aux_network_pot_profile = sum([energy_potential.auxiliary_building_profiles[building]
                                                       for building in network.connected_buildings])
                        if aux_energy_carrier in self.distributed_potentials[network.identifier].keys():
                            self.distributed_potentials[network.identifier][aux_energy_carrier] += \
                            aux_network_pot_profile
                        else:
                            aux_network_pot_flow = EnergyFlow('source', 'secondary',
                                                              aux_energy_carrier, aux_network_pot_profile)
                            self.distributed_potentials[network.identifier][aux_energy_carrier] = aux_network_pot_flow
            # distribute domain-scale energy potentials
            if energy_potential.scale == 'Domain':
                if not network_demand_shares:
                    network_yearly_demands = {network: self.subsystem_demands[network].profile.sum()
                                              for network in network_identifiers}
                    network_demands_sum = sum([network_yearly_demands[network] for network in network_identifiers])
                    network_demand_shares = {network: network_yearly_demands[network]/network_demands_sum
                                             for network in network_identifiers}

                for network_id in network_identifiers:
                    main_network_pot_profile = energy_potential.main_potential.profile * \
                                               network_demand_shares[network_id]
                    if main_energy_carrier in self.distributed_potentials[network_id].keys():
                        self.distributed_potentials[network_id][main_energy_carrier] += main_network_pot_profile
                    else:
                        main_network_pot_flow = EnergyFlow('source', 'secondary',
                                                           main_energy_carrier, main_network_pot_profile)
                        self.distributed_potentials[network_id][main_energy_carrier] = main_network_pot_flow

                    if energy_potential.auxiliary_potential.energy_carrier:
                        aux_energy_carrier = energy_potential.auxiliary_potential.energy_carrier.code
                        aux_network_pot_profile = energy_potential.auxiliary_potential.profile\
                                                  * network_demand_shares[network_id]
                        if aux_energy_carrier in self.distributed_potentials[network_id].keys():
                            self.distributed_potentials[network_id][aux_energy_carrier] += aux_network_pot_profile
                        else:
                            aux_network_pot_flow = EnergyFlow('source', 'secondary',
                                                              aux_energy_carrier, aux_network_pot_profile)
                            self.distributed_potentials[network_id][aux_energy_carrier] = aux_network_pot_flow

        return self.distributed_potentials

    def generate_optimal_supply_systems(self):
        """
        Build and calculate operation for supply systems of each of the subsystems of the district energy system:

        :return self.supply_systems: supply systems of all subsystems
        :rtype self.supply_systems: list of <cea.optimization_new.supplySystem>-SupplySystem objects
        """
        for network in self.networks:
            system_structure = SupplySystemStructure(max_supply_flow=self.subsystem_demands[network.identifier],
                                                     available_potentials=self.distributed_potentials[network.identifier])
            system_structure.build()

            pareto_optimal_systems = self.optimise_supply_system(system_structure, network)
            if pareto_optimal_systems:
                self.supply_systems[network.identifier] = pareto_optimal_systems

        return self.supply_systems

    def optimise_supply_system(self, system_structure, subsystem):
        """
        Find 'near pareto-optimal' (i.e. non-dominated) supply systems that match the given supply system structure and
        supply the energy demand required by the indicated subsystem.

        :param system_structure: structure which the generated supply systems need to satisfy
        :type system_structure: <cea.optimization_new.supplySystem>-SupplySystem object
        :param subsystem: generated supply systems need to meet this subsystem's demand
        :type subsystem: <cea.optimization_new.network>-Network object OR <cea.optimization_new.building>-Building object

        :return optimal_supply_systems: result of the optimization algorithm, i.e. a set of supply systems minimising
                                        the chosen objective functions
        :rtype optimal_supply_systems:

        """
        print(f"Starting optimisation of supply system {subsystem.identifier}.")

        start_time = time.time()

        subsystem_demand = self.subsystem_demands[subsystem.identifier]
        max_subsystem_demand = subsystem_demand.profile.max()

        structure_civ = system_structure.capacity_indicators
        algorithm = SupplySystem.optimisation_algorithm
        ref_points = tools.uniform_reference_points(algorithm.nbr_objectives, 12)
        main_process_memory = MemoryPreserver()

        toolbox = base.Toolbox()
        toolbox.register("generate", CapacityIndicatorVector.generate, civ_structure=structure_civ, method='from_memory',
                         civ_memory=self._civ_memory, max_system_demand=max_subsystem_demand)
        toolbox.register("individual", CapacityIndicatorVector.initialize,
                         capacity_indicator_generator=toolbox.generate, dependencies=structure_civ.dependencies)
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)

        toolbox.register("evaluate", SupplySystem.evaluate_supply_system,
                         system_structure=system_structure, demand_energy_flow=subsystem_demand,
                         objectives=algorithm.objectives, process_memory=main_process_memory)
        toolbox.register("mate", CapacityIndicatorVector.mate, algorithm=algorithm)
        toolbox.register("mutate", CapacityIndicatorVector.mutate, algorithm=algorithm)
        toolbox.register("select", tools.selNSGA3, ref_points=ref_points)

        # Generate initial population
        population = toolbox.population(n=algorithm.population)
        fitnesses = toolbox.map(toolbox.evaluate, population)
        for i, fit in enumerate(fitnesses):
            # if the supply system could not be built and/or operated properly, generate and evaluate a new capacity
            #   indicator vector until a fit supply system is found or until 10 attempts have been made
            j = 0
            while not fit:
                if j > 10:
                    fit = [np.inf for _ in range(algorithm.nbr_objectives)]
                    break
                else:
                    population[i] = toolbox.individual()
                    fit = toolbox.evaluate(population[i])
                    j += 1

            population[i].fitness.values = fit

        # Eliminate duplicates from population
        population = [ind1 for i, ind1 in enumerate(population)
                      if ind1.values not in [ind2.values for ind2 in population[i+1:]]]

        # Perform the genetic optimization
        for generation in range(1, algorithm.generations_supply_systems + 1):
            # initialize a few relevant variables
            population_civs = set(tuple(pop_ind.values) for pop_ind in population)
            targeted_number_of_offspring = 0
            offspring = []
            fit_offspring = []
            unfit_offspring = []
            procreation_attempts = 0

            # generate offspring until a sufficient number of fit offspring has been generated
            while unfit_offspring or procreation_attempts == 0:
                # perform mutation and crossover to generate a batch of offspring
                offspring = algorithms.varAnd(population, toolbox, cxpb=algorithm.cx_prob, mutpb=algorithm.mut_prob)
                # filter out offspring that are identical to existing population members
                novel_offspring = [offspring_ind for offspring_ind in offspring
                                   if tuple(offspring_ind.values) not in population_civs]
                # decide on the number of offspring to create in this generation
                if procreation_attempts == 0:
                    targeted_number_of_offspring = len(novel_offspring)
                # reset the list of unfit offspring
                unfit_offspring = []
                # evaluate the fitness of the offspring
                fitnesses = toolbox.map(toolbox.evaluate, novel_offspring)
                for ind, fit in zip(novel_offspring, fitnesses):
                    if fit:
                        ind.fitness.values = fit
                        if tuple(ind.values) not in set(tuple(fit_ind.values) for fit_ind in fit_offspring):
                            fit_offspring += [ind]
                    else:
                        unfit_offspring += [ind]
                # if the targeted number of offspring is not yet reached and there have been fewer than 10 attempts,
                #   try again
                procreation_attempts += 1
                if procreation_attempts >= 10 or len(fit_offspring) >= targeted_number_of_offspring:
                    break

            # select the fittest individuals among population and offspring and replace the population with them
            if len(population + fit_offspring) >= algorithm.population:
                population = toolbox.select(population + fit_offspring, algorithm.population)
            else:
                population = toolbox.select(population + fit_offspring, len(population + fit_offspring))
            print(f"{subsystem.identifier}: gen {generation} - "
                  f"{round(sum([1 for i in population if tuple(i.values) not in population_civs])/len(offspring)*100)}"
                  f"% of offspring retained")

        # evaluate the fitness of the final population and store the non-dominated individuals in the memory
        # (in case some invalid individuals of the initial population remain, remove them now)
        optimal_supply_systems = [SupplySystem(system_structure, ind, subsystem_demand) for ind in population
                                  if list(ind.fitness.values) != [np.inf for _ in range(algorithm.nbr_objectives)]]
        if optimal_supply_systems:
            [supply_system.evaluate() for supply_system in optimal_supply_systems]
            self._civ_memory.update(optimal_supply_systems)
            end_time = time.time()
            print(f"Supply system {subsystem.identifier} optimised."
                  f"(Time elapsed {end_time-start_time} s)")
        else:
            end_time = time.time()
            print(f"Supply system {subsystem.identifier} could not be optimised. There are no feasible solutions."
                  f"Try checking the configuration (e.g. available components) of the district energy system."
                  f"(Time elapsed {end_time-start_time} s)")

        return optimal_supply_systems

    def combine_supply_systems_and_networks(self):
        """
        Combine optimal supply systems of the different subsystems (networks or buildings) TODO: add latter option to config
        of the district energy system and identify the non-dominated system combinations (i.e. combinations that
        perform the best with respect to the selected optimisation objectives).

        :return self.best_subsys_combinations: A list of identifiers specifying which supply system configuration has
                                               been selected for each subsystems as part of the best system
                                               combinations.
        :rtype self.best_subsystem_combinations: list of list of str
        """
        # create a system combination container with an associated fitness value (required by the sorting function of deap)
        algorithm = SupplySystem.optimisation_algorithm

        # initialise a list of supply system combinations by adding the supply systems of the first network to them
        if not self.supply_systems: # for a district without networks
            first_network = None
            connectivity_str = self.connectivity.as_str()
            supply_system_combinations = [SystemCombination([connectivity_str])]
            supply_system_combinations[0].fitness.values = tuple([0] * algorithm.nbr_objectives)
        else:
            first_network = list(self.supply_systems.keys())[0]
            connectivity_str = self.connectivity.as_str()
            supply_system_combinations = [SystemCombination([connectivity_str,  first_network + "-" + str(i)])
                                          for i, supply_system in enumerate(self.supply_systems[first_network])]
            for i, system_combination in enumerate(supply_system_combinations):
                self.add_network_cost(first_network, i)
                system_combination.fitness.values = tuple(self.supply_systems[first_network][i].overall_fitness.values())
            supply_system_combinations = tools.emo.sortLogNondominated(supply_system_combinations, 100,
                                                                       first_front_only=True)

        # calculate fitness value of the stand-alone buildings
        if not self.stand_alone_buildings:
            total_stand_alone_building_fitness = (0,) * algorithm.nbr_objectives
        else:
            stand_alone_building_fitnesses = [building.stand_alone_supply_system.overall_fitness
                                              for building in self.consumers
                                              if building.identifier in self.stand_alone_buildings]
            total_stand_alone_building_fitness = tuple([sum([building_fitness[objective]
                                                             for building_fitness in stand_alone_building_fitnesses])
                                                        for objective in stand_alone_building_fitnesses[0].keys()])

        # combining non-dominated supply-system solutions for all networks
        for network, supply_system in self.supply_systems.items():
            if network == first_network:
                continue

            new_supply_system_combinations = []
            for combination in supply_system_combinations:
                new_combinations = [SystemCombination(combination.encoding + [network + '-' + str(i)])
                                    for i, supply_system in enumerate(self.supply_systems[network])]
                for i, system_combination in enumerate(new_combinations):
                    self.add_network_cost(network, i)
                    system_combination.fitness.values = \
                        tuple([fit_1 + fit_2 for fit_1, fit_2 in
                               zip(list(combination.fitness.values),
                                   self.supply_systems[network][i].overall_fitness.values())])

                new_supply_system_combinations += new_combinations
            supply_system_combinations = tools.emo.sortLogNondominated(new_supply_system_combinations, 100,
                                                                       first_front_only=True)

        # add the stand-alone building's fitness values to reflect the fitness of the whole district energy system
        for supsys_combination in supply_system_combinations:
            supsys_combination.fitness.values = tuple([fit_1 + fit_2 for fit_1, fit_2 in
                                                       zip(list(supsys_combination.fitness.values),
                                                           total_stand_alone_building_fitness)])

        self.best_supsys_combinations = supply_system_combinations

        return self.best_supsys_combinations

    def add_network_cost(self, network_id, supply_system_index):
        """ Add the network cost to its associated supply system's overall fitness """
        # retrieve the network cost
        network_cost = [network.annual_piping_cost for network in self.networks if network.identifier == network_id][0]
        # if cost is part of the objective functions, add the network cost
        if 'cost' in self.supply_systems[network_id][supply_system_index].overall_fitness.keys():
            self.supply_systems[network_id][supply_system_index].overall_fitness['cost'] += network_cost

        return

    def select_supply_system_combination(self, supply_system_combination):
        """
        Select definitive supply systems for each of the district energy system's subsystems
        """
        # reformat the supply system combination vector
        supply_system_selection = {system_selection.split('-')[0]: int(system_selection.split('-')[1])
                                   for system_selection in supply_system_combination}

        # create a copy of the general district energy solution (one connectivity + many non-dominated supply systems)
        definitive_des = copy(self)

        # specify the selected SupplySystem for each of the subsystems (one supply system per network &
        #   per stand-alone building)
        for subsystem_id, supsys_index in supply_system_selection.items():
            definitive_des.supply_systems[subsystem_id] = self.supply_systems[subsystem_id][supsys_index]

        # update some object attributes
        definitive_des.best_supsys_combinations = None
        DistrictEnergySystem._number_of_selected_DES += 1
        definitive_des.identifier = f'{DistrictEnergySystem._network_type}S_' \
                                    + str(100 + DistrictEnergySystem._number_of_selected_DES)

        return definitive_des

    @staticmethod
    def initialize_class_variables(domain):
        """ Store maximum number of networks and optimisation algorithm parameters in class variables. """
        DistrictEnergySystem._max_nbr_networks = domain.config.optimization_new.maximum_number_of_networks
        DistrictEnergySystem._network_type = domain.config.optimization_new.network_type

        # set district energy system optimisation parameters
        selection_algorithm = domain.config.optimization_new.networks_algorithm
        mutation_method = domain.config.optimization_new.networks_mutation_method
        crossover_method = domain.config.optimization_new.networks_crossover_method
        population_size = domain.config.optimization_new.ga_population_size
        number_of_generations = domain.config.optimization_new.ga_number_of_generations
        mut_prob = domain.config.optimization_new.ga_mutation_prob
        cx_prob = domain.config.optimization_new.ga_crossover_prob
        mut_eta = domain.config.optimization_new.ga_mutation_eta
        parallelize = domain.config.multiprocessing
        cores = multiprocessing.cpu_count() - domain.config.general.number_of_cpus_to_keep_free
        DistrictEnergySystem.optimisation_algorithm = GeneticAlgorithm(selection=selection_algorithm,
                                                                       mutation=mutation_method,
                                                                       crossover=crossover_method,
                                                                       population_size=population_size,
                                                                       number_of_generations=number_of_generations,
                                                                       mut_probability=mut_prob, cx_probability=cx_prob,
                                                                       mut_eta=mut_eta, parallelize=parallelize,
                                                                       cores=cores)
