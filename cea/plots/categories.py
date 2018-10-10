from __future__ import division
from __future__ import print_function

"""
Lists the plots by category. See ``cea/plots/__init__.py`` for documentation on how plots are organized and
the conventions for adding new plots.
"""

import pkgutil
import importlib

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def list_categories():
    """List all the categories implemented in the CEA"""
    import cea.plots
    for importer, modname, ispkg in pkgutil.iter_modules(cea.plots.__path__, cea.plots.__name__ + '.'):
        if not ispkg:
            continue
        print('module:', modname)
        module = importlib.import_module(modname)
        try:
            yield PlotCategory(module.__name__.split('.')[-1], module.label)
        except:
            # this module does not follow the conventions outlined in ``cea.plots.__init__.py`` and will be
            # ignored
            continue


class PlotCategory(object):
    """Contains the data of a plot category."""
    def __init__(self, name, label):
        self.name = name
        self.label = label


if __name__ == '__main__':
    for category in list_categories():
        print(category.name, ':', category.label)