"""
====================================
Find k optimal for kmeans clustering
====================================

Find the optimal number of periods to call kmeans with,
taking into account 5 indicators and 3 statistic measures

"""
from __future__ import division

import numpy as np
import clusterFn as cFn


def find_kopt(file_array, nPeriodMin, nPeriodMax, gam, threshErr):
    """
    Find the optimal number of periods to call kmeans with,
	taking into account 5 indicators and 3 statistic measures
    
    Parameters
    ----------
    file_array : ndarray
        Observations
    nPeriodMin : int
		Minimum number of periods
    nPeriodMax : int
		Maximum number of periods
    gam : float
        For calculation of CountPer Indicator
    threshErr : float
        Usually 20%
        To monitor the improvement when going from k to k+1 clusters
    
    Returns
    -------
    kopt : int    
    
    """
    nPeriod = nPeriodMin
    (file_typ, file_dist, file_cb) = cFn.cluster(file_array, nPeriod)
    (profileDev, loadDev, countPer) = cFn.deviationInd(file_array, file_typ, 
                                        file_cb, gam)
    (eldc, ldcMax) = cFn.loadDeviation(file_array, file_typ, file_cb)
    
    profileDevB = False
    loadDevB = False
    countPerB = False
    eldcB = False
    ldcMaxB = False
    
    nPeriod += 1
    
    while (not(profileDevB and loadDevB and countPerB and eldcB and 
        ldcMaxB)) and (nPeriod <= nPeriodMax):
        
        (file_typ, file_dist, file_cb) = cFn.cluster(file_array, nPeriod)
        (profileDevR, loadDevR, countPerR) = cFn.deviationInd(file_array, file_typ, 
                                                            file_cb, gam)
        (eldcR, ldcMaxR) = cFn.loadDeviation(file_array, file_typ, file_cb)
    
        
        if not profileDevB:
            profileDevErr = abs(profileDevR - profileDev) / profileDev
            if profileDevErr < threshErr:
                profileDevB = True
            else:
                profileDev = profileDevR
            
        if not loadDevB:
            loadDevErr = abs(loadDevR - loadDev) / loadDev
            if loadDevErr < threshErr:
                loadDevB = True
            else:
                loadDev = loadDevR
    
        if not countPerB:
            countPerErr = abs(countPerR - countPer) / countPer
            if countPerErr < threshErr:
                countPerB = True
            else:
                countPer = countPerR
    
        if not eldcB:
            eldcErr = abs(eldcR - eldc) / eldc
            if eldcErr < threshErr:
                eldcB = True
            else:
                eldc = eldcR
    
        if not ldcMaxB:
            ldcMaxErr = abs(ldcMaxR - ldcMax) / ldcMax
            if ldcMaxErr < threshErr:
                ldcMaxB = True
            else:
                ldcMax = ldcMaxR
        
        nPeriod += 1
            
            
    kmin = nPeriod - 1
    
    (file_typ, file_dist, file_cb) = cFn.cluster(file_array, kmin - 1)
    intraOld = cFn.intra(file_array, file_typ, file_cb)
    
    intraA = np.zeros((nPeriodMax - kmin + 1, 2))
    interA = np.zeros((nPeriodMax - kmin + 1, 2))
    eseA = np.zeros((nPeriodMax - kmin + 1, 2))
    
    rank = 0
    for nPeriod in range(kmin, nPeriodMax + 1):
        (file_typ, file_dist, file_cb) = cFn.cluster(file_array, nPeriod)
    
        intraA[rank][1] = interA[rank][1] = eseA[rank][1] = nPeriod
        
        intraA[rank][0] = cFn.intra(file_array, file_typ, file_cb)    
        interA[rank][0] = cFn.inter(file_typ)
    
        eseA[rank][0] = cFn.ese(nPeriod, int(file_array.shape[1]), intraOld, 
                                intraA[rank][0])
        
        intraOld = intraA[rank][0]    
        rank += 1
        
    
    intraS = intraA[np.argsort(intraA[:,0])]
    interS = interA[np.argsort(interA[:,0])]
    eseS = eseA[np.argsort(eseA[:,0])]
    
    el = len(intraS)
    rank = 0
    kfound = False
    
    optsearch = np.empty(el)
    optsearch.fill(3)
    kopt = nPeriodMax
    
    while not kfound and rank<el:
        
        optsearch[intraS[rank][1] - kmin] -= 1
        optsearch[interS[el - rank - 1][1] - kmin] -= 1
        optsearch[eseS[rank][1] - kmin] -= 1
        
        if np.count_nonzero(optsearch) != el:
            kfound = True
            kopt = np.where(optsearch == 0)[0][0] + kmin
            
            
        rank += 1
    
    return kopt
    
    
    
    
    
    
    
    
    
    
    