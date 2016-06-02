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




matlabDir = '/Applications/MATLAB_R2014a.app/bin/'
finalDir  = '/Users/Tim/Desktop/ETH/Masterarbeit/Github_Files/urben/Masterarbeit/UESM/NetworkByFlorianForZernez/'
matDir    = finalDir+'PythonZernez/Mat/'

ld = LayoutData.LayoutData()
ld.setNewYork()
ld.writeToMat(matDir+'ld')

hd = HydraulicData.HydraulicData()
hd.setNewYork(ld)
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

hs = Solution.Solution()
hs.setFromMat(matDir+'hs')

rhd = ReducedHydraulicData.ReducedHydraulicData()
rhd.setNewYork(ld,hd,hs)
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


