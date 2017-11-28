"""
A collection of classes that write out the demand results files. The `cea.globalvar.GlobalVariables.demand_writer`
variable references the `DemandWriter` to use. The default is `HourlyDemandWriter`. A `MonthlyDemandWriter` is provided
that sums the values up monthly. See the `cea.analysis.sensitivity.sensitivity_demand` module for an example of using
the `MonthlyDemandWriter`.
"""

import pandas as pd

# index into the `vars_to_print` structure, that corresponds to `gv.demand_building_csv_columns`
FLOAT_FORMAT = '%.3f'

class DemandWriter(object):
    """
    This is meant to be an abstract base class: Use the subclasses of this class instead.

    Subclasses are expected to:

    - set the `gv` field to a `cea.globalvar.GlobalVariables` instance in the constructor
    - set the `vars_to_print` field in the constructor (FIXME: describe the `vars_to_print` structure.
    - implement the `write_to_csv` method
    """

    def __init__(self):
        self.LOAD_VARS = ['QEf', 'QHf', 'QCf', 'Ef', 'Qhsf', 'Qhs', 'Qhsf_lat', 'Qwwf', 'Qww', 'Qcsf',
                          'Qcs', 'Qcsf_lat', 'Qcdataf', 'Qcref', 'Qhprof', 'Edataf', 'Ealf', 'Eaf', 'Elf',
                          'Eref', 'Eauxf', 'Eauxf_ve', 'Eauxf_hs', 'Eauxf_cs', 'Eauxf_ww', 'Eauxf_fw',
                          'Eprof', 'Ecaf', 'Egenf_cs']
        self.MASS_FLOW_VARS = ['mcphsf', 'mcpcsf', 'mcpwwf', 'mcpdataf', 'mcpref']
        self.TEMPERATURE_VARS = ['Twwf_sup', 'T_int',
                                 'Twwf_re', 'Thsf_sup', 'Thsf_re',
                                 'Tcsf_sup', 'Tcsf_re',
                                 'Tcdataf_re',
                                 'Tcdataf_sup', 'Tcref_re',
                                 'Tcref_sup']
        self.OTHER_VARS = ['Name', 'Af_m2', 'Aroof_m2', 'GFA_m2', 'people0']


    def results_to_hdf5(self, tsd, bpr, locator, date, building_name):
        columns, hourly_data = self.calc_hourly_dataframe(building_name, date, tsd)
        self.write_to_hdf5(building_name, columns, hourly_data, locator)

        # save total for the year
        columns, data = self.calc_yearly_dataframe(bpr, building_name, tsd)
        # save to disc
        pd.DataFrame(data, index=[0]).to_hdf(
            locator.get_temporary_file('%(building_name)sT.hdf' % locals()),
            index=False, columns=columns, float_format='%.3f')

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
        data = dict((x + '_MWhyr', tsd[x].sum() / 1000000) for x in self.LOAD_VARS)
        data.update(dict((x + '0_kW', tsd[x].max() / 1000) for x in self.LOAD_VARS))
        # get order of columns
        keys = data.keys()
        columns = self.OTHER_VARS
        columns.extend(keys)
        # add other default elements
        data.update({'Name': building_name, 'Af_m2': bpr.rc_model['Af'], 'Aroof_m2': bpr.rc_model['Aroof'],
                     'GFA_m2': bpr.rc_model['GFA_m2'], 'people0': tsd['people'].max()})
        return columns, data

    def calc_hourly_dataframe(self, building_name, date, tsd):
        # treating time series data of loads from W to kW
        data = dict((x + '_kWh', tsd[x] / 1000) for x in self.LOAD_VARS)
        # treating time series data of mass_flows from W/C to kW/C
        data.update(dict((x + '_kWperC', tsd[x] / 1000) for x in self.MASS_FLOW_VARS))
        # treating time series data of temperatures from W/C to kW/C
        data.update(dict((x + '_C', tsd[x]) for x in self.TEMPERATURE_VARS))
        # get order of columns
        columns = ['Name', 'people']
        columns.extend([x + '_kWh' for x in self.LOAD_VARS])
        columns.extend([x + '_kWperC' for x in self.MASS_FLOW_VARS])
        columns.extend([x + '_C' for x in self.TEMPERATURE_VARS])
        # add other default elements
        data.update({'DATE': date, 'Name': building_name, 'people': tsd['people']})
        # create dataframe with hourly values of selected data
        hourly_data = pd.DataFrame(data).set_index('DATE')
        return columns, hourly_data


