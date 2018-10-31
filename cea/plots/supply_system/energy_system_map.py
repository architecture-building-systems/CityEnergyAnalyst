"""
Implementation of the "Energy System Map" plot for the "Supply System" category.
"""
from __future__ import division
from __future__ import print_function

import os
import cea.config
import cea.inputlocator
import cea.plots.supply_system

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class EnergySystemMapPlot(cea.plots.supply_system.SupplySystemPlotBase):
    name = "Energy System Map"

    def __init__(self, config, locator, **parameters):
        super(EnergySystemMapPlot, self).__init__(config, locator, **parameters)
        self.output_name_network = "gen{generation}_{individual}".format(generation=self.generation,
                                                                         individual=self.individual)

    def plot(self, auto_open=False):
        print(self.output_path)

    def plot_div(self):
        self._create_thermal_network_layout()

    @property
    def title(self):
        return 'Energy system map for individual {individual} in generation {generation}'.format(
            individual=self.individual, generation=self.generation)

    def _create_thermal_network_layout(self, buildings_data):
        """Run the network layout script to generate the shapefiles for this plot"""
        from cea.technologies.thermal_network.network_layout.main import network_layout
        buildings_data = buildings_data.loc[buildings_data["Type"] == "CENTRALIZED"]
        buildings_connected = buildings_data.Name.values

        # configure layout script to create the new network adn store in the folder inputs.
        restricted_to = self.config.restricted_to  # allow using some config variables outside of the plots system.
        self.config.restricted_to = None
        self.config.network_layout.network_type = self.network_type
        self.config.network_layout.create_plant = True
        self.config.network_layout.buildings = buildings_connected
        network_layout(self.config, self.locator, self.output_name_network)
        self.config.restricted_to = restricted_to

def main(config):
    """
    Run the plot for default parameters (as specified in the config object).

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    assert os.path.exists(config.scenario), 'Scenario not found: %s' % config.scenario
    locator = cea.inputlocator.InputLocator(config.scenario)

    EnergySystemMapPlot(config, locator, buildings=None).plot_div()


if __name__ == '__main__':
    main(cea.config.Configuration())
