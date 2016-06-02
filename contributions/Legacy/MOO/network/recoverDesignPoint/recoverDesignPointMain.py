#read design point and store as csv
NetworkFileName = 'test'
import pandas as pd
import numpy as np
import os

Header = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/UESM Data/"
pathNetworkManualResults = Header + "NetworkManualResults"

def recoverDesignPoint(pathSubsRes, pathRaw, TotalFileName, pathNetworkManualResults):
    """
    
    """
    
    #TotalFileName = "Total.csv"
    
    #read total file
    os.chdir(pathRaw)
    building_list_dataframe = pd.read_csv(TotalFileName, sep=",", usecols=["Name"])
    os.chdir(pathSubsRes)
    
    building_list_array_helper = np.array(building_list_dataframe) 
    building_list_array     = building_list_array_helper[:]  + "_result.csv"
    building_list           = np.array(building_list_array[:,0]).tolist() #transfer building array to list
    mdotDH_design_array     = np.zeros(len(building_list))
    Tsupply_design_array    = np.zeros(len(building_list))
    deltaT_design_array     = np.zeros(len(building_list))
    
    #Recover Design Points  - initialize result-arrays
    Tsupply_array_fin     = np.zeros( (len(building_list), 8760) )
    Treturn_array_fin     = np.zeros( (len(building_list), 8760) )
    deltaT_array_fin      = np.zeros( (len(building_list), 8760) )
    mdotDH_substation_array_fin = np.zeros( (len(building_list), 8760) )
    #print "shape chosen :", np.shape(mdotDH_substation_array_fin)
    
    
    for buildingID in range(len(building_list)):
        #read buldingMassflow, store maximum 
        fName = building_list[buildingID]
        mdotDH_substation_array = np.array(pd.read_csv(fName , sep=",", usecols=["mdot_DH_result"]))
        
        #print "mdotDH_substation_array", mdotDH_substation_array[:,0]
        #print np.shape(mdotDH_substation_array_fin[buildingID, :])
        mdotDH_substation_array_fin[buildingID, :] = mdotDH_substation_array[:,0]
        #print "mdotDH_substation_test = ", mdotDH_substation_array_fin[buildingID, 10]
        
        Tsupply_array = np.array(pd.read_csv(fName , sep=",", usecols=["T_supply_DH_result"]))
        Tsupply_array_fin[buildingID,:] = Tsupply_array[:,0]
        
        Treturn_array = np.array(pd.read_csv(fName , sep=",", usecols=["T_return_DH_result"]))
        Treturn_array_fin[buildingID,:] = Treturn_array[:,0]
        
        deltaT_array = Tsupply_array_fin[buildingID,:] - Treturn_array_fin[buildingID,:]
        deltaT_array_fin[buildingID, :] = deltaT_array
        
        mdotDH_design_array[buildingID] = np.max(mdotDH_substation_array_fin[buildingID, :])
        Tsupply_design_array[buildingID] =  np.max(Tsupply_array_fin[buildingID, :])
        deltaT_design_array[buildingID] =  np.max(deltaT_array_fin[buildingID, :])
        #print fName, mdotDH_design_array[buildingID]
        #print np.shape(deltaT_array_fin)
        #print "test deltaT = ", deltaT_array_fin[buildingID, 10] 
    
    
    # ADD COOLING!  
    DesignResults = pd.DataFrame({
                                "mdotDHdesign":mdotDH_design_array,
                                "buildingName":building_list,
                                "Tsupply_array_design":Tsupply_design_array,
                                "deltaT_array_design":deltaT_design_array,
                                })
    fName_result = "DesignPoints" + ".csv"
    os.chdir(pathNetworkManualResults)
    DesignResults.to_csv(fName_result, sep= ',')
    print "Design Points stored in :", pathNetworkManualResults
    
    #write all design points into single files with timestamp (=hour)

    for hour in range(8760):
        #print np.shape(Tsupply_array_fin), np.shape(Treturn_array_fin), np.shape(deltaT_array_fin), np.shape(mdotDH_substation_array_fin)
        OperationResults = pd.DataFrame({
                                        "Tsupply_array_fin":Tsupply_array_fin[:,hour],
                                        "Treturn_array_fin":Treturn_array_fin[:,hour],
                                        "deltaT_array_fin": deltaT_array_fin[:,hour],
                                        "mdotDH": mdotDH_substation_array_fin[:,hour],
                                        "BuildingID": building_list
                                        })
        fName_result = "OperationPoint_"+ str(hour) + ".csv"
        os.chdir(pathNetworkManualResults)
        OperationResults.to_csv(fName_result, sep= ',')
    print "Operation Points stored in :", pathNetworkManualResults, "as OperationPoint_HOUR.csv"
    
    
    
"""
 for hour in range(8760):
        for buildingID in range(len(building_list)):
            TsupplyInput[buildingID,hour] = Tsupply_array_fin[]
            TreturnInput[buildingID,hour] = Treturn_array_fin
            detaTInput[buildingID,hour]   = deltaT_array_fin
            mdotDHInput[buildingID,hour]  = mdotDH_substation_array_fin
"""
    