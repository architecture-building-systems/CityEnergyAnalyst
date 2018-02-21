# -*- coding: utf-8 -*-
"""
=========================================
plot results of optimization
=========================================
"""

from __future__ import division

import os

import matplotlib
import matplotlib.cm as cmx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import cea.optimization.master.normalization as norm
import cea.optimization.supportFn as sFn

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

reload(norm)
reload(sFn)

"""
=========================================
plot results of multicriteria comparing all scenarios
=========================================
"""

def plot_multicriteria_scenarios(indRef, SQ_area, pop, pathX, listIndex, savelocation, type_analysis):

    if type_analysis == "inter":
        Area_buildings = pd.read_csv(pathX.pathRaw+'//'+'Total.csv',usecols=['Af']).values.sum()        
        costRef = indRef[0]/SQ_area
        CO2Ref = indRef[1]/SQ_area
        primRef = indRef[2]/SQ_area
        costChanges = [ 100 * ((pop[i].fitness.values[0]/Area_buildings) - costRef) / costRef for i in listIndex ]
        CO2Changes = [ 100 * ((pop[i].fitness.values[1]/Area_buildings) - CO2Ref) / CO2Ref for i in listIndex ]
        primChanges = [ 100 * ((pop[i].fitness.values[2]/Area_buildings) - primRef) / primRef for i in listIndex ]
    else:  
        costRef = indRef.fitness.values[0]
        CO2Ref = indRef.fitness.values[1]
        primRef = indRef.fitness.values[2]
        costChanges = [ 100 * (pop[i].fitness.values[0] - costRef) / costRef for i in listIndex ]
        CO2Changes = [ 100 * (pop[i].fitness.values[1] - CO2Ref) / CO2Ref for i in listIndex ]
        primChanges = [ 100 * (pop[i].fitness.values[2] - primRef) / primRef for i in listIndex ]
    
    N = len(listIndex)    
    ind = np.arange(N)  # the x locations for the groups
    width = 0.25     # the width of the bars
    
    fig, ax = plt.subplots(figsize=(12,4))
    axis = ax.bar(0,0,N)
    rects1 = ax.bar(ind, costChanges, width, color='b')
    rects2 = ax.bar(ind+width, CO2Changes, width, color='grey')
    rects3 = ax.bar(ind+ 2*width, primChanges, width, color='red')
    
    # add some text for labels, title and axes ticks
    ax.set_ylabel('Relative savings [%]')
    ax.set_xticks(ind+ 1.5*width)
    
    if len(listIndex) == 4:
        typeList = ['Balanced', 'Economic', 'Environmental', 'Social']
        indList = [ '(Ind ' + str(i) + ')' for i in listIndex ]
        labelList = [ typeList[i] + indList[i] for i in range(4) ]
    else:
        labelList = ['Ind '+str(i) for i in listIndex]
    ax.set_xticklabels( labelList )
    
    ax.legend((rects1[0], rects2[0], rects3[0]), ('TAC', 'CO2', 'PEN'), 
                bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
                ncol=3, mode="expand", borderaxespad=-0.2,fontsize=16)
    
    def autolabel(rects, values):
        # attach some text labels
        for rect, value in zip(rects,values):
            ax.text(rect.get_x()+rect.get_width()/2., 1.2, '%d%%'%int(value),
                    ha='center', va='bottom')
    
    autolabel(rects1, costChanges)
    autolabel(rects2, CO2Changes)
    autolabel(rects3, primChanges)
    plt.rcParams['font.size'] = 16
    plt.savefig(savelocation+"MCDA_multiweights.png")
    plt.clf()


"""
=========================================
plot pareto curves comparing all scenarios
=========================================
"""

