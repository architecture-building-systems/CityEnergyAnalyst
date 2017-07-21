import pandas as pd
from scipy.stats.distributions import triang
from scipy.stats.distributions import norm
from scipy.stats.distributions import uniform
from pyDOE import lhs


def latin_sampler(locator, num_samples, variables, variable_groups = ('ENVELOPE', 'INDOOR_COMFORT', 'INTERNAL_LOADS')):


    # get probability density function PDF of variables of interest
    database = pd.concat([pd.read_excel(locator.get_uncertainty_db(), group, axis=1)
                                                for group in variable_groups])
    pdf_list = database[database['name'].isin(variables)].set_index('name')

    # get number of variables
    num_vars = pdf_list.shape[0] #alternatively use len(variables)

    # get design of experiments
    design = lhs(num_vars, samples=num_samples)
    for i, variable in enumerate(variables):
        distribution = pdf_list.loc[variable, 'distribution']
        min = pdf_list.loc[variable,'min']
        max = pdf_list.loc[variable,'min']
        mu = pdf_list.loc[variable,'mu']
        stdv = pdf_list.loc[variable,'stdv']
        if distribution == 'triangular':
            design[:, i] = triang(loc=min, c=mu, scale=max).ppf(design[:, i])
        elif distribution == 'normal':
            design[:, i] = norm(loc=mu, scale=stdv).ppf(design[:, i])
        else: # assume it is uniform
            design[:, i] = uniform(loc=min, scale=max).ppf(design[:, i])

    return design