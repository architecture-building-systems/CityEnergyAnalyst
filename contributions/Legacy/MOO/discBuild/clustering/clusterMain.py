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

import globalVar as gV
import clusterFn as cFn
import findKopt as fk
import clusterDay as cDay
import combi

reload(gV)
reload(cFn)
reload(fk)
reload(cDay)
reload(combi)


def clusterMain(
    pathdata,
    pathresult,
    nDay=gV.DAYS_IN_YEAR,
    fNameList = [],
    featureList = [],
    nPeriodMin = gV.nPeriodMin,
    nPeriodMax = gV.nPeriodMax,
    gam = gV.gam,
    threshErr = gV.threshErr,
    ):
    
    # Clustering
           
    fileList, clusterDayRes = \
        cDay.clusterDay(pathdata, pathresult, nDay, fNameList, featureList, nPeriodMin,\
        nPeriodMax, gam, threshErr)

    occListDay = combi.combi(pathdata, pathresult, fileList, clusterDayRes)
   
    print "Clustering complete for", fNameList[0], "\n"

    return fileList, clusterDayRes, occListDay
