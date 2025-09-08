"""
Functions for Report generation
"""



import numpy as np
import pandas as pd
import os
from plotly.offline import plot
import plotly.graph_objs as go
from cea.constants import HOURS_IN_YEAR



__author__ = "Gabriel Happle"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Gabriel Happle", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# keys for reporting
TSD_KEYS_HEATING_LOADS = ['Qhs_sen_rc', 'Qhs_sen_shu', 'Qhs_sen_ahu', 'Qhs_sen_aru', 'Qhs_sen_sys', 'Qhs_lat_ahu',
                          'Qhs_lat_aru', 'Qhs_lat_sys', 'Qhs_sys_shu', 'Qhs_sys_ahu', 'Qhs_sys_aru', 'Qhs_em_ls',
                          'Qhs_dis_ls', 'DH_hs', 'DH_ww', 'Qhs_sys', 'Qhs', 'QH_sys', 'Qww_sys', 'Qww', 'Qhpro_sys']
TSD_KEYS_COOLING_LOADS = ['Qcs_sen_rc', 'Qcs_sen_scu', 'Qcs_sen_ahu', 'Qcs_lat_ahu', 'Qcs_sen_aru', 'Qcs_lat_aru',
                          'Qcs_sen_sys', 'Qcs_lat_sys', 'Qcs_em_ls', 'Qcs_dis_ls', 'Qcs_sys_scu', 'Qcs_sys_ahu',
                          'Qcs_sys_aru', 'DC_cs', 'Qcs', 'Qcs_sys', 'QC_sys', 'DC_cre', 'Qcre_sys', 'Qcre', 'DC_cdata',
                          'Qcdata_sys', 'Qcdata', 'Qcpro_sys']
TSD_KEYS_HEATING_TEMP = ['ta_re_hs_ahu', 'ta_sup_hs_ahu', 'ta_re_hs_aru', 'ta_sup_hs_aru']
TSD_KEYS_HEATING_FLOWS = ['ma_sup_hs_ahu', 'ma_sup_hs_aru']
TSD_KEYS_COOLING_TEMP = ['ta_re_cs_ahu', 'ta_sup_cs_ahu', 'ta_re_cs_aru', 'ta_sup_cs_aru']
TSD_KEYS_COOLING_FLOWS = ['ma_sup_cs_ahu', 'ma_sup_cs_aru']
TSD_KEYS_COOLING_SUPPLY_FLOWS = ['mcpcs_sys_ahu', 'mcpcs_sys_aru', 'mcpcs_sys_scu', 'mcpcs_sys']
TSD_KEYS_COOLING_SUPPLY_TEMP = ['Tcs_sys_re_ahu', 'Tcs_sys_re_aru', 'Tcs_sys_re_scu', 'Tcs_sys_sup_ahu',
                                'Tcs_sys_sup_aru', 'Tcs_sys_sup_scu', 'Tcs_sys_sup', 'Tcs_sys_re', 'Tcdata_sys_re',
                                'Tcdata_sys_sup', 'Tcre_sys_re', 'Tcre_sys_sup']
TSD_KEYS_HEATING_SUPPLY_FLOWS = ['mcphs_sys_ahu', 'mcphs_sys_aru', 'mcphs_sys_shu', 'mcphs_sys']
TSD_KEYS_HEATING_SUPPLY_TEMP = ['Ths_sys_re_ahu', 'Ths_sys_re_aru', 'Ths_sys_re_shu', 'Ths_sys_sup_ahu',
                                'Ths_sys_sup_aru', 'Ths_sys_sup_shu', 'Ths_sys_sup', 'Ths_sys_re',
                                'Tww_sys_sup', 'Tww_sys_re']
TSD_KEYS_RC_TEMP = ['T_int', 'theta_m', 'theta_c', 'theta_o', 'theta_ve_mech']
TSD_KEYS_MOISTURE = ['x_int', 'x_ve_inf', 'x_ve_mech', 'g_hu_ld', 'g_dhu_ld']
TSD_KEYS_VENTILATION_FLOWS = ['m_ve_window', 'm_ve_mech', 'm_ve_rec', 'm_ve_inf', 'm_ve_required']
TSD_KEYS_ENERGY_BALANCE_DASHBOARD = ['Q_gain_sen_light', 'Q_gain_sen_app', 'Q_gain_sen_peop', 'Q_gain_sen_data',
                                     'Q_loss_sen_ref', 'Q_gain_sen_wall', 'Q_gain_sen_base', 'Q_gain_sen_roof',
                                     'Q_gain_sen_wind', 'Q_gain_sen_vent', 'Q_gain_lat_peop', 'Q_gain_sen_pro']
TSD_KEYS_SOLAR = ['I_sol', 'I_rad', 'I_sol_and_I_rad']
TSD_KEYS_PEOPLE = ['people', 've_lps', 'Qs', 'w_int']

