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
    - sets up .pth files to access arcpy from the cea python interpreter.
    """
    # write out path to python.exe to the file cea_python.pth
    with open(os.path.expanduser('~/cea_python.pth'), 'w') as f:
        f.write(sys.executable)

    toolbox_dst = find_toolbox_destination()
    toolbox_folder = os.path.dirname(toolbox_dst)
    if not os.path.exists(toolbox_folder):
        os.makedirs(toolbox_folder)
    shutil.copy(find_toolbox_src(), toolbox_dst)

    with open(os.path.expanduser('~/cea_arcpy.pth'), 'w') as f:
        f.writelines('\n'.join(get_arcgis_paths()))


def find_toolbox_src():
    """
    Find the source path of the toolbox file (CityEnergyAnalyst.py) - hint: it is relative
    to the current file!
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 'CityEnergyAnalyst.py'))


def find_toolbox_destination():
    """
    Find the destination path for the toolbox file (City Energy Analyst.pyt) - hint: the
    folder is similar to "%APPDATA%\ESRI\Desktop10.4\ArcToolbox\My Toolboxes"
    """
    destination = os.path.join(
        os.path.expandvars(r"$APPDATA\ESRI\Desktop%s\ArcToolbox\My Toolboxes" % get_arcgis_version()),
        'City Energy Analyst.pyt')
    return destination


def get_arcgis_paths():
    """
    Use the windows registry to figure out the paths to the following folders:

    - bin
    - arcpy
    - scripts

    as subfolders of the installation directory.
    """
    import _winreg
    registry = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    arcgis_version = get_arcgis_version()
    try:
        key = _winreg.OpenKey(registry, r"SOFTWARE\wow6432Node\ESRI\Desktop%s" % arcgis_version)
    except WindowsError:
        key = _winreg.OpenKey(registry, r"SOFTWARE\ESRI\Desktop%s" % arcgis_version)
    install_dir, _ = _winreg.QueryValueEx(key, 'InstallDir')
    paths = [os.path.join(install_dir, 'bin64'),
            os.path.join(install_dir, 'arcpy'),
            os.path.join(install_dir, 'scripts')]
    return paths

def get_arcgis_version():
    """Check the registry for ArcGIS and return the version. Checks the following two locations:

    - HKLM\software\wow6432Node\esri\Arcgis\RealVersion
    - HKLM\SOFTWARE\ESRI\ArcGIS\RealVersion

    returns the version string as ``"major.minor"``, so ``"10.4"`` or ``"10.5"``
    """
    import _winreg
    registry = _winreg.ConnectRegistry(None, _winreg.HKEY_LOCAL_MACHINE)
    try:
        key = _winreg.OpenKey(registry, r"software\wow6432Node\esri\Arcgis")
    except WindowsError:
        key = _winreg.OpenKey(registry, r"SOFTWARE\ESRI\ArcGIS")
    value, _ = _winreg.QueryValueEx(key, 'RealVersion')
    return '.'.join(value.split('.')[:2])



if __name__ == '__main__':
    main()
