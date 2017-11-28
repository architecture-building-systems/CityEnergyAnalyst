"""
Install the grasshopper interface. This assumes that the python path for grasshopper Python scripts is in
``%APPDATA%\McNeel\Rhinoceros\5.0\scripts``.
"""

from __future__ import division
from __future__ import print_function

import os
import sys
import shutil

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def main(_):
    """
    Install a subset of the CEA for use inside grasshopper Python scripts.

    Since we don't know for sure, if ``cea install-toolbox`` (for the ArcGIS interface) was run, we need to re-create
    some stuff done there too, like storing the path to the python executable to use.

    :param _: ignored.
    :type _: cea.config.Configuration
    :return:
    """
    with open(os.path.expanduser('~/cea_python.pth'), 'w') as f:
        f.write(sys.executable)

    scripts_folder = os.path.expandvars(r'%APPDATA%\McNeel\Rhinoceros\5.0\scripts')
    copy_config(scripts_folder)
    copy_inputlocator(scripts_folder)
    copy_library(scripts_folder)

    copy_cea_ghuser(r'%APPDATA%\Grasshopper\UserObjects')

    print('Installed grasshopper interface.')


def copy_config(scripts_folder):
    """Copy the cea/config.py, cea/default.config and an empty __init__.py file to the toolbox_folder"""
    import cea.config

    cea_dst_folder = get_cea_dst_folder(scripts_folder)
    cea_src_folder = os.path.dirname(cea.config.__file__)
    shutil.copy(os.path.join(cea_src_folder, 'config.py'), cea_dst_folder)
    shutil.copy(os.path.join(cea_src_folder, 'default.config'), cea_dst_folder)
    shutil.copy(os.path.join(cea_src_folder, '__init__.py'), cea_dst_folder)

def get_cea_dst_folder(toolbox_folder):
    cea_dst_folder = os.path.join(toolbox_folder, 'cea')
    if not os.path.exists(cea_dst_folder):
        os.makedirs(cea_dst_folder)
    return cea_dst_folder


def copy_inputlocator(scripts_folder):
    """Copy the cea/inputlocator.py file to the toolbox_folder and create the cea/databases.pth file"""
    import cea.inputlocator

    cea_dst_folder = get_cea_dst_folder(scripts_folder)
    cea_src_folder = os.path.dirname(cea.inputlocator.__file__)
    shutil.copy(os.path.join(cea_src_folder, 'inputlocator.py'), cea_dst_folder)

    locator = cea.inputlocator.InputLocator(None)
    with open(os.path.join(cea_dst_folder, 'databases.pth'), 'w') as f:
        f.write(locator.db_path)


def copy_cea_ghuser(user_objects_folder):
    src_folder = os.path.dirname(__file__)
    src_file = os.path.join(src_folder, 'CEA.ghuser')
    dst_folder = os.path.expandvars(user_objects_folder)
    shutil.copy(src_file, dst_folder)


def copy_library(scripts_folder):
    """Copy the library functions"""
    lib_dst_folder = os.path.join(scripts_folder, 'cea', 'interfaces', 'grasshopper')
    if not os.path.exists(lib_dst_folder):
        os.makedirs(lib_dst_folder)

    lib_src_folder = os.path.dirname(__file__)
    shutil.copy(os.path.join(lib_src_folder, 'ghhelper.py'), lib_dst_folder)

    # we also need access to the cli.config file (ghhelper uses this to figure out the parameters)
    lib_cli_dst_folder = os.path.join(scripts_folder, 'cea', 'interfaces', 'cli')
    if not os.path.exists(lib_cli_dst_folder):
        os.makedirs(lib_cli_dst_folder)
    shutil.copy(os.path.join(lib_src_folder, '..', 'cli', 'cli.config'), lib_cli_dst_folder)

    # add `__init__.py` files to interfaces and arcgis folders
    with open(os.path.join(lib_dst_folder, '..', '..', '__init__.py'), 'w') as f:
        f.write('')
    with open(os.path.join(lib_dst_folder, '..', '__init__.py'), 'w') as f:
        f.write('')
    with open(os.path.join(lib_dst_folder, '__init__.py'), 'w') as f:
        f.write('')
    with open(os.path.join(lib_cli_dst_folder, '__init__.py'), 'w') as f:
        f.write('')


if __name__ == '__main__':
    main(None)
