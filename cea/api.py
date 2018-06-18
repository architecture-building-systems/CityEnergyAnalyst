"""
Provide access to the scripts exported by the City Energy Analyst.
"""

from __future__ import print_function


def register_scripts():
    import cea.interfaces.cli.cli
    import cea.config
    import importlib

    config = cea.config.Configuration()

    def script_wrapper(script_name):
        def script_runner(config=config, subprocess=False, **kwargs):
            print('running script {}'.format(script_name))
            option_list = cli_config.get('config', script_name).split()
            module_path = cli_config.get('scripts', script_name)
            script_module = importlib.import_module(module_path)
            config.restrict_to(option_list)
            for section, parameter in config.matching_parameters(option_list):
                if parameter.name in kwargs:
                    parameter.set(kwargs[parameter.name])
            if not subprocess:
                script_module.main(config)
        return script_runner

    cli_config = cea.interfaces.cli.cli.get_cli_config()
    for script_name in sorted(cli_config.options('scripts')):
        script_py_name = script_name.replace('-', '_')
        globals()[script_py_name] = script_wrapper(script_name)


register_scripts()
