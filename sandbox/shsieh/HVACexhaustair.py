import math
import CoolProp.CoolProp as CP
fluid = 'Water'
pressure_at_critical_point = CP.PropsSI(fluid,'pcrit')
# Massic volume (in m^3/kg) is the inverse of density
# (or volumic mass in kg/m^3). Let's compute the massic volume of liquid
# at 1bar (1e5 Pa) of pressure
vL = 1/CP.PropsSI('D','P',1e5,'Q',0,fluid)
# Same for saturated vapor
vG = 1/CP.PropsSI('D','P',1e5,'Q',1,fluid)



def cal_Cpm(w):
    """

    Parameters
    ----------
    Cp: specific heat of dry air
    w: humidity ratio
    Cv: specific heat of water vapor

    Returns
    -------

    """
    Cp = PropsSI(("C", "P", 101325, "T", 300, "Air"), "J/kg/K")
    Cv = PropsSI(("C", "P", 101325, "T", 300, "Water"), "J/kg/K")

    Cpm = Cp + w*Cv
    return Cpm

v_out = 129 # L/s
v_in = 147
w_out = 14.8 #g/kg
w_in1 = 14.8
w_in2 = 13

m_out = v_out * cal_Cpm(w_out) / 1000  # kg/s
m_in = v_in * cal_Cpm(w_in1) / 1000

t_out = 19.2
t_in1 = 30
t_in2 = 23.3

w_exhaust2 = (m_out * w_out + (w_in1 - w_in2) * m_in) / m_out
t_exhaust2 = m_in * (t_in1 - t_in2) / (m_out) + t_out

q_evaporation = (18-w_exhaust2) * m_out * 2257   # J/s

print q_evaporation