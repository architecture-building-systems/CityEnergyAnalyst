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
import json
import math
from cea.optimization.constants import *



def extract_building_names_from_csv(path_to_csv):
    """
    Extract the names of the buildings in the area

    :param path_to_csv: csv file with the names of the buildings
    :type path_to_csv: string

    :returns: building_names, list of strings with the names of the buildings
    :rtype: list
    """
    df = pd.read_csv(path_to_csv, usecols=["Name"])
    building_names = df['Name'].values.tolist()

    return building_names


def extractDemand(fName, colNameList, nDay):
    """
    Extract data from the columns of a csv file to an array.
    WARNING : the order of the columns in the array are the SAME as in the
    original file and NOT the order in the colNameList

    :param fName: name of the csv file
    :type fName: list of the columns name from which the data  needs to be extracted

    :return: np.array
    :rtype: class
    """
    df = pd.read_csv(fName, usecols=colNameList, nrows=24*nDay)
    result = np.array(df)

    return result


def calcQmax(file_name, path, gV):
    """
    Calculates the peak heating power in fName file
    
    :param file_name: name of the csv file
    :param path: path to the file
    :param gV: global variables
    :type file_name: string
    :type path: string
    :type gV: class

    :return: Qmax: maximum heating power [W]
    :rtype: float
    """    
    Q_DHNf_W = pd.read_csv(os.path.join(path, file_name), usecols=["Q_DHNf_W"]).values
    Qmax = Q_DHNf_W.max()

    return Qmax
    

def individual_to_barcode(individual):
    """
    Reads the 0-1 combination of connected/disconnected buildings
    and creates a list of strings type barcode i.e. ("12311111123012")
    
    :param individual: list containing the combination of connected/disconnected buildings
    :param gV: global variables
    :type individual: list
    :type gV: class

    :return: indCombi: list of strings
    :rtype: list
    """
    irank = nHeat * 2 + nHR + nSolar * 2 + 1 + 2 + nCool * 2 + 2
    frank = len(individual)
    DHN_barcode = ""
    DCN_barcode = ""

    for i in range(irank, irank + int((frank - irank)/2)):
        DHN_barcode += str(individual[i])

    for j in range(irank + int((frank - irank)/2), frank):
        DCN_barcode += str(individual[j])

        
    return DHN_barcode, DCN_barcode


def createTotalNtwCsv(indCombi, locator):
    """
    Create and saves the total file for a specific DHN configuration
    to make the distribution routine possible
    
    :param indCombi: string of 0 and 1: 0 if the building is disconnected, 1 if connected
    :param locator: path to raw files
    :type indCombi: string
    :type locator: string

    :return: name of the total file
    :rtype: string
    """
    df = pd.read_csv(locator.get_total_demand())
    
    index = []
    rank = 0
    for el in indCombi:
        if el == "0":
            index.append(rank)
        rank += 1
    
    dfRes = df.drop(df.index[index])
    dfRes.to_csv(locator.get_optimization_network_totals_folder_total(indCombi), sep=',')
    return dfRes
    

def readCheckPoint(locator, genCP, storeData):
    """
    Extracts data from the checkpoints created in the master routine
    
    :param locator: InputLocator set to scenario
    :param genCP: generation from whom to extract data
    :param storeData: 0 if no, 1 if yes
    :type locator: cea.inputlocator.InputLocator
    :type genCP: int
    :type storeData: int

    :returns: pop : list of individuals in the Pareto front at that generation
             eps : UN-NORMALIZED epsilon indicator from the beginning of the
             master to this generation
             testedPop : list of individuals tested in that generation
    :rtype: list, list, list
    """    
    os.chdir(locator.get_optimization_master_results_folder())

    # Set the DEAP toolbox
    creator.create("Fitness", base.Fitness, weights=(-1.0, -1.0, -1.0))
    # Contains 3 Fitnesses : Costs, CO2 emissions, Primary Energy Needs
    creator.create("Individual", list, fitness=creator.Fitness)

    with open("CheckPoint" + str(genCP),"rb") as fp:
        cp = json.load(fp)
        pop = cp["population"]
        eps = cp["epsIndicator"]
        ntwList = cp["networkList"]
        testedPop = cp["testedPop"]
        fitness = cp["population_fitness"]

    if storeData == 1:
        data_container = [['Cost', 'CO2', 'Eprim_i', 'Qmax', 'key']]
        ind_counter = 0
        for ind in pop:
            # FIXME: possibly refactor a: inline, also, this construction is weird...
            a = [ind.fitness.values]
            CO2 = [int(i[0]) for i in a]
            cost = [int(i[1]) for i in a]
            Eprim = [int(i[2]) for i in a]
            
            key = pop[ind_counter]
            
            indCombi = individual_to_barcode(ind)

            if indCombi.count("0") == 0:
                fNameNtw = "Network_summary_result_all.csv"
            else:
                fNameNtw = "Network_summary_result_" + indCombi + ".csv"
            
            Qmax = calcQmax(fNameNtw, locator.get_optimization_network_results_folder())
            print fNameNtw
            #print indCombi
            print Qmax
            
            features = [CO2[:], cost[:], Eprim[:], Qmax, key]
            data_container.append(features)
            ind_counter += 1
        results = pd.DataFrame(data_container)
        pareto_results_file = os.path.join(locator.get_optimization_master_results_folder(),
                                           "ParetoValuesAndKeysGeneration%(genCP)s.csv" % locals())
        results.to_csv(pareto_results_file, sep=',')

    return pop, eps, testedPop, ntwList, fitness


def calc_num_buildings(data_path, totalfilename):
    """
    :param data_path: path name
    :param totalfilename: path name
    :type data_path: string
    :type totalfilename: string
    :return: number
    :rtype: float
    """
    number = pd.read_csv(data_path+'//'+totalfilename, usecols=['Name']).Name.count()
    return number