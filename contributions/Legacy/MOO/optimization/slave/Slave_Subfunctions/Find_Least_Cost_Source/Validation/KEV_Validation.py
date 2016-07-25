# -*- coding: utf-8 -*-
from scipy import interpolate
import numpy as np
import matplotlib.pyplot as plt

def find_KEV_remuneration(P_PV_and_PVT_installedWh):
        """
        Calculates KEV (Kostendeckende Einspeise - Vergütung) for solar PV and PVT.
        Therefore, input the nominal capacity of EACH installation and get the according KEV as return in Rp/kWh
        
        Parameters
        ----------
        P_PV_and_PVT_installed : float
            Nominal Capacity of solar panels (PV or PVT) in Wh
        
        Returns
        -------
        KEV_obtained_in_RpPerkWh : float
            KEV remuneration in Rp / kWh
                    
        """
        
        KEV_regime = [  0,
                        0,
                        20.4,
                        20.4,
                        20.4,
                        20.4,
                        20.4,
                        20.4,
                        19.7,
                        19.3,
                        19,
                        18.9,
                        18.7,
                        18.6,
                        18.5,
                        18.1,
                        17.9,
                        17.8,
                        17.8,
                        17.7,
                        17.7,
                        17.7,
                        17.6,
                        17.6]  
        P_installed_in_kW = [0,
                            9.99,
                            10,
                             12,
                             15,
                             20,
                             29,
                             30,
                             40,
                             50,
                             60,
                             70,
                             80,
                             90,
                             100,
                             200,
                             300,
                             400,
                             500,
                             750,
                             1000,
                             1500,
                             2000,
                             1000000]
        KEV_interpolated_kW = interpolate.interp1d(P_installed_in_kW, KEV_regime, kind = "linear")
        KEV_obtained_in_RpPerkWh = KEV_interpolated_kW(P_PV_and_PVT_installedWh/ 1000.0)
        return KEV_obtained_in_RpPerkWh
        
KEV = np.zeros(2000) 

for W in range(len(KEV)):
    kW = W * 1000
    KEV[W] = find_KEV_remuneration(kW)
    
plt.plot(KEV)
plt.ylabel("KEV [CHF/Rp]")
plt.xlabel("Installed capacity [kW]")
plt.title("KEV Remuneration")
plt.show()

