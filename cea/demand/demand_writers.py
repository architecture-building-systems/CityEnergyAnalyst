"""
A collection of classes that write out the demand results files. The default is `HourlyDemandWriter`. A `MonthlyDemandWriter` is provided
that sums the values up monthly. See the `cea.analysis.sensitivity.sensitivity_demand` module for an example of using
the `MonthlyDemandWriter`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from cea.demand.time_series_data import (ElectricalLoads, HeatingLoads, 
                                       CoolingLoads, FuelSource, HeatingSystemMassFlows, 
                                       CoolingSystemMassFlows, HeatingSystemTemperatures, 
                                       CoolingSystemTemperatures, RCModelTemperatures)

from cea.utilities.reporting import TSD_KEYS_ENERGY_BALANCE_DASHBOARD, TSD_KEYS_SOLAR

if TYPE_CHECKING:
    from cea.demand.building_properties.building_properties_row import BuildingPropertiesRow
    from cea.demand.time_series_data import TimeSeriesData

FLOAT_FORMAT = '%.3f'


def get_all_load_keys():
    """Get all available load keys from time series data classes."""
    load_keys = []
    load_classes = [ElectricalLoads, HeatingLoads, CoolingLoads, FuelSource]
    for cls in load_classes:
        load_keys.extend(list(cls.__dataclass_fields__.keys()))
    return load_keys


def get_all_massflow_keys():
    """Get all available mass flow keys from time series data classes."""
    massflow_keys = []
    massflow_classes = [HeatingSystemMassFlows, CoolingSystemMassFlows]
    for cls in massflow_classes:
        massflow_keys.extend(list(cls.__dataclass_fields__.keys()))
    return massflow_keys


def get_all_temperature_keys():
    """Get all available temperature keys from time series data classes."""
    temperature_keys = []
    temperature_classes = [HeatingSystemTemperatures, CoolingSystemTemperatures, RCModelTemperatures]
    for cls in temperature_classes:
        temperature_keys.extend(list(cls.__dataclass_fields__.keys()))
    return temperature_keys

class DemandWriter(ABC):
    """
    This is meant to be an abstract base class: Use the subclasses of this class instead.
    Subclasses are expected to:
    - set the `vars_to_print` field in the constructor (FIXME: describe the `vars_to_print` structure.
    - implement the `write_to_csv` method
    """

    def __init__(self, loads=None, massflows=None, temperatures=None):
        # If empty lists are provided, generate all available keys
        self.load_vars = loads if loads else get_all_load_keys()
        self.mass_flow_vars = massflows if massflows else get_all_massflow_keys()
        self.temperature_vars = temperatures if temperatures else get_all_temperature_keys()

        self.load_plotting_vars = TSD_KEYS_ENERGY_BALANCE_DASHBOARD | TSD_KEYS_SOLAR

        self.OTHER_VARS = ['name', 'Af_m2', 'Aroof_m2', 'GFA_m2', 'Aocc_m2', 'people0']


    @abstractmethod
    def write_to_csv(self, building_name, columns, hourly_data, locator):
        """
        Write the hourly data to a CSV file.
        """
    
    @abstractmethod
    def write_to_hdf5(self, building_name, columns, hourly_data, locator):
        """
        Write the hourly data to an HDF5 file.
        """

    def results_to_hdf5(self, tsd: TimeSeriesData, bpr: BuildingPropertiesRow, locator, date, building_name):
        columns, hourly_data = self.calc_hourly_dataframe(date, tsd)
        self.write_to_hdf5(building_name, columns, hourly_data, locator)

        # save total for the year
        columns, data = self.calc_yearly_dataframe(bpr, building_name, tsd)
        # save to disc
        partial_total_data = pd.DataFrame(data, index=[0])
        partial_total_data.drop('name', inplace=True, axis=1)
        partial_total_data.to_hdf(
            locator.get_temporary_file('%(building_name)sT.hdf' % locals()),
            key='dataset')

    def results_to_csv(self, tsd: TimeSeriesData, bpr: BuildingPropertiesRow, locator, date, building_name):
        # save hourly data
        columns, hourly_data = self.calc_hourly_dataframe(date, tsd)
        self.write_to_csv(building_name, columns, hourly_data, locator)

        # save annual values to a temp file for YearlyDemandWriter
        columns, data = self.calc_yearly_dataframe(bpr, building_name, tsd)
        pd.DataFrame(data, index=[0]).to_csv(
            locator.get_temporary_file('%(building_name)sT.csv' % locals()),
            index=False, columns=columns, float_format='%.3f', na_rep='nan')

    def calc_yearly_dataframe(self, bpr: BuildingPropertiesRow, building_name, tsd: TimeSeriesData):
        # if printing total values is necessary
        # treating timeseries data from W to MWh
        data = dict((x + '_MWhyr', np.nan_to_num(tsd.get_load_value(x)).sum() / 1000000) for x in self.load_vars)
        data.update(dict((x + '0_kW', np.nan_to_num(tsd.get_load_value(x)).max() / 1000) for x in self.load_vars))
        # get order of columns
        keys = data.keys()
        columns = self.OTHER_VARS
        columns.extend(keys)

        # add other default elements]
        data.update({'name': building_name, 'Af_m2': bpr.rc_model.Af, 'Aroof_m2': bpr.envelope.Aroof,
                     'GFA_m2': bpr.rc_model.GFA_m2, 'Aocc_m2': bpr.rc_model.Aocc,
                     'people0': tsd.occupancy.people.max()})
        return columns, data

    def calc_hourly_dataframe(self, date, tsd: TimeSeriesData):
        # treating time series data of loads from W to kW
        data = dict((x + '_kWh', np.nan_to_num(tsd.get_load_value(x)) / 1000) for x in
                    self.load_vars)  # TODO: convert nan to num at the very end.
        # treating time series data of loads from W to kW
        data.update(dict((x + '_kWh', np.nan_to_num(tsd.get_load_value(x)) / 1000) for x in
                         self.load_plotting_vars))  # TODO: convert nan to num at the very end.
        # treating time series data of mass_flows from W/C to kW/C
        data.update(dict((x + '_kWperC', np.nan_to_num(tsd.get_mass_flow_value(x)) / 1000) for x in
                         self.mass_flow_vars))  # TODO: convert nan to num at the very end.
        # treating time series data of temperatures from W/C to kW/C
        data.update(dict((x + '_C', np.nan_to_num(tsd.get_temperature_value(x))) for x in
                         self.temperature_vars))  # TODO: convert nan to num at the very end.

        # get order of columns
        columns = ['people', 'x_int']
        columns.extend([x + '_kWh' for x in self.load_vars])
        columns.extend([x + '_kWh' for x in self.load_plotting_vars])
        columns.extend([x + '_kWperC' for x in self.mass_flow_vars])
        columns.extend([x + '_C' for x in self.temperature_vars])
        # add other default elements
        data.update({'date': date, 'people': tsd.occupancy.people, 'x_int': tsd.moisture.x_int * 1000})
        # create dataframe with hourly values of selected data
        hourly_data = pd.DataFrame(data).set_index('date')
        return columns, hourly_data


class HourlyDemandWriter(DemandWriter):
    """Write out the hourly demand results"""

    def __init__(self, loads=None, massflows=None, temperatures=None):
        super(HourlyDemandWriter, self).__init__(loads, massflows, temperatures)

    def write_to_csv(self, building_name, columns, hourly_data, locator):
        locator.ensure_parent_folder_exists(locator.get_demand_results_file(building_name, 'csv'))
        hourly_data.to_csv(locator.get_demand_results_file(building_name, 'csv'), columns=columns,
                           float_format=FLOAT_FORMAT, na_rep='nan')

    def write_to_hdf5(self, building_name, columns, hourly_data, locator):
        # fixing columns with strings
        hourly_data.drop('name', inplace=True, axis=1)
        locator.ensure_parent_folder_exists(locator.get_demand_results_file(building_name, 'hdf'))
        hourly_data.to_hdf(locator.get_demand_results_file(building_name, 'hdf'), key='dataset')


class MonthlyDemandWriter(DemandWriter):
    """Write out the monthly demand results"""

    def __init__(self, loads=None, massflows=None, temperatures=None):
        super(MonthlyDemandWriter, self).__init__(loads, massflows, temperatures)
        self.MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september',
                       'october', 'november', 'december']

    def write_to_csv(self, building_name, columns, hourly_data, locator):
        # get monthly totals and rename to MWhyr
        monthly_data_new = self.calc_monthly_dataframe(building_name, hourly_data)
        locator.ensure_parent_folder_exists(locator.get_demand_results_file(building_name, 'csv'))
        monthly_data_new.to_csv(locator.get_demand_results_file(building_name, 'csv'), index=False,
                                float_format=FLOAT_FORMAT, na_rep='nan')

    def write_to_hdf5(self, building_name, columns, hourly_data, locator):
        # get monthly totals and rename to MWhyr
        monthly_data_new = self.calc_monthly_dataframe(building_name, hourly_data)
        monthly_data_new.to_hdf(locator.get_demand_results_file(building_name, 'hdf'), key=building_name)

    def calc_monthly_dataframe(self, building_name, hourly_data):
        monthly_data = hourly_data[[x + '_kWh' for x in self.load_vars]].groupby(
            by=[hourly_data.index.month]).sum() / 1000

        monthly_data = monthly_data.rename(
            columns=dict((x + '_kWh', x + '_MWhyr') for x in self.load_vars))

        peaks = hourly_data[[x + '_kWh' for x in self.load_vars]].groupby(
            by=[hourly_data.index.month]).max()

        peaks = peaks.rename(
            columns=dict((x + '_kWh', x + '0_kW') for x in self.load_vars))
        monthly_data_new = monthly_data.merge(peaks, left_index=True, right_index=True)
        monthly_data_new['name'] = building_name
        monthly_data_new['Month'] = self.MONTHS

        return monthly_data_new


def aggregate_results(locator, building_names):
    aggregated_hourly_results_df = pd.DataFrame()

    for i, building in enumerate(building_names):
        hourly_results_per_building = pd.read_csv(locator.get_demand_results_file(building)).set_index('date')
        if i == 0:
            aggregated_hourly_results_df = hourly_results_per_building
        else:
            aggregated_hourly_results_df += hourly_results_per_building

    return aggregated_hourly_results_df


class YearlyDemandWriter:
    """Write out the yearly demand results"""

    @staticmethod
    def write_aggregate_buildings(locator, building_names):
        """read in the temporary results files and append them to the Total_demand_building.csv file."""
        df = None
        for building in building_names:
            temporary_file = locator.get_temporary_file('%(building)sT.csv' % locals())
            if df is None:
                df = pd.read_csv(temporary_file)
            else:
                df = pd.concat([df, pd.read_csv(temporary_file)], ignore_index=True)
        
        if df is not None:
            locator.ensure_parent_folder_exists(locator.get_total_demand('csv'))
            df.to_csv(locator.get_total_demand('csv'), index=False, float_format='%.3f', na_rep='nan')

    @staticmethod
    def write_aggregate_hourly(locator, building_names):
        """read in the building files and append them to the Total_demand_hourly.csv file."""
        aggregated_hourly_results_df = pd.DataFrame()

        for i, building in enumerate(building_names):
            hourly_results_per_building = pd.read_csv(locator.get_demand_results_file(building)).set_index('date')
            if i == 0:
                aggregated_hourly_results_df = hourly_results_per_building
            else:
                aggregated_hourly_results_df += hourly_results_per_building

        aggregated_hourly_results_df = aggregated_hourly_results_df.drop(columns=['x_int'])

        # save hourly results
        locator.ensure_parent_folder_exists(locator.get_total_demand_hourly('csv'))
        aggregated_hourly_results_df.to_csv(locator.get_total_demand_hourly('csv'),
                                            index=True, float_format='%.3f', na_rep='nan')

    @staticmethod
    def write_to_hdf5(locator, list_buildings):
        """read in the temporary results files and append them to the Totals.csv file."""
        df = None
        for name in list_buildings:
            temporary_file = locator.get_temporary_file('%(name)sT.hdf' % locals())
            if df is None:
                df = pd.read_hdf(temporary_file, key='dataset')
            else:
                df = df.append(pd.read_hdf(temporary_file, key='dataset'))
        df.to_hdf(locator.get_total_demand('hdf'), key='dataset')

        """read saved data of monthly values and return as totals"""
        monthly_data_buildings = [pd.read_hdf(locator.get_demand_results_file(building_name, 'hdf'), key=building_name)
                                  for building_name in
                                  list_buildings]
        return df, monthly_data_buildings
