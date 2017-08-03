"""
"Makefile" for doit to test the whole package with Jenkins.

This file gets run with the ``cea test`` command as well as by the Jenkins continuous integration server. It runs all
the unit tests in the ``cea/tests/`` folder as well as some of the CEA scripts, to make sure they at least run through.

In order to run reference cases besides the one called "open", you will need to set up authentication to the private
GitHub repository. The easiest way to do this is with ``cea test --save --user USERNAME --token PERSONAL_ACCESS_TOKEN``,
adding your own user name and a GitHub personal access token.

The reference cases can be found here: https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip
"""
import os
import shutil
import sys
import zipfile

import requests

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"

__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

REPOSITORY_URL = "https://github.com/architecture-building-systems/cea-reference-case/archive/%s.zip"
REPOSITORY_NAME = "master"


if 'JOB_NAME' in os.environ:
    # this script is being run as part of a Jenkins job
    ARCHIVE_PATH = os.path.expandvars(r'%TEMP%\%JOB_NAME%\cea-reference-case.zip')
    REFERENCE_CASE_PATH = os.path.expandvars(r'%TEMP%\%JOB_NAME%\cea-reference-case')
else:
    ARCHIVE_PATH = os.path.expandvars(r'%TEMP%\cea-reference-case.zip')
    REFERENCE_CASE_PATH = os.path.expandvars(r'%TEMP%\cea-reference-case')

REFERENCE_CASES = {
    'open': os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME, "reference-case-open",
                         "baseline"),
    'zug/baseline': os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME, "reference-case-zug",
                                 "baseline"),
    'zurich/baseline': os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME,
                                    "reference-case-zurich",
                                    "baseline"),
    'zurich/masterplan': os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME,
                                      "reference-case-zurich",
                                      "masterplan")}

REFERENCE_CASES_DATA = {
    'open': {'weather': 'Zug', 'latitude': 47.1628017306431, 'longitude': 8.31,
             'radiation': 'https://shared.ethz.ch/owncloud/s/uF6f4EWhPF31ko4/download',
             'properties_surfaces': 'https://shared.ethz.ch/owncloud/s/NALgN4Tlhho6QEC/download'},
    'zug/baseline': {'weather': 'Zug', 'latitude': 47.1628017306431, 'longitude': 8.31,
                     'radiation': 'https://shared.ethz.ch/owncloud/s/qgra4F2RJfKXzOp/download',
                     'properties_surfaces': 'https://shared.ethz.ch/owncloud/s/9w5ueJbXWSKaxvF/download'},
    'zurich/baseline': {'weather': 'Zurich', 'latitude': 46.9524055556, 'longitude': 7.43958333333,
                        'radiation': 'https://shared.ethz.ch/owncloud/s/8PNp6U1jpR0HnzC/download',
                        'properties_surfaces': 'https://shared.ethz.ch/owncloud/s/tYLGZcBGLO9Wpy9/download'},
    'zurich/masterplan': {'weather': 'Zurich', 'latitude': 46.9524055556, 'longitude': 7.43958333333,
                          'radiation': 'https://shared.ethz.ch/owncloud/s/MG3FeiSMVnIekwp/download',
                          'properties_surfaces': 'https://shared.ethz.ch/owncloud/s/HFHttennomZSbSf/download'}}

# set to github user and personal access token in main
_user = None
_token = None
_reference_cases = []


def get_github_auth():
    """
    get the username / token for github from a file in the home directory
    called "cea_github.auth". The first line contains the user, the second line
    the personal access token.

    :return: (user, token)
    """
    if _user and _token:
        return _user, _token

    with open(os.path.expanduser(r'~\cea_github.auth')) as f:
        user, token = map(str.strip, f.readlines())
    return user, token


def task_run_unit_tests():
    """run the unittests"""
    def run_unit_tests():
        import unittest
        import os
        testsuite = unittest.defaultTestLoader.discover(os.path.dirname(__file__))
        result = unittest.TextTestRunner(verbosity=1).run(testsuite)
        return result.wasSuccessful()
    return {
        'actions': [run_unit_tests],
        'task_dep': [],
        'verbosity': 1
    }


