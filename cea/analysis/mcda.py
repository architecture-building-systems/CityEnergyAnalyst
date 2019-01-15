"""
Post-processing: MCDA
"""
from __future__ import division

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

import cea.globalvar
import cea.optimization.supportFn as sFn
import deap
import pickle

class mcda_criteria(object):
    def __init__(self):
        
        # Weights wrt the three sustainable pillars Economics / Environment / Social
        self.wEco = 1/3
        self.wEnv = 1/3
        self.wSocial = 1 - self.wEnv - self.wEco
        
        # Eco
        self.wCosts = 0.5  #0.5
        self.wOpCosts = 1 - self.wCosts
        
        # Environment
        self.wCO2 = 0.5
        self.wPrim = 1 - self.wCO2
        
        # Social
        self.wLocal = 1
    

def mcda_indicators(individual, locator, plot = 0):
    """
    Computes the specific operational costs and the share of local resources
    
    """
    configKey = "".join(str(e)[0:4] for e in individual)
    print configKey
    buildList = sFn.extract_building_names_from_csv(locator.pathRaw + "/Total.csv")
    gv = cea.globalvar.GlobalVariables()
    
    # Recover data from the PP activation file
    resourcesFile = os.path.join(locator.get_optimization_slave_results_folder(), "%(configKey)sPPActivationPattern.csv" % locals())
    resourcesdf = pd.read_csv(resourcesFile, usecols=["ESolarProducedPVandPVT", "Q_AddBoiler", "Q_BoilerBase", "Q_BoilerPeak", "Q_CC", "Q_GHP", \
                                                        "Q_HPLake", "Q_HPSew", "Q_primaryAddBackupSum", "Q_uncontrollable"])
                                                        
    Electricity_Solar = resourcesdf.ESolarProducedPVandPVT.sum()
    Q_AddBoiler = resourcesdf.Q_AddBoiler.sum()
    Q_BoilerBase = resourcesdf.Q_BoilerBase.sum()
    Q_BoilerPeak = resourcesdf.Q_BoilerPeak.sum()
    Q_CC = resourcesdf.Q_CC.sum()
    Q_GHP = resourcesdf.Q_GHP.sum()
    Q_HPLake = resourcesdf.Q_HPLake.sum()
    Q_HPSew = resourcesdf.Q_HPSew.sum()
    Q_storage_missmatch = resourcesdf.Q_primaryAddBackupSum.sum()
    Q_uncontrollable = resourcesdf.Q_uncontrollable.sum()

    # Recover data from the Storage Operation file
    resourcesFile = os.path.join(locator.get_optimization_slave_results_folder(),
                                 "%(configKey)sStorageOperationData.csv" % locals())
    resourcesdf = pd.read_csv(resourcesFile, usecols=["Q_SCandPVT_coldstream"])
    Q_fromSolar = resourcesdf.Q_SCandPVT_coldstream.sum()


    # Recover heating needs for decentralized buildings
    indCombi = sFn.individual_to_barcode(individual, gv)
    QfromNG = 0
    QfromBG = 0
    QfromGHP = 0
    
    for i in range(len(indCombi)):
        if indCombi[i] == "0": # Decentralized building
            building_name = buildList[i]
            df = pd.read_csv(locator.get_optimization_decentralized_result_file(building_name))
            dfBest = df[ df["Best configuration"] == 1 ]
               
            QfromNG += dfBest["QfromNG"].iloc[0]
            QfromBG += dfBest["QfromBG"].iloc[0]
            QfromGHP += dfBest["QfromGHP"].iloc[0]

    # Recover electricity and cooling needs
    totalFile = locator.pathRaw + "/Total.csv"
    df = pd.read_csv(totalFile, usecols=["Ealf", "Eauxf", "Ecaf", "Edataf", "Epf"])
    arrayTotal = np.array(df)
    totalElec = np.sum(arrayTotal) * 1E6 # [Wh]

    df = pd.read_csv(totalFile, usecols=["Qcdataf", "Qcicef", "Qcpf", "Qcsf"])
    arrayTotal = np.array(df)
    if individual[12] == 0:
        totalCool = ( np.sum((arrayTotal)[:,:-1]) + np.sum((arrayTotal)[:,-1:]) * (1+gv.DCNetworkLoss) ) * 1E6 # [Wh]
    else:
        totalCool = ( np.sum((arrayTotal)[:,1:-1]) + np.sum((arrayTotal)[:,-1:]) * (1+gv.DCNetworkLoss) ) * 1E6 # [Wh]
    
    
    # Computes the specific operational costs
    totalEnergy = Q_AddBoiler + Q_BoilerBase + Q_BoilerPeak + Q_CC + Q_GHP + Q_HPLake + \
                  Q_HPSew  + Q_uncontrollable + totalElec + totalCool + \
                  QfromNG + QfromBG + QfromGHP# + Q_storage_missmatch
                  
    shareCC_NG = individual[0] % 2 * Q_CC / totalEnergy
    shareCC_BG = ( individual[0] + 1 ) % 2 * Q_CC / totalEnergy
    shareBB_NG = individual[2] % 2 * Q_BoilerBase / totalEnergy
    shareBB_BG = ( individual[2] + 1 ) % 2 * Q_BoilerBase / totalEnergy
    shareBP_NG = individual[4] % 2 * Q_BoilerPeak / totalEnergy
    shareBP_BG = ( individual[4] + 1 ) % 2 * Q_BoilerPeak / totalEnergy
    shareHPLake = Q_HPLake / totalEnergy
    shareHPSew = Q_HPSew / totalEnergy
    shareGHP = Q_GHP / totalEnergy
    shareExtraNG = (Q_AddBoiler + Q_storage_missmatch) / totalEnergy
    shareHR = (Q_uncontrollable - Q_fromSolar) / totalEnergy
    shareHeatSolar = Q_fromSolar / totalEnergy
    shareDecentralizedNG = QfromNG / totalEnergy
    shareDecentralizedBG = QfromBG / totalEnergy
    shareDecentralizedGHP = QfromGHP / totalEnergy
    shareElecGrid = (totalElec - Electricity_Solar) / totalEnergy
    shareElecSolar = Electricity_Solar / totalEnergy
    shareCoolLake = totalCool / totalEnergy
    
    printout = 1
    if printout:
        print 'CC_NG', individual[0] % 2 * Q_CC
        print 'CC_BG', ( individual[0] + 1 ) % 2 * Q_CC
        print 'BB_NG', individual[2] % 2 * Q_BoilerBase
        print 'BB_BG', ( individual[2] + 1 ) % 2 * Q_BoilerBase
        print 'BP_NG', individual[4] % 2 * Q_BoilerPeak
        print 'BP_BG', ( individual[4] + 1 ) % 2 * Q_BoilerPeak
        print 'HPLake', Q_HPLake
        print 'HPSew', Q_HPSew
        print 'GHP', Q_GHP
        print 'ExtraNG', (Q_AddBoiler + Q_storage_missmatch)
        print 'HR', (Q_uncontrollable - Q_fromSolar)
        print 'HeatSolar', Q_fromSolar
        print 'DecentralizedNG', QfromNG
        print 'DecentralizedBG', QfromBG
        print 'DecentralizedGHP', QfromGHP
        print 'ElecGrid', (totalElec - Electricity_Solar)
        print 'ElecSolar', Electricity_Solar
        print 'CoolLake', totalCool

        print 'shareCC_NG', shareCC_NG*100 
        print 'shareCC_BG', shareCC_BG*100
        print 'shareBB_NG', shareBB_NG*100
        print 'shareBB_BG',  shareBB_BG*100
        print 'shareBP_NG', shareBP_NG*100
        print 'shareBP_BG', shareBP_BG*100 
        print 'shareHPLake', shareHPLake*100 
        print 'shareHPSew', shareHPSew*100 
        print 'shareGHP', shareGHP*100 
        print 'shareExtraNG', shareExtraNG*100 
        print 'shareHR', shareHR*100
        print 'shareHeatSolar', shareHeatSolar*100
        print 'shareDecentralizedNG', shareDecentralizedNG*100
        print 'shareDecentralizedBG', shareDecentralizedBG*100 
        print 'shareDecentralizedGHP', shareDecentralizedGHP*100
        print 'shareElecGrid' ,shareElecGrid*100 
        print 'shareElecSolar', shareElecSolar*100 
        print 'shareCoolLake', shareCoolLake*100

    specificCosts = gv.ELEC_PRICE * shareElecGrid + \
                    gv.NG_PRICE * (shareCC_NG + shareBB_NG + shareBP_NG + shareExtraNG + shareDecentralizedNG) + \
                    gv.BG_PRICE * (shareCC_BG + shareBB_BG + shareBP_BG + shareDecentralizedBG)
    
    # Computes the share of local resources
    shareLocal = shareHPLake + shareHPSew + shareGHP + shareHR + shareHeatSolar + shareDecentralizedGHP + shareElecSolar + shareCoolLake
    
    # Plots the pie chart for energy resources use
    if plot == 1:
        fig = plt.figure()
        subplot = fig.add_subplot(111, adjustable = 'box', aspect = 1, title = 'Energy mix')
        
        labels = ['Lake', 'Solar', 'HR', 'Ground', 'Gas', 'Grid']
        shareLake = shareHPLake + shareCoolLake
        shareSolar = shareHeatSolar + shareElecSolar
        shareHRAll = shareHPSew + shareHR
        shareGround = shareGHP + shareDecentralizedGHP
        shareGas = 1 - shareLake - shareSolar - shareHRAll - shareGround - shareElecGrid
        
        fracs = [ shareLake, shareSolar, shareHRAll, shareGround, shareGas, shareElecGrid ]
        colors = ['RoyalBlue', 'Gold', 'LightGreen', 'SandyBrown', 'OrangeRed', 'Gray']
        
        zipper = [ (l,f,c) for (l,f,c) in zip(labels,fracs,colors) if f > 0.001 ]
        labelsPlot, fracsPlot, colorsPlot = map( list, zip(*zipper) )
        subplot.pie(fracsPlot, labels = labelsPlot, colors = colorsPlot, startangle = 90, autopct='%1.1f%%', pctdistance = 0.65)
        
        plt.show()
    
    return specificCosts, shareLocal
    