ALL_KEYS = TSD_KEYS_PEOPLE + TSD_KEYS_SOLAR + TSD_KEYS_HEATING_LOADS + TSD_KEYS_COOLING_LOADS + \
           TSD_KEYS_HEATING_FLOWS + TSD_KEYS_HEATING_SUPPLY_FLOWS + TSD_KEYS_COOLING_FLOWS + \
           TSD_KEYS_COOLING_SUPPLY_FLOWS + TSD_KEYS_HEATING_TEMP + TSD_KEYS_HEATING_SUPPLY_TEMP + \
           TSD_KEYS_COOLING_TEMP + TSD_KEYS_COOLING_SUPPLY_TEMP + TSD_KEYS_RC_TEMP + TSD_KEYS_MOISTURE + \
           TSD_KEYS_VENTILATION_FLOWS

def calc_full_hourly_dataframe(tsd, date):
    """
    This function creates a dataframe with all tsd_df values for full reporting
    """

    tsd_df = pd.DataFrame(index=date, columns=ALL_KEYS)
    for key in TSD_KEYS_PEOPLE:
        tsd_df[key] = tsd.get_occupancy_value(key)
    for key in TSD_KEYS_SOLAR:
        tsd_df[key] = tsd.get_solar_value(key)
    for key in TSD_KEYS_HEATING_LOADS + TSD_KEYS_COOLING_LOADS:
        tsd_df[key] = tsd.get_load_value(key)
    for key in TSD_KEYS_HEATING_FLOWS + TSD_KEYS_HEATING_SUPPLY_FLOWS + TSD_KEYS_COOLING_FLOWS + \
               TSD_KEYS_COOLING_SUPPLY_FLOWS:
        tsd_df[key] = tsd.get_mass_flow_value(key)
    for key in TSD_KEYS_HEATING_TEMP + TSD_KEYS_HEATING_SUPPLY_TEMP + \
               TSD_KEYS_COOLING_TEMP + TSD_KEYS_COOLING_SUPPLY_TEMP + TSD_KEYS_RC_TEMP:
        tsd_df[key] = tsd.get_temperature_value(key)
    for key in TSD_KEYS_MOISTURE:
        tsd_df[key] = tsd.get_moisture_value(key)
    for key in TSD_KEYS_VENTILATION_FLOWS:
        tsd_df[key] = tsd.get_ventilation_mass_flow_value(key)

    return tsd_df

def full_report_to_xls(tsd_df, output_folder, basename):
    """ this function is to write a full report to an ``*.xls`` file containing all intermediate and final results of a
    single building thermal loads calculation"""

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    #timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    #output_path = os.path.join(output_folder,"%(basename)s-%(timestamp)s.xls" % locals())
    output_path = os.path.join(output_folder, "%(basename)s.xlsx" % locals())
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        tsd_df.to_excel(writer, na_rep="NaN")


def quick_visualization_tsd(tsd_df, output_folder, basename):

    # set to True to produce plotly graphs of selected variables
    plot_heat_load = True
    plot_heat_temp = True
    plot_cool_load = True
    plot_cool_moisture = True
    plot_cool_air = True
    plot_cool_sup = True
    auto_open = False

    if plot_heat_load:
        filename = os.path.join(output_folder, "heat-load-{}.html").format(basename)
        traces = []
        for key in TSD_KEYS_HEATING_LOADS:
            y = tsd_df[key][50:150]
            trace = go.Scattergl(x=np.linspace(1, 100, 100), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)

    if plot_heat_temp:
        filename = os.path.join(output_folder, "heat-temp-{}.html").format(basename)
        traces = []
        keys = []
        keys.extend(TSD_KEYS_HEATING_TEMP)
        keys.extend(TSD_KEYS_RC_TEMP)
        for key in keys:
            y = tsd_df[key][50:150]
            trace = go.Scattergl(x=np.linspace(1, 100, 100), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)

    if plot_cool_load:
        filename = os.path.join(output_folder, "cool-load-{}.html").format(basename)
        traces = []
        for key in TSD_KEYS_COOLING_LOADS:
            y = tsd_df[key]
            trace = go.Scattergl(x=np.linspace(1, HOURS_IN_YEAR, HOURS_IN_YEAR), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)

    if plot_cool_moisture:
        filename = os.path.join(output_folder, "cool-moisture-{}.html").format(basename)
        traces = []
        for key in TSD_KEYS_MOISTURE:
            y = tsd_df[key]
            trace = go.Scattergl(x=np.linspace(1, HOURS_IN_YEAR, HOURS_IN_YEAR), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)

    if plot_cool_air:
        filename = os.path.join(output_folder, "cool-air-{}.html").format(basename)
        traces = []
        for key in TSD_KEYS_VENTILATION_FLOWS:
            y = tsd_df[key]
            trace = go.Scattergl(x=np.linspace(1, HOURS_IN_YEAR, HOURS_IN_YEAR), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)

    if plot_cool_sup:
        filename = os.path.join(output_folder, "cool-sup-{}.html").format(basename)
        traces = []
        keys = []
        keys.extend(TSD_KEYS_COOLING_SUPPLY_TEMP)
        keys.extend(TSD_KEYS_COOLING_SUPPLY_FLOWS)
        for key in keys:
            y = tsd_df[key]
            trace = go.Scattergl(x=np.linspace(1, HOURS_IN_YEAR, HOURS_IN_YEAR), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)
