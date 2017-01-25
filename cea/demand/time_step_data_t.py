import rc_model_SIA


class TimeStepDataT(object):
    __slots__ = ['m_ve_mech', 'm_ve_window', 'm_ve_inf_simple', 'Elf', 'Eaf', 'Qcdataf', 'Qcref', 'people', 'I_sol',
                 'T_ext', 'theta_ve_mech',
                 'h_ea', 'f_sc', 'f_ic', 'h_op_m', 'h_em', 'h_mc', 'f_im', 'f_sm', 'h_ac', 'h_ec']

    def __init__(self, tsd, t, bpr):
        self.m_ve_mech = tsd['m_ve_mech'][t]
        self.m_ve_window = tsd['m_ve_window'][t]
        self.m_ve_inf_simple = tsd['m_ve_inf_simple'][t]
        self.Elf = tsd['Elf'][t]
        self.Eaf = tsd['Eaf'][t]
        self.Qcdataf = tsd['Qcdataf'][t]
        self.Qcref = tsd['Qcref'][t]
        self.people = tsd['people'][t]
        self.I_sol = tsd['I_sol'][t]
        self.T_ext = tsd['T_ext'][t]
        self.theta_ve_mech = tsd['theta_ve_mech'][t]

        # precalculate values that are constant for a single timestep
        a_t = bpr.rc_model['Atot']
        a_m = bpr.rc_model['Am']
        a_w = bpr.rc_model['Aw']

        self.h_ec = rc_model_SIA.calc_h_ec(bpr)
        self.h_ac = rc_model_SIA.calc_h_ac(a_t)
        self.h_ea = rc_model_SIA.calc_h_ea(self)

        self.f_sc = rc_model_SIA.calc_f_sc(a_t, a_m, a_w, self.h_ec)
        self.f_ic = rc_model_SIA.calc_f_ic(a_t, a_m, self.h_ec)

        self.h_op_m = rc_model_SIA.calc_h_op_m(bpr)
        self.h_mc = rc_model_SIA.calc_h_mc(a_m)
        self.h_em = rc_model_SIA.calc_h_em(self.h_op_m, self.h_mc)
        self.f_im = rc_model_SIA.calc_f_im(a_t, a_m)
        self.f_sm = rc_model_SIA.calc_f_sm(a_t, a_m, a_w)

