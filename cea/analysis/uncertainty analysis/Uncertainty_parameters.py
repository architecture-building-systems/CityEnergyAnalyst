# -*- coding: utf-8 -*-
"""
Global variables - this object contains context information and is expected to be refactored away in future.
"""
import cea.demand.demand_writers
import numpy as np
import cea.inputlocator

# from cea.demand import thermal_loads

__author__ = "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2015, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

def run_as_script(scenario_path):
    import pandas as pd

    # Importing the excel sheet containing the uncertainty distributions
    locator = cea.inputlocator.InputLocator(scenario_path)
    uncertainty_db = pd.read_excel(locator.get_uncertainty_db(), 'ECONOMIC')

    # Fetching the distribution type and the corresponding variables from the excel sheet
    HP_n_distribution = uncertainty_db[uncertainty_db['name'] == 'HP_n']['distribution'].max()  # lifetime [years] distribution 20
    GHP_nHP_distribution = uncertainty_db[uncertainty_db['name'] == 'GHP_nHP']['distribution'].max()  # for the geothermal heat pump default 20
    Boiler_n_distribution = uncertainty_db[uncertainty_db['name'] == 'Boiler_n']['distribution'].max()  # lifetime, after A+W, default 20
    CC_n_distribution = uncertainty_db[uncertainty_db['name'] == 'CC_n']['distribution'].max()  # lifetime default 25
    FC_n_distribution = uncertainty_db[uncertainty_db['name'] == 'FC_n']['distribution'].max()  # years of operation default 10
    PVT_n_distribution = uncertainty_db[uncertainty_db['name'] == 'PVT_n']['distribution'].max()  # years of operation default 20
    CT_a_distribution = uncertainty_db[uncertainty_db['name'] == 'CT_a']['distribution'].max()  # annuity factor default 0.15
    Subst_n_distribution = uncertainty_db[uncertainty_db['name'] == 'Subst_n']['distribution'].max()  # Lifetime after A+W default 20
    ELEC_PRICE_distribution = uncertainty_db[uncertainty_db['name'] == 'ELEC_PRICE']['distribution'].max()  # default 0.2
    NG_PRICE_distribution = uncertainty_db[uncertainty_db['name'] == 'NG_PRICE']['distribution'].max()  # [CHF / wh] # default 0.068
    BG_PRICE_distribution = uncertainty_db[uncertainty_db['name'] == 'BG_PRICE']['distribution'].max()   # [CHF / wh] # default 0.076
    Subst_i_distribution = uncertainty_db[uncertainty_db['name'] == 'Subst_i']['distribution'].max()  # default 0.05
    FC_i_distribution = uncertainty_db[uncertainty_db['name'] == 'FC_i']['distribution'].max()  # interest rate default 0.05
    HP_i_distribution = uncertainty_db[uncertainty_db['name'] == 'HP_i']['distribution'].max()  # interest rate default 0.05
    Boiler_i_distribution = uncertainty_db[uncertainty_db['name'] == 'Boiler_i']['distribution'].max()  # interest rate default 0.05

    if HP_n_distribution == 'Beta':
        HP_n_c = uncertainty_db[uncertainty_db['name'] == 'HP_n']['mu/c'].max()
        HP_n_alpha = uncertainty_db[uncertainty_db['name'] == 'HP_n']['stdv/alpha'].max()
        HP_n_beta = uncertainty_db[uncertainty_db['name'] == 'HP_n']['beta'].max()
    elif HP_n_distribution == 'Normal':
        HP_n_mu = uncertainty_db[uncertainty_db['name'] == 'HP_n']['mu/c'].max()
        HP_n_stdv = uncertainty_db[uncertainty_db['name'] == 'HP_n']['stdv/alpha'].max()

    if GHP_nHP_distribution == 'Beta':
        GHP_nHP_c = uncertainty_db[uncertainty_db['name'] == 'GHP_nHP']['mu/c'].max()
        GHP_nHP_alpha = uncertainty_db[uncertainty_db['name'] == 'GHP_nHP']['stdv/alpha'].max()
        GHP_nHP_beta = uncertainty_db[uncertainty_db['name'] == 'GHP_nHP']['beta'].max()
    elif GHP_nHP_distribution == 'Normal':
        GHP_nHP_mu = uncertainty_db[uncertainty_db['name'] == 'GHP_nHP']['mu/c'].max()
        GHP_nHP_stdv = uncertainty_db[uncertainty_db['name'] == 'GHP_nHP']['stdv/alpha'].max()

    if Boiler_n_distribution == 'Beta':
        Boiler_n_c = uncertainty_db[uncertainty_db['name'] == 'Boiler_n']['mu/c'].max()
        Boiler_n_alpha = uncertainty_db[uncertainty_db['name'] == 'Boiler_n']['stdv/alpha'].max()
        Boiler_n_beta = uncertainty_db[uncertainty_db['name'] == 'Boiler_n']['beta'].max()
    elif Boiler_n_distribution == 'Normal':
        Boiler_n_mu = uncertainty_db[uncertainty_db['name'] == 'Boiler_n']['mu/c'].max()
        Boiler_n_stdv = uncertainty_db[uncertainty_db['name'] == 'Boiler_n']['stdv/alpha'].max()

    if CC_n_distribution == 'Beta':
        CC_n_c = uncertainty_db[uncertainty_db['name'] == 'CC_n']['mu/c'].max()
        CC_n_alpha = uncertainty_db[uncertainty_db['name'] == 'CC_n']['stdv/alpha'].max()
        CC_n_beta = uncertainty_db[uncertainty_db['name'] == 'CC_n']['beta'].max()
    elif CC_n_distribution == 'Normal':
        CC_n_mu = uncertainty_db[uncertainty_db['name'] == 'CC_n']['mu/c'].max()
        CC_n_stdv = uncertainty_db[uncertainty_db['name'] == 'CC_n']['stdv/alpha'].max()

    if FC_n_distribution == 'Beta':
        FC_n_c = uncertainty_db[uncertainty_db['name'] == 'FC_n']['mu/c'].max()
        FC_n_alpha = uncertainty_db[uncertainty_db['name'] == 'FC_n']['stdv/alpha'].max()
        FC_n_beta = uncertainty_db[uncertainty_db['name'] == 'FC_n']['beta'].max()
    elif FC_n_distribution == 'Normal':
        FC_n_mu = uncertainty_db[uncertainty_db['name'] == 'FC_n']['mu/c'].max()
        FC_n_stdv = uncertainty_db[uncertainty_db['name'] == 'FC_n']['stdv/alpha'].max()

    if PVT_n_distribution == 'Beta':
        PVT_n_c = uncertainty_db[uncertainty_db['name'] == 'PVT_n']['mu/c'].max()
        PVT_n_alpha = uncertainty_db[uncertainty_db['name'] == 'PVT_n']['stdv/alpha'].max()
        PVT_n_beta = uncertainty_db[uncertainty_db['name'] == 'PVT_n']['beta'].max()
    elif PVT_n_distribution == 'Normal':
        PVT_n_mu = uncertainty_db[uncertainty_db['name'] == 'PVT_n']['mu/c'].max()
        PVT_n_stdv = uncertainty_db[uncertainty_db['name'] == 'PVT_n']['stdv/alpha'].max()

    if CT_a_distribution == 'Beta':
        CT_a_c = uncertainty_db[uncertainty_db['name'] == 'CT_a']['mu/c'].max()
        CT_a_alpha = uncertainty_db[uncertainty_db['name'] == 'CT_a']['stdv/alpha'].max()
        CT_a_beta = uncertainty_db[uncertainty_db['name'] == 'CT_a']['beta'].max()
    elif CT_a_distribution == 'Normal':
        CT_a_mu = uncertainty_db[uncertainty_db['name'] == 'CT_a']['mu/c'].max()
        CT_a_stdv = uncertainty_db[uncertainty_db['name'] == 'CT_a']['stdv/alpha'].max()

    if Subst_n_distribution == 'Beta':
        Subst_n_c = uncertainty_db[uncertainty_db['name'] == 'Subst_n']['mu/c'].max()
        Subst_n_alpha = uncertainty_db[uncertainty_db['name'] == 'Subst_n']['stdv/alpha'].max()
        Subst_n_beta = uncertainty_db[uncertainty_db['name'] == 'Subst_n']['beta'].max()
    elif Subst_n_distribution == 'Normal':
        Subst_n_mu = uncertainty_db[uncertainty_db['name'] == 'Subst_n']['mu/c'].max()
        Subst_n_stdv = uncertainty_db[uncertainty_db['name'] == 'Subst_n']['stdv/alpha'].max()

    if ELEC_PRICE_distribution == 'Beta':
        ELEC_PRICE_c = uncertainty_db[uncertainty_db['name'] == 'ELEC_PRICE']['mu/c'].max()
        ELEC_PRICE_alpha = uncertainty_db[uncertainty_db['name'] == 'ELEC_PRICE']['stdv/alpha'].max()
        ELEC_PRICE_beta = uncertainty_db[uncertainty_db['name'] == 'ELEC_PRICE']['beta'].max()
    elif ELEC_PRICE_distribution == 'Normal':
        ELEC_PRICE_mu = uncertainty_db[uncertainty_db['name'] == 'ELEC_PRICE']['mu/c'].max()
        ELEC_PRICE_stdv = uncertainty_db[uncertainty_db['name'] == 'ELEC_PRICE']['stdv/alpha'].max()

    if NG_PRICE_distribution == 'Beta':
        NG_PRICE_c = uncertainty_db[uncertainty_db['name'] == 'NG_PRICE']['mu/c'].max()
        NG_PRICE_alpha = uncertainty_db[uncertainty_db['name'] == 'NG_PRICE']['stdv/alpha'].max()
        NG_PRICE_beta = uncertainty_db[uncertainty_db['name'] == 'NG_PRICE']['beta'].max()
    elif NG_PRICE_distribution == 'Normal':
        NG_PRICE_mu = uncertainty_db[uncertainty_db['name'] == 'NG_PRICE']['mu/c'].max()
        NG_PRICE_stdv = uncertainty_db[uncertainty_db['name'] == 'NG_PRICE']['stdv/alpha'].max()

    if BG_PRICE_distribution == 'Beta':
        BG_PRICE_c = uncertainty_db[uncertainty_db['name'] == 'Subst_i']['mu/c'].max()
        BG_PRICE_alpha = uncertainty_db[uncertainty_db['name'] == 'BG_PRICE']['stdv/alpha'].max()
        BG_PRICE_beta = uncertainty_db[uncertainty_db['name'] == 'BG_PRICE']['beta'].max()
    elif BG_PRICE_distribution == 'Normal':
        BG_PRICE_mu = uncertainty_db[uncertainty_db['name'] == 'BG_PRICE']['mu/c'].max()
        BG_PRICE_stdv = uncertainty_db[uncertainty_db['name'] == 'BG_PRICE']['stdv/alpha'].max()

    if Subst_i_distribution == 'Beta':
        Subst_i_c = uncertainty_db[uncertainty_db['name'] == 'Subst_i']['mu/c'].max()
        Subst_i_alpha = uncertainty_db[uncertainty_db['name'] == 'Subst_i']['stdv/alpha'].max()
        Subst_i_beta = uncertainty_db[uncertainty_db['name'] == 'Subst_i']['beta'].max()
    elif Subst_i_distribution == 'Normal':
        Subst_i_mu = uncertainty_db[uncertainty_db['name'] == 'Subst_i']['mu/c'].max()
        Subst_i_stdv = uncertainty_db[uncertainty_db['name'] == 'Subst_i']['stdv/alpha'].max()

    if FC_i_distribution == 'Beta':
        FC_i_c = uncertainty_db[uncertainty_db['name'] == 'FC_i']['mu/c'].max()
        FC_i_alpha = uncertainty_db[uncertainty_db['name'] == 'FC_i']['stdv/alpha'].max()
        FC_i_beta = uncertainty_db[uncertainty_db['name'] == 'FC_i']['beta'].max()
    elif FC_i_distribution == 'Normal':
        FC_i_mu = uncertainty_db[uncertainty_db['name'] == 'FC_i']['mu/c'].max()
        FC_i_stdv = uncertainty_db[uncertainty_db['name'] == 'FC_i']['stdv/alpha'].max()

    if HP_i_distribution == 'Beta':
        HP_i_c = uncertainty_db[uncertainty_db['name'] == 'HP_i']['mu/c'].max()
        HP_i_alpha = uncertainty_db[uncertainty_db['name'] == 'HP_i']['stdv/alpha'].max()
        HP_i_beta = uncertainty_db[uncertainty_db['name'] == 'HP_i']['beta'].max()
    elif HP_i_distribution == 'Normal':
        HP_i_mu = uncertainty_db[uncertainty_db['name'] == 'HP_i']['mu/c'].max()
        HP_i_stdv = uncertainty_db[uncertainty_db['name'] == 'HP_i']['stdv/alpha'].max()

    if Boiler_i_distribution == 'Beta':
        Boiler_i_c = uncertainty_db[uncertainty_db['name'] == 'Boiler_i']['mu/c'].max()
        Boiler_i_alpha = uncertainty_db[uncertainty_db['name'] == 'Boiler_i']['stdv/alpha'].max()
        Boiler_i_beta = uncertainty_db[uncertainty_db['name'] == 'Boiler_i']['beta'].max()
    elif Boiler_i_distribution == 'Normal':
        Boiler_i_mu = uncertainty_db[uncertainty_db['name'] == 'Boiler_i']['mu/c'].max()
        Boiler_i_stdv = uncertainty_db[uncertainty_db['name'] == 'Boiler_i']['stdv/alpha'].max()

    HP_n = []
    GHP_nHP = []
    Boiler_n = []
    CC_n = []
    FC_n = []
    PVT_n = []
    CT_a = []
    Subst_n = []
    ELEC_PRICE = []
    NG_PRICE = []
    BG_PRICE = []
    Subst_i = []
    FC_i = []
    HP_i = []
    Boiler_i = []

    for i in xrange(100):
        if HP_n_distribution == 'Beta':
            HP_n.append(HP_n_c * np.random.beta(HP_n_alpha, HP_n_beta, size = None))
        elif HP_n_distribution == 'Normal':
            HP_n.append(np.random.normal(loc=HP_n_mu, scale=HP_n_stdv))

        if GHP_nHP_distribution == 'Beta':
            GHP_nHP.append(GHP_nHP_c * np.random.beta(GHP_nHP_alpha, GHP_nHP_beta, size = None))
        elif GHP_nHP_distribution == 'Normal':
            GHP_nHP.append(np.random.normal(loc=GHP_nHP_mu, scale=GHP_nHP_stdv))

        if Boiler_n_distribution == 'Beta':
            Boiler_n.append(Boiler_n_c * np.random.beta(Boiler_n_alpha, Boiler_n_beta, size = None))
        elif Boiler_n_distribution == 'Normal':
            Boiler_n.append(np.random.normal(loc=Boiler_n_mu, scale=Boiler_n_stdv))

        if CC_n_distribution == 'Beta':
            CC_n.append(CC_n_c * np.random.beta(CC_n_alpha, CC_n_beta, size = None))
        elif CC_n_distribution == 'Normal':
            CC_n.append(np.random.normal(loc=CC_n_mu, scale=CC_n_stdv))

        if FC_n_distribution == 'Beta':
            FC_n.append(FC_n_c * np.random.beta(FC_n_alpha, FC_n_beta, size = None))
        elif FC_n_distribution == 'Normal':
            FC_n.append(np.random.normal(loc=FC_n_mu, scale=FC_n_stdv))

        if PVT_n_distribution == 'Beta':
            PVT_n.append(PVT_n_c * np.random.beta(PVT_n_alpha, PVT_n_beta, size = None))
        elif PVT_n_distribution == 'Normal':
            PVT_n.append(np.random.normal(loc=PVT_n_mu, scale=PVT_n_stdv))

        if CT_a_distribution == 'Beta':
            CT_a.append(CT_a_c * np.random.beta(CT_a_alpha, CT_a_beta, size = None))
        elif CT_a_distribution == 'Normal':
            CT_a.append(np.random.normal(loc=CT_a_mu, scale=CT_a_stdv))

        if Subst_n_distribution == 'Beta':
            Subst_n.append(Subst_n_c * np.random.beta(Subst_n_alpha, Subst_n_beta, size = None))
        elif Subst_n_distribution == 'Normal':
            Subst_n.append(np.random.normal(loc=Subst_n_mu, scale=Subst_n_stdv))

        if ELEC_PRICE_distribution == 'Beta':
            ELEC_PRICE.append(ELEC_PRICE_c * np.random.beta(ELEC_PRICE_alpha, ELEC_PRICE_beta, size = None))
        elif ELEC_PRICE_distribution == 'Normal':
            ELEC_PRICE.append(np.random.normal(loc=ELEC_PRICE_mu, scale=ELEC_PRICE_stdv))

        if NG_PRICE_distribution == 'Beta':
            NG_PRICE.append(NG_PRICE_c * np.random.beta(NG_PRICE_alpha, NG_PRICE_beta, size = None))
        elif NG_PRICE_distribution == 'Normal':
            NG_PRICE.append(np.random.normal(loc=NG_PRICE_mu, scale=NG_PRICE_stdv))

        if BG_PRICE_distribution == 'Beta':
            BG_PRICE.append(BG_PRICE_c * np.random.beta(BG_PRICE_alpha, BG_PRICE_beta, size = None))
        elif BG_PRICE_distribution == 'Normal':
            BG_PRICE.append(np.random.normal(loc=BG_PRICE_mu, scale=BG_PRICE_stdv))

        if Subst_i_distribution == 'Beta':
            Subst_i.append(Subst_i_c * np.random.beta(Subst_i_alpha, Subst_i_beta, size = None))
        elif Subst_i_distribution == 'Normal':
            Subst_i.append(np.random.normal(loc=Subst_i_mu, scale=Subst_i_stdv))

        if FC_i_distribution == 'Beta':
            FC_i.append(FC_i_c * np.random.beta(FC_i_alpha, FC_i_beta, size=None))
        elif FC_i_distribution == 'Normal':
            FC_i.append(np.random.normal(loc=FC_i_mu, scale=FC_i_stdv))

        if HP_i_distribution == 'Beta':
            HP_i.append(HP_i_c * np.random.beta(HP_i_alpha, HP_i_beta, size=None))
        elif HP_i_distribution == 'Normal':
            HP_i.append(np.random.normal(loc=HP_i_mu, scale=HP_i_stdv))

        if Boiler_i_distribution == 'Beta':
            Boiler_i.append(Boiler_i_c * np.random.beta(Boiler_i_alpha, Boiler_i_beta, size=None))
        elif Boiler_i_distribution == 'Normal':
            Boiler_i.append(np.random.normal(loc=Boiler_i_mu, scale=Boiler_i_stdv))

    table = [HP_n, GHP_nHP, Boiler_n, CC_n, FC_n, PVT_n, CT_a, Subst_n, ELEC_PRICE, NG_PRICE, BG_PRICE, Subst_i, FC_i, HP_i, Boiler_i]
    df = pd.DataFrame(table)
    df = df.transpose()
    cols = ['WHP', 'GHP', 'Boiler', 'CC', 'FC', 'PVT', 'CT', 'Substation', 'EP', 'NG', 'BG', 'Subst_IR', 'FC_IR', 'HP_IR', 'Boiler_IR']
    df.columns = cols
    print (df)
    locator.get_uncertainty_parameters()
    df.to_csv(locator.get_optimization_master_results_folder() + "\uncertainty.csv")


    print 'Uncertain Parameters have been generated for the given economic scenarios'

if __name__ == '__main__':
    run_as_script(r'C:\reference-case-zug\baseline')