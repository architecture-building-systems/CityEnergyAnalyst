# -*- coding: utf-8 -*-
"""
Waste heat potential calculation
"""




import pandas as pd
import math

import cea.config
import cea.inputlocator
from cea.constants import HOURS_IN_YEAR, P_UPS, P_D, E
from cea.datamanagement.surroundings_helper import find_datacenters_nearby

__author__ = "Giuseppe Nappi"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = 'Giuseppe Nappi'
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = 'Giuseppe Nappi'
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_wasteheat_potential(locator):
    """
    Main function for the calculation of the waste heat potential in the area. The function calculates the total area of
    the industries in the area and then calculates the waste heat potential (from the data centers) in the area.

    """
    # local variables
    avg_max_it_capacity = 13 * 1e6  # [W]
    utilization_rate = 0.3  # utilization rate of the data center

    industries, check = find_datacenters_nearby(locator)
    if check:
        tot_area = calculate_industry_total_area(industries)
        Qh_waste = datacenter_wasteheat_equation(tot_area, avg_max_it_capacity * utilization_rate) / 1e3  # [kW]
        T_source = 70  # °C
    else:
        T_source = 0
        Qh_waste = 0

    Qh_waste_list = [Qh_waste] * HOURS_IN_YEAR

    # export
    waste_gen = locator.get_wasteheat_potential()
    pd.DataFrame({"Ts_C": T_source, "Qdata_kW": Qh_waste_list}).to_csv(waste_gen, index=False, float_format='%.3f')
    update_ec(locator, T_source)

def datacenter_wasteheat_equation(area, it_load_power):
    # calculate waste heat for data center from model reported in Rasmussen, Neil. “Calculating Total Cooling Requirements
    # for Data Centers.”

    Qhdata = (1.07 * it_load_power + 0.04 * P_UPS + 0.01 * P_D + 14.32 * area + 100 * E)  # [W]
    # Cooling of the components is assumed to be obtained from the use of a on-chip two phase hybrid cooling system
    # As such, the waste heat is obtained at around 70°C (assuming no losses)

    return Qhdata

def update_ec(locator, temperature):
    water_temp = math.trunc(temperature)
    e_carriers = pd.read_excel(locator.get_database_energy_carriers(), sheet_name='ENERGY_CARRIERS')
    row_copy = e_carriers.loc[e_carriers['description'] == 'Fresh water'].copy()
    row_copy['mean_qual'] = water_temp
    row_copy['code'] = f'T{water_temp}W'
    row_copy['description'] = 'Wasteheat Water'
    row_copy['subtype'] = 'water'

    if not e_carriers.loc[e_carriers['description'] == 'Wasteheat Water'].empty:
        row_copy.index = e_carriers.loc[e_carriers['description'] == 'Wasteheat Water'].index
        e_carriers.loc[e_carriers['description'] == 'Wasteheat Water'] = row_copy.copy()
    else:
        e_carriers = pd.concat([e_carriers, row_copy], axis=0)

    e_carriers.to_excel(locator.get_database_energy_carriers(), sheet_name='ENERGY_CARRIERS', index=False)

def calculate_industry_total_area(industries):
    """
    This function calculates the total area of the industries in the area, in case it is needed for the waste heat
    calculation.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 10))
    industries.plot(column='building', categorical=True, legend=True, ax=ax)
    plt.title('Industries in the area')
    # plt.show()

    list_floors_nr = industries['building:levels'].values

    floor_nr = []
    for item in list_floors_nr:
        x = float(item)

        if not math.isnan(x):
            floor_nr.append(int(x))
        else:
            floor_nr.append(1)

    industrial_area = industries.area
    tot_area = sum(industrial_area * floor_nr)


    return tot_area

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    calc_wasteheat_potential(locator=locator)


if __name__ == '__main__':
    main(cea.config.Configuration())
