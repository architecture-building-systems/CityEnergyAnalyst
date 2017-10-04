from __future__ import print_function

"""
This script implements the main command-line interface to the CEA. It allows running the various scripts through a
standard interface.
"""
from __future__ import absolute_import

import os
import cea.config
import cea.inputlocator

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2017, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"


def demand(args):
    """Run the demand script with the arguments provided."""
    import cea.demand.demand_main
    config = cea.config.Configuration(args.scenario)
    if not args.weather:
        args.weather = config.weather
    if not os.path.exists(args.weather):
        try:
            # allow using shortcut
            import cea.inputlocator
            args.weather = cea.inputlocator.InputLocator(None).get_weather(args.weather)
        except:
            args.weather = cea.inputlocator.InputLocator(None).get_default_weather()
    if not args.multiprocessing:
        # check config file, maybe it is turned on there
        args.multiprocessing = config.multiprocessing

    print('use_dynamic_infiltration_calculation: %s' % args.use_dynamic_infiltration_calculation)
    print('multiprocessing: %s' % args.multiprocessing)
    print('weather: %s' % args.weather)
    cea.demand.demand_main.run_as_script(scenario_path=args.scenario, weather_path=args.weather,
                                         use_dynamic_infiltration_calculation=args.use_dynamic_infiltration_calculation,
                                         multiprocessing=args.multiprocessing)


def data_helper(args):
    """Run the demand helper script with the arguments provided."""
    import cea.demand.preprocessing.properties
    cea.demand.preprocessing.properties.run_as_script(scenario_path=args.scenario,
                                                      prop_thermal_flag='thermal' in args.archetypes,
                                                      prop_architecture_flag='architecture' in args.archetypes,
                                                      prop_hvac_flag='HVAC' in args.archetypes,
                                                      prop_comfort_flag='comfort' in args.archetypes,
                                                      prop_internal_loads_flag='internal-loads' in args.archetypes)


def operation_costs(args):
    """Run the operation costs script with the arguments provided (args.scenario)."""
    import cea.analysis.operation_costs
    cea.analysis.operation_costs.run_as_script(scenario_path=args.scenario)


def emissions(args):
    """Run the emissions script with the arguments provided."""
    import cea.analysis.lca.operation
    import cea.inputlocator
    cea.analysis.lca.operation.lca_operation(locator=cea.inputlocator.InputLocator(args.scenario),
                                             Qww_flag='Qww' in args.extra_files_to_create,
                                             Qhs_flag='Qhs' in args.extra_files_to_create,
                                             Qcs_flag='Qcs' in args.extra_files_to_create,
                                             Qcdata_flag='Qcdata' in args.extra_files_to_create,
                                             Qcrefri_flag='Qcrefri' in args.extra_files_to_create,
                                             Eal_flag='Eal' in args.extra_files_to_create,
                                             Eaux_flag='Eaux' in args.extra_files_to_create,
                                             Epro_flag='Epro' in args.extra_files_to_create,
                                             Edata_flag='Edata' in args.extra_files_to_create, )


def embodied_energy(args):
    """Run the embodied energy script with the arguments provided."""
    import cea.analysis.lca.embodied
    import cea.globalvar
    gv = cea.globalvar.GlobalVariables()
    cea.analysis.lca.embodied.lca_embodied(year_to_calculate=args.year_to_calculate,
                                           locator=cea.inputlocator.InputLocator(args.scenario), gv=gv)


def mobility(args):
    """Run the mobility script with the arguments provided."""
    import cea.analysis.lca.mobility
    import cea.inputlocator
    cea.analysis.lca.mobility.lca_mobility(locator=cea.inputlocator.InputLocator(args.scenario))


def benchmark_graphs(args):
    """Run the benchmark graphs script with the arguments provided."""
    import cea.analysis.benchmark
    import cea.inputlocator
    locator_list = [cea.inputlocator.InputLocator(scenario) for scenario in args.scenarios]
    cea.analysis.benchmark.benchmark(locator_list=locator_list, output_file=args.output_file)


def weather_files(_):
    """List the available weather files to STDOUT."""
    import cea.inputlocator
    weather_names = cea.inputlocator.InputLocator(None).get_weather_names()
    for weather_name in weather_names:
        print(weather_name)


def weather_path(args):
    """Find the path to the weather file by name"""
    import cea.inputlocator
    weather_path = cea.inputlocator.InputLocator(None).get_weather(args.weather)
    print(weather_path)


def file_location(args):
    """Locate a file using the InputLocator. The file to find is named the same as the InputLocator
    attribute."""
    import cea.inputlocator
    locator = cea.inputlocator.InputLocator(args.scenario)
    print(getattr(locator, args.attribute)())


def demand_graphs(args):
    """Run the demand graphs script.
    If ``args.list_fields`` is set, then just return the list of valid fields - one per line.
    """
    import cea.plots.graphs_demand

    if args.list_fields:
        fields = cea.plots.graphs_demand.demand_graph_fields(args.scenario)
        print('\n'.join(sorted(fields)))
    else:
        import cea.inputlocator
        import cea.globalvar
        locator = cea.inputlocator.InputLocator(args.scenario)
        cea.plots.graphs_demand.graphs_demand(locator, args.analysis_fields[:4])


