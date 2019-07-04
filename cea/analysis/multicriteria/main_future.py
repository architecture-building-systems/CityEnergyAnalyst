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

__author__ = "Sreepathi Bhargava Krishna"
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

    #TODO: data address

    data_processed = preprocessing_generations_data(locator, generation)
    compiled_data_df = pd.DataFrame()
    individual_list = data_processed['Name']
    for i, individual in enumerate(individual_list):
        data_address = data_address[data_address['individual_list'] == individual]
        generation_number = data_address['generation_number_address'].values[0]
        individual_number = data_address['individual_number_address'].values[0]
        df_current_individual = pd.DataFrame(data_processed.loc[i])
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
                                    config.multi_criteria.primaryenergy * config.multi_criteria.environmentalsustainability + \
                                    compiled_data_df['normalized_renewable_share'] * \
                                    config.multi_criteria.renewableshare * config.multi_criteria.socialsustainability
    compiled_data_df['user_MCDA_rank'] = compiled_data_df['user_MCDA'].rank(ascending=True)
    return compiled_data_df


def normalize_compiled_data(compiled_data_df):
    # TAC
    if (max(compiled_data_df['TAC_MioUSD']) - min(compiled_data_df['TAC_MioUSD'])) > 1E-8:
        normalized_TAC = (compiled_data_df['TAC_MioUSD'] - min(compiled_data_df['TAC_MioUSD'])) / (
                max(compiled_data_df['TAC_MioUSD']) - min(compiled_data_df['TAC_MioUSD']))
    else:
        normalized_TAC = [1] * len(compiled_data_df['TAC_MioUSD'])
    # emission
    if (max(compiled_data_df['GHG_ktonCO2']) - min(compiled_data_df['GHG_ktonCO2'])) > 1E-8:
        normalized_emissions = (compiled_data_df['GHG_ktonCO2'] - min(
            compiled_data_df['GHG_ktonCO2'])) / (
                                       max(compiled_data_df['GHG_ktonCO2']) - min(
                                   compiled_data_df['GHG_ktonCO2']))
    else:
        normalized_emissions = [1] * len(compiled_data_df['GHG_ktonCO2'])
    # primary energy
    if (max(compiled_data_df['PEN_TJoil']) - min(compiled_data_df['PEN_TJoil'])) > 1E-8:
        normalized_prim = (compiled_data_df['PEN_TJoil'] - min(compiled_data_df['PEN_TJoil'])) / (
                max(compiled_data_df['PEN_TJoil']) - min(compiled_data_df['PEN_TJoil']))
    else:
        normalized_prim = [1] * len(compiled_data_df['PEN_TJoil'])
    # capex
    if (max(compiled_data_df['Capex_total_Mio']) - min(compiled_data_df['Capex_total_Mio'])) > 1E-8:
        normalized_Capex_total = (compiled_data_df['Capex_total_Mio'] - min(compiled_data_df['Capex_total_Mio'])) / (
                max(compiled_data_df['Capex_total_Mio']) - min(compiled_data_df['Capex_total_Mio']))
    else:
        normalized_Capex_total = [1] * len(compiled_data_df['Capex_total_Mio'])
    # opex
    if (max(compiled_data_df['Opex_total_Mio']) - min(compiled_data_df['Opex_total_Mio'])) > 1E-8:
        normalized_Opex = (compiled_data_df['Opex_total_Mio'] - min(compiled_data_df['Opex_total_Mio'])) / (
                max(compiled_data_df['Opex_total_Mio']) - min(compiled_data_df['Opex_total_Mio']))
    else:
        normalized_Opex = [1] * len(compiled_data_df['Opex_total_Mio'])
    # renewable energy share
    if (max(compiled_data_df['RES_el']) - min(
            compiled_data_df['RES_el'])) > 1E-8:
        normalized_renewable_share = (compiled_data_df['RES_el'] - min(
            compiled_data_df['RES_el'])) / (
                                             max(compiled_data_df['RES_el']) - min(
                                         compiled_data_df['RES_el']))
    else:
        normalized_renewable_share = [1] * compiled_data_df['RES_el']
    compiled_data_df = compiled_data_df.assign(normalized_TAC=normalized_TAC)
    compiled_data_df = compiled_data_df.assign(normalized_emissions=normalized_emissions)
    compiled_data_df = compiled_data_df.assign(normalized_prim=normalized_prim)
    compiled_data_df = compiled_data_df.assign(normalized_Capex_total=normalized_Capex_total)
    compiled_data_df = compiled_data_df.assign(normalized_Opex=normalized_Opex)
    compiled_data_df = compiled_data_df.assign(normalized_renewable_share=normalized_renewable_share)
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

    # change units of population (e.g., form kW to MW)
    # convert from USD to millions
    costs_Mio = [round(objectives[0] / 1E6, 2) for objectives in data['tested_population_fitness']]

    # convert from tons to kiloton
    emissions_kiloton = [round(objectives[1] / 1E3, 2) for objectives in data['tested_population_fitness']]

    # convert from MJoil to Terajoules
    prim_energy_TJ = [round(objectives[2] / 1E6, 2) for objectives in data['tested_population_fitness']]

    individual_names = ['ind' + str(i) for i in range(len(costs_Mio))]
    df_population = pd.DataFrame({'individual': individual_names, 'TAC_MioUSD': costs_Mio,
                                  'GHG_ktonCO2': emissions_kiloton,
                                  'PEN_TJoil': prim_energy_TJ}).set_index("Name")
    return df_population

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)

    print("Running multicriteria with scenario = %s" % config.scenario)
    print("Running multicriteria for generation = %s" % config.multi_criteria.generation)

    multi_criteria_main(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
