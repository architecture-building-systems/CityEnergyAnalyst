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
    'open': {'databases': 'CH', 'weather': 'Zug-inducity_1990_2010_TMY', 'latitude': 47.1628017306431, 'longitude': 8.31,
             'radiation': 'open.baseline.radiation.csv',
             'properties_surfaces': 'open.baseline.properties_surfaces.csv'},
    'zug/baseline': {'databases': 'CH', 'weather': 'Zug-inducity_1990_2010_TMY', 'latitude': 47.1628017306431, 'longitude': 8.31,
                     'radiation': 'zug.baseline.radiation.csv',
                     'properties_surfaces': 'zug.baseline.properties_surfaces.csv'},
    'zurich/baseline': {'databases': 'CH', 'weather': 'Zuerich-Kloten_1990_2010_TMY', 'latitude': 46.9524055556, 'longitude': 7.43958333333,
                        'radiation': 'hq.baseline.radiation.csv',
                        'properties_surfaces': 'hq.baseline.properties_surfaces.csv'},
    'zurich/masterplan': {'databases': 'CH', 'weather': 'Zuerich-ETHZ_1990-2010_TMY', 'latitude': 46.9524055556, 'longitude': 7.43958333333,
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
        'name': 'run_unit_tests',
        'actions': [run_unit_tests],
        'task_dep': [],
        'verbosity': 1
    }


def task_download_reference_cases():
    """Download the (current) state of the reference cases"""
    def download_reference_cases():
        if os.path.exists(REFERENCE_CASE_PATH):
            print('Removing folder: %s' % REFERENCE_CASE_PATH)
            shutil.rmtree(REFERENCE_CASE_PATH)
            assert not os.path.exists(REFERENCE_CASE_PATH), 'FAILED to remove folder %s' % REFERENCE_CASE_PATH
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
        'name' : 'download_reference_cases',
        'actions': [download_reference_cases],
    }


def task_run_data_initializer():
    """Run the data initializer for each reference case"""

    def run_data_initializer(scenario_path, databases_path):
        import cea.datamanagement.data_initializer
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        config.data_initializer.databases_path = databases_path
        cea.datamanagement.data_initializer.main(config)

    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue

        databases_path = REFERENCE_CASES_DATA[reference_case]['databases']

        yield {
            'name': 'run_data_initializer:%s' % reference_case,
            'task_dep': ['download_reference_cases'],
            'actions': [
                (run_data_initializer, [], {
                    'scenario_path': scenario_path,
                    'databases_path': databases_path})],
        }

def task_run_archetypes_mapper():
    """Run the data helper for each reference case"""
    import cea.datamanagement.archetypes_mapper

    def run_archetypes_mapper(scenario_path):
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        cea.datamanagement.archetypes_mapper.main(config)

    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue

        yield {
            'name': 'run_archetypes_mapper:%s' % reference_case,
            'task_dep': ['run_data_initializer:%s' % reference_case],
            'actions': [
                (run_archetypes_mapper, [], {
                    'scenario_path': scenario_path})],
        }

def task_run_demand():
    """run the demand script for each reference cases and weather file"""
    import cea.demand.demand_main

    def run_demand(scenario_path, weather):
        import cea.config
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path

        # make sure weather file is copied to inputs first
        import cea.datamanagement.weather_helper
        import cea.demand.schedule_maker.schedule_maker
        config.weather_helper.weather = weather
        cea.datamanagement.weather_helper.main(config)
        cea.demand.schedule_maker.schedule_maker.main(config)
        cea.demand.demand_main.main(config)

    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue

        weather = REFERENCE_CASES_DATA[reference_case]['weather']

        yield {
            'name': 'run_demand:%(reference_case)s' % locals(),
            'task_dep': ['download_reference_cases', 'run_archetypes_mapper:%s' % reference_case],
            'actions': [(run_demand, [], {
                'scenario_path': scenario_path,
                'weather': weather
            })],
        }


def task_run_embodied_energy():
    """Run the embodied energy script for each reference case"""
    import cea.analysis.lca.embodied

    def run_embodied_energy(scenario_path):
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        config.emissions.year_to_calculate = 2050
        cea.analysis.lca.embodied.main(config=config)

    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue

        yield {
            'name': 'run_embodied_energy:%(reference_case)s' % locals(),
            'task_dep': ['download_reference_cases', 'run_archetypes_mapper:%s' % reference_case],
            'actions': [(run_embodied_energy, [scenario_path])],
        }


def task_run_emissions_operation():
    """run the emissions operation script for each reference case"""
    import cea.analysis.lca.operation

    def run_emissions_operation(scenario_path):
        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        config.scenario = scenario_path
        cea.analysis.lca.operation.main(config)

    for reference_case, scenario_path in REFERENCE_CASES.items():
        if _reference_cases and reference_case not in _reference_cases:
            continue

        yield {
            'name': 'run_emissions_operation:%(reference_case)s' % locals(),
            'task_dep': ['run_demand:%(reference_case)s' % locals()],
            'actions': [(run_emissions_operation, [], {
                'scenario_path': scenario_path,
            })],
        }

def task_run_thermal_network():
    """run the thermal_network for the included reference case"""
    def run_thermal_network():
        import cea.technologies.thermal_network.thermal_network as thermal_network
        from cea.technologies.network_layout.main import NetworkLayout, layout_network

        config = cea.config.Configuration(cea.config.DEFAULT_CONFIG)
        locator = cea.inputlocator.InputLocator(scenario=REFERENCE_CASES['open'])
        config.scenario = locator.scenario
        config.multiprocessing = True
        config.thermal_network.start_t = 100
        config.thermal_network.stop_t = 200
        config.thermal_network.network_type = 'DH'
        config.network_layout.network_type = 'DH'

        # first, create the network layout
        network_layout = NetworkLayout(config.network_layout)
        layout_network(network_layout, locator, [])
        thermal_network.main(config)

    return {
        'name': 'run_thermal_network',
        'task_dep': ['run_demand:open'],
        'actions': [(run_thermal_network, [], {})],
    }

def main(config):
    from doit.api import DoitMain
    from doit.task import dict_to_task
    from doit.cmd_base import TaskLoader

    global _reference_cases
    if not config.test.reference_cases:
        _reference_cases = ['open']
    elif 'all' in config.test.reference_cases:
        _reference_cases = REFERENCE_CASES.keys()
    else:
        _reference_cases = [rc for rc in config.test.reference_cases if rc in REFERENCE_CASES.keys()]

    if 'all' in config.test.tasks:
        tasks = [t[len('task_'):] for t in globals().keys() if t.startswith('task_')]
    else:
        tasks = config.test.tasks

    class CeaTaskLoader(TaskLoader):
        """Add functionality to only run specific tasks"""
        def load_tasks(self, cmd, opt_values, pos_args):
            task_list = []
            for task_name in tasks:
                print('Configuring task %s' % task_name)
                func = globals()['task_' + task_name]
                if isinstance(func(), dict):
                    task_dict = func()
                    task_dict['verbosity'] = config.test.verbosity
                    task_list.append(dict_to_task(task_dict))
                else:
                    for task_dict in func():
                        task_dict['verbosity'] = config.test.verbosity
                        task_list.append(dict_to_task(task_dict))
            task_config = {'verbosity': config.test.verbosity}
            return task_list, task_config

    sys.exit(DoitMain(CeaTaskLoader()).run([]))


if __name__ == '__main__':
    main(cea.config.Configuration())
