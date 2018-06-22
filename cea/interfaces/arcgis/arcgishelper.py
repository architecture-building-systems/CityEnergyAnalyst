"""
A library module with helper functions for creating the City Energy Analyst python toolbox for ArcGIS.
"""
import os
import subprocess
import tempfile
import ConfigParser
import traceback
import cea.config
import cea.inputlocator
from cea.interfaces.arcgis.modules import arcpy

__author__ = "Daren Thomas"
__copyright__ = "Copyright 2016, Architecture and Building Systems - ETH Zurich"
__credits__ = ["Daren Thomas", "Martin Mosteiro Romero", "Jimeno A. Fonseca"]
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Daren Thomas"
__email__ = "cea@arch.ethz.ch"
__status__ = "Production"

LOCATOR = cea.inputlocator.InputLocator(None)
CONFIG = cea.config.Configuration(cea.config.DEFAULT_CONFIG)


# set up logging to help debugging
import logging
logging.basicConfig(filename=os.path.expandvars(r'%TEMP%\arcgishelper.log'),level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s')
logging.info('arcgishelper loading...')

class CeaTool(object):
    """A base class for creating tools in an ArcGIS toolbox. Basically, the user just needs to subclass this,
    specify the usual ArcGIS stuff in the __init__ method as well as set `self.cea_tool` to the corresponding
    tool name. The rest is auto-configured based on default.config and cli.config"""

    def getParameterInfo(self):
        """Return the list of arcgis Parameter objects for this tool. The general:weather parameter is treated
        specially: it is represented as two parameter_infos, weather_name and weather_path."""
        config = cea.config.Configuration()
        parameter_infos = []
        for parameter in get_cea_parameters(config, self.cea_tool):
            if parameter.name == 'weather':
                parameter_infos.extend(get_weather_parameter_info(config))
            else:
                parameter_info = get_parameter_info(parameter, config)
                parameter_info = self.override_parameter_info(parameter_info, parameter)
                if parameter_info:
                    if isinstance(parameter_info, arcpy.Parameter):
                        parameter_infos.append(parameter_info)
                    else:
                        # allow parameters that are displayed as multiple parameter_info's
                        parameter_infos.extend(parameter_info)
        return parameter_infos

    def override_parameter_info(self, parameter_info, parameter):
        """Override this method if you need to use a non-default ArcGIS parameter handling"""
        return parameter_info

    def updateParameters(self, parameters):
        on_dialog_show = not any([p.hasBeenValidated for p in parameters])
        parameters = dict_parameters(parameters)
        config = cea.config.Configuration()
        cea_parameters = {p.fqname: p for p in get_cea_parameters(config, self.cea_tool)}
        if on_dialog_show:
            # show the parameters as defined in the config file
            for parameter_name in parameters.keys():
                if parameter_name == 'weather_name':
                    if is_builtin_weather_path(config.weather):
                        parameters['weather_name'].value = get_db_weather_name(config.weather)
                    else:
                        parameters['weather_name'].value = '<custom>'
                    parameters['weather_path'].value = config.weather
                    update_weather_parameters(parameters)
                elif parameter_name == 'weather_path':
                    continue
                elif parameter_name in cea_parameters:
                    cea_parameter = cea_parameters[parameter_name]
                    builder = BUILDERS[type(cea_parameter)](cea_parameter, config)
                    builder.on_dialog_show(parameter_name, parameters)
        else:
            if 'general:scenario' in parameters:
                check_senario_exists(parameters)
            if 'weather_name' in parameters:
                update_weather_parameters(parameters)

    def execute(self, parameters, _):
        parameters = dict_parameters(parameters)
        if 'general:scenario' in parameters:
            check_senario_exists(parameters)
        kwargs = {}
        if 'weather_name' in parameters:
            kwargs['weather'] = get_weather_path_from_parameters(parameters)
        for parameter_key in parameters.keys():
            if ':' not in parameter_key:
                # skip this parameter
                continue
            section_name, parameter_name = parameter_key.split(':')
            parameter = parameters[parameter_key]

            # allow the ParameterInfoBuilder subclass to override encoding of values
            cea_parameters = {p.fqname: p for p in get_cea_parameters(CONFIG, self.cea_tool)}
            cea_parameter = cea_parameters[parameter_key]
            logging.info(cea_parameter)
            builder = BUILDERS[type(cea_parameter)](cea_parameter, CONFIG)
            kwargs[parameter_name] = builder.encode_value(cea_parameter, parameter)
        run_cli(self.cea_tool, **kwargs)


def get_cea_parameters(config, cea_tool):
    """Return a list of cea.config.Parameter objects for each cea_parameter associated with the tool."""
    cli_config = ConfigParser.SafeConfigParser()
    cli_config.read(os.path.join(os.path.dirname(__file__), '..', 'cli', 'cli.config'))
    option_list = cli_config.get('config', cea_tool).split()
    for _, cea_parameter in config.matching_parameters(option_list):
        yield cea_parameter


def add_message(msg, **kwargs):
    """Log to arcpy.AddMessage() instead of print to STDOUT"""
    if len(kwargs):
        msg %= kwargs
    arcpy.AddMessage(msg)
    log_file = os.path.join(tempfile.gettempdir(), 'cea.log')
    with open(log_file, 'a') as log:
        log.write(str(msg))


def is_db_weather(weather_path):
    """True, if the ``weather_path`` is one of the pre-installed weather files that came with the CEA"""
    weather_name = get_db_weather_name(weather_path)
    if weather_name in LOCATOR.get_weather_names():
        # could still be a custom weather file...
        db_weather_path = LOCATOR.get_weather(weather_name)
        db_weather_path = os.path.normpath(db_weather_path)
        db_weather_path = os.path.normcase(db_weather_path)

        weather_path = LOCATOR.get_weather(weather_path)
        weather_path = os.path.normpath(weather_path)
        weather_path = os.path.normcase(weather_path)

        if os.path.dirname(db_weather_path) == os.path.dirname(weather_path):
            return True
    return False


def get_db_weather_name(weather_path):
    weather_name = os.path.splitext(os.path.basename(weather_path))[0]
    return weather_name


def get_python_exe():
    """Return the path to the python interpreter that was used to install CEA"""
    try:
        with open(os.path.expanduser('~/cea_python.pth'), 'r') as f:
            python_exe = f.read().strip()
            return python_exe
    except:
        raise AssertionError("Could not find 'cea_python.pth' in home directory.")


def get_environment():
    """Return the system environment to use for the execution - this is based on the location of the python
    interpreter in ``get_python_exe``"""
    root_dir = os.path.dirname(get_python_exe())
    scripts_dir = os.path.join(root_dir, 'Scripts')
    env = os.environ.copy()
    env['PATH'] = ';'.join((root_dir, scripts_dir, os.environ['PATH']))
    return os.environ


def run_cli(script_name, **parameters):
    """Run the CLI in a subprocess without showing windows"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [get_python_exe(), '-u', '-m', 'cea.interfaces.cli.cli', script_name]
    for parameter_name, parameter_value in parameters.items():
        parameter_name = parameter_name.replace('_', '-')
        command.append('--' + parameter_name)
        command.append(str(parameter_value))
    add_message('Executing: ' + ' '.join(command))
    process = subprocess.Popen(command, startupinfo=startupinfo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=get_environment(), cwd=tempfile.gettempdir())
    while True:
        next_line = process.stdout.readline()
        if next_line == '' and process.poll() is not None:
            break
        add_message(next_line.rstrip())
    stdout, stderr = process.communicate()
    add_message(stdout)
    add_message(stderr)
    if process.returncode == cea.ConfigError.rc:
        arcpy.AddError('Tool did not run successfully: Check parameters')
    elif process.returncode != 0:
        raise Exception('Tool did not run successfully')


def parse_boolean(s):
    """Return True or False, depending on the value of ``s`` as defined by the ConfigParser library."""
    boolean_states = {'0': False,
                      '1': True,
                      'false': False,
                      'no': False,
                      'off': False,
                      'on': True,
                      'true': True,
                      'yes': True}
    if s.lower() in boolean_states:
        return boolean_states[s.lower()]
    return False


def is_builtin_weather_path(weather_path):
    """Return True, if the weather path resolves to one of the builtin weather files shipped with the CEA."""
    if weather_path is None:
        return False
    weather_path = os.path.normpath(os.path.abspath(weather_path))
    zug_path = os.path.normpath(os.path.abspath(LOCATOR.get_weather('Zug')))
    return os.path.dirname(weather_path) == os.path.dirname(zug_path)


def demand_graph_fields(scenario):
    """Lists the available fields for the demand graphs - these are fields that are present in both the
    building demand results files as well as the totals file (albeit with different units)."""
    import pandas as pd
    locator = cea.inputlocator.InputLocator(scenario)
    df_total_demand = pd.read_csv(locator.get_total_demand())
    total_fields = set(df_total_demand.columns.tolist())
    first_building = df_total_demand['Name'][0]
    df_building = pd.read_csv(locator.get_demand_results_file(first_building))
    fields = set(df_building.columns.tolist())
    fields.remove('DATE')
    fields.remove('Name')
    # remove fields in demand results files that do not have a corresponding field in the totals file
    bad_fields = set(field for field in fields if not field.split('_')[0] + "_MWhyr" in total_fields)
    fields = fields - bad_fields
    return list(fields)


def create_weather_parameters(config):
    """Create the ``weather_name`` and ``weather_path`` parameters used for choosing the weatherfile."""
    weather_name = arcpy.Parameter(
        displayName="Weather file (choose from list or enter full path to .epw file)",
        name="weather_name",
        datatype="String",
        parameterType="Required",
        direction="Input")
    weather_name.filter.list = LOCATOR.get_weather_names() + ['<custom>']
    weather_name.value = get_db_weather_name(config.weather) if is_db_weather(config.weather) else '<custom>'
    weather_path = arcpy.Parameter(
        displayName="Path to .epw file",
        name="weather_path",
        datatype="DEFile",
        parameterType="Optional",
        direction="Input")
    weather_path.filter.list = ['epw']
    weather_path.value = config.weather
    weather_path.enabled = not is_db_weather(config.weather)
    return weather_name, weather_path


def check_senario_exists(parameters):
    """Makes sure the scenario exists. Create a dictionary of the parameters at the same time"""
    scenario_parameter = parameters['general:scenario']
    scenario = scenario_parameter.valueAsText
    if scenario is None:
        config = cea.config.Configuration()
        scenario_parameter.value = config.scenario
    else:
        scenario_parameter.value = scenario


def check_radiation_exists(parameters, scenario):
    """Make sure the radiation files exist."""
    locator = cea.inputlocator.InputLocator(scenario)
    radiation_csv = locator.get_radiation()
    if not os.path.exists(radiation_csv):
        parameters['scenario'].setErrorMessage("No radiation file found - please run radiation tool first")
    if not os.path.exists(locator.get_surface_properties()):
        parameters['scenario'].setErrorMessage("No radiation data found for scenario. Run radiation script first.")


def update_weather_parameters(parameters):
    """Update the weather_name and weather_path parameters"""
    weather_name = parameters['weather_name'].value
    if weather_name == '<custom>':
        weather_path = parameters['weather_path'].valueAsText
    else:
        weather_path = LOCATOR.get_weather(weather_name)

    parameters['weather_path'].value = weather_path

    if is_builtin_weather_path(weather_path):
        parameters['weather_path'].enabled = False
        parameters['weather_name'].value = get_db_weather_name(weather_path)
    else:
        parameters['weather_path'].enabled = True
        parameters['weather_name'].value = '<custom>'


def get_weather_path_from_parameters(parameters):
    """Return the path to the weather file to use depending on wether weather_name or weather_path is set by user"""
    if parameters['weather_name'].value == '<custom>':
        return parameters['weather_path'].valueAsText
    else:
        return LOCATOR.get_weather(parameters['weather_name'].value)


def get_weather_parameter_info(config):
    """Create two arcpy Parameter objects to deal with the weather"""
    weather_name = arcpy.Parameter(
        displayName="Weather file (choose from list or enter full path to .epw file)",
        name="weather_name",
        datatype="String",
        parameterType="Required",
        direction="Input")
    weather_name.filter.list = LOCATOR.get_weather_names() + ['<custom>']
    weather_name.value = get_db_weather_name(config.weather) if is_db_weather(config.weather) else '<custom>'
    weather_path = arcpy.Parameter(
        displayName="Path to .epw file",
        name="weather_path",
        datatype="DEFile",
        parameterType="Optional",
        direction="Input")
    weather_path.filter.list = ['epw']
    weather_path.value = config.weather
    weather_path.enabled = not is_db_weather(config.weather)
    return weather_name, weather_path


def dict_parameters(parameters):
    return {p.name: p for p in parameters}


def get_parameter_info(cea_parameter, config):
    """Create an arcpy Parameter object based on the configuration in the Default-config.
    The name is set to "section_name:parameter_name" so parameters created with this function are
    easily identified (```':' in parameter.name``)"""
    builder = BUILDERS[type(cea_parameter)](cea_parameter, config)
    try:
        arcgis_parameter = builder.get_parameter_info()
        # arcgis_parameter.value = builder.get_value()
        return arcgis_parameter
    except TypeError:
        logging.info('Failed to build arcpy.Parameter from %s', cea_parameter, exc_info=True)
        raise


class ParameterInfoBuilder(object):
    """A base class for building arcpy.Parameter objects based on :py:class:`cea.config.Parameter` objects."""
    def __init__(self, cea_parameter, config):
        self.cea_parameter = cea_parameter
        self.config = config

    def get_parameter_info(self):
        parameter = arcpy.Parameter(displayName=self.cea_parameter.help,
                                    name=self.cea_parameter.fqname, datatype='String',
                                    parameterType='Required', direction='Input', multiValue=False)

        if not self.cea_parameter.category is None:
            parameter.category = self.cea_parameter.category
        return parameter

    def on_dialog_show(self, parameter_name, parameters):
        parameters[parameter_name].value = self.cea_parameter.get()

    def encode_value(self, cea_parameter, parameter):
        return cea_parameter.encode(parameter.value)


class ScalarParameterInfoBuilder(ParameterInfoBuilder):
    DATA_TYPE_MAP = {  # (arcgis data type, multivalue)
        cea.config.StringParameter: 'String',
        cea.config.BooleanParameter: 'GPBoolean',
        cea.config.RealParameter: 'GPDouble',
        cea.config.IntegerParameter: 'GPLong',
        cea.config.DateParameter: 'GPDate',
    }

    def get_parameter_info(self):
        parameter = super(ScalarParameterInfoBuilder, self).get_parameter_info()
        if hasattr(self.cea_parameter, 'nullable') and self.cea_parameter.nullable:
            parameter.datatype = 'String'
            parameter.parameterType = 'Optional'
        else:
            parameter.datatype = self.DATA_TYPE_MAP[type(self.cea_parameter)]
            parameter.parameterType = 'Required'
        return parameter

    def get_value(self):
        if hasattr(self.cea_parameter, 'nullable') and self.cea_parameter.nullable:
            return self.cea_parameter.encode(self.cea_parameter.get())
        else:
            return self.cea_parameter.get()


class StringParameterInfoBuilder(ParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(StringParameterInfoBuilder, self).get_parameter_info()
        parameter.parameterType = 'Optional'
        return parameter

    def get_value(self):
        return self.cea_parameter.encode(self.cea_parameter.get())


class PathParameterInfoBuilder(ParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(PathParameterInfoBuilder, self).get_parameter_info()
        parameter.datatype = 'DEFolder'
        if self.cea_parameter._direction == 'output':
            parameter.direction = 'Output'
        return parameter


class ChoiceParameterInfoBuilder(ParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(ChoiceParameterInfoBuilder, self).get_parameter_info()
        parameter.filter.list = self.cea_parameter._choices
        return parameter


class MultiChoiceParameterInfoBuilder(ChoiceParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(MultiChoiceParameterInfoBuilder, self).get_parameter_info()
        parameter.multiValue = True
        parameter.parameterType = 'Optional'
        return parameter

    def encode_value(self, cea_parameter, parameter):
        if parameter.valueAsText is None:
            return ''
        else:
            return cea_parameter.encode(parameter.valueAsText.split(';'))


class SubfoldersParameterInfoBuilder(ParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(SubfoldersParameterInfoBuilder, self).get_parameter_info()
        parameter.multiValue = True
        parameter.parameterType = 'Optional'
        parameter.filter.list = self.cea_parameter.get_folders()
        return parameter

    def encode_value(self, cea_parameter, parameter):
        if parameter.valueAsText is None:
            return ''
        else:
            return cea_parameter.encode(parameter.valueAsText.split(';'))


class FileParameterInfoBuilder(ParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(FileParameterInfoBuilder, self).get_parameter_info()
        parameter.datatype = 'DEFile'
        if self.cea_parameter._direction == 'input':
            parameter.filter.list = self.cea_parameter._extensions
        else:
            parameter.direction = 'Output'

        if hasattr(self.cea_parameter, 'nullable') and self.cea_parameter.nullable:
            parameter.parameterType = 'Optional'
        return parameter


class ListParameterInfoBuilder(ParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(ListParameterInfoBuilder, self).get_parameter_info()
        parameter.multiValue = True
        parameter.parameterType = 'Optional'
        return parameter

    def encode_value(self, cea_parameter, parameter):
        if parameter.valueAsText is None:
            return ''
        else:
            return cea_parameter.encode(parameter.valueAsText.split(';'))


class OptimizationIndividualParameterInfoBuilder(ParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(OptimizationIndividualParameterInfoBuilder, self).get_parameter_info()
        parameter.parameterType = 'Required'
        parameter.datatype = "String"
        parameter.enabled = False

        scenario_parameter = arcpy.Parameter(displayName="Choose scenario for %s" % self.cea_parameter.fqname,
                                             name=self.cea_parameter.fqname.replace(':', '/') + '/scenario',
                                             datatype='String',
                                             parameterType='Required', direction='Input', multiValue=False)

        generation_parameter = arcpy.Parameter(displayName="Choose generation for %s" % self.cea_parameter.fqname,
                                             name=self.cea_parameter.fqname.replace(':', '/') + '/generation',
                                             datatype='String',
                                             parameterType='Required', direction='Input', multiValue=False)

        individual_parameter = arcpy.Parameter(displayName="Choose individual for %s" % self.cea_parameter.fqname,
                                             name=self.cea_parameter.fqname.replace(':', '/') + '/individual',
                                             datatype='String',
                                             parameterType='Required', direction='Input', multiValue=False)

        return [scenario_parameter, generation_parameter, individual_parameter, parameter]

    def on_dialog_show(self, parameter_name, parameters):
        super(OptimizationIndividualParameterInfoBuilder, self).on_dialog_show(parameter_name, parameters)
        scenario_parameter = parameters[parameter_name.replace(':', '/') + '/scenario']
        generation_parameter = parameters[parameter_name.replace(':', '/') + '/generation']
        individual_parameter = parameters[parameter_name.replace(':', '/') + '/individual']

        if len(self.cea_parameter.get().split('/')) == 1:
            s = self.cea_parameter.get()
            g = '<none>'
            i = '<none>'
        else:
            s, g, i = self.cea_parameter.get().split('/')

        scenario_parameter.value = s
        scenario_parameter.filter.list = self.cea_parameter.get_folders()
        generation_parameter.value = g
        generation_parameter.filter.list = ['<none>'] + self.cea_parameter.get_generations(s)
        individual_parameter.value = i
        individual_parameter.filter.list = ['<none>'] + self.cea_parameter.get_individuals(s, g)



class OptimizationIndividualListParameterInfoBuilder(ParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(OptimizationIndividualListParameterInfoBuilder, self).get_parameter_info()
        parameter.multiValue = True
        parameter.parameterType = 'Optional'
        parameter.datatype = "GPValueTable"
        parameter.columns = [["GPString", "Scenario"], ["GPString", "Generation"], ["GPString", "Individual"]]
        parameter.filters[0].type = 'ValueType'
        parameter.filters[1].type = 'ValueType'
        parameter.filters[2].type = 'ValueType'
        filters = self.get_filters(self.cea_parameter.replace_references(self.cea_parameter._project))
        for i in range(3):
            parameter.filters[i].list = filters[i]
        return parameter

    def get_filters(self, project_path):
        scenarios = set()
        generations = set()
        individuals = set()

        for scenario in [s for s in os.listdir(project_path) if os.path.isdir(os.path.join(project_path, s))]:
            locator = cea.inputlocator.InputLocator(os.path.join(project_path, scenario))
            for individual in locator.list_optimization_all_individuals():
                s, g, i = individual.split('/')
                g = int(g)
                i = int(i[3:])
                scenarios.add(s)
                generations.add(g)
                individuals.add(i)
            scenarios.add(scenario)
        return [sorted(scenarios),
                ['<none>'] + map(str, sorted(generations)),
                ['<none>'] + ['ind%s' % i for i in sorted(individuals)]]

    def on_dialog_show(self, parameter_name, parameters):
        """Build a nested list of the values"""
        values = []
        for v in self.cea_parameter.get():
            vlist = str(v).split('/')
            if len(vlist) == 1:
                # just the scenario, no optimization path
                vlist.extend(['<none>', '<none>'])
            values.append(vlist)
        parameters[parameter_name].values = values

    def encode_value(self, cea_parameter, parameter):
        individuals = []
        for s, g, i in parameter.values:
            if g == '<none>':
                individuals.append(s)
            else:
                assert not i == '<none>', "Can't encode individuals: %s" % parameter.values
                individuals.append('%(s)s/%(g)s/%(i)s' % locals())
        return ', '.join(individuals)

class BuildingsParameterInfoBuilder(ParameterInfoBuilder):
    def get_parameter_info(self):
        parameter = super(BuildingsParameterInfoBuilder, self).get_parameter_info()
        parameter.multiValue = True
        parameter.parameterType = 'Optional'
        parameter.filter.list = list_buildings(self.cea_parameter.config.scenario)
        return parameter


def list_buildings(scenario):
    """Shell out to the CEA python and read in the output"""
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    command = [get_python_exe(), '-u', '-m', 'cea.interfaces.arcgis.list_buildings', scenario]
    try:
        buildings_string = subprocess.check_output(command, startupinfo=startupinfo)
        return [b.strip() for b in buildings_string.split(',')]
    except subprocess.CalledProcessError:
        return []


BUILDERS = {  # dict[cea.config.Parameter, ParameterInfoBuilder]
    cea.config.PathParameter: PathParameterInfoBuilder,
    cea.config.StringParameter: StringParameterInfoBuilder,
    cea.config.BooleanParameter: ScalarParameterInfoBuilder,
    cea.config.RealParameter: ScalarParameterInfoBuilder,
    cea.config.IntegerParameter: ScalarParameterInfoBuilder,
    cea.config.MultiChoiceParameter: MultiChoiceParameterInfoBuilder,
    cea.config.ChoiceParameter: ChoiceParameterInfoBuilder,
    cea.config.SubfoldersParameter: SubfoldersParameterInfoBuilder,
    cea.config.FileParameter: FileParameterInfoBuilder,
    cea.config.ListParameter: ListParameterInfoBuilder,
    cea.config.BuildingsParameter: BuildingsParameterInfoBuilder,
    cea.config.DateParameter: ScalarParameterInfoBuilder,
    cea.config.OptimizationIndividualParameter: OptimizationIndividualParameterInfoBuilder,
    cea.config.OptimizationIndividualListParameter: OptimizationIndividualListParameterInfoBuilder,
}