def task_download_reference_cases():
    """Download the (current) state of the reference-case-zug"""
    def download_reference_cases():
        if os.path.exists(REFERENCE_CASE_PATH):
            shutil.rmtree(REFERENCE_CASE_PATH)
        if not _reference_cases or ('open' in {'open'} and len({'open'}) == 1):
            # handle case of no reference cases selected or only 'open' selected
            # (just use the built-in reference case)
            # extract the reference-case-open to the folder
            import cea.examples
            archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
            archive.extractall(os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME))
        else:
            if os.path.exists(ARCHIVE_PATH):
                os.remove(ARCHIVE_PATH)
            r = requests.get(REPOSITORY_URL % REPOSITORY_NAME, auth=get_github_auth())
            assert r.ok, 'could not download the reference case'
            with open(ARCHIVE_PATH, 'wb') as f:
                f.write(r.content)
            # extract the reference cases to the temp folder
            archive = zipfile.ZipFile(ARCHIVE_PATH)
            archive.extractall(REFERENCE_CASE_PATH)

            # extract the reference-case-open to the folder
            import cea.examples
            archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
            archive.extractall(os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME))

    return {
        'actions': [download_reference_cases],
        'verbosity': 1,
    }


def task_run_data_helper():
    """Run the data helper for each reference case"""
    import cea.demand.preprocessing.properties
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
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
        r = requests.get(data['properties_surfaces'])
        assert r.ok, 'could not download the properties_surfaces.csv file'
        with open(locator.get_surface_properties(), 'w') as f:
            f.write(r.content)
        r = requests.get(data['radiation'])
        assert r.ok, 'could not download the radiation.csv file'
        with open(locator.get_radiation(), 'w') as f:
            f.write(r.content)
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
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
        if _reference_cases and reference_case not in _reference_cases:
            continue
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
    """graph default demand variables for each reference case"""
    import cea.plots.graphs_demand
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.plots.graphs_demand.run_as_script, [], {
                'scenario_path': scenario_path
            })],
            'verbosity': 1,
        }

def task_run_embodied_energy():
    """Run the embodied energy script for each reference case"""
    import cea.analysis.lca.embodied
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.analysis.lca.embodied.run_as_script, [], {
                'scenario_path': scenario_path,
                'year_to_calculate': 2050
            })],
            'verbosity': 1,
        }


def task_run_emissions_operation():
    """run the emissions operation script for each reference case"""
    import cea.analysis.lca.operation
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.analysis.lca.operation.run_as_script, [], {
                'scenario_path': scenario_path
            })],
            'verbosity': 1,
        }


def task_run_emissions_mobility():
    """run the emissions mobility script for each reference case"""
    import cea.analysis.lca.mobility
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.analysis.lca.mobility.run_as_script, [], {
                'scenario_path': scenario_path
            })],
            'verbosity': 1,
        }


def task_run_heatmaps():
    """run the heat maps script for each reference case"""
    try:
        from cea.interfaces.arcgis.modules import arcpy
    except ImportError:
        # do not require ArcGIS to be installed, but skip testing the heatmaps
        # module if it isn't installed.
        return
    import cea.plots.heatmaps
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.plots.heatmaps.run_as_script, [], {
                'scenario_path': scenario_path
            })],
            'verbosity': 1,
        }


def task_run_scenario_plots():
    """run the scenario plots script for each reference case"""
    import cea.plots.scenario_plots
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.plots.scenario_plots.run_as_script, [], {
                'scenario_folders': [scenario_path],
                'output_file': None  # use default
            })],
            'verbosity': 1,
        }


def main(user=None, token=None, reference_cases=None):
    from doit.api import DoitMain
    from doit.api import ModuleTaskLoader
    if user:
        global _user
        _user = user
    if token:
        global _token
        _token = token
    if reference_cases and 'all' not in reference_cases:
        global _reference_cases
        _reference_cases = reference_cases
    sys.exit(DoitMain(ModuleTaskLoader(globals())).run([]))


if __name__ == '__main__':
    main()
