"""
===========================
Primary energy and CO2 emissions model algorithm for building operation
===========================
J. Fonseca  script development          26.08.15
D. Thomas   formatting and cleaning     27.08.15
D. Thomas   integration in toolbox      27.08.15
J. Fonseca  script redevelopment        19.04.16

"""
from __future__ import division
import pandas as pd
from geopandas import GeoDataFrame as gpdf
import inputlocator

reload(inputlocator)

def lca_mobility():
    locator = inputlocator.InputLocator(scenario_path=r'C:\reference-case\baseline')
    demand = pd.read_csv(locator.get_total_demand())
    print demand['Af_m2']

    print 'test_properties() succeeded'

if __name__ == '__main__':
    lca_mobility()
