"""
"Makefile" for doit to test the whole package with Jenkins.

This file gets run with the ``cea test`` command as well as by the Jenkins continuous integration server. It runs all
the unit tests in the ``cea/tests/`` folder as well as some of the CEA scripts, to make sure they at least run through.

In order to run reference cases besides the one called "open", you will need to set up authentication to the private
GitHub repository. To do this, you need to create a GitHub [authentication token](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/).
Then, create a text file called ``cea_github.auth`` in your home directory (e.g. ``C:\Users\your-user-name`` for Windows systems or equivalent on
POSIX systems, ask your administrator if you don't know what this is). The file should contain two lines, the first being
your GitHub user name the second the authentication token.

The reference cases can be found here: https://github.com/architecture-building-systems/cea-reference-case/archive/master.zip
"""
import os
import shutil
import sys
import zipfile
import tempfile
import cea.inputlocator
import cea.config

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
    ARCHIVE_PATH = os.path.expandvars(os.path.join(tempfile.gettempdir(), '%JOB_NAME%/cea-reference-case.zip'))
    REFERENCE_CASE_PATH = os.path.expandvars(os.path.join(tempfile.gettempdir(), '%JOB_NAME%/cea-reference-case'))
else:
    ARCHIVE_PATH = os.path.expandvars(os.path.join(tempfile.gettempdir(), 'cea-reference-case.zip'))
    REFERENCE_CASE_PATH = os.path.expandvars(os.path.join(tempfile.gettempdir(), 'cea-reference-case'))

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
             'radiation': 'open.baseline.radiation.csv',
             'properties_surfaces': 'open.baseline.properties_surfaces.csv'},
    'zug/baseline': {'weather': 'Zug', 'latitude': 47.1628017306431, 'longitude': 8.31,
                     'radiation': 'zug.baseline.radiation.csv',
                     'properties_surfaces': 'zug.baseline.properties_surfaces.csv'},
    'zurich/baseline': {'weather': 'Zurich', 'latitude': 46.9524055556, 'longitude': 7.43958333333,
                        'radiation': 'hq.baseline.radiation.csv',
                        'properties_surfaces': 'hq.baseline.properties_surfaces.csv'},
    'zurich/masterplan': {'weather': 'Zurich', 'latitude': 46.9524055556, 'longitude': 7.43958333333,
                          'radiation': 'hq.masterplan.radiation.csv',
                          'properties_surfaces': 'hq.masterplan.properties_surfaces.csv'}}

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

    with open(os.path.expanduser('~/cea_github.auth')) as f:
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
        # extract the bundled reference case (we will use this anyways
        import cea.examples
        archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
        archive.extractall(os.path.join(REFERENCE_CASE_PATH, "cea-reference-case-%s" % REPOSITORY_NAME))

        if len([rc for rc in _reference_cases if rc.lower() != 'open']):
            if os.path.exists(ARCHIVE_PATH):
                os.remove(ARCHIVE_PATH)
            r = requests.get(REPOSITORY_URL % REPOSITORY_NAME, auth=get_github_auth())
            assert r.ok, 'could not download the reference case'
            with open(ARCHIVE_PATH, 'wb') as f:
                f.write(r.content)
            # extract the reference cases to the temp folder
            archive = zipfile.ZipFile(ARCHIVE_PATH)
            archive.extractall(REFERENCE_CASE_PATH)

    return {
        'actions': [download_reference_cases],
        'verbosity': 1,
    }


def task_run_data_helper():
    """Run the data helper for each reference case"""
    import cea.demand.preprocessing.data_helper
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        yield {
            'name': reference_case,
            'actions': [
                (cea.demand.preprocessing.data_helper.main, [], {
                    'config': config})],
            'verbosity': 1,
        }


