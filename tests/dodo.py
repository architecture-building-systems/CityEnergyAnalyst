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

REFERENCE_CASES_DATA = {
    'zug/baseline': {'weather': 'Zug', 'latitude': 47.1628017306431, 'longitude': 8.31,
                     'radiation': 'https://shared.ethz.ch/owncloud/s/qgra4F2RJfKXzOp/download',
                     'properties_surfaces': 'https://shared.ethz.ch/owncloud/s/9w5ueJbXWSKaxvF/download'},
    'hq/baseline': {'weather': 'Zurich', 'latitude': 46.9524055556, 'longitude': 7.43958333333,
                    'radiation': 'https://shared.ethz.ch/owncloud/s/8PNp6U1jpR0HnzC/download',
                    'properties_surfaces': 'https://shared.ethz.ch/owncloud/s/tYLGZcBGLO9Wpy9/download'},
    'hq/masterplan': {'weather': 'Zurich', 'latitude': 46.9524055556, 'longitude': 7.43958333333,
                      'radiation': 'https://shared.ethz.ch/owncloud/s/MG3FeiSMVnIekwp/download',
                      'properties_surfaces': 'https://shared.ethz.ch/owncloud/s/HFHttennomZSbSf/download'}}

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
        'verbosity': 1,
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
            'verbosity': 1,
        }


def task_download_radiation():
    """For some reference cases, the radiation and properties_surfaces.csv files are too big for git and are stored
    with git lfs... For these cases we download a known good version from a url"""
    def download_radiation(scenario_path, reference_case):
        import cea.inputlocator
        locator = cea.inputlocator.InputLocator(scenario_path)
        data = REFERENCE_CASES_DATA[reference_case]
        if os.path.getsize(locator.get_surface_properties()) < 500:
            r = requests.get(data['properties_surfaces'])
            assert r.ok, 'could not download the properties_surfaces.csv file'
            with open(locator.get_surface_properties(), 'w') as f:
                f.write(r.content)
        if os.path.getsize(locator.get_radiation()) < 500:
            r = requests.get(data['radiation'])
            assert r.ok, 'could not download the radiation.csv file'
            with open(locator.get_radiation(), 'w') as f:
                f.write(r.content)
    for reference_case, scenario_path in REFERENCE_CASES.items():
        yield {
            'name': reference_case,
            'actions': [(download_radiation, [], {
                'scenario_path': scenario_path,
                'reference_case': reference_case})]
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
            'verbosity': 1,
        }


def task_run_demand_graphs():
    """graph random demand variables for each reference case"""
    import cea.plots.graphs
    import random
    for reference_case, scenario_path in REFERENCE_CASES.items():
        all_fields = cea.plots.graphs.demand_graph_fields(scenario_path)
        fields = random.sample(all_fields, 4)
        yield {
            'name': '%(reference_case)s@%(fields)s' % locals(),
            'actions': [(cea.plots.graphs.run_as_script, [], {
                'scenario_path': scenario_path,
                'analysis_fields': fields
            })],
            'verbosity': 1,
        }

def task_run_embodied_energy():
    """Run the embodied energy script for each reference case"""
    import cea.analysis.embodied
    for reference_case, scenario_path in REFERENCE_CASES.items():
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.analysis.embodied.run_as_script, [], {
                'scenario_path': scenario_path,
                'year_to_calculate': 2050
            })],
            'verbosity': 1,
        }


def task_run_emissions_operation():
    """run the emissions operation script for each reference case"""
    import cea.analysis.operation
    for reference_case, scenario_path in REFERENCE_CASES.items():
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.analysis.embodied.run_as_script, [], {
                'scenario_path': scenario_path,
                'year_to_calculate': 2050
            })],
            'verbosity': 1,
        }


if __name__ == '__main__':
    import doit

    doit.run(globals())
