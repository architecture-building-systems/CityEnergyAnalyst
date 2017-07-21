import pandas as pd
from scipy.stats.distributions import triang
from scipy.stats.distributions import norm
from scipy.stats.distributions import uniform
from pyDOE import lhs


def latin_sampler(locator, num_samples, variables, variable_groups = ('ENVELOPE', 'INDOOR_COMFORT', 'INTERNAL_LOADS')):


    # get probability density function PDF of variables of interest
    database = pd.concat([pd.read_excel(locator.get_uncertainty_db(), group, axis=1)
                                                for group in variable_groups])
    pdf_list = database[database['name'].isin(variables)].reset_index()

    # get number of variables
    num_vars = pdf_list.shape[0] #alternatively use len(variables)

    # get design of experiments
    design = lhs(num_vars, samples=num_samples)
    for i, pdf in enumerate(pdf_list.itertuples()):
        min = pdf.min
        max = pdf.max
        mu = pdf.mu
        stdv = pdf.stdv
        if pdf.distribution == 'triangular':
            design[:, i] = triang(loc=min, c=mu, scale=max).ppf(design[:, i])
        elif pdf.distribution == 'normal':
            design[:, i] = norm(loc=mu, scale=stdv).ppf(design[:, i])
        else: # assume it is uniform
            design[:, i] = uniform(loc=min, scale=max).ppf(design[:, i])

    return design