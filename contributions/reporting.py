"""
===============================
Functions for Report generation
===============================
File history and credits:
G. Happle   ... 13.05.2016

"""

import pandas as pd
import datetime
import xlwt
import os


def full_report_to_xls(dict_functions_report, dict_local, location_final):

    """ this function is to write a full report to an *.xls file containing all intermediate and final results of a
    single building thermal loads calculation"""

    # TODO: get names of used functions from glovalbars for report
    # TODO: write units to column names
    # TODO: split outputs into more work sheets, e.g. one for water, electricity, etc

    # get date and time
    now = datetime.datetime.now()
    string_now = ("%s-%s-%s-%s-%s-%s" % (now.year, now.month, now.day, now.hour, now.minute, now.second))

    # get variables from local
    gv = dict_local['gv']
    list_variable = gv.report_variables[dict_functions_report]
    name = dict_local[list_variable[0]]

    # create excel work book and work sheets
    name_file = name + '-' + string_now + '.xls'
    path_file = os.path.join(location_final, name_file)
    # filename = location_final + '\\' + name + '-' + string_now + '.xls'
    wb = xlwt.Workbook()
    wb.add_sheet('Simulation properties')
    wb.add_sheet('Building properties')
    wb.add_sheet('Thermal loads hourly')
    wb.save(path_file)

    # create data frames
    # TODO: this could be dynamic (for loop), see first 3 lines of data frame, but how to decide which variables go to which sheet?
    # TODO: maybe hard coded is better to add additional info to the column names, e.g. units
    df_building_props = pd.DataFrame({list_variable[0]: name,
                                      list_variable[1]: dict_local[list_variable[1]],
                                      list_variable[2]: dict_local[list_variable[2]],
                                      'Heating system': dict_local[list_variable[3]],
                                      'Cooling System': dict_local[list_variable[4]],
                                      'Occupants_pax': dict_local[list_variable[5]],
                                      'Am': dict_local[list_variable[6]],
                                      'Atot': dict_local[list_variable[7]],
                                      'awall_all': dict_local[list_variable[8]],
                                      'cm': dict_local[list_variable[9]],
                                      'Ll': dict_local[list_variable[10]],
                                      'Lw': dict_local[list_variable[11]],
                                      'retrofit': dict_local[list_variable[12]],
                                      'Sh_typ': dict_local[list_variable[13]],
                                      'Year': dict_local[list_variable[14]],
                                      'Footprint': dict_local[list_variable[15]],
                                      'nf_ag': dict_local[list_variable[16]],
                                      'nfp': dict_local[list_variable[17]],
                                      'Lcww_dis': dict_local[list_variable[18]],
                                      'Lsww_dis': dict_local[list_variable[19]],
                                      'Lv': dict_local[list_variable[20]],
                                      'Lvww_dis': dict_local[list_variable[21]],
                                      'Tcs_re_0': dict_local[list_variable[22]],
                                      'Tcs_sup_0': dict_local[list_variable[23]],
                                      'Ths_re_0': dict_local[list_variable[24]],
                                      'Ths_sup_0': dict_local[list_variable[25]],
                                      'Tww_re_0': dict_local[list_variable[26]],
                                      'Tww_sup_0': dict_local[list_variable[27]],
                                      'Y': dict_local[list_variable[28]],
                                      'fforma': dict_local[list_variable[29]]})

    df_thermal_loads = pd.DataFrame({'Ta_hs_set': dict_local[list_variable[30]],
                                     'Ta_cs_set': dict_local[list_variable[31]],
                                     'people': dict_local[list_variable[32]],
                                     've_schedule': dict_local[list_variable[33]],
                                     'q_int': dict_local[list_variable[34]],
                                     'eal_nove': dict_local[list_variable[35]],
                                     'eprof': dict_local[list_variable[36]],
                                     'edata': dict_local[list_variable[37]],
                                     'qcdataf': dict_local[list_variable[38]],
                                     'qcrefirf': dict_local[list_variable[39]],
                                     'vww': dict_local[list_variable[40]],
                                     'vw': dict_local[list_variable[41]],
                                     'Qcdata': dict_local[list_variable[42]],
                                     'Qcrefri': dict_local[list_variable[43]],
                                     'qv_req': dict_local[list_variable[44]],
                                     'Hve': dict_local[list_variable[45]],
                                     'Htr_is': dict_local[list_variable[46]],
                                     'Htr_ms': dict_local[list_variable[47]],
                                     'Htr_w': dict_local[list_variable[48]],
                                     'Htr_em': dict_local[list_variable[49]],
                                     'Htr_1': dict_local[list_variable[50]],
                                     'Htr_2': dict_local[list_variable[51]],
                                     'Htr_3': dict_local[list_variable[52]],
                                     'I_sol': dict_local[list_variable[53]],
                                     'I_int_sen': dict_local[list_variable[54]],
                                     'w_int': dict_local[list_variable[55]],
                                     'I_ia': dict_local[list_variable[56]],
                                     'I_m': dict_local[list_variable[57]],
                                     'I_st': dict_local[list_variable[58]],
                                     'uncomfort': dict_local[list_variable[59]],
                                     'Ta': dict_local[list_variable[60]],
                                     'Tm': dict_local[list_variable[61]],
                                     'Qhs_sen': dict_local[list_variable[62]],
                                     'Qcs_sen': dict_local[list_variable[63]],
                                     'Qhs_lat': dict_local[list_variable[64]],
                                     'Qcs_lat': dict_local[list_variable[65]],
                                     'Qhs_em_ls': dict_local[list_variable[66]],
                                     'Qcs_em_ls': dict_local[list_variable[67]],
                                     'QHC_sen': dict_local[list_variable[68]],
                                     'ma_sup_hs': dict_local[list_variable[69]],
                                     'Ta_sup_hs': dict_local[list_variable[70]],
                                     'Ta_re_hs': dict_local[list_variable[71]],
                                     'ma_sup_cs': dict_local[list_variable[72]],
                                     'Ta_sup_cs': dict_local[list_variable[73]],
                                     'Ta_re_cs': dict_local[list_variable[74]],
                                     'w_sup': dict_local[list_variable[75]],
                                     'w_re': dict_local[list_variable[76]],
                                     'Ehs_lat_aux': dict_local[list_variable[77]],
                                     'Qhs_sen_incl_em_ls': dict_local[list_variable[78]],
                                     'Qcs_sen_incl_em_ls': dict_local[list_variable[79]],
                                     't5': dict_local[list_variable[80]],
                                     'Tww_re': dict_local[list_variable[81]],
                                     'Top': dict_local[list_variable[82]],
                                     'Im_tot': dict_local[list_variable[83]],
                                     'tHset_corr': dict_local[list_variable[84]],
                                     'tCset_corr': dict_local[list_variable[85]],
                                     'Tcs_re': dict_local[list_variable[86]],
                                     'Tcs_sup': dict_local[list_variable[87]],
                                     'Ths_re': dict_local[list_variable[88]],
                                     'Ths_sup': dict_local[list_variable[89]],
                                     'mcpcs': dict_local[list_variable[90]],
                                     'mcphs': dict_local[list_variable[91]],
                                     'Mww': dict_local[list_variable[92]],
                                     'Qww': dict_local[list_variable[93]],
                                     'Qww_ls_st': dict_local[list_variable[94]],
                                     'Qwwf': dict_local[list_variable[95]],
                                     'Tww_st': dict_local[list_variable[96]],
                                     'Vw': dict_local[list_variable[97]],
                                     'Vww': dict_local[list_variable[98]],
                                     'mcpww': dict_local[list_variable[99]],
                                     'Eaux_cs': dict_local[list_variable[100]],
                                     'Eaux_fw': dict_local[list_variable[101]],
                                     'Eaux_ve': dict_local[list_variable[102]],
                                     'Eaux_ww': dict_local[list_variable[103]],
                                     'Eauxf': dict_local[list_variable[104]],
                                     'Occupancy': dict_local[list_variable[105]],
                                     'waterconsumption': dict_local[list_variable[106]]})

    # write data frames to excel work sheet
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(path_file, engine='xlwt')
    df_building_props.to_excel(writer, sheet_name='Building properties')
    df_thermal_loads.to_excel(writer, sheet_name='Thermal loads hourly')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
