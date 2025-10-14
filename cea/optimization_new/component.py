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
from cea.optimization_new.containerclasses.energyCarrier import EnergyCarrier
from cea.optimization_new.containerclasses.energyFlow import EnergyFlow
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
    """
    _components_database = None
    _model_complexity = None
    _csv_name = None
    code_to_class_mapping = None
    possible_main_ecs = {}

    def __init__(self, data_base_tab,  model_code, capacity):
        self._model_data = self._extract_model_data(data_base_tab, model_code, capacity)
        self._cost_params = self._extract_model_cost_parameters(self._model_data)

        self.code = model_code
        self.technology = ' '.join([part.capitalize() for part in data_base_tab.split('_')])
        self.type = self._model_data['type'].values[0]  # given by working principle (only 1 code is installed for each type per component)
        self.capacity = capacity
        self.main_energy_carrier = EnergyCarrier.default()
        self.input_energy_carriers = {}
        self.output_energy_carriers = {}
        self.inv_cost, self.inv_cost_annual, self.om_fix_cost_annual = self.calculate_cost()

    @staticmethod
    def initialize_class_variables(domain):
        """ Fetch components database from file and save it as a class variable (dict of pd.DataFrames)"""
        component_csvs = domain.locator.get_db4_components_conversion_technologies_all()
        Component._components_database = {name: pd.read_csv(path) for name, path in component_csvs.items()}
        Component._model_complexity = domain.config.optimization_new.component_efficiency_model_complexity
        Component.code_to_class_mapping = Component.create_code_mapping(Component._components_database)
        AbsorptionChiller.initialize_subclass_variables(Component._components_database)
        VapourCompressionChiller.initialize_subclass_variables(Component._components_database)
        AirConditioner.initialize_subclass_variables(Component._components_database)
        Boiler.initialize_subclass_variables(Component._components_database)
        CogenPlant.initialize_subclass_variables(Component._components_database)
        HeatPump.initialize_subclass_variables(Component._components_database)
        CoolingTower.initialize_subclass_variables(Component._components_database)
        PowerTransformer.initialize_subclass_variables(Component._components_database)
        HeatExchanger.initialize_subclass_variables(Component._components_database)

    @staticmethod
    def create_code_mapping(database) -> dict[str, type["Component"]]:
        """ Map component codes in the database to their corresponding database tab names. """
        component_code_to_tab_mapping = {}
        for database_tab in database.keys():
            component_codes_in_tab = set(database[database_tab].code.values)
            code_to_tab_dict = {code: Component.get_component_class(database_tab) for code in component_codes_in_tab}
            component_code_to_tab_mapping.update(code_to_tab_dict)
        return component_code_to_tab_mapping

    @staticmethod
    def get_component_class(component_tab):
        """ Return the class object corresponding to a given component-database-tab. """
        for subclass in Component.__subclasses__():
            for component_class in subclass.__subclasses__():
                if component_class._csv_name == component_tab:
                    return component_class
        return None

    @staticmethod
    def _extract_model_data(data_base_tab, model_code, capacity_kW):
        """ Extract component code from database that matches the type and capacity requirements. """
        component_database = Component._components_database[data_base_tab]
        component_model_data = component_database[component_database['code'] == model_code]
        capacity_W = capacity_kW * 1000
        adequate_component_models = component_model_data[component_model_data['cap_min'] <= capacity_W]
        selected_component_model = adequate_component_models[adequate_component_models['cap_max'] > capacity_W]
        if not len(selected_component_model.index) > 0:
            raise ValueError(f'The selected component specs: \n'
                             f' - code: {model_code} \n'
                             f' - capacity: {capacity_W}W \n'
                             f'could not be found in the {data_base_tab} tab of the conversion systems database.')
        return selected_component_model

    @staticmethod
    def get_smallest_capacity(component_class, model_code):
        """ Get the smallest possible capacity of a given component from the database. """
        component_database = Component._components_database[component_class._csv_name]
        model_data = component_database[component_database['code'] == model_code]
        smallest_model_capacity_W = min(model_data['cap_min'])
        smallest_model_capacity_kW = smallest_model_capacity_W / 1000
        return smallest_model_capacity_kW

    @staticmethod
    def _extract_model_cost_parameters(model_data):
        """ Extract investment cost code parameters from the code data and store them in a dict."""
        cost_parameters = {'a': model_data['a'].values[0],
                           'b': model_data['b'].values[0],
                           'c': model_data['c'].values[0],
                           'd': model_data['d'].values[0],
                           'e': model_data['e'].values[0],
                           'lifetime': model_data['LT_yr'].values[0],
                           'om_share': model_data['O&M_%'].values[0] / 100,
                           'int_rate': model_data['IR_%'].values[0]}
        return cost_parameters

    @staticmethod
    def _create_thermal_ecs_dict(component_database, main_temp_rating_column, thermal_energy_carrier_medium):
        """
        Create a dictionary, indicating which component models can provide each of the thermal energy carriers
        the component class can generate/reject.
        """
        main_temperatures = component_database[main_temp_rating_column].unique()
        main_therm_ecs = {temp: EnergyCarrier.temp_to_thermal_ec(thermal_energy_carrier_medium, temp)
                          for temp in main_temperatures}
        ec_code_series = pd.Series([main_therm_ecs[temp] for temp in component_database[main_temp_rating_column]],
                                   name='ec', index=component_database.index)
        model_and_ec_code_match = pd.merge(component_database['code'], ec_code_series, right_index=True,
                                           left_index=True)
        possible_main_ecs_dict = {ec: model_and_ec_code_match[model_and_ec_code_match['ec'] == ec]['code'].unique()
                                  for ec in model_and_ec_code_match['ec'].unique()}
        return possible_main_ecs_dict

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
        capacity_W = self.capacity * 1000
        if capacity_W <= 0:
            capex_USD = 0
        else:
            capex_USD = self._cost_params['a'] + \
                        self._cost_params['b'] * capacity_W ** self._cost_params['c'] + \
                        (self._cost_params['d'] + self._cost_params['e'] * capacity_W) * log(capacity_W)

        capex_a_USD = calc_capex_annualized(capex_USD, self._cost_params['int_rate'], self._cost_params['lifetime'])
        opex_a_fix_USD = capex_USD * self._cost_params['om_share']

        return capex_USD, capex_a_USD, opex_a_fix_USD


class ActiveComponent(Component):

    main_side = 'output'

    def __init__(self, data_base_tab, model_code, capacity, placement_in_supply_system):
        super().__init__(data_base_tab, model_code, capacity)
        self.placement = placement_in_supply_system

    @staticmethod
    def get_types(component_tab):
        component_types = list(Component._components_database[component_tab]['code'].unique())
        return component_types

    @staticmethod
    def get_subclass(component_tab):
        for subclass in ActiveComponent.__subclasses__():
            if subclass._csv_name == component_tab:
                return subclass
        return None


class PassiveComponent(Component):

    conversion_matrix = pd.DataFrame()

    def __init__(self, data_base_tab, model_code, capacity, placed_after, placed_before):
        super().__init__(data_base_tab, model_code, capacity)
        self.placement = {'after': placed_after,
                          'before': placed_before}


class AbsorptionChiller(ActiveComponent):

    _csv_name = 'ABSORPTION_CHILLERS'

    def __init__(self, ach_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__(AbsorptionChiller._csv_name, ach_model_code, capacity, placement)
        # initialise subclass attributes
        self.minimum_COP = self._model_data['min_eff_rating'].values[0]
        self.aux_power_share = self._model_data['aux_power'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_evap_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_gen_design'].values[0])),
             EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', self._model_data['V_power_supply'].values[0]))]
        self.output_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_cond_design'].values[0]))]

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
        Fetch possible main energy carriers of absorption chillers from the database and save a dictionary, indicating
         which component models can provide each of the energy carriers, as a new class variable.
        """
        ach_database = components_database[AbsorptionChiller._csv_name]
        AbsorptionChiller.possible_main_ecs = Component._create_thermal_ecs_dict(ach_database,
                                                                                 'T_evap_design',
                                                                                 'water')


