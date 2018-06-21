import os
import pandas as pd
import cea.config
import cea.inputlocator


def list_individuals(project_path):
    for scenario in [s for s in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, s))]:
        yield scenario
        locator = cea.inputlocator.InputLocator(os.path.join(project_path, scenario))
        all_individuals_csv = locator.get_optimization_all_individuals()
        if (os.path.exists(all_individuals_csv)):
            all_individuals_df = pd.read_csv(all_individuals_csv)[['generation', 'individual']]
            for _, row in all_individuals_df.iterrows():
                generation = row.generation
                individual = row.individual
                yield '%(scenario)s/%(generation)i/%(individual)i' % locals()

def main(config):
    """Print out all the individuals in scenario comparison syntax"""
    for individual in list_individuals(config.plots_scenario_comparisons.project):
        print(individual)

if __name__ == '__main__':
    main(cea.config.Configuration())