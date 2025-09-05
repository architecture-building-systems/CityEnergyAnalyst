import cea.config
from cea.plots.optimization_new.a_pareto_front import main as pareto_front_main

def main(config):
    return pareto_front_main(config)

if __name__ == '__main__':
    main(cea.config.Configuration())
