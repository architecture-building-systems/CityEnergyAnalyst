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
            cea_script.print_script_configuration(config)
            option_list = cea_script.parameters
            module_path = cea_script.module
            script_module = importlib.import_module(module_path)
            config.restrict_to(option_list)
            for section, parameter in config.matching_parameters(option_list):
                if parameter.name in kwargs:
                    parameter.set(kwargs[parameter.name])
            # run the script
            script_module.main(config)
        script_runner.__doc__ = "hello, world"
        return script_runner

    for cea_script in sorted(cea.scripts.list_scripts()):
        script_py_name = cea_script.name.replace('-', '_')
        globals()[script_py_name] = script_wrapper(cea_script)


register_scripts()
