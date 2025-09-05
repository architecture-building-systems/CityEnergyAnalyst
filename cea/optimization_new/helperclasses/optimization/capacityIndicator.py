"""
Capacity Indicator Vector Class:
Capacity indicators are float values in [0,1] that indicate to what percentage of the maximum capacity
each viable component of a supply system structure is installed in a specific configuration of that supply system.

E.g. The supplySystemStructure-object indicates that the maximum viable capacity for a vapour compression chiller is
2MW (since this structure is laid out to provide a maximum of 2MW of cooling). If the capacity indicator is 0.5, that
would mean, that the capacity of the installed vapour compression chiller in that system configuration would be 1MW.

Detailed Capacity Indicator Vector Example:
values = [0.3, 0.1, 0.2, 0.3, 0.4, 0.7, 0.8, 0.2, 0.3]
categories = ['primary', 'primary', 'primary', 'secondary', 'secondary', 'secondary', 'secondary', 'tertiary', 'tertiary']
codes = ['VCC1', 'VCC2', 'ACH1', 'BO1', 'BO2', 'OEHR1', 'FORC1', 'CT1', 'CT2']

The <CapacityIndicatorVector>-class behaves like a sequence (which is relevant for some methods of the deap-library)
"""

__author__ = "Mathias Niffeler"
__copyright__ = "Copyright 2023, Cooling Singapore"
__credits__ = ["Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "NA"
__email__ = "mathias.niffeler@sec.ethz.ch"
__status__ = "Production"

import copy
import random
import warnings
import numpy as np

from deap import tools

from cea.optimization_new.helperclasses.optimization.fitness import Fitness


class CapacityIndicator(object):
    def __init__(self, component_category=None, component_code=None, main_energy_carrier=None, value=None):
        if value:
            self.value = value
        else:
            self.value = 1
        self.code = component_code
        self.category = component_category
        self.main_energy_carrier = main_energy_carrier

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, new_category):
        if new_category and new_category not in ['primary', 'secondary', 'tertiary']:
            raise ValueError("The capacity indicators' associated supply system category needs to be either: "
                             "'primary', 'secondary' or 'tertiary'")
        else:
            self._category = new_category

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, new_code):
        if new_code and not isinstance(new_code, str):
            raise ValueError("Component codes need to be of type string.")
        else:
            self._code = new_code

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if new_value and new_value > 1:
            self._value = 1
            warnings.warn("There was an attempt to apply a value larger than 1 to a capacity indicator. "
                          "This is not allowed. The value is set to 1.")
        elif new_value and new_value < 0:
            self._value = 0
            warnings.warn("There was an attempt to apply a value smaller than 0 to a capacity indicator. "
                          "This is not allowed. The value is set to 0.")
        else:
            if new_value == 0 or new_value == 1:
                self._value = int(new_value)
            else:
                self._value = round(new_value, 2)


