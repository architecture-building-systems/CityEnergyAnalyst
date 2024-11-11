"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""



"""
This is a template script - an example of how a CEA script should be set up.

NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (what, why, include literature references)
"""




import os
import cea.config
import cea.inputlocator
from cea.datamanagement.data_initializer import main as intialmain
from cea.datamanagement.archetypes_mapper import main as archMapmain
from cea.datamanagement.surroundings_helper import main as surrmain
from cea.datamanagement.terrain_helper import main as termain
from cea.resources.radiation.main import main as radmain
from cea.demand.demand_main import main as demandmain
from cea.analysis.lca.embodied import main as emissionmain
from cea.analysis.lca.operation import main as operationmain
from cea.datamanagement.zone_helper import main as zmain
from cea.demand.schedule_maker.schedule_maker import main as schedulemain
from cea.datamanagement.streets_helper import geometry_extractor_osm as ge2
from cea.datamanagement.weather_helper import main as mainweather

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def embodiedUpdated(locator, config):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """

    ### data_initializer(locator,databases_path=config.data_initializer.databases_path)
    ### geometry_extractor_osm(locator,config)


    # intialmain(config)
    # archMapmain(config)
    # zmain(config)
    # surrmain(config)
    # termain(config)
    # ge2(locator, config)
    # mainweather(config)

    # archMapmain(config)
    # radmain(config)
    # schedulemain(config)
    # demandmain(config)
    # emissionmain(config)
    # operationmain(config)

    pass
def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line / user interface

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    locator = cea.inputlocator.InputLocator(config.scenario)

    embodiedUpdated(locator, config)


if __name__ == '__main__':
    main(cea.config.Configuration())
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


def template(locator, archetypes):
    """this is where the action happens if it is more than a few lines in ``main``.
    NOTE: ADD YOUR SCRIPT'S DOCUMENTATION HERE (how)
    NOTE: RENAME THIS FUNCTION (SHOULD PROBABLY BE THE SAME NAME AS THE MODULE)
    """
    pass


def main(config):
    """
    This is the main entry point to your script. Any parameters used by your script must be present in the ``config``
    parameter. The CLI will call this ``main`` function passing in a ``config`` object after adjusting the configuration
    to reflect parameters passed on the command line / user interface

    :param config:
    :type config: cea.config.Configuration
    :return:
    """
    locator = cea.inputlocator.InputLocator(config.scenario)

    template(locator, config.scenario)


if __name__ == '__main__':
    main(cea.config.Configuration())