def scenario_plots(args):
    """Run the scenario plots script with the provided arguments (``output_file`` and ``scenarios``)."""
    import cea.plots.scenario_plots
    cea.plots.scenario_plots.plot_scenarios(scenarios=args.scenarios, output_file=args.output_file)


def latitude(args):
    """Return the latitude of the scenario, based on the building geometry shape file."""
    lat = _get_latitude(args.scenario)
    print(lat)


def _get_latitude(scenario_path):
    import fiona
    import cea.inputlocator
    with fiona.open(cea.inputlocator.InputLocator(scenario_path).get_zone_geometry()) as shp:
        lat = shp.crs['lat_0']
    return lat


def longitude(args):
    """Return the longitude of the scenario, based on the building geometry shape file."""
    lon = _get_longitude(args.scenario)
    print(lon)


def _get_longitude(scenario_path):
    import fiona
    import cea.inputlocator
    with fiona.open(cea.inputlocator.InputLocator(scenario_path).get_zone_geometry()) as shp:
        lon = shp.crs['lon_0']
    return lon


def radiation(args):
    """Run the radiation script with the arguments provided."""
    import cea.resources.radiation_arcgis.radiation
    import cea.globalvar

    if not args.latitude:
        args.latitude = _get_latitude(args.scenario)
    if not args.longitude:
        args.longitude = _get_longitude(args.scenario)

    locator = cea.inputlocator.InputLocator(args.scenario)
    if not args.weather_path:
        args.weather_path = locator.get_default_weather()
    elif args.weather_path in locator.get_weather_names():
        args.weather_path = locator.get_weather(args.weather_path)

    cea.resources.radiation_arcgis.radiation.solar_radiation_vertical(locator=locator,
                                                                      path_arcgis_db=args.arcgis_db,
                                                                      latitude=args.latitude,
                                                                      longitude=args.longitude, year=args.year,
                                                                      gv=cea.globalvar.GlobalVariables(),
                                                                      weather_path=args.weather_path)


def radiation_daysim(args):
    """Run the DAYSIM radiation script with the arguments provided."""
    import cea.resources.radiation_daysim.radiation_main

    locator = cea.inputlocator.InputLocator(args.scenario)

    if not args.weather_path:
        args.weather_path = locator.get_default_weather()
    elif args.weather_path in locator.get_weather_names():
        args.weather_path = locator.get_weather(args.weather_path)

    config = cea.config.Configuration(args.scenario)
    config.weather = args.weather_path

    options = ['rad-n', 'rad-af', 'rad-ab', 'rad-ad', 'rad-as', 'rad-ar', 'rad-aa', 'rad-lr', 'rad-st', 'rad-sj',
               'rad-lw', 'rad-dj', 'rad-ds', 'rad-dr', 'rad-dp', 'sensor-x-dim', 'sensor-y-dim', 'e-terrain',
               'n-buildings-in-chunk', 'multiprocessing', 'zone-geometry', 'surrounding-geometry', 'consider-windows',
               'consider-floors']
    for option in options:
        value = getattr(args, option.replace('-', '_'))
        if value is not None:
            print('radiation-daysim', option, str(value))
            config._parser.set('radiation-daysim', option, str(value))
    config.save()

    cea.resources.radiation_daysim.radiation_main.main(locator=locator, weather_path=args.weather_path)


def photovoltaic(args):
    import cea.utilities.dbfreader as dbfreader
    import cea.technologies.solar.photovoltaic

    if not args.latitude:
        args.latitude = _get_latitude(args.scenario)
    if not args.longitude:
        args.longitude = _get_longitude(args.scenario)

    locator = cea.inputlocator.InputLocator(args.scenario)
    if not args.weather_path:
        args.weather_path = locator.get_default_weather()
    elif args.weather_path in locator.get_weather_names():
        args.weather_path = locator.get_weather(args.weather_path)

    list_buildings_names = dbfreader.dbf_to_dataframe(locator.get_building_occupancy())['Name']

    config = cea.config.Configuration(args.scenario)
    config.weather = args.weather_path
    if args.panel_on_roof is not None:
        config.solar.panel_on_roof = args.panel_on_roof
    if args.panel_on_wall is not None:
        config.solar.panel_on_wall = args.panel_on_wall
    if args.type_PVpanel is not None:
        config.solar.type_PVpanel = args.type_PVpanel
    if args.min_radiation is not None:
        config.solar.min_radiation = args.min_radiation
    if args.date_start is not None:
        config.solar.date_start = args.date_start
    if args.solar_window_solstice is not None:
        config.solar.solar_window_solstice = args.solar_window_solstice
    config.save()

    for building in list_buildings_names:
        cea.technologies.solar.photovoltaic.calc_PV(locator=locator, latitude=args.latitude, longitude=args.longitude,
                                                    weather_path=args.weather_path, building_name=building)


