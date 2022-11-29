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

import numpy as np
import pandas as pd

from cea.optimization_new.energyCarrier import EnergyCarrier


class EnergyFlow(object):
    time_frame = 8760  # placeholder, this will be made variable in the future

    def __init__(self, input_category=None, output_category=None,
                 energy_carrier_code=None, energy_flow_profile=pd.Series(0.0, index=np.arange(time_frame))):
        if all([input_category is None, output_category is None, energy_carrier_code is None]):
            self._input_category = input_category
            self._output_category = output_category
            self._energy_carrier = energy_carrier_code
            self._profile = energy_flow_profile
            self._identifier = None
            # self._is_cyclic = bool
            # self._qualifier_supply = pd.Series(0.0, index=np.arange(EnergyFlow.time_frame))
            # self._qualifier_return = pd.Series(0.0, index=np.arange(EnergyFlow.time_frame))
        elif not all([input_category is None, output_category is None, energy_carrier_code is None]):
            self.input_category = input_category
            self.output_category = output_category
            self.energy_carrier = energy_carrier_code
            self.profile = energy_flow_profile
            self._identifier = "_".join([input_category[0:2], output_category[0:2], energy_carrier_code])
        else:
            raise ValueError('Please provide a full set of parameters to define this energy flow.')

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
        elif isinstance(new_energy_carrier, type(EnergyCarrier())):
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
        """
        Generate an energy flow inplace of an empty energy flow object.
        """
        if not all([self.input_category is None, self.output_category is None, self.energy_carrier is None]):
            raise TypeError("This energy flow has been generated already, if you want to add another one to it use the "
                            "'add'-method.")
        self.input_category = input_category
        self.output_category = output_category
        self.energy_carrier = energy_carrier_code
        self.profile = energy_flow_profile
        self._identifier = "_".join([input_category[0:2], output_category[0:2], energy_carrier_code])
        return self

    def add(self, energy_flow_profile, subsystem_id=None):
        """
        Add the given energy flow profile to an existing energy flow.
        """
        if isinstance(energy_flow_profile, list) and (subsystem_id is not None):
            profile_df = pd.DataFrame(energy_flow_profile, columns=subsystem_id)
            self.profile = profile_df
        else:
            self.profile = energy_flow_profile

        if (self.input_category != energy_flow_profile.input_category) or (
                self.output_category != energy_flow_profile.output_category):
            print('Nothing')

        return self

    @staticmethod
    def aggregate(energy_flow_list):
        """
        Aggregate energy flow profiles between two component categories by energy carrier.

        :param energy_flow_list: list of energy flows between two component categories (e.g. input_category = 'primary',
                                 output_category = 'secondary')
        :type energy_flow_list: list of <cea.optimization_new.energyFlow>-EnergyFlow objects
        :return aggregated_flows: list of aggregated energy flows (one per energy carrier)
        :rtype aggregated_flows: list of <cea.optimization_new.energyFlow>-EnergyFlow objects
        """
        input_categories = np.unique(np.array([flow.input_category for flow in energy_flow_list]))
        output_categories = np.unique(np.array([flow.output_category for flow in energy_flow_list]))
        if len(input_categories) != 1 or len(output_categories) != 1:
            raise TypeError("All energy flows passed to the 'aggregate'-method need to have the same input and output "
                            "categories have been passed.")

        building_energy_carriers = np.array([flow.energy_carrier.code for flow in energy_flow_list])
        unique_energy_carriers = np.unique(building_energy_carriers)
        aggregated_flows = []
        for energy_carrier in unique_energy_carriers:
            profiles_for_ec = [flow.profile for flow in energy_flow_list if flow.energy_carrier.code == energy_carrier]
            aggregated_profile = pd.concat(profiles_for_ec, axis=1).sum(axis=1)
            aggregated_flows.append(EnergyFlow(input_categories[0], output_categories[0], energy_carrier, aggregated_profile))

        return aggregated_flows
