#-----------------
# Florian Mueller
# December 2014
#-----------------



import LayoutData
import HydraulicData
import ReducedHydraulicData
import ThermalData
import Solution
import subprocess
import os

CodePath = "C:/urben/MOO/"
finalDir = CodePath + "ntwOpt/"
matlabDir = "C:/Program Files/MATLAB/R2014a/bin"
matDir    = finalDir+'/Matlab/Mat/'

ld = LayoutData.LayoutData()
ld.setNewYork()
ld.writeToMat(matDir+'ld')

hd = HydraulicData.HydraulicData()
hd.setNewYork(ld)
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

hs = Solution.Solution()
hs.setFromMat(matDir+'hs')

rhd = ReducedHydraulicData.ReducedHydraulicData()
rhd.setNewYork(ld,hd,hs)
rhd.writeToMat(matDir+'rhd')

if 1:
    print '\nsolve reduced hydraulic linear program ...\n'
    mCode = " ".join(["cd('%(finalDir)sMatlab');",
                      "ld  = LayoutData();",
                      "ld  = setFromMat(ld, '%(matDir)sld');",
                      "hd  = HydraulicData();",
                      "hd  = setFromMat(hd, '%(matDir)shd');",
                      "rhd = ReducedHydraulicData();",
                      "rhd = setFromMat(rhd, '%(matDir)srhd');",
                      "rhs = ReducedHydraulicSolution();",
                      "rhs = solveReducedHydraulicLinProg(ld,hd,rhd,rhs);",
                      "rhs = writeToMat(rhs, '%(matDir)srhs');",
                      "exit();"]) % locals()
                      
    subprocess.call([os.path.join(matlabDir, 'matlab.exe'), '-wait', '-nosplash', '-nodesktop', '-r', mCode], shell=True)

rhs = Solution.Solution()
rhs.setFromMat(matDir+'rhs')

td = ThermalData.ThermalData()
td.setNewYork(ld,hd,rhd,rhs)
td.writeToMat(matDir+'td')

if 1:
    print '\nsolve thermal linear program ...\n'
    mCode = " ".join(["cd('%(finalDir)sMatlab');",
                      "ld  = LayoutData();",
                      "ld  = setFromMat(ld, '%(matDir)sld');",
                      "hd  = HydraulicData();",
                      "hd  = setFromMat(hd, '%(matDir)shd');",
                      "td = ThermalData();",
                      "td = setFromMat(td, '%(matDir)std\');",
                      "ts = ThermalSolution();",
                      "ts = solveThermalLinProg(ld,hd,td,ts);",
                      "ts = writeToMat(ts, '%(matDir)sts\');",
                      "exit();"]) % locals()
                      
    subprocess.call([os.path.join(matlabDir, 'matlab.exe'), '-wait', '-nosplash', '-nodesktop', '-r', mCode], shell=True)

ts = Solution.Solution()
ts.setFromMat(matDir+'ts')