class VapourCompressionChiller(ActiveComponent):

    _csv_name = 'VAPOR_COMPRESSION_CHILLERS'

    def __init__(self, vcc_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__(VapourCompressionChiller._csv_name, vcc_model_code, capacity, placement)
        # initialise subclass attributes
        self.minimum_COP = self._model_data['min_eff_rating'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_evap_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', self._model_data['V_power_supply'].values[0]))]
        self.output_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_cond_design'].values[0]))]

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
        Fetch possible main energy carriers of vapor compression chillers from the database and save a dictionary,
        indicating which component models can provide each of the energy carriers, as a new class variable.
        """
        vcc_database = components_database[VapourCompressionChiller._csv_name]
        VapourCompressionChiller.possible_main_ecs = Component._create_thermal_ecs_dict(vcc_database,
                                                                                         'T_evap_design',
                                                                                         'water')


class AirConditioner(ActiveComponent):

    _csv_name = 'UNITARY_AIR_CONDITIONERS'

    def __init__(self, ac_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__(AirConditioner._csv_name, ac_model_code, capacity, placement)
        # initialise subclass attributes
        self.minimum_COP = self._model_data['rated_COP_seasonal'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_air_indoor_rating'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', self._model_data['V_power_supply'].values[0]))]
        self.output_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_air_outdoor_rating'].values[0]))]

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
        Fetch possible main energy carriers of unitary air conditioners from the database and save a dictionary,
        indicating which component models can provide each of the energy carriers, as a new class variable.
        """
        ac_database = components_database[AirConditioner._csv_name]
        AirConditioner.possible_main_ecs = Component._create_thermal_ecs_dict(ac_database,
                                                                               'T_air_indoor_rating',
                                                                               'air')


class Boiler(ActiveComponent):

    _csv_name = 'BOILERS'

    def __init__(self, boiler_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__(Boiler._csv_name, boiler_model_code, capacity, placement)
        # initialise subclass attributes
        self.min_thermal_eff = self._model_data['min_eff_rating'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_water_out_rating'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier.from_code(self._model_data['fuel_code'].values[0])]
        self.output_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_flue_gas_design'].values[0]))]

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
        Fetch possible main energy carriers of boilers from the database and save a dictionary, indicating which
        component models can provide each of the energy carriers, as a new class variable.
        """
        blr_database = components_database[Boiler._csv_name]
        Boiler.possible_main_ecs = Component._create_thermal_ecs_dict(blr_database,
                                                                       'T_water_out_rating',
                                                                       'water')


class CogenPlant(ActiveComponent):

    _csv_name = 'COGENERATION_PLANTS'

    def __init__(self, cogen_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__(CogenPlant._csv_name, cogen_model_code, capacity, placement)
        # initialise subclass attributes
        self.thermal_eff = self._model_data['therm_eff_design'].values[0]
        self.electrical_eff = self._model_data['elec_eff_design'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_water_out_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier.from_code(self._model_data['fuel_code'].values[0])]
        self.output_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', self._model_data['V_power_out_design'].values[0])),
             EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_flue_gas_design'].values[0]))]

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
        electricity_out = EnergyFlow(self.placement, 'primary', self.output_energy_carriers[0].code)
        waste_heat_out = EnergyFlow(self.placement, 'environment', self.output_energy_carriers[1].code)

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
        Fetch possible main energy carriers of cogeneration plants from the database and save a dictionary, indicating
        which component models can provide each of the energy carriers, as a new class variable.
        """
        cp_database = components_database[CogenPlant._csv_name]
        CogenPlant.possible_main_ecs = Component._create_thermal_ecs_dict(cp_database,
                                                                           'T_water_out_design',
                                                                           'water')


class HeatPump(ActiveComponent):

    _csv_name = 'HEAT_PUMPS'

    def __init__(self, hp_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__(HeatPump._csv_name, hp_model_code, capacity, placement)
        # initialise subclass attributes
        self.minimum_COP = self._model_data['min_eff_rating_seasonal'].values[0]
        self.thermal_ec_subtype_condenser_side = self._model_data['medium_cond_side'].values[0]
        self.thermal_ec_subtype_evaporator_side = self._model_data['medium_evap_side'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(self.thermal_ec_subtype_condenser_side,
                                                           self._model_data['T_cond_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(self.thermal_ec_subtype_evaporator_side,
                                                            self._model_data['T_evap_design'].values[0])),
             EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', self._model_data['V_power_supply'].values[0]))]

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
        hp_database = components_database[HeatPump._csv_name]

        water_heating_heat_pumps = hp_database[hp_database['medium_cond_side'] == 'water']
        water_possible_main_ecs_dict = Component._create_thermal_ecs_dict(water_heating_heat_pumps,
                                                                          'T_cond_design',
                                                                          'water')

        air_heating_heat_pumps = hp_database[hp_database['medium_cond_side'] == 'air']
        air_possible_main_ecs_dict = Component._create_thermal_ecs_dict(air_heating_heat_pumps,
                                                                        'T_cond_design',
                                                                        'air')

        joined_main_ecs_dict = water_possible_main_ecs_dict.copy()
        joined_main_ecs_dict.update(air_possible_main_ecs_dict)

        HeatPump.possible_main_ecs = joined_main_ecs_dict


class CoolingTower(ActiveComponent):

    main_side = 'input'
    _csv_name = 'COOLING_TOWERS'

    def __init__(self, ct_model_code, placement, capacity):
        # initialise parent-class attributes
        super().__init__(CoolingTower._csv_name, ct_model_code, capacity, placement)
        # initialise subclass attributes
        self.aux_power_share = self._model_data['aux_power'].values[0]
        # assign technology-specific energy carriers
        self.main_energy_carrier = \
            EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('water', self._model_data['T_water_in_design'].values[0]))
        self.input_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', self._model_data['V_power_supply'].values[0]))]
        self.output_energy_carriers = \
            [EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('air', self._model_data['T_air_in_design'].values[0]))]

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
        ct_database = components_database[CoolingTower._csv_name]
        hot_water_temperatures = ct_database['T_water_in_design'].unique()
        heating_ecs = {temp: EnergyCarrier.temp_to_thermal_ec('water', temp) for temp in hot_water_temperatures}
        ec_code_series = pd.Series([heating_ecs[temp] for temp in ct_database['T_water_in_design']], name='ec')
        model_and_ec_code_match = pd.merge(ct_database['code'], ec_code_series, right_index=True, left_index=True)
        possible_main_ecs_dict = {ec: model_and_ec_code_match[model_and_ec_code_match['ec'] == ec]['code'].unique()
                                  for ec in model_and_ec_code_match['ec'].unique()}
        CoolingTower.possible_main_ecs = possible_main_ecs_dict


class PowerTransformer(PassiveComponent):

    _csv_name = 'POWER_TRANSFORMERS'

    def __init__(self, pt_model_code, placed_before, placed_after, capacity, voltage_before, voltage_after):
        # initialise parent-class attributes
        super().__init__(PowerTransformer._csv_name, pt_model_code, capacity, placed_after, placed_before)
        # initialise subclass attributes
        self.min_low_voltage = self._model_data['V_min_lowV_side'].values[0]
        self.max_low_voltage = self._model_data['V_max_lowV_side'].values[0]
        self.min_high_voltage = self._model_data['V_min_highV_side'].values[0]
        self.max_high_voltage = self._model_data['V_max_highV_side'].values[0]
        self.current_form_low_voltage_side = self._model_data['current_form_lowV'].values[0]
        self.current_form_high_voltage_side = self._model_data['current_form_highV'].values[0]

        self._set_energy_carriers(voltage_before, voltage_after)

    def operate(self, power_transfer, new_voltage=None):
        """
        Operate the power transformer, so that it transfers the targeted amount of power. The operation is modeled
        assuming there are no losses in the transfer.

        :param power_transfer: Targeted power transfer through the power transformer (into or out of the transformer)
        :type power_transfer: <cea.optimization_new.energyFlow>-EnergyFlow object
        :param new_voltage: Voltage level to which the power should be transferred
        :type new_voltage: int, float

        :return input_energy_flows: Electrical energy flow into the power transformer
        :rtype input_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        :return output_energy_flows: Thermal energy flow out of the power transformer
        :rtype output_energy_flows: dict of <cea.optimization_new.energyFlow>-EnergyFlow objects, keys are EC codes
        """
        self._check_operational_requirements(power_transfer)

        # initialize energy flows
        converted_energy_flow = EnergyFlow()
        if [self.placement['after'], self.placement['before']] \
                in [['source', 'secondary'], ['secondary', 'primary'], ['primary', 'consumer']]:
            converted_energy_flow = EnergyFlow(self.placement['after'], 'passive_conversion', self.input_energy_carriers[0].code)
        elif [self.placement['after'], self.placement['before']] \
                    in [['primary', 'tertiary'], ['secondary', 'tertiary'], ['tertiary', 'environment']]:
            converted_energy_flow = EnergyFlow('passive_conversion', self.placement['before'], self.output_energy_carriers[0].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            if [self.placement['after'], self.placement['before']] \
                in [['source', 'secondary'], ['secondary', 'primary'], ['primary', 'consumer']]:
                converted_energy_flow.profile = self._constant_efficiency_operation(power_transfer)
            elif [self.placement['after'], self.placement['before']] \
                    in [['primary', 'tertiary'], ['secondary', 'tertiary'], ['tertiary', 'environment']]:
                converted_energy_flow.profile = self._constant_efficiency_operation(power_transfer)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        return converted_energy_flow

    @staticmethod
    def _constant_efficiency_operation(power_transfer):
        """
        Operate power transformer assuming constant operating conditions, i.e. power_in = power_out.
        (Since we assume that power transformers incur negligible losses)
        """

        return power_transfer.profile

    def _set_energy_carriers(self, voltage_before, voltage_after):
        """
        This method checks if the power transformer is used with appropriate voltage levels and allocates main,
        input and output energy carriers according to the power transformer's placement within the supply system.
        """
        # check if voltage levels are valid
        if voltage_before > voltage_after:  # step-down method
            if not (self.min_high_voltage <= voltage_before <= self.max_high_voltage) and \
                    (self.min_low_voltage <= voltage_after <= self.max_low_voltage):
                raise ValueError(f"The selected transformer model {self.code} cannot operate with a high voltage side "
                                 f"at {voltage_before}V and a low voltage side at {voltage_after}V.")
        elif voltage_before < voltage_after:  # step-up method
            if not (self.min_high_voltage <= voltage_before <= self.max_high_voltage) and \
                    (self.min_low_voltage <= voltage_after <= self.max_low_voltage):
                raise ValueError(f"The selected transformer model {self.code} cannot operate with a high voltage side "
                                 f"at {voltage_after}V and a low voltage side at {voltage_before}V.")
        else:
            raise ValueError('The voltage levels of the power transformer are either identical or invalid. If they '
                             'are identical it makes no sense to install a power transformer.')
        # assign energy carriers
        if not (self.placement['before'] == 'tertiary' or self.placement['after'] == 'tertiary'):
            self.main_energy_carrier = EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', voltage_after))
            self.input_energy_carriers = [EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', voltage_before))]
        else:
            self.main_energy_carrier = EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', voltage_before))
            self.output_energy_carriers = [EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec('AC', voltage_after))]

    @staticmethod
    def initialize_subclass_variables(components_database):
        """
        Fetch possible power transformer models that can convert a given electrical input energy carrier into a
        different electrical output energy carrier (either in step-up or step-down method) and save the result in a
        pd.DataFrame with the input and output energy carrier codes in the index and column name respectively.
        """
        power_transformers_db = components_database[PowerTransformer._csv_name]
        all_transformer_codes = list(power_transformers_db['code'])
        all_electrical_ecs = EnergyCarrier.get_all_electrical_ecs()
        PowerTransformer.conversion_matrix = pd.DataFrame(data=[], index=all_electrical_ecs, columns=all_electrical_ecs)

        pt_low_voltage_side_ecs = {transformer['code']:
                                       EnergyCarrier.all_elec_ecs_between_voltages(transformer['current_form_lowV'],
                                                                                   transformer['V_max_lowV_side'],
                                                                                   transformer['V_min_lowV_side'])
                                   for index, transformer in power_transformers_db.iterrows()}
        pt_high_voltage_side_ecs = {transformer['code']:
                                        EnergyCarrier.all_elec_ecs_between_voltages(transformer['current_form_highV'],
                                                                                    transformer['V_max_highV_side'],
                                                                                    transformer['V_min_highV_side'])
                                    for index, transformer in power_transformers_db.iterrows()}

        for ec_in in all_electrical_ecs:
            for ec_out in all_electrical_ecs:
                if not ec_in == ec_out:
                    viable_components = list(set([transformer for transformer in all_transformer_codes
                                                  if (ec_in in pt_low_voltage_side_ecs[transformer] and
                                                      ec_out in pt_high_voltage_side_ecs[transformer])
                                                  or (ec_in in pt_high_voltage_side_ecs[transformer] and
                                                      ec_out in pt_low_voltage_side_ecs[transformer])]))
                    PowerTransformer.conversion_matrix[ec_in][ec_out] = viable_components
                else:
                    PowerTransformer.conversion_matrix[ec_in][ec_out] = []

        PowerTransformer.possible_main_ecs = {ec_code: list(set(component_models.explode().dropna()))
                                              for ec_code, component_models
                                              in PowerTransformer.conversion_matrix.iterrows()}


class HeatExchanger(PassiveComponent):

    _csv_name = 'HEAT_EXCHANGERS'

    def __init__(self, he_model_code, placed_before, placed_after, capacity, temperature_before, temperature_after):
        # initialise parent-class attributes
        super().__init__(HeatExchanger._csv_name, he_model_code, capacity, placed_after, placed_before)
        # initialise subclass attributes
        self.max_operating_temp = self._model_data['T_max_operating'].values[0]
        self.min_operating_temp = self._model_data['T_min_operating'].values[0]
        self.medium_in = self._model_data['medium_in'].values[0]
        self.medium_out = self._model_data['medium_out'].values[0]

        self._set_energy_carriers(temperature_before, temperature_after)

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
            self._reset_energy_carriers(heat_transfer, heat_source_temp, heat_sink_temp)
        self._check_operational_requirements(heat_transfer)

        # initialize energy flows
        converted_energy_flow = EnergyFlow()
        if [self.placement['after'], self.placement['before']] \
                in [['source', 'secondary'], ['secondary', 'primary'], ['primary', 'consumer']]:
            converted_energy_flow = EnergyFlow(self.placement['after'], 'passive_conversion', self.input_energy_carriers[0].code)
        elif [self.placement['after'], self.placement['before']] \
                    in [['primary', 'tertiary'], ['secondary', 'tertiary'], ['tertiary', 'environment']]:
            converted_energy_flow = EnergyFlow('passive_conversion', self.placement['before'], self.output_energy_carriers[0].code)

        # run operational/efficiency code
        if Component._model_complexity == 'constant':
            if [self.placement['after'], self.placement['before']] \
                in [['source', 'secondary'], ['secondary', 'primary'], ['primary', 'consumer']]:
                converted_energy_flow.profile = self._constant_efficiency_operation(heat_transfer)
            elif [self.placement['after'], self.placement['before']] \
                    in [['primary', 'tertiary'], ['secondary', 'tertiary'], ['tertiary', 'environment']]:
                converted_energy_flow.profile = self._constant_efficiency_operation(heat_transfer)
        else:
            raise ValueError(f"The chosen code complexity, i.e. '{Component._model_complexity}', has not yet been "
                             f"implemented for {self.technology}")

        return converted_energy_flow

    @staticmethod
    def _constant_efficiency_operation(heat_transfer):
        """
        Operate heat exchanger assuming constant operating conditions, i.e. heat_in = heat_out.
        (Since we assume that heat exchangers incur negligible losses)
        """

        return heat_transfer.profile

    def _set_energy_carriers(self, temperature_before, temperature_after):
        """
        This method checks if the heat exchanger is used with appropriate temperature levels and allocates main,
        input and output energy carriers according to the heat exchanger's placement within the supply system.
        """
        # check if voltage levels are valid
        if temperature_before > temperature_after:  # cooling method
            if not (self.min_operating_temp <= temperature_after < temperature_before <= self.max_operating_temp):
                raise ValueError(f"The selected heat exchanger model {self.code} cannot operate between temperatures "
                                 f"of {temperature_after}°C and {temperature_before}°C.")
        elif temperature_before < temperature_after:  # heating method
            if not (self.min_operating_temp <= temperature_before < temperature_after <= self.max_operating_temp):
                raise ValueError(f"The selected heat exchanger model {self.code} cannot operate between temperatures "
                                 f"of {temperature_before}°C and {temperature_after}°C.")
        else:
            if self.medium_in == self.medium_out:
                raise ValueError('The energy carrier medium and temperature levels on either side of the heat '
                                 'exchanger are either identical or invalid. If they are identical it makes no sense '
                                 'to install a heat exchanger.')
        # assign energy carriers
        if not (self.placement['before'] == 'tertiary' or self.placement['after'] == 'tertiary'):
            self.main_energy_carrier = \
                EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(self.medium_out, temperature_after))
            self.input_energy_carriers = \
                [EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(self.medium_in, temperature_before))]
        else:
            self.main_energy_carrier = \
                EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(self.medium_in, temperature_before))
            self.output_energy_carriers = \
                [EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(self.medium_out, temperature_after))]

    def _reset_energy_carriers(self, heat_transfer, heat_source_temp=None, heat_sink_temp=None):
        """
        This method checks if the heat exchanger is used in an appropriate position in the supply system and
        allocates main, input and output energy flows according to the heat exchangers method of operation,
        i.e. heat absorption or heat rejection.
        """
        if (heat_source_temp is not None) and (heat_sink_temp is None):  # heat absorption method
            if [self.placement['after'], self.placement['before']] not in [['source', 'secondary'], ['secondary', 'primary'], ['primary', 'consumer']]:
                raise ValueError('Providing a heat source for the heat exchanger would indicate that it is meant to '
                                 'draw the indicated heat transfer flow from that heat source. The heat exchanger '
                                 f"cannot sensibly be placed between the '{self.placement['before']}' and "
                                 f"the '{self.placement['after']}' component placement categories under "
                                 'this mode of operation.')
            thermal_ec_hot_side = EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(self.medium_in, heat_source_temp))
            thermal_ec_cold_side = heat_transfer.energy_carrier
            self._check_he_model_requirements(thermal_ec_hot_side, thermal_ec_cold_side)
            self.main_energy_carrier = thermal_ec_cold_side
            self.input_energy_carriers = [thermal_ec_hot_side]
            self.output_energy_carriers = []
        elif (heat_source_temp is None) and (heat_sink_temp is not None):  # heat rejection method
            if [self.placement['after'], self.placement['before']] not in [['primary', 'tertiary'], ['secondary', 'tertiary'], ['tertiary', 'environment']]:
                raise ValueError('Providing a heat sink for the heat exchanger would indicate that it is meant to '
                                 'reject the indicated heat transfer flow. The heat exchanger cannot sensibly be '
                                 f"placed between the '{self.placement['before']}' and the '{self.placement['after']}' "
                                 'component placement categories under this mode of operation.')
            thermal_ec_hot_side = heat_transfer.energy_carrier
            thermal_ec_cold_side = EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(self.medium_out, heat_sink_temp))
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
        Fetch possible heat exchanger models that can convert a given thermal input energy carrier into a different
        thermal output energy carrier (either for heat absorption or heat rejection) and save the result in a
        pd.DataFrame with the input and output energy carrier codes in the index and column name respectively.
        """
        heat_exchangers_db = components_database[HeatExchanger._csv_name]
        all_heat_exchanger_codes = list(heat_exchangers_db['code'])
        all_thermal_ecs = EnergyCarrier.get_all_thermal_ecs()
        HeatExchanger.conversion_matrix = pd.DataFrame(data=[], index=all_thermal_ecs, columns=all_thermal_ecs)

        he_primary_side_ecs = {heat_exchanger['code']:
                                   EnergyCarrier.all_thermal_ecs_between_temps(heat_exchanger['T_max_operating'],
                                                                               heat_exchanger['T_min_operating'],
                                                                               heat_exchanger['medium_in'])
                                   for index, heat_exchanger in heat_exchangers_db.iterrows()}
        he_secondary_side_ecs = {heat_exchanger['code']:
                                     EnergyCarrier.all_thermal_ecs_between_temps(heat_exchanger['T_max_operating'],
                                                                                 heat_exchanger['T_min_operating'],
                                                                                 heat_exchanger['medium_out'])
                                    for index, heat_exchanger in heat_exchangers_db.iterrows()}

        for ec_in in all_thermal_ecs:
            for ec_out in all_thermal_ecs:
                if not ec_in == ec_out:
                    viable_components = list(set([heat_exchanger for heat_exchanger in all_heat_exchanger_codes
                                                  if (ec_in in he_primary_side_ecs[heat_exchanger] and
                                                      ec_out in he_secondary_side_ecs[heat_exchanger])
                                                  or (ec_in in he_secondary_side_ecs[heat_exchanger] and
                                                      ec_out in he_primary_side_ecs[heat_exchanger])]))
                    HeatExchanger.conversion_matrix[ec_in][ec_out] = viable_components
                else:
                    HeatExchanger.conversion_matrix[ec_in][ec_out] = []

        HeatExchanger.possible_main_ecs = {ec_code: list(set(component_models.explode().dropna()))
                                           for ec_code, component_models in HeatExchanger.conversion_matrix.iterrows()}
