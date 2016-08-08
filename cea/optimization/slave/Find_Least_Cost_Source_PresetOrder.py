# -*- coding: utf-8 -*-
"""
FIND LEAST COST FUNCTION
USING PRESET ORDER
    
"""

import os
import time

import numpy as np
import pandas as pd

import Import_Network_Data_functions as INDf
from scipy import interpolate
import copy

def find_KEV_remuneration(P_PV_and_PVT_installedWh, gv):
        """
        Calculates KEV (Kostendeckende Einspeise - Vergütung) for solar PV and PVT.
        Therefore, input the nominal capacity of EACH installation and get the according KEV as return in Rp/kWh
        
        Parameters
        ----------
        P_PV_and_PVT_installed : float
            Nominal Capacity of solar panels (PV or PVT) in Wh
        
        Returns
        -------
        KEV_obtained_in_RpPerkWh : float
            KEV remuneration in Rp / kWh
                    
        """
        
        KEV_regime = [  0,
                        0,
                        20.4,
                        20.4,
                        20.4,
                        20.4,
                        20.4,
                        20.4,
                        19.7,
                        19.3,
                        19,
                        18.9,
                        18.7,
                        18.6,
                        18.5,
                        18.1,
                        17.9,
                        17.8,
                        17.8,
                        17.7,
                        17.7,
                        17.7,
                        17.6,
                        17.6]  
        P_installed_in_kW = [0,
                            9.99,
                            10,
                             12,
                             15,
                             20,
                             29,
                             30,
                             40,
                             50,
                             60,
                             70,
                             80,
                             90,
                             100,
                             200,
                             300,
                             400,
                             500,
                             750,
                             1000,
                             1500,
                             2000,
                             1000000]
        KEV_interpolated_kW = interpolate.interp1d(P_installed_in_kW, KEV_regime, kind = "linear")
        KEV_obtained_in_RpPerkWh = KEV_interpolated_kW(P_PV_and_PVT_installedWh/ 1000.0)
        return KEV_obtained_in_RpPerkWh
        
    

