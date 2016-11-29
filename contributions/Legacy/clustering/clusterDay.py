"""
===================================
Clusters the data into typical days
===================================

TODO : iterate for random starting points

"""
from __future__ import division
import os

import numpy as np
import pandas as pd
#import matplotlib.pyplot as plt

import clusterFn as cFn
import findKopt as fk
reload(cFn)
reload(fk)

def clusterDay(
    pathdata,
    pathresult,
    nDay,
    fNameList,
    featureList,
    nPeriodMin,
    nPeriodMax,
    gam,
    threshErr):
		
    """
    Clustering of days

    Parameters
    ----------
    pathdata : string
        path to folder where data are stored
    pathresult : string
        path to folder where results are stored
    nDay : int
	Number of days to take into account
    fNameList : list
	List of building's names
    featureList : list
	List of features (electricity, heating etc.)
    nPeriodMin : int
 	Minimum number of periods
    nPeriodMax : int
        Maximum number of periods
    gam : float
        Threshold used with the 5th indicator (see clusterFn, countPer)
    threshErr : float
	Threshold to set the minimum accepted number of clusters (usually 20%)
    [discarded] fileList : list
        List which contains the (file name, feature) already clustered.
        Defaut value is []
    [discarded] clusterDayRes : list
        List which contains the (TypicalDays, Distorsion, Codebook) of the files
        already clustered. Defaut value is []

    Returns
    -------
    fileList : list
	List of tuples 
        (Building name [str], Feature [str])
    clusterDayRes : list
	List of tuples 
	(TypicalDays [ndarray], Distorsion [float], Codebook [ndarray])

    """	
    fileList = []
    clusterDayRes = []
    index = len(fileList)
    
    for feature in featureList:
        for fName in fNameList:

            os.chdir(pathdata)
            print ("Day-clustering " + feature + " for " + 
                    fName[0:(len(fName)-4)])
            
            file_ext = cFn.extractCsv(fName, feature, nDay)
            file_arraym = cFn.toarray(file_ext)
            file_array = np.nan_to_num(file_arraym)
            
            for i in range(nDay):
                for j in range(24):
                    if file_array[i,j] < 1E-5:
                        file_array[i,j] = 0

            if np.count_nonzero(file_array) != 0:
                fileList.append((fName[0:(len(fName)-4)], feature))
                (file_strip, stripList) = cFn.strip_similarity(file_array)
                
                kopt = fk.find_kopt(file_strip, nPeriodMin, nPeriodMax, gam, 
                                    threshErr)

                (file_typ, file_dist, file_cb) = cFn.cluster(file_strip, kopt)
                (file_typadd, file_cbadd) = cFn.addExtreme(file_strip, file_typ, 
                                                     file_cb)

                file_typm = cFn.unstrip_similarity(file_typadd, stripList)
                clusterDayRes.append((file_typm, file_dist, file_cbadd))

            #    plt.figure(index)
            #    plt.plot(clusterDayRes[index][0].T)
            #    plt.title(fName[0:(len(fName)-4)] + ", " + feature + ", " +
		          #str(len(clusterDayRes[index][0])) + " centroids.")

                index += 1
                
                os.chdir(pathresult)
                results = pd.DataFrame(clusterDayRes[len(clusterDayRes)-1][0].T)
                fName_result = "Clustered_" + fName[0:(len(fName)-4)] + "_" + feature + ".csv"
                results.to_csv(fName_result, sep= ',')

            else:
                print("Feature " + feature + " is empty for building " + 
		       fName[0:(len(fName)-4)])
	   
    #plt.show()

    return fileList, clusterDayRes




