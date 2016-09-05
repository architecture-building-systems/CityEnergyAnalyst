"""
scenario_plots.py

Create a list of plots for comparing multiple scenarios.
"""
import os

import matplotlib.pyplot as plt
import pandas as pd

import cea.inputlocator


def plot_scenarios(scenarios, output_file):
    """
    List each scenario in the folder `scenario_root` and plot demand and lca (operations, embodied) data.

    :param scenarios: A list of scenario folders.
    :param output_file: The filename (pdf) to save the results as.
    :return: (None)
    """
    from matplotlib.backends.backend_pdf import PdfPages

    locators = [cea.inputlocator.InputLocator(scenario) for scenario in scenarios]
    scenario_names = [os.path.basename(locator.scenario_path) for locator in locators]

    pdf = PdfPages(output_file)

    # Page one: Demand
    fig, axes = plt.subplots(nrows=3, figsize=(8.27, 11.69))
    plt.suptitle('Demand')

    plot_demand(axes[0], locators, scenario_names, column='Ef_MWhyr', title='Ef')
    plot_demand(axes[1], locators, scenario_names, column='QHf_MWhyr', title='QH')
    plot_demand(axes[2], locators, scenario_names, column='QCf_MWhyr', title='QC')

    fig.subplots_adjust(hspace=0.5)
    pdf.savefig()
    plt.close()

    # Page Two: LCA Embodied
    fig, axes = plt.subplots(nrows=2, figsize=(8.27, 11.69))
    plt.suptitle('LCA Embodied')

    plot_lca_embodied(axes[0], locators, scenario_names, column='E_nre_pen_MJm2', title='Non-Renewable Primary Energy', unit='MJ/m2')
    plot_lca_embodied(axes[1], locators, scenario_names, column='E_ghg_kgm2', title='Greenhouse Gas', unit='kg/m2')

    fig.subplots_adjust(hspace=0.5)
    pdf.savefig()
    plt.close()

    # Page Three: LCA Operation
    fig, axes = plt.subplots(nrows=2, figsize=(8.27, 11.69))
    plt.suptitle('LCA Operation')

    plot_lca_operation(axes[0], locators, scenario_names, column='O_nre_pen_MJm2', title='Non-Renewable Primary Energy', unit='MJ/m2')
    plot_lca_operation(axes[1], locators, scenario_names, column='O_ghg_kgm2', title='Greenhouse Gas', unit='kg/m2')

    fig.subplots_adjust(hspace=0.5)
    pdf.savefig()
    plt.close()


    pdf.close()


def plot_demand(ax, locators, scenario_names, column, title):
    df = pd.DataFrame()
    afs = pd.DataFrame()
    for i, scenario in enumerate(scenario_names):
        scenario_data = pd.read_csv(locators[i].get_total_demand()).set_index('Name')
        df[scenario] = scenario_data[column] * 1000 / scenario_data['GFA_m2']
        afs[scenario] = scenario_data['GFA_m2']
    ax2 = ax.twinx()
    df.boxplot(ax=ax, sym='', return_type='axes')
    ax.set_title(title)
    ax.set_ylabel('Per Building [KWh/m2]')
    y = pd.DataFrame({scenario: df[scenario] * afs[scenario] / afs[scenario].sum()
                      for scenario in scenario_names}).sum().ravel()
    x = ax.get_xticks()

    axylim = ax.get_ylim()
    bottom = axylim[0] * 0.9
    top = axylim[1] * 1.1
    ax.set_ylim(bottom=bottom, top=top)
    ax2.set_ylim(bottom=bottom, top=top)

    plt.scatter(x, y, marker='D', color='g')
    ax2.set_ylabel('Per Scenario [KWh/m2]')


def plot_lca_embodied(ax, locators, scenario_names, column, title, unit):
    df = pd.DataFrame()
    afs = pd.DataFrame()
    for i, scenario in enumerate(scenario_names):
        demand_data = pd.read_csv(locators[i].get_total_demand()).set_index('Name')
        lca_data = pd.read_csv(locators[i].get_lca_embodied()).set_index('Name')
        scenario_data = lca_data.merge(demand_data)
        df[scenario] = scenario_data[column] * 1000 / scenario_data['GFA_m2']
        afs[scenario] = scenario_data['GFA_m2']
    ax2 = ax.twinx()
    df.boxplot(ax=ax, sym='', return_type='axes')
    ax.set_title(title)
    ax.set_ylabel('Per Building [%(unit)s]' % locals())
    y = pd.DataFrame({scenario: df[scenario] * afs[scenario] / afs[scenario].sum()
                      for scenario in scenario_names}).sum().ravel()
    x = ax.get_xticks()

    axylim = ax.get_ylim()
    bottom = axylim[0] * 0.9
    top = axylim[1] * 1.1
    ax.set_ylim(bottom=bottom, top=top)
    ax2.set_ylim(bottom=bottom, top=top)

    plt.scatter(x, y, marker='D', color='g')
    ax2.set_ylabel('Per Scenario [%(unit)s]' % locals())


def plot_lca_operation(ax, locators, scenario_names, column, title, unit):
    df = pd.DataFrame()
    afs = pd.DataFrame()
    for i, scenario in enumerate(scenario_names):
        demand_data = pd.read_csv(locators[i].get_total_demand()).set_index('Name')
        lca_data = pd.read_csv(locators[i].get_lca_operation()).set_index('Name')
        scenario_data = lca_data.merge(demand_data)
        df[scenario] = scenario_data[column] * 1000 / scenario_data['GFA_m2']
        afs[scenario] = scenario_data['GFA_m2']
    ax2 = ax.twinx()
    df.boxplot(ax=ax, sym='', return_type='axes')
    ax.set_title(title)
    ax.set_ylabel('Per Building [%(unit)s]' % locals())
    y = pd.DataFrame({scenario: df[scenario] * afs[scenario] / afs[scenario].sum()
                      for scenario in scenario_names}).sum().ravel()
    x = ax.get_xticks()

    axylim = ax.get_ylim()
    bottom = axylim[0] * 0.9
    top = axylim[1] * 1.1
    ax.set_ylim(bottom=bottom, top=top)
    ax2.set_ylim(bottom=bottom, top=top)

    plt.scatter(x, y, marker='D', color='g')
    ax2.set_ylabel('Per Scenario [%(unit)s]' % locals())


def test_plot_scenarios():
    output_file = os.path.expandvars(r'%TEMP%\scenario_plots.pdf')
    scenarios_root = r'c:\reference-case-zug'
    scenarios = [os.path.join(scenarios_root, scenario) for scenario in os.listdir(scenarios_root)
                 if os.path.isdir(os.path.join(scenarios_root, scenario))]
    plot_scenarios(scenarios, output_file)
    print 'plot_scenarios succeeded.'

if __name__ == '__main__':
    test_plot_scenarios()