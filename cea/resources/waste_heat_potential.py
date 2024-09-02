# -*- coding: utf-8 -*-
"""
Waste heat potential calculation
"""

import pandas as pd
import math
from geopandas import GeoDataFrame as Gdf

import cea.config
import cea.inputlocator
from cea.constants import HOURS_IN_YEAR, P_UPS, P_D, E
from cea.datamanagement.surroundings_helper import find_industries_nearby
from cea.utilities.dbf import dbf_to_dataframe, dataframe_to_dbf

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
    Main function for the calculation of the waste heat potential in the area under analysis. The function identifies industries, 
    extracts the total area and then calculates the waste heat potential. Only waste heat from data centers is implemented.

    """

    # local variables
    avg_max_it_capacity = 13 * 1e6  # [W]
    utilization_rate = 0.3  # utilization rate of the data center

    # Check if there are data centers in the area, otherwise check for industries. If any of the two is found, calculate
    # the total area of the industries in the zone.
    check, tot_area = find_datacenters_inzone(locator)
    if not check:
        industries, check = find_industries_nearby(locator)
        if check:
            tot_area = calculate_industry_total_area(industries)

    # If datacenters or industries are found, calculate the waste heat potential. The temperature is assumed and constant

    if check:
        Qh_waste = datacenter_wasteheat_equation(tot_area, avg_max_it_capacity * utilization_rate) / 1e3  # [kW]
        T_source = 70  # °C
    else:
        T_source = 0
        Qh_waste = 0

    Qh_waste_list = [Qh_waste] * HOURS_IN_YEAR

    # export
    waste_gen = locator.get_wasteheat_potential()
    pd.DataFrame({"Ts_C": T_source, "Qdata_kW": Qh_waste_list}).to_csv(waste_gen, index=False, float_format='%.3f')
    if T_source == 0:
        return
    update_ec(locator, T_source)

def datacenter_wasteheat_equation(area, it_load_power):
    # calculate waste heat for data center from model reported in Rasmussen, Neil. “Calculating Total Cooling Requirements
    # for Data Centers.”

    Qhdata = (1.07 * it_load_power + 0.04 * P_UPS + 0.01 * P_D + 14.32 * area + 100 * E)  # [W]

    # Cooling of the components is assumed to be obtained from the use of a on-chip two phase hybrid cooling system
    # As such, the waste heat is obtained at around 70°C (assuming no losses)

    return Qhdata

def update_ec(locator, temperature):

    ''' 
    This function calls the energy carrier database and adds the new energy carrier based on the temperature calculated.
    In this way, a different lake analysis can easily be updated.
    '''

    water_temp = math.trunc(temperature)
    e_carriers = pd.read_excel(locator.get_database_feedstocks(), sheet_name='ENERGY_CARRIERS')
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

    with pd.ExcelWriter(locator.get_database_feedstocks(), mode="a", engine="openpyxl",
                        if_sheet_exists="replace") as writer:
        e_carriers.to_excel(writer, sheet_name='ENERGY_CARRIERS', index=False)

def calculate_industry_total_area(industries):

    """
    This function calculates the total area of the industries in the area under analysis.

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


def find_datacenters_inzone(locator):
    
    '''
    This function uses OSM database to search for industries in the immediate surroundings, in order to extract waste heat
    '''
    building_typology_df = dbf_to_dataframe(locator.get_building_typology())
    building_type = building_typology_df.set_index(building_typology_df['Name'])
    prop_geometry = Gdf.from_file(locator.get_zone_geometry())

    # Separate list to store index values
    buildings_code = []
    check_server = False
    # Check if 'server' is present in each row of the column and save index if true
    for index, row in building_type.iterrows():
        if 'SERVERROOM' in row['1ST_USE']:
            buildings_code.append(index)
            check_server = True

    if check_server:
        datacenters = prop_geometry.loc[prop_geometry.Name.isin(buildings_code)]
        tot_area = sum(datacenters.area)
    else:
        tot_area = 0

    return check_server, tot_area

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    calc_wasteheat_potential(locator=locator)


if __name__ == '__main__':
    main(cea.config.Configuration())
