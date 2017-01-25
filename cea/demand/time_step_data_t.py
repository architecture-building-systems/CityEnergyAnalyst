class TimeStepDataT(object):
    __slots__ = ['m_ve_mech', 'm_ve_window', 'm_ve_inf_simple', 'Elf', 'Eaf', 'Qcdataf', 'Qcref', 'people', 'I_sol',
                 'T_ext', 'theta_ve_mech', 'h_ea']

    def __init__(self, tsd, t):
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
        self.h_ea = self.calc_h_ea()

    def calc_h_ea(self):
        cp = 1.005 / 3.6  # (Wh/kg/K)
        # TODO: check units of air flow

        # get values
        m_v_sys = self.m_ve_mech * 3600  # mass flow rate mechanical ventilation
        m_v_w = self.m_ve_window * 3600  # mass flow rate window ventilation
        m_v_inf = self.m_ve_inf_simple * 3600  # mass flow rate infiltration

        # (13) in SIA 2044 / Korrigenda C1 zum Merkblatt SIA 2044:2011 / Korrigenda C2 zum Mekblatt SIA 2044:2011
        # adapted for mass flows instead of volume flows
        h_ea = (m_v_sys + m_v_w + m_v_inf) * cp

        return h_ea

