"""
Energy Flow Class:
defines all properties of energy flows between components of district cooling systems:
CHARACTERISTICS:
- Input category: category of the DCS-component the flow originates from
- Output category: category of the DCS-component the energy flows to
- Energy carrier the flow consists of
VALUES:
- Quantity of energy that is transferred at tech time step
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

from cea.optimization_new.energyCarrier import EnergyCarrier


class EnergyFlow(object):
    time_frame = 8760  # placeholder, this will be made variable in the future

    def __init__(self):
        self._identifier = 'e.g. so_se_T100H'
        self._input_category = 'e.g. source'
        self._output_category = 'e.g. secondary'
        self._energy_carrier = EnergyCarrier()
        self._profile = pd.Series()

    @property
    def input_category(self):
        return self._input_category

    @input_category.setter
    def input_category(self, new_input_category):
        allowed_input_categories = ['source', 'primary', 'secondary', 'tertiary', 'storage']
        if not (new_input_category in allowed_input_categories):
            raise ValueError('An invalid input category was specified for an energy flow.')
        else:
            self._input_category = new_input_category

    @property
    def output_category(self):
        return self._output_category

    @output_category.setter
    def output_category(self, new_output_category):
        allowed_output_categories = ['primary', 'secondary', 'tertiary', 'storage', 'consumer', 'environment']
        if not (new_output_category in allowed_output_categories):
            raise ValueError('An invalid output category was specified for an energy flow.')
        else:
            self._output_category = new_output_category

    @property
    def energy_carrier(self):
        return self._energy_carrier

    @energy_carrier.setter
    def energy_carrier(self, new_energy_carrier):
        if isinstance(new_energy_carrier, str):
            try:
                self._energy_carrier = EnergyCarrier(new_energy_carrier)
            except ValueError:
                raise ValueError('The indicated energy carrier code is invalid.')
        elif isinstance(new_energy_carrier, type(EnergyCarrier())) and (new_energy_carrier.identifier is not None):
            self._energy_carrier = new_energy_carrier
        else:
            raise ValueError('Please indicate a valid energy carrier.')

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, new_profile):
        if not (isinstance(new_profile, pd.Series) and (len(new_profile) == self.time_frame)):
            raise ValueError(f'The energy flow profile does not have the correct format, i.e. numerical series of '
                             f'{self.time_frame} time steps.')
        else:
            self._profile = new_profile

    def generate(self, input_category, output_category, energy_carrier_code, energy_flow_profile):
        self.input_category = input_category
        self.output_category = output_category
        self.energy_carrier = energy_carrier_code
        self.profile = energy_flow_profile

        self._identifier = "_".join([input_category[0:2], output_category[0:2], energy_carrier_code])

        return self
