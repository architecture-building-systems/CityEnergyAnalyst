"""
"Makefile" for doit to test the whole package with Jenkins.

The reference cases can be found here: https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip
"""
import requests
import os
import shutil
import zipfile


def task_download_reference_case_zug():
    """Download the (current) state of the reference-case-zug"""

    def download_reference_case_zug():
        dest_folder = os.path.expandvars(r'%TEMP%\cea-reference-case')
        dest_file = os.path.expandvars(r'%TEMP%\cea-reference-case.zip')

        # get the username / password for github
        with open(os.path.expanduser('~/github.auth')) as f:
            user, password = map(str.strip, f.readlines())

        # download the zip file
        if os.path.exists(dest_file):
            os.remove(dest_file)
        r = requests.get("https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip",
                         auth=(user, password))
        assert r.ok, 'could not download the reference case'
        with open(dest_file, 'wb') as f:
            f.write(r.content)

        # extract the reference cases to the temp folder
        if os.path.exists(dest_folder):
            shutil.rmtree(dest_folder)
        archive = zipfile.ZipFile(dest_file)
        archive.extractall(dest_folder)


    return {
        'actions': [download_reference_case_zug],
        'targets': [r'c:\reference-case-zug\baseline\input']
    }


if __name__ == '__main__':
    import doit

    doit.run(globals())
