from __future__ import division
from __future__ import print_function

"""
Start the cea-dashboard webserver. You need to have installed the cea_dashboard project first.
"""

import cea.config


def main(config):
    try:
        import cea_dashboard.dashboard
    except ImportError:
        print('ERROR: package cea_dashboard not found. Please install it first')
        return

    config.restricted_to = None  # allow access to the whole config file
    cea_dashboard.dashboard.main(config)


if __name__ == '__main__':
    main(cea.config.Configuration())