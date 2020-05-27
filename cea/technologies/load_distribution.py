import numpy as np
from cea.optimization.constants import COMPRESSOR_TYPE_LIMIT_LOW, COMPRESSOR_TYPE_LIMIT_HIGH, ASHRAE_CAPACITY_LIMIT
from math import ceil

def calc_averaged_PLF(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_cw_in_K, min_chiller_size, max_chiller_size, scale):
    """
    TODO: add documentation here please

    :param float peak_cooling_load:
    :param float q_chw_load_Wh:
    :param float T_chw_sup_K:
    :param float T_cw_in_K:
    :param float min_chiller_size:
    :param float max_chiller_size:
    :param str scale: either "BUILDING" or "DISTRICT"
    :return:
    """
    design_capacity = peak_cooling_load  # * 1.15 # for future implementation, a safety factor could be introduced, in conflict with the master_to_slave_variables.WS_BaseVCC_size_W
    if scale == 'BUILDING':
        if design_capacity <= COMPRESSOR_TYPE_LIMIT_LOW: # if design cooling load smaller lower limit, implement one screw chiller
            source_type = 'WATER'
            compressor_type = 'SCREW'
            n_units = 1
        if COMPRESSOR_TYPE_LIMIT_LOW < design_capacity < COMPRESSOR_TYPE_LIMIT_HIGH:
            source_type = 'WATER'
            compressor_type = 'SCREW'
            n_units = 2
        if design_capacity >= COMPRESSOR_TYPE_LIMIT_HIGH:
            source_type = 'WATER'
            compressor_type = 'CENTRIFUGAL'
            n_units = ceil(design_capacity / ASHRAE_CAPACITY_LIMIT) # according to ASHRAE 90.1 Appendix G, chiller shall not be large then 800 tons (2813 kW)
        cooling_capacity_per_unit = design_capacity / n_units  # calculate the capacity per chiller installed

    if scale == 'DISTRICT':
        source_type = 'WATER'
        compressor_type = 'CENTRIFUGAL'
        if design_capacity <= (2*min_chiller_size):
            n_units = 1
            cooling_capacity_per_unit = max(design_capacity, min_chiller_size)
        elif (2*min_chiller_size) <= design_capacity <= max_chiller_size:
            n_units = 2
            cooling_capacity_per_unit = design_capacity / n_units
        elif design_capacity >= max_chiller_size:
            n_units = max(2, ceil(design_capacity / max_chiller_size)) # have minimum size of capacity to quailfy as DCS, have minimum of 2 chillers
            cooling_capacity_per_unit = design_capacity / n_units

    available_capacity_per_unit = calc_available_capacity(cooling_capacity_per_unit, source_type, compressor_type, T_chw_sup_K, T_cw_in_K) # calculate the available capacity(dependent on conditions)

    ### calculate the load distribution across the chillers heuristically, assuming the PLF factor is monotonously increasing with increasing PLR. Filling one chiller after the other.
    n_chillers_filled = int(q_chw_load_Wh // available_capacity_per_unit)
    part_load_chiller = float(divmod(q_chw_load_Wh, available_capacity_per_unit)[1])/ float(available_capacity_per_unit)

    load_distribution_list = []
    for i in range (n_chillers_filled):
        load_distribution_list.append(1)
    load_distribution_list.append(part_load_chiller)
    for i in range(int(n_units)-n_chillers_filled-1):
        load_distribution_list.append(0)
    load_distribution = np.array(load_distribution_list)

    averaged_PLF = np.sum(calc_PLF(load_distribution, source_type, compressor_type) * load_distribution * available_capacity_per_unit) / q_chw_load_Wh
    return averaged_PLF

def calc_PLF(PLR, source_type, compressor_type):
    """
    takes the part load ratio as an input and outputs the part load factor
    coefficients taken from https://comnet.org/index.php/382-chillers  TODO: create database entry dependent on technology
    """
    if source_type == 'WATER' and compressor_type == 'CENTRIFUGAL':
        plf_a = 0.17149273
        plf_b = 0.58820208
        plf_c = 0.23737257
    if source_type == 'WATER' and compressor_type == 'SCREW':
        plf_a = 0.33018833
        plf_b = 0.23554291
        plf_c = 0.46070828

    PLF = plf_a + plf_b * PLR + plf_c * PLR ** 2
    return PLF

def calc_available_capacity(rated_capacity, source_type, compressor_type, T_chw_sup_K, T_cw_in_K):
    """
    calculates the available Chiller capacity taking the rated capacity as well as
    T_chw_sup_K: supplied chilled water temperature in Kelvin
    T_cw_in_K: condenser water supply temperature in Kelvin
    coefficients taken from https://comnet.org/index.php/382-chillers  TODO: create database entry dependent on technology
    """
    if source_type == 'WATER' and compressor_type == 'CENTRIFUGAL':
        q_a = -0.29861976
        q_b = 0.02996076
        q_c = -0.00080125
        q_d = 0.01736268
        q_e = -0.00032606
        q_f = 0.00063139
    if source_type == 'WATER' and compressor_type == 'SCREW':
        q_a = 0.33269598
        q_b = 0.00729116
        q_c = -0.00049938
        q_d = 0.01598983
        q_e = -0.00028254
        q_f = 0.00052346

    t_chws_F = kelvin_to_fahrenheit(T_chw_sup_K)
    t_cws_F = kelvin_to_fahrenheit(T_cw_in_K)

    available_capacity = rated_capacity * (q_a + q_b*t_chws_F + q_c*t_chws_F**2 + q_d*t_cws_F + q_e * t_cws_F**2 + q_f*t_chws_F*t_cws_F)
    return available_capacity

def kelvin_to_fahrenheit(T_Kelvin):
    # converts the temperature from Kelvin to Fahrenheit
    T_Celsius = T_Kelvin - 273.15
    T_Fahrenheit = (T_Celsius*9/5)+32
    return T_Fahrenheit

def main():
    max_chiller_size = 3500
    peak_cooling_load = 10000
    q_chw_load_Wh = 5000
    T_chw_sup_K = 273.15 + 6
    T_cw_in_K = 273.15 + 28
    a = calc_averaged_PLF(peak_cooling_load, q_chw_load_Wh, T_chw_sup_K, T_cw_in_K, max_chiller_size)
    print('averaged PLF is:', a)

if __name__ == '__main__':
    main()