def calculate_emissions_and_CO2(Q_source_data,Q_coldsource_data, E_PP_el_data,\
                                Q_gas_data, Q_wood_data, Q_gas_AdduncoveredBoilerSum, E_aux_AddBoilerSum, ESolarProduced, Q_SCandPVT, \
                                HP_operation_Data_sum_array, Q_storage_content_Wh, context, pathSlaveRes, E_HP_SolarAndHeatRecoverySum,\
                                E_aux_storage_operation_sum, gv):
    
    MS_Var = context
    StorageContentEndOfYear = Q_storage_content_Wh[-1]
    StorageContentStartOfYear = Q_storage_content_Wh[0]
    
    if StorageContentEndOfYear < StorageContentStartOfYear:
        QToCoverByStorageBoiler = float(StorageContentEndOfYear - StorageContentStartOfYear)
        eta_fictive_Boiler = 0.8 # add rather low efficiency as a penalty
        E_gasPrim_fictiveBoiler = QToCoverByStorageBoiler / eta_fictive_Boiler
    
    else:
        E_gasPrim_fictiveBoiler = 0 
    
    # copy data 
    
    Q_HPSew = Q_source_data[:,0]
    Q_HPLake = Q_source_data[:,1]
    Q_GHP = Q_source_data[:,2]
    print "sum of GHP", np.sum(Q_GHP)
    Q_CC = Q_source_data[:,3]
    Q_Furnace = Q_source_data[:,4]
    Q_Boiler = Q_source_data[:,5]
    Q_BoilerPeak = Q_source_data[:,6]
    Q_uncovered = Q_source_data[:,7]
    
    Q_coldsource_HPSew = Q_coldsource_data[:,0]
    Q_coldsource_HPLake = Q_coldsource_data[:,1]
    Q_coldsource_GHP = Q_coldsource_data[:,2]

    Q_gas_CC = Q_gas_data[:,3]
    Q_gas_Boiler = Q_gas_data[:,5]
    Q_gas_Backup = Q_gas_data[:,6]

    Q_wood_Furnace  = Q_wood_data[:,4]

    E_el_CC_produced = E_PP_el_data[:,3]
    E_el_Furnace_produced = E_PP_el_data[:,4]
    E_el_AuxillaryBoilerAllSum = np.sum(E_PP_el_data[:,5]) + np.sum(E_PP_el_data[:,6]) + E_aux_AddBoilerSum
    print "\n E_el_AuxillaryBoilerAllSum",E_el_AuxillaryBoilerAllSum
    print "E_aux_AddBoilerSum", E_aux_AddBoilerSum
    print "np.sum(E_PP_el_data[:,5]) (Base Boiler)", np.sum(E_PP_el_data[:,5])
    print "np.sum(E_PP_el_data[:,6]) (Peak Boiler)", np.sum(E_PP_el_data[:,6])

    # Electricity is accounted for already, no double accounting --> leave it out. 
    # only CO2 / Eprim is not included in the installation part, neglected as its very small compared to operational values
    #QHPServerHeatSum, QHPpvtSum, QHPCompAirSum, QHPScSum = HP_operation_Data_sum_array 
    #print E_PP_el_data
    #print Q_wood_data
    #print Q_coldsource_data
    #print Q_gas_data
    #print Q_source_data
    
    
    # ask for type of fuel, then either us BG or NG 
    if MS_Var.BoilerBackupType == 'BG':
        gas_to_oil_BoilerBackup_std = gv.BG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBackup_std = gv.BG_BOILER_TO_CO2_STD
    else:
        gas_to_oil_BoilerBackup_std = gv.NG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBackup_std = gv.NG_BOILER_TO_CO2_STD
    
    if MS_Var.gt_fuel == 'BG':
        gas_to_oil_CC_std = gv.BG_CC_TO_OIL_STD
        gas_to_co2_CC_std = gv.BG_CC_TO_CO2_STD
        EL_CC_TO_CO2_STD  = gv.EL_BGCC_TO_CO2_STD
        EL_CC_TO_OIL_STD  = gv.EL_BGCC_TO_OIL_EQ_STD
    else:
        gas_to_oil_CC_std = gv.NG_CC_TO_OIL_STD
        gas_to_co2_CC_std = gv.NG_CC_TO_CO2_STD
        EL_CC_TO_CO2_STD  = gv.EL_NGCC_TO_CO2_STD
        EL_CC_TO_OIL_STD  = gv.EL_NGCC_TO_OIL_EQ_STD
        
    if MS_Var.BoilerType == 'BG':
        gas_to_oil_BoilerBase_std = gv.BG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBase_std = gv.BG_BOILER_TO_CO2_STD
    else:
        gas_to_oil_BoilerBase_std = gv.NG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerBase_std = gv.NG_BOILER_TO_CO2_STD
        
    if MS_Var.BoilerPeakType == 'BG':
        gas_to_oil_BoilerPeak_std = gv.BG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerPeak_std = gv.BG_BOILER_TO_CO2_STD
    else:
        gas_to_oil_BoilerPeak_std = gv.NG_BOILER_TO_OIL_STD
        gas_to_co2_BoilerPeak_std = gv.NG_BOILER_TO_CO2_STD
    
    if MS_Var.EL_TYPE == 'green':
        EL_TO_CO2                 = gv.EL_TO_CO2_GREEN
        EL_TO_OIL_EQ              = gv.EL_TO_OIL_EQ_GREEN
    else:
        EL_TO_CO2                 = gv.EL_TO_CO2
        EL_TO_OIL_EQ              = gv.EL_TO_OIL_EQ
        
        
    #evaluate average efficiency, recover normalized data with this efficiency, if-else is there to avoid nan's
    if np.sum(Q_Furnace)    != 0:
        eta_furnace_avg     = np.sum(Q_Furnace) / np.sum(Q_wood_Furnace)
        eta_furnace_el      = np.sum(E_el_Furnace_produced) / np.sum(Q_wood_Furnace)

    else:
        eta_furnace_avg     = 1
        eta_furnace_el      = 1
    
    
    if np.sum(Q_CC)         != 0:
        eta_CC_avg          = np.sum(Q_CC) / np.sum(Q_gas_CC)
        eta_CC_el           = np.sum(E_el_CC_produced) / np.sum(Q_gas_CC)
    else:
        eta_CC_avg          = 1
        eta_CC_el           = 1
        
    if np.sum(Q_Boiler)     != 0:
        eta_Boiler_avg      = np.sum(Q_Boiler) / np.sum(Q_gas_Boiler)
    else:
        eta_Boiler_avg      = 1
    
        
    if np.sum(Q_BoilerPeak) != 0:
        eta_PeakBoiler_avg  = np.sum(Q_BoilerPeak) / np.sum(Q_gas_Backup)
    else:
        eta_PeakBoiler_avg  = 1
    
    if np.sum(Q_uncovered) != 0:
        eta_AddBackup_avg      = np.sum(Q_uncovered) / np.sum(Q_gas_AdduncoveredBoilerSum)
    else:
        eta_AddBackup_avg      = 1
    
    if np.sum(Q_HPSew)     != 0:
        COP_HPSew_avg       = np.sum(Q_HPSew) / (-np.sum(Q_coldsource_HPSew) + np.sum(Q_HPSew))
    else:
        COP_HPSew_avg       = 100.0
        
    print "COP_HPSew_avg", COP_HPSew_avg
    
    if np.sum(Q_GHP)       != 0:
        COP_GHP_avg         = np.sum(Q_GHP) / (-np.sum(Q_coldsource_GHP) + np.sum(Q_GHP))
    else:
        COP_GHP_avg         = 100
        print "COP_GHP_avg",COP_GHP_avg 
    
    if np.sum(Q_HPLake)    != 0:
        COP_HPLake_avg      = np.sum(Q_HPLake) / (-np.sum(Q_coldsource_HPLake) + np.sum(Q_HPLake))
        print "COP_HPLAKEAVG", COP_HPLake_avg
    
    else:
        COP_HPLake_avg      = 100
    #print "COP_HPLake_avg, COP_GHP_avg, COP_HPSew_avg = ", COP_HPLake_avg, COP_GHP_avg, COP_HPSew_avg
    
    
    ######### COMPUTE THE GHG emissions
    
    CO2_from_Sewage     = np.sum(Q_HPSew) / COP_HPSew_avg * gv.SEWAGEHP_TO_CO2_STD  * gv.Wh_to_J / 1.0E6
    CO2_from_GHP        = np.sum(Q_GHP) / COP_GHP_avg * gv.GHP_TO_CO2_STD  * gv.Wh_to_J / 1.0E6
    CO2_from_HPLake     = np.sum(Q_HPLake) / COP_HPLake_avg * gv.LAKEHP_TO_CO2_STD * gv.Wh_to_J / 1.0E6
    
    CO2_from_HP         = CO2_from_Sewage + CO2_from_GHP + CO2_from_HPLake
                             
    
    CO2_from_CC_gas         = 1 /eta_CC_avg * np.sum(Q_CC) * gas_to_co2_CC_std  * gv.Wh_to_J / 1.0E6
    CO2_from_BaseBoiler_gas = 1 /eta_Boiler_avg * np.sum(Q_Boiler) * gas_to_co2_BoilerBase_std   * gv.Wh_to_J / 1.0E6
    CO2_from_PeakBoiler_gas = 1 /eta_PeakBoiler_avg * np.sum(Q_BoilerPeak) * gas_to_co2_BoilerPeak_std * gv.Wh_to_J / 1.0E6
    CO2_from_AddBoiler_gas  = 1 /eta_AddBackup_avg * np.sum(Q_uncovered) * gas_to_co2_BoilerBackup_std * gv.Wh_to_J / 1.0E6

    CO2_from_fictiveBoilerStorage= E_gasPrim_fictiveBoiler * gv.NG_BOILER_TO_CO2_STD  * gv.Wh_to_J /1.0E6
    
                                                                         
    CO2_from_gas        = CO2_from_CC_gas + CO2_from_BaseBoiler_gas + CO2_from_PeakBoiler_gas + CO2_from_AddBoiler_gas \
                                + CO2_from_fictiveBoilerStorage


    CO2_from_wood       = np.sum(Q_Furnace) * gv.FURNACE_TO_CO2_STD / eta_furnace_avg * gv.Wh_to_J / 1.0E6

    
    CO2_from_elec_sold  = np.sum(E_el_Furnace_produced) * (- EL_TO_CO2)  * gv.Wh_to_J / 1.0E6\
                            + np.sum(E_el_CC_produced) * (- EL_TO_CO2)  * gv.Wh_to_J / 1.0E6 \
                            + ESolarProduced * (gv.EL_PV_TO_CO2 - EL_TO_CO2)  * gv.Wh_to_J / 1.0E6 # ESolarProduced contains PV and PVT values
    
    CO2_from_elec_usedAuxBoilersAll  = E_el_AuxillaryBoilerAllSum * EL_TO_CO2 * gv.Wh_to_J / 1E6
    
    CO2_from_SCandPVT   = Q_SCandPVT * gv.SOLARCOLLECTORS_TO_CO2  * gv.Wh_to_J / 1.0E6
    
    CO2_from_HPSolarandHearRecovery = E_HP_SolarAndHeatRecoverySum * EL_TO_CO2 * gv.Wh_to_J / 1E6
    CO2_from_HP_StorageOperationChDeCh = E_aux_storage_operation_sum * EL_TO_CO2 * gv.Wh_to_J / 1E6
    
    # save data
    results = pd.DataFrame({
                            "CO2_from_Sewage":[CO2_from_Sewage],
                            "CO2_from_GHP":[CO2_from_GHP],
                            "CO2_from_HPLake":[CO2_from_HPLake],
                            "CO2_from_CC_gas":[CO2_from_CC_gas],
                            "CO2_from_BaseBoiler_gas":[CO2_from_BaseBoiler_gas],
                            "CO2_from_PeakBoiler_gas":[CO2_from_PeakBoiler_gas],
                            "CO2_from_AddBoiler_gas":[CO2_from_AddBoiler_gas],
                            "CO2_from_fictiveBoilerStorage":[CO2_from_fictiveBoilerStorage],
                            "CO2_from_wood":[CO2_from_wood],
                            "CO2_from_elec_sold":[CO2_from_elec_sold],
                            "CO2_from_SCandPVT":[CO2_from_SCandPVT],
                            "CO2_from_elec_usedAuxBoilersAll":[CO2_from_elec_usedAuxBoilersAll],
                            "CO2_from_HPSolarandHearRecovery":[CO2_from_HPSolarandHearRecovery],
                            "CO2_from_HP_StorageOperationChDeCh":[CO2_from_HP_StorageOperationChDeCh]
                            })
    Name = MS_Var.configKey + "_SlaveDetailedEmissionData.csv"
    os.chdir(pathSlaveRes)
    results.to_csv(Name, sep= ',')

    #CO2_from_AuxElectricity= (E_aux_AddBoilerSum + E_el_Backup + E_el_BoilerBase) * Electricity_to_CO2 # Not used as the conversion factors
    #                                                                                           of the machinery takes into account final energy
                                                                                
    
    ################## Primary energy needs
    
    Eprim_from_Sewage = np.sum(Q_HPSew) / COP_HPSew_avg  * gv.SEWAGEHP_TO_OIL_STD * gv.Wh_to_J / 1.0E6
    Eprim_from_GHP    = np.sum(Q_GHP) / COP_GHP_avg * gv.GHP_TO_OIL_STD  * gv.Wh_to_J / 1.0E6
    Eprim_from_HPLake = np.sum(Q_HPLake) / COP_HPLake_avg * gv.LAKEHP_TO_OIL_STD  * gv.Wh_to_J / 1.0E6
    
    Eprim_from_HP       =  Eprim_from_Sewage + Eprim_from_GHP + Eprim_from_HPLake
    
                                                                              
    E_prim_from_CC_gas          = 1 / eta_CC_avg * np.sum(Q_CC) * gas_to_oil_CC_std  * gv.Wh_to_J/  1.0E6
    E_prim_from_BaseBoiler_gas  = 1 /eta_Boiler_avg * np.sum(Q_Boiler) * gas_to_oil_BoilerBase_std   * gv.Wh_to_J / 1.0E6
    E_prim_from_PeakBoiler_gas  = 1 /eta_PeakBoiler_avg * np.sum(Q_BoilerPeak) * gas_to_oil_BoilerPeak_std * gv.Wh_to_J / 1.0E6
    E_prim_from_AddBoiler_gas   = 1 /eta_AddBackup_avg * np.sum(Q_uncovered) * gas_to_oil_BoilerBackup_std  * gv.Wh_to_J / 1.0E6
    E_prim_from_FictiveBoiler_gas= E_gasPrim_fictiveBoiler * gv.NG_BOILER_TO_OIL_STD  * gv.Wh_to_J / 1.0E6
 
    Eprim_from_gas      = E_prim_from_CC_gas + E_prim_from_BaseBoiler_gas + E_prim_from_PeakBoiler_gas\
                                + E_prim_from_AddBoiler_gas +E_prim_from_FictiveBoiler_gas
                                
                                               
    Eprim_from_wood     = 1 /eta_furnace_avg * np.sum(Q_Furnace) * gv.FURNACE_TO_OIL_STD * gv.Wh_to_J / 1.0E6

    EprimSaved_from_elec_sold_Furnace = np.sum(E_el_Furnace_produced) * (- EL_TO_OIL_EQ) * gv.Wh_to_J / 1.0E6
    EprimSaved_from_elec_sold_CHP     = np.sum(E_el_CC_produced) * (- EL_TO_OIL_EQ) * gv.Wh_to_J / 1.0E6
    EprimSaved_from_elec_sold_Solar   = ESolarProduced * (gv.EL_PV_TO_OIL_EQ - EL_TO_OIL_EQ)  * gv.Wh_to_J / 1.0E6

    print "np.sum(E_el_CC_produced)",np.sum(E_el_CC_produced)
    print "EprimSaved_from_elec_sold_CHP",EprimSaved_from_elec_sold_CHP
    print "EprimSaved_from_elec_sold_Furnace", EprimSaved_from_elec_sold_Furnace
    print "\n eta_furnace_avg : ",eta_furnace_avg
    print "E_el_Furnace_produced",np.sum(E_el_Furnace_produced)
    print "eta_CC_avg", eta_CC_avg
    print "np.sum(E_el_CC_produced)", np.sum(E_el_CC_produced)
    print "EprimSaved_from_elec_sold_Solar",EprimSaved_from_elec_sold_Solar
    
    EprimSaved_from_elec_sold= EprimSaved_from_elec_sold_Furnace + EprimSaved_from_elec_sold_CHP + EprimSaved_from_elec_sold_Solar
                           
                            # E_PV_Wh contains PV and PVT values (Units Wh * MJ/MJ, later on translated from Wh to MJ) 
                            
    #Eprim_from_AuxElectricity= (E_aux_AddBoilerSum + E_el_Backup + E_el_BoilerBase) * Electricity_to_CO2 # Not used as the conversion factors
    #                                                                                           of the machinery takes into account final energy
                           
    #print "Eprim_from_elec_sold",Eprim_from_elec_sold
    Eprim_from_elec_usedAuxBoilersAll  = E_el_AuxillaryBoilerAllSum * EL_TO_OIL_EQ  * gv.Wh_to_J / 1.0E6

    Eprim_from_SCandPVT = Q_SCandPVT * gv.SOLARCOLLECTORS_TO_OIL * gv.Wh_to_J / 1.0E6
    #print "Eprim_from_SCandPVT", Eprim_from_SCandPVT             
                            
    Eprim_from_HPSolarandHearRecovery = E_HP_SolarAndHeatRecoverySum * EL_TO_OIL_EQ  * gv.Wh_to_J / 1.0E6
    Eprim_from_HP_StorageOperationChDeCh = E_aux_storage_operation_sum * EL_TO_CO2 * gv.Wh_to_J / 1E6

         
    # Save data
    results = pd.DataFrame({
                            "Eprim_from_Sewage":[Eprim_from_Sewage],
                            "Eprim_from_GHP":[Eprim_from_GHP],
                            "Eprim_from_HPLake":[Eprim_from_HPLake],
                            "E_prim_from_CC_gas":[E_prim_from_CC_gas],
                            "E_prim_from_BaseBoiler_gas":[E_prim_from_BaseBoiler_gas],
                            "E_prim_from_PeakBoiler_gas":[E_prim_from_PeakBoiler_gas],
                            "E_prim_from_AddBoiler_gas":[E_prim_from_AddBoiler_gas],
                            "E_prim_from_FictiveBoiler_gas":[E_prim_from_FictiveBoiler_gas],
                            "Eprim_from_wood":[Eprim_from_wood],
                            "EprimSaved_from_elec_sold_Furnace":[EprimSaved_from_elec_sold_Furnace],
                            "EprimSaved_from_elec_sold_CC":[EprimSaved_from_elec_sold_CHP],
                            "EprimSaved_from_elec_sold_Solar":[EprimSaved_from_elec_sold_Solar],
                            "Eprim_from_elec_usedAuxBoilersAll":[Eprim_from_elec_usedAuxBoilersAll],
                            "Eprim_from_HPSolarandHearRecovery":[Eprim_from_HPSolarandHearRecovery],
                            "Eprim_from_HP_StorageOperationChDeCh":[Eprim_from_HP_StorageOperationChDeCh]
                            })
    Name = MS_Var.configKey + "_SlaveDetailedEprimData.csv"
    os.chdir(pathSlaveRes)
    results.to_csv(Name, sep= ',')
    
    
    ######### Summed up results    
    CO2_emitted     = (CO2_from_HP + CO2_from_gas + CO2_from_wood + CO2_from_elec_sold + CO2_from_SCandPVT + CO2_from_elec_usedAuxBoilersAll\
                                                                + CO2_from_HPSolarandHearRecovery + CO2_from_HP_StorageOperationChDeCh) 
                                                                
    Eprim_used      = (Eprim_from_HP + Eprim_from_gas + Eprim_from_wood + EprimSaved_from_elec_sold\
                                            + Eprim_from_SCandPVT + Eprim_from_elec_usedAuxBoilersAll + Eprim_from_HPSolarandHearRecovery\
                                            + Eprim_from_HP_StorageOperationChDeCh) 
    print "\n CO2_from_elec_sold",CO2_from_elec_sold
    print "EprimSaved_from_elec_sold",EprimSaved_from_elec_sold 
    
    print "\n CO2_from_gas", CO2_from_gas
    print "Eprim_from_gas", Eprim_from_gas
                             
    print "\n CO2_from_SCandPVT",CO2_from_SCandPVT
    print "Eprim_from_SCandPVT", Eprim_from_SCandPVT
    
    print "\n CO2_from_elec_usedAuxBoilersAll",CO2_from_elec_usedAuxBoilersAll
    print "Eprim_from_elec_usedAuxBoilersAll",Eprim_from_elec_usedAuxBoilersAll
    
    print "\nCO2_from_HP_StorageOperationChDeCh", CO2_from_HP_StorageOperationChDeCh    
    print "Eprim_from_HP_StorageOperationChDeCh", Eprim_from_HP_StorageOperationChDeCh
    
    print "\n CO2_from_HPSolarandHearRecovery", CO2_from_HPSolarandHearRecovery
    print "Eprim_from_HPSolarandHearRecovery",Eprim_from_HPSolarandHearRecovery
    
    
    
    #print Eprim_used
    #print CO2_emitted
    
    return CO2_emitted, Eprim_used



