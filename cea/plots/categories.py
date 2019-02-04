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


def is_valid_category(category):
    """True, if category is the name (not the label) of a valid CEA plot category"""
    return category in set(c.name for c in list_categories())


def load_category(category_name):
    """Returns a PlotsCategory object if is_valid_category(category), else None"""
    for c in list_categories():
        if c.name == category_name:
            return c
    return None


def load_plot(category_name, plot_name):
    category = load_category(category_name)
    if category:
        for plot in category.plots:
            if plot.__name__ == plot_name:
                return plot
    return None


def load_plot_by_id(category_name, plot_id):
    """plot_id is a web-friendly way of expressing the plot's name (which is more english friendly)"""
    category = load_category(category_name)
    if category:
        for plot in category.plots:
            if plot.id() == plot_id:
                return plot
    return None


class PlotCategory(object):
    """Contains the data of a plot category."""
    def __init__(self, module):
        self._module = module
        self.name = module.__name__.split('.')[-1]
        self.label = module.label

    @property
    def plots(self):
        """

        :return: Generator[PlotBase]
        """
        for importer, modname, ispkg in pkgutil.iter_modules(self._module.__path__, self._module.__name__ + '.'):
            if ispkg:
                # only consider modules - not packages
                continue
            module = importlib.import_module(modname)
            for cls_name, cls_object in inspect.getmembers(module, inspect.isclass):
                if cea.plots.PlotBase in inspect.getmro(cls_object):
                    yield cls_object


if __name__ == '__main__':
    config = cea.config.Configuration()
    buildings = None

    for category in list_categories():
        print('category:', category.name, ':', category.label)
        for plot_class in category.plots:
            print('plot_class:', plot_class)
            plot = plot_class(config.project, parameters={
                'scenario-name': config.scenario_name,
                'buildings': buildings,
                'region': config.region,
            })
            assert plot.name, 'plot missing name: %s' % plot
            assert plot.category_name == category.name
            print('plot:', plot.name, '/', plot.id(), '/', plot.title)

            # plot the plot!
            plot.plot()
