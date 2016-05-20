"""
==========================================
Evolutionary algorithm - Support functions
==========================================

"""
from __future__ import division
import numpy as np
import pandas as pd


def extractList(fName):
    """
    Extract the names of the buildings in the area
    
    Parameters
    ----------
    fName : string
        csv file with the names of the buildings
    
    Returns
    -------
    namesList : list
        List of strings with the names of the buildings
    
    """
    df = pd.read_csv(fName, usecols=["Name"])
    namesList = df['Name'].values.tolist()

    return namesList


def extractDemand(fName, colNameList, nDay):
    """
    Extract data from the columns of a csv file to an array.

    WARNING : the order of the columns in the array are the SAME as in the
    original file and NOT the order in the colNameList
    
    Parameters
    ----------
    fName : string
        Name of the csv file.
    colNameList : list
        List of the columns' name from whom to extract data.
    nDay : int
        Number of days to consider.
        
    Returns
    -------
    result : np.array
    
    """
    df = pd.read_csv(fName, usecols=colNameList, nrows=24*nDay)
    result = np.array(df)

    return result