def Least_Cost_Optimization(locator, context, solarFeat, gv):
    """
    This function runs the least cost optimization code and returns cost, co2 and primary energy required. \
    On the go, it saves the operation pattern
    
    Parameters
    ----------
    pathSlaveRes : string
            Path of Slave results (storage + operation pattern)
        
    pathNtwRes : string
        Path of Network summary results
    
    context : string
        Dataset of Master To Slave Variables, defined as a module
        
    
    Returns
    -------
    E_oil_eq_MJ : float
        MJ oil Equivalent used during operation
    
    CO2_kg_eq : float
        kg of CO2-Equivalent emitted during operation
        
    cost_sum : float
        total cost in CHF used for operation 
        
    Q_source_data[:,7] : array 
        uncovered demand
    
    """
    
    print "Least Cost Optimization Ready \n"
    MS_Var = context 
    
    t = time.time()
    Network_Raw_Data_Path = locator.pathNtwRes
    
    #class MS_VarError(Exception):
     #   """Base class for exceptions in this module."""
      #  pass
    
    #class ModelError(Exception):
     #   """Base class for exceptions in this module."""
      #  pass
        
        
    """ IMPORT DATA """
    
    # Import Demand Data:
    os.chdir(locator.pathSlaveRes)
    CSV_NAME =  MS_Var.configKey + "StorageOperationData.csv"
    Centralized_Plant_Requirements = INDf.import_CentralizedPlant_data(CSV_NAME, gv.DAYS_IN_YEAR, gv.HOURS_IN_DAY)
    Q_DH_networkload, E_aux_ch,E_aux_dech, Q_missing, Q_storage_content_Wh, Q_to_storage, Q_from_storage, \
                Q_uncontrollable, E_PV_Wh, E_PVT_Wh, E_aux_HP_uncontrollable, Q_SCandPVT, HPServerHeatDesignArray,\
                HPpvt_designArray, HPCompAirDesignArray, HPScDesignArray, E_produced_solarAndHPforSolar,\
                E_consumed_without_buildingdemand_solarAndHPforSolar\
                                                                    = Centralized_Plant_Requirements
    
    Q_StorageToDHNpipe_sum = np.sum(E_aux_dech) + np.sum(Q_from_storage)
    
    #E_PVT_Wh = np.sum(E_PVT_Wh_Array)
    
    HP_operation_Data_sum_array = np.sum(HPServerHeatDesignArray), \
                                  np.sum(HPpvt_designArray), \
                                  np.sum(HPCompAirDesignArray), \
                                  np.sum(HPScDesignArray)
                                  
    Q_missing_copy = Q_missing.copy()
    
    NETWORK_DATA_FILE = MS_Var.NETWORK_DATA_FILE
    
    # Import Temperatures from Network Summary: 
    
    os.chdir(Network_Raw_Data_Path)
    tdhret = np.array(pd.read_csv(NETWORK_DATA_FILE, usecols=["T_sst_heat_return_netw_total"], nrows=gv.DAYS_IN_YEAR* gv.HOURS_IN_DAY))
    mdot_DH = np.array(pd.read_csv(NETWORK_DATA_FILE, usecols=["mdot_DH_netw_total"], nrows=gv.DAYS_IN_YEAR* gv.HOURS_IN_DAY))
    tdhsup = np.array(pd.read_csv(NETWORK_DATA_FILE, usecols=["T_sst_heat_supply_netw_total"], nrows=1))[0][0]
    
    # import Marginal Cost of PP Data :
    #os.chdir(Cost_Maps_Path)
    
        
    
    """ LOAD MODULES """
    
    #    Boiler
    if (MS_Var.Boiler_on) == 1 or (MS_Var.BoilerPeak_on) == 1 or 1: # always import boilers as the backup might be used in case of non-convergence
        #os.chdir(Cost_Maps_Path)
        import cea.technologies.boilers as CMBoil
        #os.chdir(Cost_Maps_Path)
        reload(CMBoil)
        BoilerCond_op_cost = CMBoil.BoilerCond_op_cost
    
    #   Furnace
    if (MS_Var.Furnace_on) == 1:
        #os.chdir(Cost_Maps_Path)
        import cea.technologies.furnace as CMFurn
        #os.chdir(Cost_Maps_Path)
        reload(CMFurn)
        Furnace_op_cost = CMFurn.Furnace_op_cost
    
    # Heat Pumps
    if (MS_Var.GHP_on) == 1 or (MS_Var.HP_Lake_on) == 1 or (MS_Var.HP_Sew_on) == 1 :
        import cea.technologies.heatpumps as CMHP
        import cea.technologies.heatpumps as ESMHP
        HPLake_op_cost = CMHP.HPLake_op_cost
        HPSew_op_cost = CMHP.HPSew_op_cost
        GHP_op_cost = CMHP.GHP_op_cost
        GHP_Op_max = ESMHP.GHP_Op_max
            
    # CHP 
    if (MS_Var.CC_on) == 1:
        import cea.technologies.cogeneration as chp
        CC_op_cost = chp.calc_Cop_CCT
        # How to use: for e.g. cost_per_Wh(Q_therm):
        # type cost_per_Wh_fn = CC_op_cost(10E6, 273+70.0, "NG")[2]
        # similar: Q_used_prim_fn = CC_op_cost(10E6, 273+70.0, "NG")[1]
        # then: ask for Q_therm_req: 
        # Q_used_prim = Q_used_prim_fn(Q_therm_req) OR cost_per_Wh = cost_per_Wh_fn(Q_therm_req)
    

    """ Fixed order COST ALGORITHM STARTS """ # Run the Centralized Plant Operation Scheme
    
    # Import Data - Sewage
    #mdotsew = 0.0
    #tsupsew = 20 + 273.0
    if gv.HPSew_allowed == 1:
        QcoldsewArray = np.array(pd.read_csv(locator.get_sewageheat_potential , usecols=["Qsw_kW"])) * 1E3
        TretsewArray = np.array(pd.read_csv(locator.get_sewageheat_potential , usecols=["ts_C"])) + 273
    
    
    def source_activator(Q_therm_req, hour, context):
        Q_therm_req_COPY = copy.copy(Q_therm_req)
        MS_Var = context
        current_source = gv.act_first # Start with first source, no cost yet
        mdot_DH_req = mdot_DH[hour,0]
        tdhret_req = tdhret[hour,0]
        Q_uncovered = 0
        # Initializing resulting values (necessairy as not all of them are over-written):
        
        costHPSew, costHPLake, costGHP, costCC, costFurnace, costBoiler, costBackup = 0,0,0,0,0,0,0
        
        # initialize all sources to be off = 0 (turn to "on" with setting to 1)
        sHPSew = 0
        sHPLake = 0 
        srcGHP = 0 
        sorcCC = 0
        sorcFurnace = 0
        sBoiler = 0
        sBackup = 0
        Q_excess = 0
        Q_HPSew, Q_HPLake, Q_GHP, Q_CC, Q_Furnace, Q_Boiler, Q_Backup = 0,0,0,0,0,0,0
        E_el_HPSew, E_el_HPLake, E_el_GHP, E_el_CC_produced, E_el_Furnace_produced, E_el_BoilerBase, E_el_Backup = 0,0,0,0,0,0,0
        E_gas_HPSew, E_gas_HPLake, E_gas_GHP, E_gas_CC, E_gas_Furnace, E_gas_Boiler, E_gas_Backup = 0,0,0,0,0,0,0
        E_wood_HPSew, E_wood_HPLake, E_wood_GHP, E_wood_CC, E_wood_Furnace, E_wood_Boiler, E_wood_Backup = 0,0,0,0,0,0,0
        E_coldsource_HPSew, E_coldsource_HPLake,  E_coldsource_GHP, E_coldsource_CC, \
                            E_coldsource_Furnace, E_coldsource_Boiler,  E_coldsource_Backup = 0,0,0,0,0,0,0
    

        #print "Slave has uncovered demand?", Q_therm_req, " (if zero then no)"
        #print "else, the slave routine's while loop (PP Activation) will be started"
        while Q_therm_req > 1E-1: # cover demand as long as the supply is lower than demand!
            #print Q_therm_req, "Wh will now be covered, hour:", hour

            if current_source == 'HP':# use heat pumps available!
                
                #print "current_source", current_source
                
                if (MS_Var.HP_Sew_on) == 1 and Q_therm_req  > 0 and gv.HPSew_allowed == 1: # activate if its available
                    
                    sHPSew = 0
                    costHPSew= 0.0
                    Q_HPSew = 0.0
                    E_el_HPSew = 0.0
                    E_coldsource_HPSew = 0.0
                    
                    if Q_therm_req > MS_Var.HPSew_maxSize:
                        Q_therm_Sew = MS_Var.HPSew_maxSize
                        mdot_DH_to_Sew = mdot_DH_req * Q_therm_Sew / Q_therm_req.copy() #scale down the mass flow if the thermal demand is lowered
                        #Q_therm_req -= MS_Var.HPSew_maxSize
                    
                    else:
                        Q_therm_Sew = float(Q_therm_req.copy())
                        mdot_DH_to_Sew = float(mdot_DH_req.copy())
                        #Q_therm_req = 0
                    
                    HP_Sew_Cost_Data = HPSew_op_cost(mdot_DH_to_Sew, tdhsup, tdhret_req, TretsewArray[hour][0], gv)
                    C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_HPSew_cold_primary, Q_HPSew_therm, E_HPSew_el  = HP_Sew_Cost_Data
                    Q_therm_req -= Q_HPSew_therm
                    #print "C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_HPSew_cold_primary, Q_HPSew_therm", \
                    #                        C_HPSew_el_pure, C_HPSew_per_kWh_th_pure, Q_HPSew_cold_primary, Q_HPSew_therm
                    
                    # Storing data for further processing
                    if Q_HPSew_therm > 0:
                        sHPSew = 1
                    costHPSew= float(C_HPSew_el_pure)
                    Q_HPSew = float(Q_HPSew_therm)
                    #print "\n Q_HPSew", Q_HPSew
                    E_el_HPSew = float(E_HPSew_el)
                    E_coldsource_HPSew = float(Q_HPSew_cold_primary)
                    
                
                if (MS_Var.GHP_on) == 1 and hour >= MS_Var.GHP_SEASON_ON and  hour <= MS_Var.GHP_SEASON_OFF and Q_therm_req > 0: 
                                                                # activating GHP plant if possible
                    
                    #print "is GHP on?", MS_Var.GHP_on
                    srcGHP = 0
                    costGHP = 0.0
                    Q_GHP = 0.0
                    E_el_GHP = 0.0
                    E_coldsource_GHP = 0.0
                    
                    Q_max, GHP_COP  = GHP_Op_max(tdhsup, gv.TGround, MS_Var.GHP_number, gv)
                    
                    if Q_therm_req > Q_max:
                        mdot_DH_to_GHP = Q_max / (gv.cp *(tdhsup -tdhret_req))
                        Q_therm_req -= Q_max
    
                    else: # regular operation possible, demand is covered
                        mdot_DH_to_GHP = Q_therm_req.copy() / (gv.cp * (tdhsup -tdhret_req))
                        Q_therm_req = 0
                    
                    GHP_Cost_Data = GHP_op_cost(mdot_DH_to_GHP, tdhsup, tdhret_req, gv, GHP_COP)
                    C_GHP_el, Wdot_GHP, Q_GHP_cold_primary, Q_GHP_therm  = GHP_Cost_Data
                    
                    # Storing data for further processing
                    srcGHP = 1
                    costGHP = C_GHP_el
                    Q_GHP = Q_GHP_therm
                    E_el_GHP = Wdot_GHP
                    E_coldsource_GHP = Q_GHP_cold_primary
    
                if (MS_Var.HP_Lake_on) == 1 and Q_therm_req > 0 and gv.HPLake_allowed == 1: # run Heat Pump Lake
                    sHPLake  = 0
                    costHPLake = 0
                    Q_HPLake = 0
                    E_el_HPLake = 0
                    E_coldsource_HPLake = 0
                    
                    if Q_therm_req > MS_Var.HPLake_maxSize: # Scale down Load, 100% load achieved
                        Q_therm_HPL = MS_Var.HPLake_maxSize
                        mdot_DH_to_Lake = Q_therm_HPL / (gv.cp *(tdhsup - tdhret_req)) #scale down the mass flow if the thermal demand is lowered
                        Q_therm_req -=  MS_Var.HPLake_maxSize
    
                    else: # regular operation possible
                        Q_therm_HPL = Q_therm_req.copy()
                        mdot_DH_to_Lake = Q_therm_HPL / (gv.cp *(tdhsup - tdhret_req))
                        Q_therm_req = 0
                    print tdhsup
                    HP_Lake_Cost_Data = HPLake_op_cost(mdot_DH_to_Lake, tdhsup, tdhret_req, gv.TLake, gv)
                    C_HPL_el, Wdot_HPLake, Q_HPL_cold_primary, Q_HPL_therm = HP_Lake_Cost_Data
                    
                    # Storing Data
                    sHPLake  = 1
                    costHPLake = C_HPL_el
                    Q_HPLake = Q_therm_HPL
                    E_el_HPLake = Wdot_HPLake
                    E_coldsource_HPLake = Q_HPL_cold_primary
                 
                #print Q_therm_req, "Q left"             
                
            if current_source == 'CHP' and Q_therm_req > 0: # start activating the combined cycles
                
                #print "current_source", current_source
                
                #By definition, one can either activate the CHP (NG-CC) or ORC (Furnace) BUT NOT BOTH at the same time (not activated by Master)
                Cost_CC = 0.0 
                sorcCC = 0
                costCC = 0.0
                Q_CC = 0.0
                E_gas_CC = 0.0
                E_el_CC_produced = 0
                
                if (MS_Var.CC_on) == 1 and Q_therm_req > 0 and gv.CC_allowed == 1: # only operate if the plant is available
                    CC_op_cost_data = CC_op_cost(MS_Var.CC_GT_SIZE, tdhsup, MS_Var.gt_fuel, gv) # create cost information
                    Q_used_prim_CC_fn  = CC_op_cost_data[1]
                    cost_per_Wh_CC_fn = CC_op_cost_data[2] #gets interpolated cost function
                    Q_CC_min = CC_op_cost_data[3]
                    Q_CC_max = CC_op_cost_data[4]
                    eta_elec_interpol= CC_op_cost_data[5]
                    
                    if Q_therm_req > Q_CC_min: # operation Possible if above minimal load
                        print MS_Var.CC_GT_SIZE, MS_Var.gt_fuel, tdhsup, Q_therm_req, Q_CC_min, Q_CC_max
                        if Q_therm_req < Q_CC_max:# Normal operation Possible within partload regime
                            cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_therm_req)
                            Q_used_prim_CC = Q_used_prim_CC_fn(Q_therm_req)
                            Q_CC_delivered = Q_therm_req.copy()
                            Q_therm_req = 0
                            #print Q_used_prim_CC, "Q_used_prim_CC"
                            #print Q_CC_delivered, "Q_CC_delivered"
                            E_el_CC_produced = np.float(eta_elec_interpol(Q_used_prim_CC)) * Q_used_prim_CC
                            #print "CC electric efficiency:", np.float(eta_elec_interpol(Q_CC_max)) 
                            #print "Q_CC_delivered", Q_CC_delivered
                            #print "E_el_CC", np.shape(E_el_CC), E_el_CC
                            

                        else: # Only part of the demand can be delivered as 100% load achieved
                            cost_per_Wh_CC = cost_per_Wh_CC_fn(Q_CC_max)
                            Q_used_prim_CC = Q_used_prim_CC_fn(Q_CC_max)
                            Q_CC_delivered = Q_CC_max
                            Q_therm_req -= Q_CC_max
                            #print "CC electric efficiency:", np.float(eta_elec_interpol(Q_CC_max)) 
                            #print "Q_CC_delivered", Q_CC_delivered
                            E_el_CC_produced = np.float(eta_elec_interpol(Q_CC_max)) * Q_used_prim_CC
                            #print "E_el_CC", np.shape(E_el_CC), E_el_CC
                        
                        Cost_CC = cost_per_Wh_CC * Q_CC_delivered 
                        sorcCC = 1
                        costCC = Cost_CC
                        Q_CC = Q_CC_delivered
                        E_gas_CC = Q_used_prim_CC  
                    else:
                        print "CC below part load"                 
            
                if (MS_Var.Furnace_on) == 1 and Q_therm_req > 0: # Activate Furnace if its there. By definition, either ORC or NG-CC!
                    Q_Furn_therm = 0
                    sorcFurnace = 0
                    costFurnace = 0.0
                    Q_Furnace = 0.0
                    E_wood_Furnace = 0.0
                    Q_Furn_prim = 0.0
                    
                    if Q_therm_req > (gv.Furn_min_Load * MS_Var.Furnace_Q_max): # Operate only if its above minimal load
    
                        if Q_therm_req > MS_Var.Furnace_Q_max: # scale down if above maximum load, Furnace operates at max. capacity
                            Furnace_Cost_Data = Furnace_op_cost(MS_Var.Furnace_Q_max, MS_Var.Furnace_Q_max, tdhret_req, MS_Var.Furn_Moist_type, gv)
                            
                            C_Furn_therm = Furnace_Cost_Data[0]
                            Q_Furn_prim = Furnace_Cost_Data[2]
                            Q_Furn_therm = MS_Var.Furnace_Q_max
                            Q_therm_req -= Q_Furn_therm
                            E_el_Furnace_produced = Furnace_Cost_Data[4]
                            #print "\n E_el_Furnace",np.shape(E_el_Furnace), E_el_Furnace
    
            
                        else: # Normal Operation Possible
                            Furnace_Cost_Data = Furnace_op_cost(Q_therm_req, MS_Var.Furnace_Q_max, tdhret_req, MS_Var.Furn_Moist_type, gv)
    
                            Q_Furn_prim = Furnace_Cost_Data[2]
                            C_Furn_therm = Furnace_Cost_Data[0]
                            Q_Furn_therm = Q_therm_req.copy()
                            E_el_Furnace_produced = Furnace_Cost_Data[4]

                            Q_therm_req = 0 
                            
                        sorcFurnace = 1
                        costFurnace = C_Furn_therm.copy()
                        Q_Furnace = Q_Furn_therm
                        E_wood_Furnace = Q_Furn_prim
                        #print "Q_Furn_therm", Q_Furn_therm
                        #print "E_el_Furnace_produced", E_el_Furnace_produced
                        
                    else:
                        print "Furnace below minimum load!"
                        
                #print Q_therm_req, "Q left"
                        
            if current_source == 'BoilerBase' and Q_therm_req > 0:
                
                #print "current_source", current_source
                
                Q_therm_boiler = 0
                if (MS_Var.Boiler_on) == 1:
                    sBoiler = 0
                    costBoiler = 0.0
                    Q_Boiler = 0.0                     
                    E_gas_Boiler = 0.0
                    E_el_BoilerBase = 0.0
                    
                    if Q_therm_req >= gv.Boiler_min*MS_Var.Boiler_Q_max: # Boiler can be activated?
                        #Q_therm_boiler = Q_therm_req
                        
                        if Q_therm_req >= MS_Var.Boiler_Q_max: # Boiler above maximum Load?
                            Q_therm_boiler = MS_Var.Boiler_Q_max
                        else:
                            Q_therm_boiler = Q_therm_req.copy()

                        Boiler_Cost_Data = BoilerCond_op_cost(Q_therm_boiler, MS_Var.Boiler_Q_max, tdhret_req, \
                                                context.BoilerType, context.EL_TYPE, gv)
                        C_boil_therm, C_boil_per_Wh, Q_primary, E_aux_Boiler = Boiler_Cost_Data
                        
                        sBoiler = 1
                        costBoiler = C_boil_therm
                        Q_Boiler = Q_therm_boiler                     
                        E_gas_Boiler = Q_primary
                        E_el_BoilerBase = E_aux_Boiler
                        Q_therm_req -= Q_therm_boiler
                        #print "Base Boiler activated with ", Q_therm_boiler
                        #print "E_el_BoilerBase ",E_el_BoilerBase
                    else:
                        print "Base Boiler not activated (below part load)"
                
                #print Q_therm_req, "Q left"
                
            if current_source == 'BoilerPeak' and Q_therm_req > 0:
                #print "current_source", current_source
    
                if (MS_Var.BoilerPeak_on) == 1:
                    sBackup = 0
                    costBackup = 0.0
                    Q_Backup = 0.0 
                    E_gas_Backup = 0
                    E_el_Backup = 0
                    
                    if Q_therm_req > 0: #gv.Boiler_min*MS_Var.BoilerPeak_Q_max: # Boiler can be activated?
    
                        if Q_therm_req > MS_Var.BoilerPeak_Q_max: # Boiler above maximum Load?
                            Q_therm_boilerP = MS_Var.BoilerPeak_Q_max
                            Q_therm_req -= Q_therm_boilerP
                        else:                     
                            Q_therm_boilerP = Q_therm_req.copy()
                            Q_therm_req = 0
    
                        Boiler_Cost_DataP = BoilerCond_op_cost(Q_therm_boilerP, MS_Var.BoilerPeak_Q_max, tdhret_req, \
                                                context.BoilerPeakType, context.EL_TYPE, gv)
                        C_boil_thermP, C_boil_per_WhP, Q_primaryP, E_aux_BoilerP = Boiler_Cost_DataP
                        
                        sBackup = 1
                        costBackup = C_boil_thermP
                        Q_Backup = Q_therm_boilerP 
                        E_gas_Backup = Q_primaryP
                        E_el_Backup = E_aux_BoilerP
                        #print "Peak Boiler activated with ", Q_Backup
                        #print "E_el_Backup ",E_el_Backup
                    

                #print Q_therm_req, "Q left"
    
            """
            print "\n currently activated source: ", current_source
            print "available sources :", "\n Boiler", MS_Var.Boiler_on,\
                                         "\n BoilerPeak_on", MS_Var.BoilerPeak_on, \
                                         "\n Furnace_on", MS_Var.Furnace_on,\
                                         "\n GHP_on", MS_Var.GHP_on,\
                                         "\n HP_Lake_on", MS_Var.HP_Lake_on,\
                                         "\n HP_Sew_on", MS_Var.HP_Sew_on,\
                                         "\n CC_on",MS_Var.CC_on,\
                                         "\n WasteServersHeatRecovery", MS_Var.WasteServersHeatRecovery,\
                                         "\n WasteCompressorHeatRecovery", MS_Var.WasteCompressorHeatRecovery
                                         
            """
            Q_excess = 0
            if np.floor(Q_therm_req) > 0:
                if current_source == gv.act_first:
                    current_source = gv.act_second
                    #print "switch to", gv.act_second, "\n"
                elif current_source == gv.act_second:
                    current_source = gv.act_third
                    #print "switch to", gv.act_third, "\n"
                elif current_source == gv.act_third:
                    current_source = gv.act_fourth
                    #print "switch to", gv.act_fourth, "\n"
                else:
                    Q_uncovered = Q_therm_req
                    """
                    print "not covered demand: ", Q_remaining, "Wh"
                    print "last source tested: ", current_source
                    print "occured in hour: ", hour
                    print "insufficient capacity installed! Cannot cover the network demand (check Slave code, find_least_cost_source_main"
                    #break
                    """
                    print "not sufficient capacity installed in hour : ", hour
                    print Q_therm_req, "Wh missing"
                    print "check least cost optimization (here the error comes from) but also the inputs: "
                    print "It is not sufficient capacity available to the slave in order to fulfull the thermal "
                    print "demand of the network (think about the bands or gaps that occur when a system has a minimum load"
                    print "This is now covered by a boiler"
                    
                    print Q_therm_req_COPY, "Wh was required \n"
                    #print sHPSew, sHPLake,  srcGHP,  sorcCC, sorcFurnace, sBoiler,  sBackup, "sHPSew, sHPLake,  srcGHP,  sorcCC,\
                    #sorcFurnace, sBoiler,  sBackup"
                    #print "Q_HPSew, Q_HPLake, Q_GHP, Q_CC, Q_Furnace, Q_Boiler, Q_Backup ", Q_HPSew, Q_HPLake, Q_GHP, Q_CC, \
                    #Q_Furnace, Q_Boiler, Q_Backup 
                    #print MS_Var.Boiler_on, MS_Var.BoilerPeak_on, MS_Var.Furnace_on, MS_Var.GHP_on, MS_Var.HP_Lake_on, 
                    #MS_Var.HP_Sew_on, MS_Var.CC_on, "MS_Var.Boiler_on, MS_Var.BoilerPeak_on, MS_Var.Furnace_on, MS_Var.GHP_on,\
                    #MS_Var.HP_Lake_on, MS_Var.HP_Sew_on, MS_Var.CC_on, "
                    break

            elif round(Q_therm_req,0)!= 0:
                print "ERROR - TOO MUCH POWER! -     ", -Q_therm_req/1000.0,"kWh in excess"
                Q_uncovered = 0 #Q_therm_req
                Q_excess = -Q_therm_req
                Q_therm_req = 0
                #break
            else:
                #print "\n all demand covered in Slave, Q_therm_req = ", Q_therm_req, "Wh, hour:", hour, "\n"
                Q_therm_req = 0
        
        cost_data_centralPlant_op = costHPSew, costHPLake, costGHP, costCC, costFurnace, costBoiler, costBackup
        source_info = sHPSew, sHPLake,  srcGHP,  sorcCC, sorcFurnace, sBoiler,  sBackup
        Q_source_data = Q_HPSew, Q_HPLake, Q_GHP, Q_CC, Q_Furnace, Q_Boiler, Q_Backup, Q_uncovered
        E_PP_el_data = E_el_HPSew, E_el_HPLake, E_el_GHP, E_el_CC_produced, E_el_Furnace_produced, E_el_BoilerBase, E_el_Backup
        E_gas_data = E_gas_HPSew, E_gas_HPLake, E_gas_GHP, E_gas_CC,  E_gas_Furnace, E_gas_Boiler, E_gas_Backup
        E_wood_data = E_wood_HPSew, E_wood_HPLake, E_wood_GHP, E_wood_CC, E_wood_Furnace, E_wood_Boiler, E_wood_Backup
        E_coldsource_data =  E_coldsource_HPSew,  E_coldsource_HPLake,  E_coldsource_GHP,  E_coldsource_CC, \
                            E_coldsource_Furnace, E_coldsource_Boiler,  E_coldsource_Backup
        
        return  cost_data_centralPlant_op, source_info, Q_source_data, E_coldsource_data, E_PP_el_data, E_gas_data, E_wood_data, Q_excess
    
    
    
    cost_data_centralPlant_op = np.zeros((gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR,7))
    source_info = np.zeros((gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR,7))