def task_download_radiation():
    """For some reference cases, the radiation and properties_surfaces.csv files are too big for git and are stored
    with git lfs... For these cases we download a known good version from a url"""
    def download_radiation(scenario_path, reference_case):
        locator = cea.inputlocator.InputLocator(scenario_path)
        data = REFERENCE_CASES_DATA[reference_case]
        properties_surfaces_csv = os.path.join(os.path.dirname(__file__), 'radiation_data', data['properties_surfaces'])
        radiation_csv = os.path.join(os.path.dirname(__file__), 'radiation_data', data['radiation'])
        shutil.copyfile(properties_surfaces_csv, locator.get_surface_properties())
        shutil.copyfile(radiation_csv, locator.get_radiation())

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
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        locator = cea.inputlocator.InputLocator(scenario_path)
        weather = REFERENCE_CASES_DATA[reference_case]['weather']

        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        config.weather = weather
        config.demand.use_daysim_radiation = False

        yield {
            'name': '%(reference_case)s@%(weather)s' % locals(),
            'actions': [(cea.demand.demand_main.main, [], {
                'config': config,
            })],
            'verbosity': 1,
        }


def task_run_embodied_energy():
    """Run the embodied energy script for each reference case"""
    import cea.analysis.lca.embodied
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        config.embodied_energy.year_to_calculate = 2050
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.analysis.lca.embodied.main, [], {
                'config': config,
            })],
            'verbosity': 1,
        }


def task_run_emissions_operation():
    """run the emissions operation script for each reference case"""
    import cea.analysis.lca.operation
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.analysis.lca.operation.main, [], {
                'config': config
            })],
            'verbosity': 1,
        }


def task_run_emissions_mobility():
    """run the emissions mobility script for each reference case"""
    import cea.analysis.lca.mobility
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.analysis.lca.mobility.main, [], {
                'config': config
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
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.plots.heatmaps.main, [], {
                'config': config
            })],
            'verbosity': 1,
        }


def task_run_scenario_plots():
    """run the scenario plots script for each reference case"""
    import cea.plots.scenario_plots
    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue
        project = os.path.normpath(os.path.join(scenario_path, '..'))
        output_file = os.path.join(project, 'scenarios.pdf')

        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario_plots.project = project
        config.scenario_plots.scenarios = ['baseline']
        config.scenario_plots.output_file = output_file
        yield {
            'name': '%(reference_case)s' % locals(),
            'actions': [(cea.plots.scenario_plots.main, [], {
                'config': config,
            })],
            'verbosity': 1,
        }


def task_run_calibration():
    """run the calibration_sampling for each reference case"""
    def run_calibration():
        import cea.demand.calibration.bayesian_calibrator.calibration_sampling as calibration_sampling
        import cea.demand.calibration.bayesian_calibrator.calibration_gaussian_emulator as calibration_gaussian_emulator
        import cea.demand.calibration.bayesian_calibrator.calibration_main as calibration_main

        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        locator = cea.inputlocator.ReferenceCaseOpenLocator()

        config.scenario = locator.scenario
        config.single_calibration.building = 'B01'
        config.single_calibration.variables = ['U_win', 'U_wall', 'U_roof', 'n50', 'Tcs_set_C', 'Hs']
        config.single_calibration.load = 'Qcsf'
        config.single_calibration.samples = 10
        config.single_calibration.show_plots = False

        # run calibration_sampling
        calibration_sampling.sampling_main(locator=locator, config=config)

        # run calibration_gaussian_emulator
        calibration_gaussian_emulator.gaussian_emulator(locator=locator, config=config)

        # run calibration_main
        calibration_main.calibration_main(locator=locator, config=config)

        # make sure the files were created
        # FIXME: @JIMENOFONSECA - what files do I need to check? (this has changed)


    return {
        'actions': [(run_calibration, [], {})],
        'verbosity': 1,
    }


def main(config):
    from doit.api import DoitMain
    from doit.api import ModuleTaskLoader

    global _reference_cases
    if not config.test.reference_cases:
        _reference_cases = ['open']
    elif 'all' in config.test.reference_cases:
        _reference_cases = REFERENCE_CASES.keys()
    else:
        _reference_cases = [rc for rc in config.test.reference_cases if rc in REFERENCE_CASES.keys()]
    sys.exit(DoitMain(ModuleTaskLoader(globals())).run([]))


if __name__ == '__main__':
    main(cea.config.Configuration())
