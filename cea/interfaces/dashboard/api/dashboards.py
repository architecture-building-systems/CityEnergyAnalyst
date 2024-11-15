import hashlib
from typing import Dict, Any

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool

import cea.config
import cea.plots
from .utils import deconstruct_parameters
from cea.interfaces.dashboard.dependencies import CEAConfig, CEAPlotCache

router = APIRouter()

LAYOUTS = ['row', 'grid']
CATEGORIES = None


def get_categories(plugins):
    global CATEGORIES
    if not CATEGORIES:
        CATEGORIES = {c.name: {'label': c.label, 'plots': [{'id': p.id(), 'name': p.name} for p in c.plots]}
                      for c in cea.plots.categories.list_categories(plugins=plugins)}
    return CATEGORIES


def dashboard_to_dict(dashboard):
    out = dashboard.to_dict()
    for i, plot in enumerate(out['plots']):
        if plot['plot'] != 'empty':
            plot['hash'] = hashlib.md5(repr(sorted(plot.items())).encode("utf-8")).hexdigest()
            plot['title'] = dashboard.plots[i].title
    return out


def get_parameters_from_plot(config, plot, scenario_name=None):
    parameters = []
    # Make sure to set scenario name to config first
    if 'scenario-name' in plot.expected_parameters:
        if scenario_name is not None:
            config.scenario_name = scenario_name
        elif 'scenario-name' in plot.parameters:
            config.scenario_name = plot.parameters['scenario-name']

    for pname, fqname in sorted(plot.expected_parameters.items(), key=lambda x: x[1]):
        parameter = config.get_parameter(fqname)
        if pname in plot.parameters and pname != 'scenario-name':
            try:
                parameter.set(plot.parameters[pname])
            # FIXME: Use a custom exception instead
            except AssertionError as e:
                if isinstance(parameter, cea.config.MultiChoiceParameter):
                    parameter.set([])
                print(e)
        parameters.append(deconstruct_parameters(parameter))
    return parameters


def get_parameters_from_plot_class(config, plot_class, scenario_name=None):
    parameters = []
    # Make sure to set scenario name to config first
    if 'scenario-name' in plot_class.expected_parameters and scenario_name is not None:
        config.scenario_name = scenario_name

    for pname, fqname in sorted(plot_class.expected_parameters.items(), key=lambda x: x[1]):
        parameter = config.get_parameter(fqname)
        parameters.append(deconstruct_parameters(parameter))
    return parameters


@router.get('/')
async def get_dashboards(config: CEAConfig, plot_cache: CEAPlotCache):
    """
    Get list of Dashboards
    """
    dashboards = await run_in_threadpool(lambda: cea.plots.read_dashboards(config, plot_cache))

    out = []
    for d in dashboards:
        out.append(dashboard_to_dict(d))

    return out


@router.post('/')
async def create_dashboard(config: CEAConfig, plot_cache: CEAPlotCache, payload: Dict[str, Any], ):
    """
    Create Dashboard
    """
    form = payload

    if 'grid' in form['layout']:
        types = [[2] + [1] * 4, [1] * 6, [1] * 3 + [3], [2, 1] * 2]
        grid_width = types[int(form['layout'].split('-')[-1]) - 1]
        dashboard_index = cea.plots.new_dashboard(config, plot_cache, form['name'], 'grid',
                                                  grid_width=grid_width)
    else:
        dashboard_index = cea.plots.new_dashboard(config, plot_cache, form['name'], form['layout'])

    return {'new_dashboard_index': dashboard_index}


@router.get('/plot-categories')
async def get_plot_categories(config: CEAConfig):
    return get_categories(config.plugins)


@router.get('/plot-categories/{category_name}/plots/{plot_id}/parameters')
async def get_plot_category_parameters(config: CEAConfig, category_name: str, plot_id: str, scenario: str = None):
    plot_class = cea.plots.categories.load_plot_by_id(category_name, plot_id, config.plugins)
    return get_parameters_from_plot_class(config, plot_class, scenario)


@router.post('/duplicate')
async def duplicate_dashboard(config: CEAConfig, plot_cache: CEAPlotCache, payload: Dict[str, Any]):
    form = payload
    dashboard_index = cea.plots.duplicate_dashboard(config, plot_cache, form['name'], form['dashboard_index'])

    return {'new_dashboard_index': dashboard_index}


@router.get('/{dashboard_index}')
async def get_dashboard(config: CEAConfig, plot_cache: CEAPlotCache, dashboard_index: int):
    """
    Get Dashboard
    """
    dashboards = await run_in_threadpool(lambda: cea.plots.read_dashboards(config, plot_cache))

    return dashboard_to_dict(dashboards[dashboard_index])


