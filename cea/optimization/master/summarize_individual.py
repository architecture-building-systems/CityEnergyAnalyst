"""
The capacities of the individual are saved to a csv file in this function
This includes the Decentralized capacities for both heating and cooling.
This also saves the capacities of the technologies installed in the centralized plant
"""
from __future__ import division
from cea.optimization.constants import GHP_HMAX_SIZE, N_HR, N_HEAT, N_PV, N_PVT
import numpy as np
import pandas as pd

__author__ =  "Sreepathi Bhargava Krishna"
__copyright__ = "Copyright 2018, Architecture and Building Systems - ETH Zurich"
__credits__ = [ "Sreepathi Bhargava Krishna"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "thomas@arch.ethz.ch"
__status__ = "Production"

def summarize_individual_main(master_to_slave_vars, building_names, individual, solar_features, locator, config):
    
    # initializing the capacities of technologies which will not always be used, but to keep the dataframe 
    # consistent for all the cases, the capacities are all initiated with 0's
    Furnace_wet = 0
    Furnace_wet_capacity_W = 0
    Furnace_dry = 0
    Furnace_dry_capacity_W = 0
    CHP_NG = 0
    CHP_NG_capacity_W = 0
    CHP_BG = 0
    CHP_BG_capacity_W = 0
    Base_boiler_BG = 0
    Base_boiler_BG_capacity_W = 0
    Base_boiler_NG = 0
    Base_boiler_NG_capacity_W = 0
    Peak_boiler_BG = 0
    Peak_boiler_BG_capacity_W = 0
    Peak_boiler_NG = 0
    Peak_boiler_NG_capacity_W = 0
    Backup_boiler_NG_capacity_W = 0
    Backup_boiler_BG_capacity_W = 0

    if config.district_heating_network:
        network = master_to_slave_vars.DHN_barcode
    elif config.district_cooling_network:
        network = master_to_slave_vars.DCN_barcode
    cooling_all_units = 'AHU_ARU_SCU'
    heating_all_units = 'AHU_ARU_SHU' # in this version, split heating demand is not fully calculated

    column_names = ['Building Name', 'Decentralized_Boiler_BG_share_heating', 'Decentralized_Boiler_BG_capacity_heating_W',
                    'Decentralized_Boiler_NG_share_heating', 'Decentralized_Boiler_NG_capacity_heating_W',
                    'Decentralized_FC_share_heating', 'Decentralized_FC_capacity_heating_W',
                    'Decentralized_GHP_share_heating', 'Decentralized_GHP_capacity_heating_W',
                    'Decentralized_VCC_to_AHU_share_cooling', 'Decentralized_VCC_to_AHU_capacity_cooling_W',
                    'Decentralized_VCC_to_ARU_share_cooling', 'Decentralized_VCC_to_ARU_capacity_cooling_W',
                    'Decentralized_VCC_to_SCU_share_cooling', 'Decentralized_VCC_to_SCU_capacity_cooling_W',
                    'Decentralized_VCC_to_AHU_ARU_share_cooling', 'Decentralized_VCC_to_AHU_ARU_capacity_cooling_W',
                    'Decentralized_VCC_to_AHU_SCU_share_cooling', 'Decentralized_VCC_to_AHU_SCU_capacity_cooling_W',
                    'Decentralized_VCC_to_ARU_SCU_share_cooling', 'Decentralized_VCC_to_ARU_SCU_capacity_cooling_W',
                    'Decentralized_VCC_to_AHU_ARU_SCU_share_cooling', 'Decentralized_VCC_to_AHU_ARU_SCU_capacity_cooling_W',
                    'Decentralized_single_effect_ACH_to_AHU_share_FP_cooling', 'Decentralized_single_effect_ACH_to_AHU_capacity_FP_cooling_W',
                    'Decentralized_single_effect_ACH_to_AHU_share_ET_cooling', 'Decentralized_single_effect_ACH_to_AHU_capacity_ET_cooling_W',
                    'Decentralized_single_effect_ACH_to_ARU_share_FP_cooling', 'Decentralized_single_effect_ACH_to_ARU_capacity_FP_cooling_W',
                    'Decentralized_single_effect_ACH_to_ARU_share_ET_cooling', 'Decentralized_single_effect_ACH_to_ARU_capacity_ET_cooling_W',
                    'Decentralized_single_effect_ACH_to_SCU_share_FP_cooling', 'Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W',
                    'Decentralized_single_effect_ACH_to_SCU_share_ET_cooling', 'Decentralized_single_effect_ACH_to_SCU_capacity_ET_cooling_W',
                    'Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling', 'Decentralized_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W',
                    'Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling', 'Decentralized_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W',
                    'Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling', 'Decentralized_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W',
                    'Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling', 'Decentralized_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W',
                    'Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling', 'Decentralized_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W',
                    'Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling', 'Decentralized_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W',
                    'Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling', 'Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W',
                    'Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling', 'Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W',
                    'Decentralized_direct_expansion_to_AHU_share_cooling', 'Decentralized_direct_expansion_to_AHU_capacity_cooling_W',
                    'Decentralized_direct_expansion_to_ARU_share_cooling', 'Decentralized_direct_expansion_to_ARU_capacity_cooling_W',
                    'Decentralized_direct_expansion_to_SCU_share_cooling', 'Decentralized_direct_expansion_to_SCU_capacity_cooling_W',
                    'Decentralized_direct_expansion_to_AHU_SCU_share_cooling', 'Decentralized_direct_expansion_to_AHU_SCU_capacity_cooling_W',
                    'Decentralized_direct_expansion_to_AHU_ARU_share_cooling', 'Decentralized_direct_expansion_to_AHU_ARU_capacity_cooling_W',
                    'Decentralized_direct_expansion_to_ARU_SCU_share_cooling', 'Decentralized_direct_expansion_to_ARU_SCU_capacity_cooling_W',
                    'Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling', 'Decentralized_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W',
                    'Furnace_wet', 'Furnace_wet_capacity_W', 'Furnace_dry', 'Furnace_dry_capacity_W', 'CHP_NG',
                    'CHP_NG_capacity_W', 'CHP_BG', 'CHP_BG_capacity_W', 'Base_boiler_BG', 'Base_boiler_BG_capacity_W',
                    'Base_boiler_NG', 'Base_boiler_NG_capacity_W', 'Peak_boiler_BG', 'Peak_boiler_BG_capacity_W', 'Backup_boiler_BG_capacity_W',
                    'Peak_boiler_NG', 'Peak_boiler_NG_capacity_W', 'Backup_boiler_NG_capacity_W', 'HP_Lake', 'HP_Lake_capacity_W', 'HP_Sewage',
                    'HP_Sewage_capacity_W', 'GHP', 'GHP_capacity_W', 'PV', 'PV_capacity_W', 'PVT', 'PVT_capacity_W',
                    'SC_ET', 'SC_ET_capacity_W', 'SC_FP', 'SC_FP_capacity_W', 'VCC', 'VCC_capacity_W', 'Backup_VCC_capacity_W','Absorption_Chiller',
                    'Absorption_Chiller_capacity_W', 'Lake_cooling', 'Lake_cooling_capacity_W', 'storage_cooling', 'storage_cooling_capacity_W']

    building_names_capacity = np.append(building_names, 'Central Plant')
    # initiating the dataframe to save the installed capacities
    df_installed_capacity = pd.DataFrame( columns=column_names)
    df_installed_capacity['Building Name'] = building_names_capacity
    df_installed_capacity = df_installed_capacity.set_index('Building Name') # indexing the dataframe with building name

    for i in range(len(network)):
        # if a building is connected, which corresponds to '1' then the Decentralized shares are linked to the
        # number of units the DHN/DCN is supplying. A building can be supplied AHU demand from the centralized
        # plant whereas the remaining load corresponding to ARU and SHU/SCU be supplied by the decentralized option
        # if a building is Decentralized, which corresponds to '0' then Decentralized shares are imported from csv files
        # initiating capacities to avoid errors in saving the dataframes
        Decentralized_Boiler_BG_share_heating = 0
        Decentralized_Boiler_BG_capacity_heating_W = 0
        Decentralized_Boiler_NG_share_heating = 0
        Decentralized_Boiler_NG_capacity_heating_W = 0
        Decentralized_FC_share_heating = 0
        Decentralized_FC_capacity_heating_W = 0
        Decentralized_GHP_share_heating = 0
        Decentralized_GHP_capacity_heating_W = 0
        Decentralized_VCC_to_AHU_share_cooling = 0
        Decentralized_VCC_to_AHU_capacity_cooling_W = 0
        Decentralized_VCC_to_ARU_share_cooling = 0
        Decentralized_VCC_to_ARU_capacity_cooling_W = 0
        Decentralized_VCC_to_SCU_share_cooling = 0
        Decentralized_VCC_to_SCU_capacity_cooling_W = 0
        Decentralized_VCC_to_AHU_ARU_share_cooling = 0
        Decentralized_VCC_to_AHU_ARU_capacity_cooling_W = 0
        Decentralized_VCC_to_AHU_SCU_share_cooling = 0
        Decentralized_VCC_to_AHU_SCU_capacity_cooling_W = 0
        Decentralized_VCC_to_ARU_SCU_share_cooling = 0
        Decentralized_VCC_to_ARU_SCU_capacity_cooling_W = 0
        Decentralized_VCC_to_AHU_ARU_SCU_share_cooling = 0
        Decentralized_VCC_to_AHU_ARU_SCU_capacity_cooling_W = 0
        Decentralized_single_effect_ACH_to_AHU_share_FP_cooling = 0
        Decentralized_single_effect_ACH_to_AHU_capacity_FP_cooling_W = 0
        Decentralized_single_effect_ACH_to_AHU_share_ET_cooling = 0
        Decentralized_single_effect_ACH_to_AHU_capacity_ET_cooling_W = 0
        Decentralized_single_effect_ACH_to_ARU_share_FP_cooling = 0
        Decentralized_single_effect_ACH_to_ARU_capacity_FP_cooling_W = 0
        Decentralized_single_effect_ACH_to_ARU_share_ET_cooling = 0
        Decentralized_single_effect_ACH_to_ARU_capacity_ET_cooling_W = 0
        Decentralized_single_effect_ACH_to_SCU_share_FP_cooling = 0
        Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W = 0
        Decentralized_single_effect_ACH_to_SCU_share_ET_cooling = 0
        Decentralized_single_effect_ACH_to_SCU_capacity_ET_cooling_W = 0
        Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling = 0
        Decentralized_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W = 0
        Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling = 0
        Decentralized_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W = 0
        Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling = 0
        Decentralized_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W = 0
        Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling = 0
        Decentralized_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W = 0
        Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling = 0
        Decentralized_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W = 0
        Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling = 0
        Decentralized_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W = 0
        Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling = 0
        Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W = 0
        Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling = 0
        Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W = 0
        Decentralized_direct_expansion_to_AHU_share_cooling = 0
        Decentralized_direct_expansion_to_AHU_capacity_cooling_W = 0
        Decentralized_direct_expansion_to_ARU_share_cooling = 0
        Decentralized_direct_expansion_to_ARU_capacity_cooling_W = 0
        Decentralized_direct_expansion_to_SCU_share_cooling = 0
        Decentralized_direct_expansion_to_SCU_capacity_cooling_W = 0
        Decentralized_direct_expansion_to_AHU_SCU_share_cooling = 0
        Decentralized_direct_expansion_to_AHU_SCU_capacity_cooling_W = 0
        Decentralized_direct_expansion_to_AHU_ARU_share_cooling = 0
        Decentralized_direct_expansion_to_AHU_ARU_capacity_cooling_W = 0
        Decentralized_direct_expansion_to_ARU_SCU_share_cooling = 0
        Decentralized_direct_expansion_to_ARU_SCU_capacity_cooling_W = 0
        Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling = 0
        Decentralized_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W = 0

        if network[i] == "0":
            # if the building is not connected to the centralized plant, then the corresponding demand is satisfied
            # by the decentralized technologies, which were already generated using cea\optimization\preprocessing\decentralized_building_main.py
            if config.district_heating_network:
                df = pd.read_csv(
                    locator.get_optimization_decentralized_folder_building_result_heating(building_names[i]))
                dfBest = df[df["Best configuration"] == 1]
                Decentralized_Boiler_BG_share_heating = dfBest["BoilerBG Share"].iloc[0]
                Decentralized_Boiler_NG_share_heating = dfBest["BoilerNG Share"].iloc[0]
                Decentralized_FC_share_heating = dfBest["FC Share"].iloc[0]
                Decentralized_GHP_share_heating = dfBest["GHP Share"].iloc[0]

                if Decentralized_Boiler_BG_share_heating == 1:
                    Decentralized_Boiler_BG_capacity_heating_W = dfBest["Nominal Power"].iloc[0]

                if Decentralized_Boiler_NG_share_heating == 1:
                    Decentralized_Boiler_NG_capacity_heating_W = dfBest["Nominal Power"].iloc[0]

                if Decentralized_FC_share_heating == 1:
                    Decentralized_FC_capacity_heating_W = dfBest["Nominal Power"].iloc[0]

                if Decentralized_GHP_share_heating == 1:
                    Decentralized_GHP_capacity_heating_W = dfBest["Nominal Power"].iloc[0]

                if (Decentralized_FC_share_heating == 0 and Decentralized_Boiler_BG_share_heating == 0 and Decentralized_GHP_share_heating != 0 and Decentralized_Boiler_NG_share_heating != 0):
                    Decentralized_Boiler_NG_capacity_heating_W = dfBest["Nominal Power"].iloc[
                                                                    0] / Decentralized_Boiler_NG_share_heating
                    Decentralized_GHP_capacity_heating_W = dfBest["Nominal Power"].iloc[
                                                              0] / Decentralized_GHP_share_heating

                df_installed_capacity['Decentralized_Boiler_BG_share_heating'][i] = Decentralized_Boiler_BG_share_heating
                df_installed_capacity['Decentralized_Boiler_BG_capacity_heating_W'][i] = Decentralized_Boiler_BG_capacity_heating_W
                df_installed_capacity['Decentralized_Boiler_NG_share_heating'][i] = Decentralized_Boiler_NG_share_heating
                df_installed_capacity['Decentralized_Boiler_NG_capacity_heating_W'][i] = Decentralized_Boiler_NG_capacity_heating_W
                df_installed_capacity['Decentralized_FC_share_heating'][i] = Decentralized_FC_share_heating
                df_installed_capacity['Decentralized_FC_capacity_heating_W'][i] = Decentralized_FC_capacity_heating_W
                df_installed_capacity['Decentralized_GHP_share_heating'][i] = Decentralized_GHP_share_heating
                df_installed_capacity['Decentralized_GHP_capacity_heating_W'][i] = Decentralized_GHP_capacity_heating_W
                df_installed_capacity['Decentralized_VCC_to_AHU_share_cooling'][i] = Decentralized_VCC_to_AHU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_AHU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_ARU_share_cooling'][i] = Decentralized_VCC_to_ARU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_ARU_capacity_cooling_W'][i] = Decentralized_VCC_to_ARU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_SCU_share_cooling'][i] = Decentralized_VCC_to_SCU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_AHU_ARU_share_cooling'][i] = Decentralized_VCC_to_AHU_ARU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_AHU_ARU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_ARU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_AHU_SCU_share_cooling'][i] = Decentralized_VCC_to_AHU_SCU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_AHU_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_ARU_SCU_share_cooling'][i] = Decentralized_VCC_to_ARU_SCU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_ARU_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_ARU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_AHU_ARU_SCU_share_cooling'][i] = Decentralized_VCC_to_AHU_ARU_SCU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_AHU_ARU_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_ARU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_ARU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_ARU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_ARU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_ARU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_SCU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_SCU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_SCU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_share_cooling'][i] = Decentralized_direct_expansion_to_AHU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_AHU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_ARU_share_cooling'][i] = Decentralized_direct_expansion_to_ARU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_ARU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_ARU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_SCU_share_cooling'][i] = Decentralized_direct_expansion_to_SCU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_SCU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_SCU_share_cooling'][i] = Decentralized_direct_expansion_to_AHU_SCU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_SCU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_AHU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_share_cooling'][i] = Decentralized_direct_expansion_to_AHU_ARU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_AHU_ARU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_ARU_SCU_share_cooling'][i] = Decentralized_direct_expansion_to_ARU_SCU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_ARU_SCU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_ARU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling'][i] = Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W

            elif config.district_cooling_network:

                df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_names[i],
                                                                                                      cooling_all_units))
                dfBest = df[df["Best configuration"] == 1]
                Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling = \
                dfBest["single effect ACH to AHU_ARU_SCU Share (FP)"].iloc[0]
                Decentralized_single_effect_ACH_to_SCU_share_FP_cooling = \
                dfBest["single effect ACH to SCU Share (FP)"].iloc[0]
                Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling = \
                dfBest["single effect ACH to AHU_ARU_SCU Share (ET)"].iloc[0]
                Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling = dfBest["DX to AHU_ARU_SCU Share"].iloc[0]
                Decentralized_VCC_to_AHU_ARU_share_cooling = dfBest["VCC to AHU_ARU Share"].iloc[0]
                Decentralized_VCC_to_AHU_ARU_SCU_share_cooling = dfBest["VCC to AHU_ARU_SCU Share"].iloc[0]
                Decentralized_VCC_to_SCU_share_cooling = dfBest["VCC to SCU Share"].iloc[0]

                if Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling == 1:
                    Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W = \
                    dfBest["Nominal Power single effect ACH to AHU_ARU_SCU (FP) [W]"].iloc[0]

                if Decentralized_single_effect_ACH_to_SCU_share_FP_cooling == 1:
                    Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W = \
                    dfBest["Nominal Power single effect ACH to SCU (FP) [W]"].iloc[0]

                if Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling == 1:
                    Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W = \
                    dfBest["Nominal Power single effect ACH to AHU_ARU_SCU (ET) [W]"].iloc[0]

                if Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling == 1:
                    Decentralized_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W = \
                    dfBest["Nominal Power DX to AHU_ARU_SCU [W]"].iloc[0]

                if Decentralized_VCC_to_AHU_ARU_share_cooling == 1:
                    Decentralized_VCC_to_AHU_ARU_capacity_cooling_W = dfBest["Nominal Power VCC to AHU_ARU [W]"].iloc[0]

                if Decentralized_VCC_to_AHU_ARU_SCU_share_cooling == 1:
                    Decentralized_VCC_to_AHU_ARU_SCU_capacity_cooling_W = \
                    dfBest["Nominal Power VCC to AHU_ARU_SCU [W]"].iloc[0]

                if Decentralized_VCC_to_SCU_share_cooling == 1:
                    Decentralized_VCC_to_SCU_capacity_cooling_W = dfBest["Nominal Power VCC to SCU [W]"].iloc[0]

                df_installed_capacity['Decentralized_Boiler_BG_share_heating'][i] = Decentralized_Boiler_BG_share_heating
                df_installed_capacity['Decentralized_Boiler_BG_capacity_heating_W'][i] = Decentralized_Boiler_BG_capacity_heating_W
                df_installed_capacity['Decentralized_Boiler_NG_share_heating'][i] = Decentralized_Boiler_NG_share_heating
                df_installed_capacity['Decentralized_Boiler_NG_capacity_heating_W'][i] = Decentralized_Boiler_NG_capacity_heating_W
                df_installed_capacity['Decentralized_FC_share_heating'][i] = Decentralized_FC_share_heating
                df_installed_capacity['Decentralized_FC_capacity_heating_W'][i] = Decentralized_FC_capacity_heating_W
                df_installed_capacity['Decentralized_GHP_share_heating'][i] = Decentralized_GHP_share_heating
                df_installed_capacity['Decentralized_GHP_capacity_heating_W'][i] = Decentralized_GHP_capacity_heating_W
                df_installed_capacity['Decentralized_VCC_to_AHU_share_cooling'][i] = Decentralized_VCC_to_AHU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_AHU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_ARU_share_cooling'][i] = Decentralized_VCC_to_ARU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_ARU_capacity_cooling_W'][i] = Decentralized_VCC_to_ARU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_SCU_share_cooling'][i] = Decentralized_VCC_to_SCU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_AHU_ARU_share_cooling'][i] = Decentralized_VCC_to_AHU_ARU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_AHU_ARU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_ARU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_AHU_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_ARU_SCU_share_cooling'][i] = Decentralized_VCC_to_ARU_SCU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_ARU_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_ARU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_VCC_to_AHU_ARU_SCU_share_cooling'][i] = Decentralized_VCC_to_AHU_ARU_SCU_share_cooling
                df_installed_capacity['Decentralized_VCC_to_AHU_ARU_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_ARU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_ARU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_ARU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_ARU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_ARU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_SCU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_SCU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_SCU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling
                df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W'][i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_share_cooling'][i] = Decentralized_direct_expansion_to_AHU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_AHU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_ARU_share_cooling'][i] = Decentralized_direct_expansion_to_ARU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_ARU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_ARU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_SCU_share_cooling'][i] = Decentralized_direct_expansion_to_SCU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_SCU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_SCU_share_cooling'][i] = Decentralized_direct_expansion_to_AHU_SCU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_SCU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_AHU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_share_cooling'][i] = Decentralized_direct_expansion_to_AHU_ARU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_AHU_ARU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_ARU_SCU_share_cooling'][i] = Decentralized_direct_expansion_to_ARU_SCU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_ARU_SCU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_ARU_SCU_capacity_cooling_W
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling'][i] = Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling
                df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W'][i] = Decentralized_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W

            else:
                raise ValueError("the region is not specified correctly")
        else:
            DCN_unit_configuration = master_to_slave_vars.DCN_supplyunits

            if DCN_unit_configuration == 1:  # corresponds to AHU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'ARU_SCU'
                df = pd.read_csv(
                    locator.get_optimization_decentralized_folder_building_result_cooling(building_names[i],
                                                                                         decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Decentralized_direct_expansion_to_ARU_SCU_share_cooling = dfBest["DX to ARU_SCU Share"].iloc[0]
                Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling = \
                dfBest["single effect ACH to ARU_SCU Share (FP)"].iloc[0]
                Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling = \
                dfBest["single effect ACH to ARU_SCU Share (ET)"].iloc[0]
                Decentralized_VCC_to_ARU_SCU_share_cooling = dfBest["VCC to ARU_SCU Share"].iloc[0]

                if Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling == 1:
                    Decentralized_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W = \
                    dfBest["Nominal Power single effect ACH to ARU_SCU (FP) [W]"].iloc[0]

                if Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling == 1:
                    Decentralized_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W = \
                    dfBest["Nominal Power single effect ACH to ARU_SCU (ET) [W]"].iloc[0]

                if Decentralized_direct_expansion_to_ARU_SCU_share_cooling == 1:
                    Decentralized_direct_expansion_to_ARU_SCU_capacity_cooling_W = \
                    dfBest["Nominal Power DX to ARU_SCU [W]"].iloc[0]

                if Decentralized_VCC_to_ARU_SCU_share_cooling == 1:
                    Decentralized_VCC_to_ARU_SCU_capacity_cooling_W = dfBest["Nominal Power VCC to ARU_SCU [W]"].iloc[0]

            if DCN_unit_configuration == 2:  # corresponds to ARU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'AHU_SCU'
                df = pd.read_csv(
                    locator.get_optimization_decentralized_folder_building_result_cooling(building_names[i],
                                                                                         decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Decentralized_direct_expansion_to_AHU_SCU_share_cooling = dfBest["DX to AHU_SCU Share"].iloc[0]
                Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling = \
                dfBest["single effect ACH to AHU_SCU Share (FP)"].iloc[0]
                Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling = \
                dfBest["single effect ACH to AHU_SCU Share (ET)"].iloc[0]
                Decentralized_VCC_to_ARU_SCU_share_cooling = dfBest["VCC to AHU_SCU Share"].iloc[0]

                if Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling == 1:
                    Decentralized_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W = \
                    dfBest["Nominal Power single effect ACH to AHU_SCU (FP) [W]"].iloc[0]

                if Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling == 1:
                    Decentralized_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W = \
                    dfBest["Nominal Power single effect ACH to AHU_SCU (ET) [W]"].iloc[0]

                if Decentralized_direct_expansion_to_AHU_SCU_share_cooling == 1:
                    Decentralized_direct_expansion_to_AHU_SCU_capacity_cooling_W = \
                    dfBest["Nominal Power DX to AHU_SCU [W]"].iloc[0]

                if Decentralized_VCC_to_AHU_SCU_share_cooling == 1:
                    Decentralized_VCC_to_AHU_SCU_capacity_cooling_W = dfBest["Nominal Power VCC to AHU_SCU [W]"].iloc[0]

            if DCN_unit_configuration == 3:  # corresponds to SCU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'AHU_ARU'

                df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_names[i],
                                                                                                      decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Decentralized_direct_expansion_to_AHU_ARU_share_cooling = dfBest["DX to AHU_ARU Share"].iloc[0]
                Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling = \
                    dfBest["single effect ACH to AHU_ARU Share (FP)"].iloc[0]
                Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling = \
                    dfBest["single effect ACH to AHU_ARU Share (ET)"].iloc[0]
                Decentralized_VCC_to_AHU_ARU_share_cooling = dfBest["VCC to AHU_ARU Share"].iloc[0]

                if Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling == 1:
                    Decentralized_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W = \
                        dfBest["Nominal Power single effect ACH to AHU_ARU (FP) [W]"].iloc[0]

                if Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling == 1:
                    Decentralized_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W = \
                        dfBest["Nominal Power single effect ACH to AHU_ARU (ET) [W]"].iloc[0]

                if Decentralized_direct_expansion_to_AHU_ARU_share_cooling == 1:
                    Decentralized_direct_expansion_to_AHU_ARU_capacity_cooling_W = \
                        dfBest["Nominal Power DX to AHU_ARU [W]"].iloc[0]

                if Decentralized_VCC_to_AHU_ARU_share_cooling == 1:
                    Decentralized_VCC_to_AHU_ARU_capacity_cooling_W = \
                        dfBest["Nominal Power VCC to AHU_ARU [W]"].iloc[0]

            if DCN_unit_configuration == 4:  # corresponds to AHU + ARU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'SCU'

                df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_names[i],
                                                                                                      decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Decentralized_direct_expansion_to_SCU_share_cooling = dfBest["DX to SCU Share"].iloc[0]
                Decentralized_single_effect_ACH_to_SCU_share_FP_cooling = \
                    dfBest["single effect ACH to SCU Share (FP)"].iloc[0]
                Decentralized_single_effect_ACH_to_SCU_share_ET_cooling = \
                    dfBest["single effect ACH to SCU Share (ET)"].iloc[0]
                Decentralized_VCC_to_SCU_share_cooling = dfBest["VCC to SCU Share"].iloc[0]

                if Decentralized_single_effect_ACH_to_SCU_share_FP_cooling == 1:
                    Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W = \
                        dfBest["Nominal Power single effect ACH to SCU (FP) [W]"].iloc[0]

                if Decentralized_single_effect_ACH_to_SCU_share_ET_cooling == 1:
                    Decentralized_single_effect_ACH_to_SCU_capacity_ET_cooling_W = \
                        dfBest["Nominal Power single effect ACH to SCU (ET) [W]"].iloc[0]

                if Decentralized_direct_expansion_to_SCU_share_cooling == 1:
                    Decentralized_direct_expansion_to_SCU_capacity_cooling_W = \
                        dfBest["Nominal Power DX to SCU [W]"].iloc[0]

                if Decentralized_VCC_to_SCU_share_cooling == 1:
                    Decentralized_VCC_to_SCU_capacity_cooling_W = \
                        dfBest["Nominal Power VCC to SCU [W]"].iloc[0]

            if DCN_unit_configuration == 5:  # corresponds to AHU + SCU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'ARU'

                df = pd.read_csv(locator.get_optimization_decentralized_folder_building_result_cooling(building_names[i],
                                                                                                      decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Decentralized_direct_expansion_to_ARU_share_cooling = dfBest["DX to ARU Share"].iloc[0]
                Decentralized_single_effect_ACH_to_ARU_share_FP_cooling = \
                    dfBest["single effect ACH to ARU Share (FP)"].iloc[0]
                Decentralized_single_effect_ACH_to_ARU_share_ET_cooling = \
                    dfBest["single effect ACH to ARU Share (ET)"].iloc[0]
                Decentralized_VCC_to_ARU_share_cooling = dfBest["VCC to ARU Share"].iloc[0]

                if Decentralized_single_effect_ACH_to_ARU_share_FP_cooling == 1:
                    Decentralized_single_effect_ACH_to_ARU_capacity_FP_cooling_W = \
                        dfBest["Nominal Power single effect ACH to ARU (FP) [W]"].iloc[0]

                if Decentralized_single_effect_ACH_to_ARU_share_ET_cooling == 1:
                    Decentralized_single_effect_ACH_to_ARU_capacity_ET_cooling_W = \
                        dfBest["Nominal Power single effect ACH to ARU (ET) [W]"].iloc[0]

                if Decentralized_direct_expansion_to_ARU_share_cooling == 1:
                    Decentralized_direct_expansion_to_ARU_capacity_cooling_W = \
                        dfBest["Nominal Power DX to ARU [W]"].iloc[0]

                if Decentralized_VCC_to_ARU_share_cooling == 1:
                    Decentralized_VCC_to_ARU_capacity_cooling_W = \
                        dfBest["Nominal Power VCC to ARU [W]"].iloc[0]

            if DCN_unit_configuration == 6:  # corresponds to ARU + SCU in the central plant, so remaining load need to be provided by decentralized plant
                decentralized_configuration = 'AHU'

                df = pd.read_csv(
                    locator.get_optimization_decentralized_folder_building_result_cooling(building_names[i],
                                                                                         decentralized_configuration))
                dfBest = df[df["Best configuration"] == 1]
                Decentralized_direct_expansion_to_AHU_share_cooling = dfBest["DX to AHU Share"].iloc[0]
                Decentralized_single_effect_ACH_to_AHU_share_FP_cooling = \
                    dfBest["single effect ACH to AHU Share (FP)"].iloc[0]
                Decentralized_single_effect_ACH_to_AHU_share_ET_cooling = \
                    dfBest["single effect ACH to AHU Share (ET)"].iloc[0]
                Decentralized_VCC_to_AHU_share_cooling = dfBest["VCC to AHU Share"].iloc[0]

                if Decentralized_single_effect_ACH_to_AHU_share_FP_cooling == 1:
                    Decentralized_single_effect_ACH_to_AHU_capacity_FP_cooling_W = \
                        dfBest["Nominal Power single effect ACH to AHU (FP) [W]"].iloc[0]

                if Decentralized_single_effect_ACH_to_AHU_share_ET_cooling == 1:
                    Decentralized_single_effect_ACH_to_AHU_capacity_ET_cooling_W = \
                        dfBest["Nominal Power single effect ACH to AHU (ET) [W]"].iloc[0]

                if Decentralized_direct_expansion_to_AHU_share_cooling == 1:
                    Decentralized_direct_expansion_to_AHU_capacity_cooling_W = \
                        dfBest["Nominal Power DX to AHU [W]"].iloc[0]

                if Decentralized_VCC_to_AHU_share_cooling == 1:
                    Decentralized_VCC_to_AHU_capacity_cooling_W = \
                        dfBest["Nominal Power VCC to AHU [W]"].iloc[0]

            df_installed_capacity['Decentralized_Boiler_BG_share_heating'][i] = Decentralized_Boiler_BG_share_heating
            df_installed_capacity['Decentralized_Boiler_BG_capacity_heating_W'][i] = Decentralized_Boiler_BG_capacity_heating_W
            df_installed_capacity['Decentralized_Boiler_NG_share_heating'][i] = Decentralized_Boiler_NG_share_heating
            df_installed_capacity['Decentralized_Boiler_NG_capacity_heating_W'][i] = Decentralized_Boiler_NG_capacity_heating_W
            df_installed_capacity['Decentralized_FC_share_heating'][i] = Decentralized_FC_share_heating
            df_installed_capacity['Decentralized_FC_capacity_heating_W'][i] = Decentralized_FC_capacity_heating_W
            df_installed_capacity['Decentralized_GHP_share_heating'][i] = Decentralized_GHP_share_heating
            df_installed_capacity['Decentralized_GHP_capacity_heating_W'][i] = Decentralized_GHP_capacity_heating_W
            df_installed_capacity['Decentralized_VCC_to_AHU_share_cooling'][i] = Decentralized_VCC_to_AHU_share_cooling
            df_installed_capacity['Decentralized_VCC_to_AHU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_capacity_cooling_W
            df_installed_capacity['Decentralized_VCC_to_ARU_share_cooling'][i] = Decentralized_VCC_to_ARU_share_cooling
            df_installed_capacity['Decentralized_VCC_to_ARU_capacity_cooling_W'][i] = Decentralized_VCC_to_ARU_capacity_cooling_W
            df_installed_capacity['Decentralized_VCC_to_SCU_share_cooling'][i] = Decentralized_VCC_to_SCU_share_cooling
            df_installed_capacity['Decentralized_VCC_to_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_SCU_capacity_cooling_W
            df_installed_capacity['Decentralized_VCC_to_AHU_ARU_share_cooling'][i] = Decentralized_VCC_to_AHU_ARU_share_cooling
            df_installed_capacity['Decentralized_VCC_to_AHU_ARU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_ARU_capacity_cooling_W
            df_installed_capacity['Decentralized_VCC_to_AHU_SCU_share_cooling'][i] = Decentralized_VCC_to_AHU_SCU_share_cooling
            df_installed_capacity['Decentralized_VCC_to_AHU_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_AHU_SCU_capacity_cooling_W
            df_installed_capacity['Decentralized_VCC_to_ARU_SCU_share_cooling'][i] = Decentralized_VCC_to_ARU_SCU_share_cooling
            df_installed_capacity['Decentralized_VCC_to_ARU_SCU_capacity_cooling_W'][i] = Decentralized_VCC_to_ARU_SCU_capacity_cooling_W
            df_installed_capacity['Decentralized_VCC_to_AHU_ARU_SCU_share_cooling'][i] = Decentralized_VCC_to_AHU_ARU_SCU_share_cooling
            df_installed_capacity['Decentralized_VCC_to_AHU_ARU_SCU_capacity_cooling_W'][
                i] = Decentralized_VCC_to_AHU_ARU_SCU_capacity_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_share_FP_cooling'][
                i] = Decentralized_single_effect_ACH_to_AHU_share_FP_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_capacity_FP_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_AHU_capacity_FP_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_share_ET_cooling'][
                i] = Decentralized_single_effect_ACH_to_AHU_share_ET_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_capacity_ET_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_AHU_capacity_ET_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_share_FP_cooling'][
                i] = Decentralized_single_effect_ACH_to_ARU_share_FP_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_capacity_FP_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_ARU_capacity_FP_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_share_ET_cooling'][
                i] = Decentralized_single_effect_ACH_to_ARU_share_ET_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_capacity_ET_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_ARU_capacity_ET_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_share_FP_cooling'][
                i] = Decentralized_single_effect_ACH_to_SCU_share_FP_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_SCU_capacity_FP_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_share_ET_cooling'][
                i] = Decentralized_single_effect_ACH_to_SCU_share_ET_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_SCU_capacity_ET_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_SCU_capacity_ET_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling'][
                i] = Decentralized_single_effect_ACH_to_AHU_ARU_share_FP_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_AHU_ARU_capacity_FP_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling'][
                i] = Decentralized_single_effect_ACH_to_AHU_ARU_share_ET_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_AHU_ARU_capacity_ET_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling'][
                i] = Decentralized_single_effect_ACH_to_AHU_SCU_share_FP_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_AHU_SCU_capacity_FP_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling'][
                i] = Decentralized_single_effect_ACH_to_AHU_SCU_share_ET_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_AHU_SCU_capacity_ET_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling'][
                i] = Decentralized_single_effect_ACH_to_ARU_SCU_share_FP_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_ARU_SCU_capacity_FP_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling'][
                i] = Decentralized_single_effect_ACH_to_ARU_SCU_share_ET_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_ARU_SCU_capacity_ET_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling'][
                i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_FP_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_FP_cooling_W
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling'][
                i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_share_ET_cooling
            df_installed_capacity['Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W'][
                i] = Decentralized_single_effect_ACH_to_AHU_ARU_SCU_capacity_ET_cooling_W
            df_installed_capacity['Decentralized_direct_expansion_to_AHU_share_cooling'][
                i] = Decentralized_direct_expansion_to_AHU_share_cooling
            df_installed_capacity['Decentralized_direct_expansion_to_AHU_capacity_cooling_W'][
                i] = Decentralized_direct_expansion_to_AHU_capacity_cooling_W
            df_installed_capacity['Decentralized_direct_expansion_to_ARU_share_cooling'][
                i] = Decentralized_direct_expansion_to_ARU_share_cooling
            df_installed_capacity['Decentralized_direct_expansion_to_ARU_capacity_cooling_W'][
                i] = Decentralized_direct_expansion_to_ARU_capacity_cooling_W
            df_installed_capacity['Decentralized_direct_expansion_to_SCU_share_cooling'][
                i] = Decentralized_direct_expansion_to_SCU_share_cooling
            df_installed_capacity['Decentralized_direct_expansion_to_SCU_capacity_cooling_W'][
                i] = Decentralized_direct_expansion_to_SCU_capacity_cooling_W
            df_installed_capacity['Decentralized_direct_expansion_to_AHU_SCU_share_cooling'][
                i] = Decentralized_direct_expansion_to_AHU_SCU_share_cooling
            df_installed_capacity['Decentralized_direct_expansion_to_AHU_SCU_capacity_cooling_W'][
                i] = Decentralized_direct_expansion_to_AHU_SCU_capacity_cooling_W
            df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_share_cooling'][
                i] = Decentralized_direct_expansion_to_AHU_ARU_share_cooling
            df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_capacity_cooling_W'][
                i] = Decentralized_direct_expansion_to_AHU_ARU_capacity_cooling_W
            df_installed_capacity['Decentralized_direct_expansion_to_ARU_SCU_share_cooling'][
                i] = Decentralized_direct_expansion_to_ARU_SCU_share_cooling
            df_installed_capacity['Decentralized_direct_expansion_to_ARU_SCU_capacity_cooling_W'][
                i] = Decentralized_direct_expansion_to_ARU_SCU_capacity_cooling_W
            df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling'][
                i] = Decentralized_direct_expansion_to_AHU_ARU_SCU_share_cooling
            df_installed_capacity['Decentralized_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W'][
                i] = Decentralized_direct_expansion_to_AHU_ARU_SCU_capacity_cooling_W

    # Based on the slave data, capacities corresponding to the centralized network are calculated in the following
    # script. Note that irrespective of the number of technologies used in an individual, the length of the dict
    # is constant
    if master_to_slave_vars.Furn_Moist_type == "wet":
        Furnace_wet = master_to_slave_vars.Furnace_on
        Furnace_wet_capacity_W = master_to_slave_vars.Furnace_Q_max_W
    elif master_to_slave_vars.Furn_Moist_type == "dry":
        Furnace_dry = master_to_slave_vars.Furnace_on
        Furnace_dry_capacity_W = master_to_slave_vars.Furnace_Q_max_W
    if master_to_slave_vars.gt_fuel == "NG":
        CHP_NG = master_to_slave_vars.CC_on
        CHP_NG_capacity_W = master_to_slave_vars.CC_GT_SIZE_W
        Base_boiler_NG = master_to_slave_vars.Boiler_on
        Base_boiler_NG_capacity_W = master_to_slave_vars.Boiler_Q_max_W
        Peak_boiler_NG = master_to_slave_vars.BoilerPeak_on
        Peak_boiler_NG_capacity_W = master_to_slave_vars.BoilerPeak_Q_max_W
        Backup_boiler_NG_capacity_W = master_to_slave_vars.BoilerBackup_Q_max_W
    elif master_to_slave_vars.gt_fuel == "BG":
        CHP_BG = master_to_slave_vars.CC_on
        CHP_BG_capacity_W = master_to_slave_vars.CC_GT_SIZE_W
        Base_boiler_BG = master_to_slave_vars.Boiler_on
        Base_boiler_BG_capacity_W = master_to_slave_vars.Boiler_Q_max_W
        Peak_boiler_BG = master_to_slave_vars.BoilerPeak_on
        Peak_boiler_BG_capacity_W = master_to_slave_vars.BoilerPeak_Q_max_W
        Backup_boiler_BG_capacity_W = master_to_slave_vars.BoilerBackup_Q_max_W

    HP_Lake = master_to_slave_vars.HP_Lake_on
    HP_Lake_capacity_W = master_to_slave_vars.HPLake_maxSize_W
    HP_Sewage = master_to_slave_vars.HP_Sew_on
    HP_Sewage_capacity_W = master_to_slave_vars.HPSew_maxSize_W
    GHP = master_to_slave_vars.GHP_on
    GHP_capacity_W = master_to_slave_vars.GHP_number * GHP_HMAX_SIZE
    PV = individual[N_HEAT * 2 + N_HR]
    PV_capacity_W = master_to_slave_vars.SOLAR_PART_PV * solar_features.A_PV_m2 * N_PV * 1000
    if config.district_heating_network:
        PVT = individual[N_HEAT * 2 + N_HR + 2]
        PVT_capacity_W = master_to_slave_vars.SOLAR_PART_PVT * solar_features.A_PVT_m2 * N_PVT * 1000
    else:
        PVT = 0
        PVT_capacity_W = 0

    SC_ET = individual[N_HEAT * 2 + N_HR + 4]
    SC_ET_capacity_W = master_to_slave_vars.SOLAR_PART_SC_ET * solar_features.A_SC_ET_m2 * 1000
    SC_FP = individual[N_HEAT * 2 + N_HR + 6]
    SC_FP_capacity_W = master_to_slave_vars.SOLAR_PART_SC_FP * solar_features.A_SC_FP_m2 * 1000

    VCC = master_to_slave_vars.VCC_on
    VCC_capacity_W = master_to_slave_vars.VCC_cooling_size_W
    Backup_VCC_capacity_W = master_to_slave_vars.VCC_backup_cooling_size_W
    Absorption_Chiller = master_to_slave_vars.Absorption_Chiller_on
    Absorption_Chiller_capacity_W = master_to_slave_vars.Absorption_chiller_size_W
    Lake_cooling = master_to_slave_vars.Lake_cooling_on
    Lake_cooling_capacity_W = master_to_slave_vars.Lake_cooling_size_W
    storage_cooling = master_to_slave_vars.storage_cooling_on
    storage_cooling_capacity_W = master_to_slave_vars.Storage_cooling_size_W
    
    # Saving the capacities of the centralized plant based on the Slave data available for an individual
    df_installed_capacity['Furnace_wet']['Central Plant'] = Furnace_wet
    df_installed_capacity['Furnace_wet_capacity_W']['Central Plant'] = Furnace_wet_capacity_W
    df_installed_capacity['Furnace_dry']['Central Plant'] = Furnace_dry
    df_installed_capacity['Furnace_dry_capacity_W']['Central Plant'] = Furnace_dry_capacity_W
    df_installed_capacity['CHP_NG']['Central Plant'] = CHP_NG
    df_installed_capacity['CHP_NG_capacity_W']['Central Plant'] = CHP_NG_capacity_W
    df_installed_capacity['CHP_BG']['Central Plant'] = CHP_BG
    df_installed_capacity['CHP_BG_capacity_W']['Central Plant'] = CHP_BG_capacity_W
    df_installed_capacity['Base_boiler_BG']['Central Plant'] = Base_boiler_BG
    df_installed_capacity['Base_boiler_BG_capacity_W']['Central Plant'] = Base_boiler_BG_capacity_W
    df_installed_capacity['Base_boiler_NG']['Central Plant'] = Base_boiler_NG
    df_installed_capacity['Base_boiler_NG_capacity_W']['Central Plant'] = Base_boiler_NG_capacity_W
    df_installed_capacity['Peak_boiler_BG']['Central Plant'] = Peak_boiler_BG
    df_installed_capacity['Peak_boiler_BG_capacity_W']['Central Plant'] = Peak_boiler_BG_capacity_W
    df_installed_capacity['Backup_boiler_BG_capacity_W']['Central Plant'] = Backup_boiler_BG_capacity_W
    df_installed_capacity['Peak_boiler_NG']['Central Plant'] = Peak_boiler_NG
    df_installed_capacity['Peak_boiler_NG_capacity_W']['Central Plant'] = Peak_boiler_NG_capacity_W
    df_installed_capacity['Backup_boiler_NG_capacity_W']['Central Plant'] = Backup_boiler_NG_capacity_W

    df_installed_capacity['HP_Lake']['Central Plant'] = HP_Lake
    df_installed_capacity['HP_Lake_capacity_W']['Central Plant'] = HP_Lake_capacity_W
    df_installed_capacity['HP_Sewage']['Central Plant'] = HP_Sewage
    df_installed_capacity['HP_Sewage_capacity_W']['Central Plant'] = HP_Sewage_capacity_W
    df_installed_capacity['GHP']['Central Plant'] = GHP
    df_installed_capacity['GHP_capacity_W']['Central Plant'] = GHP_capacity_W
    df_installed_capacity['PV']['Central Plant'] = PV
    df_installed_capacity['PV_capacity_W']['Central Plant'] = PV_capacity_W
    df_installed_capacity['PVT']['Central Plant'] = PVT
    df_installed_capacity['PVT_capacity_W']['Central Plant'] = PVT_capacity_W
    df_installed_capacity['SC_ET']['Central Plant'] = SC_ET
    df_installed_capacity['SC_ET_capacity_W']['Central Plant'] = SC_ET_capacity_W
    df_installed_capacity['SC_FP']['Central Plant'] = SC_FP
    df_installed_capacity['SC_FP_capacity_W']['Central Plant'] = SC_FP_capacity_W
    df_installed_capacity['VCC']['Central Plant'] = VCC
    df_installed_capacity['VCC_capacity_W']['Central Plant'] = VCC_capacity_W
    df_installed_capacity['Backup_VCC_capacity_W']['Central Plant'] = Backup_VCC_capacity_W
    df_installed_capacity['Absorption_Chiller']['Central Plant'] = Absorption_Chiller
    df_installed_capacity['Absorption_Chiller_capacity_W']['Central Plant'] = Absorption_Chiller_capacity_W
    df_installed_capacity['Lake_cooling']['Central Plant'] = Lake_cooling
    df_installed_capacity['Lake_cooling_capacity_W']['Central Plant'] = Lake_cooling_capacity_W
    df_installed_capacity['storage_cooling']['Central Plant'] = storage_cooling
    df_installed_capacity['storage_cooling_capacity_W']['Central Plant'] = storage_cooling_capacity_W

    # Remove the NaN's in the dataframe and save it to a csv file
    df_installed_capacity.fillna(0, inplace=True)
    df_installed_capacity.to_csv(locator.get_optimization_slave_detailed_capacity_of_individual(master_to_slave_vars.individual_number,
                                                                           master_to_slave_vars.generation_number), sep=',')


