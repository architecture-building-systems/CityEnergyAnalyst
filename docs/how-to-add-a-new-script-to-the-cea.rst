How to add a new script to the CEA
==================================

So you want to extend the |CEA| with a new script? This guide will get you up and running!

The main steps you need to take are:

# copy the template script and rename it
# add a section to the ``default.config`` file for any parameters your script requires
# update the ``cli.config`` file to link your script name to the module
# update the ``cli.config`` file to specify the parameters your script requires
# add an ArcGIS interface to ``cea.interfaces.arcgis.CityEnergyAnalyst.py``

Step 1: The template script
---------------------------

Step 2: Parameters in the configuration file
--------------------------------------------


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
- parameter names should be unique throughout the template (create a unit test for this)
- print out parameters

.. sourcecode:: python

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