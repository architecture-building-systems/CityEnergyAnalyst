from __future__ import division
from __future__ import print_function

"""
Start the cea-dashboard webserver. You need to have installed the cea_dashboard project first.
"""

import cea.config
import cea.dashboard.dashboard


def main(config):
    config.restricted_to = None  # allow access to the whole config file
    cea.dashboard.dashboard.main(config)


if __name__ == '__main__':
    main(cea.config.Configuration())