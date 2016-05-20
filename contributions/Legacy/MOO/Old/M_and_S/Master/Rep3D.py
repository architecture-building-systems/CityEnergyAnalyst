"""
=================================
3D representation of a population
=================================

"""
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


def rep3Dscatter(pop):
    """
    Represents the individuals of a population in 3D with scattered points
    
    Parameters
    ----------
    pop : list
        Population of deap.creator.individuals
        
    """
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    ax.scatter(xs, ys, -zs,s=20, c=u'b')
   
    ax.set_xlabel('Costs')
    ax.set_ylabel('CO2 emissions')
    ax.set_zlabel('Efficiency')
    
    plt.show()


def rep3Dsurf(pop):
    """
    Represents the individuals of a population in 3D with surface
    Nota : represents -Efficiency instead of +Efficiency to obtain a hollow curve
    
    Parameters
    ----------
    pop : list
        Population of deap.creator.individuals
        
    """
    fig = plt.figure()
    ax = fig.gca(projection='3d')
    
    [xs, ys, zs] = map(np.array, zip( *[ind.fitness.values for ind in pop] ) )
    ax.plot_trisurf(xs, ys, -zs, linewidth=0.2)
    
    ax.set_xlabel('Costs')
    ax.set_ylabel('CO2 emissions')
    ax.set_zlabel('- Efficiency')
    
    plt.show()










