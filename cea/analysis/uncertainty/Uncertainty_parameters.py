" This file is used to generate various scenarios which involve uncertainty. Go through README.md"
from __future__ import division

import pandas as pd
import cea.inputlocator
import numpy as np

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def variable_uncertainty_distribution_assignment(locator, number_of_uncertain_scenarios, variable_groups):
    """
    :param locator: path to the scenario
    :type locator: string
    :param number_of_uncertain_scenarios: number of uncertain scenarios
    :type number_of_uncertain_scenarios: int
    :param variable_groups: groups displaying the various sheets present in the excel file
    :type variable_groups: tuple
    :return: saves csv file with the uncertain situations
    """
    # get probability density functions (pdf) of all variable_groups from the uncertainty database
    pdf = pd.concat([pd.read_excel(locator.get_uncertainty_db(), group, axis=1) for group in variable_groups])
    names = pdf['name']

    # Fetching the distribution type and the corresponding variables from the excel sheet
    distribution = []
    mu_c = []
    stdv_alpha = []
    beta = []
    for i in names:
        distribution.append(pdf[pdf['name'] == i]['distribution'].max())
        mu_c.append(pdf[pdf['name'] == i]['mu_c'].max())
        stdv_alpha.append(pdf[pdf['name'] == i]['stdv_alpha'].max())
        beta.append(pdf[pdf['name'] == i]['beta'].max())

    df = pd.DataFrame()
    for i in xrange(len(names)):
        if distribution[i] == 'Beta':  # based on distribution, the random numbers are generated
            a = []
            for j in xrange(number_of_uncertain_scenarios):
                a.append(mu_c[i] * np.random.beta(stdv_alpha[i], beta[i], size=None))
            df[names[i]] = a
        elif distribution[i] == 'Normal':
            a = []
            for j in xrange(number_of_uncertain_scenarios):
                a.append(np.random.normal(loc=mu_c[i], scale=stdv_alpha[i]))
            df[names[i]] = a
    df.to_csv(locator.get_uncertainty_results_folder()+ "\uncertainty.csv")


def run_as_script(scenario_path, number_of_uncertain_scenarios):
    """
    :param scenario_path: path to the scenario path
    :type scenario_path: string
    :param number_of_uncertain_scenarios: total number of uncertain scenarios
    :type number_of_uncertain_scenarios: int
    :return: NULL
    """
   # Importing the excel sheet containing the uncertainty distributions
    locator = cea.inputlocator.InputLocator(scenario_path)
    variable_uncertainty_distribution_assignment(locator, number_of_uncertain_scenarios, variable_groups=('ECONOMIC',) )

    print 'Uncertain Parameters have been generated for the given economic scenarios'

if __name__ == '__main__':
    import cea.config
    config = cea.config.Configuration()
    number_of_uncertain_scenarios = 1000  # The total number of scenarios to be generated
    run_as_script(config.scenario, number_of_uncertain_scenarios)
