# Uncertainty Analysis

Before doing the Analysis, update the database present in CEA -> databases -> Uncertainty -> uncertainty_distributions.xls
Follow the structure already established in the excel file. Provide a default value for each parameter which is used to run
the optimization. Provide further details of the distribution of each parameter.

Uncertainty Analysis is performed after finishing the optimization runs. After optimization runs, uncertainty analysis
can be performed on the population of any generation (preferably last generation).

How to do Uncertainty Analysis:

1. Run Uncertainty_parameters.py to generate the 'uncertainty.csv' file. The file is saved in the 'get_uncertainty_results_folder()'
2. After this, run Individual_Evaluation.py, providing the generation, number of uncertain scenarios to be tested
3. The resulting output files are saved in 'get_uncertainty_results_folder()' folder based on different levels

In Individual_Evaluation.py, the uncertain values are changed using 'setattr' function, and the values are reset back to the default after the analysis

### Contributors to this manual
* [Dr. Sreepathi Bhargava Krishna](http://www.fcl.ethz.ch/people/Researchers/SreepathiKrishna.html/) / Future Cities Laboratory - Singapore-ETH Centre.