def solar_collector(args):
    """Run the solar-collector script (:py:mod:`cea.technologies.solar.solar_collector`."""
    import cea.utilities.dbfreader as dbfreader
    import cea.technologies.solar.solar_collector

    if not args.latitude:
        args.latitude = _get_latitude(args.scenario)
    if not args.longitude:
        args.longitude = _get_longitude(args.scenario)

    locator = cea.inputlocator.InputLocator(args.scenario)
    if not args.weather_path:
        args.weather_path = locator.get_default_weather()
    elif args.weather_path in locator.get_weather_names():
        args.weather_path = locator.get_weather(args.weather_path)

    list_buildings_names = dbfreader.dbf_to_dataframe(locator.get_building_occupancy())['Name']

    config = cea.config.Configuration(args.scenario)
    config.weather = args.weather_path
    if args.panel_on_roof is not None:
        config.solar.panel_on_roof = args.panel_on_roof
    if args.panel_on_wall is not None:
        config.solar.panel_on_wall = args.panel_on_wall
    if args.type_SCpanel is not None:
        config.solar.type_SCpanel = args.type_SCpanel
    if args.min_radiation is not None:
        config.solar.min_radiation = args.min_radiation
    if args.date_start is not None:
        config.solar.date_start = args.date_start
    if args.solar_window_solstice is not None:
        config.solar.solar_window_solstice = args.solar_window_solstice
    config.save()

    for building in list_buildings_names:
        cea.technologies.solar.solar_collector.calc_SC(locator=locator, latitude=args.latitude,
                                                       longitude=args.longitude, weather_path=args.weather_path,
                                                       building_name=building)


def photovoltaic_thermal(args):
    """Run the photovoltaic-thermal script (:py:mod:`cea.technologies.solar.photovoltaic_thermal`."""
    import cea.utilities.dbfreader as dbfreader
    import cea.technologies.solar.photovoltaic_thermal

    if not args.latitude:
        args.latitude = _get_latitude(args.scenario)
    if not args.longitude:
        args.longitude = _get_longitude(args.scenario)

    locator = cea.inputlocator.InputLocator(args.scenario)
    if not args.weather_path:
        args.weather_path = locator.get_default_weather()
    elif args.weather_path in locator.get_weather_names():
        args.weather_path = locator.get_weather(args.weather_path)

    list_buildings_names = dbfreader.dbf_to_dataframe(locator.get_building_occupancy())['Name']

    config = cea.config.Configuration(args.scenario)
    config.weather = args.weather_path
    if args.panel_on_roof is not None:
        config.solar.panel_on_roof = args.panel_on_roof
    if args.panel_on_wall is not None:
        config.solar.panel_on_wall = args.panel_on_wall
    if args.type_PVpanel is not None:
        config.solar.type_PVpanel = args.type_PVpanel
    if args.type_SCpanel is not None:
        config.solar.type_SCpanel = args.type_SCpanel
    if args.min_radiation is not None:
        config.solar.min_radiation = args.min_radiation
    if args.date_start is not None:
        config.solar.date_start = args.date_start
    if args.solar_window_solstice is not None:
        config.solar.solar_window_solstice = args.solar_window_solstice
    config.save()

    for building in list_buildings_names:
        cea.technologies.solar.photovoltaic_thermal.calc_PVT(locator=locator, latitude=args.latitude,
                                                             longitude=args.longitude, weather_path=args.weather_path,
                                                             building_name=building)


def install_toolbox(_):
    """Install the ArcGIS toolbox and sets up .pth files to access arcpy from the cea python interpreter."""
    import cea.interfaces.arcgis.install_toolbox
    cea.interfaces.arcgis.install_toolbox.main()


def heatmaps(args):
    """Run the heatmaps tool"""
    import cea.plots.heatmaps
    import cea.inputlocator
    locator = cea.inputlocator.InputLocator(args.scenario)
    if not args.file_to_analyze:
        args.file_to_analyze = locator.get_total_demand()

    if args.list_fields:
        import pandas as pd
        df = pd.read_csv(args.file_to_analyze)
        fields = df.columns.tolist()
        fields.remove('Name')
        print('\n'.join(fields))
    else:
        cea.plots.heatmaps.heatmaps(locator=locator, analysis_fields=args.analysis_fields,
                                    file_to_analyze=args.file_to_analyze)


def test(args):
    """Run the pydoit tests (same test-suite as run by Jenkins)"""
    import cea.tests.dodo
    if args.save:
        with open(os.path.expanduser(r'~\cea_github.auth'), 'w') as f:
            f.write(args.user + '\n')
            f.write(args.token + '\n')
    try:
        cea.tests.dodo.main(user=args.user, token=args.token, reference_cases=args.reference_cases)
    except SystemExit:
        raise
    except:
        import traceback
        traceback.print_exc()


def sensitivity_demand_samples(args):
    """Run the sensitivity demand samples script"""
    import cea.analysis.sensitivity.sensitivity_demand_samples

    sampler_parameters = {}
    if args.method == 'morris':
        sampler_parameters['grid_jump'] = int(args.grid_jump)
        sampler_parameters['num_levels'] = int(args.num_levels)
    elif args.method == 'sobol':
        if args.calc_second_order == 'True':
            sampler_parameters['calc_second_order'] = True
        else:
            sampler_parameters['calc_second_order'] = False

    variable_groups = []

    if args.envelope_flag == 'True':
        variable_groups.append('ENVELOPE')
    if args.indoor_comfort_flag == 'True':
        variable_groups.append('INDOOR_COMFORT')
    if args.internal_loads_flag == 'True':
        variable_groups.append('INTERNAL_LOADS')

    cea.analysis.sensitivity.sensitivity_demand_samples.run_as_script(method=args.method, num_samples=args.num_samples,
                                                                      variable_groups=variable_groups,
                                                                      sampler_parameters=sampler_parameters,
                                                                      samples_folder=args.samples_folder)

