# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# #Statistical Energy demand model (S-EDM)

# <markdowncell>

# ###MODULES

# <codecell>

import pandas as pd
import sys
if r'C:\Console' not in sys.path: sys.path.append(r'C:\Console')
import EDMFunctions as EDM
import os

# <markdowncell>

# ###VARIABLES

# <codecell>

database = r'c:\Zernez\EDM.gdb'
Scenarios = ['SQ']#,'BAU','HEB','CAMP','UC']
number_of_zones = 1#20
Zone_of_study = 1

# <codecell>

Statistical_database = pd.ExcelFile('c:\Zernez\EDMdata\Statistical\Archetypes_properties.xls')
Model = pd.ExcelFile.parse(Statistical_database, 'Values')

# <codecell>

locationtemp1 = r'c:\Zernez\temp'
locationSEDM = r'C:\Zernez\EDMdata\DataFinal\SEDM'

# <markdowncell>

# ###PROCESS

# <codecell>

#FOR THE WHOLE AREA
for x in Scenarios:
    #Variables
    area = x+'AREA'
    locationFinal = locationSEDM+'\\'+x
    # confirm directory to save results
    if not os.path.exists(locationFinal):
        os.makedirs(locationFinal)
    # run querry or statistics and export results
    EDM.Querystatistics(database+'\\'+x+'\\'+area, 'Area', Model, locationtemp1,locationFinal)
    print 'Complete'+' '+x 

# <codecell>

# FOR EACH ZONE OF STUDY
# zones different to the Zone of study are stored in a folder called surroundings
for x in Scenarios:
    if x == 'SQ': #only for the first scenario
        for number in range(number_of_zones):
            Zone = 'Zone_'+str(number+1)
            if number+1 != Zone_of_study:
                # set local variables for iteration
                locationFinal = locationSEDM+'\\'+'Surroundings'
                # confirm directory to save results
                if not os.path.exists(locationFinal+'\\'+Zone):
                    os.makedirs(locationFinal+'\\'+Zone)
                # run querry or statistics and export results
                EDM.Querystatistics(database+'\\'+'Surroundings'+'\\'+Zone, Zone, Model, locationtemp1,locationFinal)
            else:
                # set local variables for iteration
                locationFinal = locationSEDM+'\\'+x
                # confirm directory to save results
                if not os.path.exists(locationFinal+'\\'+Zone):
                    os.makedirs(locationFinal+'\\'+Zone)
                # run querry or statistics and export results
                EDM.Querystatistics(database+'\\'+x+'\\'+x+Zone, Zone, Model, locationtemp1,locationFinal)                
    else:
        Zone = 'Zone_'+str(Zone_of_study)
        locationFinal = locationSEDM+'\\'+x
        # confirm directory to save results
        if not os.path.exists(locationFinal+'\\'+Zone):
            os.makedirs(locationFinal+'\\'+Zone)
        # run querry or statistics and export results
        EDM.Querystatistics(database+'\\'+x+'\\'+x+Zone, Zone, Model, locationtemp1,locationFinal)
    print 'Complete'+' '+x 

# <codecell>


