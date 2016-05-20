import matplotlib as plt
import pandas as pd



def graphdemand2D(pathfile,heating,cooling,electricity):
    df =pd.read_csv(pathfile, usecols=['Date',heating,cooling,electricity])
    fig = plt.figure()
    df.plot()
return print 'Plot'
    
scenario = 'SQ'
heating = 'HD1 [MW]'
cooling = 'CD1 [MW]'
electricity = 'ED1 [MW]'
pathfile: 'C:\ArcGIS\EDMdata\DataFinal\EDM\'+\\'+sceanrio+'\\'+\ZONE_4\Series.csv'


graphdemand2D(pathfile,heating,cooling,electricity):