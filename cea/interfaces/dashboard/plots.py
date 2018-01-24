"""
Describes the plots known to the system.
"""
import cea.plots.demand.load_curve

class Plot(object):
    def __init__(self, name, label, producer, category):
        self.name = name
        self.label = label
        self.producer = producer
        self.category = category


plots = {
    'load_curve': Plot('load_curve', 'Load curve', cea.plots.demand.load_curve.plot_div, 'buildings')
}

def list_plots():
    return plots.values()

def get_plot(plot_name):
    return plots[plot_name]