class HourlyDemandWriter(DemandWriter):
    """Write out the hourly demand results"""

    def __init__(self):
        super(HourlyDemandWriter, self).__init__()

    def write_to_csv(self, building_name, columns, hourly_data, locator):
        hourly_data.to_csv(locator.get_demand_results_file(building_name, 'csv'), columns=columns, float_format=FLOAT_FORMAT)

    def write_to_hdf5(self, building_name, columns, hourly_data, locator):
        hourly_data.hdf5(locator.get_demand_results_file(building_name, 'hdf'), columns=columns,
                               float_format=FLOAT_FORMAT)

class MonthlyDemandWriter(DemandWriter):
    """Write out the monthly demand results"""

    def __init__(self):
        super(MonthlyDemandWriter, self).__init__()
        self.MONTHS = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september',
                       'october', 'november', 'december']

    def write_to_csv(self, building_name, columns, hourly_data, locator):
        # get monthly totals and rename to MWhyr
        monthly_data_new = self.calc_monthly_dataframe(building_name, hourly_data)
        monthly_data_new.to_csv(locator.get_demand_results_file(building_name, 'csv'), index=False, float_format=FLOAT_FORMAT)

    def write_to_hdf5(self, building_name, columns, hourly_data, locator):
        # get monthly totals and rename to MWhyr
        monthly_data_new = self.calc_monthly_dataframe(building_name, hourly_data)
        monthly_data_new.to_hdf(locator.get_demand_results_file(building_name, 'hdf'), index=False, float_format=FLOAT_FORMAT)

    def calc_monthly_dataframe(self, building_name, hourly_data):
        monthly_data = hourly_data[[x + '_kWh' for x in self.LOAD_VARS]].groupby(
            by=[hourly_data.index.month]).sum() / 1000

        monthly_data = monthly_data.rename(
            columns=dict((x + '_kWh', x + '_MWhyr') for x in self.LOAD_VARS))

        peaks = hourly_data[[x + '_kWh' for x in self.LOAD_VARS]].groupby(
            by=[hourly_data.index.month]).max()

        peaks = peaks.rename(
            columns=dict((x + '_kWh', x + '0_kW') for x in self.LOAD_VARS))
        monthly_data_new = monthly_data.merge(peaks, left_index=True, right_index=True)
        monthly_data_new['Name'] = building_name
        monthly_data_new['Month'] = self.MONTHS

        return monthly_data_new

class YearlyDemandWriter(DemandWriter):
    """Write out the hourly demand results"""

    def __init__(self):
        super(YearlyDemandWriter, self).__init__()

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
        monthly_data_buildings = [pd.read_csv(locator.get_demand_results_file(building_name, 'csv')) for building_name in
                                  list_buildings]
        return df, monthly_data_buildings

    def write_to_hdf5(self, list_buildings, locator):
        """read in the temporary results files and append them to the Totals.csv file."""
        df = None
        for name in list_buildings:
            temporary_file = locator.get_temporary_file('%(name)sT.csv' % locals())
            if df is None:
                df = pd.read_hdf(temporary_file)
            else:
                df = df.append(pd.read_hdf(temporary_file), ignore_index=True)
        df.to_csv(locator.get_total_demand('hdf'), index=False, float_format='%.3f')

        """read saved data of monthly values and return as totals"""
        monthly_data_buildings = [pd.read_csv(locator.get_demand_results_file(building_name, 'hdf')) for building_name in
                                  list_buildings]
        return df, monthly_data_buildings