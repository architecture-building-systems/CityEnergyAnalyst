import pandas as pd
import os
from cea.utilities import dbf
import cea.globalvar
import cea.inputlocator

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def calc_spatio_temporal_visuals(locator, period, variables_to_plot, list_of_buildings, initial_date):

    # now the dates in which the building demand is calculated is stored in 'date'
    date = pd.date_range(initial_date, periods=8760, freq='H')[period[0]: period[1]]
    time = date.strftime("%Y%m%d%H%M%S")

    # this loop checks if all the buildings are selected and gets the building names from Total demand.csv file
    if 'all' in list_of_buildings:
        building_names = pd.read_csv(locator.get_total_demand())['Name'].values
    else:
        building_names = list_of_buildings

    for i, building in enumerate(building_names):
        # importing corresponding variables of each building and then slicing it to take just a single period value i.e a time step
        data = pd.read_csv(locator.get_demand_results_file(building))[variables_to_plot][period[0]: period[1]]
        data['date'] = time
        data['Name'] = building

        if i == 0:
            final = data
        else:
            final = final.append(data, ignore_index=True)

    dbf.dataframe_to_dbf(final, locator.get_4D_demand_plot(period))

def run_as_script():
    import cea.inputlocator
    import cea.config
    config = cea.config.Configuration()

    locator = cea.inputlocator.InputLocator(scenario_path=config.scenario)

    variables_to_plot = ['Qww_sys_kWh', 'QEf_kWh', 'Qhs_sys_kWh', 'Qcs_sys_kWh']
    initial_date = '1/1/2015'
    list_of_buildings = ['all']  # 'all' for all buildings or else provide a list of building names
    period = [1, 168] # period in hours of the year to viualize
    calc_spatio_temporal_visuals(locator, period, variables_to_plot, list_of_buildings, initial_date)

if __name__ == '__main__':
    run_as_script()