@router.delete('/{dashboard_index}')
async def delete_dashboard(config: CEAConfig, dashboard_index: int):
    """
    Delete Dashboard
    """
    cea.plots.delete_dashboard(config, dashboard_index)

    return {'message': 'deleted dashboard'}


@router.patch('/{dashboard_index}')
async def update_dashboard(config: CEAConfig, plot_cache: CEAPlotCache, dashboard_index: int, payload: Dict[str, Any]):
    """
    Update Dashboard properties
    """
    form = payload
    dashboards = await run_in_threadpool(lambda: cea.plots.read_dashboards(config, plot_cache))

    dashboard = dashboards[dashboard_index]
    dashboard.set_scenario(form['scenario'])
    cea.plots.write_dashboards(config, dashboards)

    return {'new_dashboard_index': dashboard_index}


@router.get('/{dashboard_index}/plots/{plot_index}')
async def get_plot(config: CEAConfig, plot_cache: CEAPlotCache, dashboard_index: int, plot_index: int):
    """
    Get Dashboard Plot
    """
    dashboards = await run_in_threadpool(lambda: cea.plots.read_dashboards(config, plot_cache))

    return dashboard_to_dict(dashboards[dashboard_index])['plots'][plot_index]


@router.put('/{dashboard_index}/plots/{plot_index}')
async def create_plot_at_index(config: CEAConfig, plot_cache: CEAPlotCache,
                               dashboard_index: int, plot_index: int, payload: Dict[str, Any]):
    """
    Create/Replace a new Plot at specified index
    """
    form = payload

    # avoid overwriting original config.scenario for plot
    temp_config = cea.config.Configuration()
    dashboards = cea.plots.read_dashboards(config, plot_cache)
    dashboard = dashboards[dashboard_index]

    if 'category' in form and 'plot_id' in form:
        dashboard.add_plot(form['category'], form['plot_id'], plugins=config.plugins, index=plot_index)

    # Set parameters if included in form and plot exists
    if 'parameters' in form:
        plot = dashboard.plots[plot_index]
        plot_parameters = plot.expected_parameters.items()
        if 'scenario-name' in plot.expected_parameters:
            temp_config.scenario_name = form['parameters']['scenario-name']
        print('expected_parameters: {}'.format(plot_parameters))
        for pname, fqname in plot_parameters:
            parameter = temp_config.get_parameter(fqname)
            if isinstance(parameter, cea.config.MultiChoiceParameter):
                plot.parameters[pname] = parameter.decode(','.join(form['parameters'][pname]))
            else:
                plot.parameters[pname] = parameter.decode(form['parameters'][pname])

    cea.plots.write_dashboards(config, dashboards)

    return dashboard_to_dict(dashboards[dashboard_index])['plots'][plot_index]


@router.delete('/{dashboard_index}/plots/{plot_index}')
async def delete_plot(config: CEAConfig, plot_cache: CEAPlotCache,  dashboard_index: int, plot_index: int):
    """
    Delete Plot from Dashboard
    """
    dashboards = await run_in_threadpool(lambda: cea.plots.read_dashboards(config, plot_cache))

    dashboard = dashboards[dashboard_index]
    dashboard.remove_plot(plot_index)
    cea.plots.write_dashboards(config, dashboards)

    return dashboard_to_dict(dashboard)


@router.get('/{dashboard_index}/plots/{plot_index}/parameters')
async def get_plot_parameters(config: CEAConfig, plot_cache: CEAPlotCache,
                              dashboard_index: int, plot_index: int, scenario: str = None):
    """
    Get Plot Form Parameters of Plot in Dashboard
    """
    dashboards = await run_in_threadpool(lambda: cea.plots.read_dashboards(config, plot_cache))

    dashboard = dashboards[dashboard_index]
    plot = dashboard.plots[plot_index]

    return get_parameters_from_plot(config, plot, scenario)


@router.get('/{dashboard_index}/plots/{plot_index}/input-files')
async def get_plot_input_files(config: CEAConfig, plot_cache: CEAPlotCache, dashboard_index: int, plot_index: int):
    """
    Get input files of Plot
    """
    dashboards = await run_in_threadpool(lambda: cea.plots.read_dashboards(config, plot_cache))

    dashboard = dashboards[dashboard_index]
    plot = dashboard.plots[plot_index]

    data_path = plot.plot_data_to_file()
    input_paths = [locator_method(*args) for locator_method, args in plot.input_files]

    return {'inputs': input_paths, 'data': [data_path] if data_path else []}
