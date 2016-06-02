# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ##MODULES

# <codecell>

import matplotlib.pyplot as plt
import pandas as pd

# <markdowncell>

# Import files with the measured heating demand in buildings of the cityquarter to analyse

# <codecell>

Data_measured= pd.ExcelFile(r'C:\ArcGIS\EDMdata\Measured\CityQuarter_3\Loads.xls')
Loads = pd.ExcelFile.parse(Data_measured, 'Values')
Measured = Loads[['Name','Qcsf','Qcdataf','Qcpf','Ealf','Edataf','Epf','Qwwf','Qhpf','Qhsf']]
CQ_name = 'CityQuarter_3'
Scenario = 'StatusQuo'
locationFinal = r'c:\ArcGIS\EDMdata\DataFinal'+'\\'+'DEDM'+'\\'+Scenario+'\\'+CQ_name

# <codecell>

Data_Analytical = pd.read_csv(locationFinal+'\\'+'total.csv')
Analytical = Data_Analytical[['Name','Qhsf','Qcsf','Ealf','Qwwf']]

# <codecell>

Data_statistic = pd.read_csv(r'C:\ArcGIS\EDMdata\DataFinal\SEDM\StatusQuo\CityQuarter_3\Loads.csv')
Statistic = Data_statistic[['Name','Qcsf','Qcdataf','Qcpf','Ealf','Edataf','Epf','Qwwf','Qhpf','Qhsf']]

# <codecell>

join1 = pd.merge(Measured,Statistic,left_on='Name', right_on='Name',suffixes=('_M', '_S'),how='inner')
Demand_join = pd.merge(join1,Analytical,left_on='Name', right_on='Name',how='inner')
Demand_join.to_excel(r'C:\ArcGIS\EDMdata\DataFinal\Models Validation\Values.xls',sheet_name='Values')
Demand_join.transpose().to_excel(r'C:\ArcGIS\EDMdata\DataFinal\Models Validation\ValuesT.xls',sheet_name='Values')

# <markdowncell>

# Import files with the results of the model to compare

# <codecell>

fig = plt.figure(figsize=(16,7)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(Demand_join.index+width,Demand_join.Qhsf_S,width, color='#000000', label='Qhsf_S');
ax.bar(Demand_join.index+width+0.3,Demand_join.Qhsf_M,width,color='#2f4f4f',label='Qhsf_M');
ax.bar(Demand_join.index+width+0.6,Demand_join.Qhsf,width,color='#708090',label='Qhsf_A');
ax.set_xticks(Demand_join.index+2.5*width); 
ax.set_xticklabels(Demand_join.Name);
plt.legend(loc='best');
plt.tight_layout()

# <codecell>

fig = plt.figure(figsize=(16,7)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(Demand_join.index+width,Demand_join.Qcsf_S,width, color='#0000cd', label='Qcsf_S');
ax.bar(Demand_join.index+width+0.3,Demand_join.Qcsf_M,width,color='#1e90ff',label='Qcsf_M');
ax.bar(Demand_join.index+width+0.6,Demand_join.Qcsf,width,color='#4169e1',label='Qcsf_A');
ax.set_xticks(Demand_join.index+2.5*width); 
ax.set_xticklabels(Demand_join.Name);
plt.legend(loc='best');
plt.tight_layout()

# <codecell>

fig = plt.figure(figsize=(16,7)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(Demand_join.index+width,Demand_join.Ealf_S,width, color='#0000cd', label='Ealf_S');
ax.bar(Demand_join.index+width+0.3,Demand_join.Ealf_M,width,color='#1e90ff',label='Ealf_M');
ax.bar(Demand_join.index+width+0.6,Demand_join.Ealf,width,color='#4169e1',label='Ealf_A');
ax.set_xticks(Demand_join.index+2.5*width); 
ax.set_xticklabels(Demand_join.Name);
plt.legend(loc='best');
plt.tight_layout()

# <codecell>

fig = plt.figure(figsize=(16,7)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(Demand_join.index+width,Demand_join.Qwwf_S,width, color='#0000cd', label='Qwwf_S');
ax.bar(Demand_join.index+width+0.3,Demand_join.Qwwf_M,width,color='#1e90ff',label='Qwwf_M');
ax.bar(Demand_join.index+width+0.6,Demand_join.Qwwf,width,color='#4169e1',label='Qwwf_A');
ax.set_xticks(Demand_join.index+2.5*width); 
ax.set_xticklabels(Demand_join.Name);
plt.legend(loc='best');
plt.tight_layout()

# <codecell>

fig = plt.figure(figsize=(16,7)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(Demand_join.index+width,Demand_join.Epf_M,width, color='#0000cd', label='Epf_M');
ax.bar(Demand_join.index+width+0.3,Demand_join.Epf_S,width,color='#1e90ff',label='Epf_S');
ax.set_xticks(Demand_join.index+2.5*width); 
ax.set_xticklabels(Demand_join.Name);
plt.legend(loc='best');
plt.tight_layout()

# <codecell>

fig = plt.figure(figsize=(16,7)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(Demand_join.index+width,Demand_join.Qhpf_M,width, color='#0000cd', label='Qhpf_M');
ax.bar(Demand_join.index+width+0.3,Demand_join.Qhpf_S,width,color='#1e90ff',label='Qhpf_S');
ax.set_xticks(Demand_join.index+2.5*width); 
ax.set_xticklabels(Demand_join.Name);
plt.legend(loc='best');
plt.tight_layout()

# <codecell>

fig = plt.figure(figsize=(16,7)); ax= fig.add_subplot(111); width = 0.3; 
ax.bar(Demand_join.index+width,Demand_join.Qcdataf_M,width, color='#0000cd', label='Edataf_M');
ax.bar(Demand_join.index+width+0.3,Demand_join.Qcdataf_S,width,color='#1e90ff',label='Edataf_S');
ax.set_xticks(Demand_join.index+2.5*width); 
ax.set_xticklabels(Demand_join.Name);
plt.legend(loc='best');
plt.tight_layout()

# <codecell>


