"""
This script implements the main command-line interface to the CEA. It allows running the various scripts through a
standard interface.
"""
from __future__ import absolute_import

import os

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
    if args.weather and not os.path.exists(args.weather):
        try:
            # allow using shortcut
            import cea.inputlocator
            args.weather = cea.inputlocator.InputLocator(None).get_weather(args.weather)
        except:
            pass
    cea.demand.demand_main.run_as_script(scenario_path=args.scenario, weather_path=args.weather)


def data_helper(args):
    """Run the demand helper script with the arguments provided."""
    import cea.demand.preprocessing.properties
    cea.demand.preprocessing.properties.run_as_script(scenario_path=args.scenario,
                                                      prop_thermal_flag='thermal' in args.archetypes,
                                                      prop_architecture_flag='architecture' in args.archetypes,
                                                      prop_hvac_flag='HVAC' in args.archetypes,
                                                      prop_comfort_flag='comfort' in args.archetypes,
                                                      prop_internal_loads_flag='internal-loads' in args.archetypes)


def emissions(args):
    """Run the emissions script with the arguments provided."""
    import cea.analysis.operation
    import cea.inputlocator
    cea.analysis.operation.lca_operation(locator=cea.inputlocator.InputLocator(args.scenario),
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
    import cea.analysis.embodied
    import cea.globalvar
    gv = cea.globalvar.GlobalVariables()
    cea.analysis.embodied.lca_embodied(year_to_calculate=args.year_to_calculate,
                                       locator=cea.inputlocator.InputLocator(args.scenario), gv=gv)


def mobility(args):
    """Run the mobility script with the arguments provided."""
    import cea.analysis.mobility
    import cea.inputlocator
    cea.analysis.mobility.lca_mobility(locator=cea.inputlocator.InputLocator(args.scenario))


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
        gv = cea.globalvar.GlobalVariables()
        cea.plots.graphs_demand.graphs_demand(locator, args.analysis_fields[:4], gv)


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
    with fiona.open(cea.inputlocator.InputLocator(scenario_path).get_building_geometry()) as shp:
        lat = shp.crs['lat_0']
    return lat


def longitude(args):
    """Return the longitude of the scenario, based on the building geometry shape file."""
    lon = _get_longitude(args.scenario)
    print(lon)


def _get_longitude(scenario_path):
    import fiona
    import cea.inputlocator
    with fiona.open(cea.inputlocator.InputLocator(scenario_path).get_building_geometry()) as shp:
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
                                                                      path_arcgis_db=args.arcgis_db, latitude=args.latitude,
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

    cea.resources.radiation_daysim.radiation_main.main(locator=locator, weather_path=args.weather_path)

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


def main():
    """Parse the arguments and run the program."""
    import argparse
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder', default=os.curdir)
    subparsers = parser.add_subparsers()

    demand_parser = subparsers.add_parser('demand',
                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    demand_parser.add_argument('-w', '--weather', help='Path to the weather file')
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

    radiation_daysim_parser = subparsers.add_parser('radiation-daysim',
                                                    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    radiation_daysim_parser.add_argument('--weather-path', help='Path to weather file.')
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

    test_parser = subparsers.add_parser('test', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    test_parser.add_argument('--user', help='GitHub user with access to cea-reference-case repository')
    test_parser.add_argument('--token', help='Personal Access Token for the GitHub user')
    test_parser.add_argument('--save', action='store_true', default=False, help='Save user and token to disk.')
    test_parser.add_argument('--reference-cases', default=[], nargs='+',
                             choices=['open', 'zug/baseline', 'zurich/baseline', 'zurich/masterplan'],
                             help='list of reference cases to test')
    test_parser.set_defaults(func=test)

    extract_reference_case_parser = subparsers.add_parser('extract-reference-case',
                                                          formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    extract_reference_case_parser.add_argument('--to', help='Folder to extract the reference case to',
                                               default='.')
    extract_reference_case_parser.set_defaults(func=extract_reference_case)

    compile_parser = subparsers.add_parser('compile', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    compile_parser.set_defaults(func=compile)

    parsed_args = parser.parse_args()
    parsed_args.func(parsed_args)


if __name__ == '__main__':
    main()