def sensitivity_demand_simulate(args):
    """Run the sensitivity demand simulate script"""
    import numpy as np
    import cea.analysis.sensitivity.sensitivity_demand_simulate

    # save output parameters
    np.save(os.path.join(args.samples_folder, 'output_parameters.npy'), np.array(args.output_parameters))

    cea.analysis.sensitivity.sensitivity_demand_simulate.simulate_demand_batch(sample_index=args.sample_index,
                                                                               batch_size=args.num_simulations,
                                                                               samples_folder=args.samples_folder,
                                                                               scenario=args.scenario_path,
                                                                               simulation_folder=args.simulation_folder,
                                                                               weather=args.weather_path,
                                                                               output_parameters=args.output_parameters)

def sensitivity_demand_analyze(args):
    """Run the sensitivity demand analyze script"""
    import numpy as np
    import cea.analysis.sensitivity.sensitivity_demand_analyze

    cea.analysis.sensitivity.sensitivity_demand_analyze.analyze_sensitivity(samples_path=args.samples_path,
                                                                            temporal_scale=args.temporal_scale)


def extract_reference_case(args):
    """extract the reference case to a folder"""
    import zipfile
    import cea.examples
    archive = zipfile.ZipFile(os.path.join(os.path.dirname(cea.examples.__file__), 'reference-case-open.zip'))
    archive.extractall(args.to)


def compile(args):
    """compile the binary versions of some modules for faster execution"""
    import cea.utilities.compile_pyd_files
    cea.utilities.compile_pyd_files.main()


def retrofit_potential(args):
    """Run the ``cea.analysis.retrofit.retrofit_potential`` module on the scenario"""
    import cea.analysis.retrofit.retrofit_potential as retrofit_potential
    import cea.inputlocator
    locator_baseline = cea.inputlocator.InputLocator(args.scenario)
    retrofit_potential.retrofit_main(locator_baseline=locator_baseline,
                                     keep_partial_matches=args.keep_partial_matches,
                                     name_new_scenario=args.name,
                                     age_retrofit=args.retrofit_target_date,
                                     age_criteria=args.age_threshold,
                                     eui_heating_criteria=args.eui_heating_threshold,
                                     eui_hotwater_criteria=args.eui_hot_water_threshold,
                                     eui_cooling_criteria=args.eui_cooling_threshold,
                                     eui_electricity_criteria=args.eui_electricity_threshold,
                                     heating_costs_criteria=args.heating_costs_threshold,
                                     hotwater_costs_criteria=args.hot_water_costs_threshold,
                                     cooling_costs_criteria=args.cooling_costs_threshold,
                                     electricity_costs_criteria=args.electricity_costs_threshold,
                                     heating_losses_criteria=args.heating_losses_threshold,
                                     hotwater_losses_criteria=args.hot_water_losses_threshold,
                                     cooling_losses_criteria=args.cooling_losses_threshold,
                                     emissions_operation_criteria=args.emissions_operation_threshold)


def read_config(args):
    """Read a key from a section in the configuration"""
    import cea.config
    import ConfigParser
    config = cea.config.Configuration(args.scenario)
    try:
        print(config._parser.get(args.section, args.key))
    except ConfigParser.NoSectionError:
        pass
    except ConfigParser.NoOptionError:
        pass


def read_config_section(args):
    """Read all keys from a section in the configuration into a json dictionary and print that"""
    import cea.config
    import ConfigParser
    import json
    config = cea.config.Configuration(args.scenario)
    try:
        keys = config._parser.options(args.section)
        section_dict = {key: config._parser.get(args.section, key) for key in keys}
        print(json.dumps(section_dict))
    except ConfigParser.NoSectionError:
        pass
    except ConfigParser.NoOptionError:
        pass


def write_config(args):
    """write a value to a section/key in the configuration in the scenario folder"""
    import cea.config
    config = cea.config.Configuration(args.scenario)
    if not config._parser.has_section(args.section):
        config._parser.add_section(args.section)
    config._parser.set(args.section, args.key, args.value)
    config.save()


def excel_to_dbf(args):
    """Convert an Excel file (*.xls) to a DBF file (*.dbf)"""
    import cea.utilities.dbfreader
    cea.utilities.dbfreader.run_as_script(args.input_path, args.output_path)


def dbf_to_excel(args):
    """Convert a DBF file (*.dbf) to an Excel file (*.xls)"""
    import cea.utilities.dbfreader
    cea.utilities.dbfreader.run_as_script(args.input_path, args.output_path)


