#Define design Point


import summarize_network_main as SNM

Header = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/UESM Data/"
CodePath = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/UESM Code/"

#sys.path.append(CodePath)


# Path to folders

pathRaw = Header + "Raw2"                    # Raw data from J+
pathSubsRes = Header + "SubsRes"            # Substation results for disconnected buildings
pathClustRes = Header + "ClustRes"          # Clustering results for disconnected buildings
pathDiscRes = Header + "DiscRes"            # Operation pattern for disconnected buildings
pathTotalNtw = Header + "TotalNtw"          # Total files (inputs to substation + ntw in master)
pathNtwRes = Header + "NtwRes"              # Ntw summary results
pathMasterRes = Header + "MasterRes"        # Master checkpoints
pathSolarRaw = Header + "SolarRaw"          # Raw solar files
pathSlaveRes = Header + "SlaveRes"          # Slave results (storage + operation pattern)



TotalFileName = "Total.csv"

pathLocalResults = Header + "NetworkManualResults"

SNM.Network_Summary(pathRaw, pathRaw, pathSubsRes, pathLocalResults, TotalFileName)

