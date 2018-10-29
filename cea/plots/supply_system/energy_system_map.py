"""
Implementation of the "Energy System Map" plot for the "Supply System" category.
"""
from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class EnergySystemMapPlot(cea.plots.supply_system.SupplySystemPlotBase):
    def __init__(self, config, locator, **parameters):
        super(EnergySystemMapPlot, self).__init__(config, locator, **parameters)

    def plot(self, auto_open=False):
        super(EnergySystemMapPlot, self).plot(auto_open)

    def plot_div(self):
        return super(EnergySystemMapPlot, self).plot_div()


def main(config):
    """
    Run the plot for default parameters (as specified in the config object).

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    EnergySystemMapPlot(config, locator, buildings=None).plot(auto_open=True)


if __name__ == '__main__':
    main(cea.config.Configuration())