def _parse_boolean(s):
    """Return True or False, depending on the value of ``s`` as defined by the ConfigParser library."""
    boolean_states = {'0': False,
                      '1': True,
                      'false': False,
                      'no': False,
                      'off': False,
                      'on': True,
                      'true': True,
                      'yes': True}
    if s.lower() in boolean_states:
        return boolean_states[s.lower()]
    return False


def main():
    """Parse the arguments and run the program."""
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder', default=os.curdir)
    subparsers = parser.add_subparsers()

    demand_parser = subparsers.add_parser('demand',
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    demand_parser.add_argument('-w', '--weather', help='Path to the weather file')
    demand_parser.add_argument('--use-dynamic-infiltration-calculation', action='store_true',
                               help='Use the dynamic infiltration calculation instead of default')
    demand_parser.add_argument('--multiprocessing', action='store_true',
                               help='Use the parallel processing to speed up computation')
    demand_parser.set_defaults(func=demand)

    data_helper_parser = subparsers.add_parser('data-helper',
                                               formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    data_helper_parser.add_argument('--archetypes', help='List of archetypes process', nargs="*",
                                    default=['thermal', 'comfort', 'architecture', 'HVAC', 'internal-loads'],
                                    choices=['thermal', 'comfort', 'architecture', 'HVAC', 'internal-loads'])
    data_helper_parser.set_defaults(func=data_helper)

    emissions_parser = subparsers.add_parser('emissions',
                                             formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    emissions_parser.add_argument('--extra-files-to-create', help='List of variables to create separate files for',
                                  nargs='*',
                                  default=['Qcs', 'Qhs', 'Qcrefri', 'Eal', 'Epro', 'Eaux', 'Qww', 'Edata', 'Qcdata'],
                                  choices=['Qcs', 'Qhs', 'Qcrefri', 'Eal', 'Epro', 'Eaux', 'Qww', 'Edata', 'Qcdata'])
    emissions_parser.set_defaults(func=emissions)

    embodied_energy_parser = subparsers.add_parser('embodied-energy',
                                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    embodied_energy_parser.add_argument('--year-to-calculate', help='Year to calculate for', type=int, default=2017)
    embodied_energy_parser.set_defaults(func=embodied_energy)

    mobility_parser = subparsers.add_parser('mobility',
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    mobility_parser.set_defaults(func=mobility)

    benchmark_graphs_parser = subparsers.add_parser('benchmark-graphs',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    benchmark_graphs_parser.add_argument('--output-file', help='File (*.pdf) to store the output in', required=True)
    benchmark_graphs_parser.add_argument('--scenarios', help='List of scenarios to benchmark',
                                         nargs='+', default=['.'])
    benchmark_graphs_parser.set_defaults(func=benchmark_graphs)

    weather_files_parser = subparsers.add_parser('weather-files',
                                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    weather_files_parser.set_defaults(func=weather_files)

    weather_path_parser = subparsers.add_parser('weather-path',
                                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    weather_path_parser.add_argument('weather', metavar='ATTR',
                                     help='The name of the weather file (from the weather-files list)')
    weather_path_parser.set_defaults(func=weather_path)

    file_location_parser = subparsers.add_parser('locate',
                                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    file_location_parser.add_argument('attribute', metavar='ATTR',
                                      help='The name of the file to find, denoted by InputLocator.ATTR()')
    file_location_parser.set_defaults(func=file_location)

    demand_graph_parser = subparsers.add_parser('demand-graphs',
                                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    demand_graph_parser.add_argument('--list-fields', action='store_true', default=False,
                                     help='List the valid fields for the --analysis-fields arguments, one per line.')
    demand_graph_parser.add_argument('--analysis-fields', nargs='+', default=[],
                                     help='The list of fields to graph. See --list-fields option for valid values. Max 4.')
    demand_graph_parser.set_defaults(func=demand_graphs)

    scenario_plots_parser = subparsers.add_parser('scenario-plots',
                                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    scenario_plots_parser.add_argument('--output-file', required=True, help='The path to the output pdf file to write.')
    scenario_plots_parser.add_argument('--scenarios', required=True, nargs='+', help='The list of scenarios to plot')
    scenario_plots_parser.set_defaults(func=scenario_plots)

    latitude_parser = subparsers.add_parser('latitude',
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    latitude_parser.set_defaults(func=latitude)

    longitude_parser = subparsers.add_parser('longitude',
                                             formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    longitude_parser.set_defaults(func=longitude)

    radiation_parser = subparsers.add_parser('radiation',
                                             formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    radiation_parser.add_argument('--arcgis-db', help='The path to the ArcGIS database',
                                  default=os.path.expanduser(os.path.join('~', 'Documents', 'ArcGIS', 'Default.gdb')))
    radiation_parser.add_argument('--latitude', help='Latitude to use for calculations.', type=float)
    radiation_parser.add_argument('--longitude', help='Longitude to use for calculations.', type=float)
    radiation_parser.add_argument('--year', help='Year to use for calculations.', type=int, default=2014)
    radiation_parser.add_argument('--weather-path', help='Path to weather file.')
    radiation_parser.set_defaults(func=radiation)

    photovoltaic_parser = subparsers.add_parser('photovoltaic',
                                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    photovoltaic_parser.add_argument('--latitude', help='Latitude to use for calculations.', type=float)
    photovoltaic_parser.add_argument('--longitude', help='Longitude to use for calculations.', type=float)
    photovoltaic_parser.add_argument('--weather-path', help='Path to weather file.')
    photovoltaic_parser.add_argument('--panel-on-roof', help='flag for considering PV on roof', type=_parse_boolean)
    photovoltaic_parser.add_argument('--panel-on-wall', help='flag for considering PV on wall', type=_parse_boolean)
    photovoltaic_parser.add_argument('--worst-hour', help='first hour of sun on the solar solstice', type=int)
    photovoltaic_parser.add_argument('--type-PVpanel',
                                     help='monocrystalline, T2 is poly and T3 is amorphous. (see relates to the database of technologies)')
    photovoltaic_parser.add_argument('--min-radiation',
                                     help='points are selected with at least a minimum production of this % from the maximum in the area.',
                                     type=float)
    photovoltaic_parser.add_argument('--date-start', help='First day of the year', type=str)
    photovoltaic_parser.add_argument('--solar-window-solstice', help='desired hours of solar window on the solstice',
                                     type=int)
    photovoltaic_parser.set_defaults(func=photovoltaic)

    solar_collector_parser = subparsers.add_parser('solar-collector',
                                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    solar_collector_parser.add_argument('--latitude', help='Latitude to use for calculations.', type=float)
    solar_collector_parser.add_argument('--longitude', help='Longitude to use for calculations.', type=float)
    solar_collector_parser.add_argument('--weather-path', help='Path to weather file.')
    solar_collector_parser.add_argument('--panel-on-roof', help='flag for considering PV on roof', type=_parse_boolean)
    solar_collector_parser.add_argument('--panel-on-wall', help='flag for considering PV on wall', type=_parse_boolean)
    solar_collector_parser.add_argument('--worst-hour', help='first hour of sun on the solar solstice', type=int)
    solar_collector_parser.add_argument('--type-SCpanel',
                                        help='Solar collector panel type (SC1: flat plate collectors, SC2: evacuated tubes)')
    solar_collector_parser.add_argument('--min-radiation',
                                        help='points are selected with at least a minimum production of this % from the maximum in the area.',
                                        type=float)
    solar_collector_parser.add_argument('--date-start', help='First day of the year', type=str)
    solar_collector_parser.add_argument('--solar-window-solstice', help='desired hours of solar window on the solstice',
                                        type=int)
    solar_collector_parser.set_defaults(func=solar_collector)

    photovoltaic_thermal_parser = subparsers.add_parser('photovoltaic-thermal',
                                                        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    photovoltaic_thermal_parser.add_argument('--latitude', help='Latitude to use for calculations.', type=float)
    photovoltaic_thermal_parser.add_argument('--longitude', help='Longitude to use for calculations.', type=float)
    photovoltaic_thermal_parser.add_argument('--weather-path', help='Path to weather file.')
    photovoltaic_thermal_parser.add_argument('--panel-on-roof', help='flag for considering PV on roof',
                                             type=_parse_boolean)
    photovoltaic_thermal_parser.add_argument('--panel-on-wall', help='flag for considering PV on wall',
                                             type=_parse_boolean)
    photovoltaic_thermal_parser.add_argument('--worst-hour', help='first hour of sun on the solar solstice', type=int)
    photovoltaic_thermal_parser.add_argument('--min-radiation',
                                             help='points are selected with at least a minimum production of this % from the maximum in the area.',
                                             type=float)
    photovoltaic_thermal_parser.add_argument('--type-SCpanel',
                                             help='Solar collector panel type (SC1: flat plate collectors, SC2: evacuated tubes)')
    photovoltaic_thermal_parser.add_argument('--type-PVpanel',
                                             help='monocrystalline, T2 is poly and T3 is amorphous. (see relates to the database of technologies)')
    photovoltaic_thermal_parser.add_argument('--date-start', help='First day of the year', type=str)
    photovoltaic_thermal_parser.add_argument('--solar-window-solstice',
                                             help='desired hours of solar window on the solstice',
                                             type=int)
    photovoltaic_thermal_parser.set_defaults(func=photovoltaic_thermal)

    radiation_daysim_parser = subparsers.add_parser('radiation-daysim',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    radiation_daysim_parser.add_argument('--weather-path', help='Path to weather file.')
    radiation_daysim_parser.add_argument('--rad-n', type=int)
    radiation_daysim_parser.add_argument('--rad-af', type=str)
    radiation_daysim_parser.add_argument('--rad-ab', type=int)
    radiation_daysim_parser.add_argument('--rad-ad', type=int)
    radiation_daysim_parser.add_argument('--rad-as', type=int)
    radiation_daysim_parser.add_argument('--rad-ar', type=int)
    radiation_daysim_parser.add_argument('--rad-aa', type=float)
    radiation_daysim_parser.add_argument('--rad-lr', type=int)
    radiation_daysim_parser.add_argument('--rad-st', type=float)
    radiation_daysim_parser.add_argument('--rad-sj', type=float)
    radiation_daysim_parser.add_argument('--rad-lw', type=float)
    radiation_daysim_parser.add_argument('--rad-dj', type=float)
    radiation_daysim_parser.add_argument('--rad-ds', type=float)
    radiation_daysim_parser.add_argument('--rad-dr', type=int)
    radiation_daysim_parser.add_argument('--rad-dp', type=int)

    # GRID FOR THE SENSORS
    # use 100 (maximum) if you want only one point per surface
    radiation_daysim_parser.add_argument('--sensor-x-dim', type=int)
    radiation_daysim_parser.add_argument('--sensor-y-dim', type=int)

    # terrain parameters
    # reflection for the terrain
    radiation_daysim_parser.add_argument('--e-terrain', type=float, help='reflection for the terrain')

    # simulation parameters
    # min number of buildings for multiprocessing
    radiation_daysim_parser.add_argument('--n-buildings-in-chunk', type=int,
                                         help='min number of buildings for multiprocessing')
    # limit the number if running out of memory
    radiation_daysim_parser.add_argument('--multiprocessing', type=_parse_boolean,
                                         help='use multiprocessing to speed up calculations')

    # geometry simplification
    radiation_daysim_parser.add_argument('--zone-geometry', type=int,
                                         help='level of simplification of the zone geometry')
    radiation_daysim_parser.add_argument('--surrounding-geometry', type=int,
                                         help='level of simplification of the district geometry')
    radiation_daysim_parser.add_argument('--consider-windows', type=_parse_boolean,
                                         help='consider windows in the geometry')
    radiation_daysim_parser.add_argument('--consider-floors', type=_parse_boolean,
                                         help='consider floors in the geometry')
    radiation_daysim_parser.set_defaults(func=radiation_daysim)

    install_toolbox_parser = subparsers.add_parser('install-toolbox',
                                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    install_toolbox_parser.set_defaults(func=install_toolbox)

    heatmaps_parser = subparsers.add_parser('heatmaps',
                                            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    heatmaps_parser.add_argument('--file-to-analyze',
                                 help='The file to analyse (Either the Total_Demand.csv file or one of the emissions results files)')  # noqa
    heatmaps_parser.add_argument('--analysis-fields', nargs='+', help='The fields to analyze',
                                 default=["Qhsf_MWhyr", "Qcsf_MWhyr"])
    heatmaps_parser.add_argument('--list-fields', action='store_true', help='List available fields in the file.',
                                 default=False)
    heatmaps_parser.set_defaults(func=heatmaps)

    operation_costs_parser = subparsers.add_parser('operation-costs',
                                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    operation_costs_parser.set_defaults(func=operation_costs)

    retrofit_potential_parser = subparsers.add_parser('retrofit-potential',
                                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    retrofit_potential_parser.add_argument('--keep-partial-matches', default=False, action='store_true',
                                           help='exclude buildings that only fit some of the criteria?')
    retrofit_potential_parser.add_argument('--name', default="retrofit_HVAC", help="name for new scenario")
    retrofit_potential_parser.add_argument('--retrofit-target-date', default=2020, type=int,
                                           help="date to base retrofit age calculations on")
    retrofit_potential_parser.add_argument('--age-threshold', default=None, type=int,
                                           help="threshold age of HVAC (built / retrofitted)")
    retrofit_potential_parser.add_argument('--eui-heating-threshold', default=None, type=int,
                                           help="End use intensity threshold for heating")
    retrofit_potential_parser.add_argument('--eui-hot-water-threshold', default=None, type=int,
                                           help="End use intensity threshold for hot water")
    retrofit_potential_parser.add_argument('--eui-cooling-threshold', default=None, type=int,
                                           help="End use intensity threshold for cooling")
    retrofit_potential_parser.add_argument('--eui-electricity-threshold', default=None, type=int,
                                           help="End use intensity threshold for electricity")
    retrofit_potential_parser.add_argument('--emissions-operation-threshold', default=None, type=int,
                                           help="threshold for emissions due to operation")
    retrofit_potential_parser.add_argument('--heating-costs-threshold', default=None, type=int,
                                           help="threshold for heating costs")
    retrofit_potential_parser.add_argument('--hot-water-costs-threshold', default=None, type=int,
                                           help="threshold for hot water costs")
    retrofit_potential_parser.add_argument('--cooling-costs-threshold', default=None, type=int,
                                           help="threshold for hot water costs")
    retrofit_potential_parser.add_argument('--electricity-costs-threshold', default=None, type=int,
                                           help="threshold for electricity costs")
    retrofit_potential_parser.add_argument('--heating-losses-threshold', default=None, type=int,
                                           help="threshold for thermal losses from heating")
    retrofit_potential_parser.add_argument('--hot-water-losses-threshold', default=None, type=int,
                                           help="threshold for thermal losses from hot water")
    retrofit_potential_parser.add_argument('--cooling-losses-threshold', default=None, type=int,
                                           help="threshold for thermal losses from cooling")
    retrofit_potential_parser.set_defaults(func=retrofit_potential)

    test_parser = subparsers.add_parser('test', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    test_parser.add_argument('--user', help='GitHub user with access to cea-reference-case repository')
    test_parser.add_argument('--token', help='Personal Access Token for the GitHub user')
    test_parser.add_argument('--save', action='store_true', default=False, help='Save user and token to disk.')
    test_parser.add_argument('--reference-cases', default=['open'], nargs='+',
                             choices=['open', 'zug/baseline', 'zurich/baseline', 'zurich/masterplan', 'all'],
                             help='list of reference cases to test')
    test_parser.set_defaults(func=test)

    extract_reference_case_parser = subparsers.add_parser('extract-reference-case',
                                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    extract_reference_case_parser.add_argument('--to', help='Folder to extract the reference case to',
                                               default='.')
    extract_reference_case_parser.set_defaults(func=extract_reference_case)

    compile_parser = subparsers.add_parser('compile', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    compile_parser.set_defaults(func=compile)

    read_config_parser = subparsers.add_parser('read-config', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    read_config_parser.add_argument('--section', help='section to read from')
    read_config_parser.add_argument('--key', help='key to read')
    read_config_parser.set_defaults(func=read_config)

    read_config_section_parser = subparsers.add_parser('read-config-section',
                                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    read_config_section_parser.add_argument('--section', help='section to read from')
    read_config_section_parser.set_defaults(func=read_config_section)

    write_config_parser = subparsers.add_parser('write-config', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    write_config_parser.add_argument('--section', help='section to write to')
    write_config_parser.add_argument('--key', help='key to write')
    write_config_parser.add_argument('--value', help='value to write')
    write_config_parser.set_defaults(func=write_config)

    excel_to_dbf_parser = subparsers.add_parser('excel-to-dbf', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    excel_to_dbf_parser.add_argument('--input-path', help='Excel input file path')
    excel_to_dbf_parser.add_argument('--output-path', help='DBF output file path')
    excel_to_dbf_parser.set_defaults(func=excel_to_dbf)

    dbf_to_excel_parser = subparsers.add_parser('dbf-to-excel', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    dbf_to_excel_parser.add_argument('--input-path', help='DBF input file path')
    dbf_to_excel_parser.add_argument('--output-path', help='Excel output file path')
    dbf_to_excel_parser.set_defaults(func=dbf_to_excel)

    sensitivity_demand_samples_parser = subparsers.add_parser('sensitivity-demand-samples',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sensitivity_demand_samples_parser.add_argument('--method', help='Sampling method', required=True)
    sensitivity_demand_samples_parser.add_argument('--num-samples', help='Number of samples', type=int, required=True)
    sensitivity_demand_samples_parser.add_argument('--samples-folder', help='Folder to store samples', required=True)
    sensitivity_demand_samples_parser.add_argument('--envelope-flag', help='Flag for envelope variables', required=True)
    sensitivity_demand_samples_parser.add_argument('--indoor-comfort-flag', help='Flag for indoor comfort variables',
                                                   required=True)
    sensitivity_demand_samples_parser.add_argument('--internal-loads-flag', help='Flag for internal load variables',
                                                   required=True)
    sensitivity_demand_samples_parser.add_argument('--calc-second-order', help='Whether Sobol second order '
                                                                               'sensitivities are included',
                                                   required=False)
    sensitivity_demand_samples_parser.add_argument('--grid-jump', help='Grid jump for Morris method', required=False)
    sensitivity_demand_samples_parser.add_argument('--num-levels', help='Number of grid levels for Morris method',
                                                   required=False)
    sensitivity_demand_samples_parser.set_defaults(func=sensitivity_demand_samples)

    sensitivity_demand_simulate_parser = subparsers.add_parser('sensitivity-demand-simulate',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sensitivity_demand_simulate_parser.add_argument('--scenario-path', help='Path to scenario to analyze',
                                                    required=True)
    sensitivity_demand_simulate_parser.add_argument('--weather-path', help='Path to weather file', required=True)
    sensitivity_demand_simulate_parser.add_argument('--samples-folder', help='Folder where samples are stored',
                                                   required=True)
    sensitivity_demand_simulate_parser.add_argument('--simulation-folder', help='Folder to copy the reference case to '
                                                                               'for simulation', required=True)
    sensitivity_demand_simulate_parser.add_argument('--num-simulations', help='Number of simulations to perform',
                                                   type=int, required=True)
    sensitivity_demand_simulate_parser.add_argument('--sample-index', help='Zero-based index into the samples list to'
                                                                          'simulate', type=int, required=True)
    sensitivity_demand_simulate_parser.add_argument('--output-parameters', nargs='+',
                                                    help='Output parameters for sensitivity analysis', required=True)
    sensitivity_demand_simulate_parser.set_defaults(func=sensitivity_demand_simulate)

    sensitivity_demand_analyze_parser = subparsers.add_parser('sensitivity-demand-analyze',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    sensitivity_demand_analyze_parser.add_argument('--samples-path', help='Folder to place the output files '
                                                                            '(samples.npy, problem.pickle) in',
                                                    required=True)
    sensitivity_demand_analyze_parser.add_argument('--temporal-scale', help='Temporal scale of analysis '
                                                                            '(monthly or yearly)', required=True)
    sensitivity_demand_analyze_parser.set_defaults(func=sensitivity_demand_analyze)

    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)


if __name__ == '__main__':
    main()
