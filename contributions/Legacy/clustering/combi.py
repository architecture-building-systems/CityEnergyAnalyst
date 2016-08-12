"""
===========================
Calculates the combinations
===========================

"""
from __future__ import division
import os

import numpy as np
import pandas as pd


def combi(
    pathdata,
    pathresult,
    fileList,
    clusterDayRes,
    ):
    """
    Computes the existing combinations of typical days
    
    Parameters
    ----------
    pathdata : string
        path to folder where data are stored
    pathresult : string
        path to folder where results are stored
    fileList : list
        List which contains the (file name, feature) already clustered.
    clusterDayRes : list
        List which contains the (TypicalDays, Distorsion, Codebook) of the file
        already clustered.
        
    Returns
    -------
    occListDay : list
	List of tuples (Combination [ndarray], Occurrence [int])

    """
    os.chdir(pathdata)
    occListDay = []    
    
    print "Counting the number of combinations"
    el = len(clusterDayRes)
    nDay = len(clusterDayRes[0][2])
    cb_array = np.zeros((nDay,el))
    cb_array_sorted = np.zeros((nDay,el))

    indices = np.lexsort([clusterDayRes[k][2] for k in range(el)])

    for i in range(el):
        cb_array[:,i] = clusterDayRes[i][2]

    for i in range(nDay):
        cb_array_sorted[i,:] = cb_array[indices[i],:]

    cb_array = np.concatenate((cb_array_sorted,np.zeros((1,el))))
    del cb_array_sorted

    new_combi = False
    occ = 1

    for i in range(nDay):
        if np.count_nonzero(cb_array[i,:] - cb_array[i+1,:]) != 0:
            new_combi = True
        else:
            occ += 1
        if new_combi:
            occListDay.append((cb_array[i,:],occ))
            new_combi = False
            occ = 1
            
    combi_toexport = np.zeros((len(occListDay),el+1))
    for i in range(len(occListDay)):
        for j in range(el):
            combi_toexport[i,j] = occListDay[i][0][j]
        combi_toexport[i,el] = occListDay[i][1]
    
    dico = {}
    
    for i in range(el):
        dico[ fileList[i][0] + fileList[i][1] ] = combi_toexport[:,i]
    dico["Occurrences"] = combi_toexport[:,el]
    
    os.chdir(pathresult)
    results = pd.DataFrame(dico)
    fName = fileList[0][0]
    fName_result = "Combi_" + fName +".csv"
    results.to_csv(fName_result, sep= ',')
    
    print ("Strip down from " + str(nDay) + " to " + 
           str(len(occListDay)) + " days.")


    return occListDay







