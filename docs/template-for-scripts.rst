- config.scripts
  - list of script names (keys) and the module to call (values)
- script file follows a naming convention
  - module variable ``CEA_CONFIG_SECTIONS = ['general', 'demand']`` returns a list of configuration sections that are
    used by this script
  - module level function ``main`` is called to run script
- always call the scenario "scenario_path"??
- how to add a new option to the config file?
- purposes and principals
  - scripts should be runnable from the commandline with ``cea template --parameter value``
  - scripts should be runnable from PyCharm
  - all arguments to the scripts have a default value in ``default.config``
- place path names in double quotes when used as command lines
- parameter names should be unique throughout the tempalte (create a unit test for this)
- print out parameters

.. source:: python

    """
    Each script requires a documentation block at the top describing purpose and main principles of the script.
    This block should also include references to literature where appropriate.
    """

    # a list of configuration sections read by this script
    CEA_CONFIG_SECTIONS = ['general', 'script-name']

    def main():
        pass

    if __name__ == '__main__':
        main()