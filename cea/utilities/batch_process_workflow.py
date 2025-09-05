"""
Batch processing CEA commands over all scenarios in a project.
This was originally explored and created for the ETH MiBS IDP 2023.
"""

# TODO: change the hard-coded path; this is subject to a structural separation of project-based CEA Features from scenario-based CEA Features

import os
import subprocess
import sys
import cea.config
import time

__author__ = "Zhongming Shi, Mathias Niffeler"
__copyright__ = "Copyright 2023, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Zhongming Shi, Mathias Niffeler"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Reynold Mok"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

# adding CEA to the environment
# Fix for running in PyCharm for users using micromamba
my_env = os.environ.copy()
my_env['PATH'] = f"{os.path.dirname(sys.executable)}:{my_env['PATH']}"

def exec_cea_commands(config, cea_scenario):
    """
    Automate user-defined CEA commands one after another.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :param cea_scenario: path to the CEA scenario to be assessed using CEA
    :type cea_scenario: file path
    :return:
    """
    # acquire the user-defined CEA commands
    export_to_rhino_gh = config.batch_process_workflow.export_to_rhino_gh
    import_from_rhino_gh = config.batch_process_workflow.import_from_rhino_gh

    database_helper = config.batch_process_workflow.database_helper
    archetypes_mapper = config.batch_process_workflow.archetypes_mapper
    weather_helper = config.batch_process_workflow.weather_helper
    surroundings_helper = config.batch_process_workflow.surroundings_helper
    terrain_helper = config.batch_process_workflow.terrain_helper
    streets_helper = config.batch_process_workflow.streets_helper

    radiation = config.batch_process_workflow.radiation
    demand_forecasting = config.batch_process_workflow.demand_forecasting

    emissions = config.batch_process_workflow.emissions
    system_costs = config.batch_process_workflow.system_costs

    solar_pv = config.batch_process_workflow.solar_potential_pv
    solar_pvt = config.batch_process_workflow.solar_potential_pvt
    solar_sc = config.batch_process_workflow.solar_potential_sc
    shallow_geothermal = config.batch_process_workflow.shallow_geothermal_potential
    water_body = config.batch_process_workflow.water_body_potential
    sewage_heat = config.batch_process_workflow.sewage_heat_potential

    thermal_network_layout = config.batch_process_workflow.thermal_network_layout
    thermal_network_operation = config.batch_process_workflow.thermal_network_operation

    optimisation = config.batch_process_workflow.optimisation

    results_summary_and_analytics = config.batch_process_workflow.results_summary_and_analytics

    # execute selected CEA commands
    if export_to_rhino_gh and not import_from_rhino_gh:
        subprocess.run(['cea', 'export-to-rhino-gh', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)

    if import_from_rhino_gh and not export_to_rhino_gh:
        subprocess.run(['cea', 'import-from-rhino-gh', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)

    if import_from_rhino_gh and export_to_rhino_gh:
        raise ValueError("Cannot import from and export to Rhino/Grasshopper at the same time.")

    if database_helper:
        subprocess.run(['cea', 'data-helper', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
    if archetypes_mapper:
        subprocess.run(['cea', 'archetypes-mapper', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
    if weather_helper:
        subprocess.run(['cea', 'weather-helper', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
    if surroundings_helper:
        subprocess.run(['cea', 'surroundings-helper', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
    if terrain_helper:
        subprocess.run(['cea', 'terrain-helper', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
    if streets_helper:
        subprocess.run(['cea', 'streets-helper', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)

    if radiation:
        subprocess.run(['cea', 'radiation', '--scenario', cea_scenario], env=my_env, check=True, capture_output=True)

    if solar_pv:
        subprocess.run(['cea', 'photovoltaic', '--scenario', cea_scenario], env=my_env, check=True, capture_output=True)

    if solar_sc:
        subprocess.run(['cea', 'solar-collector', '--scenario', cea_scenario],
                       env=my_env, check=True, capture_output=True)

    if solar_pvt:
        subprocess.run(['cea', 'photovoltaic-thermal', '--scenario', cea_scenario],
                       env=my_env, check=True, capture_output=True)

    if shallow_geothermal:
        subprocess.run(['cea', 'shallow-geothermal-potential', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
    if water_body:
        subprocess.run(['cea', 'water-body-potential', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)

    if demand_forecasting:
        subprocess.run(['cea', 'occupancy-helper', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
        subprocess.run(['cea', 'demand', '--scenario', cea_scenario], env=my_env, check=True, capture_output=True)

    if sewage_heat:
        subprocess.run(['cea', 'sewage-potential', '--scenario', cea_scenario], env=my_env, check=True, capture_output=True)

    if thermal_network_layout:
        subprocess.run(['cea', 'network-layout', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
    if thermal_network_operation:
        subprocess.run(['cea', 'thermal-network', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)

    if emissions:
        subprocess.run(['cea', 'emissions', '--scenario', cea_scenario], env=my_env, check=True, capture_output=True)

    if system_costs:
        subprocess.run(['cea', 'system-costs', '--scenario', cea_scenario], env=my_env, check=True, capture_output=True)

    if optimisation:
        subprocess.run(['cea', 'decentralized', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)
        subprocess.run(['cea', 'optimization-new', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)

    if results_summary_and_analytics:
        subprocess.run(['cea', 'export-results-csv', '--scenario', cea_scenario], env=my_env, check=True,
                       capture_output=True)


def main(config):
    """
    Batch processing all selectedscenarios under a project.

    :param config: the configuration object to use
    :type config: cea.config.Configuration
    :return:
    """

    # Start the timer
    t0 = time.perf_counter()

    assert os.path.exists(config.general.project), 'input file not found: %s' % config.project

    project_path = config.general.project
    scenario_name = config.general.scenario_name
    scenarios_list = config.batch_process_workflow.scenarios_to_simulate

    # Loop over one or all selected scenarios under the project
    for scenario in scenarios_list:
        # Ignore hidden directories
        if scenario.startswith('.') or os.path.isfile(os.path.join(project_path, scenario)):
            continue

        cea_scenario = os.path.join(project_path, scenario)
        print(f'Executing CEA simulations on {cea_scenario}.')
        try:
            # executing CEA commands
            exec_cea_commands(config, cea_scenario)
        except subprocess.CalledProcessError as e:
            print(f"CEA simulation for scenario `{scenario_name}` failed at script: {e.cmd[1]}.")
            err_msg = e.stderr
            if err_msg is not None:
                print(err_msg.decode())
            raise e

    # Print the time used for the entire processing
    time_elapsed = time.perf_counter() - t0
    print('The entire batch processing sequence is now completed - time elapsed: %d.2 seconds' % time_elapsed)


if __name__ == '__main__':
    main(cea.config.Configuration())
