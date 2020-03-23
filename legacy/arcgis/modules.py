"""
Ensure the ArcGIS modules ``arcpy`` and ``arcgisscripting`` can be imported properly by adding the paths
(as written by the ``cea install-toolbox`` command to ``~/cea_arcgis.pth``) to ``sys.path``.
"""

import os

import sys

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# make sure the ArcGIS paths are removed from PYTHONPATH (they are added later)
sys.path = [path for path in sys.path if not 'arcgis' in path.lower()]

arcpy = None

try:
    import arcpy
    import arcgisscripting
except ImportError:
    pth_file = os.path.expanduser('~/cea_arcpy.pth')
    if not os.path.exists(pth_file):
        raise ImportError("Could not find `cea_arcpy.pth` in user home directory. Run `cea install-toolbox` first.")
    with open(os.path.expanduser(pth_file), 'r') as f:
        folders = map(str.strip, f.readlines())
    for folder in folders:
        if folder not in sys.path:
            sys.path.append(folder)

    import arcpy
    import arcgisscripting
