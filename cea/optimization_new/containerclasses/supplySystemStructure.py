"""
SupplySystemStructure Class:
defines what type of components can be installed in each of the supply system's component categories,
specifications of the system structure including:
- types of installed components
- maximum capacities of components
- activation order of the components
- passive components required for base energy carrier conversion

THE SUPPLY SYSTEM STRUCTURE WILL ALWAYS FOLLOW THIS GENERALISED SYSTEM LAYOUT:
 _________       ___________________       _______________       __________       ___________
| source | ---> | secondary/supply | ---> | primary/main | ---> | storage | ---> | consumer |
‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾‾
                                                 ↓
                  ______________       _____________________
                 | environment | <--- | tertiary/rejection |
                 ‾‾‾‾‾‾‾‾‾‾‾‾‾‾       ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"


import warnings
import pandas as pd
from cea.optimization_new.containerclasses.energyCarrier import EnergyCarrier
from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
from cea.optimization_new.component import ActiveComponent, PassiveComponent
from cea.optimization_new.helperclasses.optimization.capacityIndicator import CapacityIndicator, CapacityIndicatorVector


class SupplySystemStructure(object):
    _STANDARD_DH_TEMPERATURE = 60  # °C
    _STANDARD_DC_TEMPERATURE = 10  # °C
    _MIN_NETWORK_TEMPERATURE = 0  # °C
    _MAX_NETWORK_TEMPERATURE = 150  # °C
    _NETWORK_FLUID = 'water'

    _system_type = ''
    _climatic_reference_temperature = None
    _network_temperature = None
    _default_final_energy_carrier = EnergyCarrier.default()
    _infinite_energy_carriers = []
    _releasable_environmental_energy_carriers = []
    _releasable_grid_based_energy_carriers = []
    _active_component_classes = []
    _full_component_activation_order = ()
    initial_network_supply_systems = dict()
    initial_network_supply_systems_composition = {'N1001': {'primary': [], 'secondary': [], 'tertiary': []}}

    def __init__(self, max_supply_flow=EnergyFlow(), available_potentials=None, user_component_selection=None,
                 target_building_or_network=None):
        # set system requirement parameters
        self.maximum_supply = max_supply_flow
        self.main_final_energy_carrier = self.maximum_supply.energy_carrier

        # set energy potential parameters
        if available_potentials:
            self.available_potentials = available_potentials
        else:
            self._available_potentials = {}
        self._used_potentials = {}

        # structure defining parameters
        if user_component_selection:
            self.user_component_selection = user_component_selection
        else:
            self.user_component_selection = {}
        self._activation_order = {'primary': (), 'secondary': (), 'tertiary': ()}
        self._component_selection_by_ec = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self._passive_component_selection = {}
        self._max_cap_active_components = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self._max_cap_passive_components = {'primary': {}, 'secondary': {}, 'tertiary': {}}
        self._dependencies = {'primary': {}, 'secondary': {}, 'tertiary': {}}

        # capacity indicator structure
        self.capacity_indicators = CapacityIndicatorVector()

        # identifier
        self._target = target_building_or_network

    @property
    def system_type(cls):
        return cls._system_type

    @staticmethod
    def get_system_type(new_system_type):
        if new_system_type not in ['DC', 'DH', 'cooling', 'heating']:
            raise TypeError("The indicated system type is invalid. The only two types currently allowed are 'heating'"
                            "and 'cooling'.")
        elif new_system_type in ['DC', 'cooling']:
            return 'cooling'
        else:
            return 'heating'

    @property
    def climatic_reference_temperature(self):
        return self._climatic_reference_temperature

    @staticmethod
    def get_climatic_reference_temperature(new_climatic_reference_temperature):
        if not isinstance(new_climatic_reference_temperature, (float, int)):
            raise TypeError("The climatic reference temperature needs to be a numerical value in °C.")
        else:
            return round(new_climatic_reference_temperature, 1)

    @property
    def network_temperature(self):
        return self._network_temperature

    @staticmethod
    def get_network_temperature(new_network_temperature):
        """ Set the network temperature for the supply system. """

        if new_network_temperature < 0:
            if SupplySystemStructure._system_type == "heating":
                new_network_temperature = SupplySystemStructure._STANDARD_DH_TEMPERATURE
            elif SupplySystemStructure._system_type == "cooling":
                new_network_temperature = SupplySystemStructure._STANDARD_DC_TEMPERATURE

        if not isinstance(new_network_temperature, (float, int)):
            raise TypeError("The network temperature needs to be a numerical value in °C.")

        if SupplySystemStructure._system_type == "heating":
            if not (SupplySystemStructure._climatic_reference_temperature <= new_network_temperature
                    <= SupplySystemStructure._MAX_NETWORK_TEMPERATURE):
                raise ValueError("For district heating networks, the network temperature needs to fall between the"
                                 f"average outdoor temperature {SupplySystemStructure._climatic_reference_temperature}°C"
                                 f" and {SupplySystemStructure._MAX_NETWORK_TEMPERATURE}°C. Please adjust your "
                                 f"configurations accordingly.")
        elif SupplySystemStructure._system_type == "cooling":
            if not (SupplySystemStructure._MIN_NETWORK_TEMPERATURE <= new_network_temperature
                    <= SupplySystemStructure._climatic_reference_temperature):
                raise ValueError("For district cooling networks, the network temperature needs to fall between the"
                                 f"{SupplySystemStructure._MIN_NETWORK_TEMPERATURE}°C and the average outdoor temperature "
                                 f"{SupplySystemStructure._climatic_reference_temperature}°C. Please adjust your configurations "
                                 f"accordingly.")

        return new_network_temperature

    @property
    def default_final_energy_carrier(self):
        return self._default_final_energy_carrier

    @staticmethod
    def get_default_final_energy_carrier(new_default_fec):
        if not isinstance(new_default_fec, EnergyCarrier):
            raise TypeError("The main final energy carrier of the supply system needs to be of type EnergyCarrier.")
        else:
            return new_default_fec

    @property
    def infinite_energy_carriers(self):
        return self._infinite_energy_carriers

    @property
    def releasable_environmental_energy_carriers(self):
        return self._releasable_environmental_energy_carriers

    @property
    def releasable_grid_based_energy_carriers(self):
        return self._releasable_grid_based_energy_carriers

    @property
    def releasable_energy_carriers(self):
        return self._releasable_environmental_energy_carriers + self._releasable_grid_based_energy_carriers

    @property
    def active_component_classes(self):
        return self._active_component_classes

    @property
    def maximum_supply(self):
        return self._maximum_supply

    @maximum_supply.setter
    def maximum_supply(self, new_maximum_supply):
        if isinstance(new_maximum_supply, (int, float)):
            self._maximum_supply = EnergyFlow(input_category='primary', output_category='consumer',
                                              energy_carrier_code=self.default_final_energy_carrier.code,
                                              energy_flow_profile=pd.Series([new_maximum_supply]))
        elif isinstance(new_maximum_supply, EnergyFlow):
            if not new_maximum_supply.energy_carrier:
                self._maximum_supply = EnergyFlow(input_category=None, output_category=None,
                                                  energy_carrier_code=None,
                                                  energy_flow_profile=pd.Series([0.0]))
            elif not (new_maximum_supply.profile.size == 1 and
                      new_maximum_supply.input_category == 'primary' and
                      new_maximum_supply.output_category == 'consumer'):
                warnings.warn("The format of the required maximum supply flow was corrected slightly.")
                self._maximum_supply = EnergyFlow(input_category='primary', output_category='consumer',
                                                  energy_carrier_code=new_maximum_supply.energy_carrier.code,
                                                  energy_flow_profile=pd.Series([new_maximum_supply.profile.max()]))
            else:
                self._maximum_supply = new_maximum_supply
        else:
            raise TypeError("The maximum supply flow needs to be of type 'EnergyFlow' or a numerical value.")

    @property
    def available_potentials(self):
        return self._available_potentials

    @available_potentials.setter
    def available_potentials(self, new_available_potentials):
        if not isinstance(new_available_potentials, dict):
            raise TypeError("The available potentials need to be indicated as a dictionary with energy carrier "
                            "codes as keys.")
        elif not all([isinstance(potential, EnergyFlow) for potential in new_available_potentials.values()]):
            raise TypeError("The indicated energy potentials need to be of type EnergyFlow.")
        else:
            self._available_potentials = new_available_potentials

    @property
    def used_potentials(self):
        return self._used_potentials

    @property
    def user_component_selection(self):
        return self._user_component_selection

    @user_component_selection.setter
    def user_component_selection(self, new_user_component_selection):
        if not isinstance(new_user_component_selection, dict):
            raise TypeError("The user component selection needs be of type 'dict'.")
        elif not all([str(key) in ['primary', 'secondary', 'tertiary'] for key in new_user_component_selection.keys()]):
            raise TypeError("The user component selection needs to be classified in the three component categories:"
                            "'primary', 'secondary' and 'tertiary'")
        elif not all([isinstance(selection, list) for selection in new_user_component_selection.values()]):
            raise TypeError("The user component selection for each component category needs to be of type 'list'.")
        elif not all([component in ActiveComponent.code_to_class_mapping.keys()
                      for component_selection in new_user_component_selection.values()
                      for component in component_selection]):
            raise TypeError("Some of the user selected components (i.e. codes) cannot be found in the components "
                            "database. ")
        else:
            self._user_component_selection = new_user_component_selection

    @property
    def activation_order(self):
        return self._activation_order

    @property
    def component_selection_by_ec(self):
        return self._component_selection_by_ec

    @property
    def passive_component_selection(self):
        return self._passive_component_selection

    @property
    def max_cap_active_components(self):
        return self._max_cap_active_components

    @property
    def max_cap_passive_components(self):
        return self._max_cap_passive_components

    @property
    def target(self):
        return self._target

    @staticmethod
    def _get_infinite_ecs(energy_sources_config):
        """
        Get the codes of all energy carriers which are quasi-infinitely available.
        """
        infinite_energy_carriers = [EnergyCarrier.ambient_thermal_energy_carrier.code]
        if 'power_grid' in energy_sources_config:
            infinite_energy_carriers.extend(EnergyCarrier.get_all_electrical_ecs())
        if 'fossil_fuels' in energy_sources_config:
            infinite_energy_carriers.extend(EnergyCarrier.get_combustible_ecs_of_subtype('fossil'))
        if 'bio_fuels' in energy_sources_config:
            infinite_energy_carriers.extend(EnergyCarrier.get_combustible_ecs_of_subtype('biofuel'))
        return infinite_energy_carriers

    @staticmethod  # TODO: Adapt this method when typical days are introduced
    def _get_releasable_environmental_ecs():
        """
        Get the codes of all energy carriers that can be freely released to the environment.
        """
        typical_air_ec = EnergyCarrier.ambient_thermal_energy_carrier

        if SupplySystemStructure._system_type == 'heating':
            releasable_environmental_ecs = EnergyCarrier.get_thermal_ecs_of_subtype('air')
        elif SupplySystemStructure._system_type == 'cooling':
            releasable_environmental_ecs = EnergyCarrier.get_hotter_thermal_ecs(typical_air_ec, 'air',
                                                                                include_thermal_ec=True)
        else:
            raise ValueError('Make sure the energy system type is set before allocating environmental energy carriers.')

        return releasable_environmental_ecs

    @staticmethod
    def _get_releasable_grid_based_ecs():
        """
        Get the codes of all energy carriers that can be freely released to a grid.
        """
        releasable_grid_based_ecs = EnergyCarrier.get_all_electrical_ecs()

        return releasable_grid_based_ecs

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

    def build(self):
        """
        Select components from the list of available supply system components for each of the placement categories of
        the supply system (i.e. 'primary', 'secondary', 'tertiary') that can meet the maximum demand required of the
        system.
        The selection of all useful components at their maximum useful capacity prescribe the solution space of
        sensible supply systems. This information is therefore saved to define the supply system structure.
        """
        # BUILD PRIMARY COMPONENTS
        # get components that can produce the given system demand
        if self.user_component_selection:
            viable_primary_and_passive_components = {self.maximum_supply.energy_carrier.code:
                                                        self._instantiate_components(
                                                            self.user_component_selection['primary'],
                                                            self.maximum_supply.energy_carrier.code,
                                                            self.maximum_supply.profile.max(),
                                                            'primary', 'consumer')}
        else:
            viable_primary_and_passive_components = {self.maximum_supply.energy_carrier.code:
                                                        self._fetch_viable_components(
                                                            self.maximum_supply.energy_carrier.code,
                                                            self.maximum_supply.profile.max(),
                                                            'primary', 'consumer')}

        # identify dependencies of primary components
        self._determine_dependencies('primary', viable_primary_and_passive_components,
                                     upstream_components=None)

        # operate said components and get the required input energy flows and corresponding output energy flows
        max_primary_demand = {self.maximum_supply.energy_carrier.code: self.maximum_supply}
        max_primary_energy_flows_in, \
        max_primary_energy_flows_out, \
        split_by_primary_component = \
            SupplySystemStructure._extract_max_required_energy_flows(max_primary_demand,
                                                                     viable_primary_and_passive_components)

        # Check if any of the input energy flows can be covered by the energy potential flows
        #   (if so, subtract them from demand)
        remaining_max_primary_energy_flows_in = self._draw_from_potentials(max_primary_energy_flows_in)
        max_secondary_components_demand = self._draw_from_infinite_sources(remaining_max_primary_energy_flows_in)
        max_secondary_components_demand_flow = {ec_code:
                                                    EnergyFlow('secondary', 'primary', ec_code, pd.Series(max_demand))
                                                for ec_code, max_demand in max_secondary_components_demand.items()}

        # BUILD SECONDARY COMPONENTS
        # get the components that can supply the input energy flows to the primary components
        if self.user_component_selection:
            viable_secondary_and_passive_components = {ec_code: self._instantiate_components(
                                                                    self.user_component_selection['secondary'],
                                                                    ec_code, max_flow, 'secondary', 'primary')
                                                       for ec_code, max_flow
                                                       in max_secondary_components_demand.items()}
        else:
            viable_secondary_and_passive_components = {ec_code:
                                                           self._fetch_viable_components(ec_code,
                                                                                         max_flow,
                                                                                         'secondary',
                                                                                         'primary')
                                                       for ec_code, max_flow in max_secondary_components_demand.items()}

        # determine dependencies between secondary and primary components
        self._determine_dependencies('secondary', viable_secondary_and_passive_components,
                                     split_by_primary_component['input'])

        # operate all secondary components and get the required input energy flows and corresponding output energy flows
        max_secondary_energy_flows_in, \
        max_secondary_energy_flows_out, \
        split_by_secondary_component = \
            SupplySystemStructure._extract_max_required_energy_flows(max_secondary_components_demand_flow,
                                                                     viable_secondary_and_passive_components)

        # check if any of the outgoing energy-flows can be absorbed by the environment directly
        max_tertiary_demand_from_primary = self._release_to_grids_or_env(max_primary_energy_flows_out)
        max_tertiary_demand_from_secondary = self._release_to_grids_or_env(max_secondary_energy_flows_out)
        all_main_tertiary_ecs = list(set(list(max_tertiary_demand_from_primary.keys()) +
                                         list(max_tertiary_demand_from_secondary.keys())))
        max_tertiary_components_demand = {}
        max_tertiary_demand_flow = {}
        for ec_code in all_main_tertiary_ecs:
            if ec_code not in max_tertiary_demand_from_primary.keys():
                max_tertiary_components_demand[ec_code] = max_tertiary_demand_from_secondary[ec_code]
                max_tertiary_demand_flow[ec_code] = EnergyFlow('secondary', 'tertiary', ec_code,
                                                               pd.Series(max_tertiary_demand_from_secondary[ec_code]))
            elif ec_code not in max_tertiary_demand_from_secondary.keys():
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
        if self.user_component_selection:
            viable_tertiary_and_passive_cmpts = {ec_code: self._instantiate_components(
                                                            self.user_component_selection['tertiary'],
                                                            ec_code, max_flow, 'tertiary', 'primary')
                                                 for ec_code, max_flow
                                                 in max_tertiary_components_demand.items()}
        else:
            viable_tertiary_and_passive_cmpts = {ec_code:
                                                     self._fetch_viable_components(ec_code,
                                                                                   max_flow,
                                                                                   'tertiary',
                                                                                   'primary or secondary')
                                                 for ec_code, max_flow in max_tertiary_components_demand.items()}

        # determine dependencies between secondary and primary components
        maximum_outputs = (max_primary_energy_flows_out, max_secondary_energy_flows_out)
        shares_of_outputs = (split_by_primary_component, split_by_secondary_component)
        split_by_component = SupplySystemStructure._combine_energy_flow_shares('output', maximum_outputs,
                                                                               shares_of_outputs)
        self._determine_dependencies('tertiary', viable_tertiary_and_passive_cmpts,
                                     split_by_component['output'])

        # operate said components and get the required input energy flows and corresponding output energy flows
        max_tertiary_energy_flows_in, \
        max_tertiary_energy_flows_out, \
        split_by_tertiary_component = \
            SupplySystemStructure._extract_max_required_energy_flows(max_tertiary_demand_flow,
                                                                     viable_tertiary_and_passive_cmpts)

        # check if the necessary *infinite* energy sources and sinks are available (e.g. gas & electricity grids, air, water bodies)
        required_external_secondary_inputs = self._draw_from_potentials(max_secondary_energy_flows_in)
        required_external_tertiary_inputs = self._draw_from_potentials(max_tertiary_energy_flows_in)
        unmet_inputs = {**self._draw_from_infinite_sources(required_external_secondary_inputs),
                        **self._draw_from_infinite_sources(required_external_tertiary_inputs)}

        unreleasable_outputs = {**self._release_to_grids_or_env(max_secondary_energy_flows_out),
                                **self._release_to_grids_or_env(max_tertiary_energy_flows_out)}

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

        # create capacity indicator vector structure
        component_categories = [category for category, components in self.max_cap_active_components.items()
                                for _ in components]
        component_codes = [code for category, components in self.max_cap_active_components.items()
                           for code in components.keys()]
        component_main_ecs = [component.main_energy_carrier.code
                              for category, components in self.max_cap_active_components.items()
                              for code, component in components.items()]
        capacity_indicators_list = [CapacityIndicator(category, code, energy_carrier) for category, code, energy_carrier
                                    in zip(component_categories, component_codes, component_main_ecs)]
        self.capacity_indicators = CapacityIndicatorVector(capacity_indicators_list, self._dependencies)

        return self.capacity_indicators

    def _instantiate_components(self, component_codes, demand_energy_carrier, component_capacity, component_placement,
                                demand_origin):
        """
        Instantiate components taken from list of component codes, that meet a given set of positional requirements,
        i.e. the components:
            a. need to be able to produce a given demand energy carrier
            b. need to fit in the given supply system placement
            c. need to match a given maximum capacity
        """
        passive_components_dict = {}

        fitting_components, components_fitting_after_passive_conversion = self._try_fitting_component_selection(
            component_codes, demand_energy_carrier, component_capacity, component_placement)

        if fitting_components:
            return {'active': fitting_components, 'passive': passive_components_dict}
        elif components_fitting_after_passive_conversion:
            passive_components_dict = SupplySystemStructure._fetch_viable_passive_components(
                components_fitting_after_passive_conversion, component_placement, component_capacity,
                demand_energy_carrier, demand_origin)
            return {'active': components_fitting_after_passive_conversion, 'passive': passive_components_dict}
        else:
            raise ValueError(f"None of the components chosen for the {component_placement} category of the supply "
                             f"system of {self.target} can generate/absorb the required energy carrier "
                             f"{demand_energy_carrier}. Please change the component selection for your supply system.")

    @staticmethod
    def _try_fitting_component_selection(component_codes, demand_energy_carrier, component_capacity,
                                         component_placement):
        """
        Try to fit the component selection into the supply system structure. If the components cannot provide the
        required energy carrier, try to find alternative energy carriers that can be converted into the required
        energy carrier using passive components.
        If that is not possible either, return empty lists.
        """
        fitting_components = []
        components_fitting_after_passive_conversion = []

        for component_code in component_codes:
            # Get component class from mapping (may be None if not found)
            if ActiveComponent.code_to_class_mapping is None:
                raise RuntimeError("Component.initialize_class_variables() must be called before using components")

            component_class = ActiveComponent.code_to_class_mapping.get(component_code)

            # Skip if component class not found or if it's a passive component
            # Passive components need different instantiation parameters
            # and are handled separately by _fetch_viable_passive_components
            if component_class is None or issubclass(component_class, PassiveComponent):
                continue

            component = component_class(component_code, component_placement, component_capacity)
            if component.main_energy_carrier.code == demand_energy_carrier:
                fitting_components.append(component)
            else:
                viable_ecs = SupplySystemStructure._find_convertible_energy_carriers(demand_energy_carrier,
                                                                                     component_placement)
                if component.main_energy_carrier.code in viable_ecs:
                    components_fitting_after_passive_conversion.append(component)

        return fitting_components, components_fitting_after_passive_conversion

    def _fetch_viable_components(self, main_energy_carrier, maximum_demand_energy_flow, component_placement,
                                 demand_origin):
        """
        Get a list of all 'active' components that can generate or absorb a given maximum demand of a given
        energy carrier.
        The components are initialised with a capacity matching the maximum demand and placed in the indicated
        location of the subsystem.
        """
        maximum_demand = maximum_demand_energy_flow

        # fetch active components that can cover the maximum energy demand flow
        viable_active_components_list = \
            SupplySystemStructure._fetch_viable_active_components(main_energy_carrier, maximum_demand,
                                                                  component_placement)

        # if no component models could be initialised successfully, try to find alternative energy sources
        necessary_passive_components = {}
        if not viable_active_components_list:
            viable_active_components_list, \
            necessary_passive_components = \
                SupplySystemStructure._find_alternatives(main_energy_carrier, maximum_demand, component_placement,
                                                         demand_origin)
            if not viable_active_components_list:
                raise Exception(f'The available {component_placement} components cannot provide the energy carrier '
                                f'{main_energy_carrier}, nor any of the viable alternative energy carriers in '
                                f'{self.target}. No adequate supply system can therefore be built. \n'
                                f'Please change your component selection!')

        return {'active': viable_active_components_list, 'passive': necessary_passive_components}

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
        all_active_component_classes = [component_class for component_class in
                                        SupplySystemStructure._active_component_classes
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
        alternative_ecs = SupplySystemStructure._find_convertible_energy_carriers(required_energy_carrier_code,
                                                                                  component_placement)

        # find out if there are active components that can provide any of the alternative energy carriers
        ecs_with_possible_active_components = list(set([ec_code
                                                        for ec_code in alternative_ecs
                                                        for component_class in
                                                        SupplySystemStructure._active_component_classes
                                                        if ec_code in component_class.possible_main_ecs.keys()]))
        if not ecs_with_possible_active_components:
            return [], {}

        # find out if any of the identified active components can provide the required demand
        pot_alternative_active_components = [component
                                             for ec_code in ecs_with_possible_active_components
                                             for component
                                             in SupplySystemStructure._fetch_viable_active_components(ec_code,
                                                                                                      maximum_demand,
                                                                                                      component_placement)]

        # find and dimension passive components that can supply the active components
        required_passive_components = SupplySystemStructure._fetch_viable_passive_components(
            pot_alternative_active_components,
            component_placement,
            maximum_demand,
            required_energy_carrier_code,
            demand_origin)
        alternative_active_components = [active_component
                                         for active_component in pot_alternative_active_components
                                         if active_component.code in required_passive_components.keys()]

        return alternative_active_components, required_passive_components

    @staticmethod
    def _find_convertible_energy_carriers(required_energy_carrier_code, component_placement):
        """
        Find out which alternative energy carriers could potentially be converted into the required energy carrier
        using passive components.
        """
        required_ec_type = EnergyCarrier.from_code(required_energy_carrier_code).type
        if required_ec_type == 'thermal':
            if component_placement == 'tertiary' \
                    or (SupplySystemStructure._system_type == 'cooling' and component_placement == 'primary'):
                convertible_ecs = EnergyCarrier.get_colder_thermal_ecs(required_energy_carrier_code)
            else:
                convertible_ecs = EnergyCarrier.get_hotter_thermal_ecs(required_energy_carrier_code)
        elif required_ec_type == 'electrical':
            convertible_ecs = EnergyCarrier.get_all_other_electrical_ecs(required_energy_carrier_code)
        else:
            raise ValueError(f'There are no ways to convert {required_ec_type} energy carriers using passive '
                             f'components.')
        return convertible_ecs

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
            mean_qual_before = EnergyCarrier.from_code(required_energy_carrier_code).mean_qual

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

        else:  # i.e. active components are used for generation
            placed_before = demand_origin
            placed_after = active_component_placement
            mean_qual_after = EnergyCarrier.from_code(required_energy_carrier_code).mean_qual

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
                            continue
                required_passive_components[active_component.code] = passive_component_list

        return required_passive_components

    @staticmethod
    def _extract_max_required_energy_flows(maximum_energy_flows, viable_active_and_passive_components):
        """
        Operate each component in the list of viable component-objects to output (or absorb) the given main energy flow
        and return the maximum necessary input energy flows and maximum resulting output energy flows.
        (example of component-object - <cea.optimization_new.component.AbsorptionChiller>)
        """
        input_and_output_energy_flows = SupplySystemStructure._operate_components(maximum_energy_flows,
                                                                                  viable_active_and_passive_components)

        # separate input and output energy flows
        input_energy_flow_dicts = {component_code: {ef_code: ef.profile if isinstance(ef, EnergyFlow) else ef
                                                    for ef_code, ef in energy_flows[0].items()}
                                   for component_code, energy_flows in input_and_output_energy_flows.items()}
        output_energy_flow_dicts = {component_code: {ef_code: ef.profile if isinstance(ef, EnergyFlow) else ef
                                                     for ef_code, ef in energy_flows[1].items()}
                                    for component_code, energy_flows in input_and_output_energy_flows.items()}

        # get maximum input and output energy flows of all components combined
        input_energy_flow_requirements = SupplySystemStructure._get_maximum_per_energy_carrier(input_energy_flow_dicts)
        output_energy_flow_requirements = SupplySystemStructure._get_maximum_per_energy_carrier(
            output_energy_flow_dicts)

        # calculate the share each component has in the total input/output energy flow
        split_by_component = {
            'input': {ec_code: {component_code: input_energy_flow_dicts[component_code][ec_code].max() /
                                                input_energy_flow_requirements[ec_code]
                                                if isinstance(input_energy_flow_dicts[component_code][ec_code],
                                                              pd.Series)
                                                else input_energy_flow_dicts[component_code][ec_code] /
                                                     input_energy_flow_requirements[ec_code]
                                for component_code in input_energy_flow_dicts.keys()
                                if ec_code in input_energy_flow_dicts[component_code].keys()}
                      for ec_code in input_energy_flow_requirements.keys()},
            'output': {ec_code: {component_code: output_energy_flow_dicts[component_code][ec_code].max() /
                                                 output_energy_flow_requirements[ec_code]
                                                 if isinstance(output_energy_flow_dicts[component_code][ec_code],
                                                               pd.Series)
                                                 else output_energy_flow_dicts[component_code][ec_code] /
                                                      output_energy_flow_requirements[ec_code]
                                 for component_code in output_energy_flow_dicts.keys()
                                 if ec_code in output_energy_flow_dicts[component_code].keys()}
                       for ec_code in output_energy_flow_requirements.keys()}}

        return input_energy_flow_requirements, output_energy_flow_requirements, split_by_component

    @staticmethod
    def _operate_components(maximum_energy_flows, viable_active_and_passive_components):

        input_and_output_energy_flows = {}

        for main_energy_carrier in maximum_energy_flows.keys():
            main_flow = maximum_energy_flows[main_energy_carrier]
            viable_active_components = viable_active_and_passive_components[main_energy_carrier]['active']
            necessary_passive_components = viable_active_and_passive_components[main_energy_carrier]['passive']

            if necessary_passive_components:
                passive_component_demand_flows = {active_component_code: passive_component[0].operate(main_flow)
                                                  for active_component_code, passive_component in
                                                  necessary_passive_components.items()}
                input_and_output_energy_flows = {component.code:
                                                     component.operate(passive_component_demand_flows[component.code])
                                                 for component in viable_active_components}
            else:
                input_and_output_energy_flows = {component.code: component.operate(main_flow)
                                                 for component in viable_active_components}

        return input_and_output_energy_flows

    @staticmethod
    def _get_maximum_per_energy_carrier(component_flow_dicts):
        """
        Extract maximum flow requirement for each energy carrier from a dictionary of component energy flow requirements
        :param component_flow_dicts: dict of dicts, i.e. {component_code: {energy_carrier_code: energy_flow_profile}}.
        """
        energy_flow_requirements_df = pd.DataFrame([[ec_code, energy_flow.max()]
                                                    if isinstance(energy_flow, pd.Series) else [ec_code, energy_flow]
                                                    for component, energy_flow_dict in component_flow_dicts.items()
                                                    for ec_code, energy_flow in energy_flow_dict.items()],
                                                   columns=['EnergyCarrier', 'PeakDemand'])
        energy_carrier_codes = energy_flow_requirements_df['EnergyCarrier'].unique()
        energy_flow_requirements = {ec_code: energy_flow_requirements_df[
            energy_flow_requirements_df['EnergyCarrier'] == ec_code]['PeakDemand'].max()
                                    for ec_code in energy_carrier_codes}
        return energy_flow_requirements

    def _determine_dependencies(self, category, viable_components_by_ec, upstream_components):
        """
        Match the main energy carriers transferred to a given category with their upstream components that dictate how
        large installed capacity of the viable components in the category needs to be. Also match the upstream
        components' share in the total energy flow provided/absorbed by viable component under peak operating
        conditions. This is used to determine interdependencies between upstream and viable components of the respective
        category and set boundaries for capacity indicator values of the viable components.

                e.g. if a boiler is a viable component of the secondary/supply category of a DC plant, find and match
                all primary cooling components that require the heat the boiler provides (e.g. absorption chillers ACH).
                If ACH1 requires 40% of the heat provided by the boiler and ACH2 requires 60% of the heat provided
                by the boiler, then also match the boiler's heat output with ACH1's and ACH2's respective shares in that
                demand. (all of these relations should already be given by 'upstream_components')

        WARNING: This method only works with 'upstream components' that have linear efficiency functions. If new,
                 non-linear efficiency functions were to be introduced, the dependency factor (share) would need to be
                 updated to:
                        dependency_factor = share * peak_load_efficiency / min_efficiency
        """
        if not upstream_components:
            self._dependencies[category].update({ec: {'components': (),
                                                      'factors': ()}
                                                 for ec in viable_components_by_ec.keys()})
        else:
            self._dependencies[category].update({ec: {'components': tuple([upstream_component
                                                                           for upstream_component
                                                                           in upstream_components[ec].keys()]),
                                                      'factors': tuple([share
                                                                        for share
                                                                        in upstream_components[ec].values()])}
                                                 for ec in viable_components_by_ec.keys()})

    @staticmethod
    def _combine_energy_flow_shares(side = 'output', maximum_flows = (), shares = ()):
        """
        Combine the maximum energy flows of a component with the shares of upstream components that dictate how large
        the component's installed capacity needs to be.
        """
        combined_energy_flow_shares = {'input': {}, 'output': {}}
        all_ec_codes = set([code for max_flows_of_cat in maximum_flows for code in max_flows_of_cat.keys()])
        combined_maximum_flows = {energy_carrier:
                                      sum([max_flows_of_cat[energy_carrier]
                                           if energy_carrier in max_flows_of_cat.keys() else 0
                                           for max_flows_of_cat in maximum_flows])
                                  for energy_carrier in all_ec_codes}

        if side in ['input', 'output']:
            for max_flows_in_cat, shares_in_cat in zip(maximum_flows, shares):
                for ec_code, components_share in shares_in_cat[side].items():
                    if ec_code not in combined_energy_flow_shares[side].keys():
                        combined_energy_flow_shares[side][ec_code] = {component:
                                                                          share * max_flows_in_cat[ec_code] /
                                                                          combined_maximum_flows[ec_code]
                                                                      for component, share in components_share.items()}
                    else:
                        combined_energy_flow_shares[side][ec_code].update({component:
                                                                               share * max_flows_in_cat[ec_code] /
                                                                               combined_maximum_flows[ec_code]
                                                                           for component, share
                                                                           in components_share.items()})
        else:
            raise ValueError('Invalid side argument. Must be either "input" or "output".')

        return combined_energy_flow_shares


    def _draw_from_potentials(self, required_energy_flows, reset=False):
        """
        Check if there are available local energy potentials that can provide the required energy flow.
        """
        if reset:
            self._used_potentials = {}

        if isinstance(required_energy_flows, EnergyFlow):
            required_energy_flows = {required_energy_flows.energy_carrier.code: required_energy_flows}

        remaining_potentials = {ec_code: self.available_potentials[ec_code] - self._used_potentials[ec_code]
                                if ec_code in self._used_potentials.keys() else self.available_potentials[ec_code]
                                for ec_code in self.available_potentials.keys()}

        min_potentials = {ec_code: remaining_potentials[ec_code].profile.min()
                          if ec_code in remaining_potentials.keys() else 0.0
                          for ec_code in required_energy_flows.keys()}
        insufficient_potential = {ec_code: min_potentials[ec_code] < required_energy_flows[ec_code]
                                  for ec_code in min_potentials.keys()}
        new_required_energy_flow = {ec_code: required_energy_flows[ec_code] - min_potentials[ec_code]
                                    for ec_code in required_energy_flows.keys()
                                    if insufficient_potential}
        for ec_code in min_potentials.keys():
            if ec_code in self._used_potentials.keys():
                self._used_potentials[ec_code] += min_potentials[ec_code]
            elif ec_code in self.available_potentials.keys():
                self._used_potentials[ec_code] = \
                    EnergyFlow('source', 'secondary', ec_code,
                               pd.Series([min_potentials[ec_code]] * len(EnergyFlow.time_series)))

        return new_required_energy_flow

    @staticmethod
    def _draw_from_infinite_sources(required_energy_flows):
        """
        Check if there are available external energy sources (e.g. power or gas grid) that can provide the required
        energy flow. If so, remove the respective flows from the dataframe of required energy flows.
        """
        if isinstance(required_energy_flows, EnergyFlow):
            required_energy_flows = {required_energy_flows.energy_carrier.code: required_energy_flows}

        new_required_energy_flow = {ec_code: flow for ec_code, flow in required_energy_flows.items()
                                    if ec_code not in SupplySystemStructure().infinite_energy_carriers}

        return new_required_energy_flow

    @staticmethod
    def _release_to_grids_or_env(energy_flows_to_release):
        """
        Check if the energy flow that needs to be released to the environment or the relevant grids can sensibly be
        released.
        """
        if isinstance(energy_flows_to_release, EnergyFlow):
            energy_flows_to_release = {energy_flows_to_release.energy_carrier.code: energy_flows_to_release}

        remaining_energy_flows_to_release = {ec_code: flow for ec_code, flow in energy_flows_to_release.items()
                                             if ec_code not in SupplySystemStructure().releasable_energy_carriers}

        return remaining_energy_flows_to_release

    def _set_system_structure(self, component_category, viable_active_and_passive_components_dict):
        """
        Set all object variables defining the supply system structure of the chosen component category, based a
        dictionary that list all active components providing each of the required energy carriers and their
        corresponding necessary passive components, i.e.:
            {'EnergyCarrier.code': ([<ActiveComponent_1>, <ActiveComponent_2>],
                                    {'ActiveComponent_1.code': [<PassiveComponent_1>, <PassiveComponent_2>]})
            ...}
        """
        for ec_code, act_and_psv_cmpts in viable_active_and_passive_components_dict.items():
            self._component_selection_by_ec[component_category][ec_code] = [component.code for component in
                                                                            act_and_psv_cmpts['active']]
            self._max_cap_active_components[component_category].update({active_component.code: active_component
                                                                        for active_component
                                                                        in act_and_psv_cmpts['active']})
            self._passive_component_selection.update(act_and_psv_cmpts['passive'])
            self._max_cap_passive_components[component_category].update({active_component:
                                                                             {passive_component.code: passive_component
                                                                              for passive_component
                                                                              in passive_components}
                                                                         for active_component, passive_components
                                                                         in act_and_psv_cmpts['passive'].items()})
        self._activation_order[component_category] = [code
                                                      for component_type in
                                                      SupplySystemStructure._full_component_activation_order
                                                      for code in
                                                      self._max_cap_active_components[component_category].keys()
                                                      if code == component_type]
        return

    @staticmethod
    def initialize_class_variables(domain):
        """
        Depending on the type of network (district cooling or district heating), determine the energy carriers and
        types of components that can be used/installed in different spots of the supply system.
        More specifically, determine which energy carriers and components can be used to:
            A. meet the network's demand (main)
            B. supply necessary inputs to the components of category A
            C. reject 'waste energy' generated by other components in the supply system.

        :param domain: domain for which these potential components and energy carriers need to be defined
        :type domain: <cea.optimization_new.domain>-Domain object
        """
        # Set main energy carrier based on type of network-optimisation
        config = domain.config
        SupplySystemStructure._system_type \
            = SupplySystemStructure.get_system_type(config.optimization_new.network_type)
        SupplySystemStructure._climatic_reference_temperature \
            = SupplySystemStructure.get_climatic_reference_temperature(domain.weather['drybulb_C'].mean())
        SupplySystemStructure._network_temperature \
            = SupplySystemStructure.get_network_temperature(config.optimization_new.network_temperature)
        SupplySystemStructure._default_final_energy_carrier \
            = SupplySystemStructure.get_default_final_energy_carrier(
            EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(
                SupplySystemStructure._NETWORK_FLUID, SupplySystemStructure._network_temperature)))
        SupplySystemStructure._infinite_energy_carriers \
            = SupplySystemStructure._get_infinite_ecs(config.optimization_new.available_energy_sources)
        SupplySystemStructure._releasable_environmental_energy_carriers \
            = SupplySystemStructure._get_releasable_environmental_ecs()
        SupplySystemStructure._releasable_grid_based_energy_carriers \
            = SupplySystemStructure._get_releasable_grid_based_ecs()
        SupplySystemStructure._active_component_classes, \
        SupplySystemStructure._full_component_activation_order \
            = SupplySystemStructure._get_component_priorities(config.optimization_new)
