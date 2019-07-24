# -*- coding: utf-8 -*-
"""
Sewage source heat exchanger
"""
from __future__ import division

import pandas as pd

import cea.config
import cea.globalvar
import cea.inputlocator
from cea.constants import P_WATER_KGPERM3, HEAT_CAPACITY_OF_WATER_JPERKGK
from cea.resources.geothermal import calc_temperature_underground

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def calc_lake_potential(locator, config):
    """
    Wuick calcualtion of lake potential. THis does nore refere to CEA original publication.
    In that case, the implementation of the Lkae potential algorithm was carried out with another tool and then
    the resutls was implemented in CEA for a specific case study
    # TODO: create proper lake potential model
    """
    # local variables
    conductivity_water = 0.6  # W/mK
    heat_capacity_water = HEAT_CAPACITY_OF_WATER_JPERKGK  # JkgK
    density_water = P_WATER_KGPERM3  # kg.m3
    depth_m = 0.1  # m #just calibrated variable

    V_max_m3h = config.water_body.max_water_volume_withdrawal  # in m3h
    AT_max_K = config.water_body.max_delta_temperature_withdrawal + 273  # to Kelvin
    T_max_K = config.water_body.temperature_max + 273  # to kelvin
    T_min_K = config.water_body.temperature_min + 273  # to kelvin

    T_amplitude_K = abs((T_max_K - T_min_K))
    T_avg_K = (T_max_K + T_min_K) / 2
    t_source = calc_temperature_underground(T_amplitude_K, T_avg_K, conductivity_water, density_water, depth_m,
                                            heat_capacity_water)
    # convert back to degrees C
    t_source_final = [x - 273.0 for x in t_source]

    Q_max_kwh = (V_max_m3h * P_WATER_KGPERM3 / 3600) * heat_capacity_water / 1000 * AT_max_K  # in kW

    # export
    lake_gen = locator.get_lake_potential()
    pd.DataFrame({"Ts_C": t_source_final, "QLake_kW": Q_max_kwh}).to_csv(lake_gen, index=False, float_format='%.3f')


def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    calc_lake_potential(locator=locator, config=config)


if __name__ == '__main__':
    main(cea.config.Configuration())
