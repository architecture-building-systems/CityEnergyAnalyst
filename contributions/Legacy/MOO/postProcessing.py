"""
=========================
Post-processing: Plotting
=========================

"""
from __future__ import division
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pylab import *
import supportFn as sFn


def configDesign(pop, indIndex):
    ind = pop[indIndex]
    fig = plt.figure(figsize=(6,4))
    fig.suptitle('Design of the centralized heating hub')
    
    # Central heating plant
    subplot1 = fig.add_subplot(221, adjustable = 'box', aspect = 1)
    
    def NGorBG(value):
        if value%2 == 1:
            gas = 'NG'
        else:
            gas = 'BG'
        return gas
    
    labels = ['CC '+NGorBG(ind[0]), 'Boiler Base '+NGorBG(ind[2]), 'Boiler peak '+NGorBG(ind[4]), 'HP Lake', 'HP Sew', 'GHP']
    fracs = [ ind[2*i + 1] for i in range(6) ]
    colors = ['LimeGreen', 'LightSalmon', 'Crimson', 'RoyalBlue', 'MidnightBlue', 'Gray']
    
    zipper = [ (l,f,c) for (l,f,c) in zip(labels,fracs,colors) if f > 0.01 ]
    labelsPlot, fracsPlot, colorsPlot = map( list, zip(*zipper) )
    subplot1.pie(fracsPlot, labels = labelsPlot, colors = colorsPlot, startangle = 90, autopct='%1.1f%%', pctdistance = 0.5)

    # Solar total area
    subplot2 = fig.add_subplot(222, adjustable = 'box', aspect = 1)
    labels = ['Solar covered area', 'Uncovered area']
    fracs = [ ind[20], 1 - ind[20] ]
    colors = ['Gold', 'Gray']
    subplot2.pie(fracs, labels = labels, startangle = 90, colors = colors, autopct='%1.1f%%', pctdistance = 0.5)
    
    # Solar system distribution
    subplot3 = fig.add_subplot(223, adjustable = 'box', aspect = 1)
    labels = ['PV', 'PVT', 'SC']
    fracs = [ ind[15], ind[17], ind[19] ]
    colors = ['Yellow', 'Orange', 'OrangeRed']
    
    zipper = [ (l,f,c) for (l,f,c) in zip(labels,fracs,colors) if f > 0.01 ]
    labelsPlot, fracsPlot, colorsPlot = map( list, zip(*zipper) )
    subplot3.pie(fracsPlot, labels = labelsPlot, colors = colorsPlot, startangle = 90, autopct='%1.1f%%', pctdistance = 0.5)
    
    # Connected buildings
    connectedBuild = ind[21:].count(1) / len(ind[21:])
    subplot4 = fig.add_subplot(224, adjustable = 'box', aspect = 1)
    labels = ['Connected buildings', 'Disconnected buildings',]
    fracs = [ connectedBuild, 1 - connectedBuild]
    colors = ['Chocolate', 'Gray']
    subplot4.pie(fracs, labels = labels, startangle = 90, colors = colors, autopct='%1.1f%%', pctdistance = 0.5)
    plt.rcParams.update({'font.size':10})
    plt.show()
    

def compareRef(indRef, pop, listIndex):
    
    costRef = indRef.fitness.values[0]
    CO2Ref = indRef.fitness.values[1]
    primRef = indRef.fitness.values[2]
    
    costChanges = [ 100 * (pop[i].fitness.values[0] - costRef) / costRef for i in listIndex ]
    CO2Changes = [ 100 * (pop[i].fitness.values[1] - CO2Ref) / CO2Ref for i in listIndex ]
    primChanges = [ 100 * (pop[i].fitness.values[2] - primRef) / primRef for i in listIndex ]
    
    N = len(listIndex)    
    ind = np.arange(N)  # the x locations for the groups
    width = 1/4       # the width of the bars
    
    fig, ax = plt.subplots(figsize=(6,4))
    axis = ax.bar(0,0,N)
    rects1 = ax.bar(ind, costChanges, width, color='LightBlue')
    rects2 = ax.bar(ind+width, CO2Changes, width, color='LimeGreen')
    rects3 = ax.bar(ind+ 2*width, primChanges, width, color='Gray')
    
    # add some text for labels, title and axes ticks
    ax.set_ylabel('Relative savings [%]')
    ax.set_xticks(ind+ 3/2*width)
    
    if len(listIndex) == 4:
        typeList = ['Balanced', 'Focus Economy', 'Focus Environment', 'Focus Social']
        indList = [ '(Ind ' + str(i) + ')' for i in listIndex ]
        labelList = [ typeList[i] + indList[i] for i in range(4) ]
    else:
        labelList = ['Ind '+str(i) for i in listIndex]
    ax.set_xticklabels( labelList )
    
    ax.legend( (rects1[0], rects2[0], rects3[0]), ('TAC', 'CO2', 'PEN') )
    
    def autolabel(rects, values):
        # attach some text labels
        for rect, value in zip(rects,values):
            ax.text(rect.get_x()+rect.get_width()/2., 1.2, '%d%%'%int(value),
                    ha='center', va='bottom')
    
    autolabel(rects1, costChanges)
    autolabel(rects2, CO2Changes)
    autolabel(rects3, primChanges)
    plt.rcParams.update({'font.size':15})
    plt.show()


