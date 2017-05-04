Guide
=======
**Author : Sreepathi Bhargava Krishna**

**Intent : To provide information about what and where files are saved while running CEA**

**Date : 04-May-2017**

## Optimization
This section deals with the different files saved in `reference-case\baseline\outputs\data\optimization`
The folders present inside this are:
1. disconnected
2. master
3. network
4. slave
5. substations

#### 1. Disconnected

**Purpose:** ?????

**File Names:** ?????

**Rewritten:** ????

**Origin:** ????

**Information:** ????

#### 2. Master

**Purpose:** This folder saves the files corresponding to various generations in an optimization run.

**File Names:** `CheckPoint_Initial`, `CheckPoint_generationnumber`, `CheckPoint_Final`

**Rewritten:** The files present in this folder are rewritten. If the optimization is run multiple
times, the files are constantly replaced with new ones. **Thus if using multiple runs, be aware**

**Origin:** All the files in this folder are created in the following script 
`CEAforArcGIS\cea\optimization\master\master_main.py`

**Information:** The file has `population_fitness`, `epsIndicator`, `generation`, `testedPop`, `population`

#### 3. Network

**Purpose:** ?????

**File Names:** ?????

**Rewritten:** ????

**Origin:** ????

**Information:** ????

#### 4. Slave

**Purpose:** ????

**File Names:**
 
`configuration_AveragedCostData`
  
`configuration_InvestmentCostDetailed`

`configuration_PrimaryEnergyBySource`

`configuration_SlaveCostData`

`configuration_SlaveToMasterCostEmissionsPrimE`
 
`configuration_PPActivationPattern`

`configuration_SlaveDetailedEmissionData`

`configuration_SlaveDetailedEprimData`

`configuration_Storage_Sizing_Parameters`

`configuration_StorageOperationData`

**Rewritten:** Highly unlikely to be rewritten as `configuration` is associated
with each saved file. Over time this folder will get cluttered with files if the simulations
are run multiple times

**Origin:**

`configuration_AveragedCostData` --> `CEAforArcGIS\cea\optimization\slave\least_cost.py`

`configuraiton_InvestmentCostDetailed` --> `CEAforArcGIS\cea\optimization\master\cost_model.py`

`configuration_PrimaryEnergyBySource` --> `CEAforArcGIS\cea\optimization\slave\least_cost.py`

`configuration_SlaveCostData` --> `CEAforArcGIS\cea\optimization\slave\least_cost.py`

`configuration_SlaveToMasterCostEmissionsPrimE` --> `CEAforArcGIS\cea\optimization\slave\least_cost.py`

`configuration_PPActivationPattern` --> `CEAforArcGIS\cea\optimization\slave\least_cost.py`

`configuration_SlaveDetailedEmissionData` --> `CEAforArcGIS\cea\optimization\slave\least_cost.py`

`configuration_SlaveDetailedEprimData` --> `CEAforArcGIS\cea\optimization\slave\least_cost.py`

`configuration_Storage_Sizing_Parameters` --> `CEAforArcGIS\cea\optimization\slave\seasonal_storage\storage_main.py`

`configuration_StorageOperationData` --> `CEAforArcGIS\cea\optimization\slave\seasonal_storage\design_operation.py`

**Information:**

`configuration_AveragedCostData` includes the following parameters:
 `avgCostAddBoiler`,	`avgCostBoilerBaseRpkWh`,
`avgCostBoilerPeakRpkWh`,	`avgCostCCRpkWh`,	`avgCostFurnaceRpkWh`,
`avgCostGHPRpkWh`,	`avgCostHPLakeRpkWh`,	`avgCostHPSewRpkWh`,
`avgCostStorageOperation`,	`avgCostUncontrollableSources`

  
`configuration_InvestmentCostDetailed` includes the following parameters:
`BoilerAddInvC`,	`BoilerBInvCost`,	`BoilerPInvCost`,
`CO2DiscBuild`,	`CostDiscBuild`,	`DHNInvestCost`,
`FurnaceInvCost`,	`GasConnectionInvCa`,	`HPLakeInvC`,
`HPSewInvC`,	`NetworkCost`,	`PVTHEXCost`,	`PVTInvC`,
`PrimDiscBuild`,	`SCHEXCost`,	`SCInvC`,	`StorageCostSum`,
`StorageHEXCost`,	`StorageHPCost`,	`StorageInvC`,	`SubstHEXCost`,
`SumInvestCost`,	`pumpCosts`


`configuration_PrimaryEnergyBySource` includes the following parameters:
`EelExport`,	`EelectrImportSlave`,	`EgasPrimary`,
`EgasPrimaryPeakPower`,	`Egroundheat`,	`EsolarUsed`,
`EwoodPrimary`,	`costBenefitNotUsedHPs`