def plot_pareto_scenarios(locator, generations, relative):
    '''
    This function plots a pareto curve for a certan checkpoint number. The checkpoint number is equivalent
    to the Generation number to be mapped

    :param locator:
    :param generations:
    :param headers:
    :param relative:
    :param savelocation:
    :return:
    '''

    # create local variables
    xs =[]
    ys =[]
    zs =[]
    fig = plt.figure()
    savelocation = locator.get_plots_folder()

    # read the checkpoint
    counter = 0
    #for scenario in scenarios:
    pop, eps, testedPop, ntwList, fitness = sFn.readCheckPoint(locator, generations, 0)

    # get floor area of buildings and estimate relative parameters
    Area_buildings = pd.read_csv(locator.get_total_demand(),usecols=['Af_m2']).values.sum()
    [x, y, z] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    ax = fig.add_subplot(111)
    if relative == True:
        z[:] = [a / Area_buildings for a in z]
        x[:] = [b / Area_buildings for b in x]
        y[:] = [c / Area_buildings for c in y]
    xs.extend(x)
    ys.extend(y)
    zs.extend(z)
    counter +=1
        
    if relative == True:
        TAC = 'TAC [EU/m2.yr]'
        CO2 = 'CO2 [kg-CO2/m2.yr]'
        PEN = 'PEN [MJ/m2.yr]'
        ax.set_ylim([10,50])
        finallocation = os.path.join(savelocation, "pareto_m2.png")
    else:
        var = 1000000
        zs[:] = [x / var for x in zs]
        xs[:] = [x / var for x in xs]
        ys[:] = [x / var for x in ys]
        TAC = 'TAC [Mio EU/yr]'
        CO2 = 'CO2 [kton-CO2/yr]'
        PEN = 'PEN [TJ/yr]' 
        ax.set_xlim([2.5,7.0]) 
        finallocation = os.path.join(savelocation, "pareto.png")
               
    cm = plt.get_cmap('jet')
    cNorm = matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs))
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
    ax.scatter(xs, ys, c=scalarMap.to_rgba(zs), s=50, alpha =0.8)    
    ax.set_xlabel(TAC)
    ax.set_ylabel(CO2)
    

    scalarMap.set_array(zs)
    fig.colorbar(scalarMap, label=PEN)
    plt.grid(True)
    plt.rcParams['figure.figsize'] = (6,4)
    plt.rcParams.update({'font.size':12})
    plt.gcf().subplots_adjust(bottom=0.15)
    plt.savefig(finallocation)
    plt.clf()


"""
=========================================
plot epsilon indicator for each generation of the MOO and scenario
=========================================
"""


def plot_epsilon_scenarios(scenarios, generations, headers):
    colors = ['b','r','y','c']    
    fig = plt.figure()   
    counter = 0    
    for scenario in scenarios:
        epsNorm = norm.normalize_epsIndicator(sFn.pathX(headers[counter]), generations[counter])
        xList = [ 2 + x for x in range(len(epsNorm)) ]
        ax = fig.add_subplot(111)
        ax.plot(xList, epsNorm, colors[counter], label=scenario)
        ax.set_ylabel('Normalized epsilon indicator')
        ax.set_xlabel('Generation No.')
        plt.legend(scenarios, loc='upper right')
        plt.rcParams['figure.figsize'] = (6,4)
        plt.rcParams['font.size'] = 12
        counter +=1
    plt.show()


"""
=========================================
plot percentage of buildings connected to the grid for each generation of the MOO and scenario
=========================================
"""

def plot_buildings_connected_scenarios(scenarios, generations, headers):
    counter =0    
    data = [1,2,3,4]  
    colors = ['b','r','y','c']
    fig = plt.figure()
    for header in headers:
        pathX = sFn.pathX(header)
        BuildCon = []
        BuildCon2 = []
        for i in range(generations[counter]):
            i += 1
            pop, eps, testedPop, ntwList, fitness = sFn.readCheckPoint(pathX, i, 0)
            buildCon = []
            buildCon2 = []
            for ind in pop:
                buildCon.extend([np.average(ind[21:])*100])
                buildCon2.append([np.average(ind[21:])*100])
                
            BuildCon.extend(buildCon)
            BuildCon2.append(np.average(buildCon2))
            
        data[counter] = BuildCon
    
        # individual lines per generation
        xList = [ 1 + x for x in range(len(BuildCon2)) ]
        ax = fig.add_subplot(111)
        ax.plot(xList, BuildCon2, colors[counter], label=scenarios)
        ax.set_xlim(1,generations[counter])
        ax.set_ylabel('Percentage of buildings connected (%)')
        ax.set_xlabel('Generation No.')
        #ax.set_xticks(np.arange(1,generations[counter]+1,2))
        counter +=1
    plt.legend(scenarios, loc='upper left')        
    plt.rcParams['figure.figsize'] = (6,4)
    plt.rcParams['font.size'] = 12
    plt.show()
    
    # box plot with all data)
    fig = plt.figure(figsize = (6,4))
    plt.rcParams['font.size'] = 12
    plt.boxplot(data,1,'rs',0)  
    plt.yticks([1, 2, 3, 4], scenarios)
    plt.xlabel("Percentage of buildings connected (%)")
    plt.show()
    return data 

