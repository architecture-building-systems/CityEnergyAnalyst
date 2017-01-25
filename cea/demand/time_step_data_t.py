class TimeStepDataT(object):
    __slots__ = ['m_ve_mech', 'm_ve_window', 'm_ve_inf_simple', 'Elf', 'Eaf', 'Qcdataf', 'Qcref', 'people', 'I_sol',
                 'T_ext', 'theta_ve_mech']
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

