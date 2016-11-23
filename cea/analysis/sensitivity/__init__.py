"""
Sensitivity analysis for demand_main.py

These scripts use the morris algorithm (morris 1991)(campologo 2011) and Sobol Algorithm Sltalli 20110
to screen the most sensitive variables of a selection of parameters of the CEA.

The morris method serves to do basic screening of input variables and it is based on the family of One-at-a-time
screening methods (OAT). morris provides a ranking but not a quantitative measure of the importance of each parameter.

The Sobol method serves for a complete sensitivity analysis of input variables. It is based on variance methods.
"""

__author__ = "Jimeno A. Fonseca; Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Jimeno A. Fonseca", "Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"
