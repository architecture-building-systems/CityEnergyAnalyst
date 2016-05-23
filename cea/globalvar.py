"""
================
Global variables
================

"""
import functions


class GlobalVariables(object):
    def __init__(self):
        self.list_uses = ['ADMIN', 'SR', 'INDUS', 'REST', 'RESTS', 'DEPO', 'COM', 'MDU', 'SDU',
                          'EDU', 'CR', 'HEALTH', 'SPORT', 'SWIM', 'PUBLIC', 'SUPER', 'ICE', 'HOT']
        self.seasonhours = [3216, 6192]
        self.main_use = 'ADMIN'
        self.Z = 3  # height of basement for every building in m
        self.Bf = 0.7  # it calculates the coefficient of reduction in transmittance for surfaces in contact with the ground according to values of SIA 380/1
        self.his = 3.45  # heat transfer coefficient between air and the surfacein W/(m2K)
        self.hms = 9.1  # heat transfer coefficient between nodes m and s in W/m2K
        self.g_gl = 0.9 * 0.75  # solar energy transmittance assuming a reduction factor of 0.9 and most of the windows due to double glazing (0.75)
        self.F_f = 0.3  # Frame area faction coefficient
        self.D = 20  # in mm the diameter of the pipe to calculate losses
        self.hf = 3  # average height per floor in m
        self.Pwater = 998  # water density kg/m3
        self.PaCa = 1200  # Air constant J/m3K 
        self.Cpw = 4.184  # heat capacity of water in kJ/kgK
        self.Flowtap = 0.036  # in m3/min == 12 l/min during 3 min every tap opening
        # constant values for HVAC
        self.nrec_N = 0.75  # possilbe recovery
        self.NACH_inf_non_occ = 0.2  # num air exchanges due to infiltration when no occupied
        self.NACH_inf_occ = 0.5  # num air exchanges due to infiltration when occupied
        self.C1 = 0.054  # assumed a flat plate heat exchanger (-)
        self.Vmax = 3  # maximum estimated flow in m3/s
        self.Pair = 1.2  # air density in kg/m3
        self.Cpv = 1.859  # specific heat capacity of water vapor in KJ/kgK
        self.Cpa = 1.008  # specific heat capacity of air in KJ/kgK
        self.U_dhwtank = 0.225  # tank insulation heat transfer coefficient in W/m2-K, value taken from SIA 385
        self.AR = 3.3  # tank height aspect ratio, H=(4*V*AR^2/pi)^(1/3), taken from commercial tank geometry (jenni.ch)
        self.lvapor = 2257  # latent heat of air kJ/kg
        self.Tww_setpoint = 60  # dhw tank set point temperature in C
        # constant variables for pumping operation
        self.hoursop = 5  # assuming around 2000 hours of operation per year. It is charged to the electrical system from 11 am to 4 pm
        self.gr = 9.81  # m/s2 gravity
        self.effi = 0.6  # efficiency of pumps
        self.deltaP_l = 0.1  # delta of pressure
        self.fsr = 0.3  # factor for pressure calculation
        # grey emssions
        self.fwratio = 1.5  # conversion component's area to floor area
        self.sl_materials = 60  # service life of standard building components and materials
        self.sl_services = 40  # service life of technical instalations
        # constant variables for air conditioning fan
        self.Pfan = 0.55 # specific fan consumption in W/m3/h

        # here is where we plug in the models to use for calculations
        self.models = {'calc-thermal-loads': functions.CalcThermalLoads}

        # here is where we decide whether full excel reports of the calculations are generated
        self.testing = True  # if true: reports are generated, if false: not

        self.report_variables = {
            'calc-thermal-loads': {
                'Building properties':
                    ['Name',                'Af',                   'Aef',          'sys_e_heating',
                     'sys_e_cooling',       'Occupants',            'Am',           'Atot',
                     'Awall_all',           'Cm',                   'Ll',           'Lw',
                     'Retrofit',            'Sh_typ',               'Year',         'footprint',
                     'nf_ag',               'nfp',                  'Lcww_dis',     'Lsww_dis',
                     'Lv',                  'Lvww_dis',             'Tcs_re_0',     'Tcs_sup_0',
                     'Ths_re_0',            'Ths_sup_0',            'Tww_re_0',     'Tww_sup_0',
                     'Y',                   'fforma'],
                'Thermal loads hourly':
                    ['ta_hs_set',           'ta_cs_set',            'people',       've',
                     'q_int',               'Eal_nove',             'Eprof',        'Edata',
                     'Qcdataf',             'Qcrefrif',             'vww',          'vw',
                     'Qcdata',              'Qcrefri',              'qv_req',       'Hve',
                     'Htr_is',              'Htr_ms',               'Htr_w',        'Htr_em',
                     'Htr_1',               'Htr_2',                'Htr_3',        'I_sol',
                     'I_int_sen',           'w_int',                'I_ia',         'I_m',
                     'I_st',                'uncomfort',            'Ta',           'Tm',
                     'Qhs_sen',             'Qcs_sen',              'Qhs_lat',      'Qcs_lat',
                     'Qhs_em_ls',           'Qcs_em_ls',            'QHC_sen',      'ma_sup_hs',
                     'Ta_sup_hs',           'Ta_re_hs',             'ma_sup_cs',    'Ta_sup_cs',
                     'Ta_re_cs',            'w_sup',                'w_re',         'Ehs_lat_aux',
                     'Qhs_sen_incl_em_ls',  'Qcs_sen_incl_em_ls',   't5',           'Tww_re',
                     'Top',                 'Im_tot',               'tHset_corr',   'tCset_corr',
                     'Tcs_re',              'Tcs_sup','Ths_re',     'Ths_sup',      'mcpcs',
                     'mcphs',               'Mww',                  'Qww',          'Qww_ls_st',
                     'Qwwf',                'Tww_st',               'Vw',           'Vww',
                     'mcpww',               'Eaux_cs',              'Eaux_fw',      'Eaux_ve',
                     'Eaux_ww',             'Eauxf',                'Occupancy',    'Waterconsumption']},
            'other-module-that-needs-logging': {'worksheet1': ['v1', 'v2', 'v3'],
                                                #'worksheet2': [('v4', 'm'), ('v5', 'Mwh'), ('v6', 'MJ')]}}
                                                'worksheet2': ['v4', 'v5', 'v6']}}

    def report(self, template, variables, output_folder, basename):
        """Use vars to fill worksheets in an excel file $destination_template based on the template.
        The template references self.report_variables. The destination_template may contain date format codes that
        will be updated with the current datetime."""
        if self.testing:
            import reporting
            reporting.full_report_to_xls(template, variables, output_folder, basename, self)



    def log(self, msg, **kwargs):
        print msg % kwargs
