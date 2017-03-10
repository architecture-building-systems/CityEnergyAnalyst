"""Install the toolbox into ArcGIS Desktop 10.4"""
import sys
import shutil
import os.path


def main():
    """
    Perform the following steps:

    - add a link to the python.exe that ran setup.py to user's home directory in the file cea_python.pth
    - copy the file "CityEnergyAnalyst.py" to the "My Toolboxes" folder of ArcGIS Desktop and rename the
      extension to ".pyt"
    """
    # write out path to python.exe to the file cea_python.pth
    with open(os.path.expanduser('~/cea_python.pth'), 'w') as f:
        f.write(sys.executable)

    shutil.copy(find_toolbox_src(), find_toolbox_dst())


def find_toolbox_src():
    """
    Find the source path of the toolbox file (CityEnergyAnalyst.py) - hint: it is relative
    to the current file!
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'CityEnergyAnalyst.py'))


def find_toolbox_dst():
    """
    Find the destination path for the toolbox file (City Energy Analyst.pyt) - hint: the
    folder is "%APPDATA%\ESRI\Desktop10.4\ArcToolbox\My Toolboxes"
    """
    return os.path.join(os.path.expandvars(r"%APPDATA%\ESRI\Desktop10.4\ArcToolbox\My Toolboxes"),
                        'City Energy Analyst.pyt')


if __name__ == '__main__':
    main()
