# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# # 7. SUMMARY
# 
# In this routine, we calculate the peak demands of each cluster for heating and totals, cooling and electrical loads. The totals including processes and other services.

# <codecell>

import pandas as pd

# <codecell>

Scenario = 'StatusQuo'
CQ = 'CityQuarter_3'
locationData = r'C:\ArcGIS\EDMdata\DataFinal\EDM'+'\\'+Scenario

# <codecell>

# Names of buildings
Totals = pd.read_csv(locationData+'\\'+CQ+'\\'+'Total.csv')
Totals['Qh0'] = Totals['Qc0'] = Totals['E0'] = Totals['Qh'] = Totals['Qc'] = Totals['E'] = 0
Counter = Totals.Name.count()                     
# first files with peak demands and temperatures
for row in range(Counter):
    Name = Totals.Name[row]
    #series with loads in buildings
    Series1 = pd.read_csv(locationData+'\\'+CQ+'\\'+Name+'.csv')
    #series with loads iof processes
    Series2 = pd.read_csv(locationData+'\\'+CQ+'\\'+Name+'P.csv')
    # Create sum of heating, cooling and electrical loads
    Series1.Qh =  Series1.Qhsf + Series1.Qwwf + Series2.Qhpf  
    Series1.Qc =  Series1.Qcsf + Series2.Qcdataf + Series2.Qcicef + Series2.Qcpf
    Series1.E = Series1.Ealf + Series2.Edataf + Series2.Epf + Series2.Ecaf
    #Calculate the peaks in kWh and total yearly consumption in MWh
    Totals.Qh0[row] =  Series1.Qh.max()
    Totals.Qc0[row] = Series1.Qc.max()
    Totals.E0[row] = Series1.E.max()
    Totals.E[row] = Series1.E.sum()/1000
    Totals.Qh[row] = Series1.Qh.sum()/1000
    Totals.Qc[row] = Series1.Qc.sum()/1000

Totals.to_csv(locationData+'\\'+CQ+'\\'+'Total.csv')

# <codecell>

print Series1

# <codecell>


