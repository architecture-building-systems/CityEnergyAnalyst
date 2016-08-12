"""
=================
Support functions
=================

"""
from __future__ import division
import numpy as np
import pandas as pd
import os
from numpy.random import random_sample
from pickle import Unpickler
from deap import base
from deap import creator
import math


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


def calcQmax(fName, filepath, gV):
    """
    Calculates the peak heating power in fName file
    
    Parameters
    ----------
    fname : string
        Name of the csv file
    filepath : string
        path to the file
    
    Returns
    -------
    Qmax: float
        maximum heating power [W]
    
    """    
    HeatfeatureList = ["T_sst_heat_return_netw_total", "T_sst_heat_supply_netw_total", "mdot_DH_netw_total"]
    buildDemand = extractDemand(filepath+'//'+fName, HeatfeatureList, gV.DAYS_IN_YEAR)
    Qmax = np.max(buildDemand)

    return Qmax
    

def readCombi(individual, gV):
    """
    Reads the 0-1 combination of connected/disconnected buildings
    and creates a lsit of strings type barcode i.e. ("12311111123012")
    
    Parameters
    ----------
    individual: list
    
    Returns
    -------
    indCombi : list of strings
    
    """
    irank = (gV.nHeat + gV.nSolar) * 2 + gV.nHR + 1
    frank = len(individual)
    indCombi = ""
    
    while irank < frank:

        indCombi += str(individual[irank])
        irank += 1
        
    return indCombi


def createTotalNtwCsv(indCombi, locator):
    """
    Create and saves the total file for a specific DHN configuration
    to make the network routine possible
    
    Parameters
    ----------
    indCombi : string
        string of 0 and 1: 0 of the building is disconnected, 1 if connected
    locator: string
        path to raw files
    pathTotalNtw :string
        path to were to store the csv Total file
    
    Returns
    -------
    fName_result : string
        name of the Total file
    
    """
    df = pd.read_csv(locator.get_total_demand())
    
    index = []
    rank = 0
    for el in indCombi:
        if el == "0":
            index.append(rank)
        rank += 1
    
    dfRes = df.drop(df.index[index])
    
    fName_result = "Total_" + indCombi + ".csv"
    dfRes.to_csv(locator.pathTotalNtw+'//'+fName_result, sep= ',')
    
    return dfRes
    

def readCheckPoint(pathX, genCP, storeData):
    """
    Extracts data from the checkpoints created in the master routine
    
    Parameters
    ----------
    pathMasterRes : string
        path to folder where CPs are stored
    genCP : int
        generation from whom to extract data
    pathNtwRes : string
        path to folder where the files from the network routine are stored
    storeData : int
        0 if no, 1 if yes
    
    Returns
    -------
    pop : list
        list of individuals in the Pareto front at that generation
    eps : list
        UN-NORMALIZED epsilon indicator from the beginning of the EA to this
        generation
    testedPop : list
        list of individuals tested in that generation
    
    """    
    os.chdir(pathX.pathMasterRes)

    # Set the DEAP toolbox
    creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0, -1.0))
    # Contains 3 Fitnesses : Costs, CO2 emissions, Primary Energy Needs
    creator.create("Individual", list, fitness=creator.Fitness)

    with open("CheckPoint" + str(genCP),"rb") as CPread:
        CPunpick = Unpickler(CPread)
        cp = CPunpick.load()
        pop = cp["population"]
        eps = cp["epsIndicator"]
        testedPop = cp["testedPop"]

    if storeData == 1:
        data_container = [['Cost', 'CO2', 'Eprim_i','Qmax', 'key']]
        #frame = pd.DataFrame()
        ind_counter = 0
        for ind in pop:
            
            a = [ind.fitness.values]
            CO2      = [int(i[0]) for i in a]
            cost     = [int(i[1]) for i in a]
            Eprim    = [int(i[2]) for i in a]
            
            key = pop[ind_counter]
            
            indCombi = readCombi(ind)

            if indCombi.count("0") == 0:
                fNameNtw = "Network_summary_result_all.csv"
            else:
                fNameNtw = "Network_summary_result_" + indCombi + ".csv"
            
            Qmax = calcQmax(fNameNtw, pathX.pathNtwRes)
            print fNameNtw
            #print indCombi
            print Qmax
            
            features = [CO2[:], cost[:], Eprim[:], Qmax, key]
            data_container.append(features)
            ind_counter += 1
        results = pd.DataFrame(data_container)
        Name = pathX.pathMasterRes + "/ParetoValuesAndKeysGeneration" + genCP+".csv"
        results.to_csv(Name, sep= ',')

    return pop, eps, testedPop


class solarFeatures(object):
    def __init__(self):
        self.SolarArea = 35710     # [m2]
        
        self.PV_Peak = 5680.8      # [kW_el]
        self.PVT_Peak = 849        # [kW_el]
        self.PVT_Qnom = 24512E3    # [W_th]
        self.SC_Qnom = 17359E3   # [W_th]
            
            
def solarRead(locator, gV):
    """
    Extract the appropriate solar features
    
    Parameters
    ----------
    locator : string
        path to raw solar files
    
    Returns
    -------
    solarFeat : solarFeatures
        includes : the total solar area
        the PV electrical peak production [kW]
        the PVT electrical peak production [kW]
        the PVT heating peak production [Wth]
        the SC heating peak production [Wth]
    
    """
    solarFeat = solarFeatures()
    
    PVarray = extractDemand(locator.pathSolarRaw + "/Pv.csv", ["PV_kWh"], gV.DAYS_IN_YEAR)
    solarFeat.PV_Peak = np.amax(PVarray)

    PVarray = extractDemand(locator.pathSolarRaw + "/Pv.csv", ["Area"], gV.DAYS_IN_YEAR)
    solarFeat.SolarAreaPV = PVarray[0][0]
    
    PVTarray = extractDemand(locator.pathSolarRaw + "/PVT_35.csv", ["PV_kWh"], gV.DAYS_IN_YEAR)
    solarFeat.PVT_Peak = np.amax(PVTarray)

    PVTarray = extractDemand(locator.pathSolarRaw + "/PVT_35.csv", ["Qsc_KWh"], gV.DAYS_IN_YEAR)
    solarFeat.PVT_Qnom = np.amax(PVTarray) * 1000

    PVTarray = extractDemand(locator.pathSolarRaw + "/PVT_35.csv", ["Area"], gV.DAYS_IN_YEAR)
    solarFeat.SolarAreaPVT = PVTarray[0][0]
    
    SCarray = extractDemand(locator.pathSolarRaw + "/SC_75.csv", ["Qsc_Kw"], gV.DAYS_IN_YEAR)
    solarFeat.SC_Qnom = np.amax(SCarray) * 1000

    SCarray = extractDemand(locator.pathSolarRaw + "/SC_75.csv", ["Area"], gV.DAYS_IN_YEAR)
    solarFeat.SolarAreaSC = SCarray[0][0]
    
    return solarFeat


def calc_num_buildings(data_path, totalfilename):
    number = pd.read_csv(data_path+'//'+totalfilename, usecols=['Name']).Name.count()
    return number