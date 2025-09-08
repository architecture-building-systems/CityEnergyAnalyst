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


def full_report_to_xls(tsd, output_folder, basename):
    """ this function is to write a full report to an ``*.xls`` file containing all intermediate and final results of a
    single building thermal loads calculation"""

    df = pd.DataFrame(tsd)

    # Create a Pandas Excel writer using XlsxWriter as the engine.
    #timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    #output_path = os.path.join(output_folder,"%(basename)s-%(timestamp)s.xls" % locals())
    output_path = os.path.join(output_folder, "%(basename)s.xls" % locals())
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, na_rep="NaN")


def quick_visualization_tsd(tsd, output_folder, basename):

    # import keys
    TSD_KEYS_HEATING_LOADS = ['Qhs_sen_rc', 'Qhs_sen_shu', 'Qhs_sen_ahu', 'Qhs_lat_ahu', 'Qhs_sen_aru', 'Qhs_lat_aru',
                              'Qhs_sen_sys', 'Qhs_lat_sys', 'Qhs_em_ls', 'Qhs_dis_ls', 'Qhs_sys_shu', 'Qhs_sys_ahu',
                              'Qhs_sys_aru', 'DH_hs', 'Qhs', 'Qhs_sys', 'QH_sys', 'DH_ww', 'Qww_sys', 'Qww',
                              'Qhs', 'Qhpro_sys']
    TSD_KEYS_COOLING_LOADS = ['Qcs_sen_rc', 'Qcs_sen_scu', 'Qcs_sen_ahu', 'Qcs_lat_ahu', 'Qcs_sen_aru', 'Qcs_lat_aru',
                              'Qcs_sen_sys', 'Qcs_lat_sys', 'Qcs_em_ls', 'Qcs_dis_ls', 'Qcs_sys_scu', 'Qcs_sys_ahu',
                              'Qcs_sys_aru', 'DC_cs', 'Qcs', 'Qcs_sys', 'QC_sys', 'DC_cre', 'Qcre_sys', 'Qcre',
                              'DC_cdata', 'Qcdata_sys', 'Qcdata', 'Qcpro_sys']
    TSD_KEYS_HEATING_TEMP = ['ta_re_hs_ahu', 'ta_sup_hs_ahu', 'ta_re_hs_aru', 'ta_sup_hs_aru']
    TSD_KEYS_COOLING_SUPPLY_FLOWS = ['mcpcs_sys_ahu', 'mcpcs_sys_aru', 'mcpcs_sys_scu', 'mcpcs_sys']
    TSD_KEYS_COOLING_SUPPLY_TEMP = ['Tcs_sys_re_ahu', 'Tcs_sys_re_aru', 'Tcs_sys_re_scu', 'Tcs_sys_sup_ahu',
                                    'Tcs_sys_sup_aru', 'Tcs_sys_sup_scu', 'Tcs_sys_sup', 'Tcs_sys_re',
                                    'Tcdata_sys_re', 'Tcdata_sys_sup', 'Tcre_sys_re', 'Tcre_sys_sup']
    TSD_KEYS_RC_TEMP = ['T_int', 'theta_m', 'theta_c', 'theta_o', 'theta_ve_mech']
    TSD_KEYS_MOISTURE = ['x_int', 'x_ve_inf', 'x_ve_mech', 'g_hu_ld', 'g_dhu_ld']
    TSD_KEYS_VENTILATION_FLOWS = ['m_ve_window', 'm_ve_mech', 'm_ve_rec', 'm_ve_inf', 'm_ve_required']

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
            y = tsd[key][50:150]
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
            y = tsd[key][50:150]
            trace = go.Scattergl(x=np.linspace(1, 100, 100), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)

    if plot_cool_load:
        filename = os.path.join(output_folder, "cool-load-{}.html").format(basename)
        traces = []
        for key in TSD_KEYS_COOLING_LOADS:
            y = tsd[key]
            trace = go.Scattergl(x=np.linspace(1, HOURS_IN_YEAR, HOURS_IN_YEAR), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)

    if plot_cool_moisture:
        filename = os.path.join(output_folder, "cool-moisture-{}.html").format(basename)
        traces = []
        for key in TSD_KEYS_MOISTURE:
            y = tsd[key]
            trace = go.Scattergl(x=np.linspace(1, HOURS_IN_YEAR, HOURS_IN_YEAR), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)

    if plot_cool_air:
        filename = os.path.join(output_folder, "cool-air-{}.html").format(basename)
        traces = []
        for key in TSD_KEYS_VENTILATION_FLOWS:
            y = tsd[key]
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
            y = tsd[key]
            trace = go.Scattergl(x=np.linspace(1, HOURS_IN_YEAR, HOURS_IN_YEAR), y=y, name=key, mode='lines+markers')
            traces.append(trace)
        fig = go.Figure(data=traces)
        plot(fig, filename=filename, auto_open=auto_open)
