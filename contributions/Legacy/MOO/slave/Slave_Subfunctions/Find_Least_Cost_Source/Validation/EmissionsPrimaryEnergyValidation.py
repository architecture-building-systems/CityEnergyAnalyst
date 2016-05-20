import numpy as np
import globalVar as gV
import MasterToSlaveVariables as MS_Var

StorageContentEndOfYear = 0 # Wh
StorageContentStartOfYear = 100000

if StorageContentEndOfYear < StorageContentStartOfYear:
    QToCoverByStorageBoiler = float(StorageContentEndOfYear - StorageContentStartOfYear)
    eta_fictive_Boiler = 0.8 # add rather low efficiency as a penalty
    E_gasPrim_fictiveBoiler = QToCoverByStorageBoiler / eta_fictive_Boiler

else:
    E_gasPrim_fictiveBoiler = 0 

# copy data 

cost_data, source_info, Q_source_data, Q_coldsource_data, E_PP_el_data, Q_gas_data, Q_wood_data = PP_activation_data
Q_HPSew, Q_HPLake, Q_GHP, Q_CC, Q_Furnace, Q_Boiler, Q_BoilerPeak, Q_uncovered = Q_source_data
Q_coldsource_HPSew,  Q_coldsource_HPLake,  Q_coldsource_GHP,  Q_coldsource_CC, \
                        Q_coldsource_Furnace, Q_coldsource_Boiler,  Q_coldsource_Backup = Q_coldsource_data
                        
Q_gas_HPSew, Q_gas_HPLake, Q_gas_GHP, Q_gas_CC,  Q_gas_Furnace, Q_gas_Boiler, Q_gas_Backup = Q_gas_data
Q_wood_HPSew, Q_wood_HPLake, Q_wood_GHP, Q_wood_CC, Q_wood_Furnace, Q_wood_Boiler, Q_wood_Backup = Q_wood_data
E_el_HPSew, E_el_HPLake, E_el_GHP, E_el_CC_produced, E_el_Furnace_produced, E_el_BoilerBase, E_el_Backup = E_PP_el_data

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
    gas_to_oil_BoilerBackup_std = gV.BG_BOILER_TO_OIL_STD
    gas_to_co2_BoilerBackup_std = gV.BG_BOILER_TO_CO2_STD
else:
    gas_to_oil_BoilerBackup_std = gV.NG_BOILER_TO_OIL_STD
    gas_to_co2_BoilerBackup_std = gV.NG_BOILER_TO_CO2_STD

if MS_Var.gt_fuel == 'BG':
    gas_to_oil_CC_std = gV.BG_CC_TO_OIL_STD
    gas_to_co2_CC_std = gV.BG_CC_TO_CO2_STD
    EL_CC_TO_CO2_STD  = gV.EL_BGCC_TO_CO2_STD
    EL_CC_TO_OIL_STD  = gV.EL_BGCC_TO_OIL_EQ_STD
else:
    gas_to_oil_CC_std = gV.NG_CC_TO_OIL_STD
    gas_to_co2_CC_std = gV.NG_CC_TO_CO2_STD
    EL_CC_TO_CO2_STD  = gV.EL_NGCC_TO_CO2_STD
    EL_CC_TO_OIL_STD  = gV.EL_NGCC_TO_OIL_EQ_STD
    
if MS_Var.BoilerType == 'BG':
    gas_to_oil_BoilerBase_std = gV.BG_BOILER_TO_OIL_STD
    gas_to_co2_BoilerBase_std = gV.BG_BOILER_TO_CO2_STD
else:
    gas_to_oil_BoilerBase_std = gV.NG_BOILER_TO_OIL_STD
    gas_to_co2_BoilerBase_std = gV.NG_BOILER_TO_CO2_STD
    
if MS_Var.BoilerPeakType == 'BG':
    gas_to_oil_BoilerPeak_std = gV.BG_BOILER_TO_OIL_STD
    gas_to_co2_BoilerPeak_std = gV.BG_BOILER_TO_CO2_STD
else:
    gas_to_oil_BoilerPeak_std = gV.NG_BOILER_TO_OIL_STD
    gas_to_co2_BoilerPeak_std = gV.NG_BOILER_TO_CO2_STD

if MS_Var.EL_TYPE == 'green':
    EL_TO_CO2                 = gV.EL_TO_CO2_GREEN
    EL_TO_OIL_EQ              = gV.EL_TO_OIL_EQ_GREEN
else:
    EL_TO_CO2                 = gV.EL_TO_CO2
    EL_TO_OIL_EQ              = gV.EL_TO_OIL_EQ
    
    
#evaluate average efficiency, recover normalized data with this efficiency, if-else is there to avoid nan's
if np.sum(Q_Furnace)    != 0:
    eta_furnace_avg     = np.sum(Q_Furnace) / np.sum(Q_wood_Furnace)
else:
    eta_furnace_avg     = 1


if np.sum(Q_CC)         != 0:
    eta_CC_avg          = np.sum(Q_CC) / np.sum(Q_gas_CC)
else:
    eta_CC_avg          = 1
    
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

if np.sum(Q_GHP)       != 0:
    COP_GHP_avg         = np.sum(Q_GHP) / (-np.sum(Q_coldsource_GHP) + np.sum(Q_GHP))
else:
    COP_GHP_avg         = 100

if np.sum(Q_HPLake)    != 0:
    COP_HPLake_avg      = np.sum(Q_HPLake) / (-np.sum(Q_coldsource_HPLake) + np.sum(Q_HPLake))
    
else:
    COP_HPLake_avg      = 100
#print "COP_HPLake_avg, COP_GHP_avg, COP_HPSew_avg = ", COP_HPLake_avg, COP_GHP_avg, COP_HPSew_avg

