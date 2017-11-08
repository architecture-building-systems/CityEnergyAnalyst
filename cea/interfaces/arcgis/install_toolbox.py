"""Install the toolbox into ArcGIS Desktop 10.4 and 10.5"""
import sys
import shutil
import os.path


def main(_):
    """
    Perform the following steps:

    - add a link to the python.exe that ran setup.py to user's home directory in the file cea_python.pth
    - copy the file "CityEnergyAnalyst.py" to the "My Toolboxes" folder of ArcGIS Desktop and rename the
      extension to ".pyt"
    - copy cea.config and the default.config to the "My Toolboxes/cea" folder.
    - sets up .pth files to access arcpy from the cea python interpreter.
    - copy the inputlocator.py file
    - create the databases.pth file in the "My Toolboxes/cea" directory
    """
    # write out path to python.exe to the file cea_python.pth
    with open(os.path.expanduser('~/cea_python.pth'), 'w') as f:
        f.write(sys.executable)

    toolbox_dst = find_toolbox_destination()
    toolbox_folder = os.path.dirname(toolbox_dst)
    if not os.path.exists(toolbox_folder):
        os.makedirs(toolbox_folder)
    shutil.copy(find_toolbox_src(), toolbox_dst)

    copy_config(toolbox_folder)
    copy_inputlocator(toolbox_folder)

    with open(os.path.expanduser('~/cea_arcpy.pth'), 'w') as f:
        f.writelines('\n'.join(get_arcgis_paths()))
    print('toolbox installed.')


def copy_config(toolbox_folder):
    """Copy the cea/config.py, cea/default.config and an empty __init__.py file to the toolbox_folder"""
    import cea.config

    cea_dst_folder = get_cea_dst_folder(toolbox_folder)
    cea_src_folder = os.path.dirname(cea.config.__file__)
    shutil.copy(os.path.join(cea_src_folder, 'config.py'), cea_dst_folder)
    shutil.copy(os.path.join(cea_src_folder, 'default.config'), cea_dst_folder)
    shutil.copy(os.path.join(cea_src_folder, '__init__.py'), cea_dst_folder)


def get_cea_dst_folder(toolbox_folder):
    cea_dst_folder = os.path.join(toolbox_folder, 'cea')
    if not os.path.exists(cea_dst_folder):
        os.makedirs(cea_dst_folder)
    return cea_dst_folder


def copy_inputlocator(toolbox_folder):
    """Copy the cea/inputlocator.py file to the toolbox_folder and create the cea/databases.pth file"""
    import cea.inputlocator

    cea_dst_folder = get_cea_dst_folder(toolbox_folder)
    cea_src_folder = os.path.dirname(cea.inputlocator.__file__)
    shutil.copy(os.path.join(cea_src_folder, 'inputlocator.py'), cea_dst_folder)

    locator = cea.inputlocator.InputLocator(None)
    with open(os.path.join(cea_dst_folder, 'databases.pth'), 'w') as f:
        f.write(locator.db_path)


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
