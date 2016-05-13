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


def full_report_to_xls(name, area_f, area_ef, sys_e_heating, sys_e_cooling, occupants, am, atot, awall_all,
                       cm, ll, lw, retrofit, sh_typ, year, footprint, nf_ag, nfp, lcww_dis, lsww_dis, lv, lvww_dis,
                       tcs_re_0, tcs_sup_0, ths_re_0, ths_sup_0, tww_re_0, tww_sup_0, y, fforma, ta_hs_set, ta_cs_set,
                       people, ve_schedule, q_int, eal_nove, eprof, edata, qcdataf, qcrefirf, vww, vw, qcdata, qcrefri,
                       qv_req, hve, htr_is, htr_ms, htr_w, htr_em, htr_1, htr_2, htr_3, i_sol, i_int_sen, w_int, i_ia,
                       i_m, i_st, uncomfort, ta, tm, qhs_sen, qcs_sen, qhs_lat, qcs_lat, qhs_em_ls, qcs_em_ls, qhc_sen,
                       ma_sup_hs, ta_sup_hs, ta_re_hs, ma_sup_cs, ta_sup_cs, ta_re_cs, w_sup, w_re, ehs_lat_aux,
                       qhs_sen_incl_em_ls, qcs_sen_incl_em_ls, t5, tww_re, top, im_tot, thset_corr, tcset_corr, tcs_re,
                       tcs_sup, ths_re, ths_sup, mcpcs, mcphs, mww, qww, qww_ls_st, qwwf, tww_st, vw_large, vww_large,
                       mcpww, eaux_cs, eaux_fw, eaux_ve, eaux_ww, eauxf, occupancy, waterconsumption, location_final):

    """ this function is to write a full report to an *.xls file containing all intermediate and final results of a
     single building thermal loads calculation"""

    # TODO: get names of used functions from glovalbars for report
    # TODO: write units to column names
    # TODO: split outputs into more work sheets, e.g. one for water, electricity, etc

    # get date and time
    now = datetime.datetime.now()
    string_now = ("%s-%s-%s-%s-%s-%s" % (now.year, now.month, now.day, now.hour, now.minute, now.second))

    # create excel work book and work sheets
    filename = location_final + '\\' + name + '-' + string_now + '.xls'
    wb = xlwt.Workbook()
    wb.add_sheet('Simulation properties')
    wb.add_sheet('Building properties')
    wb.add_sheet('Thermal loads hourly')
    wb.save(filename)

    # create data frames
    df2 = pd.DataFrame({'Name': name, 'Af_m2': area_f, 'Aef_m2': area_ef, 'Heating system': sys_e_heating,
                        'Cooling System': sys_e_cooling, 'Occupants_pax': occupants, 'Am': am, 'Atot': atot,
                        'awall_all': awall_all, 'cm': cm, 'Ll': ll, 'Lw': lw, 'retrofit': retrofit, 'Sh_typ': sh_typ,
                        'Year': year, 'Footprint': footprint, 'nf_ag': nf_ag, 'nfp': nfp, 'Lcww_dis': lcww_dis,
                        'Lsww_dis': lsww_dis, 'Lv': lv, 'Lvww_dis': lvww_dis, 'Tcs_re_0': tcs_re_0,
                        'Tcs_sup_0': tcs_sup_0, 'Ths_re_0': ths_re_0, 'Ths_sup_0': ths_sup_0, 'Tww_re_0': tww_re_0,
                        'Tww_sup_0': tww_sup_0, 'Y': y, 'fforma': fforma})

    df3 = pd.DataFrame({'Ta_hs_set': ta_hs_set, 'Ta_cs_set': ta_cs_set, 'people': people, 've_schedule': ve_schedule,
                        'q_int': q_int, 'eal_nove': eal_nove, 'eprof': eprof, 'edata': edata, 'qcdataf': qcdataf,
                        'qcrefirf': qcrefirf, 'vww': vww, 'vw': vw, 'Qcdata': qcdata, 'Qcrefri': qcrefri,
                        'qv_req': qv_req, 'Hve': hve, 'Htr_is': htr_is, 'Htr_ms': htr_ms, 'Htr_w': htr_w,
                        'Htr_em': htr_em, 'Htr_1': htr_1, 'Htr_2': htr_2, 'Htr_3': htr_3, 'I_sol': i_sol,
                        'I_int_sen': i_int_sen, 'w_int': w_int, 'I_ia': i_ia, 'I_m': i_m, 'I_st': i_st,
                        'uncomfort': uncomfort, 'Ta': ta, 'Tm': tm, 'Qhs_sen': qhs_sen, 'Qcs_sen': qcs_sen,
                        'Qhs_lat': qhs_lat, 'Qcs_lat': qcs_lat, 'Qhs_em_ls': qhs_em_ls, 'Qcs_em_ls': qcs_em_ls,
                        'QHC_sen': qhc_sen, 'ma_sup_hs': ma_sup_hs, 'Ta_sup_hs': ta_sup_hs, 'Ta_re_hs': ta_re_hs,
                        'ma_sup_cs': ma_sup_cs, 'Ta_sup_cs': ta_sup_cs, 'Ta_re_cs': ta_re_cs, 'w_sup': w_sup,
                        'w_re': w_re, 'Ehs_lat_aux': ehs_lat_aux, 'Qhs_sen_incl_em_ls': qhs_sen_incl_em_ls,
                        'Qcs_sen_incl_em_ls': qcs_sen_incl_em_ls, 't5': t5, 'Tww_re': tww_re, 'Top': top,
                        'Im_tot': im_tot, 'tHset_corr': thset_corr, 'tCset_corr': tcset_corr, 'Tcs_re': tcs_re,
                        'Tcs_sup': tcs_sup, 'Ths_re': ths_re, 'Ths_sup': ths_sup, 'mcpcs': mcpcs, 'mcphs': mcphs,
                        'Mww': mww, 'Qww': qww, 'Qww_ls_st': qww_ls_st, 'Qwwf': qwwf, 'Tww_st': tww_st, 'Vw': vw_large,
                        'Vww': vww_large, 'mcpww': mcpww, 'Eaux_cs': eaux_cs, 'Eaux_fw': eaux_fw, 'Eaux_ve': eaux_ve,
                        'Eaux_ww': eaux_ww, 'Eauxf': eauxf, 'Occupancy': occupancy,
                        'waterconsumption': waterconsumption})

    # write data frames to excel work sheet
    # Create a Pandas Excel writer using XlsxWriter as the engine.
    writer = pd.ExcelWriter(filename, engine='xlwt')
    df2.to_excel(writer, sheet_name='Building properties')
    df3.to_excel(writer, sheet_name='Thermal loads hourly')

    # Close the Pandas Excel writer and output the Excel file.
    writer.save()