CO2_from_HP         =  np.sum(Q_HPSew) / COP_HPSew_avg * gV.SEWAGEHP_TO_CO2_STD \
                        + np.sum(Q_GHP) / COP_GHP_avg * gV.GHP_TO_CO2_STD \
                        + np.sum(Q_HPLake) / COP_HPLake_avg * gV.LAKEHP_TO_CO2_STD
#print CO2_from_HP
                                                
CO2_from_gas        = 1 / eta_CC_avg * np.sum(Q_CC) * gas_to_co2_CC_std \
                        + 1 /eta_Boiler_avg * np.sum(Q_Boiler) * gas_to_co2_BoilerBase_std \
                        + 1 /eta_PeakBoiler_avg * np.sum(Q_BoilerPeak) * gas_to_co2_BoilerPeak_std \
                        + 1 /eta_AddBackup_avg * np.sum(Q_uncovered) * gas_to_co2_BoilerBackup_std\
                        + 1 / 0.8 * E_gasPrim_fictiveBoiler * gV.NG_BOILER_TO_CO2_STD # 1 / eta (eta = 0.8) * "Value" as "Value" is standardized
                        
# print CO2_from_gas, " = nan ?"
#print "eta_CC_avg", eta_CC_avg
#print "eta_Boiler_avg", eta_Boiler_avg
#print "eta_PeakBoiler_avg", eta_PeakBoiler_avg
#print "eta_AddBackup_avg", eta_AddBackup_avg
                                                
CO2_from_wood       = np.sum(Q_Furnace) * gV.FURNACE_TO_CO2_STD / eta_furnace_avg
#print CO2_from_wood


CO2_from_elec_sold  = np.sum(E_el_Furnace_produced) * (gV.EL_FURNACE_TO_CO2_STD - EL_TO_CO2) \
                        + np.sum(E_el_CC_produced) * (EL_CC_TO_CO2_STD - EL_TO_CO2)\
                        + ESolarProduced * (gV.EL_PV_TO_CO2 - EL_TO_CO2) # ESolarProduced contains PV and PVT values
#print CO2_from_elec_sold


CO2_from_SCandPVT   = Q_SCandPVT * gV.SOLARCOLLECTORS_TO_CO2 
#print CO2_from_SCandPVT

#CO2_from_AuxElectricity= (E_aux_AddBoilerSum + E_el_Backup + E_el_BoilerBase) * Electricity_to_CO2 # Not used as the conversion factors
#                                                                                           of the machinery takes into account final energy
                                                                            
Eprim_from_HP       =  np.sum(Q_HPSew) / COP_HPSew_avg  * gV.SEWAGEHP_TO_OIL_STD \
                        + np.sum(Q_GHP) / COP_GHP_avg * gV.GHP_TO_OIL_STD \
                        + np.sum(Q_HPLake) / COP_HPLake_avg * gV.LAKEHP_TO_OIL_STD
#print "Eprim_from_HP", Eprim_from_HP

                                                
Eprim_from_gas      = 1 / eta_CC_avg * np.sum(Q_CC) * gas_to_oil_CC_std \
                        + 1 /eta_Boiler_avg * np.sum(Q_Boiler) * gas_to_oil_BoilerBase_std \
                        + 1 /eta_PeakBoiler_avg * np.sum(Q_BoilerPeak) * gas_to_oil_BoilerPeak_std \
                        + 1 /eta_AddBackup_avg * np.sum(Q_uncovered) * gas_to_oil_BoilerBackup_std\
                        + E_gasPrim_fictiveBoiler * gV.NG_BOILER_TO_OIL_STD / 0.8 # Value / eta as Value is standardized
                            
#print "Eprim_from_gas", Eprim_from_gas

                                            
Eprim_from_wood     = 1 /eta_furnace_avg * np.sum(Q_Furnace) * gV.FURNACE_TO_OIL_STD
#print "Eprim_from_wood",Eprim_from_wood


Eprim_from_elec_sold= 1 / eta_furnace_avg *np.sum(E_el_Furnace_produced) * (gV.EL_FURNACE_TO_OIL_EQ_STD - EL_TO_OIL_EQ)\
                        + 1 / eta_CC_avg * np.sum(E_el_CC_produced) * (EL_CC_TO_OIL_STD - EL_TO_OIL_EQ) \
                        + ESolarProduced * (gV.EL_PV_TO_OIL_EQ - EL_TO_OIL_EQ) 
                        # E_PV_Wh contains PV and PVT values (Units Wh * MJ/MJ, later on translated from Wh to MJ) 
                        
#Eprim_from_AuxElectricity= (E_aux_AddBoilerSum + E_el_Backup + E_el_BoilerBase) * Electricity_to_CO2 # Not used as the conversion factors
#                                                                                           of the machinery takes into account final energy
                        
#print "Eprim_from_elec_sold",Eprim_from_elec_sold

Eprim_from_SCandPVT = Q_SCandPVT * gV.SOLARCOLLECTORS_TO_OIL 
#print "Eprim_from_SCandPVT", Eprim_from_SCandPVT             
                        
                        
# As all values are in units [per MJ], this is now converted:
#CONVERT : * Wh_to_J / 10E6
CO2_emitted     = (CO2_from_HP + CO2_from_gas + CO2_from_wood + CO2_from_elec_sold + CO2_from_SCandPVT) * gV.Wh_to_J / 10.0E6
Eprim_used      = (Eprim_from_HP + Eprim_from_gas + Eprim_from_wood + Eprim_from_elec_sold + Eprim_from_SCandPVT) * gV.Wh_to_J / 10.0E6
#print Eprim_used
#print CO2_emitted
    
