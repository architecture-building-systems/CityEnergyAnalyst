# -*- coding: utf-8 -*-
"""
Comfort models
"""




import numpy as np
import pythermalcomfort

from cea.demand.latent_loads import calc_saturation_pressure, P_ATM


def calc_pmv_pdd_ashrae(tsd, bpr, config):
    """
    Calculate thermal comfort metrics (predicted mean vote -PMV-, predicted percentage of dissatisfied -PPD- and
    thermal sensation vote -TSV-) of a single building using pythermalcomfort.
    The calculation procedure follows the methodology of ASHRAE 55.

    :param tsd: Timestep data
    :type tsd: Dict[str, numpy.ndarray]

    :param bpr: a collection of building properties for the building used for thermal loads calculation
    :type bpr: BuildingPropertiesRow

    :returns pmv: Predicted Mean Vote (PMV)
    :returns ppd: Predicted Percentage of Dissatisfied (PPD)
    :returns tsv: Predicted thermal sensation vote
    :rtype pmv: float
    :rtype ppd: float
    :rtype tsv: float

    """

    T_dry_bulb = tsd['T_int']
    T_operative = tsd['theta_o']
    T_mean_radiant = calc_mean_radiant_temperature(T_dry_bulb, T_operative)
    relative_humidity = convert_moisture_content_to_rh(tsd)
    air_velocity = convert_flow_rate_to_velocity(bpr, tsd)
    met = calc_met_from_sensible_gains(tsd)
    clo = config.comfort.clo
    relative_air_velocity = pythermalcomfort.utilities.v_relative(air_velocity, met)

    results = pythermalcomfort.models.pmv_ppd_ashrae.pmv_ppd_ashrae(
        tdb=T_dry_bulb, tr=T_mean_radiant, vr=relative_air_velocity, rh=relative_humidity, met=met, clo=clo)

    return results.pmv, results.ppd, results.tsv


def calc_met_from_sensible_gains(tsd):
    '''
    This is a simple estimate of the metabolic rate based on the sensible heat gains.
    This was done by:
        1. assuming met values for each use type in CEA based on the reference values in pythermalcomfort and the
            engineering toolbox (https://www.engineeringtoolbox.com/met-metabolic-rate-d_733.html)
            'INDUSTRIAL': default Qs_Wp = 90 => assume met = 3
            'GYM': default Qs_Wp = 120=> assume met = 6
            all others: default_Qs_Wp = 70 => assume met = 1
        2. estimating the relationship by linear regression

    :return met: metabolic rate [met]
    :rtype met: float
    '''

    # sensible heat gain per person
    Qs_Wp = tsd['Qs'] / tsd['people']
    # assume minimum met is for sleeping
    met_min = pythermalcomfort.utilities.met_typical_tasks['Sleeping']
    # estimate met
    met = np.vectorize(max)(0.1 * Qs_Wp - 6, met_min)

    return met


def convert_flow_rate_to_velocity(bpr, tsd):
    '''
    Estimate air velocity from ventilation flow rate and building floor area
    NOTE: This calculation gives very low results!! If using the CEA archetypes, the maximum air velocity is 0.005556
    : return v_ms: Air velocity [m/s]
    : rtype : float
    '''
    ve_m3s = tsd['ve_lps'] * 1e-3         # ventilation [m3/s]
    v_ms = ve_m3s / bpr.rc_model['Aocc']  # air velocity [m/s]

    return v_ms


def convert_moisture_content_to_rh(tsd):
    '''
    This function is the inversion of the function cea.demand.convert_moisture_content_to_rh
    '''
    return 100 * tsd['x_int'] * P_ATM / (0.622 * calc_saturation_pressure(tsd['T_int']))


def calc_mean_radiant_temperature(T_dry_bulb, T_operative):
    '''
    The mean radiant temperature is the weighted mean of the room surface temperatures. However, we don't have the
    surface temperatures as part of the CEA thermal loads calculation.
    At low air speeds, the operative temperature of a space is the average of the air temperature and the mean radiant
    temperature [Hawks & Cho, 2024, who in turn cite ASHRAE Standard 55-2020]
    :param T_dry_bulb:  dry bulb temperature [C]
    :type tilt_radians: float
    :param T_operative: operative temperature [C]
    :type T_operative: float
    :return : mean radiant temperature [C]
    :rtype : float

    :References: Hawks, M.A. and Cho, S. (2024) Review and analysis of current solutions and trends for zero energy
                 building (ZEB) thermal systems. Renewable and Sustainable Energy Reviews 189, Part B: 114028.
                 doi: 10.1016/j.rser.2023.114028
    '''

    return 2 * T_operative - T_dry_bulb

