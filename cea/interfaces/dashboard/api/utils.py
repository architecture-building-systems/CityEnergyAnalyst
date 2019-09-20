import cea.config
import cea.inputlocator

def deconstruct_parameters(p):
    params = {'name': p.name, 'type': p.typename,
              'value': p.get(), 'help': p.help}
    try:
        params['choices'] = p._choices
    except AttributeError:
        pass
    if p.typename == 'WeatherPathParameter':
        config = cea.config.Configuration()
        locator = cea.inputlocator.InputLocator(config.scenario)
        params['choices'] = {wn: locator.get_weather(
            wn) for wn in locator.get_weather_names()}
    return params