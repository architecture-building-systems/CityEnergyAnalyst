"""
Provide access to the scripts exported by the City Energy Analyst.
"""

import datetime
from enum import StrEnum


class ScriptStatus(StrEnum):
    """
    Enum for the status of a script.
    """
    COMPLETED = "completed"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


def register_scripts():
    import cea.config
    import cea.scripts
    import importlib

    def print_execution_time(start_time: datetime.datetime, status: ScriptStatus = ScriptStatus.COMPLETED):
        elapsed = (datetime.datetime.now() - start_time).total_seconds()

        msg = f"Script {status}. Execution time: {elapsed:.2f}s"
        print("")
        print("-" * len(msg))
        print(msg)

    def run_script(script_func, config: cea.config.Configuration):
        """Execute script"""
        t0 = datetime.datetime.now()
        try:
            output = script_func(config)
            print_execution_time(t0)
            return output
        except Exception:
            print_execution_time(t0, status=ScriptStatus.FAILED)
            raise
        except SystemExit:
            print_execution_time(t0, status=ScriptStatus.INTERRUPTED)
            raise

    def script_wrapper(cea_script):
        # defines script_runner using closures so that it's tied to a specific cea script.
        module_path = cea_script.module
        script_module = importlib.import_module(module_path)

        def script_runner(config=None, **kwargs):
            # each cea script is represented by this function - but assigned the name of the script at module
            # level. this is done when the module is read. Note that we use the LazyLoader below to only actually
            # import the module when it's accessed the first time to save startup time (scripts are often run
            # infrequently and most are not run at all during an average cea session)
            if not config:
                config = cea.config.Configuration()

            option_list = cea_script.parameters

            with config.temp_restrictions(option_list):
                for section, parameter in config.matching_parameters(option_list):
                    if parameter.py_name in kwargs:
                        parameter.set(kwargs[parameter.py_name])
                cea_script.print_script_configuration(config)
                if list(cea_script.missing_input_files(config)):
                    cea_script.print_missing_input_files(config)
                    raise cea.MissingInputDataException()
                # run the script
                output = run_script(script_module.main, config)
                return output

        if script_module.__doc__:
            script_runner.__doc__ = script_module.__doc__.strip()
        else:
            script_runner.__doc__ = 'FIXME: Add API documentation to {}'.format(module_path)
        return script_runner

    class LazyLoader(object):
        """Allow lazy-loading of cea scripts"""

        def __init__(self, cea_script):
            self._cea_script = cea_script
            self._runner = None

        def __call__(self, *args, **kwargs):
            return self._runner.__call__(*args, **kwargs)

        def __getattribute__(self, item):
            if item == "_runner" and not object.__getattribute__(self, "_runner"):
                # lazy load happens here!
                self._runner = script_wrapper(self._cea_script)

            if item in {"__call__", "_cea_script", "_runner"}:
                # handle access to some methods / attributes
                return object.__getattribute__(self, item)

            return getattr(self._runner, item)

    for cea_script in cea.scripts.list_scripts(cea.config.Configuration().plugins):
        script_py_name = cea_script.name.replace('-', '_')
        globals()[script_py_name] = LazyLoader(cea_script)


register_scripts()
