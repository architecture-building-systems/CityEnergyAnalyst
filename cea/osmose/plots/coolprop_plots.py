import CoolProp
from CoolProp.Plots import PropertyPlot

## T-s diagram ##

def main():
    fluid_list = ['CO2','R134a','R717','R1234yf']
    fluid_name = 'R717'
    graph_type = 'TS'
    for fluid_name in fluid_list:
        plot_fluid(graph_type, fluid_name)
    return


def plot_fluid(graph_type, fluid_name):
    plot = PropertyPlot('HEOS::' + fluid_name, graph_type, unit_system='EUR', tp_limits='ORC')
    plot.calc_isolines(CoolProp.iQ, num=11)
    # plot.calc_isolines(CoolProp.iP, iso_range=[1,10], num=10, rounding=True)
    plot.draw()
    plot.isolines.clear()
    # iso-baric lines
    plot.props[CoolProp.iP]['color'] = 'green'
    plot.props[CoolProp.iP]['lw'] = '0.5'
    tp_limits = plot.get_Tp_limits()
    p_limits = tp_limits[2:4]
    plot.calc_isolines(CoolProp.iP, iso_range=[5, 160], num=10, rounding=False)  # numbers of isolines
    axis = plot.get_axis_limits()
    plot.set_axis_limits(axis[0:2] + [0, 150])
    plot.title(r'$T,s$ Graph for ' + fluid_name)
    # plot.show()
    plot.savefig('E:\\ipese_new\\osmose_mk\\results\\HCS_base_hps\\' + fluid_name + '_' + graph_type + '.png')


if __name__ == '__main__':
    main()
