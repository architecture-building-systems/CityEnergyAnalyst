from flask_restplus import Namespace, Resource, fields

import cea.scripts
import cea.config

api = Namespace('Tools', description='Scripts for CEA')

TOOL_DESCRIPTION_MODEL = api.model('Tool', {
    'label': fields.String(description='Name of tool'),
    'description': fields.String(description='Description of tool')
})

TOOL_LIST = api.model('ToolList', {'tools': fields.List})


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


@api.route('/')
class ToolList(Resource):
    def get(self):
        from itertools import groupby
        from collections import OrderedDict

        tools = sorted(cea.scripts.for_interface(
            'dashboard'), key=lambda t: t.category)
        result = OrderedDict()
        for category, group in groupby(tools, lambda t: t.category):
            result[category] = [
                {'name': t.name, 'label': t.label, 'description': t.description} for t in group]

        return result


@api.route('/<string:tool_name>')
class Tool(Resource):
    def get(self, tool_name):
        config = cea.config.Configuration()
        script = cea.scripts.by_name(tool_name)

        parameters = []
        categories = {}
        for _, parameter in config.matching_parameters(script.parameters):
            if parameter.category:
                if parameter.category not in categories:
                    categories[parameter.category] = []
                categories[parameter.category].append(
                    deconstruct_parameters(parameter))
            else:
                parameters.append(deconstruct_parameters(parameter))

        out = {
            'label': script.label,
            'category': script.category,
            'parameters': parameters,
            'categorical_parameters': categories,
        }

        return out


@api.route('/<string:tool_name>/default')
class ToolDefault(Resource):
    def post(self, tool_name):
        """Restore the default configuration values for the CEA"""
        config = cea.config.Configuration()
        default_config = cea.config.Configuration(
            config_file=cea.config.DEFAULT_CONFIG)

        for parameter in parameters_for_script(tool_name, config):
            if parameter.name != 'scenario':
                parameter.set(
                    default_config.sections[parameter.section.name].parameters[parameter.name].get())
        config.save()
        return 'Success'


@api.route('/<string:tool_name>/save-config')
class ToolSave(Resource):
    def post(self, tool_name):
        """Save the configuration for this tool to the configuration file"""
        config = cea.config.Configuration()
        for parameter in parameters_for_script(tool_name, config):
            payload = api.payload[parameter.name]
            print('%s: %s' % (parameter.name, payload))
            parameter.set(payload)
        config.save()
        return 'Success'


@api.route('/<string:tool_name>/save-config')
class ToolSave(Resource):
    def post(self, tool_name):
        """Save the configuration for this tool to the configuration file"""
        config = cea.config.Configuration()
        for parameter in parameters_for_script(tool_name, config):
            payload = api.payload[parameter.name]
            print('%s: %s' % (parameter.name, payload))
            parameter.set(payload)
        config.save()
        return 'Success'


def parameters_for_script(script_name, config):
    """Return a list consisting of :py:class:`cea.config.Parameter` objects for each parameter of a script"""
    import cea.scripts
    parameters = [p for _, p in config.matching_parameters(
        cea.scripts.by_name(script_name).parameters)]
    return parameters
