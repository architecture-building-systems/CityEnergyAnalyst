"""
"Makefile" for doit to test the whole package with Jenkins.

The reference cases can be found here: https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip
"""
import requests
import os
import shutil
import zipfile

REPOSITORY_URL = "https://github.com/architecture-building-systems/cea-reference-case/archive/%s.zip"
# REPOSITORY_NAME = "master"
REPOSITORY_NAME = "i346-Radiation-data-missing-from-reference-case-zug"

ARCHIVE_PATH = os.path.expandvars(r'%TEMP%\cea-reference-case.zip')
REFERENCE_CASE_PATH = os.path.expandvars(r'%TEMP%\cea-reference-case')

REFERENCE_CASES = {
    'zug/baseline': os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME, "reference-case-zug",
                                 "baseline"),
    'hq/baseline': os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME, "reference-case (HQ)",
                                "baseline"),
    'hq/masterplan': os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME, "reference-case (HQ)",
                                  "masterplan")}

REFERENCE_CASES_DATA = {'zug/baseline': {'weather': 'Zug', 'latitude': 47.1628017306431, 'longitude': 8.31},
                        'hq/baseline': {'weather': 'Zurich', 'latitude': 46.9524055556, 'longitude': 7.43958333333},
                        'hq/masterplan': {'weather': 'Zurich', 'latitude': 46.9524055556, 'longitude': 7.43958333333}}

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
        r = requests.get(REPOSITORY_URL % REPOSITORY_NAME, auth=get_github_auth())
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


def task_run_data_helper():
    """Run the data helper for each reference case"""
    import cea.demand.preprocessing.properties
    for reference_case, scenario_path in REFERENCE_CASES.items():
        yield {
            'name': reference_case,
            'actions': [
                (cea.demand.preprocessing.properties.run_as_script, [], {
                    'scenario_path': scenario_path})],
            'verbosity': 2,
        }


def task_run_radiation():
    """Run radiation for each reference case"""
    import cea.resources.radiation
    import cea.inputlocator
    for reference_case, scenario_path in REFERENCE_CASES.items():
        locator = cea.inputlocator.InputLocator(scenario_path)
        data = REFERENCE_CASES_DATA[reference_case]
        yield {
            'name': reference_case,
            'actions': [(cea.resources.radiation.run_as_script, [], {
                'scenario_path': scenario_path,
                'weather_path': locator.get_weather(data['weather']),
                'latitude': data['latitude'],
                'longitude': data['longitude'],
                'year': 2010,
            })]
        }


def task_run_demand():
    """run the demand script for each reference cases and weather file"""
    import cea.demand.demand_main
    import cea.inputlocator
    for reference_case, scenario_path in REFERENCE_CASES.items():
        locator = cea.inputlocator.InputLocator(scenario_path)
        weather = REFERENCE_CASES_DATA[reference_case]['weather']
        yield {
            'name': '%(reference_case)s@%(weather)s' % locals(),
            'actions': [(cea.demand.demand_main.run_as_script, [], {
                'scenario_path': scenario_path,
                'weather_path': locator.get_weather(weather)
            })],
            'verbosity': 2,
        }


if __name__ == '__main__':
    import doit

    doit.run(globals())
