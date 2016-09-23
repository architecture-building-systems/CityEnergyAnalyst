"""
"Makefile" for doit to test the whole package with Jenkins.

The reference cases can be found here: https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip
"""
import requests
import os
import shutil
import zipfile

reference_case_folder = os.path.expandvars(r'%TEMP%\cea-reference-case')


def get_github_auth():
    """
    get the username / password for github from a file in the home directory
    called "github.auth". The first line contains the user, the second line
    the password.

    :return: (user, password)
    """
    with open(os.path.expanduser('~/github.auth')) as f:
        user, password = map(str.strip, f.readlines())
    return user, password


def task_download_reference_cases():
    """Download the (current) state of the reference-case-zug"""
    archive_path = os.path.expandvars(r'%TEMP%\cea-reference-case.zip')

    def download_reference_cases():
        if os.path.exists(archive_path):
            os.remove(archive_path)
        r = requests.get("https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip",
                         auth=get_github_auth())
        assert r.ok, 'could not download the reference case'
        with open(archive_path, 'wb') as f:
            f.write(r.content)

        # extract the reference cases to the temp folder
        if os.path.exists(reference_case_folder):
            shutil.rmtree(reference_case_folder)
        archive = zipfile.ZipFile(archive_path)
        archive.extractall(reference_case_folder)

    return {
        'actions': [download_reference_cases],
        'targets': [r'c:\reference-case-zug\baseline\input']
    }


if __name__ == '__main__':
    import doit

    doit.run(globals())
