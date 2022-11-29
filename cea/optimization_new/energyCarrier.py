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
    _thermal_energy_carriers = pd.DataFrame

    def __init__(self, code=None):
        self._code = None
        self._description = 'some description'
        self._type = 'e.g. thermal'
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
        if not (new_code in EnergyCarrier._available_energy_carriers['code'].to_list()):
            raise ValueError('Please make sure that the energy carriers in the data base match the energy system '
                             'components inputs and outputs. Make sure they also include the basic energy carriers '
                             'generated using renewable energy potentials.')
        else:
            self._code = new_code

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, new_type):
        allowed_types = ['thermal', 'electrical', 'combustible', 'radiation']
        if not (new_type in allowed_types):
            raise ValueError("The energy carrier data base contains an invalid energy type. Valid energy carrier "
                             "types are: \n 'thermal', 'electrical', 'combustible', 'radiation'")
        else:
            self._type = new_type

    @property
    def qualifier(self):
        return self._qualifier

    @qualifier.setter
    def qualifier(self, new_qualifier):
        if not (new_qualifier in EnergyCarrier._available_energy_carriers['qualifier'].to_list()):
            raise ValueError('Please make sure all basic energy carrier qualifiers appear in the data base, namely: '
                             'temperature, voltage, wavelength')
        else:
            self._qualifier = new_qualifier

    @property
    def qual_unit(self):
        return self._qual_unit

    @qual_unit.setter
    def qual_unit(self, new_qual_unit):
        if not (new_qual_unit in EnergyCarrier._available_energy_carriers['unit_qual'].to_list()):
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

    @staticmethod
    def _load_energy_carriers(locator):
        EnergyCarrier._available_energy_carriers = pd.read_excel(locator.get_database_energy_carriers())

    @staticmethod
    def _extract_thermal_energy_carriers():
        if EnergyCarrier._available_energy_carriers.empty:
            raise AttributeError('The energy carrier database has not been loaded or was not found.')
        EnergyCarrier._thermal_energy_carriers = \
            EnergyCarrier._available_energy_carriers[EnergyCarrier._available_energy_carriers['type'] == 'thermal']
        if len(EnergyCarrier._thermal_energy_carriers) == 0:
            raise ValueError('No thermal energy carriers could be found in the energy carriers data base.')

    @staticmethod
    def temp_to_thermal_ec(temperature):
        """
        Determine which thermal energy carrier corresponds to a given temperature.

        :param temperature: temperature in °C
        :type temperature: float
        :return energy_carrier_code: code of the corresponding thermal energy carrier
        :rtype energy_carrier_code: str
        """
        if EnergyCarrier._thermal_energy_carriers.empty:
            EnergyCarrier._extract_thermal_energy_carriers()

        thermal_ec_mean_quals = pd.to_numeric(EnergyCarrier._thermal_energy_carriers['mean_qual'])
        if not np.isnan(temperature):
            index_closest_mean_temp = (thermal_ec_mean_quals - temperature).abs().nsmallest(n=1).index[0]
            energy_carrier_code = EnergyCarrier._thermal_energy_carriers['code'].iloc[index_closest_mean_temp]
        else:
            energy_carrier_code = EnergyCarrier._thermal_energy_carriers['code'][0]
            print(f'The temperature level of a renewable energy potential was not available. '
                  f'We assume that the following energy carrier is output: '
                  f'{EnergyCarrier._thermal_energy_carriers["description"][0]}')
        return energy_carrier_code
