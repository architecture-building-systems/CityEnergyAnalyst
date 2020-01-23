"""
Updates CEA and GUI by checking GitHub releases
"""
from __future__ import division

import os
import re
import cea
import sys
import requests
import subprocess
import tempfile
from pyunpack import Archive
from packaging import version

GITHUB_REPO_URL = 'https://github.com/architecture-building-systems/CityEnergyAnalyst'
DOWNLOAD_URL_PREFIX = '{}/releases/latest/download'.format(GITHUB_REPO_URL)
VERSION_REGEX = r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[0-9A-Za-z-]+)?'
DEPENDENCIES = 'Dependencies.7z'
GUI_FILE = 'win-unpacked.7z'  # For windows only


def update_available(online_version):
    return version.parse(online_version) > version.parse(cea.__version__)


# Could also use PyPi API to get latest version on PyPi
# https://pypi.org/pypi/cityenergyanalyst/json
def fetch_online_version():
    """Get online version by extracting version number from GitHub redirect url"""
    r = requests.head("{}/releases/latest".format(GITHUB_REPO_URL))
    url = r.headers['Location']
    online_version = re.search(VERSION_REGEX, url).group(0)
    if not online_version:
        raise Exception('Could not retrieve online version.')
    return online_version


# Ignore for now
def download_dependencies():
    pass


def installed_as_editable():
    """
    Used to determine if CEA is installed as dev
    Developer version is installed as editable by installer
    """
    for path_item in sys.path:
        egg_link = os.path.join(path_item, 'cityenergyanalyst' + '.egg-link')
        if os.path.isfile(egg_link):
            return True
    return False


def main(*_):
    """
    Update CEA using GitHub latest release tag. CEA will be updated using `pip` and GUI will be downloaded from GitHub
    """
    print("Checking latest version available online...")
    online_version = fetch_online_version()
    print("Version {} found.".format(online_version))
    if update_available(online_version):
        if not installed_as_editable():  # Should not `pip install cityenergyanalyst` if dev version is installed
            print("CEA installed as dev. Will only update CEA GUI. Run `git pull` to update CEA")
        else:
            # Update CEA
            print("\n### UPDATING CEA ###")
            download_dependencies()
            # Run pip to update CEA from PyPi
            pip_cmd = "{python} -m pip install -U cityenergyanalyst".format(python=sys.executable)
            print("Running `{}`".format(pip_cmd))
            subprocess.call(pip_cmd.split(" "))

        # Update CEA GUI
        print("\n### UPDATING GUI ###")
        # Get GUI path relative to python path (only true if folder structure holds)
        gui_url = '{}/{}'.format(DOWNLOAD_URL_PREFIX, GUI_FILE)
        gui_path = os.path.abspath(os.path.join(sys.executable, "../../.."))
        temp_path = os.path.join(tempfile.gettempdir(), 'temp.7z')
        sys.stdout.write("Downloading GUI...")
        with open(temp_path, "wb") as f:
            r = requests.get(gui_url, stream=True)
            total_length = r.headers.get('content-length')
            downloaded_length = 0
            if total_length is None:  # no content length header
                f.write(r.content)
            else:
                total_length = int(total_length)
                for chunk in r.iter_content(chunk_size=1024*100):
                    f.write(chunk)
                    downloaded_length += len(chunk)
                    sys.stdout.write("\rDownloading GUI... (%.2f%%)" % (100 * downloaded_length / total_length))
                print("\rDownloading GUI... (done!)  ")
        sys.stdout.write("Extracting GUI...")
        Archive(temp_path).extractall(gui_path)
        os.remove(temp_path)  # Cleanup
        print("\rExtracting GUI... (done!)")

        print("\nCEA updated to version {}".format(online_version))

    else:  # Do not do anything if no update available
        print("\nYou already have the latest version.")


if __name__ == '__main__':
    main()
