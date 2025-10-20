import cea.config
from cea.plots.optimization_new.a_pareto_front import main as pareto_front_main

def main(config: cea.config.Configuration):
    plot_2d, plot_3d =  pareto_front_main(config)

    return plot_2d.to_html(), plot_3d.to_html()

if __name__ == '__main__':
    main(cea.config.Configuration())
