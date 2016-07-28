"""
============================
multi-objective optimization
============================

"""

########################### Import modules

from __future__ import division

import contributions.Legacy.MOO.optimization.master.master_Main as mM
from contributions.Legacy.MOO.optimization.preprocessing.preprocessing import preproccessing
import contributions.Legacy.MOO.ntwOpt.Python.NtwMain as ntwM

"""
============================
optimization
============================

"""


def moo_optimization(pathX, Header, matlabDir, finalDir, gV):

    # call pre-processing
    extraCosts, extraCO2, extraPrim, solarFeat = preproccessing(pathX, gV)

    # network optimization
    ntwFeat = ntwM.ntwMain2(matlabDir, finalDir, Header)     #ntwMain2 -linear, #ntwMain - optimization

    # main optimization routine
    mM.EA_Main(pathX, extraCosts, extraCO2, extraPrim, solarFeat, ntwFeat, gV)


"""
============================
test
============================

"""
def test_optimization_main():
    """
    Run the properties script with input from the reference case and compare the results. This ensures that changes
    made to this script (e.g. refactorings) do not stop the script from working and also that the results stay the same.
    """
    import contributions.Legacy.MOO.globalVar as glob
    Header = "C:\ArcGIS\ESMdata\DataFinal\MOO\HEB/"  # path to the input / output folders
    CodePath = "C:\urben\MOO/"  # path to this UESM_MainZug.py file
    matlabDir = "C:/Program Files/MATLAB/R2014a/bin"  # path to the Matlab core files
    finalDir = CodePath + "ntwOpt/"
    gV = glob.globalVariables()
    pathX = gV.pathX
    moo_optimization(pathX=pathX, Header=Header, matlabDir=matlabDir, finalDir=finalDir, gV=gV)
    print 'test_properties() succeeded'


if __name__ == '__main__':
    test_optimization_main()

