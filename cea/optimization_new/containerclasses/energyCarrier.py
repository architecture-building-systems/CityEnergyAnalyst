"""
Energy Carrier Class:
defines all properties of an energy carrier:
CHARACTERISTICS:
- Identifier of the energy carrier
- Verbal description of the energy carrier
- Overarching type of energy (thermal, electrical, chemical, radiation) describing the energy carrier
- Descriptor for the quality of  an energy carrier (e.g. temperature level for thermal ECs)
PERFORMANCE:
- Unit cost of the energy carrier
- Unit GHG-emissions of the energy carrier
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2022, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

import warnings

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, ClassVar, Dict, Any


@dataclass(frozen=True)
class EnergyCarrier:
    # TODO: This is only optional to support default EnergyCarrier creation. Consider removing this option in the future.
    code: Optional[str]
    description: str
    type: str
    subtype: str
    qualifier: str
    qual_unit: str
    mean_qual: float

    # Class variables
    _available_energy_carriers: ClassVar[pd.DataFrame] = pd.DataFrame()
    _thermal_energy_carriers: ClassVar[Dict[str, Any]] = {}
    _electrical_energy_carriers: ClassVar[Dict[str, Any]] = {}
    _combustible_energy_carriers: ClassVar[Dict[str, Any]] = {}
    ambient_thermal_energy_carrier: ClassVar[Optional['EnergyCarrier']] = None
    _feedstock_tab: ClassVar[Dict[str, str]] = {}
    _daily_ghg_profile: ClassVar[Dict[str, Dict[int, float]]] = {}             # in kg CO2 eq. per kWh
    _daily_buy_price_profile: ClassVar[Dict[str, Dict[int, float]]] = {}       # in USD (2015) per kWh
    _daily_sell_price_profile: ClassVar[Dict[str, Dict[int, float]]] = {}      # in USD (2015) per kWh

    def __post_init__(self):
        if self.code is None:
            return  # Skip validation for default instance

        # Validate type
        allowed_types = ['thermal', 'electrical', 'combustible', 'radiation']
        if self.type not in allowed_types:
            raise ValueError("The energy carrier data base contains an invalid energy type. Valid energy carrier "
                             "types are: \n 'thermal', 'electrical', 'combustible', 'radiation'")

        # Validate subtype
        allowed_subtypes = {'thermal': ['water', 'air', 'brine'],
                            'electrical': ['AC', 'DC'],
                            'combustible': ['fossil', 'biofuel'],
                            'radiation': ['-']}
        
        if self.subtype not in allowed_subtypes[self.type]:
            raise ValueError("The energy carrier data base contains an invalid energy type. The only valid subtypes "
                             f"for energy carriers of type '{self.type}' are {allowed_subtypes[self.type]} for the "
                             "moment. \n Including further subtypes would require changes to be made to the code of "
                             "the supply system components that should take the new type into account.")

        # Validate qualifier
        if self.qualifier not in set(self._available_energy_carriers['qualifier'].values):
            raise ValueError('Please make sure all basic energy carrier qualifiers appear in the data base, namely: '
                             'temperature, voltage, wavelength')

        # Validate qual_unit
        if self.qual_unit not in set(self._available_energy_carriers['unit_qual'].values):
            raise ValueError('Please make sure the energy carrier qualifier units are set correctly.')
        
        # Validate mean_qual
        if not isinstance(self.mean_qual, (int, float)):
            raise ValueError("Please make sure the energy carrier qualifier's mean qualifier values are set correctly. "
                             "Acceptable values are numerical or '-'.")

    @classmethod
    def from_code(cls, code: str) -> 'EnergyCarrier':
        """Create an EnergyCarrier instance from a database code."""
        if cls._available_energy_carriers.empty:
            raise ValueError("Energy carrier database not loaded. Call initialize_class_variables() first.")

        if code not in set(cls._available_energy_carriers['code'].values):
            raise ValueError(f'Tried to assign a new energy energy carrier using the code "{code}". This code '
                             f'could not be found in the energy carriers database.')

        energy_carrier = cls._available_energy_carriers.loc[cls._available_energy_carriers['code'] == code].iloc[0]

        # Extract values from database
        description = energy_carrier['description']
        energy_type = energy_carrier['type']
        subtype = energy_carrier['subtype']
        qualifier = energy_carrier['qualifier']
        qual_unit = energy_carrier['unit_qual']
        mean_qual_value = energy_carrier['mean_qual']

        # Handle mean_qual conversion and validation
        if isinstance(mean_qual_value, (int, float)):
            mean_qual = float(mean_qual_value)
        elif mean_qual_value == '-':
            mean_qual = float('nan')
        else:
            raise ValueError("Please make sure the energy carrier qualifier's mean qualifier values are set correctly. "
                             "Acceptable values are numerical or '-'.")

        return cls(code=code,
                   description=description,
                   type=energy_type,
                   subtype=subtype,
                   qualifier=qualifier,
                   qual_unit=qual_unit,
                   mean_qual=mean_qual)
    
    @classmethod
    def default(cls) -> 'EnergyCarrier':
        """Create a default EnergyCarrier instance."""
        return cls(code=None,
                   description="",
                   type='none',
                   subtype='none',
                   qualifier='none',
                   qual_unit='none',
                   mean_qual=float('nan'))
        
    def describe(self):
        """ Provide a short written description of the energy carrier."""
        description = self.description + ": " + str(self.mean_qual) + " " + self.qual_unit
        return description

    @staticmethod
    def initialize_class_variables(domain):
        """
        Load energy carriers from database and determine which of the energy carriers are of type thermal. Save both
        data sets as class variables.
        """
        EnergyCarrier._load_energy_carriers(domain.locator)
        EnergyCarrier._extract_thermal_energy_carriers()
        EnergyCarrier._extract_electrical_energy_carriers()
        EnergyCarrier._extract_combustible_energy_carriers()
        EnergyCarrier._establish_thermal_environment_energy_carrier(domain.weather)

    @staticmethod
    def _load_energy_carriers(locator):
        """ Fetch a complete description of available energy carriers from the FEEDSTOCKS database """
        # Load the feedstock database
        feedstocks = {feedstock: pd.read_csv(csv_file) for feedstock, csv_file
                      in locator.get_db4_components_feedstocks_all().items()}
        def to_numeric(x):
            if x == '-':
                return x
            try:
                return float(x)
            except ValueError:
                raise ValueError(f'Invalid qualifier value for energy carrier. Could not convert {x} to float.')
        energy_carriers_overview = pd.read_csv(locator.get_database_components_feedstocks_energy_carriers(),
                                               converters={'mean_qual': to_numeric})

        # Correct potential basic format errors if there are any
        energy_carriers_overview['feedstock_file'].fillna('-', inplace=True)
        energy_carriers_overview['feedstock_file'] = \
            energy_carriers_overview['feedstock_file'].astype(str).str.strip().str.upper()
        EnergyCarrier._available_energy_carriers = energy_carriers_overview.fillna(0.0)

        # Check if tab references are valid
        referenced_files = [file_name for file_name in list(set(energy_carriers_overview['feedstock_file']))
                            if file_name != '-']
        if not all([file_name in feedstocks.keys() for file_name in referenced_files]):
            raise ValueError('The energy carriers data base contains references to tabs that do not exist in the '
                             'feedstock data base. Please make sure the tabs are named correctly.')

        # Fetch unitary ghg emissions as well as buy and sell prices for each energy carrier from the feedstock database
        for file_name in referenced_files:
            cost_and_ghg = feedstocks[file_name]
            EnergyCarrier._daily_ghg_profile[file_name] = \
                {hour: ghg_emission * 3.6 for hour, ghg_emission in zip(cost_and_ghg['hour'], cost_and_ghg['GHG_kgCO2MJ'])}
            EnergyCarrier._daily_buy_price_profile[file_name] = \
                {hour: cost for hour, cost in zip(cost_and_ghg['hour'], cost_and_ghg['Opex_var_buy_USD2015kWh'])}
            EnergyCarrier._daily_sell_price_profile[file_name] = \
                {hour: cost for hour, cost in zip(cost_and_ghg['hour'], cost_and_ghg['Opex_var_sell_USD2015kWh'])}


    @staticmethod
    def _extract_thermal_energy_carriers():
        if EnergyCarrier._available_energy_carriers.empty:
            raise AttributeError('The energy carrier database has not been loaded or was not found.')
        all_thermal_energy_carriers = \
            EnergyCarrier._available_energy_carriers[EnergyCarrier._available_energy_carriers['type'] == 'thermal']
        thermal_ec_subtypes = all_thermal_energy_carriers['subtype'].unique()
        for subtype in thermal_ec_subtypes:
            EnergyCarrier._thermal_energy_carriers[subtype] = \
                all_thermal_energy_carriers[all_thermal_energy_carriers['subtype'] == subtype]
        if len(EnergyCarrier._thermal_energy_carriers) == 0:
            raise ValueError('No thermal energy carriers could be found in the energy carriers data base.')

    @staticmethod
    def _extract_electrical_energy_carriers():
        if EnergyCarrier._available_energy_carriers.empty:
            raise AttributeError('The energy carrier database has not been loaded or was not found.')
        all_electrical_energy_carriers = \
            EnergyCarrier._available_energy_carriers[EnergyCarrier._available_energy_carriers['type'] == 'electrical']
        electrical_ec_subtypes = all_electrical_energy_carriers['subtype'].unique()
        for subtype in electrical_ec_subtypes:
            EnergyCarrier._electrical_energy_carriers[subtype] = \
                all_electrical_energy_carriers[all_electrical_energy_carriers['subtype'] == subtype]
        if len(EnergyCarrier._electrical_energy_carriers) == 0:
            raise ValueError('No electrical energy carriers could be found in the energy carriers data base.')

    @staticmethod
    def _extract_combustible_energy_carriers():
        if EnergyCarrier._available_energy_carriers.empty:
            raise AttributeError('The energy carrier database has not been loaded or was not found.')
        all_combustible_energy_carriers = \
            EnergyCarrier._available_energy_carriers[EnergyCarrier._available_energy_carriers['type'] == 'combustible']
        combustible_ec_subtypes = all_combustible_energy_carriers['subtype'].unique()
        for subtype in combustible_ec_subtypes:
            EnergyCarrier._combustible_energy_carriers[subtype] = \
                all_combustible_energy_carriers[all_combustible_energy_carriers['subtype'] == subtype]
        if len(EnergyCarrier._electrical_energy_carriers) == 0:
            raise ValueError('No electrical energy carriers could be found in the energy carriers data base.')

    @staticmethod
    def _establish_thermal_environment_energy_carrier(weather):
        """
        Determine the thermal energy carrier that corresponds to the ambient temperature of the environment.
        """
        ambient_temperature = weather['drybulb_C'].mean()
        EnergyCarrier.ambient_thermal_energy_carrier = \
            EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec('air', ambient_temperature))

    @staticmethod
    def get_thermal_ecs_of_subtype(subtype):
        """
        Return a list of all thermal energy carrier codes for the indicated subtype.
        """
        thermal_ecs_of_subtype = EnergyCarrier._thermal_energy_carriers[subtype]
        energy_carrier_codes = list(thermal_ecs_of_subtype['code'])
        return energy_carrier_codes

    @staticmethod
    def get_all_thermal_ecs():
        """
        Return a list of all thermal energy carrier codes.
        """
        if not EnergyCarrier._thermal_energy_carriers:
            EnergyCarrier._extract_thermal_energy_carriers()

        thermal_ec_subtypes = list(EnergyCarrier._thermal_energy_carriers.keys())
        energy_carrier_codes = [ec_code for subtype in thermal_ec_subtypes
                                for ec_code in EnergyCarrier.get_thermal_ecs_of_subtype(subtype)]
        return energy_carrier_codes

    @staticmethod
    def get_hotter_thermal_ecs(thermal_energy_carrier, subtype=None, include_thermal_ec=False):
        """
        Get all thermal energy carriers with a higher mean temperature level than the indicated thermal energy carrier.
        """
        if isinstance(thermal_energy_carrier, EnergyCarrier):
            thermal_energy_carrier = thermal_energy_carrier.code

        if thermal_energy_carrier is None:
            warnings.warn('No thermal energy carrier was indicated. Returning an empty list.', UserWarning)
            return []

        if subtype:
            all_thermal_ec_codes = EnergyCarrier.get_thermal_ecs_of_subtype(subtype)
        else:
            all_thermal_ec_codes = EnergyCarrier.get_all_thermal_ecs()
        
        if include_thermal_ec:
            hotter_energy_carrier_codes = [ec_code for ec_code in all_thermal_ec_codes
                                           if EnergyCarrier.from_code(ec_code).mean_qual >=
                                           EnergyCarrier.from_code(thermal_energy_carrier).mean_qual]
        else:
            hotter_energy_carrier_codes = [ec_code for ec_code in all_thermal_ec_codes
                                           if EnergyCarrier.from_code(ec_code).mean_qual >
                                           EnergyCarrier.from_code(thermal_energy_carrier).mean_qual]

        return hotter_energy_carrier_codes

    @staticmethod
    def get_colder_thermal_ecs(thermal_energy_carrier, subtype=None, include_thermal_ec=False):
        """
        Get all thermal energy carriers with a lower mean temperature level than the indicated thermal energy carrier.
        """
        if isinstance(thermal_energy_carrier, EnergyCarrier):
            thermal_energy_carrier = thermal_energy_carrier.code

        if thermal_energy_carrier is None:
            warnings.warn('No thermal energy carrier was indicated. Returning an empty list.', UserWarning)
            return []

        if subtype:
            all_thermal_ec_codes = EnergyCarrier.get_thermal_ecs_of_subtype(subtype)
        else:
            all_thermal_ec_codes = EnergyCarrier.get_all_thermal_ecs()
        
        if include_thermal_ec:
            colder_energy_carrier_codes = [ec_code for ec_code in all_thermal_ec_codes
                                           if EnergyCarrier.from_code(ec_code).mean_qual <=
                                           EnergyCarrier.from_code(thermal_energy_carrier).mean_qual]
        else:
            colder_energy_carrier_codes = [ec_code for ec_code in all_thermal_ec_codes
                                           if EnergyCarrier.from_code(ec_code).mean_qual <
                                           EnergyCarrier.from_code(thermal_energy_carrier).mean_qual]

        return colder_energy_carrier_codes

    @staticmethod
    def temp_to_thermal_ec(energy_carrier_subtype, temperature):
        """
        Determine which thermal energy carrier corresponds to a given temperature.

        :param energy_carrier_subtype: type of the thermal energy carrier
        :type energy_carrier_subtype: str
        :param temperature: temperature in °C
        :type temperature: float
        :return energy_carrier_code: code of the corresponding thermal energy carrier
        :rtype energy_carrier_code: str
        """
        if not EnergyCarrier._thermal_energy_carriers:
            EnergyCarrier._extract_thermal_energy_carriers()

        thermal_ecs_of_subtype = EnergyCarrier._thermal_energy_carriers[energy_carrier_subtype]
        thermal_ec_mean_quals = pd.to_numeric(thermal_ecs_of_subtype['mean_qual'])
        if not np.isnan(temperature):
            index_closest_mean_temp = (thermal_ec_mean_quals - temperature).abs().nsmallest(n=1).index[0]
            energy_carrier_code = thermal_ecs_of_subtype['code'].loc[index_closest_mean_temp]
        else:
            energy_carrier_code = thermal_ecs_of_subtype['code'].iloc[0]
            print(f'The temperature level of a renewable energy potential was not available. '
                  f'We assume that the following energy carrier is output: '
                  f'{thermal_ecs_of_subtype["description"].iloc[0]}')
        return energy_carrier_code

    @staticmethod
    def all_thermal_ecs_between_temps(temperature_1, temperature_2, energy_carrier_subtype='all'):
        """
        Get all thermal energy carriers that either fall in the range of or between two predetermined temperatures
        for a given thermal energy carrier type.

        :param temperature_1: higher one of the two temperatures defining the range, in °C
        :type temperature_1: float
        :param temperature_2: lower one of the two temperatures defining the range, in °C
        :type temperature_2: float
        :param energy_carrier_subtype: type of the thermal energy carrier (usually thermal energy carrier medium)
        :type energy_carrier_subtype: str
        :return thermal_ecs_between_temps: list of codes of the corresponding thermal energy carriers that correspond to
                                           the prescribed range.
        :rtype thermal_ecs_between_temps: list of str
        """
        if np.isnan(temperature_1) and np.isnan(temperature_2):
            return []
        elif np.isnan(temperature_1) or np.isnan(temperature_2):
            raise ValueError('Please make sure the boundaries of the indicated temperature range are valid.')

        high_temperature, low_temperature = max(temperature_1, temperature_2), min(temperature_1, temperature_2)

        if energy_carrier_subtype == 'all':
            ec_subtype_list = list(EnergyCarrier._thermal_energy_carriers.keys())
        elif energy_carrier_subtype in EnergyCarrier._thermal_energy_carriers:
            ec_subtype_list = [energy_carrier_subtype]
        else:
            raise ValueError('Please make sure the indicated thermal energy carrier subtype is valid.')

        return EnergyCarrier._filter_thermal_ecs_between_temps(low_temperature, high_temperature, ec_subtype_list)

    @staticmethod
    def _filter_thermal_ecs_between_temps(low_temperature, high_temperature, subtypes):
        """
        Filter the list of all thermal energy carriers for those that correspond to one of the specified subtypes and
        fall within the specified temperature range.

        :param low_temperature: Low temperature in °C
        :type low_temperature: float
        :param high_temperature: High temperature in °C
        :type high_temperature: float
        :param subtypes: Energy carrier subtypes
        :type subtypes: list
        :return: Codes of the corresponding thermal energy carriers
        :rtype: list
        """
        equivalent_discrete_low_temps = {
            ec_subtype: EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(ec_subtype, low_temperature)).mean_qual
            for ec_subtype in subtypes
        }
        equivalent_discrete_high_temps = {
            ec_subtype: EnergyCarrier.from_code(EnergyCarrier.temp_to_thermal_ec(ec_subtype, high_temperature)).mean_qual
            for ec_subtype in subtypes
        }

        thermal_ecs_between_temps = [
            energy_carrier['code']
            for ec_subtype in subtypes
            for _, energy_carrier in EnergyCarrier._thermal_energy_carriers[ec_subtype].iterrows()
            if equivalent_discrete_low_temps[ec_subtype] <= energy_carrier['mean_qual'] <=
               equivalent_discrete_high_temps[ec_subtype]
        ]

        return thermal_ecs_between_temps

    @staticmethod
    def get_electrical_ecs_of_subtype(subtype):
        """
        Return a list of all electrical energy carrier codes for the indicated subtype.
        """
        electrical_ecs_of_subtype = EnergyCarrier._electrical_energy_carriers[subtype]
        energy_carrier_codes = list(electrical_ecs_of_subtype['code'])
        return energy_carrier_codes

    @staticmethod
    def get_all_electrical_ecs():
        """
        Return a list of all electrical energy carrier codes.
        """
        if not EnergyCarrier._electrical_energy_carriers:
            EnergyCarrier._extract_electrical_energy_carriers()

        electrical_ec_subtypes = list(EnergyCarrier._electrical_energy_carriers.keys())
        energy_carrier_codes = [ec_code for subtype in electrical_ec_subtypes
                                for ec_code in EnergyCarrier.get_electrical_ecs_of_subtype(subtype)]
        return energy_carrier_codes

    @staticmethod
    def get_all_other_electrical_ecs(electrical_energy_carrier):
        if isinstance(electrical_energy_carrier, EnergyCarrier):
            electrical_energy_carrier = electrical_energy_carrier.code

        all_electrical_ecs = EnergyCarrier.get_all_electrical_ecs()
        all_other_electrical_ecs = [ec_code for ec_code in all_electrical_ecs if ec_code != electrical_energy_carrier]
        return all_other_electrical_ecs

    @staticmethod
    def volt_to_electrical_ec(energy_carrier_subtype, voltage):
        """
        Determine which electrical energy carrier corresponds to a given voltage.

        :param energy_carrier_subtype: type of electrical energy carrier (distinguished by form of the current, e.g. AC)
        :type energy_carrier_subtype: str
        :param voltage: voltage in V
        :type voltage: float
        :return energy_carrier_code: code of the corresponding electrical energy carrier
        :rtype energy_carrier_code: str
        """
        if not EnergyCarrier._electrical_energy_carriers:
            EnergyCarrier._extract_electrical_energy_carriers()

        electrical_ec_mean_quals = pd.to_numeric(EnergyCarrier._electrical_energy_carriers[energy_carrier_subtype]['mean_qual'])
        if not np.isnan(voltage):
            index_closest_mean_voltage = (electrical_ec_mean_quals - voltage).abs().nsmallest(n=1).index[0]
            energy_carrier_code = \
                EnergyCarrier._electrical_energy_carriers[energy_carrier_subtype]['code'].loc[index_closest_mean_voltage]
        else:
            energy_carrier_code = EnergyCarrier._electrical_energy_carriers[energy_carrier_subtype]['code'][0]
            print(f'The voltage of a renewable energy potential was not available. '
                  f'We assume that the following energy carrier is output: '
                  f'{EnergyCarrier._electrical_energy_carriers["description"][0]}')
        return energy_carrier_code

    @staticmethod
    def all_elec_ecs_between_voltages(energy_carrier_subtype, high_voltage, low_voltage):
        """
        Get all electrical energy carriers that either fall in the range of or between two predetermined voltages
        for a given electrical energy carrier type.

        :param energy_carrier_subtype: type of electrical energy carrier (distinguished by form of the current, e.g. AC)
        :type energy_carrier_subtype: str
        :param high_voltage: higher one of the two voltages defining the range, in V
        :type high_voltage: float
        :param low_voltage: lower one of the two voltages defining the range, in V
        :type low_voltage: float
        :return electrical_ecs_between_voltages: list of codes of the corresponding electrical energy carriers that
                                                 correspond to the prescribed range.
        :rtype electrical_ecs_between_voltages: list of str
        """
        if np.isnan(high_voltage) and np.isnan(low_voltage):
            electrical_ecs_between_voltages = []
        elif not np.isnan(high_voltage) and not np.isnan(low_voltage):
            top_of_range_ec = EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec(energy_carrier_subtype, high_voltage))
            bottom_of_range_ec = EnergyCarrier.from_code(EnergyCarrier.volt_to_electrical_ec(energy_carrier_subtype, low_voltage))
            electrical_ecs_of_subtype = EnergyCarrier._electrical_energy_carriers[energy_carrier_subtype]
            electrical_ecs_between_voltages = [energy_carrier['code']
                                               for row, energy_carrier in electrical_ecs_of_subtype.iterrows()
                                               if (top_of_range_ec.mean_qual >= energy_carrier['mean_qual'] >= bottom_of_range_ec.mean_qual)]
        else:
            raise ValueError('Please make sure the boundaries of the indicated temperature range are valid.')

        return electrical_ecs_between_voltages

    @staticmethod
    def get_combustible_ecs_of_subtype(subtype):
        """
        Return a list of all combustible energy carrier codes for the indicated subtype.
        """
        if not EnergyCarrier._combustible_energy_carriers:
            EnergyCarrier._extract_combustible_energy_carriers()
        combustible_ecs_of_subtype = EnergyCarrier._combustible_energy_carriers[subtype]
        energy_carrier_codes = list(combustible_ecs_of_subtype['code'])
        return energy_carrier_codes

    @staticmethod
    def fetch_ghg_emissions(energy_carrier_code, energy_flow_profile):
        """

        """
        if energy_carrier_code not in EnergyCarrier._feedstock_tab.keys():
            EnergyCarrier._bind_feedstock_tab(energy_carrier_code)

        data_tab_name = EnergyCarrier._feedstock_tab[energy_carrier_code]

        if data_tab_name == '-':
            return (0.0 for _ in energy_flow_profile)
        elif data_tab_name not in EnergyCarrier._daily_ghg_profile.keys():
            raise ValueError(f'The data tab "{data_tab_name}" was not found in the feedstock data base. GHG emissions '
                             f'could not be fetched for the energy carrier "{energy_carrier_code}".')
        else:
            positive_flow_profile = energy_flow_profile.replace(list(energy_flow_profile[energy_flow_profile<0]), 0)
            ghg_emissions_profile = (energy * EnergyCarrier._daily_ghg_profile[data_tab_name][timestep.hour]
                                     for timestep, energy in positive_flow_profile.items())
            return ghg_emissions_profile

    @staticmethod
    def fetch_cost(energy_carrier_code, energy_flow_profile):
        """

        """
        if energy_carrier_code not in EnergyCarrier._feedstock_tab.keys():
            EnergyCarrier._bind_feedstock_tab(energy_carrier_code)

        data_tab_name = EnergyCarrier._feedstock_tab[energy_carrier_code]

        if data_tab_name == '-':
            return (0.0 for _ in energy_flow_profile)
        elif data_tab_name not in set(list(EnergyCarrier._daily_buy_price_profile.keys()) +
                                      list(EnergyCarrier._daily_sell_price_profile.keys())):
            raise ValueError(f'The data tab "{data_tab_name}" was not found in the feedstock data base. Costs could '
                             f'not be fetched for the energy carrier "{energy_carrier_code}".')
        else:
            return sum(EnergyCarrier.get_price_for_timestep(data_tab_name, timestep, energy)
                       for timestep, energy in energy_flow_profile.items())

    @staticmethod
    def get_price_for_timestep(data_tab_name, timestep, energy_demand):
        """
        Return the sell or buy price for a given quantity of energy and a given timestep from the database.
        """
        if energy_demand >= 0: # i.e. energy is bought
            unit_price = EnergyCarrier._daily_buy_price_profile[data_tab_name][timestep.hour]
        elif energy_demand < 0: # i.e. energy is sold
            unit_price = EnergyCarrier._daily_sell_price_profile[data_tab_name][timestep.hour]
        else:
            raise ValueError('Can\'t determine whether energy is bought or sold. Please make sure the energy demand is '
                             f'calculated correctly. Energy demand was: {energy_demand} for timestep {timestep}.')

        return unit_price * energy_demand

    @staticmethod
    def _bind_feedstock_tab(energy_carrier_code):
        """
        Associate the respective tab-name of the feedstock-database to the energy carrier code.
        """
        corresponding_feedstock_tab = EnergyCarrier._available_energy_carriers[
            EnergyCarrier._available_energy_carriers['code'] == energy_carrier_code]['feedstock_file'].values[0]
        EnergyCarrier._feedstock_tab[energy_carrier_code] = corresponding_feedstock_tab
