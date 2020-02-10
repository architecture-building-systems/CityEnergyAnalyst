from flask import current_app

import cea.config
import cea.inputlocator


def deconstruct_parameters(p):
    params = {'name': p.name, 'type': p.typename,
              'value': p.get(), 'help': p.help}
    if isinstance(p, cea.config.ChoiceParameter):
        params['choices'] = p._choices
    if p.typename == 'WeatherPathParameter':
        config = current_app.cea_config
        locator = cea.inputlocator.InputLocator(config.scenario)
        params['choices'] = {wn: locator.get_weather(
            wn) for wn in locator.get_weather_names()}
    elif p.typename == 'DatabasePathParameter':
        params['choices'] = p._choices
    return params