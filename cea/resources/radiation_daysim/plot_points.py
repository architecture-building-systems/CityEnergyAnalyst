from __future__ import division
import pandas as pd
import matplotlib.pyplot as plt
from cea import config
import numpy as np
from cea import inputlocator

configur = config.Configuration()
locator = inputlocator.InputLocator(scenario=configur.scenario)

# index = pd.date_range('1/1/2016', periods=8760, freq='H')
file = pd.read_csv(r'C:\reference-case-open\baseline\outputs\data\demand/total_demand.csv')
# file.set_index(index, inplace=True)
print file[['Qhsf_MWhyr', 'Ef_MWhyr','Qcsf_MWhyr']].sum(axis = 0 )

list_buildings = pd.read_csv(locator.get_total_demand())['Name'].values
I_sol = np.array([])
for building in list_buildings:
    data = pd.read_excel(r'C:\reference-case-open\baseline\outputs\data\demand/'+building+'.xls')
    I_sol = np.append(I_sol, [data['I_sol_gross'].sum()/1000])

I_sol2 = np.nansum(I_sol)
print I_sol2



#print file[2300:2370]
file.plot()

# plt.show()


