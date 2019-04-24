"""
Provide access to the scripts exported by the City Energy Analyst.
"""

from __future__ import print_function


def register_scripts():
    import cea.config
    import cea.scripts
    import importlib

    config = cea.config.Configuration()

    def script_wrapper(cea_script):
        def script_runner(config=config, **kwargs):
            option_list = cea_script.parameters
            module_path = cea_script.module
            script_module = importlib.import_module(module_path)
            config.restrict_to(option_list)
            for section, parameter in config.matching_parameters(option_list):
                parameter_py_name = parameter.name.replace('-', '_')
                if parameter_py_name in kwargs:
                    parameter.set(kwargs[parameter_py_name])
            # run the script
            cea_script.print_script_configuration(config)
            script_module.main(config)
        return script_runner

    for cea_script in sorted(cea.scripts.list_scripts()):
        script_py_name = cea_script.name.replace('-', '_')
        globals()[script_py_name] = script_wrapper(cea_script)


register_scripts()
