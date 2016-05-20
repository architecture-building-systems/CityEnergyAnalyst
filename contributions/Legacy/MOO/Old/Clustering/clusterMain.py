"""
============================================
Clusters the data using the kmeans algorithm
============================================

Followed steps are:
    - clustering for typical days
    - determination of combinations
    - clustering for typical hours

Modifications wrt previous version:
    - Extreme days added
    - TODO : iterate for random starting points

"""
from __future__ import division
import os
import pandas as pd

#from pickle import Pickler


import clusterFn as cFn
import findKopt as fk
import clusterDay as cDay
import combi
import clusterHour as cHour

reload(cFn)
reload(fk)
reload(cDay)
reload(combi)
reload(cHour)


def clusterMain(
    pathdata,
    pathresult,
    nDay=365,
    fNameList = [],
    featureList = [],
    nPeriodMin = 2,
    nPeriodMax = 15,
    gam = 0.2,
    threshErr = 0.2,
    ):
    
    # Clustering
           
    fileList, clusterDayRes = \
        cDay.clusterDay(pathdata, pathresult, nDay, fNameList, featureList, nPeriodMin,\
        nPeriodMax, gam, threshErr)
        
    occListDay = combi.combi(pathdata, pathresult, fileList, clusterDayRes)
    
    ## Create codebook file
    #
    #os.chdir(pathdata)
    #dico = {}
    #
    #el = len(fileList)
    #for i in range(el):
    #    dico[ fileList[i][0] + fileList[i][1] ] = clusterDayRes[i][2]
    #
    #cbtocsv = pd.DataFrame(dico)
    #
    #fName_result = "Codebook.csv"
    #cbtocsv.to_csv(fName_result, sep= ',')
    #
    #clusterHourRes, occListHour = \
    #    cHour.clusterHour(clusterDayRes, occListDay, nPeriodMin, nPeriodMax,\
    #    gam, threshErr)
    
    #os.chdir(pathdata)
    #print "Storing the results"
    #
    #with open("Cluster","wb") as cluster_write:
    #    cluster_pick = Pickler(cluster_write)
    #
    #    cluster_pick.dump(fileList)
    #    cluster_pick.dump(clusterDayRes)
    #    cluster_pick.dump(occListDay)
        #cluster_pick.dump(clusterHourRes)
        #cluster_pick.dump(occListHour)
    
    print "Work complete"

    return fileList, clusterDayRes, occListDay
