from cea.demand.calibration.latin_sampler import latin_sampler
from cea.demand.calibration.settings import subset_generations
from cea.demand.calibration.settings import subset_threshold
import cea.inputlocator as inputlocator
import cea
__author__ = "Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Fazel Khayatian","Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Testing"

gv = cea.globalvar.GlobalVariables()
scenario_path = gv.scenario_reference
locator = inputlocator.InputLocator(scenario_path=scenario_path)
variables = ['U_win', 'U_wall', 'n50', 'Ths_set_C', 'Cm_Af']
design, pdf_list =latin_sampler(locator, subset_generations, variables)



min_cv_rmse = 1
while min_cv_rmse < subset_threshold:
    simon_and_garfunkel=1