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

import pandas as pd
import numpy as np


class EnergyCarrier(object):
    _available_energy_carriers = pd.DataFrame
    _thermal_energy_carriers = {}
    _electrical_energy_carriers = {}
    _combustible_energy_carriers = {}
    _unit_ghg_dict = {}
    _unit_cost_dict = {}

    def __init__(self, code=None):
        self._code = None
        self._description = 'some description'
        self._type = 'e.g. thermal'
        self._subtype = 'e.g. water'
        self._qualifier = 'e.g. temperature'
        self._qual_unit = 'e.g. °C'
        self._mean_qual = 0.0
        self._unit_cost = 0.0   # in USD per kWh
        self._unit_ghg = 0.0    # in kg C02 eq. per kWh

        self._set_to(code)

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, new_code):
        if new_code not in EnergyCarrier._available_energy_carriers['code'].to_list():
            raise ValueError(f'Tried to assign a new energy energy carrier using the code "{new_code}". This code '
                             f'could not be found in the energy carriers database.')
        else:
            self._code = new_code

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, new_type):
        allowed_types = ['thermal', 'electrical', 'combustible', 'radiation']
        if new_type not in allowed_types:
            raise ValueError("The energy carrier data base contains an invalid energy type. Valid energy carrier "
                             "types are: \n 'thermal', 'electrical', 'combustible', 'radiation'")
        else:
            self._type = new_type

    @property
    def subtype(self):
        return self._subtype

    @subtype.setter
    def subtype(self, new_subtype):
        allowed_subtypes = {'thermal': ['water', 'air', 'brine'],
                            'electrical': ['AC', 'DC'],
                            'combustible': ['fossil', 'biofuel'],
                            'radiation': ['-']}
        if new_subtype not in allowed_subtypes[self.type]:
            raise ValueError("The energy carrier data base contains an invalid energy type. The only valid subtypes "
                             f"for energy carriers of type '{self.type}' are {allowed_subtypes[self.type]} for the "
                             "moment. \n Including further subtypes would require changes to be made to the code of "
                             "the supply system components that should take the new type into account.")
        else:
            self._subtype = new_subtype

    @property
    def qualifier(self):
        return self._qualifier

    @qualifier.setter
    def qualifier(self, new_qualifier):
        if new_qualifier not in EnergyCarrier._available_energy_carriers['qualifier'].to_list():
            raise ValueError('Please make sure all basic energy carrier qualifiers appear in the data base, namely: '
                             'temperature, voltage, wavelength')
        else:
            self._qualifier = new_qualifier

    @property
    def qual_unit(self):
        return self._qual_unit

    @qual_unit.setter
    def qual_unit(self, new_qual_unit):
        if new_qual_unit not in EnergyCarrier._available_energy_carriers['unit_qual'].to_list():
            raise ValueError('Please make sure the energy carrier qualifier units are set correctly.')
        else:
            self._qual_unit = new_qual_unit

    @property
    def mean_qual(self):
        return self._mean_qual

    @mean_qual.setter
    def mean_qual(self, new_mean_qual):
        if not (isinstance(new_mean_qual, (int, float)) or (new_mean_qual == '-')):
            raise ValueError("Please make sure the energy carrier qualifier's mean qualifier values are set correctly. "
                             "Acceptable values are numerical or '-'.")
        else:
            self._mean_qual = new_mean_qual

    @property
    def unit_cost(self):
        return self._unit_cost

    @unit_cost.setter
    def unit_cost(self, new_unit_cost):
        if not isinstance(new_unit_cost, (int, float)):
            raise ValueError("Please make sure the unit costs of energy carriers in the data base are numeric.")
        else:
            self._unit_cost = new_unit_cost

    @property
    def unit_ghg(self):
        return self._unit_ghg

    @unit_ghg.setter
    def unit_ghg(self, new_unit_ghg):
        if not isinstance(new_unit_ghg, (int, float)):
            raise ValueError("Please make sure the unit GHG emissions of energy carriers in the data base are numeric.")
        else:
            self._unit_ghg = new_unit_ghg

    def _set_to(self, code):
        if code:
            energy_carrier = EnergyCarrier._available_energy_carriers[EnergyCarrier._available_energy_carriers['code'] == code]

            self.code = code
            self._description = energy_carrier['description'].iloc[0]
            self.type = energy_carrier['type'].iloc[0]
            self.subtype = energy_carrier['subtype'].iloc[0]
            self.qualifier = energy_carrier['qualifier'].iloc[0]
            self.qual_unit = energy_carrier['unit_qual'].iloc[0]
            self.mean_qual = energy_carrier['mean_qual'].iloc[0]
            self.unit_cost = energy_carrier['unit_cost_USD.kWh'].iloc[0]
            self.unit_ghg = energy_carrier['unit_ghg_kgCO2.kWh'].iloc[0]

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

    @staticmethod
    def _load_energy_carriers(locator):
        EnergyCarrier._available_energy_carriers = pd.read_excel(locator.get_database_energy_carriers())

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

        if subtype:
            all_thermal_ec_codes = EnergyCarrier.get_thermal_ecs_of_subtype(subtype)
        else:
            all_thermal_ec_codes = EnergyCarrier.get_all_thermal_ecs()
        if include_thermal_ec:
            hotter_energy_carrier_codes = [ec_code for ec_code in all_thermal_ec_codes
                                           if EnergyCarrier(ec_code).mean_qual >=
                                           EnergyCarrier(thermal_energy_carrier).mean_qual]
        else:
            hotter_energy_carrier_codes = [ec_code for ec_code in all_thermal_ec_codes
                                           if EnergyCarrier(ec_code).mean_qual >
                                           EnergyCarrier(thermal_energy_carrier).mean_qual]

        return hotter_energy_carrier_codes

    @staticmethod
    def get_colder_thermal_ecs(thermal_energy_carrier, subtype=None, include_thermal_ec=False):
        """
        Get all thermal energy carriers with a lower mean temperature level than the indicated thermal energy carrier.
        """
        if isinstance(thermal_energy_carrier, EnergyCarrier):
            thermal_energy_carrier = thermal_energy_carrier.code

        if subtype:
            all_thermal_ec_codes = EnergyCarrier.get_thermal_ecs_of_subtype(subtype)
        else:
            all_thermal_ec_codes = EnergyCarrier.get_all_thermal_ecs()
        if include_thermal_ec:
            colder_energy_carrier_codes = [ec_code for ec_code in all_thermal_ec_codes
                                           if EnergyCarrier(ec_code).mean_qual <=
                                           EnergyCarrier(thermal_energy_carrier).mean_qual]
        else:
            colder_energy_carrier_codes = [ec_code for ec_code in all_thermal_ec_codes
                                           if EnergyCarrier(ec_code).mean_qual <
                                           EnergyCarrier(thermal_energy_carrier).mean_qual]

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
    def all_thermal_ecs_between_temps(energy_carrier_subtype, high_temperature, low_temperature):
        """
        Get all thermal energy carriers that either fall in the range of or between two predetermined temperatures
        for a given thermal energy carrier type.

        :param energy_carrier_subtype: type of the thermal energy carrier (usually thermal energy carrier medium)
        :type energy_carrier_subtype: str
        :param high_temperature: higher one of the two temperatures defining the range, in °C
        :type high_temperature: float
        :param low_temperature: lower one of the two temperatures defining the range, in °C
        :type low_temperature: float
        :return thermal_ecs_between_temps: list of codes of the corresponding thermal energy carriers that correspond to
                                           the prescribed range.
        :rtype thermal_ecs_between_temps: list of str
        """
        if np.isnan(high_temperature) and np.isnan(low_temperature):
            thermal_ecs_between_temps = []
        elif not np.isnan(high_temperature) and not np.isnan(low_temperature):
            top_of_range_ec = EnergyCarrier(EnergyCarrier.temp_to_thermal_ec(energy_carrier_subtype, high_temperature))
            bottom_of_range_ec = EnergyCarrier(EnergyCarrier.temp_to_thermal_ec(energy_carrier_subtype, low_temperature))
            thermal_ecs_of_subtype = EnergyCarrier._thermal_energy_carriers[energy_carrier_subtype]
            thermal_ecs_between_temps = [energy_carrier['code']
                                         for row, energy_carrier in thermal_ecs_of_subtype.iterrows()
                                         if (top_of_range_ec.mean_qual >= energy_carrier['mean_qual'] >= bottom_of_range_ec.mean_qual)]
        else:
            raise ValueError('Please make sure the boundaries of the indicated temperature range are valid.')

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
            top_of_range_ec = EnergyCarrier(EnergyCarrier.volt_to_electrical_ec(energy_carrier_subtype, high_voltage))
            bottom_of_range_ec = EnergyCarrier(EnergyCarrier.volt_to_electrical_ec(energy_carrier_subtype, low_voltage))
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
    def get_unit_ghg(energy_carrier_code):
        """
        Return the unit greenhouse gas emissions of a specific energy carrier from the database.
        """
        if not EnergyCarrier._unit_ghg_dict:
            available_energy_carrier_codes = list(EnergyCarrier._available_energy_carriers['code'])
            EnergyCarrier._unit_ghg_dict = {ec_code:
                                                EnergyCarrier._available_energy_carriers[
                                                    EnergyCarrier._available_energy_carriers['code'] == ec_code]
                                                ['unit_ghg_kgCO2.kWh'].values[0]
                                            for ec_code in available_energy_carrier_codes}

        unit_ghg = EnergyCarrier._unit_ghg_dict[energy_carrier_code]

        return unit_ghg

    @staticmethod
    def get_unit_cost(energy_carrier_code):
        """
        Return the unit greenhouse gas emissions of a specific energy carrier from the database.
        """
        if not EnergyCarrier._unit_cost_dict:
            available_energy_carrier_codes = list(EnergyCarrier._available_energy_carriers['code'])
            EnergyCarrier._unit_cost_dict = {ec_code:
                                                 EnergyCarrier._available_energy_carriers[
                                                     EnergyCarrier._available_energy_carriers['code'] == ec_code]
                                                 ['unit_cost_USD.kWh'].values[0]
                                             for ec_code in available_energy_carrier_codes}

        unit_cost = EnergyCarrier._unit_ghg_dict[energy_carrier_code]

        return unit_cost
