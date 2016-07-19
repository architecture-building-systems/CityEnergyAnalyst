#-----------------
# Florian Mueller
# December 2014
#-----------------


import LayoutData_Zernez
import HydraulicData_Zernez
import ReducedHydraulicData_Zernez
import ThermalData_Zernez
import Solution
import subprocess
import pandas as pd
import numpy as np

reload(LayoutData_Zernez)
reload(HydraulicData_Zernez)
reload(ReducedHydraulicData_Zernez)
reload(ThermalData_Zernez)


matlabDir = '/Applications/MATLAB_R2014a.app/bin/'
finalDir  = '/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/NetworkByFlorianForZernez/'
matDir    = finalDir+'PythonZernez/Mat/'

Header = "/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/UESM Data/"
pathToOperationPointFiles = Header + "NetworkManualResults"

def main():
    print "Process is running"
    ld = LayoutData_Zernez.LayoutData()
    ld.setZernez()
    ld.writeToMat(matDir+'ld')
    
    hd = HydraulicData_Zernez.HydraulicData()
    
    hd.setZernez(ld) # set Zernez_Master
    
    #import design data from my place
    Tsupply_array_design, deltaT_array_design, vdot_DH_design = import_design_data(pathToOperationPointFiles)
    vdot_DH_design_sorted = assignImportToCodeIndex(vdot_DH_design)
    deltaT_design_sorted = assignImportToCodeIndex(deltaT_array_design)
    Tsupply_design_sorted = assignImportToCodeIndex(Tsupply_array_design)
    
    
    
    hd.c['vDotRq_n'] =  -vdot_DH_design_sorted
    hd.c['vDotPl']   = -sum(hd.c['vDotRq_n'][np.array(range(ld.c['N']))!=ld.c['nPl']*np.ones(ld.c['N']),0]);
    hd.c['L_e']      = np.array([[7.3],[18.7],[2.8],[11.8],[3.7],[11.6],[9.6],[2.0],
                                    [14.5],[15.2],[10.5],[9.4],[8.3],[7.7],[11.0],[28.4],[61.25],
                                    
                                    [12.1],[18.4],[19.5],[1.2],[8.0],[1.0],[10.2],[3.0],[10.0],[12.8],[8.6],[4.5],[27.0],[39.4],[7.8],
                                    [10.4],[9.2],[17.3],[7.9],[21.5],[29.0],[40.0],[7.4],[21.75],[13.2],[8.0],[12.4],[11.0],[33.7],[35.4],[46.0],
                                    
                                    [32.5],[31.65],[6.8],[24.4],[14.5],[22.3],[10.2],[37.6],[5.9],[25.7],[28.0],[15.7],
                                    [14.5],[32.0],[20.1],[12.5],[16.3],[13.0],[17.8],[17.6],[24.7],[12.8],[23.0],[12.2],[16.8],[27.3]
                                    ])
    
    hd.writeToMat(matDir+'hd')
    
    if 1:
        command = 'cd '+matlabDir+'; \
                ./matlab -nodesktop -nosplash -r \
                \" \
                cd(\''+finalDir+'Matlab\'); \
                ld = LayoutData(); \
                ld = setFromMat(ld,\''+matDir+'ld\'); \
                hd = HydraulicData(); \
                hd = setFromMat(hd,\''+matDir+'hd\'); \
                hs = Solution(); \
                hs = solveHydraulicMixedIntLinProg(ld,hd,hs); \
                hs = writeToMat(hs,\''+matDir+'hs\'); \
                exit(); \
                \"'
        subprocess.call(command,shell=True)
    
    hs = Solution.Solution()
    hs.setFromMat(matDir+'hs')
    
    # iterate this part
    # for hour in range(8760):
    hour = 1
    
    thermalData = read_thermalData(hour, pathToOperationPointFiles, 'import')
    Tsupply_array_unsorted = thermalData[0] 
    deltaT_array_unsorted = thermalData[1] 
    vdot_DH_unsorted = thermalData[2]
    
    vdot_DH_sorted = assignImportToCodeIndex(vdot_DH_unsorted)
    deltaT_array_sorted = assignImportToCodeIndex(deltaT_array_unsorted)
    Tsupply_array_sorted = assignImportToCodeIndex(Tsupply_array_unsorted)
    
    hd.c['vDotRq_n']    = - vdot_DH_sorted # include nodes which do not consume anything!
    hd.c['vDotPl']      = -sum(hd.c['vDotRq_n'][np.array(range(ld.c['N']))!=ld.c['nPl']*np.ones(ld.c['N']),0]);


    
    rhd = ReducedHydraulicData_Zernez.ReducedHydraulicData()
    rhd.setZernez(ld,hd,hs)
    rhd.writeToMat(matDir+'rhd')

    if 1:
        print '\nsolve reduced hydraulic linear program ...\n'
        command = 'cd '+matlabDir+'; \
                ./matlab -nodesktop -nosplash -r \
                \" \
                cd(\''+finalDir+'Matlab\'); \
                ld  = LayoutData(); \
                ld  = setFromMat(ld,\''+matDir+'ld\'); \
                hd  = HydraulicData(); \
                hd  = setFromMat(hd,\''+matDir+'hd\'); \
                rhd = ReducedHydraulicData(); \
                rhd = setFromMat(rhd,\''+matDir+'rhd\'); \
                rhs = ReducedHydraulicSolution(); \
                rhs = solveReducedHydraulicLinProg(ld,hd,rhd,rhs); \
                rhs = writeToMat(rhs,\''+matDir+'rhs\'); \
                exit(); \
                \"'
        subprocess.call(command,shell=True)
        
        
        
    rhs = Solution.Solution()
    rhs.setFromMat(matDir+'rhs')
    
    td = ThermalData_Zernez.ThermalData()
    td.setZernez(ld,hd,rhd,rhs)
    
    
        # change TRq_n (required temprature of node), use Tsupply_array_fin and deltaT_array_fin 

    td.c['TRq_n']   = (np.max(Tsupply_array_sorted) - 273.0 )*np.ones((ld.c['N'],1));# imput for temperature dem!  write here T_DH of time step t
    #change dT_n, temperature drop in node
    
    td.c['dT_n']    = deltaT_array_sorted - 273.0 #INCLUDE SHAPE OF NETWORK& NODES REQUIREMENT! # 20.*np.ones((ld.c['N'],1)); # input for temperature drop, recover this from substation main (return temperature) 
        
    
    td.writeToMat(matDir+'td')
    
    
    # change thermal data here!
    td.writeToMat(matDir+'td')
    
    if 1:
        command = 'cd '+matlabDir+'; \
                ./matlab -nodesktop -nosplash -r \
                \" \
                cd(\''+finalDir+'Matlab\'); \
                ld = LayoutData(); \
                ld = setFromMat(ld,\''+matDir+'ld\'); \
                hd = HydraulicData(); \
                hd = setFromMat(hd,\''+matDir+'hd\'); \
                td = ThermalData(); \
                td = setFromMat(td,\''+matDir+'td\'); \
                ts = ThermalSolution(); \
                ts = solveThermalLinProg(ld,hd,td,ts); \
                ts = writeToMat(ts,\''+matDir+'ts\'); \
                exit(); \
                \"'
        subprocess.call(command,shell=True)
    
    ts = Solution.Solution()
    ts.setFromMat(matDir+'ts')


    
