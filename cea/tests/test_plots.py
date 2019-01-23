from __future__ import print_function
from __future__ import division

"""
Unittests for the plots framework of the CEA.
"""

import unittest
import cea.plots.categories

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


class TestCategories(unittest.TestCase):
    def test_category_names_in_plots(self):
        """
        Test to make sure each plot defines the ``category_name`` attribute and that it is
        the same as the category the plot is defined in.
        """
        for category in cea.plots.categories.list_categories():
            for plot in category.plots:
                self.assertEqual(plot.category_name, category.name)
