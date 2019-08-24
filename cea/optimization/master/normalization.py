from __future__ import division


def normalize_fitnesses(scaler_dict, fitnesses_population):
    number_of_objectives = scaler_dict['NOBJ']
    fitness_population_scaled = []
    for ind in fitnesses_population:
        fitness_individual_scaled = []
        for objective in range(number_of_objectives):
            min_value = scaler_dict['min'][objective]
            max_value = scaler_dict['max'][objective]
            fitness_individual_scaled.append(minmax_scaler(ind[objective], min_value, max_value))
        fitness_population_scaled.append(tuple(fitness_individual_scaled))

    return fitness_population_scaled


def minmax_scaler(value, min_value, max_value):
    return (value - min_value) / (max_value - min_value)


def scaler_for_normalization(number_of_objectives, fitnesses):
    max_ob = []
    min_ob = []
    for objective in range(number_of_objectives):
        list_fitness_objective = [x[objective] for x in fitnesses]
        max_ob.append(max(list_fitness_objective))
        min_ob.append(min(list_fitness_objective, 0.0))  # in case there are negative, select the negative

    # Output to scale data inside the fitness funcion from the second generation on
    scaler_dict = {'max': max_ob, 'min': min_ob, 'NOBJ': number_of_objectives}

    return scaler_dict