def mcda_analysis(pop, setWeights, pathX):
    nCriteria = 5
    nPop = len(pop)
    
    normArray = np.zeros((nPop, nCriteria))
    scoreArray = np.zeros(nPop)
    
    # Computes the specific costs and share of local resources for all individual
    extraIndicators = np.zeros((nPop, 2))
    index = 0
    for ind in pop:
        specificCosts, shareLocal = mcda_indicators(ind, pathX, plot = 0)
        #extraIndicators[index][0] = specificCosts
        extraIndicators[index][1] = shareLocal
        index += 1
    
    # Computes the better / worst
    betterWorstArray = np.zeros((2, nCriteria))
        
    betterWorstArray[0][0] = min ( [costs for (costs, CO2, prim) in [ind.fitness.values for ind in pop] ] )
    betterWorstArray[1][0] = max ( [costs for (costs, CO2, prim) in [ind.fitness.values for ind in pop] ] )
    
    betterWorstArray[0][1] = min ( [CO2 for (costs, CO2, prim) in [ind.fitness.values for ind in pop] ] )
    betterWorstArray[1][1] = max ( [CO2 for (costs, CO2, prim) in [ind.fitness.values for ind in pop] ] )
    
    betterWorstArray[0][2] = min ( [prim for (costs, CO2, prim) in [ind.fitness.values for ind in pop] ] )
    betterWorstArray[1][2] = max ( [prim for (costs, CO2, prim) in [ind.fitness.values for ind in pop] ] )
    
    #betterWorstArray[0][3] = min ( extraIndicators[:,0] )
    #betterWorstArray[1][3] = max ( extraIndicators[:,0] )
    
    betterWorstArray[0][4] = max ( extraIndicators[:,1] )
    betterWorstArray[1][4] = min ( extraIndicators[:,1] )
    
    # Computes the normalized score
    for objective in range(3):
        for i in range(nPop):
            ind = pop[i]
            normArray[i][objective] = (betterWorstArray[1][objective] - ind.fitness.values[objective]) / (betterWorstArray[1][objective] - betterWorstArray[0][objective])
    for objective in range(2):
        for i in range(nPop):
            ind = pop[i]
            normArray[i][3+objective] = (betterWorstArray[1][3+objective] - extraIndicators[i][objective]) / (betterWorstArray[1][3+objective] - betterWorstArray[0][3+objective])

    for i in range(nPop):
        scoreArray[i] = normArray[i][0] * setWeights.wCosts * setWeights.wEco \
                        + normArray[i][1] * setWeights.wCO2 * setWeights.wEnv \
                        + normArray[i][2] * setWeights.wPrim * setWeights.wEnv \
                        + normArray[i][4] * setWeights.wLocal * setWeights.wSocial
                        #+ normArray[i][3] * setWeights.wOpCosts * setWeights.wEco \
    
    bestInd = pop[0]
    currentScore = scoreArray[0]
    indexBest = 0
    for i in range(nPop):
        if scoreArray[i] > currentScore:
            currentScore = scoreArray[i]
            bestInd = pop[i] 
            indexBest = i   
    
    scoreBest = pop[indexBest].fitness.values[0], \
                extraIndicators[indexBest][0], \
                pop[indexBest].fitness.values[1], \
                pop[indexBest].fitness.values[2], \
                extraIndicators[indexBest][1]
    
    return scoreArray, bestInd, indexBest, scoreBest



