"""
============================================
Clusters the data using the kmeans algorithm
============================================

Followed steps are:
    - clustering for typical days
    - determination of combinations
    - clustering for typical hours

Modifications wrt previous version:
    - Extreme days
    - TODO : iterate for random starting points

"""
from __future__ import division
import os
os.chdir("C:/Users/Thuy-An/Documents/GitHub/urben/Masterarbeit/Clustering")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pickle import Pickler

import clusterFn as cFn
import findKopt as fk

reload(cFn)
reload(fk)


def clusterAll(
    nDay,
    fNameList,
    featureList,
    nPeriodMin,
    nPeriodMax,
    gam,
    threshErr):
		
    """
    Master clustering of days and hours

    Parameters
    ----------
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

    Returns
    -------
    Saves in the "Cluster" file :
    fileList : list
	List of tuples 
        (Building name [str], Feature [str])
    clusterDayRes : list
	List of tuples 
	(TypicalDays [ndarray], Distorsion [float], Codebook [ndarray])
    occListDay : list
	List of tuples
	(Combination [ndarray], Occurrence [int])
    clusterHourRes : list
	List of tuples
    (TypicalHours [ndarray], Distorsion [float], Codebook [ndarray])
	occListHour : list
	List of ndarray with the occurrences

    """	
    # Results objects

    fileList = []
    clusterDayRes = []
    occListDay = []
    clusterHourRes = []
    occListHour = []


    # Solar file

    print "Day-clustering for solar file"
    fileList.append(("Solar","G_glb"))

    file_ext = pd.read_csv("Solar_temp.csv", sep=";", usecols=["G_glb"], 
                           nrows=24*nDay)
    file_array = cFn.toarray(file_ext)
    (file_strip, front, back) = cFn.strip(file_array)

    kopt = fk.find_kopt(file_strip, nPeriodMin, nPeriodMax, gam, threshErr)

    (file_typ, file_dist, file_cb) = cFn.cluster(file_strip, kopt)
    (file_typ, file_cb) = cFn.addExtreme(file_strip, file_typ, file_cb)

    clusterDayRes.append((cFn.unstrip(file_typ, front, back), 
                          file_dist, file_cb))

    plt.figure(0)
    plt.plot(clusterDayRes[0][0].T)
    plt.title("Solar, Global radiation, " + str(len(clusterDayRes[0][0])) + 
              " centroids.")


    # Building files

    index = 1

    for feature in featureList:
        for fName in fNameList:

            print ("Day-clustering " + feature + " for " + 
                    fName[0:(len(fName)-4)])
            file_ext = cFn.extractCsv(fName, feature, nDay)
            file_array = cFn.toarray(file_ext)

            if np.count_nonzero(file_array) != 0:
		fileList.append((fName[0:(len(fName)-4)], feature))
                (file_strip, front, back) = cFn.strip(file_array)

                kopt = fk.find_kopt(file_strip, nPeriodMin, nPeriodMax, gam, 
                                    threshErr)

                (file_typ, file_dist, file_cb) = cFn.cluster(file_strip, kopt)
                (file_typ, file_cb) = cFn.addExtreme(file_strip, file_typ, 
                                                     file_cb)
                clusterDayRes.append((cFn.unstrip(file_typ, front, back), 
                                    file_dist, file_cb))

                plt.figure(index)
                plt.plot(clusterDayRes[index][0].T)
                plt.title(fName[0:(len(fName)-4)] + ", " + feature + ", " +
		          str(len(clusterDayRes[index][0])) + " centroids.")

                index += 1

            else:
                print("Feature " + feature + " is empty for building " + 
		       fName[0:(len(fName)-4)])

    plt.show()
		  

    # Strip down number of combinations

    print "Counting the number of combinations"
    el = len(clusterDayRes)
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

    print ("Strip down from " + str(nDay) + " to " + 
           str(len(occListDay)) + " days.")


    # Cluster the hours of the day

    print "Hour-clustering"
    for rank in range(len(occListDay)):
        
        print (str(len(occListDay)-rank) + " combinations left")
        selected_combi = occListDay[rank][0]

        file_array = np.array([clusterDayRes[0][0][selected_combi[0],:]]).T

        for i in range(1,el):
            file_array = np.concatenate((file_array.T, 
		       np.array([clusterDayRes[i][0][selected_combi[i],:]]))).T

        kopt = fk.find_kopt(file_array, nPeriodMin, nPeriodMax, gam, threshErr)
        (file_typ, file_dist, file_cb) = cFn.cluster(file_array, kopt)

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

        clusterHourRes.append((file_typ, file_dist, file_cb))


    # Store all results in "Cluster" file

    print "Storing the results"
    with open("Cluster","wb") as cluster_write:
        cluster_pick = Pickler(cluster_write)

        cluster_pick.dump(fileList)
        cluster_pick.dump(clusterDayRes)
        cluster_pick.dump(occListDay)
        cluster_pick.dump(clusterHourRes)
        cluster_pick.dump(occListHour)

    print "Work complete"
    

if __name__ == '__main__':
    clusterAll(
	nDay=365,
	fNameList = ["AA16.csv"],
        featureList = ["E"],
        nPeriodMin = 2,
        nPeriodMax = 15,
        gam = 0.2,
        threshErr = 0.2)
















