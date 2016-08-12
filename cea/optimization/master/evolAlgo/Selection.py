"""
=======================================
Selection of Pareto Optimal individuals
=======================================

"""
def selectPareto(pop):
    """
    Select Pareto Optimal individuals in the population
    An individual is considered Pareto optimal if there exist no other
    individual by whom it is dominated.

    Parameters
    ----------
    pop : list
        List of individuals
    
    Returns
    -------
    selectedInd : list
        list of selected individuals

    """
    selectedInd = list(pop)
    for ind in pop:
        if (ind in selectedInd):
            otherList = [el for el in selectedInd if el != ind]
            for other in otherList:
                if ind.fitness.dominates(other.fitness):
                    selectedInd.remove(other)
    
    return selectedInd
                













