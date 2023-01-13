"""
This Component Class defines all properties of individual supply system components in the DCS.

 Properties include:
- the placement of components in the supply system (primary, secondary, tertiary or storage)
- the component's accepted input and output energy carriers
- the conversion efficiencies (inputs- and outputs related to main energy carriers)
- the sizing of the component
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

# imports
# standard libraries
import pandas as pd
from math import log
# third party libraries
# other files (modules) of this project
from cea.optimization_new.energyCarrier import EnergyCarrier
from cea.optimization_new.energyFlow import EnergyFlow
from cea.analysis.costs.equations import calc_capex_annualized
from cea.technologies.chiller_vapor_compression import calc_VCC_const
from cea.technologies.chiller_absorption import calc_ACH_const
from cea.technologies.direct_expansion_units import calc_AC_const
from cea.technologies.boiler import calc_boiler_const
from cea.technologies.cogeneration import calc_cogen_const
from cea.technologies.heatpumps import calc_HP_const
from cea.technologies.cooling_tower import calc_CT_const


class Component(object):
    """
    This is a class that represents supply system components of district cooling systems

    :param data_base_tab: name of the database tab in the conversions-database that corresponds to selected component
    :type data_base_tab: str
    :param model_code: code of the selected component model
    :type model_code: str
    :param capacity: thermal capacity of the component
    :type capacity: float
    :param place_in_supply_system: conceptual placement of the component within the supply system
                                   ('primary': direct heating or cooling generation,
                                    'secondary': energy supply for primary components,
                                    'tertiary': components for waste heat rejection,
                                    'storage': thermal storage components)
    :type place_in_supply_system: str
    """
    _components_database = None
    _model_complexity = None

    def __init__(self, data_base_tab,  model_code, capacity, place_in_supply_system):
        self._model_data = self._extract_model_data(data_base_tab, model_code, capacity)
        self._cost_params = self._extract_model_cost_parameters(self._model_data)

        self.code = model_code
        self.technology = ' '.join([part.capitalize() for part in data_base_tab.split('_')])
        self.type = self._model_data['type'].values[0]  # given by working principle (only 1 code is installed for each type per component)
        self.placement = place_in_supply_system  # primary (main cooling or heating), secondary (supply of primary) or tertiary (waste heat rejection)
        self.capacity = capacity
        self.main_energy_carrier = EnergyCarrier()
        self.input_energy_carriers = []
        self.output_energy_carriers = []
        self.inv_cost, self.inv_cost_annual, self.om_fix_cost_annual = self.calculate_cost()

    @staticmethod
    def initialize_class_variables(domain):
        """ Fetch components database from file and save it as a class variable (dict of pd.DataFrames)"""
        Component._components_database = pd.read_excel(domain.locator.get_database_conversion_systems_new(), None)
        Component._model_complexity = domain.config.optimization_new.component_efficiency_model_complexity
        AbsorptionChiller.initialize_subclass_variables(Component._components_database)
        VapourCompressionChiller.initialize_subclass_variables(Component._components_database)
        AirConditioner.initialize_subclass_variables(Component._components_database)
        Boiler.initialize_subclass_variables(Component._components_database)
        CogenPlant.initialize_subclass_variables(Component._components_database)
        HeatPump.initialize_subclass_variables(Component._components_database)
        CoolingTower.initialize_subclass_variables(Component._components_database)
        HeatExchanger.initialize_subclass_variables(Component._components_database)

    @staticmethod
    def _extract_model_data(data_base_tab, model_code, capacity):
        """ Extract component code from database that matches the type and capacity requirements. """
        component_database = Component._components_database[data_base_tab]
        vcc_type_data = component_database[component_database['code'] == model_code]
        adequate_component_models = vcc_type_data[vcc_type_data['cap_min'] <= capacity]
        selected_component_model = adequate_component_models[adequate_component_models['cap_max'] > capacity]
        if not len(selected_component_model.index) > 0:
            raise ValueError(f'The selected component specs: \n'
                             f' - code: {model_code} \n'
                             f' - capacity: {capacity} \n'
                             f'could not be found in the {data_base_tab} tab of the conversion systems database.')
        return selected_component_model

    @staticmethod
    def _extract_model_cost_parameters(model_data):
        """ Extract investment cost code parameters from the code data and store them in a dict."""
        cost_parameters = {'a': model_data['a'].values[0],
                           'b': model_data['b'].values[0],
                           'c': model_data['c'].values[0],
                           'd': model_data['d'].values[0],
                           'e': model_data['e'].values[0],
                           'lifetime': model_data['LT_yr'].values[0],
                           'om_share': model_data['O&M_%'].values[0],
                           'int_rate': model_data['IR_%'].values[0]}
        return cost_parameters

    def _check_operational_requirements(self, main_energy_flow):
        """ check if the component can output the main energy flow as requested """
        if not main_energy_flow.energy_carrier.code == self.main_energy_carrier.code:
            raise TypeError(f'The {self.technology} ({self.code}) can only output {self.main_energy_carrier.code}. '
                            f'The requested output energy carrier is {main_energy_flow.energy_carrier.code}.')
        if (main_energy_flow.profile > self.capacity).any():
            raise ValueError(f'The {self.technology} ({self.code}) can only output a maximum of {self.capacity} W. '
                             f'Requested output: {max(main_energy_flow.profile)} W.')

    def operate(self, main_energy_flow):
        """ placeholder for subclass operational behaviour to output/reject the main energy flow """
        input_energy_flows = [EnergyFlow()]
        output_energy_flows = [EnergyFlow()]
        return input_energy_flows, output_energy_flows

    def calculate_cost(self):
        """ placeholder for subclass investment cost functions """
        capex_USD = self._cost_params['a'] + \
                         self._cost_params['b'] * self.capacity ** self._cost_params['c'] + \
                         (self._cost_params['d'] + self._cost_params['e'] * self.capacity) * log(self.capacity)

        capex_a_USD = calc_capex_annualized(capex_USD, self._cost_params['int_rate'], self._cost_params['lifetime'])
        opex_a_fix_USD = capex_USD * self._cost_params['om_share']

        return capex_USD, capex_a_USD, opex_a_fix_USD


class AbsorptionChiller(Component):

    _possible_main_ecs = None

    def __init__(self, ach_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__('absorption_chillers', ach_model_code, capacity, placement)
        # initialise subclass attributes
        self.minimum_COP = self._model_data['min_eff_rating'].values[0]
        self.aux_power_share = self._model_data['aux_power'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_evap_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_gen_design'].values[0])),
             EnergyCarrier(EnergyCarrier.volt_to_electrical_ec(self._model_data['V_power_supply'].values[0]))]
        self.output_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_cond_design'].values[0]))]

    def operate(self, cooling_out):
        """
        Operate the absorption chiller, so that it generates the targeted amount of cooling. The operation is modeled
        according to the overall component general efficiency code complexity.

        :param cooling_out: Targeted outgoing cooling energy flow (i.e. heat extracted from the chilled water loop)
        :type cooling_out: <cea.optimization_new.energyFlow>-EnergyFlow object

        :return input_energy_flows: Heat and auxiliary power required to output the targeted amount of cooling
        :rtype input_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        :return output_energy_flows: Waste heat rejected to the cold water loop to output the targeted amount of cooling
        :rtype output_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        """
        self._check_operational_requirements(cooling_out)

        # initialize energy flows
        heat_in = EnergyFlow('secondary', self.placement, self.input_energy_carriers[0].code)
        electricity_in = EnergyFlow('secondary', self.placement, self.input_energy_carriers[1].code)
        waste_heat_out = EnergyFlow(self.placement, 'tertiary', self.output_energy_carriers[0].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            heat_in.profile, electricity_in.profile, waste_heat_out.profile = self._constant_efficiency_operation(cooling_out)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        # reformat outputs to dicts
        input_energy_flows = {self.input_energy_carriers[0].code: heat_in,
                              self.input_energy_carriers[1].code: electricity_in}
        output_energy_flows = {self.output_energy_carriers[0].code: waste_heat_out}

        return input_energy_flows, output_energy_flows

    def _constant_efficiency_operation(self, cooling_demand):
        """ Operate absorption chiller assuming a constant COP. """
        heat_flow, \
        electricity_flow, \
        waste_heat_flow = calc_ACH_const(cooling_demand.profile, self.minimum_COP, self.aux_power_share)
        return heat_flow, electricity_flow, waste_heat_flow

    @staticmethod
    def initialize_subclass_variables(components_database):
        """
        Fetch possible main energy carriers of absorption chillers from the database and save the list as a new
        class variable.
        """
        evaporator_temperatures = components_database['absorption_chillers']['T_evap_design'].unique()
        AbsorptionChiller._possible_main_ecs = [EnergyCarrier.temp_to_thermal_ec('water', temp) for temp
                                                in evaporator_temperatures]


class VapourCompressionChiller(Component):

    _possible_main_ecs = None

    def __init__(self, vcc_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__('vapor_compression_chillers', vcc_model_code, capacity, placement)
        # initialise subclass attributes
        self.minimum_COP = self._model_data['min_eff_rating'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_evap_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.volt_to_electrical_ec(self._model_data['V_power_supply'].values[0]))]
        self.output_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_cond_design'].values[0]))]

    def operate(self, cooling_out):
        """
        Operate the vapor compression chiller, so that it generates the targeted amount of cooling. The operation is
        modeled according to the chosen general component efficiency code complexity.

        :param cooling_out: Targeted outgoing cooling energy flow (i.e. heat extracted from the chilled water loop)
        :type cooling_out: <cea.optimization_new.energyFlow>-EnergyFlow object

        :return input_energy_flows: Power supply required to output the targeted amount of cooling
        :rtype input_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        :return output_energy_flows: Waste heat rejected to the cold water loop to output the targeted amount of cooling
        :rtype output_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        """
        self._check_operational_requirements(cooling_out)

        # initialize energy flows
        electricity_in = EnergyFlow('secondary', self.placement, self.input_energy_carriers[0].code)
        waste_heat_out = EnergyFlow(self.placement, 'tertiary', self.output_energy_carriers[0].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            electricity_in.profile, waste_heat_out.profile = self._constant_efficiency_operation(cooling_out)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        # reformat outputs to dicts
        input_energy_flows = {self.input_energy_carriers[0].code: electricity_in}
        output_energy_flows = {self.output_energy_carriers[0].code: waste_heat_out}

        return input_energy_flows, output_energy_flows

    def _constant_efficiency_operation(self, cooling_demand):
        """ Operate vapor compression chiller assuming a constant COP. """
        electricity_flow, waste_heat_flow = calc_VCC_const(cooling_demand.profile, self.minimum_COP)
        return electricity_flow, waste_heat_flow

    @staticmethod
    def initialize_subclass_variables(components_database):
        """
        Fetch possible main energy carriers of vapor compression chillers from the database and save the list as a new
        class variable.
        """
        evaporator_temperatures = components_database['vapor_compression_chillers']['T_evap_design'].unique()
        VapourCompressionChiller._possible_main_ecs = [EnergyCarrier.temp_to_thermal_ec('water', temp) for temp
                                                       in evaporator_temperatures]


class AirConditioner(Component):

    _possible_main_ecs = None

    def __init__(self, ac_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__('unitary_air_conditioners', ac_model_code, capacity, placement)
        # initialise subclass attributes
        self.minimum_COP = self._model_data['rated_COP_seasonal'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_air_indoor_rating'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.volt_to_electrical_ec(self._model_data['V_power_supply'].values[0]))]
        self.output_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_air_outdoor_rating'].values[0]))]

    def operate(self, cooling_out):
        """
        Operate the unitary air conditioner, so that it generates the targeted amount of cooling. The operation is
        modeled according to the chosen general component efficiency code complexity.

        :param cooling_out: Targeted outgoing cooling energy flow (i.e. heat extracted from air)
        :type cooling_out: <cea.optimization_new.energyFlow>-EnergyFlow object

        :return input_energy_flows: Power supply required to output the targeted amount of cooling
        :rtype input_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        :return output_energy_flows: Waste heat rejected to the cold water loop to output the targeted amount of cooling
        :rtype output_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        """
        self._check_operational_requirements(cooling_out)

        # initialize energy flows
        electricity_in = EnergyFlow('secondary', self.placement, self.input_energy_carriers[0].code)
        waste_heat_out = EnergyFlow(self.placement, 'tertiary', self.output_energy_carriers[0].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            electricity_in.profile, waste_heat_out.profile = self._constant_efficiency_operation(cooling_out)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        # reformat outputs to dicts
        input_energy_flows = {self.input_energy_carriers[0].code: electricity_in}
        output_energy_flows = {self.output_energy_carriers[0].code: waste_heat_out}

        return input_energy_flows, output_energy_flows

    def _constant_efficiency_operation(self, cooling_demand):
        """ Operate unitary air conditioner assuming a constant COP. """
        electricity_flow, waste_heat_flow = calc_AC_const(cooling_demand.profile, self.minimum_COP)
        return electricity_flow, waste_heat_flow

    @staticmethod
    def initialize_subclass_variables(components_database):
        """
        Fetch possible main energy carriers of unitary air conditioners from the database and save the list as a new
        class variable.
        """
        indoor_air_temperatures = components_database['unitary_air_conditioners']['T_air_indoor_rating'].unique()
        AirConditioner._possible_main_ecs = [EnergyCarrier.temp_to_thermal_ec('water', temp) for temp
                                             in indoor_air_temperatures]


class Boiler(Component):

    _possible_main_ecs = None

    def __init__(self, boiler_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__('boilers', boiler_model_code, capacity, placement)
        # initialise subclass attributes
        self.min_thermal_eff = self._model_data['min_eff_rating'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_water_out_rating'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier(self._model_data['fuel_code'].values[0])]
        self.output_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_flue_gas_design'].values[0]))]

    def operate(self, heating_out):
        """
        Operate the boiler, so that it produces the targeted amount of heat. The operation is modeled according to
        the chosen general component efficiency code complexity.

        :param heating_out: Targeted heat produced by the boiler
        :type heating_out: <cea.optimization_new.energyFlow>-EnergyFlow object

        :return input_energy_flows: Total heat of combustion of the fuel used to produce the targeted heat output
        :rtype input_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        :return output_energy_flows: Total amount of heat contained in the rejected flue gas
        :rtype output_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        """
        self._check_operational_requirements(heating_out)

        # initialize energy flows
        fuel_in = EnergyFlow('source', self.placement, self.input_energy_carriers[0].code)
        waste_heat_out = EnergyFlow(self.placement, 'environment', self.output_energy_carriers[0].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            fuel_in.profile, waste_heat_out.profile = self._constant_efficiency_operation(heating_out)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        # reformat outputs to dicts
        input_energy_flows = {self.input_energy_carriers[0].code: fuel_in}
        output_energy_flows = {self.output_energy_carriers[0].code: waste_heat_out}

        return input_energy_flows, output_energy_flows

    def _constant_efficiency_operation(self, heating_load):
        """ Operate boiler assuming a constant thermal efficiency rating. """
        fuel_flow, waste_heat_flow = calc_boiler_const(heating_load.profile, self.min_thermal_eff)
        return fuel_flow, waste_heat_flow

    @staticmethod
    def initialize_subclass_variables(components_database):
        """
        Fetch possible main energy carriers of boilers from the database and save the list as a new class
        variable.
        """
        hot_water_temperatures = components_database['boilers']['T_water_out_rating'].unique()
        Boiler._possible_main_ecs = [EnergyCarrier.temp_to_thermal_ec('water', temp) for temp
                                     in hot_water_temperatures]


class CogenPlant(Component):

    _possible_main_ecs = None

    def __init__(self, cogen_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__('cogeneration_plants', cogen_model_code, capacity, placement)
        # initialise subclass attributes
        self.thermal_eff = self._model_data['therm_eff_design'].values[0]
        self.electrical_eff = self._model_data['elec_eff_design'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_water_out_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier(self._model_data['fuel_code'].values[0])]
        self.output_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.volt_to_electrical_ec(self._model_data['V_power_out_design'].values[0])),
             EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_flue_gas_design'].values[0]))]

    def operate(self, heating_out):
        """
        Operate the cogeneration plant, whereby the targeted heating output dictates the operating point of the plant.
        The electrical output is simply given by that operating point. The operation is modeled according to
        the chosen general component efficiency code complexity.

        :param heating_out: Targeted heat produced by the cogeneration plant
        :type heating_out: <cea.optimization_new.energyFlow>-EnergyFlow object

        :return input_energy_flows: Total electrical power produced by the combined heat and power plant,
        :rtype input_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        :return output_energy_flows: Total amount of heat contained in the rejected flue gas
        :rtype output_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        """
        self._check_operational_requirements(heating_out)

        # initialize energy flows
        fuel_in = EnergyFlow('source', self.placement, self.input_energy_carriers[0].code)
        electricity_out = EnergyFlow(self.placement, 'primary', self.input_energy_carriers[0].code)
        waste_heat_out = EnergyFlow(self.placement, 'environment', self.output_energy_carriers[0].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            fuel_in.profile, \
            electricity_out.profile, \
            waste_heat_out.profile = self._constant_efficiency_operation(heating_out)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        # reformat outputs to dicts
        input_energy_flows = {self.input_energy_carriers[0].code: fuel_in}
        output_energy_flows = {self.output_energy_carriers[0].code: electricity_out,
                               self.output_energy_carriers[1].code: waste_heat_out}

        return input_energy_flows, output_energy_flows

    def _constant_efficiency_operation(self, heating_load):
        """ Operate cogeneration plant assuming constant thermal and electrical efficiency ratings. """
        fuel_flow, \
        electricity_flow, \
        waste_heat_flow = calc_cogen_const(heating_load.profile, self.thermal_eff, self.electrical_eff)
        return fuel_flow, electricity_flow, waste_heat_flow

    @staticmethod
    def initialize_subclass_variables(components_database):
        """
        Fetch possible main energy carriers of cogeneration plants from the database and save the list as a new class
        variable.
        """
        hot_water_temperatures = components_database['cogeneration_plants']['T_water_out_design'].unique()
        Boiler._possible_main_ecs = [EnergyCarrier.temp_to_thermal_ec('water', temp) for temp
                                     in hot_water_temperatures]


class HeatPump(Component):

    _possible_main_ecs = None

    def __init__(self, hp_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__('heat_pumps', hp_model_code, capacity, placement)
        # initialise subclass attributes
        self.minimum_COP = self._model_data['min_eff_rating_seasonal'].values[0]
        self.thermal_ec_subtype_condenser_side = self._model_data['medium_cond_side'].values[0]
        self.thermal_ec_subtype_evaporator_side = self._model_data['medium_evap_side'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier(EnergyCarrier.temp_to_thermal_ec(self.thermal_ec_subtype_condenser_side,
                                                           self._model_data['T_cond_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.temp_to_thermal_ec(self.thermal_ec_subtype_evaporator_side,
                                                            self._model_data['T_evap_design'].values[0])),
             EnergyCarrier(EnergyCarrier.volt_to_electrical_ec(self._model_data['V_power_supply'].values[0]))]

    def operate(self, heating_load):
        """
        Operate the heat pump, so that it meets the targeted heating load. The operation is modeled according to the
        chosen general component efficiency code complexity.

        :param heating_load: Targeted outgoing heating energy flow
        :type heating_load: <cea.optimization_new.energyFlow>-EnergyFlow object

        :return input_energy_flows: Heat flow taken from the environment (earth, water or air) and power supply required
                                    to operate the heat pump (i.e. accomplish heat transfer)
        :rtype input_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        """
        self._check_operational_requirements(heating_load)

        # initialize energy flows
        ambient_heat_in = EnergyFlow('secondary', self.placement, self.input_energy_carriers[0].code)
        electricity_in = EnergyFlow('secondary', self.placement, self.input_energy_carriers[1].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            ambient_heat_in.profile, electricity_in.profile = self._constant_efficiency_operation(heating_load)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        # reformat outputs to dicts
        input_energy_flows = {self.input_energy_carriers[0].code: ambient_heat_in,
                              self.input_energy_carriers[1].code: electricity_in}
        output_energy_flows = {}

        return input_energy_flows, output_energy_flows

    def _constant_efficiency_operation(self, heating_demand):
        """ Operate heat pump assuming a constant COP. """
        ambient_heat_flow, electricity_flow = calc_HP_const(heating_demand.profile, self.minimum_COP)
        return ambient_heat_flow, electricity_flow

    @staticmethod
    def initialize_subclass_variables(components_database):
        """
        Fetch possible main energy carriers of heat pumps from the database and save the list as a new class variable.
        """
        heat_pumps_db = components_database['heat_pumps']
        water_heating_heat_pumps = heat_pumps_db[heat_pumps_db['medium_cond_side'] == 'water']
        air_heating_heat_pumps = heat_pumps_db[heat_pumps_db['medium_cond_side'] == 'air']

        water_loop_temperatures = water_heating_heat_pumps['T_cond_design'].unique()
        indoor_air_temperatures = air_heating_heat_pumps['T_cond_design'].unique()

        water_energy_carriers = [EnergyCarrier.temp_to_thermal_ec('water', temp) for temp in water_loop_temperatures]
        air_energy_carriers = [EnergyCarrier.temp_to_thermal_ec('air', temp) for temp in indoor_air_temperatures]
        HeatPump._possible_main_ecs = water_energy_carriers + air_energy_carriers


class CoolingTower(Component):

    _possible_main_ecs = None

    def __init__(self, ct_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__('cooling_towers', ct_model_code, capacity, placement)
        # initialise subclass attributes
        self.aux_power_share = self._model_data['aux_power'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_water_in_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.volt_to_electrical_ec(self._model_data['V_power_supply'].values[0]))]
        self.output_energy_carriers = \
            [EnergyCarrier(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_air_in_design'].values[0]))]

    def operate(self, heat_rejection):
        """
        Operate the cooling tower, so that it rejects the targeted amount of heat. The operation is modeled according to
        the chosen general component efficiency code complexity.

        :param heat_rejection: Targeted heat rejection from the cooling tower's water loop
        :type heat_rejection: <cea.optimization_new.energyFlow>-EnergyFlow object

        :return input_energy_flows: Power supply required to reject the targeted amount of heat
        :rtype input_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        :return output_energy_flows: Total amount of anthropogenic heat rejected to the environment
        :rtype output_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        """
        self._check_operational_requirements(heat_rejection)

        # initialize energy flows
        electricity_in = EnergyFlow('secondary', self.placement, self.input_energy_carriers[0].code)
        anthropogenic_heat_out = EnergyFlow(self.placement, 'environment', self.output_energy_carriers[0].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            electricity_in.profile, anthropogenic_heat_out.profile = self._constant_efficiency_operation(heat_rejection)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        # reformat outputs to dicts
        input_energy_flows = {self.input_energy_carriers[0].code: electricity_in}
        output_energy_flows = {self.output_energy_carriers[0].code: anthropogenic_heat_out}

        return input_energy_flows, output_energy_flows

    def _constant_efficiency_operation(self, heat_rejection_load):
        """ Operate cooling tower assuming a constant electrical efficiency rating. """
        electricity_flow, anthropogenic_heat_out = calc_CT_const(heat_rejection_load.profile, self.aux_power_share)
        return electricity_flow, anthropogenic_heat_out

    @staticmethod
    def initialize_subclass_variables(components_database):
        """
        Fetch possible main energy carriers of cooling towers from the database and save the list as a new class
        variable.
        """
        water_loop_temperatures = components_database['cooling_towers']['T_water_in_design'].unique()
        CoolingTower._possible_main_ecs = [EnergyCarrier.temp_to_thermal_ec('water', temp) for temp
                                           in water_loop_temperatures]


class HeatExchanger(Component):

    _possible_main_ecs = None

    def __init__(self, he_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__('heat_exchangers', he_model_code, capacity, placement)
        # initialise subclass attributes
        self.max_operating_temp = self._model_data['T_max_operating'].values[0]
        self.min_operating_temp = self._model_data['T_min_operating'].values[0]
        self.medium_in = self._model_data['medium_in'].values[0]
        self.medium_out = self._model_data['medium_out'].values[0]

    def operate(self, heat_transfer, heat_source_temp=None, heat_sink_temp=None):
        """
        Operate the heat exchanger, so that it transfers the targeted amount of heat. The operation is modeled according
        to the chosen general component efficiency code complexity.

        :param heat_transfer: Targeted heat transfer through the heat exchanger
        :type heat_transfer: <cea.optimization_new.energyFlow>-EnergyFlow object
        :param heat_source_temp: Temperature level of the heat source, assumed to be constant throughout operation
        :type heat_source_temp: int, float
        :param heat_sink_temp: Temperature level of the heat sink, assumed to be constant throughout operation
        :type heat_sink_temp: int, float

        :return input_energy_flows: Thermal energy flow required to absorb the targeted amount of heat from a heat
                                    source (only when heat exchanger is used as a primary or secondary component)
        :rtype input_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        :return output_energy_flows: Thermal energy flow required to reject the targeted amount of heat (only when the
                                     heat exchanger is operated as a tertiary component)
        :rtype output_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        """
        if not self.main_energy_carrier.code:
            self._set_energy_carriers(heat_transfer, heat_source_temp, heat_sink_temp)
        self._check_operational_requirements(heat_transfer)

        # initialize energy flows
        heat_in = EnergyFlow()
        heat_out = EnergyFlow()
        if self.placement == 'primary':
            heat_in = EnergyFlow('secondary', self.placement, self.input_energy_carriers[0].code)
        elif self.placement == 'secondary':
            heat_in = EnergyFlow('source', self.placement, self.input_energy_carriers[0].code)
        elif self.placement == 'tertiary':
            heat_out = EnergyFlow(self.placement, 'environment', self.output_energy_carriers[0].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            if self.placement in ['primary', 'secondary']:
                heat_in.profile = self._constant_efficiency_operation(heat_transfer)
            elif self.placement == 'tertiary':
                heat_out.profile = self._constant_efficiency_operation(heat_transfer)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        # reformat outputs to dicts
        input_energy_flows = {}
        output_energy_flows = {}
        if self.placement in ['primary', 'secondary']:
            input_energy_flows = {self.input_energy_carriers[0].code: heat_in}
        elif self.placement == 'tertiary':
            output_energy_flows = {self.output_energy_carriers[0].code: heat_out}

        return input_energy_flows, output_energy_flows

    @staticmethod
    def _constant_efficiency_operation(heat_transfer):
        """
        Operate heat exchanger assuming constant operating conditions, i.e. heat_in = heat_out.
        (Since we assume that heat exchanger incur negligible losses)
        """

        return heat_transfer.profile

    def _set_energy_carriers(self, heat_transfer, heat_source_temp, heat_sink_temp):
        """
        This method checks if the heat exchanger is used in an appropriate position in the supply system and
        allocates main, input and output energy flows according to the heat exchangers mode of operation,
        i.e. heat absorption or heat rejection.
        """
        if (heat_source_temp is not None) and (heat_sink_temp is None):  # heat absorption mode
            if not (self.placement in ['primary', 'secondary']):
                raise ValueError('Providing a heat source for the heat exchanger would indicate that it is meant to '
                                 'draw the indicated heat transfer flow from that heat source. The heat exchanger '
                                 f"cannot sensibly be placed in the '{self.placement}' component placement under "
                                 'this mode of operation.')
            thermal_ec_hot_side = EnergyCarrier(EnergyCarrier.temp_to_thermal_ec(self.medium_in, heat_source_temp))
            thermal_ec_cold_side = heat_transfer.energy_carrier
            self._check_he_model_requirements(thermal_ec_hot_side, thermal_ec_cold_side)
            self.main_energy_carrier = thermal_ec_cold_side
            self.input_energy_carriers = [thermal_ec_hot_side]
            self.output_energy_carriers = []
        elif (heat_source_temp is None) and (heat_sink_temp is not None):  # heat rejection mode
            if not (self.placement in ['tertiary']):
                raise ValueError('Providing a heat sink for the heat exchanger would indicate that it is meant to '
                                 'reject the indicated heat transfer flow. The heat exchanger cannot sensibly be placed '
                                 f"in the '{self.placement}' component placement under this mode of operation.")
            thermal_ec_hot_side = heat_transfer.energy_carrier
            thermal_ec_cold_side = EnergyCarrier(EnergyCarrier.temp_to_thermal_ec(self.medium_out, heat_sink_temp))
            self.main_energy_carrier = thermal_ec_hot_side
            self.input_energy_carriers = []
            self.output_energy_carriers = [thermal_ec_cold_side]
        else:
            raise ValueError('Please provide either a heat sink or heat source temperature for the heat exchanger.')

    def _check_he_model_requirements(self, thermal_ec_hot_side, thermal_ec_cold_side):
        """
        Check if the hot and cold side energy carriers correspond to what the chosen heat exchanger code can provide.
        """
        if not all([thermal_ec_hot_side.type == 'thermal',
                    thermal_ec_cold_side.type == 'thermal',
                    thermal_ec_hot_side.mean_qual > thermal_ec_cold_side.mean_qual,
                    thermal_ec_hot_side.mean_qual < self.max_operating_temp,
                    thermal_ec_cold_side.mean_qual > self.min_operating_temp]):
            raise ValueError(f'The energy carriers handed to the heat exchanger {self.code} do not correspond to '
                             f'the requirements of the heat exchanger code:'
                             f'\nEnergy carrier hot side: type - {thermal_ec_cold_side.type}, '
                             f'mean_qual - {thermal_ec_hot_side.mean_qual}'
                             f'\nEnergy carrier cold side: type - {thermal_ec_cold_side.type}, '
                             f'mean_qual - {thermal_ec_hot_side.mean_qual}')

    @staticmethod
    def initialize_subclass_variables(components_database):
        """
        Fetch possible main energy carriers of cooling towers from the database and save the list as a new class
        variable.
        """
        heat_exchangers_db = components_database['heat_exchangers']
        max_operating_temperatures = heat_exchangers_db['T_max_operating']
        min_operating_temperatures = heat_exchangers_db['T_min_operating']

        # when operating the heat exchanger for heat absorption
        max_cold_side_water_temperature = max_operating_temperatures[heat_exchangers_db['medium_out'] == 'water'].max()
        min_cold_side_water_temperature = min_operating_temperatures[heat_exchangers_db['medium_out'] == 'water'].min()
        cold_side_water_ecs = EnergyCarrier.all_thermal_ecs_between_temps('water',
                                                                          max_cold_side_water_temperature,
                                                                          min_cold_side_water_temperature)
        max_cold_side_air_temperature = max_operating_temperatures[heat_exchangers_db['medium_out'] == 'air'].max()
        min_cold_side_air_temperature = min_operating_temperatures[heat_exchangers_db['medium_out'] == 'air'].min()
        cold_side_air_ecs = EnergyCarrier.all_thermal_ecs_between_temps('air',
                                                                        max_cold_side_air_temperature,
                                                                        min_cold_side_air_temperature)
        absorption_mode_main_ecs = cold_side_water_ecs + cold_side_air_ecs

        # when operating the heat exchanger for heat rejection
        max_hot_side_water_temperatures = max_operating_temperatures[heat_exchangers_db['medium_in'] == 'water'].max()
        min_hot_side_water_temperatures = min_operating_temperatures[heat_exchangers_db['medium_in'] == 'water'].min()
        hot_side_water_ecs = EnergyCarrier.all_thermal_ecs_between_temps('water',
                                                                         max_hot_side_water_temperatures,
                                                                         min_hot_side_water_temperatures)
        max_hot_side_air_temperatures = max_operating_temperatures[heat_exchangers_db['medium_in'] == 'air'].max()
        min_hot_side_air_temperatures = min_operating_temperatures[heat_exchangers_db['medium_in'] == 'air'].min()
        hot_side_air_ecs = EnergyCarrier.all_thermal_ecs_between_temps('air',
                                                                       max_hot_side_air_temperatures,
                                                                       min_hot_side_air_temperatures)
        rejection_mode_main_ecs = hot_side_water_ecs + hot_side_air_ecs

        # Create a dict of possible main energy carriers for the different modes of operation
        HeatExchanger._possible_main_ecs = {'absorption': absorption_mode_main_ecs,
                                            'rejection': rejection_mode_main_ecs}
