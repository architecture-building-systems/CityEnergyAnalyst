"""
====================================
Clusters the data into typical hours
====================================

"""
from __future__ import division

import numpy as np

import clusterFn as cFn
import findKopt as fk


def clusterHour(
    clusterDayRes,
    occListDay,
    nPeriodMin,
    nPeriodMax,
    gam,
    threshErr,
    ):
    
    """
    Clustering of hours

    Parameters
    ----------
    clusterDayRes : list
        List which contains the (TypicalDays, Distorsion, Codebook) of the files
        already clustered.
    occListDay : list
	List of tuples (Combination [ndarray], Occurrence [int])
    nPeriodMin : int
 	Minimum number of periods
    nPeriodMax : int
        Maximum number of periods
    gam : float
        Threshold used with the 5th indicator (see clusterFn, countPer)
    threshErr : float
	Threshold to set the minimum accepted number of clusters (usually 20%)

    Returns
    -------
    clusterHourRes : list
	List of tuples
        (TypicalHours [ndarray], Distorsion [float], Codebook [ndarray])
    occListHour : list
	List of ndarray with the occurrences

    """	
    print "Hour-clustering for all combinations"
    el = len(clusterDayRes)
    occListHour = []
    clusterHourRes = []
    
    for rank in range(len(occListDay)):
        
        print (str(len(occListDay)-rank) + " combinations left")
        selected_combi = occListDay[rank][0]

        file_array = np.array([clusterDayRes[0][0][selected_combi[0],:]]).T

        for i in range(1,el):
            file_array = np.concatenate((file_array.T, 
		       np.array([clusterDayRes[i][0][selected_combi[i],:]]))).T
	
	(file_strip, stripList) = cFn.strip_similarity(file_array)

        kopt = fk.find_kopt(file_strip, nPeriodMin, nPeriodMax, gam, threshErr)
        (file_typ, file_dist, file_cb) = cFn.cluster(file_strip, kopt)

        # Calculates occurrence
        occurrence = np.zeros(len(file_typ))
        for i in range(len(file_cb)):
            occurrence[file_cb[i]] += 1

        occListHour.append(occurrence)

        # Add the extreme hours
        maxIndex = []
        for i in range(el):
            maxInd = np.argmax(file_array[:,i])
            if not (maxInd in maxIndex):
                maxIndex.append(maxInd)

        for rankMax in maxIndex:
            typDay = file_cb[rankMax]
            if occurrence[typDay] == 1:
                file_typ[typDay,:] = file_array[rankMax,:]
            else:
                file_typ = np.concatenate((file_typ, 
                         np.array([file_array[rankMax,:]]) ))
                occurrence = np.concatenate((occurrence, np.array([1]) ))
                occurrence[file_cb[rankMax]] -= 1
                file_cb[rankMax] = len(file_typ) - 1

        file_typm = cFn.unstrip_similarity(file_typ, stripList)
        clusterHourRes.append((file_typm, file_dist, file_cb))
        
    return clusterHourRes, occListHour
        
        
        
        
        
        
        
        
        