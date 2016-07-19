"""
NOTE: This approach will only work when we upgrade to a newer version of numpy, since we will need a modern version
of numba (>=18) for this to work...
"""

import numba
from numba.pycc import CC

import cea.dem.sensible_loads

cc = CC('calc_tm')

# Uncomment the following line to print out the compilation steps
cc.verbose = True

cc.export('calc_tm', numba.float32(numba.float64, numba.float64, numba.float64, numba.float64, numba.float64), cea.dem.sensible_loads.calc_tm)


if __name__ == "__main__":
    cc.compile()