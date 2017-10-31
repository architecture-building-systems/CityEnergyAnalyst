"""
scenario_plots.py

Create a list of plots for comparing multiple scenarios.
"""
import os

import matplotlib.pyplot as plt
import pandas as pd

import cea.inputlocator


def plot_scenarios(scenario_folders, output_file):
    """
    List each scenario in the folder `scenario_root` and plot demand and lca (operations, embodied) data.

    :param scenario_folders: A list of scenario folders.
    :param output_file: The filename (pdf) to save the results as.
    :return: (None)
    """
    from matplotlib.backends.backend_pdf import PdfPages

    locators = [cea.inputlocator.InputLocator(scenario) for scenario in scenario_folders]
    scenario_names = [os.path.basename(locator.scenario) for locator in locators]

    pdf = PdfPages(output_file)
    try:
        create_page_demand(locators, pdf, scenario_names)
        create_page_lca_embodied(locators, pdf, scenario_names)
        create_page_lca_operation(locators, pdf, scenario_names)
    finally:
        pdf.close()


def create_page_lca_operation(locators, pdf, scenario_names):
    """
    Create Page Three: LCA Operation
    :param locators: list of InputLocators, one for each scenario
    :param pdf:  the PdfFile to write the page to
    :param scenario_names: list of scenario names
    :return: None
    """
    try:
        fig, axes = plt.subplots(nrows=2, figsize=(8.27, 11.69))
        plt.suptitle('LCA Operation')
        plot_lca_operation(axes[0], locators, scenario_names, column='O_nre_pen_MJm2',
                           title='Non-Renewable Primary Energy', unit='MJ/m2')
        plot_lca_operation(axes[1], locators, scenario_names, column='O_ghg_kgm2', title='Greenhouse Gas', unit='kg/m2')
        fig.subplots_adjust(hspace=0.5)
        pdf.savefig()
    finally:
        plt.close()


def create_page_lca_embodied(locators, pdf, scenario_names):
    """
    Create Page Two: LCA Embodied
    :param locators: list of InputLocators, one for each scenario
    :param pdf:  the PdfFile to write the page to
    :param scenario_names: list of scenario names
    :return: None
    """
    try:
        fig, axes = plt.subplots(nrows=2, figsize=(8.27, 11.69))
        plt.suptitle('LCA Embodied')
        plot_lca_embodied(axes[0], locators, scenario_names, column='E_nre_pen_MJm2',
                          title='Non-Renewable Primary Energy', unit='MJ/m2')
        plot_lca_embodied(axes[1], locators, scenario_names, column='E_ghg_kgm2', title='Greenhouse Gas', unit='kg/m2')
        fig.subplots_adjust(hspace=0.5)
        pdf.savefig()
    finally:
        plt.close()


def create_page_demand(locators, pdf, scenario_names):
    """
    Create Page one: Demand
    :param locators: list of InputLocators, one for each scenario
    :param pdf:  the PdfFile to write the page to
    :param scenario_names: list of scenario names
    :return: None
    """
    try:
        fig, axes = plt.subplots(nrows=3, figsize=(8.27, 11.69))
        plt.suptitle('Demand')
        plot_demand(axes[0], locators, scenario_names, column='Ef_MWhyr', title='Ef')
        plot_demand(axes[1], locators, scenario_names, column='QHf_MWhyr', title='QH')
        plot_demand(axes[2], locators, scenario_names, column='QCf_MWhyr', title='QC')
        fig.subplots_adjust(hspace=0.5)
        pdf.savefig()
    finally:
        plt.close()


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


def main(config):

    print('Running scenario-plots with project = %s' % config.scenario_plots.project)
    print('Running scenario-plots with scenarios = %s' % config.scenario_plots.scenarios)
    print('Running scenario-plots with output-file = %s' % config.scenario_plots.output_file)

    scenario_folders = [os.path.join(config.scenario_plots.project, scenario) for scenario in
                        config.scenario_plots.scenarios]
    for scenario in scenario_folders:
        assert os.path.exists(scenario), "Scenario not found: %s" % scenario

    plot_scenarios(scenario_folders=scenario_folders, output_file=config.scenario_plots.output_file)

if __name__ == '__main__':
    main(cea.config.Configuration())
