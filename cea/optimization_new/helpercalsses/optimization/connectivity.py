"""
Connectivity Vector Class:
Connectivity Vectors are objects that contain information regarding the connection of buildings in the domain to the
available thermal networks.

E.g. let's assume there are 8 buildings in a district energy system which can be connected in up to 2 networks.
The corresponding connectivity vector contain 8 <Connection> objects (one per building) indicating which of the networks
each of the buildings are connected to in the given configuration:

network_connctions = [0, 1, 0, 0, 2, 1, 1, 2]
buildings = ['B1001', 'B1002', 'B1003', 'B1004', 'B1005', 'B1006', 'B1007', 'B1008']

The <ConnectivityVector>-class behaves like a sequence (which is relevant for some methods of the deap-library)
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

from random import randint
from deap import tools

from cea.optimization_new.helpercalsses.optimization.fitness import Fitness


class Connection(object):
    possible_connections = range(0)
    possible_building_codes = []
    zero_demand_buildings = []

    def __init__(self, network_connection=None, building_code=None):
        self.building = building_code
        if network_connection:
            self.network_connection = network_connection
        else:
            self.network_connection = 0

    @property
    def network_connection(self):
        return self._network_connection

    @network_connection.setter
    def network_connection(self, new_connection):
        if new_connection and not isinstance(new_connection, int):
            raise ValueError(f"Network connection indicators need to be integer values. Tried to assign "
                             f"{new_connection}.")
        elif new_connection and not (new_connection in Connection.possible_connections):
            raise ValueError(f"The network connection indicator needs to be in the range "
                             f"[{Connection.possible_connections.start}, {Connection.possible_connections.stop - 1}]. "
                             f"Tried to assign {new_connection}.")
        elif self.building in Connection.zero_demand_buildings:
            self._network_connection = 0
        else:
            self._network_connection = new_connection

    @property
    def building(self):
        return self._building

    @building.setter
    def building(self, new_building_code):
        if new_building_code and not isinstance(new_building_code, str):
            raise ValueError(f"The connection indicators' corresponding building codes need to be of type string. "
                             f"Tried to assign {new_building_code}.")
        elif new_building_code and not (new_building_code in Connection.possible_building_codes):
            raise ValueError(f"The building code needs to be a valid identifier of one of the buildings withing the "
                             f"domain. Tried to assign {new_building_code}.")
        else:
            self._building = new_building_code

    @staticmethod
    def initialize_class_variables(domain):
        Connection.possible_connections = range(domain.config.optimization_new.maximum_number_of_networks + 1)
        Connection.possible_building_codes = [building.identifier for building in domain.buildings]
        Connection.zero_demand_buildings = [building.identifier for building in domain.buildings
                                            if all(building.demand_flow.profile == 0)]


class ConnectivityVector(object):

    def __init__(self, connection_list=None):
        if not connection_list:
            self.connections = [Connection()]
        else:
            self.connections = connection_list
        self.fitness = Fitness()

    @property
    def connections(self):
        return self._connections

    @connections.setter
    def connections(self, new_connections):
        if not (isinstance(new_connections, list) and
                all([isinstance(connection, Connection) for connection in new_connections])):
            raise ValueError("The initialisation of a new connectivity vector requires a list of 'Connection'-objects.")
        else:
            # Check if any of the network connection values appear only once...
            new_values = [new_connection.network_connection for new_connection in new_connections]
            values_appearing_once = [i for i in Connection.possible_connections if new_values.count(i) == 1]

            # ... if so set them to 0 (network with only one building = stand-alone building)
            if values_appearing_once:
                changed_values = {i: 0 for i, connection in enumerate(new_connections)
                                  if connection.network_connection in values_appearing_once}
                for index, corrected_value in changed_values.items():
                    new_connections[index].network_connection = corrected_value

            # Set the connectivity vector
            self._connections = new_connections


    @property
    def values(self):
        network_connection_values = [connection.network_connection for connection in self.connections]
        return network_connection_values

    @values.setter
    def values(self, new_values):
        if not (isinstance(new_values, list) and len(new_values) == len(self)):
            raise ValueError("To assign new network connection indicator values they need to be given as a list of "
                             "the same length as the connectivity vector.")
        else:
            # Check if any of the network connection values appear only once...
            values_appearing_once = [i for i in Connection.possible_connections if new_values.count(i) == 1]

            # ... if so set them to 0 (network with only one building = stand-alone building)
            if values_appearing_once:
                new_values = [0 if i in values_appearing_once else i for i in new_values]

            # Set the new values
            for i in range(len(self)):
                self[i] = new_values[i]

    @property
    def fitness(self):
        return self._fitness

    @fitness.setter
    def fitness(self, new_fitness):
        if not isinstance(new_fitness, Fitness):
            raise ValueError("The indicated fitness value is not an object of the Fitness class. The deap library's "
                             "selection functions need the attributes of that class to operate properly.")
        else:
            self._fitness = new_fitness

    def __len__(self):
        return len(self.connections)

    def __getitem__(self, item):
        if isinstance(item, slice):
            selected_connections = self._connections[item]
            return [connection.network_connection for connection in selected_connections]
        elif isinstance(item, int):
            return self.connections[item].network_connection
        else:
            return None

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            if key.start:
                ind_start = key.start
            else:
                ind_start = 0
            if key.stop:
                ind_stop = key.stop
            else:
                ind_stop = len(self)
            if key.step:
                ind_step = key.step
            else:
                ind_step = 1
            for index in list(range(ind_start, ind_stop, ind_step)):
                self.connections[index].network_connection = round(value[index-ind_start], 2)
        elif isinstance(key, int):
            self.connections[key].network_connection = round(value, 2)

    def reset(self):
        """
        Reset the entire connectivity vector at once in order to correct connectivity values (checked in the setter)
        after mutation or recombination.
        e.g. if only one building is connected to any given network, i.e. it is really a stand-alone building)
        """
        self.connections = self.connections

        return self

    def as_str(self):
        """
        Return the capacity indicator vector as single string-object (network connection values spaced by an underscore)
        """
        connectivity_str = '_'.join(map(str, self.values))
        return connectivity_str

    @staticmethod
    def generate(method='random'):
        """
        Generate a new list of <Connection>-class objects with random network-connection values in [0, nbr_networks].
        """
        if method == 'random':
            min_connection_ind = Connection.possible_connections.start
            max_connection_ind = Connection.possible_connections.stop - 1
            connections_list = [Connection(randint(min_connection_ind, max_connection_ind), building)
                                for building in Connection.possible_building_codes]
        else:
            connections_list = [Connection(0, building) for building in Connection.possible_building_codes]
        return connections_list

    @staticmethod
    def mutate(cv, algorithm=None):
        """
        Mutate the connectivity vector (inplace) according to the defined mutation algorithm.
        """
        if algorithm.mutation == 'ShuffleIndexes':
            mutated_cv = tools.mutShuffleIndexes(cv, algorithm.mut_prob)
        elif algorithm.mutation == 'UniformInteger':
            nbr_of_networks = Connection.possible_connections.stop - 1
            mutated_cv = tools.mutUniformInt(cv, low=0, up=nbr_of_networks, indpb=algorithm.mut_prob)
        else:
            raise ValueError(f"The chosen mutation method ({algorithm.mutation}) has not been implemented for "
                             f"connectivity vectors.")

        # reset to correct potential format of the connectivity vector
        mutated_cv[0].reset()

        return mutated_cv

    @staticmethod
    def mate(cv_1, cv_2, algorithm=None):
        """
        Recombine two connectivity vectors (inplace) according to the defined crossover algorithm.
        """
        if algorithm.crossover == 'OnePoint':
            recombined_cvs = tools.cxOnePoint(cv_1, cv_2)
        elif algorithm.crossover == 'TwoPoint':
            recombined_cvs = tools.cxTwoPoint(cv_1, cv_2)
        elif algorithm.crossover == 'Uniform':
            recombined_cvs = tools.cxUniform(cv_1, cv_2, algorithm.cx_prob)
        else:
            raise ValueError(f"The chosen crossover method ({algorithm.crossover}) has not been implemented for "
                             f"connectivity vectors.")

        # reset to correct potential error in format of the connectivity vectors
        recombined_cvs[0].reset()
        recombined_cvs[1].reset()

        return recombined_cvs

    @staticmethod
    def select(individuals_list, energy_system_solutions_dict, population_size, optimization_tracker=None):
        """
        Select the 'best' connectivity vectors by performing 'non-dominated sorting' (NSGA) on their respective energy
        system solutions; where the energy system solutions are given by the 'best' combinations of the supply systems
        for each of the networks given by the connectivity vectors.

        :param individuals_list: list of the investigated connectivity vectors
        :type individuals_list: list of <ConnectivityVector>-class objects
        :param energy_system_solutions_dict: A set of non-dominated energy system solutions for each connectivity vector.
                                             Each energy system solution is a combination of supply systems for each
                                             network + supply systems for each stand-alone building. Non-domination is
                                             determined based on selected objectives for the optimisation.
        :type energy_system_solutions_dict: dict of lists of <deap.creator.SystemCombination>-class objects
                                            (defined in cea.optimization_new.districtEnergySystem.py)
        :param population_size: number of individuals to be selected as the population of the next interation
        :type population_size: int
        :param optimization_tracker: object tracking the progress of the optimization
        :type optimization_tracker: <cea.optimization_new.helperclasses.optimization.tracker>-OptimizationTracker class
                                    object
        """
        # create a dictionary associating the connectivity 'str'-expression to the corresponding objects
        individual_dict = {ind.as_str(): ind for ind in individuals_list}

        # combine all energy system solutions (i.e. supply system combinations) in one large list
        all_supsys_combinations = sum(energy_system_solutions_dict.values(), start=[])
        nbr_solutions = len(all_supsys_combinations)

        # perform non-dominated sorting on the list of energy system solutions and identify which connectivity-vector's
        # solutions appear in which front (i.e. order of non-dominated front)
        supsys_combination_solution_fronts = tools.emo.sortLogNondominated(all_supsys_combinations, nbr_solutions)
        connectivity_vectors_by_front = {front: list(set([supsys_combination.encoding[0]
                                                          for supsys_combination in solutions_in_front]))
                                         for front, solutions_in_front in enumerate(supsys_combination_solution_fronts)}

        # select a new population of 'best' connectivity vectors
        new_population = []
        for front in connectivity_vectors_by_front.values():
            if len(new_population) >= population_size:
                break

            for connectivity_vector in front:
                if len(new_population) >= population_size:
                    break

                if connectivity_vector in individual_dict.keys():
                    new_population += [individual_dict[connectivity_vector]]
                    del individual_dict[connectivity_vector]

        if optimization_tracker:
            optimization_tracker.update_current_non_dominated_fronts(new_population, supsys_combination_solution_fronts)

        return new_population
