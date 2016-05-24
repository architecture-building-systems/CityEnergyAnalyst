# -*- coding: utf-8 -*-
"""
'Post-processing routine - GRAPHS
Created on Fri Sep 25 10:58:48 2015

@author: Jimeno Fonseca
"""

from __future__ import division
import matplotlib.pyplot as plt
import normalizeResults as norm
import matplotlib
import matplotlib.cm as cmx
import supportFn as sFn
import pandas as pd
import mcda as mcda
import numpy as np

reload(norm)
reload(sFn)

def plot_comparison_MCDA(indRef, SQ_area, pop, pathX, listIndex, savelocation, type_analysis):
    
    
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


def plot_pareto(generations, headers, relative, savelocation): 
    xs =[]
    ys =[]
    zs =[]
    fig = plt.figure()
    counter = 0
    for header in headers:
        pathX = sFn.pathX(header)
        pop, eps, testedPop = sFn.readCheckPoint(pathX, generations[counter], 0)
        Area_buildings = pd.read_csv(pathX.pathRaw+'//'+'Total.csv',usecols=['Af']).values.sum()
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
        finallocation = savelocation+"pareto_m2.png"
    else:
        var = 1000000
        zs[:] = [x / var for x in zs]
        xs[:] = [x / var for x in xs]
        ys[:] = [x / var for x in ys]
        TAC = 'TAC [Mio EU/yr]'
        CO2 = 'CO2 [kton-CO2/yr]'
        PEN = 'PEN [TJ/yr]' 
        ax.set_xlim([2.5,7.0]) 
        finallocation = savelocation+"pareto.png"
               
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
    
def plot_epsilon_norm(scenarios,generations, headers):    
    colors = ['b','r','y','c']    
    fig = plt.figure()   
    counter = 0    
    for scenario in scenarios:
        epsNorm = norm.epsIndicator(sFn.pathX(headers[counter]), generations[counter])
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

def plot_building_connection(scenarios, generations, headers):
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
            pop, eps, testedPop = sFn.readCheckPoint(pathX, i, 0)
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
    
# define scenarios and headers
scenarios = ['BAU', 'CAMP', 'HEB', 'UC']
generations = [24,24,5,24] 
#headers = ["/Volumes/SAMSUNG/paper 3/BAU/", "/Volumes/SAMSUNG/paper 3/CAMP/", "/Volumes/SAMSUNG/paper 3/HEB/", "/Volumes/SAMSUNG/paper 3/UC/"]
#savelocation = "/Volumes/SAMSUNG/paper 3/Figures/"
#CodePath = "/Users/jimeno/Documents/Urben/MOO/" 
	
headers = ["D:\paper 3/BAU/", "D:\paper 3/CAMP/", "D:\paper 3/HEB/", "D:\paper 3/UC/"]
savelocation = "D:\paper 3/Figures/"
CodePath = "C:\urben\MOO/"
matlabDir = "C:/Program Files/MATLAB/R2014a/bin"    # path to the Matlab core files
# run epsilon all scenarios and graph
#plot_epsilon_norm(scenarios,generations, headers)

# run building connection average box plot and lines per generation
#plot_building_connection(scenarios, generations, headers)

# run graphs of pareto optimal
plot_pareto(generations, headers, True, savelocation)
plot_pareto(generations, headers, False, savelocation)

#run graphs of multi-criteria assement and comparison to baseline Intra-scenario
#header = headers[0]
#pathX = sFn.pathX(headers[0])
#Generation = generations[0]
#pop, eps, testedPop = sFn.readCheckPoint(pathX, Generation, 0)
#
#print "Network Optimization \n"
#finalDir = CodePath + "ntwOpt/"
#ntwFeat = ntwM.ntwMain2(matlabDir, finalDir, header)  
#gV = glob.globalVariables()
#print "Compute electricity needs for all buildings"
#elecCosts, elecCO2, elecPrim = elecMain.elecOp(pathX, gV)
#print elecCosts, elecCO2, elecPrim, "elecCosts, elecCO2, elecPrim \n"
#
#print "Process Heat Treatment"
#hpCosts, hpCO2, hpPrim = hpMain.processHeatOp(pathX, gV)
#print hpCosts, hpCO2, hpPrim, "hpCosts, hpCO2, hpPrim \n"
#
#print "Solar features extraction \n"
#solarFeat = sFn.solarRead(pathX, gV)
#
#extraCosts = elecCosts + hpCosts
#extraCO2 = elecCO2 + hpCO2
#extraPrim = elecPrim + hpPrim
#popRef, epsInd = mM.EA_Main(pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gV, manualCheck = 1)
#
#reload(mcda)
#indToCompare = mcda.mcda_differentWeights(pop, pathX)
#plot_comparison_MCDA(popRef[0], 0, pop, indToCompare,savelocation, "intra")


#run graphs of multi-criteria assement and comparison to baseline Interscenario
#SQ_values = [2900000,6106734.8,230330106] # cost,CO2,prim
#SQ_area = 132274.8
#header = headers[3]
#pathX = sFn.pathX(headers[3])
#Generation = generations[3]
#pop, eps, testedPop = sFn.readCheckPoint(pathX, Generation, 0)
#indToCompare = mcda.mcda_differentWeights(pop, pathX)
#plot_comparison_MCDA(SQ_values, SQ_area, pop, pathX, indToCompare, savelocation, "inter")

#Area_buildings = pd.read_csv(pathX.pathRaw+'//'+'Total.csv',usecols=['Af']).values.sum()