class CapacityIndicatorVector(object):

    _overdimensioning_factor = 1.2

    def __init__(self, capacity_indicators_list=None, dependencies=None):
        self.dependencies = dependencies
        if not capacity_indicators_list:
            self._capacity_indicators = [CapacityIndicator()]
        else:
            self.capacity_indicators = capacity_indicators_list
        self.fitness = Fitness()

    @staticmethod
    def initialize(capacity_indicator_generator=None, dependencies=None):
        """ Initializes a capacity indicator vector based on a preset generator function. """
        return CapacityIndicatorVector(capacity_indicator_generator(), dependencies)

    @property
    def capacity_indicators(self):
        return self._capacity_indicators

    @capacity_indicators.setter
    def capacity_indicators(self, new_capacity_indicators):
        if not all([isinstance(capacity_indicator, CapacityIndicator) for capacity_indicator in new_capacity_indicators]):
            raise ValueError("Elements of the capacity indicators vector can only be instances of CapacityIndicator.")
        else:
            self._capacity_indicators = new_capacity_indicators
            if any(self._categories_overdimensioned([ci.value for ci in new_capacity_indicators])):
                self.values = [ci.value for ci in new_capacity_indicators] # values setter will correct overdimensioning

    @property
    def values(self):
        ci_values = [capacity_indicator.value for capacity_indicator in self.capacity_indicators]
        return ci_values

    @values.setter
    def values(self, new_values):
        if not (isinstance(new_values, list) and len(new_values) == len(self)):
            raise ValueError("The new capacity indicator vector values need to be a list and correspond to the "
                             "length of the supply system structure's capacity indicator vector.")
        elif not new_values == [] and \
                any(self._categories_overdimensioned(new_values)):
            corrected_values = self._correct_values(new_values)
            for i in range(len(self)):
                self[i] = corrected_values[i]
        else:
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
        return len(self.capacity_indicators)

    def __getitem__(self, item):
        """
        Allows calling the capacity indicator vector (civ) values easily, by indexing the civ directly.
        (e.g. civ.values: [0.8, 0.2, 0.5, 0.2, 1.0],
        """
        if isinstance(item, slice):
            selected_capacity_indicators = self._capacity_indicators[item]
            return [capacity_indicator.value for capacity_indicator in selected_capacity_indicators]
        elif isinstance(item, int):
            return self.capacity_indicators[item].value
        else:
            return None

    def __setitem__(self, key, value):
        """
        Allows resetting the values of the capacity indicator vector (civ) easily, by assigning the list of new
        values to the civ directly. (e.g. civ = [0.3, 0.4, 0.8, 0.1, 0.9] -> civ.values: [0.3, 0.4, 0.8, 0.1, 0.9])
        """
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
                self.capacity_indicators[index].value = round(value[index-ind_start], 2)
        elif isinstance(key, int):
            self.capacity_indicators[key].value = round(value, 2)


    def __eq__(self, other):
        """
        Allows comparing two capacity indicator vectors (civs) easily, by comparing:
        - the component categories (primary, secondary, tertiary)
        - the component codes (e.g. CH2, AC1, BO3, etc.)
        - the values
        of each of the capacity indicators that make up the civs.
        """
        if isinstance(other, CapacityIndicatorVector):
            categories = "_".join([ci.category for ci in self.capacity_indicators])
            other_categories = "_".join([ci.category for ci in other.capacity_indicators])
            codes = "_".join([ci.code for ci in self.capacity_indicators])
            other_codes = "_".join([ci.code for ci in other.capacity_indicators])
            values = "_".join([str(ci.value) for ci in self.capacity_indicators])
            other_values = "_".join([str(ci.value) for ci in other.capacity_indicators])

            categories_match = categories == other_categories
            codes_match = codes == other_codes
            values_match = values == other_values

            return categories_match and codes_match and values_match
        else:
            return False

    def __hash__(self):
        """
        Allows using capacity indicator vectors (civs) as keys in dictionaries.
        """
        categories_string = "_".join([ci.category for ci in self.capacity_indicators])
        codes_sting = "_".join([ci.code for ci in self.capacity_indicators])
        values_string = "_".join([str(ci.value) for ci in self.capacity_indicators])

        return hash(("categories", categories_string, "codes", codes_sting, "values", values_string))


    def reset(self):
        """
        Reset the entire capacity indicator vector at once in order to correct capacity indicator values if necessary
        (checked in the setter) after mutation or recombination.
        e.g. if the capacity indicators of a given category overdimensioned
        """
        self.capacity_indicators = self.capacity_indicators

        return self

    def get_cat(self, category):
        """
        Get values of all capacity indicators corresponding to the chosen supply system category.
        """
        if category not in ['primary', 'secondary', 'tertiary']:
            raise ValueError(f"The indicated supply system category ({category}) doesn't exist.")
        else:
            values_of_cat = [self.capacity_indicators[i].value for i in range(len(self))
                             if self.capacity_indicators[i].category == category]
            return values_of_cat

    def set_cat(self, category, new_values):
        """
        Set values of all capacity indicators corresponding to the chosen supply system category.
        """
        if category not in ['primary', 'secondary', 'tertiary']:
            raise ValueError(f"The indicated supply system category ({category}) doesn't exist.")
        else:
            new_val_vector = []
            for cat in ['primary', 'secondary', 'tertiary']:
                if cat == category:
                    new_val_vector += new_values
                else:
                    new_val_vector += self.get_cat(cat)
            self.values = new_val_vector

    def matches_structure(self, other_civ):
        """
        Check if the capacity indicator vector matches the structure of another capacity indicator vector.
        """
        if isinstance(other_civ, CapacityIndicatorVector):
            # transform the capacity indicator vector's categories and codes into strings
            categories = "_".join([ci.category for ci in self.capacity_indicators])
            other_categories = "_".join([ci.category for ci in other_civ.capacity_indicators])
            codes = "_".join([ci.code for ci in self.capacity_indicators])
            other_codes = "_".join([ci.code for ci in other_civ.capacity_indicators])

            # check if the categories and codes match
            categories_match = categories == other_categories
            codes_match = codes == other_codes

            return categories_match and codes_match
        else:
            return False


    def _categories_overdimensioned(self, new_capacity_indicator_values):
        """
        Check if the component categories in a list of new capacity indicators are overdimensioned.
        """
        categories_overdimensioned  = []

        for category in ['primary', 'secondary', 'tertiary']:
            if any([capacity_indicator.category == category for capacity_indicator in self.capacity_indicators]):
                main_ec_list = list(set(self.dependencies[category].keys()))
                category_overdimensioned = any([self._values_breach_upper_bound(category,
                                                                                energy_carrier,
                                                                                new_capacity_indicator_values)
                                                for energy_carrier in main_ec_list])
                categories_overdimensioned.append(category_overdimensioned)

        return categories_overdimensioned

    def _values_breach_upper_bound(self, category, energy_carrier, new_capacity_indicator_values):
        """
        Check if the values of a list of capacity indicators of a given category and with a given
        main energy carrier (MEC) are overdimensioned (i.e. cumulated capacity of the component group would exceed the
        maximum demand required by upstream components by more than a factor of X).
        """
        upper_bound = self._get_upper_bound(category, energy_carrier, new_capacity_indicator_values)
        cumulated_ci_values = sum([capacity_indicator_value
                                   for i, capacity_indicator_value in enumerate(new_capacity_indicator_values)
                                   if (self.capacity_indicators[i].category == category) and
                                   (self.capacity_indicators[i].main_energy_carrier == energy_carrier)])

        upper_bound_breached = round(cumulated_ci_values, 2) > \
                               round(upper_bound * CapacityIndicatorVector._overdimensioning_factor, 2)

        return upper_bound_breached

    def _get_upper_bound(self, category, energy_carrier, capacity_indicator_values):
        """
        Calculate the upper bound of cumulated capacity indicator values for a given category and
        main energy carrier (MEC), i.e.:
            1. 1 for primary components, or
            2. sum y_i * c_i for secondary/tertiary components, where:
                - y_i is the capacity indicator value of their upstream component and
                - c_i is the associated dependency factor
        """
        if category == 'primary':
            upper_bound = 1
        elif category in ['secondary', 'tertiary']:
            upper_bound = sum([factor * [ci_value
                                         for i, ci_value in enumerate(capacity_indicator_values)
                                         if self.capacity_indicators[i].code == dependency][0]
                               for dependency, factor
                               in zip(self.dependencies[category][energy_carrier]['components'],
                                      self.dependencies[category][energy_carrier]['factors'])])
        else:
            raise ValueError(f"The indicated supply system category ({category}) doesn't exist.")

        return round(upper_bound, 2)

    def _correct_values(self, new_capacity_indicator_values):
        """
        Correct a list of tentative CapacityIndicatorVector values by following these steps:
            1. Find group of components that are part of the same category and have the same main energy carrier.
            2. Determine if the cumulative capacity indicator values of these groups meet the required upper bound.
            3. If not, while the group does not meet the upper bound:
                a) identify the lowest non-zero capacity indicator value in that group (if multiple, chose one at random)
                b) lower that value (minimum 0) so that the sum of all values in that group meets the upper bound.
        """
        # Step 1
        component_categories = list(set([ci.category for ci in self.capacity_indicators]))
        main_energy_carriers_in_cat = {category: list(set([ci.main_energy_carrier
                                                           for ci in self.capacity_indicators
                                                           if ci.category == category]))
                                       for category in component_categories}

        # Step 2
        overdimensioned_groups = [{'category': category, 'main_ec': main_ec}
                                 for category, main_ecs in main_energy_carriers_in_cat.items()
                                 for main_ec in main_ecs
                                 if self._values_breach_upper_bound(category, main_ec, new_capacity_indicator_values)]

        # Step 3
        while overdimensioned_groups:
            for group in overdimensioned_groups:
                while self._values_breach_upper_bound(group['category'], group['main_ec'],
                                                      new_capacity_indicator_values):
                    # Step 3a
                    non_zero_ci_values_in_group = {self.capacity_indicators[i].code: ci_value
                                                   for i, ci_value in enumerate(new_capacity_indicator_values)
                                                   if (self.capacity_indicators[i].category == group['category']) and
                                                   (self.capacity_indicators[i].main_energy_carrier == group['main_ec'])
                                                   and
                                                   (ci_value > 0)}
                    lowest_ci_components = [component for component, value in non_zero_ci_values_in_group.items()
                                            if value == min(non_zero_ci_values_in_group.values())]
                    component_to_resize = random.choice(lowest_ci_components)

                    # Step 3b
                    upper_bound = self._get_upper_bound(group['category'], group['main_ec'],
                                                        new_capacity_indicator_values)
                    odf_corrected_bound = upper_bound * CapacityIndicatorVector._overdimensioning_factor
                    corrected_ci_value = min(non_zero_ci_values_in_group.values()) - \
                                         (sum(non_zero_ci_values_in_group.values()) - odf_corrected_bound)
                    new_capacity_indicator_values = [ci_value
                                                     if not self.capacity_indicators[i].code == component_to_resize
                                                     else max(corrected_ci_value, 0)
                                                     for i, ci_value in enumerate(new_capacity_indicator_values)]

            # check if the changing the CI-values in one category have led to overdimensioning in a downstream category
            overdimensioned_groups = [{'category': category, 'main_ec': main_ec}
                                      for category, main_ecs in main_energy_carriers_in_cat.items()
                                      for main_ec in main_ecs
                                      if self._values_breach_upper_bound(category, main_ec,
                                                                         new_capacity_indicator_values)]

        return new_capacity_indicator_values

    @staticmethod
    def generate(civ_structure, method='random', civ_memory=None, max_system_demand=None):
        """
        Generate a new capacity indicator vector randomly.
        :param civ_structure: structure of the capacity indicator vector (i.e. defined codes and categories attributes)
        :param method: method of generation of the capacity indicators values
        :param civ_memory: memory of previously found optimal capacity indicator vectors
        :param max_system_demand: maximum supply system demand
        """
        civ = copy.deepcopy(civ_structure)

        if method == 'random' or \
                (method == 'from_memory' and civ_memory.recall_optimal_civs(max_system_demand, civ) is None):
            i = 0
            while i <= 10:
                try:
                    civ.values = [random.randint(0, 100) / 100 for _ in civ_structure]
                except ValueError:
                    i += 1
                    continue
                break
        elif method == 'from_memory':
            civ.values = civ_memory.recall_optimal_civs(max_system_demand, civ)
        else:
            if civ_memory not in ['random', 'from_memory']:
                raise ValueError(f"Method {method} not implemented.")

        return civ.capacity_indicators

    @staticmethod
    def mutate(civ, algorithm=None):
        """
        Mutate a capacity indicator vector (inplace) based on the chosen mutation algorithm.
        """
        if algorithm.mutation == "UniformBounded":  # by dividing by setting low=0, up=100 and dividing by 0)
            i = 0
            while i <= 0:
                try:
                    civ_values_percentages = np.array(civ.values) * 100
                    mut_percentages = tools.mutUniformInt(civ_values_percentages, low=0, up=100, indpb=algorithm.mut_prob)
                    civ.values = list(np.array(mut_percentages[0]) / 100)
                except ValueError:
                    i += 1
                    continue
                break
            mutated_civ = tuple([civ])
        elif algorithm.mutation == "PolynomialBounded":
            mutated_civ = tools.mutPolynomialBounded(civ, eta=algorithm.mut_eta, low=0, up=1, indpb=algorithm.mut_prob)
        else:
            raise ValueError(f"The chosen mutation method ({algorithm.mutation}) has not been implemented for "
                             f"capacity indicator vectors.")

        # reset to correct potential format of the capacity indicator vector
        mutated_civ[0].reset()

        return mutated_civ

    @staticmethod
    def mate(civ_1, civ_2, algorithm=None):
        """
        Recombine two capacity indicator vectors (inplace) based on the chosen crossover algorithm
        """
        if algorithm.crossover == "OnePoint":
            recombined_civs = tools.cxOnePoint(civ_1, civ_2)
        elif algorithm.crossover == "TowPoint":
            recombined_civs = tools.cxTwoPoint(civ_1, civ_2)
        elif algorithm.crossover == "Uniform":
            recombined_civs = tools.cxUniform(civ_1, civ_2, indpb=algorithm.cx_prob)
        else:
            raise ValueError(f"The chosen crossover method ({algorithm.crossover}) has not been implemented for "
                             f"capacity indicator vectors.")

        # reset to correct potential error in format of the capacity indicator vectors
        recombined_civs[0].reset()
        recombined_civs[1].reset()

        return recombined_civs

