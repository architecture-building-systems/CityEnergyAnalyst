# coding=utf-8
"""
'nn_settings.py' script is host to variables that are fixed during a run (the entered values are recommended)
"""

__author__ = "Fazel Khayatian"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Fazel Khayatian"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# burn-in period for estimation:
warmup_period = 759 # in hourse taken form the end of the year.
#   data preperation properties
nn_delay=1 #recommended is 1
#   neural net training properties
nn_passes=3 #recommended is 20
#   scaler random : this is the number of generations of the city
number_samples_scaler=3 #recommended is 200 but it is a function of the number of features.
#   neural net random generation properties
number_samples=3 #recommended is 10, it is a function of the ram we have, in this case each sample requires 1GB of ram.
#   neural net random generation properties
number_sweeps=3 #recommended is 10,
#   boolean weather using autoencoder or not
autoencoder = False #only true if you have more than 70 features and enough ram.
#   feature that are not float numbers (instead are classes) and should have Boolean properties
boolean_vars = ['ECONOMIZER','WIN_VENT','MECH_VENT','HEAT_REC','NIGHT_FLSH']
#   features selected from the weather data file
climatic_variables = ['drybulb_C', 'wetbulb_C', 'relhum_percent', 'glohorrad_Whm2', 'dirnorrad_Whm2', 'difhorrad_Whm2', 'skytemp_C', 'windspd_ms']
#   features that are subject to uncertainty, and therefore, random sampling
random_variables = ['win_wall','Cm_Af','n50',
                    'U_roof','a_roof','U_wall','a_wall','U_base','U_win','G_win','rf_sh',
                    'Ths_set_C','Tcs_set_C','Ths_setb_C','Tcs_setb_C','Ve_lps',
                    'Qs_Wp','X_ghp','Ea_Wm2','El_Wm2','Vww_lpd','Vw_lpd',
                    'dThs_C','dTcs_C','ECONOMIZER','WIN_VENT','MECH_VENT','HEAT_REC','NIGHT_FLSH','dT_Qhs','dT_Qcs']
#   parameters intended for estimation by the neural network
target_parameters = ['Qhsf_kWh', 'Qcsf_kWh', 'Qwwf_kWh', 'Ef_kWh','T_int_C']
