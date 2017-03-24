def configDesign(generation):
    import cea.globalvar
    import cea.inputlocator
    import csv
    import matplotlib
    import matplotlib.cm as cmx
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import os
    import re

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path)
    os.chdir(locator.get_optimization_master_results_folder())
    with open("CheckPoint" + str(generation), "rb") as csv_file:
        reader = csv.reader(csv_file)
        mydict = dict(reader)
        pop = mydict['population']
        m = re.findall(r"\[.*?\]", pop)
        for i in xrange(len(m)):
            m[i] = re.findall(r'\d+(?:\.\d+)?', m[i])
            m[i] = [float(j) for j in m[i]]
    ind = m[0]
    fig = plt.figure(figsize=(6,4))
    fig.suptitle('Design of the centralized heating hub')

    # Central heating plant
    subplot1 = fig.add_subplot(221, adjustable = 'box', aspect = 1)

    def NGorBG(value):
        if value%2 == 1:
            gas = 'NG'
        else:
            gas = 'BG'
        return gas

    labels = ['CC '+NGorBG(ind[0]), 'Boiler Base '+NGorBG(ind[2]), 'Boiler peak '+NGorBG(ind[4]), 'HP Lake', 'HP Sew', 'GHP']
    fracs = [ ind[2*i + 1] for i in range(6) ]
    colors = ['LimeGreen', 'LightSalmon', 'Crimson', 'RoyalBlue', 'MidnightBlue', 'Gray']

    zipper = [ (l,f,c) for (l,f,c) in zip(labels,fracs,colors) if f > 0.01 ]
    labelsPlot, fracsPlot, colorsPlot = map( list, zip(*zipper) )
    subplot1.pie(fracsPlot, labels = labelsPlot, colors = colorsPlot, startangle = 90, autopct='%1.1f%%', pctdistance = 0.5)

    # Solar total area
    subplot2 = fig.add_subplot(222, adjustable = 'box', aspect = 1)
    labels = ['Solar covered area', 'Uncovered area']
    fracs = [ ind[20], 1 - ind[20] ]
    colors = ['Gold', 'Gray']
    subplot2.pie(fracs, labels = labels, startangle = 90, colors = colors, autopct='%1.1f%%', pctdistance = 0.5)

    # Solar system distribution
    subplot3 = fig.add_subplot(223, adjustable = 'box', aspect = 1)
    labels = ['PV', 'PVT', 'SC']
    fracs = [ ind[15], ind[17], ind[19] ]
    colors = ['Yellow', 'Orange', 'OrangeRed']

    zipper = [ (l,f,c) for (l,f,c) in zip(labels,fracs,colors) if f > 0.01 ]
    labelsPlot, fracsPlot, colorsPlot = map( list, zip(*zipper) )
    subplot3.pie(fracsPlot, labels = labelsPlot, colors = colorsPlot, startangle = 90, autopct='%1.1f%%', pctdistance = 0.5)

    # Connected buildings
    connectedBuild = ind[21:].count(1) / len(ind[21:])
    subplot4 = fig.add_subplot(224, adjustable = 'box', aspect = 1)
    labels = ['Connected buildings', 'Disconnected buildings',]
    fracs = [ connectedBuild, 1 - connectedBuild]
    colors = ['Chocolate', 'Gray']
    subplot4.pie(fracs, labels = labels, startangle = 90, colors = colors, autopct='%1.1f%%', pctdistance = 0.5)
    plt.rcParams.update({'font.size':10})
    plt.show()

def test_graphs_optimization(generation):
    import cea.globalvar
    import cea.inputlocator
    import csv
    import matplotlib
    import matplotlib.cm as cmx
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import os
    import re

    gv = cea.globalvar.GlobalVariables()
    scenario_path = gv.scenario_reference
    locator = cea.inputlocator.InputLocator(scenario_path)
    os.chdir(locator.get_optimization_master_results_folder())
    pareto = []
    xs = []
    ys = []
    zs = []
    if generation is 'all':
        for i in xrange(gv.NGEN):
            with open("CheckPoint" + str(i + 1), "rb") as csv_file:
                reader = csv.reader(csv_file)
                mydict = dict(reader)
                objective_function = mydict['objective_function_values']
                objective_function = re.findall(r'\d+\.\d+', objective_function)
                for j in xrange(gv.initialInd):
                    pareto_intermediate = [objective_function[3 * j], objective_function[3 * j + 1],
                                           objective_function[3 * j + 2]]
                    pareto.append(pareto_intermediate)
                    xs.append(float(objective_function[3 * j]))
                    ys.append(float(objective_function[3 * j + 1]))
                    zs.append(float(objective_function[3 * j + 2]))
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(xs, ys, zs, c='r', marker='o')
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        ax.set_zlabel('Z Label')
        os.chdir(locator.get_optimization_plots_folder())
        plt.savefig("Generation" + str(generation) + "Pareto_Front_3D.png")
        plt.show()

        fig = plt.figure()
        ax = fig.add_subplot(111)
        cm = plt.get_cmap('jet')
        cNorm = matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs))
        scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
        ax.scatter(xs, ys, c=scalarMap.to_rgba(zs), s=50, alpha=0.8)
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')

        scalarMap.set_array(zs)
        fig.colorbar(scalarMap, label='Z Label')
        plt.grid(True)
        plt.rcParams['figure.figsize'] = (6, 4)
        plt.rcParams.update({'font.size': 12})
        plt.gcf().subplots_adjust(bottom=0.15)
        plt.savefig("Generation" + str(generation) + "Pareto_Front_2D.png")
        plt.show()
        plt.clf()

    else:
        with open("CheckPoint" + str(generation), "rb") as csv_file:
            pareto = []
            xs = []
            ys = []
            zs = []
            reader = csv.reader(csv_file)
            mydict = dict(reader)
            objective_function = mydict['objective_function_values']
            objective_function = re.findall(r'\d+\.\d+', objective_function)
            for i in xrange(gv.initialInd):
                pareto_intermediate = [objective_function[3*i], objective_function[3*i + 1], objective_function[3*i + 2]]
                pareto.append(pareto_intermediate)
                xs.append(float(objective_function[3*i]))
                ys.append(float(objective_function[3*i + 1]))
                zs.append(float(objective_function[3*i + 2]))

            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.scatter(xs, ys, zs, c='r', marker='o')
            ax.set_xlabel('X Label')
            ax.set_ylabel('Y Label')
            ax.set_zlabel('Z Label')
            os.chdir(locator.get_optimization_plots_folder())
            plt.savefig("Generation" + str(generation) + "Pareto_Front_3D.png")
            # plt.show()

            fig = plt.figure()
            ax = fig.add_subplot(111)
            cm = plt.get_cmap('jet')
            cNorm = matplotlib.colors.Normalize(vmin=min(zs), vmax=max(zs))
            scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=cm)
            ax.scatter(xs, ys, c=scalarMap.to_rgba(zs), s=50, alpha=0.8)
            ax.set_xlabel('X Label')
            ax.set_ylabel('Y Label')

            scalarMap.set_array(zs)
            fig.colorbar(scalarMap, label='Z Label')
            plt.grid(True)
            plt.rcParams['figure.figsize'] = (6, 4)
            plt.rcParams.update({'font.size': 12})
            plt.gcf().subplots_adjust(bottom=0.15)
            plt.savefig("Generation" + str(generation) + "Pareto_Front_2D.png")
            # plt.show()
            plt.clf()



if __name__ == '__main__':
    generation = 'all'
    # configDesign(generation)
    test_graphs_optimization(generation)