def mcda_differentWeights(pop, pathX):
    setWeights = mcda_criteria()
    
    # Balanced weights : 1/3-1/3-1/3
    scoreArray, bestInd, indexBestOriginal, scoreBest = mcda_analysis(pop, setWeights, pathX)
    
    # More weight on the economy : 0.7-0.15-0.15
    setWeights.wEco = 0.8
    setWeights.wEnv = 0.1
    setWeights.wSocial = 0.1
    scoreArray, bestInd, indexBestEco, scoreBest = mcda_analysis(pop, setWeights, pathX)

    # More weight on the environment : 0.15-0.7-0.15
    setWeights.wEco = 0.1
    setWeights.wEnv = 0.8
    setWeights.wSocial = 0.1
    scoreArray, bestInd, indexBestEnv, scoreBest = mcda_analysis(pop, setWeights, pathX)

    # More weight on the society : 0.15-0.15-0.7
    setWeights.wEco = 0.1
    setWeights.wEnv = 0.1
    setWeights.wSocial = 0.8
    scoreArray, bestInd, indexBestSoc, scoreBest = mcda_analysis(pop, setWeights, pathX)
    
    return [indexBestOriginal, indexBestEco, indexBestEnv, indexBestSoc]


def mcda_cluster_main(input_path, what_to_plot, weight_fitness1, weight_fitness2, weight_fitness3):

    #get modules to read pickle file
    deap.creator.create("Fitness", deap.base.Fitness, weights=(1.0, 1.0, 1.0))
    deap.creator.create("Individual", list, fitness=deap.creator.Fitness)

    #read data form pickle file:
    cp = pickle.load(open(input_path, "rb"))
    frontier = cp[what_to_plot]
    individuals = [str(ind) for ind in frontier]
    fitness1, fitness2, fitness3 = map(np.array, zip(*[ind.fitness.values for ind in frontier]))

    #normalizaiton of weights
    total_weights = weight_fitness1 + weight_fitness2 + weight_fitness3
    w1 = weight_fitness1 / total_weights * 100
    w2 = weight_fitness2 / total_weights * 100
    w3 = weight_fitness3 / total_weights * 100

    #normalization of data
    f1_min = min(fitness1)
    f1_max = max(fitness1)
    f1 = np.array([(value-f1_min)/(f1_max-f1_min) if (f1_max-f1_min) else value for value in fitness1])
    f2_min = min(fitness2)
    f2_max = max(fitness2)
    f2 = np.array([(value-f2_min)/(f2_max-f2_min) if (f1_max-f1_min) else value for value in fitness2])
    f3_min = min(fitness3)
    f3_max = max(fitness3)
    f3 = np.array([(value-f3_min)/(f3_max-f3_min) if (f3_max-f3_min) else value for value in fitness3])

    #calculate MCDA score
    global_value = f1 * w1 + f2 * w2 + f3 * w3

    #computation of global value
    data = pd.DataFrame({"Global_value": global_value,
                         "Individual": individuals, "fitness1": fitness1, "fitness2": fitness2,
                         "fitness3": fitness3})

    index_best = data["Global_value"].argmax()
    result = data.ix[index_best]
    return result
