"""
=================================
3D representation of a population
=================================

"""
import numpy as np
import matplotlib.pyplot as plt
#from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from pylab import *
import matplotlib.cm as cmx
import supportFn as sFn
import pandas as pd


def rep3Dscatter(pop, IndicatorToPlot):
    """
    Represents the individuals of a population in 3D with scattered points
    
    Parameters
    ----------
    pop : list
        Population of deap.creator.individuals
        
    cmap : string
        name the cost map you'd like to use, e.g. 
        
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    

    def resadjust(ax, xs, ys, zs, nticks):
        """Send in an axis and I fix the resolution as desired."""
        xres = (max(xs)-min(xs))/ nticks
        yres = (max(ys)-min(ys))/ nticks
        zres = (max(zs)-min(zs))/ nticks
        
        start, stop = ax.get_xlim()
        ticks = np.round(np.arange(start, stop + xres, xres),-4)
        ax.set_xticks(ticks)
        
        start, stop = ax.get_ylim()
        ticks = np.round(np.arange(start, stop + yres, yres),-4)
        ax.set_yticks(ticks)
        
        start, stop = ax.get_zlim()
        ticks = np.round(np.arange(start, stop + zres, zres),-4)
        ax.set_zticks(ticks)
        
 
    def scatter3d(x,y,z, cs, colorsMap='jet'):
        cm = plt.get_cmap(colorsMap)
        cNorm = matplotlib.colors.Normalize(vmin=min(cs), vmax=max(cs))
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
        fig = plt.figure()
        ax = Axes3D(fig)
        ax.scatter(x, y, z, c=scalarMap.to_rgba(cs))    
        ax.set_xlabel('Cost [CHF]')
        ax.set_ylabel('GHG emissions [kg_CO2_eq]')
        ax.set_zlabel('Primary Energy Needs [MJ_Oil]')

        scalarMap.set_array(cs)
        fig.colorbar(scalarMap)
        #fig.set_label("cost in CHF")
        #for i in range(len(xs)):
        #    ax.plot([xs[i], xs[i]], [ys[i], ys[i]], [min(zs)*0.95, zs[i]], '--', linewidth=1, color='b', alpha=.5)
        #ax.set_zlim(min(zs),max(zs))
        #resadjust(ax, xs, ys, zs, nticks= 3)

        
    cs = zs # state what the color map should stand for
    scatter3d(xs,ys,zs, cs, colorsMap='jet')
    #print "xs", xs
    
    ax.scatter(xs, ys, zs, cmap = cm.jet)
    #resadjust(ax, xs, ys, zs, nticks= 3)
    ax.set_xlabel('Total annualized costs')
    ax.set_ylabel('GHG emissions')
    ax.set_zlabel('Primary Energy Needs')
            
        

    if IndicatorToPlot == 1:
        plt.show()


def rep3Dscatter_sensitivity(pop, ParetoResults):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    
    [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    minP = min(ParetoResults)
    maxP = max(ParetoResults)
    normParetoRes = np.array( [ (x-minP) / (maxP-minP) for x in ParetoResults ] )
    
    cm = plt.get_cmap('jet')
    cNorm = matplotlib.colors.Normalize(vmin=0, vmax=1)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
    
    ax.scatter(xs, ys, zs, c=scalarMap.to_rgba(normParetoRes))
    ax.set_xlabel('Total annualized costs')
    ax.set_ylabel('GHG emissions')
    ax.set_zlabel('Primary Energy Needs')
    
    scalarMap.set_array(normParetoRes)
    fig.colorbar(scalarMap)
        
    plt.show()


def rep3Dsurf(pop):
    """
    Represents the individuals of a population in 3D with surface
    
    Parameters
    ----------
    pop : list
        Population of deap.creator.individuals
        
    """
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    
    [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    ax.plot_trisurf(xs, ys, zs, cmap=cm.jet, linewidth=0.2)



    def surfWithLines(x,y,z, cs, colorsMap='jet'):
        #cm = plt.get_cmap(colorsMap)
        cNorm = matplotlib.colors.Normalize(vmin=min(cs), vmax=max(cs))
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
        fig = plt.figure()
        ax = Axes3D(fig)
        ax.plot_trisurf(xs, ys, zs, cmap=cm.jet, linewidth=0.2)
        ax.set_xlabel('Cost [CHF] Trisurf')
        ax.set_ylabel('GHG emissions [kg_CO2_eq]')
        ax.set_zlabel('Primary Energy Needs [MJ_Oil]')

        scalarMap.set_array(cs)
        fig.colorbar(scalarMap)
        fig.set_label("cost in CHF")
        for i in range(len(xs)):
            ax.plot([xs[i], xs[i]], [ys[i], ys[i]], [min(zs)*0.95, zs[i]], '--', linewidth=0.5, color='y', alpha=.5)
        ax.set_zlim(min(zs),max(zs)*1.1)
        plt.show()

    #cs = xs # state what the color map should stand for
    #surfWithLines(xs,ys,zs, cs, colorsMap='jet')
    ax.set_xlabel('Total annualized costs')
    ax.set_ylabel('GHG emissions')
    ax.set_zlabel('Primary Energy Needs')
    
    plt.show()


def twoParetoFronts(GenerationA, GenerationB, pathX):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlabel('Total annualized costs')
    ax.set_ylabel('GHG emissions')
    ax.set_zlabel('Primary Energy Needs')

    pop, eps, testedPop = sFn.readCheckPoint(pathX, GenerationA, 0)    
    [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    ax.scatter(xs, ys, zs, s=40, c='r', marker='o')
    
    pop, eps, testedPop = sFn.readCheckPoint(pathX, GenerationB, 0)    
    [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    ax.scatter(xs, ys, zs, s=40, c='g', marker='o')
    
    plt.show()

    
def rep2Dscatter_sensitivity(pop, ParetoResults,pathX):
    
    Area_buildings = pd.read_csv(pathX.pathRaw+'//'+'Total.csv',usecols=['Af']).values.sum()
    fig = plt.figure(figsize=(6,4))
    ax = fig.add_subplot(111)
    
    [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    minP = min(ParetoResults)
    maxP = max(ParetoResults)
    normParetoRes = np.array( [ (x-minP) / (maxP-minP) for x in ParetoResults ] )
    
    
    cm = plt.get_cmap('Blues')
    cNorm = matplotlib.colors.Normalize(vmin=0.8, vmax=0.8)
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
    
    ax.scatter(xs/Area_buildings, ys/Area_buildings, c=scalarMap.to_rgba(normParetoRes),s=100)
    ax.set_xlabel('TAC [EU/m2.yr]')
    ax.set_ylabel('CO2 [kg-CO2/m2.yr]')
    ax.grid(True)
    
    scalarMap.set_array(normParetoRes)
    fig.colorbar(scalarMap, label='ROBUSTNESS [-]')
    plt.rcParams.update({'font.size':20})
    
    plt.show()
    #count number of individuals out of threshold 0.8:
    individuals_out= [x for x in normParetoRes if x<0.8]
    num_discarded = len(individuals_out)   
    print  'num of individuals to discrad with robustness < 0.8:  ' + str(num_discarded) 

def rep2Dscatter(pop, IndicatorToPlot,pathX):

    Area_buildings = pd.read_csv(pathX.pathRaw+'//'+'Total.csv',usecols=['Af']).values.sum()
    fig = plt.figure(figsize=(6,4))
    ax = fig.add_subplot(111)

    [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    
    zs = zs/Area_buildings
    cm = plt.get_cmap('jet')
    cNorm = matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs))
    scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)

    ax.scatter(xs/Area_buildings, ys/Area_buildings, c=scalarMap.to_rgba(zs), s=100, )    
    ax.set_xlabel('TAC [EU/m2.yr]')
    ax.set_ylabel('CO2 [kg-CO2/m2.yr]')
    ax.grid(True)
    ax.ylim=(15,80)

    scalarMap.set_array(zs)
    fig.colorbar(scalarMap, label='PEN [MJ/m2.yr]')
    plt.rcParams.update({'font.size':20})
    
    plt.show()

def rep2Dscatter_scenarios(pop, num, list_paths):
    
    fig = plt.figure()
    for x in range(num):
        Area_buildings = pd.read_csv(list_paths[x].pathRaw+'//'+'Total.csv',usecols=['Af']).values.sum()
        ax = fig.add_subplot(111)
        [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop[x]] ) )
        zs = zs/Area_buildings
        cm = plt.get_cmap('jet')
        cNorm = matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs))
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
    
        ax.scatter(xs/1000000, ys/Area_buildings, c=scalarMap.to_rgba(zs), s=100)    
        ax.set_xlabel('TAC [Mio EU/yr]')
        ax.set_ylabel('CO2 [kg-CO2/m2.yr]')
        ax.grid(True)
    
        scalarMap.set_array(zs)
        fig.colorbar(scalarMap, label='PEN [MJ/m2.yr]')

    plt.rcParams.update({'font.size':15})
    plt.show()