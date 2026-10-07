"""Which feature a `plot-*` script plots is decided by the script, not by `plots-general:context`.

`context` is one parameter shared by every plot script (and sent by the dashboard client), so
it routinely still holds the feature of whichever plot ran last. Trusting it made e.g.
`plot-lifecycle-emissions` read the `plots-solar` section and fail on a parameter the script is
not configured for.
"""

import pytest

import cea.config
import cea.scripts
from cea import CEAException
from cea.visualisation import plot_main


@pytest.fixture
def config():
    return cea.config.Configuration(cea.config.DEFAULT_CONFIG)


def plot_main_scripts():
    return [s for s in cea.scripts.list_scripts(plugins=[]) if s.module == 'cea.visualisation.plot_main']


def test_there_are_plot_main_scripts_to_check():
    assert plot_main_scripts()


@pytest.mark.parametrize('script', plot_main_scripts(), ids=lambda s: s.name)
def test_feature_is_the_scripts_own_plot_section(config, script):
    with config.temp_restrictions(script.parameters):
        feature = plot_main.get_plot_cea_feature(config)
    assert f'plots-{feature}' in script.parameters


def run_main(config, monkeypatch, script_name, context):
    """Run `plot_main.main` far enough to see which context `plot_all` is handed."""
    seen = {}

    class Stop(Exception):
        pass

    def fake_plot_all(_config, _scenario, plot_dict, **_kwargs):
        seen.update(plot_dict)
        raise Stop

    monkeypatch.setattr(plot_main, 'plot_all', fake_plot_all)
    script = cea.scripts.by_name(script_name, plugins=[])
    config.plots_general.context = context
    with config.temp_restrictions(script.parameters), pytest.raises(Stop):
        plot_main.main(config)
    return seen


def test_a_stale_solar_context_does_not_redirect_another_plot(config, monkeypatch):
    stale = {'feature': 'pv', 'period_start': 0, 'period_end': 8760, 'solar_panel_types': {'pv': 'PV1'}}
    seen = run_main(config, monkeypatch, 'plot-demand', stale)
    assert seen['feature'] == 'demand'


def test_plot_solar_keeps_the_technology_named_in_the_context(config, monkeypatch):
    context = {'feature': 'pvt', 'solar_panel_types': {'pv': 'PV1', 'sc': 'SC1'}}
    seen = run_main(config, monkeypatch, 'plot-solar', context)
    assert seen['feature'] == 'pvt'


@pytest.mark.parametrize('feature', ['solar', 'demand', None])
def test_plot_solar_without_a_technology_says_what_is_missing(config, feature):
    script = cea.scripts.by_name('plot-solar', plugins=[])
    config.plots_general.context = {'feature': feature} if feature else {}
    with config.temp_restrictions(script.parameters), pytest.raises(CEAException, match='solar technology'):
        plot_main.main(config)
