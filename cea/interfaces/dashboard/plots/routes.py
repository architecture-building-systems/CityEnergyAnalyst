import re
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import cea.inputlocator
import cea.plots
import cea.plots.categories
import cea.schemas
from cea import MissingInputDataException
from cea.interfaces.dashboard.dependencies import CEAConfig, CEAPlotCache
from cea.interfaces.dashboard.lib.logs import getCEAServerLogger

logger = getCEAServerLogger("cea-server-plots")

router = APIRouter()

dir_path = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(Path(dir_path, 'templates')))


def script_suggestions(locator_names):
    """Return a list of CeaScript objects that produce the output for each locator name"""
    import cea.scripts
    # TODO: Load plugins from config
    plugins = []
    schemas = cea.schemas.schemas(plugins=plugins)
    script_names = []
    for name in locator_names:
        script_names.extend(schemas[name]['created_by'])
    return [cea.scripts.by_name(n, plugins=plugins) for n in sorted(set(script_names))]


def load_plot(config, plot_cache, dashboard, plot_index):
    """Load a plot from the dashboard_yml"""
    dashboards = cea.plots.read_dashboards(config, plot_cache)
    dashboard = dashboards[dashboard]
    plot = dashboard.plots[plot_index]
    return plot


def render_missing_data(request, missing_files):
    return templates.TemplateResponse(
        request=request,
        name='missing_input_files.html',
        context={
            "missing_input_files": [lm(*args) for lm, args in missing_files],
            "script_suggestions": script_suggestions(lm.__name__ for lm, _ in missing_files)
        },
        # TODO: Change to 400 code after frontend is updated
        status_code=404
    )


def render_plot(request, plot_div, plot_title):
    return templates.TemplateResponse(
        request=request,
        name='plot.html',
        context={
            "plot_div": plot_div,
            "plot_title": plot_title
        }
    )


@router.get('/div/{dashboard_index}/{plot_index}', response_class=HTMLResponse)
async def route_div(config: CEAConfig, plot_cache: CEAPlotCache,
                    request: Request, dashboard_index: int, plot_index: int):
    """Return the plot as a div to be used in an AJAX call"""
    plot = load_plot(config, plot_cache, dashboard_index, plot_index)
    try:
        plot_div = plot.plot_div()
    except MissingInputDataException:
        return render_missing_data(request, plot.missing_input_files())
    except NotImplementedError as e:
        logger.error("NotImplementedError occurred: %s", e, exc_info=True)
        return HTMLResponse('<p>An internal error has occurred.</p>', 404)
    # Remove parent <div> if exists due to plotly v4
    if plot_div.startswith("<div>"):
        plot_div = plot_div[5:-5].strip()
    # BUGFIX for (#2102 - Can't add the same plot twice in a dashboard)
    # update id of div to include dashboard_index and plot_index
    if plot_div.startswith("<div id="):
        div_id = re.match('<div id="([0-9a-f-]+)"', plot_div).group(1)
        plot_div = plot_div.replace(div_id, "{div_id}-{dashboard_index}-{plot_index}".format(
            div_id=div_id, dashboard_index=dashboard_index, plot_index=plot_index))
    return HTMLResponse(plot_div, 200)


@router.get('/plot/{dashboard_index}/{plot_index}', response_class=HTMLResponse)
async def route_plot(config: CEAConfig, plot_cache: CEAPlotCache,
                     request: Request, dashboard_index: int, plot_index: int):
    plot = load_plot(config, plot_cache, dashboard_index, plot_index)
    plot_title = plot.title
    if 'scenario-name' in plot.parameters:
        plot_title += ' - {}'.format(plot.parameters['scenario-name'])
    try:
        plot_div = plot.plot_div()
    except MissingInputDataException:
        return render_missing_data(request, plot.missing_input_files())
    except NotImplementedError as e:
        logger.error("NotImplementedError occurred: %s", e, exc_info=True)
        return HTMLResponse('<p>An internal error has occurred.</p>', 404)
    return render_plot(request, plot_div, plot_title)

# @blueprint.app_errorhandler(500)
# def internal_error(error):
#     import traceback
#     error_trace = traceback.format_exc()
#     return error_trace, 500
