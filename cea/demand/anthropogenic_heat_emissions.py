"""
Class consolidating anthropogenic heat emissions of a building for selected dates during the year.
The calculated anthropogenic heat emissions are assumed to exclusively come from the building's space
cooling and space heating demand.
"""

import numbers
import numpy as np


class HeatEmissionsProfile:
    time_steps = 24

    def __init__(self, profile=None):
        self.profile = profile

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, profile):
        """Method to make sure the emissions profile is passed in the right format and to set it correspondingly."""
        # Check if the profile is a numpy array and convert it to a list
        if isinstance(profile, np.ndarray):
            profile = profile.tolist()

        # Check if the profile is a list of numerical values
        if not isinstance(profile, list) or not all([isinstance(i, numbers.Number) for i in profile]):
            print (f'The indicated profile is non-numeric. It will be converted to a list of 0s.')
            self._profile = [0.0] * self.time_steps

       # Check if the profile is too long or too short
        if len(profile) == self.time_steps:
            self._profile = profile
        elif len(profile) > self.time_steps:
            print(f'The indicated heat emissions profile is too long ({len(profile)} elements). '
                  f'It will be truncated to {self.time_steps} time steps.')
            self._profile = profile[:self.time_steps]
        else:
            raise ValueError(f'The indicated heat emissions profile is too short ({len(profile)} elements). '
                             f'It should be {self.time_steps} time steps long.')

    def set_profile_length(self, nbr_time_steps):
        self.time_steps = nbr_time_steps


class AnthropogenicHeatEmissions:

    def __init__(self, building, time_series_data, sampling_dates, full_time_series):
        self.building = building
        self.sampling_time_steps = self.get_sampling_time_steps(sampling_dates, full_time_series)
        self.heat_emissions = self.extract_heat_emission_profiles(time_series_data)

    def extract_heat_emission_profiles(self, time_series_data):
        """ Method to extract the heat emissions profile from the time series data for the selected dates."""
        self.heat_emissions = {date: HeatEmissionsProfile([x +y for x, y in
                                                           zip(list(time_series_data['E_cs'][time_steps]),
                                                               list(time_series_data['Qcs_sys'][time_steps]))])
                               for date, time_steps in self.sampling_time_steps.items()}
        return self.heat_emissions

    @staticmethod
    def get_sampling_time_steps(sampling_dates, full_time_series):
        """ Method to get the indices of all time steps in the full time series corresponding to the sampling dates."""
        sampling_time_steps = {sampling_date: np.where(full_time_series.date == sampling_date)[0]
                               for sampling_date in sampling_dates}
        return sampling_time_steps

