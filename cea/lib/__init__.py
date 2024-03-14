"""
This only works for wntr v0.2.3

Apple Silicon lib builds from:
WNTR (https://github.com/USEPA/WNTR/tree/0.2.3)
set `use_swig` and `build` to True in setup.py
make sure swig is installed
python setup.py build_ext --inplace
copy _evaluator and _network from build

EPANET (https://github.com/OpenWaterAnalytics/EPANET/tree/v2.0.12)
replace all `malloc.h` with `stdlib.h`
gcc -dynamiclib *.c -o libepanet.dylib
copy libepanet.dylib to Darwin folder
"""

import platform
import sys
import os


def apply_wntr_fix():
    """
    Load required libraries for wntr for Apple Silicon machines since wntr v0.2.3 only has libraries for Intel machines
    """
    if sys.platform == "darwin" and platform.processor() == "arm":
        # Add required shared objects to path before importing wntr
        sys.path.append(os.path.dirname(__file__))

        # Make sure correct version of wntr is installed
        import wntr
        if wntr.__version__ != '0.2.3':
            raise ImportError(f"Require wntr version 0.2.3, found {wntr.__version__}")

        print("Applying fix for Apple Silicon")
        # Change where wntr looks for libepanet
        import wntr.epanet.toolkit
        wntr.epanet.toolkit.epanet_toolkit = "cea.lib"
