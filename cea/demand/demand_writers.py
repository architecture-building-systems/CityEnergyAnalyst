"""
A collection of classes that write out the demand results files. The `cea.globalvar.GlobalVariables.demand_writer`
variable references the `DemandWriter` to use. The default is `HourlyDemandWriter`. A `MonthlyDemandWriter` is provided
that sums the values up monthly. See the `cea.analysis.sensitivity.sensitivity_demand` module for an example of using
the `MonthlyDemandWriter`.
"""

import pandas as pd

# index into the `vars_to_print` structure, that corresponds to `gv.demand_building_csv_columns`
FLOAT_FORMAT = '%.3f'
LOAD_VARS = 0
MASS_FLOW_VARS = 1
TEMPERATURE_VARS = 2

class DemandWriter(object):
    """
    This is meant to be an abstract base class: Use the subclasses of this class instead.

    Subclasses are expected to:

    - set the `gv` field to a `cea.globalvar.GlobalVariables` instance in the constructor
    - set the `vars_to_print` field in the constructor (FIXME: describe the `vars_to_print` structure.
    - implement the `write_to_csv` method
    """
    def __init__(self, gv):
        self.gv = gv
        self.vars_to_print = gv.demand_building_csv_columns

    def results_to_csv(self, tsd, bpr, locator, date, building_name):

        # treating time series data of loads from W to kW
        data = dict((x + '_kWh', tsd[x] / 1000) for x in self.vars_to_print[LOAD_VARS])

        # treating time series data of mass_flows from W/C to kW/C
        data.update(dict((x + '_kWC', tsd[x] / 1000) for x in self.vars_to_print[MASS_FLOW_VARS]))

        # treating time series data of temperatures from W/C to kW/C
        data.update(dict((x + '_C', tsd[x]) for x in self.vars_to_print[TEMPERATURE_VARS]))

        # get order of columns
        columns = ['Name', 'people']
        columns.extend([x + '_kWh' for x in self.vars_to_print[LOAD_VARS]])
        columns.extend([x + '_kWC' for x in self.vars_to_print[MASS_FLOW_VARS]])
        columns.extend([x + '_C' for x in self.vars_to_print[TEMPERATURE_VARS]])

        # add other default elements
        data.update({'DATE': date, 'Name': building_name, 'people': tsd['people']})

        # create dataframe with hourly values of selected data
        hourly_data = pd.DataFrame(data).set_index('DATE')

        self.write_to_csv(building_name, columns, hourly_data, locator)

        if self.gv.print_yearly:
            # treating timeseries data from W to MWh
            data = dict((x + '_MWhyr', tsd[x].sum() / 1000000) for x in self.vars_to_print[LOAD_VARS])

            if self.gv.print_yearly_peak:
                data.update(dict((x + '0_kW', tsd[x].max() / 1000) for x in self.vars_to_print[LOAD_VARS]))

            # get order of columns
            # get order of columns
            keys = data.keys()
            columns = ['Name', 'Af_m2', 'Aroof_m2', 'GFA_m2', 'people0']
            columns.extend(keys)

            # add other default elements
            data.update({'Name': building_name, 'Af_m2': bpr.rc_model['Af'], 'Aroof_m2': bpr.rc_model['Aroof'],
                         'GFA_m2': bpr.rc_model['GFA_m2'], 'people0': tsd['people'].max()})
            yearly_data = pd.DataFrame(data, index=[0]).to_csv(
                locator.get_temporary_file('%(building_name)sT.csv' % locals()),
                index=False, columns=columns, float_format='%.3f')

    def write_to_csv(self, building_name, columns, hourly_data, locator):
        raise NotImplementedError('Use a subclass of DemandWriter instead')


class HourlyDemandWriter(DemandWriter):
    """Write out the hourly demand results"""
    def __init__(self, gv):
        super(HourlyDemandWriter, self).__init__(gv)

    def write_to_csv(self, building_name, columns, hourly_data, locator):
        hourly_data.to_csv(locator.get_demand_results_file(building_name), columns=columns, float_format=FLOAT_FORMAT)


class MonthlyDemandWriter(DemandWriter):
    def __init__(self, gv):
        super(MonthlyDemandWriter, self).__init__(gv)
        self.vars_to_print = [['QEf', 'QHf', 'QCf', 'Ef'], [], []]

    def write_to_csv(self, building_name, columns, hourly_data, locator):
        monthly_data = hourly_data[[x + '_kWh' for x in self.vars_to_print[0]]].groupby(
            by=[hourly_data.index.month]).sum() / 1000
        monthly_data = monthly_data.rename(
            columns=dict((x + '_kWh', x + '_MWhyr') for x in self.vars_to_print[LOAD_VARS]))
        monthly_data['Name'] = building_name
        monthly_data.to_csv(locator.get_demand_results_file(building_name), index=False, float_format=FLOAT_FORMAT)
