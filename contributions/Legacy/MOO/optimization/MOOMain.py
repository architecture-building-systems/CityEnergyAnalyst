"""
============================
MOO - Multiobjective Urban Energy System Optimization
============================

"""
#WINDOWS
Header = "C:\ArcGIS\ESMdata\DataFinal\MOO\HEB/"   # path to the input / output folders
CodePath = "C:\urben\MOO/"    # path to this UESM_MainZug.py file

# mac
#Header = "/Volumes/SAMSUNG/paper 3/HEB/"   # path to the input / output folders
#CodePath = "/Users/jimeno/Documents/Urben/MOO/"    # path to this UESM_MainZug.py file


matlabDir = "C:/Program Files/MATLAB/R2014a/bin"    # path to the Matlab core files

import sys
sys.path.append(CodePath)

########################### Import modules

#from __future__ import division
import time
import os
from contributions.Legacy.MOO.technologies import substation as subsM
from contributions.Legacy.MOO.optimization import individual_systems as dbM
from contributions.Legacy.MOO.LCA import processheat as hpMain, electricity
import contributions.Legacy.MOO.optimization.evolAlgo.masterMain as mM
from contributions.Legacy.MOO.network import summarize_network_main as nM
import contributions.Legacy.MOO.optimization.normalizeResults as norm
import contributions.Legacy.MOO.supportFn as sFn
import contributions.Legacy.MOO.ntwOpt.Python.NtwMain as ntwM
import Rep3D as rep
import contributions.Legacy.MOO.globalVar as glob
from contributions.Legacy.MOO.analysis import sensitivity as sens
import contributions.Legacy.MOO.analysis.mcda

reload(subsM)
reload(dbM)
reload(electricity)
reload(hpMain)
reload(mM)
reload(nM)
reload(norm)
reload(sFn)
reload(ntwM)
reload(rep)
reload(glob)
reload(sens)
reload(contributions.Legacy.MOO.analysis.mcda)
reload(post)


##########################  T2 code 

outToFile = 0   # Do you want to save the print outs in an external file ?
                # Warning : this would make sense if you evaluate few / a single individual
                # as the print outs are quite heavy.
preTreat = 1 # Is it the first time you evaluate this scenario ?
                # The first three blocks are pre-treatment.
                # They can be run only once, which saves some time.
runEvol = 1     # Do you want to start an evolution ?
                # If so, have you modified the commands for the EA (in globalVar.py) ?


t0 = time.clock()
gV = glob.globalVariables()
pathX = sFn.pathX(Header)
gV.Tg = sFn.calc_ground_temperature(pathX.pathRaw, gV)
gV.num_tot_buildings = sFn.calc_num_buildings(pathX.pathRaw, "Total.csv")

if outToFile:
    orig_stdout = sys.stdout
    os.chdir(pathX.pathMasterRes)
    f = file("output_Ind154.txt", "w")
    sys.stdout = f

if preTreat:
    print "Run substation model for each building separately \n"
    subsM.subsMain(pathX.pathRaw, pathX.pathRaw, pathX.pathSubsRes, "Total.csv",1, gV) # 1 if disconected buildings are calculated

    print "Heating operation pattern for disconnected buildings \n"
    dbM.discBuildOp(pathX, gV)

    print "Create network file with all buildings connected \n"
    nM.Network_Summary(pathX.pathRaw, pathX.pathRaw, pathX.pathSubsRes, pathX.pathNtwRes, pathX.pathNtwLayout, "Total.csv", gV)

print "Solar features extraction \n"
solarFeat = sFn.solarRead(pathX, gV)

print "Network Optimization \n"
finalDir = CodePath + "ntwOpt/"
ntwFeat = ntwM.ntwMain2(matlabDir, finalDir, Header)    
# WARNING: values in the ntwMain2 routine were computed with the linearization 
# of the pressure losses for the complete networks of Inducity SQ scenario,
# NtwMain is calling the optimization routine

print "Compute electricity needs for all buildings"
elecCosts, elecCO2, elecPrim = electricity.elecOp(pathX, gV)
print elecCosts, elecCO2, elecPrim, "elecCosts, elecCO2, elecPrim \n"

print "Process Heat Treatment"
hpCosts, hpCO2, hpPrim = hpMain.calc_pareto_Qhp(pathX, gV)
print hpCosts, hpCO2, hpPrim, "hpCosts, hpCO2, hpPrim \n"

extraCosts = elecCosts + hpCosts
extraCO2 = elecCO2 + hpCO2
extraPrim = elecPrim + hpPrim

if runEvol:
    print "Master / Slave optimization \n"
    popFinal, eps = mM.EA_Main(pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gV)
    print eps
    
print "Time for routine: ", time.clock()-t0 ,"seconds \n"

if outToFile:
    sys.stdout = orig_stdout
    f.close()


########################### Post-processing
# Un-comment the blocs that you want to run

Generation = 24
print "Reading and Plotting the results of generation " + str(Generation)
pop, eps, testedPop = sFn.readCheckPoint(pathX, Generation, 0)
print len(pop), "individuals after generation " + str(Generation) + "\n"
#
##Prints the individuals and their fitness
#sFn.printFit(pop)
#sFn.printInd(pop)
#
#reload(rep)
### Plots the Pareto front
#rep.rep2Dscatter(pop, 1, pathX)
#rep.rep3Dscatter(pop, 1)
#rep.rep3Dsurf(pop)
#subGeneration = 1
#rep.twoParetoFronts(Generation, subGeneration, pathX)

## Plots the normalized epsilon indicator
#epsNorm = norm.epsIndicator(pathX, Generation)

## Plots the averaged number of connected buildings & the number of individuals
#BuildCon, nInd = plots.buildingConnection(Generation, pathX)

## Sensitivity analysis
## WARNING : can be very long depending on the chosen sensibility step! (multiple days)
#bandwidth = sens.sensBandwidth()
#sensibilityStep = 2
#paretoResults, FactorResults, mostSensitive = sens.sensAnalysis(sensibilityStep, pathX, finances, extraCO2, extraPrim, solarFeat, ntwFeat, Generation, bandwidth)
#print 'Most sensitive factor :', mostSensitive
#rep.rep3Dscatter_sensitivity(pop, ParetoResults)
#reload(rep)
#rep.rep2Dscatter_sensitivity(pop, ParetoResults, pathX)
#
### Bar chart for the relative savings compared to baseline
#popRef, epsInd = mM.EA_Main(pathX, finances, extraCO2, extraPrim, solarFeat, ntwFeat, gV, manualCheck = 1)
#indToCompare = mcda.mcda_differentWeights(pop, pathX)
#reload(plots)
#plots.compareRef(popRef[0], pop, indToCompare)
#
### intra-scenario MCDA to find the best individual
#reload(mcda)
#setWeights = mcda.mcda_criteria()
#scoreArray, bestInd, indexBest, scoreBest = mcda.mcda_analysis(pop, setWeights, pathX)
#
#reload(plots)
#indexBest = 147
### Pie charts for the best individual
#plots.configDesign(pop, indexBest)
#plots.connectedbuildings(pop,indexBest)
#reload(mcda)
#specificCosts, shareLocal = mcda.mcda_indicators(pop[indexBest], pathX, plot = 1)
#imp,exp = plots.Elec_ImportExport(pop[indexBest], pathX)
#costsDisc = normalizeresults.decentralizeCosts(pop[indexBest], pathX, gV)