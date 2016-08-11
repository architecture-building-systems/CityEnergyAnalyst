"""
=====================================
Main routine for Network optimization
=====================================

"""
from __future__ import division
import os
import subprocess
import numpy as np

import cea.optimization.ntwOpt.Python.LayoutData
import cea.optimization.ntwOpt.Python.HydraulicData
import cea.optimization.ntwOpt.Python.Solution
import cea.optimization.ntwOpt.Python.NtwRead

reload(cea.optimization.ntwOpt.Python.HydraulicData)
reload(cea.optimization.ntwOpt.Python.NtwRead)


class ntwFeatures(object):
    def __init__(self):
        self.pipesCosts_DHN = 58310     # CHF
        self.pipesCosts_DCN = 64017     # CHF
        self.DeltaP_DHN = 77743         # Pa
        self.DeltaP_DCN = 77743         # Pa


def ntwOpt(matlabDir, finalDir, Header, Ntw):
    """
    Computes the parameters from the network optimization
    
    """
    matDir    = finalDir+'Python/Mat/'
    
    
    #################################################### Set the Layout
    ld = cea.optimization.ntwOpt.Python.LayoutData.LayoutData()
    ld.setNewYork()
    cea.optimization.ntwOpt.Python.NtwRead.modifyLayout(ld, Header, Ntw)
    ld.writeToMat(matDir+'ld')
    
    
    #################################################### Design phase
    
    # Design the pipes to the buildings
    hd = cea.optimization.ntwOpt.Python.HydraulicData.HydraulicData()
    hd.setNewYork(ld)
    cea.optimization.ntwOpt.Python.NtwRead.modifyHydraulicBuild(hd, ld, Header, Ntw)
    hd.writeToMat(matDir+'hd')
    
    if 1:
        print '\nsolve hydraulic mixed integer linear program ...\n'
        mCode = " ".join(["cd('%(finalDir)sMatlab');",
                        "ld = LayoutData();",
                        "ld = setFromMat(ld, '%(matDir)sld');",
                        "hd = HydraulicData();",
                        "hd = setFromMat(hd, '%(matDir)shd');",
                        "hs = HydraulicSolution();",
                        "hs = solveHydraulicMixedIntLinProg(ld, hd, hs);",
                        "hs = writeToMat(hs, '%(matDir)shs');",
                        "exit();"]) % locals()
    
        subprocess.call([os.path.join(matlabDir, 'matlab.exe'), '-wait', '-nosplash', '-nodesktop', '-r', mCode], shell=True)
    
    hsBuild = cea.optimization.ntwOpt.Python.Solution.Solution()
    hsBuild.setFromMat(matDir+'hs')
    
    
    # Design the pipes in the network
    hd = cea.optimization.ntwOpt.Python.HydraulicData.HydraulicData()
    hd.setNewYork(ld)
    cea.optimization.ntwOpt.Python.NtwRead.modifyHydraulicNtw(hd, ld, Header, Ntw)
    hd.writeToMat(matDir+'hd')
    
    if 1:
        print '\nsolve hydraulic mixed integer linear program ...\n'
        mCode = " ".join(["cd('%(finalDir)sMatlab');",
                        "ld = LayoutData();",
                        "ld = setFromMat(ld, '%(matDir)sld');",
                        "hd = HydraulicData();",
                        "hd = setFromMat(hd, '%(matDir)shd');",
                        "hs = HydraulicSolution();",
                        "hs = solveHydraulicMixedIntLinProg(ld, hd, hs);",
                        "hs = writeToMat(hs, '%(matDir)shs');",
                        "exit();"]) % locals()
    
        subprocess.call([os.path.join(matlabDir, 'matlab.exe'), '-wait', '-nosplash', '-nodesktop', '-r', mCode], shell=True)
    
    hsNtw = cea.optimization.ntwOpt.Python.Solution.Solution()
    hsNtw.setFromMat(matDir+'hs')
    DeltaP = np.amax(hsNtw.c["p_n"])
    
    # Calculate annualized pipe investment costs
    pipesCosts = cea.optimization.ntwOpt.Python.NtwRead.InvCostsPipes(ld, hd, hsBuild, hsNtw, Header, Ntw)
    print pipesCosts, "[CHF/y] Pipes Investment Costs"
    
    return pipesCosts, DeltaP


def ntwMain(matlabDir, finalDir, Header):
    ntwFeat = ntwFeatures()
    pipesCosts_DHN, DeltaP_DHN = ntwOpt(matlabDir, finalDir, Header, "DH")
    #pipesCosts_DCN, DeltaP_DCN = ntwOpt(matlabDir, finalDir, Header, "DC")
    
    ntwFeat.pipesCosts_DHN = pipesCosts_DHN
    #ntwFeat.pipesCosts_DCN = pipesCosts_DCN
    ntwFeat.DeltaP_DHN = DeltaP_DHN
    #ntwFeat.DeltaP_DCN = DeltaP_DCN
    
    return ntwFeat


def ntwMain2():
    # WARNING : linearization on the complete network of SQ Data
    ntwFeat = ntwFeatures()
    ntwFeat.pipesCosts_DHN = 58682
    ntwFeat.pipesCosts_DCN = 64017
    ntwFeat.DeltaP_DHN = 77158
    ntwFeat.DeltaP_DCN = 86938
    
    return ntwFeat