"""
=========================================
plot energy mix
=========================================
"""

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

"""
=========================================
number of buildings connected per scenario
=========================================
"""

def buildingConnection(generation, locator):
    BuildCon = []
    nInd = []

    for i in range(generation):
        i += 1
        pop, eps, testedPop, ntwList, fitness = sFn.readCheckPoint(locator, i, 0)
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

"""
=========================================
plot electricity imports and exports
=========================================
"""

def Elec_ImportExport(individual, locator):

    # Extract Electricity needs
    buildList = sFn.extract_building_names_from_csv(locator.pathRaw + "/Total.csv")

    allElec = np.zeros((8760,1))

    for build in buildList:
        buildFileRaw = locator.pathRaw + "/" + build + ".csv"
        builddf = pd.read_csv(buildFileRaw, usecols = ["Ealf", "Eauxf", "Ecaf", "Edataf", "Epf"])
        buildarray = np.array(builddf)

        for i in range(8760):
            allElec[i,0] += np.sum(buildarray[i,:])*1000
    print sum(allElec)

    # Extract electricity produced form solar
    configKey = "".join(str(e)[0:4] for e in individual)
    ESolardf = pd.read_csv(os.path.join(locator.get_optimization_slave_results_folder(),
                                        configKey + 'PPActivationPattern.csv'), usecols=['ESolarProducedPVandPVT'])
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



"""
=========================================
test
=========================================
"""

