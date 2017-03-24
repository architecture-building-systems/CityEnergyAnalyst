# -*- coding: utf-8 -*-
"""
Global variables - this object contains context information and is expected to be refactored away in future.
"""
import cea.demand.demand_writers
import numpy as np

# from cea.demand import thermal_loads

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class GlobalVariables(object):
    def __init__(self):

        # Parameters of the cost equations can vary within a range such as [a,b]. This file enlists
        # the range and the type of distribution the parameter will vary in

        # Water Source Heat Pump
        # The equation in consideration is Investment Cost = (a*ln(x) + b)*x
        # x being the thermal load of Water Source Heat Pump
        self.WHP_a = -493.53
        self.WHP_b = 5484
        self.WHP_c = 20.0  # lifetime [years]

        # Ground Source Heat Pump
        # The equation in consideration is Investment Cost = (a*(x)^b + c*(x)^d)
        # x being the thermal load of Ground Source Heat Pump
        self.GHP_a = 5247.5
        self.GHP_b = 0.49
        self.GHP_c = 7100
        self.GHP_d = 0.74
        self.GHP_e = 50  # Borehole lifetime [years]
        self.GHP_f = 20  # GHP lifetime [years]

        # Condensing Boilers
        # The equation in consideration is Investment Cost = a + b*x for x > 320,000 W
        #                                                  = c*x     for x <= 320,000 W
        # x being the boiler load
        self.Boiler_a = 8400
        self.Boiler_b = 0.014
        self.Boiler_c = 0.8
        self.Boiler_d = 20  # Boiler Lifetime [years]

        # Combined gas cycle turbine
        # The equation in consideration is Investment Cost = a*(x)^b
        # x is the load
        self.CC_a = 32978
        self.CC_b = 0.5946
        self.CC_c = 25  # Gas Cycle turbine Lifetime [years]

        # Fuel Cell
        # The equation in consideration is Investment Cost = a*x
        # x is the load
        self.FC_a = 55000
        self.FC_b = 40000  # Fuel Cell Lifetime [hours]

        # Photovoltaic panel
        # The equation in consideration is Investment Cost = a*x if x < 10 kW
        #                                                  = b*x if 10 kW < x < 200 kW
        # x is the load
        self.PV_a = 3500
        self.PV_b = 2500
        self.PV_c = 20  # Photovoltaic panel Lifetime [years]

        # Solar Collector
        # The equation in consideration is Investment Cost = a*x
        # x is the load
        self.SC_a = 2050
        self.SC_b = 20  # Solar Collector Lifetime [years]

        # Photovoltaic Thermal
        # The equation in consideration is Investment Cost = sum of (a*x)
        # x is the load of a individual cell
        self.PVT_a = 5000
        self.PVT_b = 20  # Photovoltaic Thermal cell Lifetime [years]

        # Chillers and Cooling Towers
        # The equation in consideration is Investment Cost = (a*x + b*x + c)
        # x is the load of cooling tower
        self.CT_a = 386
        self.CT_b = 15.4
        self.CT_c = 1400
        self.CT_d = 20  # Cooling Tower Lifetime [years]

        # Thermal Storage
        # The equation in consideration is Investment Cost = [(a*ln(x) + b)*x + c*(y)^d]
        # x, y are calculated using load
        self.TS_a = -493.53
        self.TS_b = 5484
        self.TS_c = 7229
        self.TS_d = -0.522
        self.TS_e = 60  # Thermal Storage Lifetime [years]

        # Substation and HEX
        # The equation in consideration is Investment Cost = a*(x/b)^c
        # x is the load of HEX
        self.HEX_a = 3364
        self.HEX_b = 5.5
        self.HEX_c = 0.6
        self.HEX_d = 20  # HEX Lifetime [years]

        # Circulation Pump
        # The equation in consideration is Investment Cost = [a*(x)^b + c*(x)^d]
        # x is the load of Circulation Pump
        self.CP_a = 414.8
        self.CP_b = -0.187
        self.CP_c = 440.11
        self.CP_d = -0.9
        self.CP_e = 10  # Circulation Pump Lifetime [years]

        # Furnace
        # The equation in consideration is Investment Cost = a*x
        # x is the Q_Design
        self.Furn_a = 0.67

        # Cost of Utilities
        self.EP = 0.104
        self.NG = 0.057
        self.BG = 0.078



def run_as_script(scenario_path=None):
    import pandas as pd
    WHP_LT = []
    GHP_LT = []
    CB_LT = []
    CC_LT = []
    FC_LT = []
    PV_LT = []
    SC_LT = []
    PVT_LT = []
    CCT_LT = []
    TS_LT = []
    HEX_LT = []
    CP_LT = []
    EP = []
    NG = []
    BG = []
    IR = []

    for i in xrange(1000):
        # print (i)
        WHP_LT.append(34 * np.random.beta(5.8, 4, size=None))
        GHP_LT.append(34 * np.random.beta(5.8, 4, size=None))
        CB_LT.append(34 * np.random.beta(5.8, 4, size=None))
        CC_LT.append(43 * np.random.beta(5.8, 4, size=None))
        FC_LT.append(17 * np.random.beta(5.8, 4, size=None))
        PV_LT.append(34 * np.random.beta(5.8, 4, size=None))
        SC_LT.append(34 * np.random.beta(5.8, 4, size=None))
        PVT_LT.append(34 * np.random.beta(5.8, 4, size=None))
        CCT_LT.append(11.27 * np.random.beta(5.8, 4, size=None))
        TS_LT.append(102 * np.random.beta(5.8, 4, size=None))
        HEX_LT.append(34 * np.random.beta(5.8, 4, size=None))
        CP_LT.append(17 * np.random.beta(5.8, 4, size=None))
        EP.append(np.random.normal(loc=0.2, scale=0.02))
        NG.append(np.random.normal(loc=0.068, scale=0.0068))
        BG.append(np.random.normal(loc=0.076, scale=0.0076))
        IR.append(np.random.normal(loc=5, scale=1))

    table = [WHP_LT, GHP_LT, CB_LT, CC_LT, FC_LT, PV_LT, SC_LT, PVT_LT, CCT_LT, TS_LT, HEX_LT, CP_LT, EP, NG, BG, IR]
    df = pd.DataFrame(table)
    df = df.transpose()
    cols = ['WHP', 'GHP', 'CB', 'CC', 'FC', 'PV', 'SC', 'PVT', 'CCT', 'TS', 'HEX', 'CP', 'EP', 'NG', 'BG', 'IR']
    df.columns = cols
    print (df)
    df.to_csv("C:\Users\Bhargava\Documents\uncertainty.csv")

    # print (np.mean(WHP_LT))
    # print (np.mean(GHP_LT))
    # print (np.mean(CB_LT))
    # print (np.mean(CC_LT))
    # print (np.mean(FC_LT))
    # print (np.mean(PV_LT))
    # print (np.mean(SC_LT))
    # print (np.mean(PVT_LT))
    # print (np.mean(CCT_LT))
    # print (np.mean(TS_LT))
    # print (np.mean(HEX_LT))
    # print (np.mean(CP_LT))
    # print (np.mean(EP))
    # print (np.mean(NG))
    # print (np.mean(BG))
    # print (np.mean(IR))

    print 'test_optimization_main() succeeded'

if __name__ == '__main__':
    run_as_script(r'C:\reference-case-zug\baseline')