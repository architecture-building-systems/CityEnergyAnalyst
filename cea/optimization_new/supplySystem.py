"""
Subsystem Class:
defines a specific supply system layout of a single network or stand-alone building in the DCS, including:
STRUCTURE
- types of installed components
- capacities of components
OPERATION
- energy inputs, outputs and losses during operation
PERFORMANCE
- cost of components and energy carriers
- system energy demand (i.e. power inputs to the supply system)
- heat rejection of the system (losses + exhausts)
- greenhouse gas emissions of the system
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
from copy import copy
from math import isclose

from cea.optimization_new.containerclasses.energyCarrier import EnergyCarrier
from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
from cea.optimization_new.containerclasses.supplySystemStructure import SupplySystemStructure
from cea.optimization_new.helpercalsses.optimization.algorithm import GeneticAlgorithm
from cea.optimization_new.helpercalsses.optimization.capacityIndicator import CapacityIndicatorVector


class SupplySystem(object):
    optimisation_algorithm = GeneticAlgorithm()
    _ec_releases_to_grids = []
    _ec_releases_to_env = []

    def __init__(self, system_structure=SupplySystemStructure(), capacity_indicator_vector=CapacityIndicatorVector(),
                 demand_energy_flow=EnergyFlow()):
        self.structure = system_structure
        self.capacity_indicator_vector = capacity_indicator_vector
        self.demand_energy_flow = demand_energy_flow

        # set energy potential parameters
        self.available_potentials = system_structure.available_potentials
        self.used_potentials = {}

        # set system operation parameters
        self.installed_components = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self.component_energy_inputs = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self.component_energy_outputs = {'primary': {}, 'secondary': {}, 'tertiary': {}}

        # set system evaluation parameters
        self.system_energy_demand = {}
        self.heat_rejection = {}
        self.greenhouse_gas_emissions = {}
        self.annual_cost = {}
        self.overall_fitness = {}

    @property
    def structure(self):
        return self._structure

    @structure.setter
    def structure(self, new_structure):
        if not isinstance(new_structure, SupplySystemStructure):
            raise TypeError("Make sure the indicated supply system structure is of type SupplySystemStructure.")
        else:
            self._structure = new_structure

    def __copy__(self):
        """ Create a copy of the supply system object. """
        # Initialize a new object
        object_copy = SupplySystem(self.structure, self.capacity_indicator_vector, self.demand_energy_flow)

        # Assign the same values to the new object
        #  First, all attributes that are shared between the original and the new object (same memory address)
        object_copy.installed_components = self.installed_components

        #  Then, all attributes that are unique to the original object and need to be copied (new memory address)
        object_copy.component_energy_inputs = {placement: {component: {carrier: copy(flow)
                                                                       for carrier, flow in component_dict.items()}
                                                           for component, component_dict in placement_dict.items()}
                                               for placement, placement_dict in self.component_energy_inputs.items()}
        object_copy.component_energy_outputs = {placement: {component: {carrier: copy(flow)
                                                                        for carrier, flow in component_dict.items()}
                                                            for component, component_dict in placement_dict.items()}
                                                for placement, placement_dict in self.component_energy_outputs.items()}

        object_copy.used_potentials = {carrier: copy(flow_profile)
                                       for carrier, flow_profile in self.used_potentials.items()}
        object_copy.system_energy_demand = {carrier: copy(flow_profile)
                                            for carrier, flow_profile in self.system_energy_demand.items()}
        object_copy.heat_rejection = {carrier: copy(flow_profile)
                                      for carrier, flow_profile in self.heat_rejection.items()}
        object_copy.greenhouse_gas_emissions = {carrier: copy(flow_profile)
                                                for carrier, flow_profile in self.greenhouse_gas_emissions.items()}

        object_copy.annual_cost = {carrier: cost for carrier, cost in self.annual_cost.items() }
        object_copy.overall_fitness = {carrier: fitness for carrier, fitness in self.overall_fitness.items()}

        return object_copy

    @staticmethod
    def evaluate_supply_system(capacity_indicators, system_structure, demand_energy_flow, objectives,
                               process_memory=None):
        """
        Wrapper of the 'evaluate' method used in the deap toolbox's register function.
        """
        if process_memory.multiprocessing:
            process_memory.recall_class_variables()

        supply_system = SupplySystem(system_structure=system_structure,
                                     capacity_indicator_vector=capacity_indicators,
                                     demand_energy_flow=demand_energy_flow)
        try:
            supply_system.evaluate()
            fitness = [supply_system.overall_fitness[objective] for objective in objectives]
        except ValueError:
            fitness = None

        return fitness

    def evaluate(self):
        """
        "Evaluate" the supply system by following the steps hereafter:
        1. Build the supply system (corresponding to the capacity indicator vector)
        2. Operate the built supply system.
        3. Evaluate the objective functions for the supply system.
        """
        self.installed_components = self._build_supply_system()
        # operate primary components
        primary_demand_dict = {self.structure.main_final_energy_carrier.code: self.demand_energy_flow}
        remaining_primary_demand_dict = self._draw_from_potentials(primary_demand_dict, reset=True)
        remaining_primary_demand_dict = self._draw_from_infinite_sources(remaining_primary_demand_dict)
        self._perform_water_filling_principle('primary', remaining_primary_demand_dict)
        # operate secondary components
        secondary_demand_dict = self._group_component_flows_by_ec('primary', 'in')
        remaining_secondary_demand_dict = self._draw_from_potentials(secondary_demand_dict)
        remaining_secondary_demand_dict = self._draw_from_infinite_sources(remaining_secondary_demand_dict)
        self._perform_water_filling_principle('secondary', remaining_secondary_demand_dict)
        # operate tertiary components
        component_energy_release_dict = self._group_component_flows_by_ec(['primary', 'secondary'], 'out')
        tertiary_demand_dict = self._release_to_grids_or_env(component_energy_release_dict)
        self._perform_water_filling_principle('tertiary', tertiary_demand_dict)

        system_energy_flows_in = self._group_component_flows_by_ec(['secondary', 'tertiary'], 'in')
        remaining_system_energy_flows_in = self._draw_from_potentials(system_energy_flows_in)
        unavailable_system_energy_flows_in = self._draw_from_infinite_sources(remaining_system_energy_flows_in)

        system_energy_flows_out = self._group_component_flows_by_ec('tertiary', 'out')
        unreleasable_system_energy_flows_out = self._release_to_grids_or_env(system_energy_flows_out)

        self._calculate_greenhouse_gas_emissions()
        self._calculate_cost()

        if unavailable_system_energy_flows_in or unreleasable_system_energy_flows_out:
            raise ValueError('There was an error in operating the supply system. '
                             'Some of the required energy inputs could not be drawn from the available potentials and '
                             'grids or some of the energy outputs could not be released to grids or the environment.')

        objectives = SupplySystem.optimisation_algorithm.objectives

        if 'system_energy_demand' in objectives:
            total_sed = sum([sum(energy) for key, energy in self.system_energy_demand.items()])
            self.overall_fitness['system_energy_demand'] = total_sed
        if 'anthropogenic_heat' in objectives:
            total_heat_rejection = sum([sum(heat) for key, heat in self.heat_rejection.items()])
            self.overall_fitness['anthropogenic_heat'] = total_heat_rejection
        if 'GHG_emissions' in objectives:
            total_ghg_emissions = sum([sum(emissions) for key, emissions in self.greenhouse_gas_emissions.items()])
            self.overall_fitness['GHG_emissions'] = total_ghg_emissions
        if 'cost' in objectives:
            total_cost = sum([cost for key, cost in self.annual_cost.items()])
            self.overall_fitness['cost'] = total_cost

        return self.capacity_indicator_vector

    def _build_supply_system(self):
        """
        Build supply system components based on the supply system structure and the capacity indicators vector.

        If a given component can not be installed because the CONVERSION database does not contain any component of
        the requested type providing the required capacity, the capacity indicator is...:
         1. changed to 0 if the combined power output of the other components in the supply system placement category
            is sufficient, or
         2. set to the minimum available capacity of the component type otherwise.
        """
        for capacity_indicator in self.capacity_indicator_vector.capacity_indicators:

            component_model = capacity_indicator.code
            placement = capacity_indicator.category

            max_capacity_component = self.structure.max_cap_active_components[placement][component_model]
            component_class = type(max_capacity_component)
            capacity_kw = capacity_indicator.value * max_capacity_component.capacity

            try:
                if capacity_kw > 0:
                    self.installed_components[placement][component_model] = \
                        component_class(component_model, placement, capacity_kw)
            except ValueError:
                capacity_indicator.value = 0

        return self.installed_components

    def _group_component_flows_by_ec(self, placements, side):
        """
        Group energy flows into or out of a specified placement category of the supply system by energy carriers.
        Main energy flows of the components are not accounted for in this balance.
        """

        if side == 'in':
            if isinstance(placements, str):
                relevant_energy_flows = [energy_flow
                                         for component_code, energy_flows in
                                         self.component_energy_inputs[placements].items()
                                         for ec_code, energy_flow in energy_flows.items()]
            elif isinstance(placements, list):
                relevant_energy_flows = [energy_flow
                                         for placement in placements
                                         for component_code, energy_flows in
                                         self.component_energy_inputs[placement].items()
                                         for ec_code, energy_flow in energy_flows.items()]
            else:
                raise ValueError('Please indicate a valid placement category or list of placement categories.')
        elif side == 'out':
            if isinstance(placements, str):
                relevant_energy_flows = [energy_flow
                                         for component_code, energy_flows in
                                         self.component_energy_outputs[placements].items()
                                         for ec_code, energy_flow in energy_flows.items()]
            elif isinstance(placements, list):
                relevant_energy_flows = [energy_flow
                                         for placement in placements
                                         for component_code, energy_flows in
                                         self.component_energy_outputs[placement].items()
                                         for ec_code, energy_flow in energy_flows.items()]
            else:
                raise ValueError('Please indicate a valid placement category or list of placement categories.')
        else:
            raise ValueError("Please indicate whether the energy flows into (side='in') or out of (side='out') should "
                             f"be aggregated for the {placements} category of the supply system.")

        grouped_energy_flows = {}
        for energy_flow in relevant_energy_flows:
            ec_code = energy_flow.energy_carrier.code
            if ec_code in grouped_energy_flows.keys():
                grouped_energy_flows[ec_code] += energy_flow
            else:
                grouped_energy_flows[ec_code] = energy_flow

        return grouped_energy_flows

    def _perform_water_filling_principle(self, placement, demand_dict):
        """
        The 'water filling principle' describes a method for activating a set of viable components to meet a
        given demand energy flow. Following this method an activation order is set for the available components and the
        components are activated in a cascading fashion, i.e. the first component is ramped up until it hits its
        maximum capacity, if that is not sufficient to cover the demand the next component in the activation order is
        ramped up ... and so on.
        (Analogously to when a given volume of water is released atop a cascade of water basins filling them up
        one after the other until they spill over into the next lower basin.)
        TODO: Add reference to paper/technical documentation once it's published

        :param placement: category of components in the supply system structure, the demand needs to be met with
        :type placement: str
        :param demand_dict: dictionary of demand energy flows that need to be met, keys are energy carrier codes
        :type demand_dict: dict of <cea.optimization_new.energyFlow>-EnergyFlow class objects
        """

        for ec_code in demand_dict.keys():
            demand = demand_dict[ec_code]

            for component_model in self.structure.activation_order[placement]:
                if not ((component_model in self.structure.component_selection_by_ec[placement][ec_code]) and
                        (component_model in self.installed_components[placement].keys())):
                    continue

                component = self.installed_components[placement][component_model]
                main_energy_flow = demand.cap_at(component.capacity)
                demand = demand - main_energy_flow

                if component.main_energy_carrier.code == main_energy_flow.energy_carrier.code:
                    self.component_energy_inputs[placement][component_model], \
                    self.component_energy_outputs[placement][component_model] = component.operate(main_energy_flow)
                else:
                    auxiliary_component = list(self.structure.max_cap_passive_components[placement]
                                               [component_model].values())[0]  # TODO: change this to allow all passive components to be activated
                    converted_energy_flow = auxiliary_component.operate(main_energy_flow)

                    self.component_energy_inputs[placement][component_model], \
                    self.component_energy_outputs[placement][component_model] = component.operate(converted_energy_flow)

            if not isclose(max(demand.profile), 0, abs_tol=1e-09):
                raise ValueError(f'The installed component capacity was insufficient and demand could not be met. '
                                 f'An additional {max(demand.profile)} kW of capacity to produce '
                                 f'{demand.energy_carrier.mean_qual} {demand.energy_carrier.qual_unit} '
                                 f'{demand.energy_carrier.type} energy ({demand.energy_carrier.subtype}) is required.'
                                 f'\nPlease correct the generation/mutation/mating of your capacity indicator vectors.')

        return self.component_energy_inputs, self.component_energy_outputs

    def _draw_from_potentials(self, required_energy_flows, for_sizing=False, reset=False):
        """
        Check if there are available local energy potentials that can provide the required energy flow.
        """
        if reset:
            self.used_potentials = {}

        if isinstance(required_energy_flows, EnergyFlow):
            required_energy_flows = {required_energy_flows.energy_carrier.code: required_energy_flows}

        remaining_potentials = {ec_code: self.available_potentials[ec_code] - self.used_potentials[ec_code]
                                if ec_code in self.used_potentials.keys() else self.available_potentials[ec_code]
                                for ec_code in self.available_potentials.keys()}

        if for_sizing:
            min_potentials = {ec_code: remaining_potentials[ec_code].profile.min()
                              if ec_code in remaining_potentials.keys() else 0.0
                              for ec_code in required_energy_flows.keys()}
            insufficient_potential = {ec_code: min_potentials[ec_code] < required_energy_flows[ec_code]
                                      for ec_code in min_potentials.keys()}
            new_required_energy_flow = {ec_code: required_energy_flows[ec_code] - min_potentials[ec_code]
                                        for ec_code in required_energy_flows.keys()
                                        if insufficient_potential}
            for ec_code in min_potentials.keys():
                if ec_code in self.used_potentials.keys():
                    self.used_potentials[ec_code] += min_potentials[ec_code]
                elif ec_code in self.available_potentials.keys():
                    self.used_potentials[ec_code] = \
                        EnergyFlow('source', 'secondary', ec_code,
                                   pd.Series([min_potentials[ec_code]] * EnergyFlow.time_frame))
        else:
            usable_potential = {ec_code: remaining_potentials[ec_code].cap_at(required_energy_flows[ec_code].profile)
                                if ec_code in remaining_potentials.keys() else required_energy_flows[ec_code].cap_at(0)
                                for ec_code in required_energy_flows.keys()}
            new_required_energy_flow = {ec_code: required_energy_flows[ec_code] - usable_potential[ec_code]
                                        for ec_code in required_energy_flows.keys()}
            for ec_code in usable_potential.keys():
                if ec_code in self.used_potentials.keys():
                    self.used_potentials[ec_code] += usable_potential[ec_code]
                elif ec_code in self.available_potentials.keys():
                    self.used_potentials[ec_code] = usable_potential[ec_code]

        return new_required_energy_flow

    def _draw_from_infinite_sources(self, required_energy_flows, for_sizing=False):
        """
        Check if there are available external energy sources (e.g. power or gas grid) that can provide the required
        energy flow. If so, remove the respective flows from the dataframe of required energy flows.
        """
        if isinstance(required_energy_flows, EnergyFlow):
            required_energy_flows = {required_energy_flows.energy_carrier.code: required_energy_flows}

        new_required_energy_flow = {ec_code: flow for ec_code, flow in required_energy_flows.items()
                                    if ec_code not in self.structure.infinite_energy_carriers}

        if not for_sizing:
            self._add_to_system_energy_demand(required_energy_flows, self.structure.infinite_energy_carriers)

        return new_required_energy_flow

    def _release_to_grids_or_env(self, energy_flows_to_release, for_sizing=False):
        """
        Check if the energy flow that needs to be released to the environment or the relevant grids can sensibly be
        released.
        """
        if isinstance(energy_flows_to_release, EnergyFlow):
            energy_flows_to_release = {energy_flows_to_release.energy_carrier.code: energy_flows_to_release}

        remaining_energy_flows_to_release = {ec_code: flow for ec_code, flow in energy_flows_to_release.items()
                                             if ec_code not in self.structure.releasable_energy_carriers}

        if not for_sizing:
            if not SupplySystem._ec_releases_to_env:
                SupplySystem._ec_releases_to_env = SupplySystemStructure().releasable_environmental_energy_carriers
            if not SupplySystem._ec_releases_to_grids:
                SupplySystem._ec_releases_to_grids = SupplySystemStructure().releasable_grid_based_energy_carriers

            self._add_to_heat_rejection(energy_flows_to_release, SupplySystem._ec_releases_to_env)
            self._deduct_from_system_energy_demand(energy_flows_to_release, SupplySystem._ec_releases_to_grids)

        return remaining_energy_flows_to_release

    def _add_to_system_energy_demand(self, energy_flow_dict, available_system_energy_carriers):
        """
        Add energy flows to the 'system energy demand' if they consist of one of the available system energy carriers.
        """
        for ec_code, energy_flow in energy_flow_dict.items():
            if ec_code in available_system_energy_carriers:
                if ec_code in self.system_energy_demand.keys():
                    self.system_energy_demand[ec_code] += energy_flow.profile
                else:
                    self.system_energy_demand[ec_code] = energy_flow.profile

        return self.system_energy_demand

    def _deduct_from_system_energy_demand(self, energy_flow_dict, available_system_energy_carriers):
        """
        Remove energy flows from the 'system energy demand'. This is meant to be used to take into account unused
        energy generation of the supply system (e.g. electricity generation of cogen components).
        """
        for ec_code, energy_flow in energy_flow_dict.items():
            if ec_code in available_system_energy_carriers:
                if ec_code in self.system_energy_demand.keys():
                    self.system_energy_demand[ec_code] -= energy_flow.profile
                else:
                    self.system_energy_demand[ec_code] = -energy_flow.profile

        return self.system_energy_demand

    def _add_to_heat_rejection(self, energy_flow_dict, releasable_energy_carriers):
        """
        Add energy flows to the system heat rejection if they consist of one of the releasable energy carriers.
        """
        for ec_code, energy_flow in energy_flow_dict.items():
            if ec_code in releasable_energy_carriers:
                if ec_code in self.heat_rejection.keys():
                    self.heat_rejection[ec_code] += energy_flow.profile
                else:
                    self.heat_rejection[ec_code] = energy_flow.profile

        return self.heat_rejection

    def _calculate_greenhouse_gas_emissions(self):
        """
        Calculate green house gas emissions of all system energy demand flows.
        """

        self.greenhouse_gas_emissions = {ec_code: energy_flow.replace(list(energy_flow[energy_flow<0]), 0)
                                                  * EnergyCarrier.get_unit_ghg(ec_code)
                                         for ec_code, energy_flow in self.system_energy_demand.items()}

        return self.greenhouse_gas_emissions

    def _calculate_cost(self):
        """
        Calculate the total annual cost associated to the supply system. This includes the annualised cost of components
        (investment + operation & maintenance) and the cost of the system energy demand flows.
        """

        annual_component_cost = {}
        for placement, components in self.installed_components.items():
            for component_code, component in components.items():
                if component_code in annual_component_cost.keys():
                    annual_component_cost[component_code] += (component.inv_cost_annual + component.om_fix_cost_annual)
                else:
                    annual_component_cost[component_code] = (component.inv_cost_annual + component.om_fix_cost_annual)

        annual_energy_supply_cost = {ec_code: max(sum(energy_flow), 0) * EnergyCarrier.get_unit_cost(ec_code)
                                     for ec_code, energy_flow in self.system_energy_demand.items()}

        self.annual_cost = {**annual_component_cost, **annual_energy_supply_cost}

        return self.annual_cost

    @staticmethod
    def initialize_class_variables(domain):
        # set supply system optimisation parameters
        selection_algorithm = domain.config.optimization_new.systems_algorithm
        mutation_method = domain.config.optimization_new.systems_mutation_method
        crossover_method = domain.config.optimization_new.systems_crossover_method
        population_size = domain.config.optimization_new.ga_population_size
        number_of_generations = domain.config.optimization_new.ga_number_of_generations
        mut_prob = domain.config.optimization_new.ga_mutation_prob
        cx_prob = domain.config.optimization_new.ga_crossover_prob
        mut_eta = domain.config.optimization_new.ga_mutation_eta
        parallelize_computation = domain.config.general.multiprocessing
        SupplySystem.optimisation_algorithm = GeneticAlgorithm(selection=selection_algorithm,
                                                               mutation=mutation_method,
                                                               crossover=crossover_method,
                                                               population_size=population_size,
                                                               number_of_generations=number_of_generations,
                                                               mut_probability=mut_prob, cx_probability=cx_prob,
                                                               mut_eta=mut_eta, parallelize=parallelize_computation)
