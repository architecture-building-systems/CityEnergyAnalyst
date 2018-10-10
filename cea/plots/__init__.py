from __future__ import division
from __future__ import print_function

"""
Organizes the plots for the CEA. The dashboard uses the package structure of cea.plots to group the plots into
cateogories and find the implementations of the plots.

Each sub-package of ``cea.plots`` is a plot category. The ``__init__.py`` file of that sub-package is expected to
have an attribute ``label`` which is used as the user-visible label of that category.

Each module contained such a sub-package is considered a plot.

The module ``cea.plots.categories`` contains helper-methods for dealing with the categories.
"""

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"