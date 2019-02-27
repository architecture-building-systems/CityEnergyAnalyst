import time
import datetime
from ga_config import *
import random
import process_individual
import numpy as np
import matplotlib.pyplot as plt
import ga_plotting as pf
import pandas as pd
import math
import concept.model_electric_network.emodel as emodel
import copy
import sys

from deap import base
from deap import creator
from deap import tools

import ga_support_functions as sf
import multiprocessing as mp

__author__ = "Sebastian Troitzsch"
__copyright__ = "Copyright 2019, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sebastian Troitzsch", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main():
    """
    Main function of network planning with genetic algorithm
    """

    # Start time tracking
    time_main = time.time()
    datetime_main = datetime.datetime.now()

    # str_csvname = '%4i%02i%02i_%2i%02i%02i_ga_printout.txt' \
    #               % (datetime_main.year, datetime_main.month, datetime_main.day,
    #                  datetime_main.hour, datetime_main.minute, datetime_main.second)
    #
    # sys.stdout = open(LOCATOR + '/' + str_csvname, 'w')

    # +++++++++++++++++++++++++++++++++++++
    # Initiate problem data
    # ++++++++++++++++++++++++++++++++++++++

    df_nodes, tranches, dict_length, dict_path, idx_edge = sf.initial_network()
    df_line_parameter = pd.read_csv(LOCATOR + '/electric_line_data.csv')

    # +++++++++++++++++++++++++++++++++++++
    # SET-UP EVOLUTIONARY ALGORITHM
    # ++++++++++++++++++++++++++++++++++++++

    creator.create("FitnessMin", base.Fitness, weights=(-1.0,))  # weights of -1 for minimization, +1 for maximization
    creator.create("Individual", list, fitness=creator.FitnessMin)

    toolbox = base.Toolbox()

    toolbox.register("generate", sf.generate_pop, idx_edge, df_line_parameter)
    toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.generate)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("mate", tools.cxUniform, indpb=CROSS_RATE)
    toolbox.register("mutate", tools.mutFlipBit, indpb=MUTATE_RATE)
    toolbox.register("select", tools.selTournament, tournsize=TOURNAMENT_SIZE)

    # create population based on the number of individuals in the config file
    pop = toolbox.population(n=POP_SIZE)
    
    # +++++++++++++++++++++++++++++++++++++
    # Variable keeping track of performance
    # ++++++++++++++++++++++++++++++++++++++

    idx_generation = 0  # number of current generation
    fitness_hist = np.zeros(N_GENERATIONS + 1)  # saves fitness of all generations
    time_gen_hist = np.zeros(N_GENERATIONS + 1)
    time_accumulated_hist = np.zeros(N_GENERATIONS + 1)
    fitness_change_hist = np.zeros(N_GENERATIONS + 1)

    halloffame = []
    n_halloffame = int(math.ceil(0.1 * POP_SIZE))

    if PLOTTING:
        fig, (ax1, ax2) = plt.subplots(1, 2, gridspec_kw={'width_ratios': [3, 1]})

    # +++++++++++++++++++++++++++++++++++++
    # Evolution starts !
    # ++++++++++++++++++++++++++++++++++++++

    while idx_generation < N_GENERATIONS:
        time_gen = time.time()
        print "Generation", idx_generation

        # +++++++++++++++++++++++++++++++++++++
        # Multiprocessing individuals
        # ++++++++++++++++++++++++++++++++++++++

        # Open pool for multiprocessing
        n_cpu = mp.cpu_count()
        p = mp.Pool(processes=n_cpu)

        list_pop = []
        for ind in pop:
            list_pop.append(list(ind))

        list_job_result = []

        for idx_ind, ind in enumerate(pop):
            list_ind = list(ind)  # Multiprocessing only processes standard container
            job_result = p.apply_async(process_individual.main,
                                       [idx_ind, list_ind, df_nodes, idx_edge, dict_length, df_line_parameter])

            list_job_result.append(job_result)

        p.close()
        p.join()

        # +++++++++++++++++++++++++++++++++++++
        # Process results of individuals
        # ++++++++++++++++++++++++++++++++++++++

        list_power_loss = []

        for idx_job_ind, list_job_ind in enumerate(list_job_result):
            ind_extracted = list_job_ind.get()

            chromosome = ind_extracted[0]
            ind_power_loss = ind_extracted[1]

            for idx_gene, gene in enumerate(chromosome):
                pop[idx_job_ind][idx_gene] = gene

            list_power_loss.append(ind_power_loss)

        # +++++++++++++++++++++++++++++++++++++
        # Evaluation of individuals
        # ++++++++++++++++++++++++++++++++++++++

        fitnesses = []

        for idx_ind, ind in enumerate(pop):
            ind_power_loss = list_power_loss[idx_ind]
            fitness = sf.evaluate_individual(ind, idx_ind, idx_edge, dict_length, ind_power_loss, df_line_parameter)
            fitnesses.append((fitness,))

        for ind, fit in zip(pop, fitnesses):
            ind.fitness.values = fit

        if not halloffame:
            halloffame = tools.selBest(copy.deepcopy(pop), n_halloffame)
        else:
            halloffame = tools.selBest(copy.deepcopy(pop) + halloffame, n_halloffame)

        best_ind = tools.selBest(halloffame, 1)[0]

        # +++++++++++++++++++++++++++++++++++++
        # Print results of best individual
        # ++++++++++++++++++++++++++++++++++++++

        net = emodel.powerflow_mp(list(best_ind), df_nodes, idx_edge, dict_length, df_line_parameter)
        print net.line.ix[:, ['name', 'from_bus', 'to_bus']]
        print net.res_line

        fitness_hist[idx_generation] = best_ind.fitness.values[0]
        fitness_change_hist[idx_generation] = 100.0 - (fitness_hist[idx_generation]/fitness_hist[idx_generation - 1]) * 100.0

        print fitness_hist
        print 'Fitness change compared to pre-generation: -%.2f %%' % fitness_change_hist[idx_generation]
        print best_ind

        # +++++++++++++++++++++++++++++++++++++
        # Plotting Network and fitness
        # ++++++++++++++++++++++++++++++++++++++

        if PLOTTING:
            # ax1.clear()
            # ax2.clear()
            pf.plot_network(df_nodes, tranches, idx_edge, dict_path, best_ind, fitness_hist, fig, (ax1, ax2))
            # pf.plot_complete(df_nodes, tranches, best_ind, fitness_hist, fig, (ax1, ax2))
            # plt.show()

            plt.draw()
            plt.pause(0.0000001)

        # +++++++++++++++++++++++++++++++++++++
        # Mutation and Crossover
        # ++++++++++++++++++++++++++++++++++++++

        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop)-len(halloffame))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

        # Crossing of Individuals
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < IND_CROSS_RATE:
                toolbox.mate(child1, child2)

        # Mutation of Individuals
        for mutant in offspring:
            if random.random() < IND_MUTATE_RATE:
                toolbox.mutate(mutant)

        # The population is entirely replaced by the offspring
        pop[:] = offspring + copy.deepcopy(halloffame)

        print 'Generation %02i: GA Time: %.2f sec and Gen Time: %.2f sec' \
              % (idx_generation, (time.time() - time_main), (time.time() - time_gen))

        time_gen_hist[idx_generation] = time.time() - time_gen
        time_accumulated_hist[idx_generation] = time.time() - time_main

        idx_generation += 1

    print("-- End of evolution --")
    print("Best individual is %s, %s" % (best_ind, best_ind.fitness.values))

    eval_best = sf.evaluate_best(best_ind, idx_edge, dict_length, ind_power_loss, df_line_parameter)
    net = emodel.powerflow_mp(list(best_ind), df_nodes, idx_edge, dict_length, df_line_parameter)
    print net.line.ix[:, ['name', 'from_bus', 'to_bus']]
    print net.res_line

    sf.write_csv(fitness_hist, best_ind, datetime_main, time_gen_hist, time_accumulated_hist, fitness_change_hist, eval_best)
    sf.save_png(best_ind, datetime_main)
    # plt.show()


if __name__ == "__main__":
    t0 = time.time()
    main()
    print 'network_optimization_main() succeeded'
    print('total time: ', time.time() - t0)