def test_graphs_optimization():
    import cea.globalvar
    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path=scenario_path)

    # define scenarios and headers
    scenarios = ['BAU', 'CAMP', 'HEB', 'UC']
    generation = 7
    # headers = ["/Volumes/SAMSUNG/paper 3/BAU/", "/Volumes/SAMSUNG/paper 3/CAMP/", "/Volumes/SAMSUNG/paper 3/HEB/", "/Volumes/SAMSUNG/paper 3/UC/"]
    # savelocation = "/Volumes/SAMSUNG/paper 3/Figures/"
    # CodePath = "/Users/jimeno/Documents/Urben/MOO/"

    #headers = ["D:\paper 3/BAU/", "D:\paper 3/CAMP/", "D:\paper 3/HEB/", "D:\paper 3/UC/"]
    ##savelocation = "C:\urben\MOO"
    CodePath = "C:\urben\MOO"
    matlabDir = "C:\Program Files\MATLAB\R2015b\\bin"  # path to the Matlab core files
    # run epsilon all scenarios and graph
    # plot_epsilon_norm(scenarios,generations, headers)

    # run building connection average box plot and lines per generation
    # plot_building_connection(scenarios, generations, headers)

    # run graphs of pareto optimal
    plot_pareto_scenarios(locator, generation, True)
    plot_pareto_scenarios(locator, generation, False)

    # run graphs of multi-criteria assement and comparison to decentralized_buildings Intra-scenario
    # header = headers[0]
    # pathX = sFn.pathX(headers[0])
    # Generation = generations[0]
    # pop, eps, testedPop = sFn.readCheckPoint(pathX, Generation, 0)
    #
    # print "Network Optimization \n"
    # finalDir = CodePath + "distribution/"
    # ntwFeat = ntwM.ntwMain2(matlabDir, finalDir, header)
    # gV = glob.globalVariables()
    # print "Compute electricity needs for all buildings"
    # elecCosts, elecCO2, elecPrim = elecMain.elecOp(pathX, gV)
    # print elecCosts, elecCO2, elecPrim, "elecCosts, elecCO2, elecPrim \n"
    #
    # print "Process Heat Treatment"
    # hpCosts, hpCO2, hpPrim = hpMain.processHeatOp(pathX, gV)
    # print hpCosts, hpCO2, hpPrim, "hpCosts, hpCO2, hpPrim \n"
    #
    # print "Solar features extraction \n"
    # solarFeat = sFn.solarRead(pathX, gV)
    #
    # finances = elecCosts + hpCosts
    # extraCO2 = elecCO2 + hpCO2
    # extraPrim = elecPrim + hpPrim
    # popRef, epsInd = mM.EA_Main(pathX, finances, extraCO2, extraPrim, solarFeat, ntwFeat, gV, manualCheck = 1)
    #
    # reload(mcda)
    # indToCompare = mcda.mcda_differentWeights(pop, pathX)
    # plot_comparison_MCDA(popRef[0], 0, pop, indToCompare,savelocation, "intra")


    # run graphs of multi-criteria assement and comparison to decentralized_buildings Interscenario
    # SQ_values = [2900000,6106734.8,230330106] # cost,CO2,prim
    # SQ_area = 132274.8
    # header = headers[3]
    # pathX = sFn.pathX(headers[3])
    # Generation = generations[3]
    # pop, eps, testedPop = sFn.readCheckPoint(pathX, Generation, 0)
    # indToCompare = mcda.mcda_differentWeights(pop, pathX)
    # plot_comparison_MCDA(SQ_values, SQ_area, pop, pathX, indToCompare, savelocation, "inter")

    # Area_buildings = pd.read_csv(pathX.pathRaw+'//'+'Total.csv',usecols=['Af']).values.sum()


    #print "Reading and Plotting the results of generation " + str(Generation)
    #pop, eps, testedPop = sFn.readCheckPoint(pathX, Generation, 0)
    #print len(pop), "individuals after generation " + str(Generation) + "\n"


    ## Plots the normalized epsilon indicator
    # epsNorm = norm.epsIndicator(pathX, Generation)

    ## Plots the averaged number of connected buildings & the number of individuals
    # BuildCon, nInd = plots.buildingConnection(Generation, pathX)

    ## Sensitivity analysis
    ## WARNING : can be very long depending on the chosen sensibility step! (multiple days)
    # bandwidth = sens.sensBandwidth()
    # sensibilityStep = 2
    # paretoResults, FactorResults, mostSensitive = sens.sensAnalysis(sensibilityStep, pathX, finances, extraCO2, extraPrim, solarFeat, ntwFeat, Generation, bandwidth)
    # print 'Most sensitive factor :', mostSensitive

    #
    ### Bar chart for the relative savings compared to decentralized_buildings
    # popRef, epsInd = mM.EA_Main(pathX, finances, extraCO2, extraPrim, solarFeat, ntwFeat, gV, manualCheck = 1)
    # indToCompare = mcda.mcda_differentWeights(pop, pathX)
    # reload(plots)
    # plots.compareRef(popRef[0], pop, indToCompare)
    #
    ### intra-scenario MCDA to find the best individual
    # reload(mcda)
    # setWeights = mcda.mcda_criteria()
    # scoreArray, bestInd, indexBest, scoreBest = mcda.mcda_analysis(pop, setWeights, pathX)
    #
    # reload(plots)
    # indexBest = 147
    ### Pie charts for the best individual
    # plots.configDesign(pop, indexBest)
    # plots.connectedbuildings(pop,indexBest)
    # reload(mcda)
    # specificCosts, shareLocal = mcda.mcda_indicators(pop[indexBest], pathX, plot = 1)
    # imp,exp = plots.Elec_ImportExport(pop[indexBest], pathX)
    # costsDisc = normalizeresults.decentralizeCosts(pop[indexBest], pathX, gV)

if __name__ == '__main__':
    test_graphs_optimization()
