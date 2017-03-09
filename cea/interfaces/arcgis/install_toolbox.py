"""Install the toolbox into ArcGIS Desktop 10.4"""
import sys
import os.path


def main():
    """
    Perform the following steps:

    - add a link to the python.exe that ran setup.py to user's home directory in the file cea_python.pth
    - copy the file "City Energy Analyst.py" to the "My Toolboxes" folder of ArcGIS Desktop and rename the
      extension to ".pyt"
    """
    # write out path to python.exe to the file cea_python.pth
    with open(os.path.expanduser('~/cea_python.pth'), 'w') as f:
        f.write(sys.executable)


if __name__ == '__main__':
    main()