def buildingConnection(generation, pathX):
    BuildCon = []
    nInd = []
    
    for i in range(generation):
        i += 1
        pop, eps, testedPop = sFn.readCheckPoint(pathX, i, 0)
        buildCon = []
        
        for ind in pop:
            buildCon.append(np.average(ind[21:]))
            
        BuildCon.append(np.average(buildCon))
        nInd.append(len(pop))
    
    # Plotting the number of connected buildings vs the generations
    fig = plt.figure()
    ax = fig.add_subplot(111, xlim = (1,generation), ylim = (0.1))
    xList = [ 1 + x for x in range(len(BuildCon)) ]
    ax.plot(xList, BuildCon)
    ax.set_xlim(1,generation)
    ax.set_ylabel('Averaged building connection')
    ax.set_xlabel('Generation')
    ax.set_xticks(np.arange(1,generation+1,2))
    plt.show()
    
    # Plotting the number of individuals vs the generations
    fig = plt.figure()    
    ax = fig.add_subplot(111, xlim = (1,generation))
    xList = [ 1 + x for x in range(len(nInd)) ]
    ax.plot(xList, nInd)
    ax.set_xlim(1,generation)
    ax.set_ylabel('Number of individuals in the Pareto front')
    ax.set_xlabel('Generation')
    ax.set_xticks(np.arange(1,generation+1,2))
    plt.show()

    return BuildCon, nInd


def Elec_ImportExport(individual, pathX):
    
    # Extract Electricity needs
    buildList = sFn.extractList(pathX.pathRaw + "/Total.csv")

    allElec = np.zeros((8760,1))
    
    for build in buildList:
        buildFileRaw = pathX.pathRaw + "/" + build + ".csv"
        builddf = pd.read_csv(buildFileRaw, usecols = ["Ealf", "Eauxf", "Ecaf", "Edataf", "Epf"])
        buildarray = np.array(builddf)
        
        for i in range(8760):
            allElec[i,0] += np.sum(buildarray[i,:])*1000
    print sum(allElec)
        
    # Extract electricity produced form solar
    configKey = "".join(str(e)[0:4] for e in individual)
    PPactivationFile = pathX.pathSlaveRes + '/' + configKey + 'PPActivationPattern.csv'
    ESolardf = pd.read_csv(PPactivationFile, usecols = ['ESolarProducedPVandPVT'])
    EsolarArray = np.array(ESolardf)
    
    # Compute Import / Export
    imp = 0
    exp = 0
    for i in range(8760):
        delta = allElec[i,0] - EsolarArray[i,0]
        if delta > 0:
            imp += delta
        else:
            exp += delta
    
    return imp,exp


def decentralizeCosts(individual, pathX, gV):
    indCombi = sFn.readCombi(individual, gV)
    buildList = sFn.extractList(pathX.pathRaw + "/Total.csv")
    costsDisc = 0
    
    for i in range(len(indCombi)):
        if indCombi[i] == "0": # Decentralized building
            buildName = buildList[i]
            DecentFile = pathX.pathDiscRes + "/DiscOp_" + buildName + "_result.csv"
    
            df = pd.read_csv(DecentFile)
            dfBest = df[df["Best configuration"] == 1]
            
            costsDisc += dfBest["Annualized Investment Costs [CHF]"].iloc[0]
    
    print costsDisc, "costsDisc"
    return costsDisc

def connectedbuildings(pop,IndexBest):
    con = pop[IndexBest][21:]
    percentage = sum(con)/len(con)
    print con,percentage
