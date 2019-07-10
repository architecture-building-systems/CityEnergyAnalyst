"""
Multi criteria decision analysis
"""
from __future__ import division
from __future__ import print_function

import json
import os

import pandas as pd
import numpy as np
import cea.config
import cea.inputlocator
from cea.optimization.lca_calculations import LcaCalculations
from cea.technologies.heat_exchangers import calc_Cinv_HEX
import cea.optimization.distribution.network_optimization_features as network_opt
from cea.analysis.multicriteria.optimization_post_processing.locating_individuals_in_generation_script import \
    locating_individuals_in_generation_script, create_data_address_file
from math import ceil, log

__author__ = "Jimeno A. Fonseca"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Shanshan Hsieh", "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def multi_criteria_main(locator, config):
    # local variables
    generation = config.multi_criteria.generation

    # This calculates the exact path of the individual
    # It might be that this individual was repeated already some generations back
    # so we make sure that a pointer to the right address exists first
    if not os.path.exists(locator.get_address_of_individuals_of_a_generation(generation)):
        data_address = locating_individuals_in_generation_script(generation, locator)
    else:
        data_address = pd.read_csv(locator.get_address_of_individuals_of_a_generation(generation))

    individual_list = preprocessing_generations_data(locator, generation)
    compiled_data_df = pd.DataFrame()
    for i, individual in enumerate(individual_list):
        new_data_address = data_address[data_address['individual_list'] == individual]
        generation_number = new_data_address['generation_number_address'].values[0]
        individual_number = new_data_address['individual_number_address'].values[0]
        df_current_individual = pd.read_csv(locator.get_optimization_slave_total_performance(individual_number, generation_number))
        compiled_data_df = compiled_data_df.append(df_current_individual, ignore_index=True)

    compiled_data_df = compiled_data_df.assign(individual=individual_list)

    # normalize data
    compiled_data_df = normalize_compiled_data(compiled_data_df)
    # rank data
    compiled_data_df = rank_normalized_data(compiled_data_df, config)

    compiled_data_df.to_csv(locator.get_multi_criteria_analysis(generation))
    return

def rank_normalized_data(compiled_data_df, config):
    compiled_data_df['TAC_rank'] = compiled_data_df['normalized_TAC'].rank(ascending=True)
    compiled_data_df['GHG_rank'] = compiled_data_df['normalized_emissions'].rank(ascending=True)
    compiled_data_df['PEN_rank'] = compiled_data_df['normalized_prim'].rank(ascending=True)
    ## user defined mcda
    compiled_data_df['user_MCDA'] = compiled_data_df['normalized_Capex_total'] * \
                                    config.multi_criteria.capextotal * \
                                    config.multi_criteria.economicsustainability + \
                                    compiled_data_df['normalized_Opex'] * \
                                    config.multi_criteria.opex * config.multi_criteria.economicsustainability + \
                                    compiled_data_df['normalized_TAC'] * \
                                    config.multi_criteria.annualizedcosts * config.multi_criteria.economicsustainability + \
                                    compiled_data_df['normalized_emissions'] * \
                                    config.multi_criteria.emissions * config.multi_criteria.environmentalsustainability + \
                                    compiled_data_df['normalized_prim'] * \
                                    config.multi_criteria.primaryenergy * config.multi_criteria.environmentalsustainability
    compiled_data_df['user_MCDA_rank'] = compiled_data_df['user_MCDA'].rank(ascending=True)
    return compiled_data_df


def normalize_compiled_data(compiled_data_df):
    # TAC
    if (max(compiled_data_df['TAC_sys_USD']) - min(compiled_data_df['TAC_sys_USD'])) > 1E-8:
        normalized_TAC = (compiled_data_df['TAC_sys_USD'] - min(compiled_data_df['TAC_sys_USD'])) / (
                max(compiled_data_df['TAC_sys_USD']) - min(compiled_data_df['TAC_sys_USD']))
    else:
        normalized_TAC = [1] * len(compiled_data_df['TAC_sys_USD'])
    # emission
    if (max(compiled_data_df['GHG_sys_tonCO2']) - min(compiled_data_df['GHG_sys_tonCO2'])) > 1E-8:
        normalized_emissions = (compiled_data_df['GHG_sys_tonCO2'] - min(
            compiled_data_df['GHG_sys_tonCO2'])) / (
                                       max(compiled_data_df['GHG_sys_tonCO2']) - min(
                                   compiled_data_df['GHG_sys_tonCO2']))
    else:
        normalized_emissions = [1] * len(compiled_data_df['GHG_sys_tonCO2'])
    # primary energy
    if (max(compiled_data_df['PEN_sys_MJoil']) - min(compiled_data_df['PEN_sys_MJoil'])) > 1E-8:
        normalized_prim = (compiled_data_df['PEN_sys_MJoil'] - min(compiled_data_df['PEN_sys_MJoil'])) / (
                max(compiled_data_df['PEN_sys_MJoil']) - min(compiled_data_df['PEN_sys_MJoil']))
    else:
        normalized_prim = [1] * len(compiled_data_df['PEN_sys_MJoil'])
    # capex
    if (max(compiled_data_df['Capex_total_sys_USD']) - min(compiled_data_df['Capex_total_sys_USD'])) > 1E-8:
        normalized_Capex_total = (compiled_data_df['Capex_total_sys_USD'] - min(compiled_data_df['Capex_total_sys_USD'])) / (
                max(compiled_data_df['Capex_total_sys_USD']) - min(compiled_data_df['Capex_total_sys_USD']))
    else:
        normalized_Capex_total = [1] * len(compiled_data_df['Capex_total_sys_USD'])
    # opex
    if (max(compiled_data_df['Opex_a_sys_USD']) - min(compiled_data_df['Opex_a_sys_USD'])) > 1E-8:
        normalized_Opex = (compiled_data_df['Opex_a_sys_USD'] - min(compiled_data_df['Opex_a_sys_USD'])) / (
                max(compiled_data_df['Opex_a_sys_USD']) - min(compiled_data_df['Opex_a_sys_USD']))
    else:
        normalized_Opex = [1] * len(compiled_data_df['Opex_a_sys_USD'])

    compiled_data_df = compiled_data_df.assign(normalized_TAC=normalized_TAC)
    compiled_data_df = compiled_data_df.assign(normalized_emissions=normalized_emissions)
    compiled_data_df = compiled_data_df.assign(normalized_prim=normalized_prim)
    compiled_data_df = compiled_data_df.assign(normalized_Capex_total=normalized_Capex_total)
    compiled_data_df = compiled_data_df.assign(normalized_Opex=normalized_Opex)
    return compiled_data_df


def preprocessing_generations_data(locator, generation_number):
    """
    compile data from all individuals in this generation
    :param locator:
    :param generation_number:
    :return:
    """

    # load data of generation
    with open(locator.get_optimization_checkpoint(generation_number), "rb") as fp:
        data = json.load(fp)

    individual_names = ['ind' + str(i) for i in range(len(data['tested_population_fitness']))]

    return individual_names

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running multicriteria with scenario = %s" % config.scenario)
    print("Running multicriteria for generation = %s" % config.multi_criteria.generation)

    multi_criteria_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
