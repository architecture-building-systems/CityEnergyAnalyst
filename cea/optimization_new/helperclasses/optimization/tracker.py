"""
This Building Class defines a building in the domain analysed by the optimisation script.

The buildings described using the Building Class bundle all properties relevant for the optimisation, including:
- The building's unique identifier (i.e. 'name' from the input editor)
- The building's location
- The demand profile of the building
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


import pandas as pd


class OptimizationTracker(object):

    def __init__(self, objectives, nbr_networks, buildings_in_domain, debug_locator):
        self.objectives = objectives
        self.network_codes = [f'N{1001 + network_ind}' for network_ind in range(nbr_networks)]
        self.buildings_in_domain = buildings_in_domain
        self.debug_locator = debug_locator

        self.current_generation = 0
        self.current_individual = 0

        self.candidate_individuals = {}
        self.current_networks_selection = {}
        self.current_supsys_combinations_selection = {}

        self.non_dom_networks = pd.DataFrame(columns=['Generation', 'Ind_Code', 'Connectivity',
                                                      'Network']+self.buildings_in_domain)
        self.non_dom_supsys_combinations = pd.DataFrame(columns=['Generation', 'Front', 'Ind_Code', 'Connectivity',
                                                                 'SupSys_Combination', 'Network'])
        self.non_dom_ind_fitnesses = pd.DataFrame(columns=['Generation', 'Front', 'Ind_Code',
                                                           'Connectivity', 'SupSys_Combination']+self.objectives)

        self._simplified_connectivity_codes = {}
        self._simplified_supsys_codes = {}

    def add_candidate_individual(self, candidate_individual):
        """
        Add a district energy system to the list of investigated 'candidate individuals'. This prevents details
        concerning the structure of the DistrictEnergySystem-object from being discarded before the whole generation of
        connectivity vectors have been analysed.
        """
        network_ids = [network.identifier for network in candidate_individual.networks]
        networks_with_supsys = list(candidate_individual.supply_systems.keys())
        network_graphs = {network.identifier: network
                          for network in candidate_individual.networks}
        supsys_structures = {network_id: supply_systems[0].structure
                             for network_id, supply_systems in candidate_individual.supply_systems.items()}
        supsys_individuals = {network_id: {ind: supsys.capacity_indicator_vector.values
                                          for ind, supsys in enumerate(supply_systems)}
                             for network_id, supply_systems in candidate_individual.supply_systems.items()}

        self.candidate_individuals[self.current_individual] = \
            {network_id: {'network_graph': network_graphs[network_id],
                          'supsys_structure': supsys_structures[network_id],
                          'supsys_individuals': supsys_individuals[network_id]}
             for network_id in network_ids
             if network_id in networks_with_supsys}

    def set_current_individual(self, connectivty_vector):
        """ Update the current connectivity vector which is being evaluated. """
        self.current_individual = connectivty_vector.as_str()

    def update_current_non_dominated_fronts(self, connectivity_selection, ordered_supsys_combinations):
        """
        Update the information on the 'best' individuals. 'Best' in this context means the energy systems resulting
        from the respective individuals are part of the highest order non-dominated fronts (in the objective functions
        space).
        Each individual is characterised by their combination of connectivity vector and capacity indicator vector and
        the resulting district energy system.
        """
        # update the network selection for the current generation of 'best' connectivity vectors
        self.update_network_selection(connectivity_selection)

        # update the current selection of the 'best' (i.e. least dominated) combinations of connectiviy vectors
        #   and capacity indicator vectors
        self.update_selected_supsys_combinations(ordered_supsys_combinations, connectivity_selection)

        # add current selections to the complete trackers
        self.add_to_trackers()
        self.print_evolutions()
        self.current_generation += 1

        return self

    def consolidate(self, list_of_trackers):
        """
        Python's multiprocessing tool on Windows 'spawns' child-processes i.e. all required object-instances
        are simply copied or recreated from scratch and are therefore separate from the instance in the parent-process.
        This method serves to consolidate the information stored in the trackers of the child-process in the main
        tracker instance of the parent-process.
        """

        self.candidate_individuals.update({individual_id: individual
                                           for tracker in list_of_trackers
                                           for individual_id, individual in tracker.candidate_individuals.items()})

        return self

    def update_network_selection(self, selected_individuals):
        """
        Update the selection connectivity vectors and their corresponding information on network-layout and supply
        system structures for the current generation.
        """
        # check if selection contains individuals (i.e. connectivity vectors) of previous generations selections
        selected_connectivities = [individual.as_str() for individual in selected_individuals]
        new_networks_selection = {connectivity: properties
                                     for connectivity, properties in self.current_networks_selection.items()
                                     if connectivity in selected_connectivities}

        # identify the newly selected connectivity vectors and their corresponding energy system information
        newly_selected = [individual for individual in selected_connectivities
                          if individual not in new_networks_selection.keys()]
        selected_candidates = {ind: self.candidate_individuals[ind] for ind in newly_selected}

        # Summarise the newly selected individual's network-layout and supply system structure
        for connectivity, energy_system in selected_candidates.items():
            # summarise network graph information
            network_graph_info = {network_id: pd.concat([properties['network_graph'].network_nodes,
                                                         properties['network_graph'].network_edges])
                                  for network_id, properties in energy_system.items()}

            # summarise supply system structure info
            active_components = {network_id: {category: {component_code: component.capacity
                                                          for component_code, component in components.items()}
                                               for category, components
                                               in properties['supsys_structure'].max_cap_active_components.items()}
                                  for network_id, properties in energy_system.items()}
            passive_components = {network_id: {category: {act_component_code: psv_components
                                                          for act_component_code, psv_components in components.items()}
                                               for category, components
                                               in properties['supsys_structure'].max_cap_passive_components.items()}
                                  for network_id, properties in energy_system.items()}
            supsys_structure_info = {network_id: {category: {**components,
                                                             **passive_components[network_id][category]}
                                                  for category, components in component_categories.items()}
                                     for network_id, component_categories in active_components.items()}

            # identify the components corresponding to each element of the capacity indicator vector
            ci_components = {network_id: [f'{capacity_indicator.category[0]}_{capacity_indicator.code}'
                                          for capacity_indicator
                                          in properties['supsys_structure'].capacity_indicators.capacity_indicators]
                             for network_id, properties in energy_system.items()}

            # add the summarised information to the new selection of the connectivity vectors' corr. energy systems
            new_networks_selection[connectivity] = {network_id: {'network_layout': network_graph_info[network_id],
                                                                 'supsys_structure': supsys_structure_info[network_id],
                                                                 'ci_component_sequence': ci_components[network_id]}
                                                       for network_id in energy_system.keys()}

        self.current_networks_selection = new_networks_selection

        return self.current_networks_selection

    def update_selected_supsys_combinations(self, ordered_supsys_combinations, connectivity_selection):
        """
        Update the selection of the best combinations of connectivity vectors and capacity indicator vectors, as well
        as the fitness values of their corresponding energy systems.
        """
        selected_connectivities = [individual.as_str() for individual in connectivity_selection]
        previous_supsys_combinations = {connectivity: {supsys_comb: front for supsys_comb in supsys_combinations.keys()}
                                        for front, combinations_in_front
                                        in self.current_supsys_combinations_selection.items()
                                        for connectivity, supsys_combinations in combinations_in_front.items()}

        # IDENTIFY THE COMBINATIONS THAT ARE PART OF THE n LEAST-DOMINATED FRONTS
        new_supsys_combinations_selection = {}

        # iterate over all evaluated supply system combination (ordered by fronts)
        for ind, combinations_in_front in enumerate(ordered_supsys_combinations):
            # when at least one n-th order non-dominated combination (connectivity + capacity indicators) has been
            #   found for each of the selected connectivities, stop tracking the rest.
            if all([any([connectivity in front.keys() for front in new_supsys_combinations_selection.values()])
                    for connectivity in selected_connectivities]):
                break

            front = ind + 1
            new_supsys_combinations_selection[f'front_{front}'] = {}

            for cv_and_supsys_combination in combinations_in_front:
                # when at least one n-th order non-dominated combination (connectivity + capacity indicators) has been
                #   found for each of the selected connectivities, stop tracking the rest.
                if all([any([connectivity in front.keys() for front in new_supsys_combinations_selection.values()])
                        for connectivity in selected_connectivities]):
                    break

                # identify the codes for the connectivity vector and supply system combination of the new individual
                connectivity = cv_and_supsys_combination.encoding[0]
                supsys_ind_by_network = {supply_system_ind.split('-')[0]: supply_system_ind.split('-')[1]
                                         for supply_system_ind in cv_and_supsys_combination.encoding[1:]}
                combination_id = "_".join([supsys_ind_by_network[network]
                                           if network in supsys_ind_by_network.keys() else 'x'
                                           for network in self.network_codes])

                # check if the connectivity is part of the generation's selection...
                if connectivity not in selected_connectivities:
                    continue
                # ... and if it is, clear the memory of the last generation if it was also part of that selection
                elif connectivity not in new_supsys_combinations_selection[f'front_{front}'].keys():
                    new_supsys_combinations_selection[f'front_{front}'][connectivity] = {}

                # if this connectivity vector and supply systems combination is part of the previous generation...
                if connectivity in previous_supsys_combinations.keys():
                    if combination_id in previous_supsys_combinations[connectivity]:
                        # ... simply allocate it to the correct new front
                        new_supsys_combinations_selection[f'front_{front}'][connectivity][combination_id] =\
                            self.current_supsys_combinations_selection[
                                previous_supsys_combinations[connectivity][combination_id]][
                                connectivity][combination_id]
                        continue

                # otherwise proceed with summarising combination's supply systems and overall fitness
                try:
                    combination = {'capacity_indicators': {comb[0:5]: self.summarize_civ(connectivity, comb)
                                                           for comb in cv_and_supsys_combination.encoding[1:]},
                                   'fitness': self.summarize_fitness(cv_and_supsys_combination)}
                except KeyError:
                    continue

                new_supsys_combinations_selection[f'front_{front}'][connectivity][combination_id] = combination

        self.current_supsys_combinations_selection = new_supsys_combinations_selection

        return self.current_supsys_combinations_selection

    def add_to_trackers(self):
        """ add information about the selected individuals to the network-, supply-systems- and fitness-tracker dataframes respectively """
        self.add_to_networks_tracker()
        self.add_to_supsys_tracker()
        self.add_to_fitness_tracker()

    def add_to_networks_tracker(self):
        """ add all information relating to the current networks to the relevant tracker dataframe """
        self._simplified_connectivity_codes = {connectivity: i+1
                                               for i, connectivity in enumerate(self.current_networks_selection.keys())}

        # flatten 'general information'-part of the current networks dictionary
        general_info = [{'Generation': self.current_generation,
                         'Ind_Code': self._simplified_connectivity_codes[connectivity],
                         'Connectivity': connectivity,
                         'Network': network}
                        for connectivity, networks in self.current_networks_selection.items()
                        for network in networks.keys()]

        # flatten 'building connections'-part of the current networks dictionary
        building_connections = [{building: 'X' if connectivity.split('_')[i] == network[-1] else '-'
                                 for i, building in enumerate(self.buildings_in_domain)}
                                for connectivity, networks in self.current_networks_selection.items()
                                for network in networks.keys()]

        # flatten 'supply systems capacities'-part of the current networks dictionary
        max_supsys_capacities = [{f'{category[0]}_{code}': capacity
                                  for category, components in network['supsys_structure'].items()
                                  for code, capacity in components.items()}
                                 for connectivity, networks in self.current_networks_selection.items()
                                 for network in networks.values()]

        # combine flattened dictionaries and store them in the main tracker dataframe
        current_networks_info = pd.DataFrame([{**general_info[i], **building_connections[i], **max_supsys_capacities[i]}
                                              for i in range(len(general_info))])
        self.non_dom_networks = pd.concat([self.non_dom_networks, current_networks_info])

        return self.non_dom_networks

    def add_to_supsys_tracker(self):

        self._simplified_supsys_codes = {}
        for connectivities in self.current_supsys_combinations_selection.values():
            for connectivity, supsys_combinations in connectivities.items():
                if connectivity not in self._simplified_supsys_codes.keys():
                    self._simplified_supsys_codes[connectivity] = {supsys_combination:
                                                                       f'{self._simplified_connectivity_codes[connectivity]}.{j+1}'
                                                                   for j, supsys_combination
                                                                   in enumerate(supsys_combinations.keys())}
                else:
                    self._simplified_supsys_codes[connectivity].update({supsys_combination:
                                                                            f'{self._simplified_connectivity_codes[connectivity]}.{j+1}'
                                                                        for j, supsys_combination
                                                                        in enumerate(supsys_combinations.keys())})



        # flatten 'general information'-part of the current supply systems dictionary
        general_info = [{'Generation': self.current_generation,
                         'Front': int(front.split('_')[1]),
                         'Ind_Code': self._simplified_supsys_codes[connectivity][supsys_combination],
                         'Connectivity': connectivity,
                         'SupSys_Combination': supsys_combination,
                         'Network': network}
                        for front, connectivities in self.current_supsys_combinations_selection.items()
                        for connectivity, supsys_combinations in connectivities.items()
                        for supsys_combination, properties in supsys_combinations.items()
                        for network in properties['capacity_indicators'].keys()]


        # flatten 'capacity indicators'-part of the current supply systems dictionary
        capacity_indicators = [capacity_indicators
                               for front in self.current_supsys_combinations_selection.values()
                               for connectivity in front.values()
                               for supsys_combination in connectivity.values()
                               for capacity_indicators in supsys_combination['capacity_indicators'].values()]

        # combine flattened dictionaries and store them in the main tracker dataframe
        current_supsys_info = pd.DataFrame([{**general_info[i], **capacity_indicators[i]}
                                              for i in range(len(general_info))])
        self.non_dom_supsys_combinations = pd.concat([self.non_dom_supsys_combinations, current_supsys_info])

        return self.non_dom_supsys_combinations

    def add_to_fitness_tracker(self):

        # flatten 'general information'-part of the current supply systems dictionary
        general_info = [{'Generation': self.current_generation,
                         'Front': int(front.split('_')[1]),
                         'Ind_Code': self._simplified_supsys_codes[connectivity][supsys_combination],
                         'Connectivity': connectivity,
                         'SupSys_Combination': supsys_combination}
                        for front, connectivities in self.current_supsys_combinations_selection.items()
                        for connectivity, supsys_combinations in connectivities.items()
                        for supsys_combination in supsys_combinations.keys()]

        # flatten 'fitness'-part of the current systems dictionary
        fitnesses = [supsys_combination['fitness']
                     for front in self.current_supsys_combinations_selection.values()
                     for connectivity in front.values()
                     for supsys_combination in connectivity.values()]

        # combine flattened dictionaries and store them in the main tracker dataframe
        current_fitness_info = pd.DataFrame([{**general_info[i], **fitnesses[i]}
                                            for i in range(len(general_info))])
        self.non_dom_ind_fitnesses = pd.concat([self.non_dom_ind_fitnesses, current_fitness_info])

        return self.non_dom_ind_fitnesses

    def summarize_civ(self, connectivity, supsys_combination):
        """ Create a dictionary representing the capacity indicator vector (with component codes as keys) """
        capacity_indicators = \
            {self.current_networks_selection[connectivity][supsys_combination[0:5]]['ci_component_sequence'][i]: ci
             for i, ci in enumerate(self.candidate_individuals[connectivity][supsys_combination[0:5]][
                                        'supsys_individuals'][int(supsys_combination[-1])])}
        return capacity_indicators

    def summarize_fitness(self, connectivity_and_capacities_combination):
        """
        Create a fitness dictionary for a given individual (i.e. combination of connectivity vector & corresponding
        capacity indicator vectors for each network's supply system)
        """
        overall_fitness = {self.objectives[i]: fitness
                           for i, fitness in enumerate(connectivity_and_capacities_combination.fitness.values)}
        return overall_fitness

    def print_evolutions(self):
        """ Print the contents of all tracker dataframes to their respective files """

        self.non_dom_networks.to_csv(self.debug_locator.get_new_optimization_debugging_network_tracker_file(), index=False)
        self.non_dom_supsys_combinations.to_csv(self.debug_locator.get_new_optimization_debugging_supply_system_tracker_file(), index=False)
        self.non_dom_ind_fitnesses.to_csv(self.debug_locator.get_new_optimization_debugging_fitness_tracker_file(), index=False)
