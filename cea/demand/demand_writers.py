"""
A collection of classes that write out the demand results files. The default is `HourlyDemandWriter`. A `MonthlyDemandWriter` is provided
that sums the values up monthly. See the `cea.analysis.sensitivity.sensitivity_demand` module for an example of using
the `MonthlyDemandWriter`.
"""





import numpy as np
import pandas as pd

FLOAT_FORMAT = '%.3f'


class DemandWriter(object):
    """
    This is meant to be an abstract base class: Use the subclasses of this class instead.
    Subclasses are expected to:
    - set the `vars_to_print` field in the constructor (FIXME: describe the `vars_to_print` structure.
    - implement the `write_to_csv` method
    """

    def __init__(self, loads, massflows, temperatures):

        from cea.demand.thermal_loads import TSD_KEYS_ENERGY_BALANCE_DASHBOARD, TSD_KEYS_SOLAR

        self.load_vars = loads
        self.load_plotting_vars = TSD_KEYS_ENERGY_BALANCE_DASHBOARD + TSD_KEYS_SOLAR
        self.mass_flow_vars = massflows
        self.temperature_vars = temperatures

        self.OTHER_VARS = ['Name', 'Af_m2', 'Aroof_m2', 'GFA_m2', 'Aocc_m2', 'people0']

    def results_to_hdf5(self, tsd, bpr, locator, date, building_name):
        columns, hourly_data = self.calc_hourly_dataframe(building_name, date, tsd)
        self.write_to_hdf5(building_name, columns, hourly_data, locator)

        # save total for the year
        columns, data = self.calc_yearly_dataframe(bpr, building_name, tsd)
        # save to disc
        partial_total_data = pd.DataFrame(data, index=[0])
        partial_total_data.drop('Name', inplace=True, axis=1)
        partial_total_data.to_hdf(
            locator.get_temporary_file('%(building_name)sT.hdf' % locals()),
            key='dataset')

    def results_to_csv(self, tsd, bpr, locator, date, building_name):
        # save hourly data
        columns, hourly_data = self.calc_hourly_dataframe(building_name, date, tsd)
        self.write_to_csv(building_name, columns, hourly_data, locator)

        # save total for the year
        columns, data = self.calc_yearly_dataframe(bpr, building_name, tsd)
        # save to disc
        pd.DataFrame(data, index=[0]).to_csv(
            locator.get_temporary_file('%(building_name)sT.csv' % locals()),
            index=False, columns=columns, float_format='%.3f')

    def calc_yearly_dataframe(self, bpr, building_name, tsd):
        # if printing total values is necessary
        # treating timeseries data from W to MWh
        data = dict((x + '_MWhyr', tsd[x].sum() / 1000000) for x in self.load_vars)
        data.update(dict((x + '0_kW', tsd[x].max() / 1000) for x in self.load_vars))
        # get order of columns
        keys = data.keys()
        columns = self.OTHER_VARS
        columns.extend(keys)
        # add other default elements
        data.update({'Name': building_name, 'Af_m2': bpr.rc_model['Af'], 'Aroof_m2': bpr.rc_model['Aroof'],
                     'GFA_m2': bpr.rc_model['GFA_m2'], 'Aocc_m2': bpr.rc_model['Aocc'],
                     'people0': tsd['people'].max()})
        return columns, data

    def calc_hourly_dataframe(self, building_name, date, tsd):
        # treating time series data of loads from W to kW
        data = dict((x + '_kWh', np.nan_to_num(tsd[x]) / 1000) for x in
                    self.load_vars)  # TODO: convert nan to num at the very end.
        # treating time series data of loads from W to kW
        data.update(dict((x + '_kWh', np.nan_to_num(tsd[x]) / 1000) for x in
                         self.load_plotting_vars))  # TODO: convert nan to num at the very end.
        # treating time series data of mass_flows from W/C to kW/C
        data.update(dict((x + '_kWperC', np.nan_to_num(tsd[x]) / 1000) for x in
                         self.mass_flow_vars))  # TODO: convert nan to num at the very end.
        # treating time series data of temperatures from W/C to kW/C
        data.update(dict((x + '_C', np.nan_to_num(tsd[x])) for x in
                         self.temperature_vars))  # TODO: convert nan to num at the very end.
        # get order of columns
        columns = ['Name', 'people', 'x_int']
        columns.extend([x + '_kWh' for x in self.load_vars])
        columns.extend([x + '_kWh' for x in self.load_plotting_vars])
        columns.extend([x + '_kWperC' for x in self.mass_flow_vars])
        columns.extend([x + '_C' for x in self.temperature_vars])
        # add other default elements
        data.update({'DATE': date, 'Name': building_name, 'people': tsd['people'], 'x_int': tsd['x_int'] * 1000})
        # create dataframe with hourly values of selected data
        hourly_data = pd.DataFrame(data).set_index('DATE')
        return columns, hourly_data


class HourlyDemandWriter(DemandWriter):
    """Write out the hourly demand results"""

    def __init__(self, loads, massflows, temperatures):
        super(HourlyDemandWriter, self).__init__(loads, massflows, temperatures)

    def write_to_csv(self, building_name, columns, hourly_data, locator):
        hourly_data.to_csv(locator.get_demand_results_file(building_name, 'csv'), columns=columns,
                           float_format=FLOAT_FORMAT)

    def write_to_hdf5(self, building_name, columns, hourly_data, locator):
        # fixing columns with strings
        hourly_data.drop('Name', inplace=True, axis=1)
        hourly_data.to_hdf(locator.get_demand_results_file(building_name, 'hdf'), key='dataset')


class MonthlyDemandWriter(DemandWriter):
    """Write out the monthly demand results"""

    def __init__(self, loads, massflows, temperatures):
        super(MonthlyDemandWriter, self).__init__(loads, massflows, temperatures)
        self.MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september',
                       'october', 'november', 'december']

    def write_to_csv(self, building_name, columns, hourly_data, locator):
        # get monthly totals and rename to MWhyr
        monthly_data_new = self.calc_monthly_dataframe(building_name, hourly_data)
        monthly_data_new.to_csv(locator.get_demand_results_file(building_name, 'csv'), index=False,
                                float_format=FLOAT_FORMAT)

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
        monthly_data_new['Name'] = building_name
        monthly_data_new['Month'] = self.MONTHS

        return monthly_data_new


class YearlyDemandWriter(DemandWriter):
    """Write out the hourly demand results"""

    def __init__(self, loads, massflows, temperatures):
        super(YearlyDemandWriter, self).__init__(loads, massflows, temperatures)

    def write_to_csv(self, list_buildings, locator):
        """read in the temporary results files and append them to the Totals.csv file."""
        df = None
        for name in list_buildings:
            temporary_file = locator.get_temporary_file('%(name)sT.csv' % locals())
            if df is None:
                df = pd.read_csv(temporary_file)
            else:
                df = df.append(pd.read_csv(temporary_file), ignore_index=True)
        df.to_csv(locator.get_total_demand('csv'), index=False, float_format='%.3f')

        """read saved data of monthly values and return as totals"""
        monthly_data_buildings = [pd.read_csv(locator.get_demand_results_file(building_name, 'csv')) for building_name
                                  in
                                  list_buildings]
        return df, monthly_data_buildings

    def write_to_hdf5(self, list_buildings, locator):
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
