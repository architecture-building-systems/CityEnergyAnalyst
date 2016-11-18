# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ##MODULES

# <codecell>

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

# <markdowncell>

# ##VARIABLES

# <codecell>

CQ_name = 'CityQuarter_3'
Scenario = 'StatusQuo'
locationFinal = r'c:\ArcGIS\EDMdata\DataFinal'+'\\'+'EDM'+'\\'+Scenario+'\\'+CQ_name

# <markdowncell>

# ##PROCESS

# <markdowncell>

# ###1. Representation Hourly Heating Demand

# <codecell>

totals = pd.read_csv(locationFinal+'\\'+'Total.csv')
counter = totals.Name.count()

# <codecell>

name = 'Bau 17P'
dataframe = pd.read_csv(locationFinal+'\\'+name+'.csv')
total = dataframe.Ecaf.sum()
DataToPlot = dataframe[['Ecaf']]

# <codecell>

total

# <codecell>

DataToPlot.plot(figsize = (8,4))

# <codecell>

DataToPlot.sum()

# <codecell>

total = pd.read_csv(locationFinal+'\\'+name+'T.csv')
print total

# <codecell>

DataToPlot_MWh.plot(figsize = (20,9))

# <codecell>

fig, ax = plt.subplots(figsize = (15,9)); DataToPlot_MWh.plot(ax=ax); plt.legend(loc='best'); plt.axis([8736,8760,0,8])

# <codecell>

DataToPlot_MWh.plot(subplots=True,figsize = (10,50)); plt.legend(loc='best'); plt.axis([8736,8760,0,8])

# <markdowncell>

# ### 2. Comparison cooling and heating demands Between models

# <markdowncell>

# Import files with the results of the model to compare

# <codecell>

Data_modeled = pd.read_csv(locationFinal+'\\'+'total.csv')
Demand_modeled0 = Data_modeled[['Name','Qh','Qc']]
Demand_modeled0.rename(columns={'Qh':'Qhn_Simulated','Qc':'Qcn_Simulated'}, inplace=True)

# <codecell>

Data_statistic = pd.read_csv(r'C:\ArcGIS\EDMdata\DataFinal\SEDM\StatusQuo\CityQuarter_6\Total.csv')
Data_statistic0 = Data_statistic[['Name','Qh_MWh','Qc_MWh']]
Demand_join = Demand_modeled0.merge(Data_statistic0,on='Name')
Demand_join.rename(columns={'Qh_MWh':'Qhf_Statistic','Qc_MWh':'Qcf_Statistic'}, inplace=True)

# <codecell>

fig = plt.figure(figsize=(20,7)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(Demand_join.index+width,Demand_join.Qhn_Simulated,width, color='#000000', label='Qhn_Simulated');
ax.bar(Demand_join.index+width+0.3,Demand_join.Qhf_Statistic,width,color='#708090',label='Qhf_Statistic');
ax.set_xticks(Demand_join.index+2*width); 
ax.set_xticklabels(Demand_join.Name);
plt.legend(loc='best');
plt.tight_layout()

# <codecell>

results = Demand_join.sum(axis=0)
results

# <codecell>

fig = plt.figure(figsize=(5,5)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(0+width,results[1],width, color='#000000', label='Qhn_Simulated');
ax.bar(0+width+0.3,results[3],width,color='#708090',label='Qhf_Statistic');
plt.legend(loc='best');
plt.tight_layout()

# <codecell>


