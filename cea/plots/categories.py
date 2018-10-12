from __future__ import division
from __future__ import print_function

"""
Lists the plots by category. See ``cea/plots/__init__.py`` for documentation on how plots are organized and
the conventions for adding new plots.
"""

import pkgutil
import importlib
import inspect
import cea.plots

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
            # only consider subfolders of cea/plots to be categories
            continue
        module = importlib.import_module(modname)
        if not hasattr(module, 'label'):
            # doesn't implement the interface for categories (__init__.py must have a "label" attribute)
            continue
        try:
            yield PlotCategory(module)
        except:
            # this module does not follow the conventions outlined in ``cea.plots.__init__.py`` and will be
            # ignored
            continue


class PlotCategory(object):
    """Contains the data of a plot category."""
    def __init__(self, module):
        self._module = module
        self.name = module.__name__.split('.')[-1]
        self.label = module.label

    @property
    def plots(self):
        self._plots = None

    def _list_plots(self):
        for importer, modname, ispkg in pkgutil.iter_modules(self._module.__path__, self._module.__name__ + '.'):
            if ispkg:
                # only consider modules - not packages
                continue
            module = importlib.import_module(modname)
            for cls_name, cls_object in inspect.getmembers(module, inspect.isclass):
                if cea.plots.PlotBase in inspect.getmro(cls_object):
                    yield cls_object



if __name__ == '__main__':
    for category in list_categories():
        print(category.name, ':', category.label)
        for plot in category._list_plots():
            print('plot:', plot)