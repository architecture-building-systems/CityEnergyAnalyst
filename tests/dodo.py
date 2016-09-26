"""
"Makefile" for doit to test the whole package with Jenkins.

The reference cases can be found here: https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip
"""
import requests
import os
import shutil
import zipfile

ARCHIVE_PATH = os.path.expandvars(r'%TEMP%\cea-reference-case.zip')
REFERENCE_CASE_PATH = os.path.expandvars(r'%TEMP%\cea-reference-case')


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
    def download_reference_cases():
        if os.path.exists(ARCHIVE_PATH):
            os.remove(ARCHIVE_PATH)
        r = requests.get("https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip",
                         auth=get_github_auth())
        assert r.ok, 'could not download the reference case'
        with open(ARCHIVE_PATH, 'wb') as f:
            f.write(r.content)

        # extract the reference cases to the temp folder
        if os.path.exists(REFERENCE_CASE_PATH):
            shutil.rmtree(REFERENCE_CASE_PATH)
        archive = zipfile.ZipFile(ARCHIVE_PATH)
        archive.extractall(REFERENCE_CASE_PATH)

    return {
        'actions': [download_reference_cases],
        'verbosity': 2,
    }


def task_run_data_helper_zug():
    """Run the data helper for the zug reference case"""
    import cea.demand.preprocessing.properties
    return {
        'actions': [
            (cea.demand.preprocessing.properties.run_as_script, [], {
                'scenario_path': os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-master", "reference-case-zug",
                                              "baseline")})],
        'verbosity': 2,
    }



if __name__ == '__main__':
    import doit

    doit.run(globals())