#    source_info = np.chararray((gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR,7), itemsize = 3)
    Q_source_data = np.zeros((gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR,8))
    E_coldsource_data  = np.zeros((gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR,7))
    E_PP_el_data  = np.zeros((gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR,7))
    E_gas_data  = np.zeros((gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR,7))
    E_wood_data  = np.zeros((gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR,7))
    Q_excess = np.zeros(gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR)
    
    # Iterate over all hours in the year
    for hour in range(gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR):
        Q_therm_req = Q_missing[hour]
        PP_activation_data= source_activator(Q_therm_req, hour, context)
        #print PP_activation_data
        cost_data_centralPlant_op[hour,:], source_info[hour,:], Q_source_data[hour,:], E_coldsource_data[hour,:], \
                E_PP_el_data[hour,:], E_gas_data[hour,:], E_wood_data[hour,:], Q_excess[hour] = PP_activation_data
        #print "source_info[hour,:]", source_info[hour,:]
        #print "cost_data[hour,:], source_info[hour,:], Q_source_data[hour,:], E_coldsource_data[hour,:], \
        #        E_PP_el_data[hour,:], E_gas_data[hour,:], E_wood_data[hour,:]:"
        #print np.shape(cost_data[hour,:]), np.shape(source_info[hour,:]), np.shape(Q_source_data[hour,:]), np.shape(E_coldsource_data[hour,:]), \
        #        np.shape(E_PP_el_data[hour,:]), np.shape(E_gas_data[hour,:]), np.shape(E_wood_data[hour,:])
    
    # save data 
    
    elapsed = time.time() - t
    
    print np.round(elapsed, decimals=0), "seconds used for this optimization"
    #current_time = time.time()
    
    #sum up the uncovered demand, get average and peak load
    QUncovered = Q_source_data[:,7]
    QUncoveredDesign = np.amax(QUncovered)
    QUncoveredAnnual = np.sum(QUncovered)
    C_boil_thermAddBackup = np.zeros(gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR)
    Q_primaryAddBackup = np.zeros(gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR)
    E_aux_AddBoiler = np.zeros(gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR)
    costHPSew = cost_data_centralPlant_op[:,0]
    costHPLake = cost_data_centralPlant_op[:,1]
    costGHP = cost_data_centralPlant_op[:,2]
    costCC = cost_data_centralPlant_op[:,3]
    costFurnace = cost_data_centralPlant_op[:,4]
    costBoiler = cost_data_centralPlant_op[:,5]
    costBackup = cost_data_centralPlant_op[:,6]
    costHPSew_sum, costHPLake_sum, costGHP_sum, costCC_sum, costFurnace_sum, costBoiler_sum, costBackup_sum = \
            np.sum(costHPSew), np.sum(costHPLake), np.sum(costGHP), np.sum(costCC), np.sum(costFurnace), np.sum(costBoiler), np.sum(costBackup)
        
        
    if QUncoveredDesign != 0:
        for hour in range(gv.HOURS_IN_DAY * gv.DAYS_IN_YEAR):
            tdhret_req = tdhret[hour,0]
            BoilerBackup_Cost_Data = BoilerCond_op_cost(QUncovered[hour], QUncoveredDesign, tdhret_req, \
                                                context.BoilerBackupType, context.EL_TYPE, gv)
            C_boil_thermAddBackup[hour], C_boil_per_WhBackup, Q_primaryAddBackup[hour], E_aux_AddBoiler[hour] = BoilerBackup_Cost_Data
        Q_primaryAddBackupSum = np.sum(Q_primaryAddBackup)
        costAddBackup_total = np.sum(C_boil_thermAddBackup)

    else:
         Q_primaryAddBackupSum = 0.0
         costAddBackup_total = 0.0
    

    
    save_file = 1
   #Sum up all electricity needs
    E_PP_tot_used = E_PP_el_data[:,0] + E_PP_el_data[:,1] + E_PP_el_data[:,2] + \
                                                                                E_PP_el_data[:,5] + E_PP_el_data[:,6] + E_aux_AddBoiler
    E_aux_storage_operation = E_aux_ch[:,0] + E_aux_dech[:,0]
    E_aux_storage_operation_sum = np.sum(E_aux_storage_operation)
    E_PP_and_storage = E_PP_tot_used + E_aux_storage_operation
    E_HP_SolarAndHeatRecoverySum = np.sum(E_aux_HP_uncontrollable)
    # Sum up all electricity produced by CHP (CC and Furnace) 
        # cost already accounted for in System Models (selling electricity --> cheaper thermal energy) 
    E_CC_tot_produced = E_PP_el_data[:,3] + E_PP_el_data[:,4] 
    
    # price from PV and PVT electricity (both are in E_PV_Wh, see Storage_Design_and..., about Line 133)
    ESolarProduced = E_PV_Wh + E_PVT_Wh
    
    
    
    E_produed_total = E_produced_solarAndHPforSolar[:,0] + E_CC_tot_produced

    E_consumed_without_buildingdemand = E_consumed_without_buildingdemand_solarAndHPforSolar[:,0] + E_PP_and_storage
    
    
    
    
    if save_file == 1:
        results = pd.DataFrame({
                                "Q_Network_Demand_after_Storage":Q_missing_copy[:,0],
                                "Cost_HPSew":cost_data_centralPlant_op[:,0],
                                "Cost_HPLake":cost_data_centralPlant_op[:,1],
                                "Cost_GHP":cost_data_centralPlant_op[:,2],
                                "Cost_CC":cost_data_centralPlant_op[:,3], 
                                "Cost_Furnace":cost_data_centralPlant_op[:,4],
                                "Cost_BoilerBase":cost_data_centralPlant_op[:,5],
                                "Cost_BoilerPeak":cost_data_centralPlant_op[:,6],
                                "Cost_AddBoiler":C_boil_thermAddBackup,
                                "HPSew_Status":source_info[:,0],
                                "HPLake_Status":source_info[:,1],
                                "GHP_Status":source_info[:,2],
                                "CC_Status":source_info[:,3],
                                "Furnace_Status":source_info[:,4],
                                "BoilerBase_Status":source_info[:,5],
                                "BoilerPeak_Status":source_info[:,6],
                                "Q_HPSew":Q_source_data[:,0], 
                                "Q_HPLake":Q_source_data[:,1],
                                "Q_GHP":Q_source_data[:,2],\
                                "Q_CC":Q_source_data[:,3], 
                                "Q_Furnace":Q_source_data[:,4], 
                                "Q_BoilerBase":Q_source_data[:,5], 
                                "Q_BoilerPeak":Q_source_data[:,6], 
                                "Q_uncontrollable":Q_uncontrollable[:,0],
                                "Q_primaryAddBackupSum":Q_primaryAddBackupSum,
                                "E_PP_and_storage":E_PP_and_storage, 
                                "Q_uncovered":Q_source_data[:,7], 
                                "Q_AddBoiler":QUncovered,
                                "E_aux_HP_uncontrollable":E_aux_HP_uncontrollable[:,0],
                                "ESolarProducedPVandPVT":ESolarProduced[:,0],
				"E_GHP":E_PP_el_data[:,2],
				"Qcold_HPLake":E_coldsource_data[:,1],
				"E_produced_total":E_produed_total,
				"E_consumed_without_buildingdemand":E_consumed_without_buildingdemand,
				"Q_excess":Q_excess
                                })
                                
        Name = MS_Var.configKey + "PPActivationPattern.csv"
        results.to_csv(locator.pathSlaveRes + '//'+ Name, sep= ',')
        
        print "PP Activation Results saved in : ", locator.pathSlaveRes
        print " as : ", Name
        
        
        
    
    #print "Q_source_data", Q_source_data
    
         
    CO2_emitted, Eprim_used = calculate_emissions_and_CO2(Q_source_data, E_coldsource_data, E_PP_el_data, \
                                                          E_gas_data, E_wood_data, Q_primaryAddBackupSum, np.sum(E_aux_AddBoiler), \
                                                          np.sum(ESolarProduced), np.sum(Q_SCandPVT), HP_operation_Data_sum_array, Q_storage_content_Wh, \
                                                          context, locator.pathSlaveRes, E_HP_SolarAndHeatRecoverySum, E_aux_storage_operation_sum, gv)
                            
                            
                            
    # sum up results from PP Activation
    #E_HPSew_sum = np.sum(E_el_data) - Sums up the energy consumption of 
    E_el_sum_consumed = np.sum(E_PP_and_storage) + np.sum(E_aux_HP_uncontrollable) # (excl. AddBoiler)
    print "np.sum(E_PP_and_storage)", np.sum(E_PP_and_storage)
    print "np.sum(E_aux_HP_uncontrollable)", np.sum(E_aux_HP_uncontrollable)
    
    #E_el_sum_generated = np.sum(ESolarProduced) # CC and Furnace are already taken into account in the models
    #E_gas_sum = np.sum(E_gas_data)
    #E_el_sum = E_el_sum_generated - E_el_sum_consumed
    #E_wood_sum = np.sum(E_wood_data)
    # E_coldsource_sum = np.sum(E_coldsource_data)
    
    # Differenciate between Normal and green electricity for
    if MS_Var.EL_TYPE == 'green':
        ELEC_PRICE = gv.ELEC_PRICE_GREEN
        #el_to_oil = gv.EL_TO_OIL_EQ_GREEN
        #el_to_co2 = gv.EL_TO_CO2_GREEN
    
    else: 
        ELEC_PRICE = gv.ELEC_PRICE
        #el_to_oil = gv.EL_TO_OIL_EQ
        #el_to_co2 = gv.EL_TO_CO2
        
    #determine KEV remuneration, weighted average by capacity installed
    
    #P_PV_installed = gv.PV_Peak * MS_Var.SOLAR_PART_PV
    #P_PVT_installed_electric = gv.PVT_Peak * MS_Var.SOLAR_PART_PVT
    
    #P_PVavgPerInstalltaion = P_PV_installed / MS_Var.nPV_installations
    #P_PVTavgPerInstalltaion = P_PVT_installed_electric / MS_Var.nPVT_installations
    
    
    #PeakPowerAvgkW      = INDf.import_solar_PeakPower(MS_Var.fNameTotalCSV, MS_Var.nBuildingsConnected, gv)
    # Area available in NEtwork 
    Area_AvailablePV     = solarFeat.SolarArea * MS_Var.SOLAR_PART_PV
    Area_AvailablePVT    = solarFeat.SolarArea * MS_Var.SOLAR_PART_PVT
    print "MS_Var.SOLAR_PART_PVT = ",MS_Var.SOLAR_PART_PVT
    print "MS_Var.SOLAR_PART_PV = ",MS_Var.SOLAR_PART_PV
    #    import from master 
    eta_m2_to_kW = gv.eta_area_to_peak # Data from Jimeno
    PowerPeakAvailablePV     = Area_AvailablePV * eta_m2_to_kW
    PowerPeakAvailablePVT    = Area_AvailablePVT * eta_m2_to_kW
    #calculate with conversion factor m'2-kWPeak
    
    KEV_RpPerkWhPVT     = find_KEV_remuneration(PowerPeakAvailablePVT * 1000.0, gv)
    KEV_RpPerkWhPV      = find_KEV_remuneration(PowerPeakAvailablePV * 1000.0, gv)
    print "\n", KEV_RpPerkWhPVT, "KEV PVT"
    print KEV_RpPerkWhPV, "KEV PV"
    
    KEV_total         = KEV_RpPerkWhPVT/100 * np.sum(E_PVT_Wh) / 1000 + KEV_RpPerkWhPV /100* np.sum(E_PV_Wh) / 1000 
                                                                                    # Units: from Rp/kWh to CHF/Wh
    
    price_obtained_from_KEV_for_PVandPVT = KEV_total 
    print "E_PVT_Wh",np.sum(E_PVT_Wh)
    print "E_PV_Wh", np.sum(E_PV_Wh)
    print "price_obtained_from_KEV_for_PVandPVT", price_obtained_from_KEV_for_PVandPVT, "\n"
    
    print "E_el_sum_consumed (excl. AddBoiler)", E_el_sum_consumed
    print "ELEC_PRICE", ELEC_PRICE
    #cost_electricity_thermalneeds = E_el_sum_consumed * ELEC_PRICE
    #print "cost_electricity_thermalneeds", cost_electricity_thermalneeds
    #cost_electricity_total = cost_electricity_thermalneeds - price_obtained_from_KEV_for_PVandPVT
    #print np.shape(cost_electricity_thermalneeds)
    #print "price_obtained_from_KEV_for_PVandPVT", np.shape(price_obtained_from_KEV_for_PVandPVT)
    # E_PP_el_data[:,3] = electricity produced in Wh from a CC
    cost_CC_maintenance = np.sum(E_PP_el_data[:,3]) * gv.CC_Maintenance_per_kWhel / 1000.0
    
    #Fill up storage if end-of-season energy is lower than beginning of season
    Q_Storage_SeasonEndReheat = Q_storage_content_Wh[-1] - Q_storage_content_Wh[0]
    

    gas_price = gv.NG_PRICE
    
    if Q_Storage_SeasonEndReheat > 0:
        cost_Boiler_for_Storage_reHeat_at_seasonend = float(Q_Storage_SeasonEndReheat) / 0.8 * gas_price
        #print "cost_Boiler_for_Storage_reHeat_at_seasonend", np.shape(cost_Boiler_for_Storage_reHeat_at_seasonend) 
    else:
        cost_Boiler_for_Storage_reHeat_at_seasonend = 0
    
    #print "cost_CC_maintenance", cost_CC_maintenance
    #cost_sum = np.sum(cost_data) + cost_electricity_total + costAddBackup_total + cost_CC_maintenance + \
    #                       cost_Boiler_for_Storage_reHeat_at_seasonend
    # CHANGED AS THE COST_DATA INCLUDES COST_ELECTRICITY_TOTAL ALREADY! (= double accounting) 
    cost_HP_aux_uncontrollable = np.sum(E_aux_HP_uncontrollable) * ELEC_PRICE
    cost_HP_storage_operation = np.sum(E_aux_storage_operation) * ELEC_PRICE
    
    #cost_data_centralPlant_op contains information about : 
    #                     costHPSew, costHPLake, costGHP, costCC, costFurnace, costBoiler, costBackup 
    #                     in 8760h operation
    
    cost_sum = np.sum(cost_data_centralPlant_op) - price_obtained_from_KEV_for_PVandPVT + costAddBackup_total + cost_CC_maintenance + \
                            cost_Boiler_for_Storage_reHeat_at_seasonend + cost_HP_aux_uncontrollable  + cost_HP_storage_operation
                            
    save_cost = 1            
    if save_cost == 1:
        results = pd.DataFrame({
                            "total cost":[cost_sum], 
                            "PPoperation_exclAddBackup":[np.sum(cost_data_centralPlant_op)],
                            "KEV_Remuneration":[price_obtained_from_KEV_for_PVandPVT],
                            "costAddBackup_total":[costAddBackup_total],
                            "cost_CC_maintenance":[cost_CC_maintenance],
                            "costHPSew_sum":[costHPSew_sum], 
                            "costHPLake_sum":[costHPLake_sum], 
                            "costGHP_sum":[costGHP_sum],
                            "costCC_sum":[costCC_sum],
                            "costFurnace_sum":[costFurnace_sum],
                            "costBoiler_sum":[costBoiler_sum],
                            "costBackup_sum":[costBackup_sum],
                            "cost_Boiler_for_Storage_reHeat_at_seasonend":[cost_Boiler_for_Storage_reHeat_at_seasonend],
                            "cost_HP_aux_uncontrollable":[cost_HP_aux_uncontrollable],
                            "cost_HP_storage_operation":[cost_HP_storage_operation]
                            })
        Name = MS_Var.configKey + "_SlaveCostData.csv"
        results.to_csv(locator.pathSlaveRes+ '//'+ Name, sep= ',')
        print "Slave to Master Variables saved in : ", locator.pathSlaveRes
        print " as : ", Name
   
   
   
    # Store out Average cost
     
    saveAverageCost = 1
   
    avgCostHPSewRpkWh             = 100 * 1000.0 * costHPSew_sum / np.sum(Q_source_data[:,0])
    avgCostHPLakeRpkWh            = 100 * 1000.0 * costHPLake_sum / np.sum(Q_source_data[:,1])
    avgCostGHPRpkWh               = 100 * 1000.0 * costGHP_sum / np.sum(Q_source_data[:,2])
    avgCostCCRpkWh                = 100 * 1000.0 * costCC_sum / np.sum(Q_source_data[:,3])
    avgCostFurnaceRpkWh           = 100 * 1000.0 * costFurnace_sum / np.sum(Q_source_data[:,4])
    avgCostBoilerBaseRpkWh        = 100 * 1000.0 * costBoiler_sum / np.sum(Q_source_data[:,5])
    avgCostBoilerPeakRpkWh        = 100 * 1000.0 * costBackup_sum / np.sum(Q_source_data[:,6])
    avgCostUncontrollableSources  = 100 * 1000.0 * cost_HP_aux_uncontrollable / np.sum(Q_uncontrollable[:,0])
    avgCostAddBoiler              = 100 * 1000.0 * costAddBackup_total / np.sum(QUncovered)
    avgCostStorageOperation       = 100 * 1000.0 * cost_HP_storage_operation / Q_StorageToDHNpipe_sum 
    
    print "\n Q_uncontrollable produced",np.sum(Q_uncontrollable[:,0])
    print "cost_HP_aux_uncontrollable", cost_HP_aux_uncontrollable
    print "E_aux_HP_uncontrollable sum", np.sum(E_aux_HP_uncontrollable)
    
    if saveAverageCost == 1:
        results = pd.DataFrame({
                                "avgCostHPSewRpkWh":[avgCostHPSewRpkWh],
                                "avgCostHPLakeRpkWh":[avgCostHPLakeRpkWh],
                                "avgCostGHPRpkWh":[avgCostGHPRpkWh],
                                "avgCostCCRpkWh":[avgCostCCRpkWh],
                                "avgCostFurnaceRpkWh":[avgCostFurnaceRpkWh],
                                "avgCostBoilerBaseRpkWh":[avgCostBoilerBaseRpkWh],
                                "avgCostBoilerPeakRpkWh":[avgCostBoilerPeakRpkWh],
                                "avgCostUncontrollableSources":[avgCostUncontrollableSources],
                                "avgCostAddBoiler":[avgCostAddBoiler],
                                "avgCostStorageOperation":[avgCostStorageOperation]
                                })
                                
        Name = MS_Var.configKey + "AveragedCostData.csv"
        results.to_csv(locator.pathSlaveRes+'//'+ Name, sep= ',')
        
        print "Averaged Cost Results saved in : ", locator.pathSlaveRes
        print " as : ", Name
        
    #print E_oil_eq_MJ, CO2_kg_eq, cost_sum
    #print type(E_oil_eq_MJ), type(CO2_kg_eq), type(cost_sum)

    E_oil_eq_MJ   = Eprim_used
    CO2_kg_eq     = CO2_emitted
    
    print "\n Values found in Slave:" 
    print "cost_sum", cost_sum, np.shape(cost_sum)
    print "E_oil_eq_MJ", E_oil_eq_MJ, np.shape(E_oil_eq_MJ)
    print "CO2_kg_eq", CO2_kg_eq, np.shape(CO2_kg_eq)
    
    if save_file == 1:
        results = pd.DataFrame({"E_oil_eq_MJ":[E_oil_eq_MJ], "CO2_kg_eq":[CO2_kg_eq],"cost_sum":[cost_sum]})
        Name = MS_Var.configKey + "_SlaveToMasterCostEmissionsPrimE.csv"
        os.chdir(locator.pathSlaveRes)
        results.to_csv(Name, sep= ',')
        print "Slave to Master Variables saved in : ", locator.pathSlaveRes
        print " as : ", Name
    printcost = 0
    if printcost == 1:
        print "Total_Cost_HPSew", np.sum(cost_data_centralPlant_op[:,0])
        print "Total_Cost_HPLake", np.sum(cost_data_centralPlant_op[:,1])
        print "Total_Cost_GHP", np.sum(cost_data_centralPlant_op[:,2])
        print "Total_Cost_CC", np.sum(cost_data_centralPlant_op[:,3])
        print "Total_Cost_Furnace", np.sum(cost_data_centralPlant_op[:,4])
        print "Total_Cost_BoilerBase", np.sum(cost_data_centralPlant_op[:,5])
        print "Total_Cost_BoilerPeak", np.sum(cost_data_centralPlant_op[:,6])    
    
    
    
    # Calculate primary energy from ressources:
    EgasPrimary = Q_primaryAddBackupSum + np.sum(E_gas_data)
    EwoodPrimary = np.sum(E_wood_data) 
    EelectrImportSlave = E_el_sum_consumed + np.sum(E_aux_AddBoiler)
    EelExport = np.sum(E_produed_total)
    Egroundheat = np.sum(E_coldsource_data) 
    EsolarUsed = np.sum(ESolarProduced) + np.sum(Q_SCandPVT)
    EgasPrimaryPeakPower = np.amax(E_gas_data) + np.amax(Q_primaryAddBackup)
    
    
    costBenefitNotUsedHPs = 0

    if MS_Var.HPLake_maxSize > 0 and gv.HPLake_allowed == 0:
        """
        Values & calculation after furnace.py
        """
        HP_Size = MS_Var.HPLake_maxSize
        InvC = (-493.53 * np.log(HP_Size * 1E-3) + 5484) * (HP_Size * 1E-3)
        InvCa = InvC * gv.HP_i * (1+ gv.HP_i) ** gv.HP_n / \
                ((1+gv.HP_i) ** gv.HP_n - 1)
    else:
        InvCa = 0

    costBenefitNotUsedHPLake = InvCa
    
    if MS_Var.HPSew_maxSize > 0 and gv.HPSew_allowed == 0:
        """
        Values & calculation after furnace.py
        """
        HP_Size = MS_Var.HPSew_maxSize
        InvC = (-493.53 * np.log(HP_Size * 1E-3) + 5484) * (HP_Size * 1E-3)
        InvCa = InvC * gv.HP_i * (1+ gv.HP_i) ** gv.HP_n / \
                ((1+gv.HP_i) ** gv.HP_n - 1)
    else:
        InvCa = 0
        
        
    costBenefitNotUsedHPSew = InvCa
    
    costBenefitNotUsedHPs = costBenefitNotUsedHPSew + costBenefitNotUsedHPLake

    results = pd.DataFrame({
                            "EgasPrimary":[EgasPrimary],
                            "EgasPrimaryPeakPower":[EgasPrimaryPeakPower],
                            "EwoodPrimary":[EwoodPrimary],
                            "EelectrImportSlave":[EelectrImportSlave],
                            "EelExport":[EelExport],
                            "Egroundheat":[Egroundheat],
                            "EsolarUsed":[EsolarUsed],
                            "costBenefitNotUsedHPs":[costBenefitNotUsedHPs]
                            })
                            
    Name = locator.pathSlaveRes + "/" + MS_Var.configKey + "PrimaryEnergyBySource.csv"
    results.to_csv(Name, sep= ',')
    
    print "Averaged Cost Results saved in : ", locator.pathSlaveRes
    print " as : ", Name
    
    cost_sum -= costBenefitNotUsedHPs                             
                                      
    return E_oil_eq_MJ, CO2_kg_eq, cost_sum, QUncoveredDesign, QUncoveredAnnual