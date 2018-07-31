import os
import pandas as pd
import cea.config
import cea.inputlocator


def list_individuals(project_path):
    for scenario in [s for s in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, s))]:
        yield scenario
        locator = cea.inputlocator.InputLocator(os.path.join(project_path, scenario))
        for individual in locator.list_optimization_all_individuals():
            yield individual

def main(config):
    """Print out all the individuals in scenario comparison syntax"""
    for individual in list_individuals(config.plots_scenario_comparisons.project):
        print(individual)

if __name__ == '__main__':
    main(cea.config.Configuration())