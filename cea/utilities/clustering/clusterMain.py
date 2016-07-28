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

import cea.globalvar as gv

import clusterDay as cDay
import clusterFn as cFn
import combi
import findKopt as fk

reload(gv)
reload(cFn)
reload(fk)
reload(cDay)
reload(combi)


def clusterMain(
    pathdata,
    pathresult,
    nDay=gv.DAYS_IN_YEAR,
    fNameList = [],
    featureList = [],
    nPeriodMin = gv.nPeriodMin,
    nPeriodMax = gv.nPeriodMax,
    gam = gv.gam,
    threshErr = gv.threshErr,
    ):
    
    # Clustering
           
    fileList, clusterDayRes = \
        cDay.clusterDay(pathdata, pathresult, nDay, fNameList, featureList, nPeriodMin,\
        nPeriodMax, gam, threshErr)

    occListDay = combi.combi(pathdata, pathresult, fileList, clusterDayRes)
   
    print "Clustering complete for", fNameList[0], "\n"

    return fileList, clusterDayRes, occListDay
