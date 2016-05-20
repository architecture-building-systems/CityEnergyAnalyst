"""
=====================================
Main routine for Network optimization
=====================================

"""
from __future__ import division
import os
import subprocess

import LayoutData
import HydraulicData
reload(HydraulicData)
import ReducedHydraulicData
import ThermalData
import Solution
import NtwReadZernez as NtwRead
reload(NtwRead)


matlabDir = '/Applications/MATLAB_R2014a.app/bin/'
finalDir  = '/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/NetworkByFlorianForZernez/'
matDir    = finalDir+'Python/Mat/'

#################################################### Set the Layout
ld = LayoutData.LayoutData()
ld.setNewYork()
NtwRead.modifyLayout(ld)
ld.writeToMat(matDir+'ld')


#################################################### Design phase

# Design the pipes to the buildings
hd = HydraulicData.HydraulicData()
hd.setNewYork(ld)
NtwRead.modifyHydraulicBuild(hd, ld)
hd.writeToMat(matDir+'hd')

if 1:
    print '\nsolve hydraulic mixed integer linear program ...\n'
    command = 'cd '+matlabDir+'; \
              ./matlab -nodesktop -nosplash -r \
              \" \
              cd(\''+finalDir+'Matlab\'); \
              ld = LayoutData(); \
              ld = setFromMat(ld,\''+matDir+'ld\'); \
              hd = HydraulicData(); \
              hd = setFromMat(hd,\''+matDir+'hd\'); \
              hs = HydraulicSolution(); \
              hs = solveHydraulicMixedIntLinProg(ld,hd,hs); \
              hs = writeToMat(hs,\''+matDir+'hs\'); \
              exit(); \
              \"'
    subprocess.call(command,shell=True)


hsBuild = Solution.Solution()
hsBuild.setFromMat(matDir+'hs')


# Design the pipes in the network
hd = HydraulicData.HydraulicData()
hd.setNewYork(ld)
NtwRead.modifyHydraulicNtw(hd, ld)
hd.writeToMat(matDir+'hd')

if 1:
    print '\nsolve hydraulic mixed integer linear program ...\n'
    command = 'cd '+matlabDir+'; \
              ./matlab -nodesktop -nosplash -r \
              \" \
              cd(\''+finalDir+'Matlab\'); \
              ld = LayoutData(); \
              ld = setFromMat(ld,\''+matDir+'ld\'); \
              hd = HydraulicData(); \
              hd = setFromMat(hd,\''+matDir+'hd\'); \
              hs = HydraulicSolution(); \
              hs = solveHydraulicMixedIntLinProg(ld,hd,hs); \
              hs = writeToMat(hs,\''+matDir+'hs\'); \
              exit(); \
              \"'
    subprocess.call(command,shell=True)


hsNtw = Solution.Solution()
hsNtw.setFromMat(matDir+'hs')

# Calculate annualized pipe investment costs
PipesCosts = NtwRead.InvCostsPipes(ld, hd, hsBuild, hsNtw)
print PipesCosts, "[CHF/y] Pipes Investment Costs"


############################################### Reduced hydraulic problem

# Load hydraulic data of hour h
h = 100

hd = HydraulicData.HydraulicData()
hd.setNewYork(ld)
NtwRead.modifyHydraulicTime(hd, ld, h)
hd.writeToMat(matDir+'hd')


# Modify hsNtw to integrate hsBuild (pipe types modification)
rhd = ReducedHydraulicData.ReducedHydraulicData()
rhd.setNewYork(ld, hd, hsNtw)
NtwRead.modifyReducedHyd(rhd, ld, hsBuild)
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


######################################################## Thermal

td = ThermalData.ThermalData()
td.setNewYork(ld,hd,rhd,rhs)
td.writeToMat(matDir+'td')

if 1:
    print '\nsolve thermal linear program ...\n'
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

