"""
This script implements the main command-line interface to the CEA. It allows running the various scripts through a
standard interface.
"""
import sys


def demand(args):
    """Run the demand script with the arguments provided."""
    import cea.demand.demand_main
    cea.demand.demand_main.run_as_script(scenario_path=args.scenario, weather_path=args.weather)


def demand_helper(args):
    """Run the demand helper script with the arguments provided."""
    import cea.demand.preprocessing.properties
    cea.demand.preprocessing.properties.run_as_script(scenario_path=args.scenario)


def main(args):
    """Parse the arguments and run the program."""
    print 'main(args)', args
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--scenario', help='Path to the scenario folder')
    subparsers = parser.add_subparsers()

    demand_parser = subparsers.add_parser('demand')
    demand_parser.add_argument('-w', '--weather', help='Path to the weather file')
    demand_parser.set_defaults(func=demand)

    demand_helper_parser = subparsers.add_parser('demand-helper')
    demand_helper_parser.set_defaults(func=demand_helper)

    parsed_args = parser.parse_args(args)
    parsed_args.func(parsed_args)



if __name__ == '__main__':
    main(sys.argv[1:])
