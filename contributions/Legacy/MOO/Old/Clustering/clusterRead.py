"""
=======================================
Reads the objects in the "Cluster" file
=======================================

"""
import os
from pickle import Unpickler

def clusterRead(path):
    """
    Loads the "Cluster" file:
        
    Parameters
    ----------
    path : string
        path to folder where the "cluster" file is
        
    Returns
    -------
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
        List of ndarray with the occurrence
        
    """
    os.chdir(path)
    
    with open("Cluster","rb") as cluster_read:
        cluster_unpick = Unpickler(cluster_read)

        fileList = cluster_unpick.load()
        clusterDayRes = cluster_unpick.load()
        occListDay = cluster_unpick.load()
        clusterHourRes = cluster_unpick.load()
        occListHour = cluster_unpick.load()

    return (fileList, clusterDayRes, occListDay, clusterHourRes, occListHour)
		

if __name__ == '__main__':
    clusterRead("C:/Users/Thuy-An/Documents/ETH/Arch Master Thesis/Python results")