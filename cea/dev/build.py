"""
Build a new CEA installer for the current version. This script runs a bunch of commands necessary to create a new
CEA installer - it will run a long time. It _expects_ to be run in a development version of CEA (i.e. ``pip install -e``
was used to install cityenergyanalyst from the repo.

- create a conda environment for the version (unless already exists, then use that)
- install cea to that environment
- (bonus points: install a default list of cea plugins)
- conda-pack that environment to the setup Dependencies folder
- yarn dist:dir the GUI
"""

import cea.api
import cea.config
import cea.inputlocator

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2020, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(config):
    """
    Build the CEA.
    """
    cea.api.conda_env_create(config)


if __name__ == '__main__':
    main(cea.config.Configuration())