class CapacityIndicatorVectorMemory(object):

    def __init__(self, max_district_energy_demand=None, nbr_of_brackets=20):

        self.max_district_energy_demand = max_district_energy_demand
        self.nbr_of_brackets = nbr_of_brackets

        if max_district_energy_demand:
            self.best_capacity_indicator_vectors = self._create_brackets(nbr_of_brackets)
        else:
            self.best_capacity_indicator_vectors = None

    def _create_brackets(self, nbr_of_brackets, rounding_decimal=3):
        """
        Create brackets for the district energy demand for which the best capacity indicator vectors shall be stored.
        """
        bracket_edges = np.linspace(0, self.max_district_energy_demand, nbr_of_brackets + 1)
        bracket_medians = (bracket_edges[1:] + bracket_edges[:-1]) / 2
        bracket_medians = [round(median, rounding_decimal) for median in bracket_medians]

        return {median: [] for median in bracket_medians}

    def _relevant_bracket(self, district_energy_demand):
        """
        Find the bracket in which the district energy demand falls.
        """
        bracket_medians_list = list(self.best_capacity_indicator_vectors.keys())
        diff_with_bracket_medians = [abs(district_energy_demand - bracket_median) for bracket_median in bracket_medians_list]
        bracket_median = bracket_medians_list[diff_with_bracket_medians.index(min(diff_with_bracket_medians))]

        return bracket_median

    def update(self, optimal_supply_systems):
        """
        Store the optimal capacity indicator vectors in the bracket closest to the max supply system energy demand.

        :param optimal_supply_systems: list of optimal supply systems
        :type optimal_supply_systems: list of <cea.optimization_new.supplySystem>-SupplySystem objects
        """
        # Find the bracket median closest to the max district energy demand and clear the list of optimal capacity
        # indicator vectors in that bracket
        max_system_demand = max(optimal_supply_systems[0].demand_energy_flow.profile)
        bracket_median = self._relevant_bracket(max_system_demand)
        bracket_medians_list = list(self.best_capacity_indicator_vectors.keys())
        former_optimal_civs = self.best_capacity_indicator_vectors[bracket_median]
        self.best_capacity_indicator_vectors[bracket_median] = []

        # Store the new optimal capacity indicator vectors in the bracket
        for optimal_supply_system in optimal_supply_systems:
            self.best_capacity_indicator_vectors[bracket_median].append(optimal_supply_system.capacity_indicator_vector)

        # Fill up to two adjacent empty brackets with the same optimal capacity indicator vectors
        median_index = bracket_medians_list.index(bracket_median)

        lower_index = median_index - 1
        for i in range(2):
            if lower_index < 0:  # Prevent index error
                break

            lower_bracket_median = bracket_medians_list[lower_index]

            if i > 0 and lower_bracket_median > bracket_median:
                break # Quit in case the lower index is out of bounds, i.e. loops around and fetches the highest bracket

            if (self.best_capacity_indicator_vectors[lower_bracket_median]
                    and self.best_capacity_indicator_vectors[lower_bracket_median] != former_optimal_civs):
                break

            self.best_capacity_indicator_vectors[lower_bracket_median] = \
                self.best_capacity_indicator_vectors[bracket_median]

            lower_index -= 1

        upper_index = median_index + 1
        for i in range(2):
            if upper_index >= len(bracket_medians_list):  # Prevent index error
                break

            upper_bracket_median = bracket_medians_list[upper_index]

            if i > 0 and upper_bracket_median < bracket_median:
                break # Quit in case the higher index is out of bounds, i.e. loops around and fetches the lowest bracket

            if (self.best_capacity_indicator_vectors[upper_bracket_median]
                    and self.best_capacity_indicator_vectors[upper_bracket_median] != former_optimal_civs):
                break

            self.best_capacity_indicator_vectors[upper_bracket_median] = \
                self.best_capacity_indicator_vectors[bracket_median]

            upper_index += 1

    def recall_optimal_civs(self, max_system_demand, current_civ):
        """
        Recall the optimal capacity indicator vectors from the bracket closest to the max supply system energy demand
        and return one of them at random.

        :param max_system_demand: maximum supply system energy demand for any given time step
        :type max_system_demand: float
        :param current_civ: the current capacity indicator vector
        :type current_civ: <CapacityIndicatorVector>-object
        """
        diff_with_bracket_medians = [abs(max_system_demand - bracket_median)
                                     for bracket_median in self.best_capacity_indicator_vectors.keys()]
        bracket_median = list(self.best_capacity_indicator_vectors.keys())[diff_with_bracket_medians.
                            index(min(diff_with_bracket_medians))]
        matching_civs = self.find_matches(current_civ, bracket_median)

        if matching_civs:
            randomly_selected_civ = random.choice(matching_civs)
            return randomly_selected_civ.values
        else:
            return None

    def find_matches(self, current_civ, bracket_median):
        if not self.best_capacity_indicator_vectors[bracket_median]:
            return None
        else:
            matching_civs = [civ for civ in self.best_capacity_indicator_vectors[bracket_median]
                             if civ.matches_structure(current_civ)]
            return matching_civs

    def clear(self):
        """
        Clear the list of best capacity indicator vectors in all brackets.
        """
        self.best_capacity_indicator_vectors = {median: [] for median in self.best_capacity_indicator_vectors.keys()}

    def consolidate(self, more_civ_memory):

        if not self.max_district_energy_demand:
            self.max_district_energy_demand = more_civ_memory.max_district_energy_demand
            self.nbr_of_brackets = more_civ_memory.nbr_of_brackets
            self.best_capacity_indicator_vectors = self._create_brackets(self.nbr_of_brackets)

        for bracket_median in self.best_capacity_indicator_vectors.keys():
            # combine the two lists of capacity indicator vectors...
            combined_civs = self.best_capacity_indicator_vectors[bracket_median] + \
                            more_civ_memory.best_capacity_indicator_vectors[bracket_median]
            # ...and remove duplicates...
            combined_civs = list(set(combined_civs))
            # ...before finding the non-dominated set of capacity indicator vectors among them
            if combined_civs:
                self.best_capacity_indicator_vectors[bracket_median] = \
                    tools.emo.sortLogNondominated(combined_civs, 100, first_front_only=True)
            else:
                self.best_capacity_indicator_vectors[bracket_median] = []

