""
from __future__ import division

import multiprocessing as mp
import pandas as pd
import time
import numpy as np
from cea.demand import thermal_loads as tl
from cea.technologies import controllers
from cea.demand import sensible_loads
from cea.demand import electrical_loads
from cea.demand import hotwater_loads
from cea.demand import refrigeration_loads
from cea.demand import datacenter_loads
from cea.utilities import helpers
from sandbox.ghapple import energy_demand_heating_cooling as edhc
from sandbox.ghapple import ventilation_xx as v


import cea.globalvar
import cea.inputlocator
from cea.demand import occupancy_model
from cea.demand import thermal_loads
from cea.demand.thermal_loads import BuildingProperties
from cea.utilities import epwreader

def testing_gabriel(locator, weather_path, gv):

    t0 = time.clock()

    gv = cea.globalvar.GlobalVariables()

    date = pd.date_range(gv.date_start, periods=8760, freq='H')

    # weather model
    weather_data = epwreader.epw_reader(weather_path)[['drybulb_C', 'relhum_percent', 'windspd_ms', 'skytemp_C']]

    # building properties model
    building_properties = BuildingProperties(locator, gv)

    # schedules model
    list_uses = list(building_properties._prop_occupancy.drop('PFloor', axis=1).columns)
    schedules = occupancy_model.schedule_maker(date, locator, list_uses)
    schedules_dict = {'list_uses': list_uses, 'schedules': schedules}

    # demand model
    num_buildings = len(building_properties)


    # prepare for thermal loads
    usage_schedules = schedules_dict
    bpr = building_properties['B01']


    # thermal loads
    tsd = {'T_ext': weather_data.drybulb_C.values,
           'rh_ext': weather_data.relhum_percent.values,
           'T_sky': weather_data.skytemp_C.values,
           'Ts' : np.empty(8760) * np.nan,
           'Ta': np.empty(8760) * np.nan,
           'Tm': np.empty(8760) * np.nan,
           'Qhs_sen': np.empty(8760) * np.nan,
           'Qcs_sen': np.empty(8760) * np.nan,
           'Qhs_lat': np.empty(8760) * np.nan,
           'Qcs_lat': np.empty(8760) * np.nan,
           'Top': np.empty(8760) * np.nan,
           'Im_tot': np.empty(8760) * np.nan,
           'Ehs_lat_aux': np.empty(8760) * np.nan,
           'Qhs_em_ls': np.empty(8760) * np.nan,
           'Qcs_em_ls': np.empty(8760) * np.nan,
           'ma_sup_hs': np.empty(8760) * np.nan,
           'ma_sup_cs': np.empty(8760) * np.nan,
           'Ta_sup_hs': np.empty(8760) * np.nan,
           'Ta_sup_cs': np.empty(8760) * np.nan,
           'Ta_re_hs': np.empty(8760) * np.nan,
           'Ta_re_cs': np.empty(8760) * np.nan,
           'w_re': np.empty(8760) * np.nan,
           'w_sup': np.empty(8760) * np.nan,
           'Tww_re': np.empty(8760) * np.nan,
           'I_sol': np.empty(8760) * np.nan,
           'I_int_sen': np.empty(8760) * np.nan,
           'w_int': np.empty(8760) * np.nan,
           'm_ve_mech': np.empty(8760) * np.nan,
           'm_ve_window': np.empty(8760) * np.nan,
           'I_rad': np.empty(8760) * np.nan,
           'I_ia': np.empty(8760) * np.nan,
           'I_m': np.empty(8760) * np.nan,
           'I_st': np.empty(8760) * np.nan,
           'QEf': np.empty(8760) * np.nan,
           'QHf': np.empty(8760) * np.nan,
           'QCf': np.empty(8760) * np.nan,
           'Ef': np.empty(8760) * np.nan,
           'Qhsf': np.empty(8760) * np.nan,
           'Qhs': np.empty(8760) * np.nan,
           'Qhsf_lat': np.empty(8760) * np.nan,
           'Qwwf': np.empty(8760) * np.nan,
           'Qww': np.empty(8760) * np.nan,
           'Qcsf': np.empty(8760) * np.nan,
           'Qcs': np.empty(8760) * np.nan,
           'Qcsf_lat': np.empty(8760) * np.nan,
           'Qhprof': np.empty(8760) * np.nan,
           'Eauxf': np.empty(8760) * np.nan,
           'Eauxf_ve': np.empty(8760) * np.nan,
           'Eauxf_hs': np.empty(8760) * np.nan,
           'Eauxf_cs': np.empty(8760) * np.nan,
           'Eauxf_ww': np.empty(8760) * np.nan,
           'Eauxf_fw': np.empty(8760) * np.nan,
           'mcphsf': np.empty(8760) * np.nan,
           'mcpcsf': np.empty(8760) * np.nan,
           'mcpwwf': np.empty(8760) * np.nan,
           'Twwf_sup': np.empty(8760) * np.nan,
             'Twwf_re': np.empty(8760) * np.nan, 'Thsf_sup': np.empty(8760) * np.nan, 'Thsf_re': np.empty(8760) * np.nan,
             'Tcsf_sup': np.empty(8760) * np.nan, 'Tcsf_re': np.empty(8760) * np.nan,
             'Tcdataf_re': np.empty(8760) * np.nan,
             'Tcdataf_sup': np.empty(8760) * np.nan, 'Tcref_re': np.empty(8760) * np.nan,
             'Tcref_sup': np.empty(8760) * np.nan, 'theta_ve_mech': np.empty(8760) * np.nan, 'h_ve_adj': np.empty(8760) * np.nan, 'Qcs_lat_HVAC':  np.empty(8760) * np.nan, 'Qcs_sen_HVAC':  np.empty(8760) * np.nan}  # TODO: initialize refrigeration loads, etc.

    # get schedules
    list_uses = usage_schedules['list_uses']
    schedules = usage_schedules['schedules']

    # get n50 value
    n50 = bpr.architecture['n50']

    # get occupancy
    tsd['people'] = occupancy_model.calc_occ(list_uses, schedules, bpr)

    # get electrical loads (no auxiliary loads)
    tsd = tl.electrical_loads.calc_Eint(tsd, bpr, list_uses, schedules)

    # get refrigeration loads
    tsd['Qcref'], tsd['mcpref'], \
    tsd['Tcref_re'], tsd['Tcref_sup'] = np.vectorize(refrigeration_loads.calc_Qcref)(tsd['Eref'])

    # get server loads
    tsd['Qcdataf'], tsd['mcpdataf'], \
    tsd['Tcdataf_re'], tsd['Tcdataf_sup'] = np.vectorize(datacenter_loads.calc_Qcdataf)(tsd['Edataf'])

    # ground water temperature in C during heating season (winter) according to norm
    tsd['Twwf_re'][:] = bpr.building_systems['Tww_re_0']

    # ground water temperature in C during non-heating season (summer) according to norm  -  FIXME: which norm?
    tsd['Twwf_re'][gv.seasonhours[0] + 1:gv.seasonhours[1] - 1] = 14

    if bpr.rc_model['Af'] > 0:  # building has conditioned area

        v.calc_m_ve_required(bpr, tsd)
        v.calc_m_ve_leakage_simple(bpr, tsd, gv)

        # get internal comfort properties
        tsd = controllers.calc_simple_temp_control(tsd, bpr.comfort, gv.seasonhours[0] + 1, gv.seasonhours[1],
                                                      date.dayofweek)

        # minimum mass flow rate of ventilation according to schedule
        # with infiltration and overheating
        #tsd['qv_req'] = np.vectorize(controllers.calc_simple_ventilation_control)(tsd['ve'], tsd['people'], bpr.rc_model['Af'], gv,
               #                                                       date.hour, range(8760), n50)
        #tsd['qm_ve_req'] = tsd['qv_req'] * gv.Pair  # TODO:  use dynamic rho_air

        # latent heat gains
        tsd['w_int'] = sensible_loads.calc_Qgain_lat(tsd['people'], bpr.internal_loads['X_ghp'],
                                                     bpr.hvac['type_cs'],
                                                     bpr.hvac['type_hs'])

        # natural ventilation building propertiess
        # new
        #dict_props_nat_vent = ventilation_model.get_properties_natural_ventilation(
           # bpr.geometry,
          #  bpr.architecture, gv)

        # create flag season FIXME: rename, e.g. "is_not_heating_season" or something like that...
        # FIXME: or work with gv.is_heating_season(t)?
        #tsd['flag_season'] = np.zeros(8760, dtype=bool)  # default is heating season
        #tsd['flag_season'][gv.seasonhours[0] + 1:gv.seasonhours[1]] = True  # True means cooling season

        # end-use demand calculation
        for t in range(-720, 8760):

            hoy = helpers.seasonhour_2_hoy(t, gv)

            # heat flows in [W]
            # sensible heat gains
            # --> moved to inside of procedure

            edhc.procedure_1(bpr, tsd, hoy, gv)

        tsd['Qhs_sen_incl_em_ls'] = tsd['Qhs_sen'] + tsd['Qhs_em_ls']
        tsd['Qcs_sen_incl_em_ls'] = tsd['Qcs_sen'] + tsd['Qcs_em_ls']

        # Calc of Qhs_dis_ls/Qcs_dis_ls - losses due to distribution of heating/cooling coils
        Qhs_d_ls, Qcs_d_ls = np.vectorize(sensible_loads.calc_Qhs_Qcs_dis_ls)(tsd['Ta'], tsd['T_ext'],
                                                                                  tsd['Qhs_sen_incl_em_ls'],
                                                                                  tsd['Qcs_sen_incl_em_ls'],
                                                                                  bpr.building_systems['Ths_sup_0'],
                                                                                  bpr.building_systems['Ths_re_0'],
                                                                                  bpr.building_systems['Tcs_sup_0'],
                                                                                  bpr.building_systems['Tcs_re_0'],
                                                                                  np.nanmax(tsd['Qhs_sen_incl_em_ls']),
                                                                                  np.nanmin(tsd['Qcs_sen_incl_em_ls']),
                                                                                  gv.D, bpr.building_systems['Y'][0],
                                                                                  bpr.hvac['type_hs'],
                                                                                  bpr.hvac['type_cs'], gv.Bf,
                                                                                  bpr.building_systems['Lv'])

        tsd['Qcsf_lat'] = tsd['Qcs_lat_HVAC']

        # Calc requirements of generation systems (both cooling and heating do not have a storage):
        tsd['Qhs'] = tsd['Qhs_sen']
        tsd['Qhsf'] = tsd['Qhs'] + tsd['Qhs_em_ls'] + Qhs_d_ls  # no latent is considered because it is already added a
        # s electricity from the adiabatic system.
        tsd['Qcs'] = (tsd['Qcs_sen']) + tsd['Qcsf_lat']
        tsd['Qcsf'] = tsd['Qcs'] + tsd['Qcs_em_ls'] + Qcs_d_ls
        tsd['Qcsf'] = -abs(tsd['Qcsf'])
        tsd['Qcs'] = -abs(tsd['Qcs'])

        # Calc nomincal temperatures of systems
        Qhsf_0 = np.nanmax(tsd['Qhsf'])  # in W
        Qcsf_0 = np.nanmin(tsd['Qcsf'])  # in W negative

        # Cal temperatures of all systems
        tsd['Tcsf_re'], tsd['Tcsf_sup'], tsd['Thsf_re'], \
        tsd['Thsf_sup'], tsd['mcpcsf'], tsd['mcphsf'] = sensible_loads.calc_temperatures_emission_systems(tsd, bpr,
                                                                                                              Qcsf_0,
                                                                                                              Qhsf_0,
                                                                                                              gv)

        Mww, tsd['Qww'], Qww_ls_st, tsd['Qwwf'], Qwwf_0, Tww_st, Vww, Vw, tsd['mcpwwf'] = hotwater_loads.calc_Qwwf(
            bpr.rc_model['Af'],
            bpr.building_systems['Lcww_dis'],
            bpr.building_systems['Lsww_dis'],
            bpr.building_systems['Lvww_c'],
            bpr.building_systems['Lvww_dis'],
            tsd['T_ext'],
            tsd['Ta'],
            tsd['Twwf_re'],
            bpr.building_systems['Tww_sup_0'],
            bpr.building_systems['Y'],
            gv,
            bpr.internal_loads['Vww_lpd'],
            bpr.internal_loads['Vw_lpd'],
            bpr.architecture['Occ_m2p'],
            list_uses,
            schedules,
            bpr.occupancy)

        # calc auxiliary loads
        tsd['Eauxf'], tsd['Eauxf_hs'], tsd['Eauxf_cs'], \
            tsd['Eauxf_ve'], tsd['Eauxf_ww'], tsd['Eauxf_fw'] = electrical_loads.calc_Eauxf(bpr.geometry['Blength'],
                                                                                            bpr.geometry['Bwidth'],
                                                                                            Mww, tsd['Qcsf'], Qcsf_0,
                                                                                            tsd['Qhsf'], Qhsf_0,
                                                                                            tsd['Qww'],
                                                                                            tsd['Qwwf'], Qwwf_0,
                                                                                            tsd['Tcsf_re'],
                                                                                            tsd['Tcsf_sup'],
                                                                                            tsd['Thsf_re'],
                                                                                            tsd['Thsf_sup'],
                                                                                            Vw,
                                                                                            bpr.age['built'],
                                                                                            bpr.building_systems[
                                                                                                'fforma'],
                                                                                            gv,
                                                                                            bpr.geometry['floors_ag'],
                                                                                            bpr.occupancy['PFloor'],
                                                                                            tsd['m_ve_mech'],
                                                                                            bpr.hvac['type_cs'],
                                                                                            bpr.hvac['type_hs'],
                                                                                            tsd['Ehs_lat_aux'])

        # calculate other quantities
        tsd['Qcsf_lat'] = -tsd['Qcsf_lat']
        tsd['Qcsf'] = -tsd['Qcsf']
        tsd['Qcs'] = -tsd['Qcs']
        tsd['people'] = np.floor(tsd['people'])
        tsd['QHf'] = tsd['Qhsf'] + tsd['Qwwf'] + tsd['Qhprof']
        tsd['QCf'] = tsd['Qcsf'] + tsd['Qcdataf'] + tsd['Qcref']
        tsd['Ef'] = tsd['Ealf'] + tsd['Edataf'] + tsd['Eprof'] + tsd['Ecaf'] + tsd['Eauxf'] + tsd['Eref']
        tsd['QEf'] = tsd['QHf'] + tsd['QCf'] + tsd['Ef']

        # write results to csv
        gv.demand_writer.results_to_csv(tsd, bpr, locator, date, 'B01-G')
        # write report
        gv.report('calc-thermal-loads', locals(), locator.get_demand_results_folder(), 'B01-G')













def thermal_loads_all_buildings(building_properties, date, gv, locator, num_buildings, usage_schedules,
                                weather_data):
    for i, building in enumerate(building_properties.list_building_names()):
        bpr = building_properties[building]
        thermal_loads.calc_thermal_loads(
            building, bpr, weather_data, usage_schedules, date, gv, locator)
        gv.log('Building No. %(bno)i completed out of %(num_buildings)i: %(building)s', bno=i + 1,
               num_buildings=num_buildings, building=building)



"""
=========================================
test
=========================================
"""


def run_as_script(scenario_path=None, weather_path=None):
    gv = cea.globalvar.GlobalVariables()
    if scenario_path is None:
        scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)
    # for the interface, the user should pick a file out of of those in ...DB/Weather/...
    if weather_path is None:
        weather_path = locator.get_default_weather()

    gv.log('Running demand calculation for scenario %(scenario)s', scenario=scenario_path)
    gv.log('Running demand calculation with weather file %(weather)s', weather=weather_path)
    testing_gabriel(locator=locator, weather_path=weather_path, gv=gv)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    parser.add_argument('-w', '--weather', help='Path to the weather file')
    args = parser.parse_args()

    run_as_script(scenario_path=args.scenario, weather_path=args.weather)
