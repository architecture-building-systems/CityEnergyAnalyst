"""
Energy Flow Class:
defines all properties of energy flows between components of district cooling systems:
CHARACTERISTICS:
- Input category: placement of the DCS-component the flow originates from
- Output category: placement of the DCS-component the energy flows to
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

from cea.optimization_new.containerclasses.energyCarrier import EnergyCarrier


class EnergyFlow(object):
    time_frame = 8760  # TODO: turn this into a variable (i.e. replace by timeframe given by typical days approach)
    allow_negative_flows = False

    def __init__(self, input_category=None, output_category=None,
                 energy_carrier_code=None, energy_flow_profile=pd.Series(0.0, index=np.arange(time_frame))):
        if all([input_category is None, output_category is None, energy_carrier_code is None]):
            self._input_category = input_category
            self._output_category = output_category
            self._energy_carrier = energy_carrier_code
            self._profile = energy_flow_profile
            self._identifier = None
            # self._is_cyclic = bool  # TODO: introduce these variables when more complex component models are added
            # self._supply_profile = pd.Series(0.0, index=np.arange(EnergyFlow.time_frame))
            # self._return_profile = pd.Series(0.0, index=np.arange(EnergyFlow.time_frame))
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
        allowed_input_categories = ['source', 'primary', 'secondary', 'tertiary', 'storage', 'primary or secondary',
                                    'passive_conversion']
        if new_input_category not in allowed_input_categories:
            raise ValueError('An invalid component-placement was specified as the origin of energy flow.')
        else:
            self._input_category = new_input_category

    @property
    def output_category(self):
        return self._output_category

    @output_category.setter
    def output_category(self, new_output_category):
        allowed_output_categories = ['primary', 'secondary', 'tertiary', 'storage', 'consumer', 'environment',
                                     'passive_conversion']
        if new_output_category not in allowed_output_categories:
            raise ValueError('An invalid component-placement was specified as the target an energy flow.')
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
        if isinstance(new_profile, pd.Series) and (len(new_profile) in [1, self.time_frame]):
            if new_profile.min() < 0 and not EnergyFlow.allow_negative_flows:
                new_profile[new_profile < 0] = 0.0
            self._profile = new_profile
        else:
            raise ValueError(f'The energy flow profile does not have the correct format, '
                             f'i.e. numerical series of {self.time_frame} time steps or single numerical value.')

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

    def __add__(self, energy_flow):
        """
        Add the given energy flow profile to an existing energy flow.
        """
        if isinstance(energy_flow, (float, int)):
            new_profile = self.profile + energy_flow
        elif isinstance(energy_flow, list):
            new_profile = self.profile.add(energy_flow)
        elif isinstance(energy_flow, pd.Series):
            new_profile = sum([self.profile, energy_flow])
        elif isinstance(energy_flow, EnergyFlow):
            new_profile = sum([self.profile, energy_flow.profile])
        else:
            raise TypeError('Make sure the energy flow you indicated is either in a list, pd.Series or EnergyFlow '
                            f'format. Your indicated variable has is of type {type(energy_flow)}.')

        sum_of_energy_flows = EnergyFlow(self.input_category, self.output_category, self.energy_carrier.code,
                                         new_profile)

        return sum_of_energy_flows

    def __sub__(self, energy_flow):
        """
        Subtract the given energy flow profile from an existing energy flow.
        """
        if isinstance(energy_flow, (float, int)):
            new_profile = self.profile - energy_flow
        elif isinstance(energy_flow, list):
            energy_flow = [-flow for flow in energy_flow]
            new_profile = self.profile.add(energy_flow)
        elif isinstance(energy_flow, pd.Series):
            new_profile = sum([self.profile, -energy_flow])
        elif isinstance(energy_flow, EnergyFlow):
            new_profile = sum([self.profile, -energy_flow.profile])
        else:
            raise TypeError('Make sure the energy flow you indicated is either in a list, pd.Series or EnergyFlow '
                            f'format. Your indicated variable has is of type {type(energy_flow)}.')

        sum_of_energy_flows = EnergyFlow(self.input_category, self.output_category, self.energy_carrier.code,
                                         new_profile)

        return sum_of_energy_flows

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
                            "categories. Please check the energy flows you are trying to aggregate.")

        building_energy_carriers = np.array([flow.energy_carrier.code for flow in energy_flow_list])
        unique_energy_carriers = np.unique(building_energy_carriers)
        aggregated_flows = []
        for energy_carrier in unique_energy_carriers:
            profiles_for_ec = [flow.profile for flow in energy_flow_list if flow.energy_carrier.code == energy_carrier]
            aggregated_profile = pd.concat(profiles_for_ec, axis=1).sum(axis=1)
            aggregated_flows.append(
                EnergyFlow(input_categories[0], output_categories[0], energy_carrier, aggregated_profile))

        return aggregated_flows

    def cap_at(self, profile_threshold):
        """
        Create a copy of the given energy flow only with the profile capped at a given threshold.
        """
        new_energy_flow = EnergyFlow(self.input_category, self.output_category, self.energy_carrier.code,
                                     self.profile.clip(upper=profile_threshold))

        return new_energy_flow