def import_design_data(pathToOperationPointFiles):
    """
    reads thermal Data from operation point files for every hour
    
    Return
    ------
    Tsupply_array_fin : array
       supply temperature required of costumers     
        
    deltaT_array_fin : array
        temperature drop in costumers in m^3/s
        
    vdot_DH : array
        volume flow in costumers in m^3/s
    """
    dataFileName = pathToOperationPointFiles + "/DesignPoints.csv"
    
    Tsupply_array_fin = np.array(pd.read_csv(dataFileName, sep=",", usecols=["Tsupply_array_design"]))
    deltaT_array_fin = np.array(pd.read_csv(dataFileName, sep=",", usecols=["deltaT_array_design"]))
    mdot_DH_kgs = np.array(pd.read_csv(dataFileName, sep=",", usecols=["mdotDHdesign"]))
    vdot_DH = mdot_DH_kgs/1000.0 # translate kg/s into m^3/s
    
    return Tsupply_array_fin, deltaT_array_fin, vdot_DH 


def read_thermalData(hour, pathToOperationPointFiles, *argv):
    """
    reads thermal Data from operation point files for every hour
    
    Return
    ------
    Tsupply_array_fin : array
       supply temperature required of costumers     
        
    deltaT_array_fin : array
        temperature drop in costumers in m^3/s
        
    vdot_DH : array
        volume flow in costumers in m^3/s
    """
    if  argv == 'import':
        dataFileName = pathToOperationPointFiles + "/DesignPoints.csv"
    else:
        dataFileName = pathToOperationPointFiles + "/OperationPoint_"+ str(hour) + ".csv"
    print dataFileName
    Tsupply_array_fin = np.array(pd.read_csv(dataFileName, sep=",", usecols=["Tsupply_array_fin"]))
    deltaT_array_fin = np.array(pd.read_csv(dataFileName, sep=",", usecols=["deltaT_array_fin"]))
    mdot_DH_kgs = np.array(pd.read_csv(dataFileName, sep=",", usecols=["mdotDH"]))
    vdot_DH = mdot_DH_kgs/1000.0 # translate kg/s into m^3/s
    
    return Tsupply_array_fin, deltaT_array_fin, vdot_DH
    
def assignImportToCodeIndex(inputarray):
    """
    assigns inport-index to coding-index (for Zernez Base Scenario)
    
    """
    outputarray = np.zeros((75,1))
    outputarray[14] = inputarray[0]
    outputarray[16] = inputarray[1]
    outputarray[12] = inputarray[2]
    outputarray[11] = inputarray[3]
    outputarray[9]  = inputarray[4]
    outputarray[61] = inputarray[5]
    outputarray[63] = inputarray[6]
    outputarray[33] = inputarray[7]
    outputarray[34] = inputarray[8]
    outputarray[64] = inputarray[9]
    outputarray[65] = inputarray[10]
    outputarray[36] = inputarray[11]
    outputarray[37] = inputarray[12]
    outputarray[39] = inputarray[13]
    outputarray[66] = inputarray[14]
    outputarray[67] = inputarray[15]
    outputarray[68] = inputarray[16]
    outputarray[43] = inputarray[17]
    outputarray[45] = inputarray[18]
    outputarray[46] = inputarray[19]
    outputarray[47] = inputarray[20]
    outputarray[48] = inputarray[21]
    outputarray[72] = inputarray[22]
    outputarray[74] = inputarray[23]
    outputarray[73] = inputarray[24]
    outputarray[70] = inputarray[25]
    outputarray[69] = inputarray[26]
    outputarray[71] = inputarray[27]
    outputarray[17] = inputarray[28]
    outputarray[15] = inputarray[29]
    outputarray[13] = inputarray[30]
    outputarray[10] = inputarray[31]
    outputarray[38] = inputarray[32]
    outputarray[35] = inputarray[33]
    outputarray[40] = inputarray[34]
    outputarray[41] = inputarray[35]
    outputarray[44] = inputarray[36]
    outputarray[42] = inputarray[37]
    
    return outputarray
    

if __name__ == '__main__':
    main()