`configuration_SlaveCostData` includes the following parameters:
`KEV_Remuneration`,	`PPoperation_exclAddBackup`,	`costAddBackup_total`,
`costBackup_sum`,	`costBoiler_sum`,	`costCC_sum`,	`costFurnace_sum`,
`costGHP_sum`,	`costHPLake_sum`,	`costHPSew_sum`,
`cost_Boiler_for_Storage_reHeat_at_seasonend`,
`cost_CC_maintenance`,	`cost_HP_aux_uncontrollable`,
`cost_HP_storage_operation`,	`total cost`


`configuration_SlaveToMasterCostEmissionsPrimE` includes the following parameters:
`CO2_kg_eq`,	`E_oil_eq_MJ`,	`cost_sum`

 
`configuration_PPActivationPattern` file has **8760** lines. It includes the following parameters:
`BoilerBase_Status`,	`BoilerPeak_Status`,	`CC_Status`,
`Cost_AddBoiler`,	`Cost_BoilerBase`,	`Cost_BoilerPeak`,
`Cost_CC`,	`Cost_Furnace`,	`Cost_GHP`,	`Cost_HPLake`,
`Cost_HPSew`,	`ESolarProducedPVandPVT`,	`E_GHP`,
`E_PP_and_storage`,	`E_aux_HP_uncontrollable`,
`E_consumed_without_buildingdemand`,	`E_produced_total`,	`Furnace_Status`,
`GHP_Status`,	`HPLake_Status`,	`HPSew_Status`,	`Q_AddBoiler`,
`Q_BoilerBase`,	`Q_BoilerPeak`,	`Q_CC`,	`Q_Furnace`,	`Q_GHP`,
`Q_HPLake`,	`Q_HPSew`,	`Q_Network_Demand_after_Storage`,	`Q_excess`,
`Q_primaryAddBackupSum`,	`Q_uncontrollable`,	`Q_uncovered`,	`Qcold_HPLake`


`configuration_SlaveDetailedEmissionData` includes the following parameters:
`CO2_from_AddBoiler_gas`,	`CO2_from_BaseBoiler_gas`,
`CO2_from_CC_gas`,	`CO2_from_GHP`,	`CO2_from_HPLake`,
`CO2_from_HPSolarandHearRecovery`,	`CO2_from_HP_StorageOperationChDeCh`,
`CO2_from_PeakBoiler_gas`,	`CO2_from_SCandPVT`,	`CO2_from_Sewage`,
`CO2_from_elec_sold`,	`CO2_from_elec_usedAuxBoilersAll`,
`CO2_from_fictiveBoilerStorage`,	`CO2_from_wood`


`configuration_SlaveDetailedEprimData` includes the following parameters:
`E_prim_from_AddBoiler_gas`,	`E_prim_from_BaseBoiler_gas`,
`E_prim_from_CC_gas`,	`E_prim_from_FictiveBoiler_gas`,
`E_prim_from_PeakBoiler_gas`,	`EprimSaved_from_elec_sold_CC`,
`EprimSaved_from_elec_sold_Furnace`,	`EprimSaved_from_elec_sold_Solar`,
`Eprim_from_GHP`,	`Eprim_from_HPLake`,	`Eprim_from_HPSolarandHearRecovery`,
`Eprim_from_HP_StorageOperationChDeCh`,	`Eprim_from_Sewage`,
`Eprim_from_elec_usedAuxBoilersAll`,	`Eprim_from_wood`


`configuration_Storage_Sizing_Parameters` includes the following parameters:
`Q_initial`,	`Storage_Size_opt`,	`T_initial`


`configuration_StorageOperationData` file has **8760** lines. It includes the following parameters:
`E_PVT_Wh`,	`E_PV_Wh`,	`E_aux_HP_uncontrollable`,	`E_aux_ch`,
`E_aux_dech`,	`E_consumed_total_without_buildingdemand`,	`E_produced_total`,
`HPCompAirDesignArray`,	`HPScDesignArray`,	`HPServerHeatDesignArray`,
`HPpvt_designArray`,	`P_HPCharge_max`,	`Q_DH_networkload`,
`Q_SCandPVT_coldstream`,	`Q_from_storage_used`,	`Q_missing`,
`Q_rejected_fin`,	`Q_storage_content_Wh`,	`Q_to_storage`,	`Q_uncontrollable_hot`
`Storage_Size`,	`mdot_DH_fin`


#### 5. Substations

**Purpose:** ?????

**File Names:** ?????

**Rewritten:** ????

**Origin:** ????

**Information:** ????
