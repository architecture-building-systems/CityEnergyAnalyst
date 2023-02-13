"""
Subsystem Class:
defines all properties as supply system of a single network or stand-alone building in the DCS, including:
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

GENERALISED SUPPLY SYSTEM LAYOUT:
 _________       ___________________       _______________       __________       ___________
| source | ---> | secondary/supply | ---> | primary/main | ---> | storage | ---> | consumer |
‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾‾
                                                 ↓
                  ______________       _____________________
                 | environment | <--- | tertiary/rejection |
                 ‾‾‾‾‾‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

import random

import pandas as pd
from math import ceil
from cea.optimization_new.energyCarrier import EnergyCarrier
from cea.optimization_new.energyFlow import EnergyFlow
from cea.optimization_new.component import ActiveComponent, PassiveComponent


class SupplySystem(object):
    _system_type = ''
    _active_component_classes = []
    _full_component_activation_order = ()
    _infinite_energy_carriers = []
    _releasable_energy_carriers = []
    _ec_releases_to_grids = []
    _ec_releases_to_env = []

    def __init__(self, demand_energy_flow=None, available_potentials=None):
        if demand_energy_flow is None:
            self.demand_energy_flow = EnergyFlow()
            self._maximum_demand = None
            self._main_final_energy_carrier = EnergyCarrier()
        else:
            self.demand_energy_flow = demand_energy_flow
            self._maximum_demand = EnergyFlow(input_category='primary', output_category='consumer',
                                              energy_carrier_code=demand_energy_flow.energy_carrier.code,
                                              energy_flow_profile=pd.Series(demand_energy_flow.profile.max()))
            self._main_final_energy_carrier = demand_energy_flow.energy_carrier
        if available_potentials is None:
            self.available_potentials = {}
            self.used_potentials = {}
        else:
            self.available_potentials = available_potentials
            self.used_potentials = {}

        # structure defining parameters
        self._activation_order = {'primary': (), 'secondary': (), 'tertiary': ()}
        self._component_selection_by_ec = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self._passive_component_selection = {}
        self._max_cap_active_components = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self._max_cap_passive_components = {'primary': {}, 'secondary': {}, 'tertiary': {}}

        # specific system layout parameters
        self.capacity_indicators = {'primary': [], 'secondary': [], 'tertiary': []}
        self.installed_components = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self.component_energy_inputs = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self.component_energy_outputs = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self.system_energy_demand = {}
        self.heat_rejection = {}
        self.greenhouse_gas_emissions = {}
        self.annual_cost = {}

    @staticmethod
    def _get_infinite_ecs(energy_sources_config):
        """
        Get the codes of all energy carriers which are quasi-infinitely available.
        """
        infinite_energy_carriers = []
        if 'power_grid' in energy_sources_config:
            infinite_energy_carriers.extend(EnergyCarrier.get_all_electrical_ecs())
        if 'fossil_fuels' in energy_sources_config:
            infinite_energy_carriers.extend(EnergyCarrier.get_combustible_ecs_of_subtype('fossil'))
        if 'bio_fuels' in energy_sources_config:
            infinite_energy_carriers.extend(EnergyCarrier.get_combustible_ecs_of_subtype('biofuel'))
        return infinite_energy_carriers

    @staticmethod  # TODO: Adapt this method when typical days are introduced
    def _get_releasable_ecs(domain, system_type):
        """
        Get the codes of all energy carriers that can be freely released to a grid or the environment.
        """
        avrg_yearly_temp = domain.weather['drybulb_C'].mean()
        typical_air_ec = EnergyCarrier.temp_to_thermal_ec('air', avrg_yearly_temp)

        if system_type == 'heating':
            releasable_environmental_ecs = EnergyCarrier.get_colder_thermal_ecs(typical_air_ec, 'air')
        elif system_type == 'cooling':
            releasable_environmental_ecs = EnergyCarrier.get_hotter_thermal_ecs(typical_air_ec, 'air')
        else:
            raise ValueError('Make sure the energy system type is set before allocating environmental energy carriers.')

        releasable_grid_based_ecs = EnergyCarrier.get_all_electrical_ecs()

        releasable_ecs = releasable_environmental_ecs + releasable_grid_based_ecs

        return releasable_ecs

    @staticmethod
    def _get_component_priorities(optimisation_config):
        """
        Get the chosen component priorities from the optimisation configurations.
        """
        active_components_list = []
        component_types_list = []

        for technology in optimisation_config.cooling_components:
            active_components_list.append(ActiveComponent.get_subclass(technology))
            component_types_list.append(ActiveComponent.get_types(technology))

        for technology in optimisation_config.heating_components:
            active_components_list.append(ActiveComponent.get_subclass(technology))
            component_types_list.append(ActiveComponent.get_types(technology))

        for technology in optimisation_config.heat_rejection_components:
            active_components_list.append(ActiveComponent.get_subclass(technology))
            component_types_list.append(ActiveComponent.get_types(technology))

        component_types_tuple = tuple([type_code
                                       for component_types in component_types_list
                                       for type_code in component_types])

        return active_components_list, component_types_tuple

    def _set_system_structure(self, component_category, viable_active_and_passive_components_dict):
        """
        Set all object variables defining the supply system structure of the chosen component category, based a
        dictionary that list all active components providing each of the required energy carriers and their
        corresponding necessary passive components, i.e.:
            {'EnergyCarrier.code': ([<ActiveComponent_1>, <ActiveComponent_2>],
                                    {'ActiveComponent_1.code': [<PassiveComponent_1>, <PassiveComponent_2>]})
            ...}
        """
        for ec_code, ter_and_psv_cmpts in viable_active_and_passive_components_dict.items():
            self._component_selection_by_ec[component_category][ec_code] = [component.code for component in
                                                                            ter_and_psv_cmpts[0]]
            self._max_cap_active_components[component_category].update({active_component.code: active_component
                                                                        for active_component in ter_and_psv_cmpts[0]})
            self._passive_component_selection.update(ter_and_psv_cmpts[1])
            self._max_cap_passive_components[component_category].update({passive_component.code: passive_component
                                                                         for active_component, passive_components
                                                                         in ter_and_psv_cmpts[1].items()
                                                                         for passive_component in passive_components})
        self._activation_order[component_category] = [code
                                                      for component_type in
                                                      SupplySystem._full_component_activation_order
                                                      for code in
                                                      self._max_cap_active_components[component_category].keys()
                                                      if code == component_type]
        return

    # TODO: shift all the supply system builder methods to a separate script (outside of SupplySystem-class)
    #       if they cannot be reused for system operation
    @staticmethod
    def _fetch_viable_components(main_energy_carrier, maximum_demand_energy_flow, component_placement, demand_origin):
        """
        Get a list of all 'active' components that can generate or absorb a given maximum demand of a given
        energy carrier.
        The components are initialised with a capacity matching the maximum demand and placed in the indicated
        location of the subsystem.
        """
        maximum_demand = maximum_demand_energy_flow

        # fetch active components that can cover the maximum energy demand flow
        viable_active_components_list = \
            SupplySystem._fetch_viable_active_components(main_energy_carrier, maximum_demand, component_placement)

        # if not component models could be initialised successfully, try to find alternative energy sources
        necessary_passive_components = {}
        if not viable_active_components_list:
            viable_active_components_list, \
            necessary_passive_components = \
                SupplySystem._find_alternatives(main_energy_carrier, maximum_demand, component_placement, demand_origin)
            if not viable_active_components_list:
                raise Exception(f'The available {component_placement} components cannot provide the energy carrier '
                                f'{main_energy_carrier}, nor any of the viable alternative energy carriers. '
                                f'No adequate supply system can therefore be built. \n'
                                f'Please change your component selection!')

        return viable_active_components_list, necessary_passive_components

    @staticmethod
    def _fetch_viable_active_components(main_energy_carrier, maximum_demand, component_placement):
        """
        Get a list of all 'active' components that can generate or absorb a given maximum demand of a given
        energy carrier.
        The components are initialised with a capacity matching the maximum demand and placed in the indicated
        location of the subsystem.
        """
        if component_placement == 'primary' or component_placement == 'secondary':
            main_side = 'output'  # i.e. component is used for generating a given energy carrier
        elif component_placement == 'tertiary':
            main_side = 'input'  # i.e. component is used for absorbing a given energy carrier
        else:
            raise ValueError(f'Active components can not viably be placed in the following location: '
                             f'{component_placement}')
        # find component models (codes) that can generate/absorb the requested energy carrier
        all_active_component_classes = [component_class for component_class in SupplySystem._active_component_classes
                                        if component_class.main_side == main_side]
        viable_component_models = [[component_class, component_class.possible_main_ecs[main_energy_carrier]]
                                   for component_class in all_active_component_classes
                                   if main_energy_carrier in component_class.possible_main_ecs.keys()]

        # try initialising component models with a capacity equal to the peak demand
        viable_components_list = []
        for component, component_models in viable_component_models:
            for model_code in component_models:
                try:
                    viable_components_list.append(component(model_code, component_placement, maximum_demand))
                except ValueError:
                    pass

        return viable_components_list

    @staticmethod
    def _find_alternatives(required_energy_carrier_code, maximum_demand, component_placement, demand_origin):
        """
        Check if there are components that can provide the requested energy carrier after passive transformation,
        i.e. temperature change using a heat exchanger or change in voltage using an electrical transformer.
        """
        # find out which alternative energy carriers could potentially be converted into the required energy carrier
        #   using passive components
        required_ec_type = EnergyCarrier(required_energy_carrier_code).type
        if required_ec_type == 'thermal':
            if component_placement == 'tertiary' \
                    or (SupplySystem._system_type == 'cooling' and component_placement == 'primary'):
                alternative_ecs = EnergyCarrier.get_colder_thermal_ecs(required_energy_carrier_code)
            else:
                alternative_ecs = EnergyCarrier.get_hotter_thermal_ecs(required_energy_carrier_code)
        elif required_ec_type == 'electrical':
            alternative_ecs = EnergyCarrier.get_all_other_electrical_ecs(required_energy_carrier_code)
        else:
            raise ValueError(f'There are no ways to convert {required_ec_type} energy carriers using passive '
                             f'components.')

        # find out if there are active components that can provide any of the alternative energy carriers
        ecs_with_possible_active_components = list(set([ec_code
                                                        for ec_code in alternative_ecs
                                                        for component_class in SupplySystem._active_component_classes
                                                        if ec_code in component_class.possible_main_ecs.keys()]))
        if not ecs_with_possible_active_components:
            return [], {}

        # find out if any of the identified active components can provide the required demand
        pot_alternative_active_components = [component
                                             for ec_code in ecs_with_possible_active_components
                                             for component
                                             in SupplySystem._fetch_viable_active_components(ec_code,
                                                                                             maximum_demand,
                                                                                             component_placement)]

        # find and dimension passive components that can supply the active components
        required_passive_components = SupplySystem._fetch_viable_passive_components(pot_alternative_active_components,
                                                                                    component_placement,
                                                                                    maximum_demand,
                                                                                    required_energy_carrier_code,
                                                                                    demand_origin)
        alternative_active_components = [active_component
                                         for active_component in pot_alternative_active_components
                                         if active_component.code in required_passive_components.keys()]

        return alternative_active_components, required_passive_components

    @staticmethod
    def _fetch_viable_passive_components(active_components_to_feed, active_component_placement, maximum_demand,
                                         required_energy_carrier_code, demand_origin):
        """
        Get the passive components for a list of active components. The premise of this function is that the
        main energy carriers generated/absorbed by the active components can only satisfy the original demand if
        passive components are used for conversion into the desired energy carrier.
        """
        active_component_ecs = list(set([component.main_energy_carrier.code
                                         for component in active_components_to_feed]))

        # find passive components that can provide the energy carriers generated/absorbed by the active components
        passive_components_for_ec = {alternative_ec:
                                         {component_class:
                                              component_class.conversion_matrix[alternative_ec][
                                                  required_energy_carrier_code]}
                                     for component_class in PassiveComponent.__subclasses__()
                                     for alternative_ec in active_component_ecs
                                     if alternative_ec in component_class.conversion_matrix.columns}

        # try to instantiate appropriate passive components for each the active components
        required_passive_components = {}

        if active_component_placement == 'tertiary':  # i.e. active components are used for absorption/rejection
            placed_before = active_component_placement
            placed_after = demand_origin
            mean_qual_after = EnergyCarrier(required_energy_carrier_code).mean_qual
            for active_component in active_components_to_feed:
                passive_component_list = []
                for passive_component_class, component_models \
                        in passive_components_for_ec[active_component.main_energy_carrier.code].items():
                    for component_model in component_models:
                        try:
                            passive_component_list.append(
                                passive_component_class(component_model, placed_before, placed_after, maximum_demand,
                                                        active_component.main_energy_carrier.mean_qual,
                                                        mean_qual_after))
                        except ValueError:
                            pass
                required_passive_components[active_component.code] = passive_component_list

        else:  # i.e. active components are used for generation
            placed_before = demand_origin
            placed_after = active_component_placement
            mean_qual_before = EnergyCarrier(required_energy_carrier_code).mean_qual

            for active_component in active_components_to_feed:
                passive_component_list = []
                for passive_component_class, component_models \
                        in passive_components_for_ec[active_component.main_energy_carrier.code].items():
                    for component_model in component_models:
                        try:
                            passive_component_list.append(
                                passive_component_class(component_model, placed_before, placed_after, maximum_demand,
                                                        mean_qual_before,
                                                        active_component.main_energy_carrier.mean_qual))
                        except ValueError:
                            pass
                required_passive_components[active_component.code] = passive_component_list

        return required_passive_components

    @staticmethod
    def _extract_max_required_energy_flows(main_flow, viable_components):
        """
        Operate each component in the list of viable component-objects to output (or absorb) the given main energy flow
        and return the maximum necessary input energy flows and maximum resulting output energy flows.
        (example of component-object - <cea.optimization_new.component.AbsorptionChiller>)
        """
        input_and_output_energy_flows = [component.operate(main_flow) for component in viable_components]
        input_energy_flow_dicts = [input_ef for input_ef, output_ef in input_and_output_energy_flows]
        output_energy_flow_dicts = [output_ef for input_ef, output_ef in input_and_output_energy_flows]

        input_energy_flow_requirements = SupplySystem._get_maximum_per_energy_carrier(input_energy_flow_dicts)
        output_energy_flow_requirements = SupplySystem._get_maximum_per_energy_carrier(output_energy_flow_dicts)

        return input_energy_flow_requirements, output_energy_flow_requirements

    @staticmethod
    def _get_maximum_per_energy_carrier(list_of_code_and_flow_dicts):
        """
        Extract maximum flow requirement for each energy carrier in a list of {energy_carrier_code: energy_flow}-dicts.
        """
        energy_flow_requirements_df = pd.DataFrame([[ec_code, energy_flow.profile.max()]
                                                    if isinstance(energy_flow, EnergyFlow) else [ec_code, energy_flow]
                                                    for energy_flow_dict in list_of_code_and_flow_dicts
                                                    for ec_code, energy_flow in energy_flow_dict.items()],
                                                   columns=['EnergyCarrier', 'PeakDemand'])
        energy_carrier_codes = energy_flow_requirements_df['EnergyCarrier'].unique()
        energy_flow_requirements = {ec_code: energy_flow_requirements_df[
            energy_flow_requirements_df['EnergyCarrier'] == ec_code]['PeakDemand'].max()
                                    for ec_code in energy_carrier_codes}
        return energy_flow_requirements

    def draw_from_potentials(self, required_energy_flows, for_sizing=False, reset=False):
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

    def draw_from_infinite_sources(self, required_energy_flows, for_sizing=False):
        """
        Check if there are available external energy sources (e.g. power or gas grid) that can provide the required
        energy flow. If so, remove the respective flows from the dataframe of required energy flows.
        """
        if isinstance(required_energy_flows, EnergyFlow):
            required_energy_flows = {required_energy_flows.energy_carrier.code: required_energy_flows}

        new_required_energy_flow = {ec_code: flow for ec_code, flow in required_energy_flows.items()
                                    if ec_code not in SupplySystem._infinite_energy_carriers}

        if not for_sizing:
            self.add_to_system_energy_demand(required_energy_flows, SupplySystem._infinite_energy_carriers)

        return new_required_energy_flow

    def release_to_grids_or_env(self, energy_flows_to_release, for_sizing=False):
        """
        Check if the energy flow that needs to be released to the environment or the relevant grids can sensibly be
        released.
        """
        if isinstance(energy_flows_to_release, EnergyFlow):
            energy_flows_to_release = {energy_flows_to_release.energy_carrier.code: energy_flows_to_release}

        remaining_energy_flows_to_release = {ec_code: flow for ec_code, flow in energy_flows_to_release.items()
                                             if ec_code not in SupplySystem._releasable_energy_carriers}

        if not for_sizing:
            if not SupplySystem._ec_releases_to_env:
                SupplySystem._ec_releases_to_env = [ec_code for ec_code in SupplySystem._releasable_energy_carriers
                                                    if not (ec_code in SupplySystem._infinite_energy_carriers)]
            if not SupplySystem._ec_releases_to_grids:
                SupplySystem._ec_releases_to_grids = [ec_code for ec_code in SupplySystem._releasable_energy_carriers
                                                      if ec_code in SupplySystem._infinite_energy_carriers]

            self.add_to_heat_rejection(energy_flows_to_release, SupplySystem._ec_releases_to_env)
            self.deduct_from_system_energy_demand(energy_flows_to_release, SupplySystem._ec_releases_to_grids)

        return remaining_energy_flows_to_release

    def build_system_structure(self):
        """
        Select components from the list of available supply system components for each of the placement categories of
        the supply system (i.e. 'primary', 'secondary', 'tertiary') that can meet the maximum demand required of the
        system.
        The selection of all useful components at their maximum useful capacity prescribe the solution space of
        sensible supply systems. This information is therefore saved to define the supply system structure.
        """
        # get maximum consumer demand
        if not self._maximum_demand:
            self._maximum_demand = self.demand_energy_flow.profile.max()

        # BUILD PRIMARY COMPONENTS
        # get components that can produce the given system demand
        viable_primary_and_passive_components = {self._main_final_energy_carrier.code:
                                                    SupplySystem._fetch_viable_components(
                                                        self._maximum_demand.energy_carrier.code,
                                                        self._maximum_demand.profile.max(),
                                                        'primary', 'consumer')}

        # operate said components and get the required input energy flows and corresponding output energy flows
        viable_primary_components = viable_primary_and_passive_components[self._main_final_energy_carrier.code][0]
        max_primary_energy_flows_in, \
        max_primary_energy_flows_out = SupplySystem._extract_max_required_energy_flows(self._maximum_demand,
                                                                                       viable_primary_components)

        # Check if any of the input energy flows can be covered by the energy potential flows
        #   (if so, subtract them from demand)
        remaining_max_primary_energy_flows_in = self.draw_from_potentials(max_primary_energy_flows_in,
                                                                          for_sizing=True)
        max_secondary_components_demand = self.draw_from_infinite_sources(remaining_max_primary_energy_flows_in,
                                                                          for_sizing=True)
        max_secondary_components_demand_flow = {ec_code:
                                                    EnergyFlow('secondary', 'primary', ec_code, pd.Series(max_demand))
                                                for ec_code, max_demand in max_secondary_components_demand.items()}

        # BUILD SECONDARY COMPONENTS
        # get the components that can supply the input energy flows to the primary components
        viable_secondary_and_passive_components = {ec_code: SupplySystem._fetch_viable_components(ec_code,
                                                                                                  max_flow,
                                                                                                  'secondary',
                                                                                                  'primary')
                                                   for ec_code, max_flow in max_secondary_components_demand.items()}

        # operate all secondary components and get the required input energy flows and corresponding output energy flows
        max_secondary_energy_flows = \
            [SupplySystem._extract_max_required_energy_flows(max_secondary_components_demand_flow[ec_code],
                                                             act_and_psv_components[0])
             for ec_code, act_and_psv_components in viable_secondary_and_passive_components.items()]
        max_secondary_energy_flows_in = SupplySystem._get_maximum_per_energy_carrier(
            [max_energy_flows_in for max_energy_flows_in, max_energy_flows_out in max_secondary_energy_flows])
        max_secondary_energy_flows_out = SupplySystem._get_maximum_per_energy_carrier(
            [max_energy_flows_out for max_energy_flows_in, max_energy_flows_out in max_secondary_energy_flows])

        # check if any of the outgoing energy-flows can be absorbed by the environment directly
        max_tertiary_demand_from_primary = self.release_to_grids_or_env(max_primary_energy_flows_out,
                                                                        for_sizing=True)
        max_tertiary_demand_from_secondary = self.release_to_grids_or_env(max_secondary_energy_flows_out,
                                                                          for_sizing=True)
        all_main_tertiary_ecs = list(set(list(max_tertiary_demand_from_primary.keys()) +
                                         list(max_tertiary_demand_from_secondary.keys())))
        max_tertiary_components_demand = {}
        max_tertiary_demand_flow = {}
        for ec_code in all_main_tertiary_ecs:
            if not (ec_code in max_tertiary_demand_from_primary.keys()):
                max_tertiary_components_demand[ec_code] = max_tertiary_demand_from_secondary[ec_code]
                max_tertiary_demand_flow[ec_code] = EnergyFlow('secondary', 'tertiary', ec_code,
                                                               pd.Series(max_tertiary_demand_from_secondary[ec_code]))
            elif not (ec_code in max_tertiary_demand_from_secondary.keys()):
                max_tertiary_components_demand[ec_code] = max_tertiary_demand_from_primary[ec_code]
                max_tertiary_demand_flow[ec_code] = EnergyFlow('primary', 'tertiary', ec_code,
                                                               pd.Series(max_tertiary_demand_from_primary[ec_code]))
            else:
                max_tertiary_components_demand[ec_code] = max_tertiary_demand_from_primary[ec_code] + \
                                                          max_tertiary_demand_from_secondary[ec_code]
                max_tertiary_demand_flow[ec_code] = EnergyFlow('primary or secondary', 'tertiary', ec_code,
                                                               pd.Series(max_tertiary_demand_from_primary[ec_code] +
                                                                         max_tertiary_demand_from_secondary[ec_code]))

        # BUILD TERTIARY COMPONENTS
        # sum up output energy flows of primary and secondary components and find components that can reject them
        #   (i.e. tertiary components)
        viable_tertiary_and_passive_cmpts = {ec_code: SupplySystem._fetch_viable_components(ec_code,
                                                                                            max_flow,
                                                                                            'tertiary',
                                                                                            'primary or secondary')
                                             for ec_code, max_flow in max_tertiary_components_demand.items()}

        # operate said components and get the required input energy flows and corresponding output energy flows
        max_tertiary_energy_flows = \
            [SupplySystem._extract_max_required_energy_flows(max_tertiary_demand_flow[ec_code],
                                                             act_and_psv_components[0])
             for ec_code, act_and_psv_components in viable_tertiary_and_passive_cmpts.items()]
        max_tertiary_energy_flows_in = SupplySystem._get_maximum_per_energy_carrier(
            [max_energy_flows_in for max_energy_flows_in, max_energy_flows_out in max_tertiary_energy_flows])
        max_tertiary_energy_flows_out = SupplySystem._get_maximum_per_energy_carrier(
            [max_energy_flows_out for max_energy_flows_in, max_energy_flows_out in max_tertiary_energy_flows])

        # check if the necessary *infinite* energy sources and sinks are available (e.g. gas & electricity grids, air, water bodies)
        required_external_secondary_inputs = self.draw_from_potentials(max_secondary_energy_flows_in, for_sizing=True)
        required_external_tertiary_inputs = self.draw_from_potentials(max_tertiary_energy_flows_in, for_sizing=True)
        unmet_inputs = {**self.draw_from_infinite_sources(required_external_secondary_inputs, for_sizing=True),
                        **self.draw_from_infinite_sources(required_external_tertiary_inputs, for_sizing=True)}

        unreleasable_outputs = {**self.release_to_grids_or_env(max_secondary_energy_flows_out, for_sizing=True),
                                **self.release_to_grids_or_env(max_tertiary_energy_flows_out, for_sizing=True)}

        if unmet_inputs:
            raise ValueError(f'The following energy carriers could potentially not be supplied to the supply system, '
                             f'the selected system structure is therefore infeasible: '
                             f'{list(unmet_inputs.keys())}')
        elif unreleasable_outputs:
            raise ValueError(f'The following energy carriers could potentially not be released to a grid or the '
                             f'environment, the selected system structure is therefore infeasible: '
                             f'{list(unreleasable_outputs.keys())}')

        # save supply system structure in object variables
        self._set_system_structure('primary', viable_primary_and_passive_components)
        self._set_system_structure('secondary', viable_secondary_and_passive_components)
        self._set_system_structure('tertiary', viable_tertiary_and_passive_cmpts)

        # create capacity indicator vector
        self.capacity_indicators['primary'] = [0] * len(self._max_cap_active_components['primary'])
        self.capacity_indicators['secondary'] = [0] * len(self._max_cap_active_components['secondary'])
        self.capacity_indicators['tertiary'] = [0] * len(self._max_cap_active_components['tertiary'])

        return self.capacity_indicators

    def optimize_subsystem(self):
        """
        Optimise the supply system with the following iterate process hereafter:
        TODO: fill in the optimisation algorithm specifics
        1. Build the supply system (corresponding to the capacity indicator vector)
        2. Operate the built supply system.
        3. Evaluate the objective functions for the supply system.
        """
        self.capacity_indicators = self.generate_capacity_indicators(method='random')
        self.installed_components = self.build_supply_system()
        # operate primary components
        primary_demand_dict = {self._main_final_energy_carrier.code: self.demand_energy_flow}
        self.perform_water_filling_principle('primary', primary_demand_dict)
        # operate secondary components
        secondary_demand_dict = self.group_component_flows_by_ec('primary', 'in')
        self.perform_water_filling_principle('secondary', secondary_demand_dict)
        # operate tertiary components
        component_energy_release_dict = self.group_component_flows_by_ec(['primary', 'secondary'], 'out')
        tertiary_demand_dict = self.release_to_grids_or_env(component_energy_release_dict)
        self.perform_water_filling_principle('tertiary', tertiary_demand_dict)

        system_energy_flows_in = self.group_component_flows_by_ec(['secondary', 'tertiary'], 'in')
        remaining_system_energy_flows_in = self.draw_from_potentials(system_energy_flows_in)
        unavailable_system_energy_flows_in = self.draw_from_infinite_sources(remaining_system_energy_flows_in)

        system_energy_flows_out = self.group_component_flows_by_ec('tertiary', 'out')
        unreleasable_system_energy_flows_out = self.release_to_grids_or_env(system_energy_flows_out)

        self.calculate_greenhouse_gas_emissions()
        self.calculate_cost()

        if unavailable_system_energy_flows_in or unreleasable_system_energy_flows_out:
            raise ValueError('There was an error in operating the supply system. '
                             'Some of the required energy inputs could not be drawn from the available potentials and '
                             'grids or some of the energy outputs could not be released to grids or the environment.')

        return self.capacity_indicators

    def build_supply_system(self):
        """
        Build supply system based on the supply system structure and the capacity indicators vector.
        """
        for placement in self.capacity_indicators.keys():
            ind_counter = 0
            for component_model in self._activation_order[placement]:
                max_capacity_component = self._max_cap_active_components[placement][component_model]
                component_class = type(max_capacity_component)
                capacity_kW = self.capacity_indicators[placement][ind_counter] * max_capacity_component.capacity

                try:
                    self.installed_components[placement][component_model] = \
                        component_class(component_model, placement, capacity_kW)
                except ValueError:
                    if sum(self.capacity_indicators[placement]) - \
                            self.capacity_indicators[placement][ind_counter] < 1:
                        min_model_capacity = ActiveComponent.get_smallest_capacity(component_class, component_model)
                        new_cap_indicator = ceil(min_model_capacity / max_capacity_component.capacity * 100) / 100
                        self.capacity_indicators[placement][component_model] = new_cap_indicator
                        capacity_kW = self.capacity_indicators[placement][ind_counter] * max_capacity_component.capacity
                        self.installed_components[placement][component_model] = \
                            component_class(component_model, placement, capacity_kW)
                    else:
                        self.capacity_indicators[placement][ind_counter] = 0

                ind_counter += 1

        return self.installed_components

    def generate_capacity_indicators(self, method='random'):
        """
        Generate a new capacity indicator vector randomly.
        """
        if method == 'random':
            for placement in self.capacity_indicators.keys():
                self.capacity_indicators[placement] = [random.randint(0, 100) / 100
                                                       for _ in self.capacity_indicators[placement]]

        for placement in self.capacity_indicators.keys():
            if sum(self.capacity_indicators[placement]) < 1:
                while sum(self.capacity_indicators[placement]) < 1:
                    self.capacity_indicators[placement] = [random.randint(0, 100) / 100
                                                           for _ in self.capacity_indicators[placement]]

        return self.capacity_indicators

    def group_component_flows_by_ec(self, placements, side):
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
                raise ValueError(f'Please indicate a valid placement category or list of placement categories.')
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
                raise ValueError(f'Please indicate a valid placement category or list of placement categories.')
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

    def perform_water_filling_principle(self, placement, demand_dict):
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
        remaining_demand_dict = self.draw_from_potentials(demand_dict, reset=True)
        remaining_demand_dict = self.draw_from_infinite_sources(remaining_demand_dict)

        for ec_code in remaining_demand_dict.keys():
            demand = remaining_demand_dict[ec_code]

            for component_model in self._activation_order[placement]:
                if not ((component_model in self._component_selection_by_ec[placement][ec_code]) and
                        (component_model in self.installed_components[placement].keys())):
                    continue

                component = self.installed_components[placement][component_model]
                main_energy_flow = demand.cap_at(component.capacity)
                demand = demand - main_energy_flow

                if component.main_energy_carrier.code == main_energy_flow.energy_carrier.code:
                    self.component_energy_inputs[placement][component_model], \
                    self.component_energy_outputs[placement][component_model] = component.operate(main_energy_flow)
                else:
                    auxiliary_component = self._max_cap_passive_components[placement][component_model][0]  # TODO: change this to allow all passive components to be activated
                    self.component_energy_inputs[placement][auxiliary_component.code], \
                    self.component_energy_outputs[placement][auxiliary_component.code] \
                        = auxiliary_component.operate(main_energy_flow)

                    if (max(self.component_energy_inputs[placement][auxiliary_component.code]) > 0) and \
                            (max(self.component_energy_inputs[placement][auxiliary_component.code]) == 0):
                        converted_energy_flow = self.component_energy_inputs[placement][auxiliary_component.code]
                    elif (max(self.component_energy_inputs[placement][auxiliary_component.code]) == 0) and \
                            (max(self.component_energy_inputs[placement][auxiliary_component.code]) > 0):
                        converted_energy_flow = self.component_energy_inputs[placement][auxiliary_component.code]
                    else:
                        raise ValueError(f'The conversion of the energy carrier {main_energy_flow.energy_carrier}, '
                                         f'for the use in a component of type {component.code} in the primary category '
                                         f'of a supply system failed. The supply system can therefore not be created.')

                    self.component_energy_inputs[placement][component_model], \
                    self.component_energy_outputs[placement][component_model] = component.operate(converted_energy_flow)

        return self.component_energy_inputs, self.component_energy_outputs

    def add_to_system_energy_demand(self, energy_flow_dict, available_system_energy_carriers):
        """
        Add energy flows to the 'system energy demand' if they consist of one of the available system energy carriers.
        """
        for ec_code, energy_flow in energy_flow_dict.items():
            if ec_code in available_system_energy_carriers:
                if ec_code in self.system_energy_demand.keys():
                    self.system_energy_demand[ec_code] += energy_flow.profile.sum()
                else:
                    self.system_energy_demand[ec_code] = energy_flow.profile.sum()

        return self.system_energy_demand

    def deduct_from_system_energy_demand(self, energy_flow_dict, available_system_energy_carriers):
        """
        Remove energy flows from the 'system energy demand'. This is meant to be used to take into account unused
        energy generation of the supply system (e.g. electricity generation of cogen components).
        """
        for ec_code, energy_flow in energy_flow_dict.items():
            if ec_code in available_system_energy_carriers:
                if ec_code in self.system_energy_demand.keys():
                    self.system_energy_demand[ec_code] -= energy_flow.profile.sum()
                else:
                    self.system_energy_demand[ec_code] = -energy_flow.profile.sum()

        return self.system_energy_demand

    def add_to_heat_rejection(self, energy_flow_dict, releasable_energy_carriers):
        """
        Add energy flows to the system heat rejection if they consist of one of the releasable energy carriers.
        """
        for ec_code, energy_flow in energy_flow_dict.items():
            if ec_code in releasable_energy_carriers:
                if ec_code in self.heat_rejection.keys():
                    self.heat_rejection[ec_code] += energy_flow.profile.sum()
                else:
                    self.heat_rejection[ec_code] = energy_flow.profile.sum()

        return self.heat_rejection

    def calculate_greenhouse_gas_emissions(self):
        """
        Calculate green house gas emissions of all system energy demand flows.
        """

        self.greenhouse_gas_emissions = {ec_code: energy_flow * EnergyCarrier.get_unit_ghg(ec_code)
                                         for ec_code, energy_flow in self.system_energy_demand.items()}

        return self.greenhouse_gas_emissions

    def calculate_cost(self):
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

        annual_energy_supply_cost = {ec_code: energy_flow * EnergyCarrier.get_unit_cost(ec_code)
                                     for ec_code, energy_flow in self.system_energy_demand.items()}

        self.annual_cost = {**annual_component_cost, **annual_energy_supply_cost}

        return self.annual_cost

    @staticmethod
    def initialize_class_variables(domain):
        """
        Depending on the type of network (district cooling or district heating), determine the energy carriers and
        types of components that can be used/installed in different spots of the supply system.
        More specifically, determine which energy carriers and components can be used to:
            A. meet the network's demand (main)
            B. supply necessary inputs to the components of category A
            C. reject 'waste energy' generated by other components in the supply system.

        :param domain: domain these potential components and energy carriers need to be defined for
        :type domain: <cea.optimization_new.domain>-Domain object
        """
        # Set main energy carrier based on type of network-optimisation
        config = domain.config
        network_type = config.optimization_new.network_type
        if network_type == 'DH':
            SupplySystem._main_final_energy_carrier = EnergyCarrier('T60W')
            SupplySystem._system_type = 'heating'
        elif network_type == 'DC':
            SupplySystem._main_final_energy_carrier = EnergyCarrier('T10W')
            SupplySystem._system_type = 'cooling'
        else:
            raise ValueError("The only accepted values for the network type are 'DH' and 'DC'.")

        SupplySystem._infinite_energy_carriers = SupplySystem._get_infinite_ecs(config.optimization_new.
                                                                                available_energy_sources)
        SupplySystem._releasable_energy_carriers = SupplySystem._get_releasable_ecs(domain,
                                                                                    SupplySystem._system_type)
        SupplySystem._active_component_classes, \
        SupplySystem._full_component_activation_order = SupplySystem._get_component_priorities(config.optimization_new)
