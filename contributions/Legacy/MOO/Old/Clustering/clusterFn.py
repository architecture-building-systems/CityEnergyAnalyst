"""
==================================
Data clustering, support functions
==================================

Provides routines for k-means clustering
Modifications wrt previous version: 5 indicators instead of 1

"""
from __future__ import division
import numpy as np
import pandas as pd
from scipy.cluster.vq import kmeans,vq,whiten
from sklearn import metrics
from math import sqrt


def extractCsv(fName, colName, nDay):
    """
    Extract data from one column of a csv file to a pandas.DataFrame
    
    Parameters
    ----------
    fName : string
        Name of the csv file.
    colName : string
        Name of the column from whom to extract data.
    nDay : int
        Number of days to consider.
        
    Returns
    -------
    result : pandas.DataFrame
        Contains the hour of the day in the first column and the data 
        of the selected column in the second.   
    
    """
    result = pd.read_csv(fName, usecols=[colName], nrows=24*nDay)
    return result

        
def toarray(df):
    """
    Takes a DataFrame and transposes it to an array useable for the 
    Python built-in kmeans function. Each row of the array represents 
    a day and each column a feature.
    
    Parameters
    ----------
    df : DataFrame
        From km_extract.
    
    Returns
    -------
    result : ndarray
    
    """
    df_to_array = np.array(df)
    result = np.zeros((len(df_to_array)//24,24))

    i=0
    j=0
    for k in range(len(df_to_array)):
        result[i,j] = df_to_array[k,0]
        j+=1
        if j==24:
            j=0
            i+=1
    return result


def cluster(obs,nPeriod):
    """
    Takes an array of observations and the desired number of typical
    days. Returns the array of typical days, the overall distortion and 
	an array which assigns each day to a typical day.
    
    Parameters
    ----------
    obs : ndarray
        Array of observations. Each row represents a day and each column
        a feature.
    nPeriod : int
        Desired number of typical periods to obtain.
    
    Returns
    -------
    typical_days : ndarray
        Each row represents a typical day and each column a feature.
    distortion : float
        The square error between the observations and the centroids.
    codebook : ndarray
        Assigns to each day of obs, the corresponding typical day.
        
    """
    obs_wh = whiten(obs)
    obs_km = kmeans(obs_wh, nPeriod)
    obs_vq = vq(obs_wh, obs_km[0])

    typical_days = obs_km[0]*np.std(obs,axis =0)
    distorsion = obs_km[1]
    codebook = obs_vq[0]
    
    return typical_days, distorsion, codebook


def strip(array):
    """
    Strips out the columns, at the beginning and the end of the array,
    where there are only 0.
    
    Parameters
    ----------
    array : ndarray
    
    Returns
    -------
    result : ndarray
        Stripped array
    front : int
        Number of columns stripped at the beginning of the array
    back : int
        Number of columns stripped at the end of the array
        
    """
    stop = False
    front = 0
    back_rk = int(array.shape[1])-1
    
    while not stop:
        if np.count_nonzero(array[:,front]) == 0:
            front += 1
        else:
            stop = True
    
    stop = False
    while not stop:
        if np.count_nonzero(array[:,back_rk]) == 0:
            back_rk -= 1
        else:
            stop = True

    result = array[:,front:(back_rk+1)]
    back = int(array.shape[1]) - back_rk - 1
    
    return result, front, back


def unstrip(array, front, back):
    """
    Takes an array and adds 0 columns at the front and at the back.
    
    Parameters
    ----------
    array : ndarray
    front : int
        Number of columns to add at the front
    back : int
        Number of columns to add at the back
    
    Returns
    -------
    result : ndarray
        Array with 0 columns added
        
    """
    length = int(array.shape[0])
    front_array = np.zeros((length,front))
    back_array = np.zeros((length,back))
    
    result = np.concatenate((front_array.T,array.T,back_array.T))
    return result.T


def silhouette(obs, cb):
    """
    Parameters
    ----------
    obs : ndarray
        Array of observations. Each row represents a day and each column
        a feature.
    cb : ndarray
        Codebook
        
    Returns
    -------
    silhouette : float
        Silhouette Score

    """
    obs_norm = (obs - obs.mean()) / (obs.max() - obs.min()) # normalized
    obs_matrix = np.matrix(obs_norm) # create matrix form    
    
    #Calc Silhouette Coeff Score (for global use)
    silhouette = metrics.silhouette_score(obs_matrix, cb, metric='euclidean')
    
    return silhouette


def deviationInd(obs, cluster, cb, gam):
    """
    Calculates deviation indicators, according to S. Fazlollahi
    
    Parameters
    ----------
    obs : ndarray
        Array of raw observations
    cluster : ndarray
        Typical observations, obtained with kmeans
    cb : ndarray
        Codebook, obtained with kmeans
        
    Returns
    -------
    profileDev : float
        Profile deviation
    avgDev : float
        Daily-averages deviation
    countPer : int
		Number of periods with relative error above gam
		
    
    """
    nDay = len(obs)
    nHour = int(obs.shape[1])
    nCluster = len(cluster)
    
    avgDay = []
    for i in range(nDay):
        avgDay.append(np.mean(obs[i,:]))
    
    avgCluster = []
    for i in range(nCluster):
        avgCluster.append(np.mean(cluster[i,:]))
        
    avgAll = np.mean(obs)
    
    profileDev = 0
    for i in range(nDay):
        rankCl = cb[i]
        for g in range(nHour):
            profileDev += (obs[i,g] - avgDay[i] - cluster[rankCl, g] + 
                        avgCluster[rankCl]) ** 2
    profileDev = sqrt(profileDev / (nDay * nHour * avgAll**2))
    
    avgDev = 0
    for i in range(nDay):
        rankCl = cb[i]
        avgDev += (1- avgCluster[rankCl]/avgDay[i]) ** 2
    avgDev = sqrt(avgDev / nDay)
    
    countPer = 1
    for i in range(nDay):
        indic = 0
        for g in range(nHour):
            rankCl = cb[i]
            indic += abs(obs[i,g] - cluster[rankCl, g]) / (obs[i,g])
        if indic > gam:
            countPer += 1
    
    return profileDev, avgDev, countPer
    

def loadDeviation(obs, cluster, cb):
    """
    Calculates deviation indicators, according to S. Fazlollahi
    
    Parameters
    ----------
    obs : ndarray
        Array of raw observations
    cluster : ndarray
        Typical observations, obtained with kmeans
    cb : ndarray
        Codebook, obtained with kmeans
        
    Returns
    -------
    eldc : float
		Load duration curve deviation
    ldcMax : float
		Maximum load duration curve difference
	
    """
    nDay = len(obs)
    
    ldc = sorted(obs.flatten())
    
    ldcClustTemp = cluster[cb[0],:] 
    for i in range(1,nDay):
        ldcClustTemp = np.concatenate((ldcClustTemp, cluster[cb[i],:]))
    ldcClust = sorted(ldcClustTemp.flatten())
    
    eldc = 0
    for i in range(nDay):
        eldc += abs(ldc[i] - ldcClust[i])
    eldc = eldc / sum(ldc)
    
    el_ldc = len(ldc)
    ldcMax = abs(ldc[el_ldc-1] - ldcClust[el_ldc-1]) / (ldc[el_ldc-1])
        
    return eldc, ldcMax
        

def intra(obs, cluster, cb):
    """
    Calculates intra-cluster distance, according to S. Fazlollahi
    
    Parameters
    ----------
    obs : ndarray
        Array of raw observations
    cluster : ndarray
        Typical observations, obtained with kmeans
    cb : ndarray
        Codebook, obtained with kmeans
        
    Returns
    -------
    intraDist : float
    
    """
    nDay = len(obs)
    nHour = int(obs.shape[1])
    nCluster = len(cluster)
    
    intraDist = 0
    for i in range(nDay):
        rankCl = cb[i]
        for g in range(nHour):
            intraDist += (obs[i,g] - cluster[rankCl, g]) ** 2
    intraDist = intraDist / nCluster
    
    return intraDist
    
    
def inter(cluster):
    """
    Calculates inter-cluster distance, according to S. Fazlollahi
    
    Parameters
    ----------
    cluster : ndarray
        Typical observations, obtained with kmeans
        
    Returns
    -------
    interDist : float
    
    """
    nCluster = len(cluster)
    nHour = int(cluster.shape[1])
    
    interDist = 0
    
    for i in range(nCluster):    
        for j in range(i+1,nCluster):
            for g in range(nHour):
                interDist += (cluster[i,g] - cluster[j,g]) ** 2
    
    interDist = interDist * 2 / nCluster ** 2
    
    return interDist


def ese(nPeriod, el, intraPre, intraCur):
    """
    Calculates the ratio of observed to expected squared errors, 
    according to S. Fazlollahi
    
    Parameters
    ----------
    nPeriod : int
    el : int
        Width of the observation array
    intraPre : float
        intraDist calculated for nPeriod - 1
    intraCur : float
        intraDist calculated for nPeriod

    Returns
    -------
    ese : float
        Ratio of observed to expected squared errors

    """
    if nPeriod == 1 or intraPre == 0:
        ese = 1
    
    else:
        alphIni = 1 - 3 / (4 * el)
        
        if nPeriod == 2:
            alph = alphIni
        else:
            a = 5/6
            b = 1/6
            r = b / (1-a)
            alph = a ** (nPeriod-2) * (alphIni - r) + r
        
        ese = nPeriod * intraCur / (alph * (nPeriod-1) * intraPre )
        
    return ese


def addExtreme(obs, cluster, cb):
    """
    Add the extreme day as a typical day
    
    Parameters
    ----------
    obs : ndarray
        Array of raw observations
    cluster : ndarray
        Typical observations, obtained with kmeans
    cb : ndarray
        Codebook, obtained with kmeans
        
    Returns
    -------
    new_cluster : ndarray
        Typical days, with the extreme added
    new_cb : ndarray
        Codebook modified accordingly
        
    """
    nHour = int(obs.shape[1])
    nDay = int(obs.shape[0])
    maxInd = np.argmax(obs) // nHour
    
    new_cb = np.copy(cb)

    typDay = cb[maxInd]
    if (typDay in cb[0:maxInd]) or (typDay in cb[maxInd+1:nDay]):
        new_cluster = np.concatenate((cluster, np.array([obs[maxInd,:]]) ))
        new_cb[maxInd] = len(new_cluster) - 1
        
    else:
        new_cluster = np.copy(cluster)
        new_cluster[typDay,:] = obs[maxInd,:]

    return new_cluster, new_cb


def strip_middle(array):
    """
    Strips out the columns, in the middle of the array,
    where there are only 0.
    
    Parameters
    ----------
    array : ndarray
    
    Returns
    -------
    result : ndarray
        Stripped array
    ncol : int
        Number of columns stripped
    nfirst : int
        Rank of the first column stripped
        
    """
    stop_found = False
    stop_strip = False

    nrank = 0
    ncol = 0
    
    while (not stop_found) or (not stop_strip):
        if not stop_found:
            if nrank == int(array.shape[1]):
                break
            else:
                if np.count_nonzero(array[:,nrank]) == 0:
                    stop_found = True
                    ncol += 1
                    nrank +=1
                else:
                    nrank += 1
        else:
            if np.count_nonzero(array[:,nrank]) == 0:
                ncol += 1
                nrank += 1
            else:
                stop_strip = True

    nfirst = nrank - ncol
    result = np.concatenate((array[:,0:nfirst].T,array[:,nrank:].T)).T
    
    return result, ncol, nfirst


def unstrip_middle(array, ncol, nfirst):
    """
    Takes an array and adds 0 columns in the middle.
    
    Parameters
    ----------
    array : ndarray
    ncol : int
        Number of columns stripped
    nfirst : int
        Rank of the first column stripped
    
    Returns
    -------
    result : ndarray
        Array with 0 columns added
        
    """
    length = int(array.shape[0])
    middle_array = np.zeros((length,ncol))
    
    result = np.concatenate((array[:,0:nfirst].T,
                             middle_array.T,
                             array[:,nfirst:].T))
    return result.T


def strip_similarity(array):
    """
    Takes an array and remove columns where the feature is EXACTLY the same
    throughout the year
    
    Parameters
    ----------
    array : ndarray
    
    Returns
    -------
    result : ndarray
        array stripped
    striplist : list
        List of tuples (rank of the column removed, original feature value)
    
    """
    nhour = int(array.shape[1])
    nday = int(array.shape[0])
    array_totreat = np.zeros((nday,nhour))
    
    stripList = []
    
    for hour in range(nhour):
        value = array[0,hour]
        for day in range(nday):
            array_totreat[day,hour] = array[day,hour] - value
        if np.count_nonzero(array_totreat[:,hour]) == 0:
            stripList.append((hour, value))
    
    ncoltoremove = len(stripList)
    if ncoltoremove != 0:
        result = array[:,0:stripList[0][0]]
        for interval in range(ncoltoremove - 1):
            rankbefore = stripList[interval][0]
            rankafter = stripList[interval+1][0]
            columnstoadd = array[:, (rankbefore+1) : rankafter]
            result = np.concatenate((result.T, columnstoadd.T)).T
        lastrank = stripList[ncoltoremove-1][0]
        lastcolumns = array[:,lastrank+1:]
        result = np.concatenate((result.T, lastcolumns.T)).T
    
    else:
        result = array
    
    return result, stripList


def unstrip_similarity(array, stripList):
    """
    Unstrip the array
    
    Parameters
    ----------
    array : ndarray
        stripped array
    stripList : list
    
    Returns
    -------
    result : ndarray
        unstrip array
    
    """
    nday = int(array.shape[0])
    ncoltoadd = len(stripList)
    if ncoltoadd != 0:
        result = array[:, 0:stripList[0][0] ]
        ncolumnadded = stripList[0][0]
        
        for interval in range(ncoltoadd-1):
            columnvalue = stripList[interval][1]
            columntoadd = np.zeros((nday,1))
            columntoadd.fill(columnvalue)
            
            result = np.concatenate((result.T, columntoadd.T)).T
            
            ninterval = stripList[interval+1][0] - stripList[interval][0] - 1
            intervalcol = array[:,ncolumnadded : ncolumnadded + ninterval]
            
            result = np.concatenate((result.T, intervalcol.T)).T
            
            ncolumnadded += ninterval
        
        columnvalue = stripList[ncoltoadd-1][1]
        columntoadd = np.zeros((nday,1))
        columntoadd.fill(columnvalue)
        
        result = np.concatenate((result.T, columntoadd.T)).T
        result = np.concatenate((result.T, array[:,(ncolumnadded):].T)).T
            
    
    else:
        result = array
    
    return result



