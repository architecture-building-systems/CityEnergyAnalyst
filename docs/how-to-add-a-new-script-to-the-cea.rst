:orphan:

How to add a new script
=======================

So you want to extend the CEA? This guide will get you up and running!

The main steps you need to take are:

#. start with a script template.
#. develop your script.
#. add your script to the ``scripts.yml`` file
#. add a section to the ``default.config`` file for any parameters your script requires


Step 1: Start with a template
------------------------------

In ``cea/examples/template.py`` you will find a template for scripts in CEA. Go ahead and copy it to a location inside the ``cea`` folder hierarchy - check other scripts for a good place to locate it. If you need to create a subfolder, make sure you add an (empty) file called ``__init__.py`` to that folder - this makes the folder a python package and is essential for referencing the script later on.

Rename the copied file to a name that describes your script as good as possible. You should now be able to run the
script in PyCharm (or by hand with ``python -m cea.your_package_name.your_script_name``) and get the following
output::

    Running template with scenario = C:\reference-case-open\baseline
    Running template with archetypes = ['comfort', 'architecture', 'HVAC', 'internal-loads']

Inside the ``main`` function of your script, there is a section of ``print`` statements. It is a good idea to update
this list to print out the parameters actually used by your script.

The ``main`` function in the template calls a function ``template``, passing in an ``InputLocator`` object and unpacking
the ``config`` parameter. We call this the "core" function of your script. You should definitely change the name of
the core function - ideally to the name of the script / module it resides in. The ``InputLocator`` object (by convention
called ``locator``) is used by nearly every single CEA script.

The other parameters are much more dependant on the requirements of your script. If you find yourself adding more
than a few parameters, consider just passing in the ``config`` variable instead, as long parameter lists in functions
can make your code hard to read.

While you're at it give it a Purpose and an Author!:

- update the module-level documentation (at the top of the script) to reflect the _what_ and the _why_ of your script, including references to
  literature
- update the documentation of the core function of your script (the one called ``template`` in the template) to reflect
  the __how__ of your script
- update the credits section (near the top of the script) - be sure to change at least the following parts:
  - ``__author__`` (add your name!)
  - ``__credits__`` (add a list of names of colaborators)
  - ``__copyright__`` (update the year of the copyright for this script)


Step 2: Develop your script
----------------------------

Each script is unique. But to fit nicely into the CEA ecosystem, pay attention to the following points:

- spend some time to come up with good names for variables and functions

  - as a general rule, don't use abbreviations other than as loop indices (they're just hard to communicate later on)

    - beginners often think using short names and abreviations is "cool" - this is probably the fault of decades and
      decades of bad examples in code. There used to be a time when it mattered, but nobody uses those languages
      anymore. It's a lot easier to read real words.

  - try to use the same names for the same thing
  - make sure the names refer to the subject domain of your script (this makes the leap between literature and your
    code easier to make for anyone trying to figure out what your script does later on)
  - use plural for names referring to lists, tuples, sets and dictionaries
  - check for spelling errors (this also counts for comments) - HINT: PyCharm has a built-in automatic spellchecker much
    like the one in MS Word. If PyCharm marks any of your code in yellow or green, try to figure out why and fix it!

- don't hardcode paths! The CEA uses the ``cea.inputlocator.InputLocator`` class to define where files are. Follow this
  convention.

  - If you do need to manually create paths, use ``os.path.join(folder, ..., filename)`` instead of concatenating strings.

- if you think you need to use ``os.chdir``, you're doing it wrong!


Step 3: add your script to the ``scripts.yml`` file
---------------------------------------------------

The ``scripts.yml`` file (located in ``cea/``) tells the ``cea`` command line program

- the name of each script in the CEA
- the module path of the script to run
- the list of parameters that the script accepts
- what interfaces (arcgis, cli, dashboard, grasshopper) the script is meant to be used with
- the category to list the script under (for arcgis and dashboard interfaces)

By adding your script to the ``scripts.yml`` file, your script becomes executable from the command line like this::

    $ cea your-script-name

And you can use parameters like this:

    $ cea your-script-name --scenario C:\reference-case-open\baseline --your-parameter 123

During development of your script, you will probably not be too interested in this feature - you will probably just be
running your script from PyCharm. Please take the time to do this anyway, since it is a *requirement for adding it to
the ArcGIS and dashboard interfaces* and other interfaces yet to come (e.g. Rhino/Grasshopper interface)

The name of your script should be the same as the module name and the core function name from
`Step 2: Develop your script`_  - except replace any underscores (``_``) with dashes (``-``).

The ``scripts.yml`` file is grouped by categories and each category contains a list of scripts in that category. The
syntax used is YAML_. The easiest way to add a new script is to copy an existing script definition.

.. _YAML: https://en.wikipedia.org/wiki/YAML

Here is an example category with a script::

    Thermal networks:

    - name: thermal-network
      label: Thermo-hydraulic network (branched)
      description: Solve the thermal hydraulic network
      interfaces: [cli, dashboard]
      module: cea.technologies.thermal_network.thermal_network_matrix
      parameters: ['general:scenario', thermal-network]

Note that whitespace is relevant in YAML - except for the newlines, I added them to make the structure easier to
eyeball. The name of the category is "Thermal networks" and it consists of a list of cea scripts. Each script starts
with a bullet point (a ``-``) and then a dictionary of script properties. These are the properties to define:

name
    The script name. This is what is used to identify the script with the ``cea`` program and the other interfaces.
    It should use dashes (``-``) instead of underscores. Note the :py:mod:`cea.api` module provides a programmatic
    was of accessing these scripts as functions with the script names replacing the dashes with underscores (``_``).

label
    A label to use in user interfaces (e.g. ArcGIS or the dashboard).

description
    A description of the tool. This should be short but also contain a relevant description of the functionality.

interfaces
    A list of interfaces the script is to be used with.

module
    The fully qualified name (fqn) of the module that implements the script. This module is assumed to have a ``main``
    function that takes one argument, a :py:class:`cea.config.Configuration` object.

parameters
    A list of parameters that your script uses

    - use the notation ``section:parameter`` to specify a specific parameter defined in the ``default.config`` file.
    - use the notation ``section`` as a shorthand to specify that your script uses all the parameters from that section
      in the ``default.config`` file.
    - by defining the parameters used by the script, interfaces such as the command line, ArcGIS and Rhino/Grasshopper
      "know" what parameters to offer the user for a script.


Step 4: Add a section to the ``default.config`` file for any parameters your script requires
--------------------------------------------------------------------------------------------

The file ``default.config`` (found in the ``cea`` folder) specifies the list of parameters the user can set for the CEA.
This file has the same sections and parameters as the ``cea.config`` file in the user's home folder, except it also
includes additional information like parameter type and a description of the parameter.

The configuration is split up into sections. The main section ``[general]`` contains parameters that are considered
global to most scripts, e.g. ``scenario``, ``weather``, ``region``, ``multiprocessing``. All other parameters reside
in a section with the same name as the script that uses them (e.g. ``[demand]``, ``[data-helper]`` etc.) with exceptions
for tools that are closely related and share parameters (e.g. ``[solar]`` for ``photovoltaic``, ``solar-collector`` and
``photovoltaic-thermal``, ``[dbf-tools]`` for ``dbf-to-excel`` and ``excel-to-dbf``).

Follow these steps to add a new parameter for your script:

- add a section to ``default.config`` with the same name as the script or locate the appropriate section
- add a parameter name: CEA parameter names follow the naming conventions of python variable names, except they use
  kebab-case_ instead of snake_case_, i.e. dashes instead of underscores.
- set the default value
- add a line specifying the type (key: ``parameter-name.type``, value: one of the ``Parameter`` subclasses from
  ``cea.config``, e.g. ``IntegerParameter``, ``RealParameter``, ``MultiChoiceParameter``, ``PathParameter`` etc.)
- add a line specifying the documentation for the parameter (key: ``parameter-name.help``, value: the text to show in
  interfaces for that parameter - future users of your tool will be grateful for good help texts!)
- (optional) add a line specifying the category of the tool (key: ``parameter-name.category``, value: the category name)
  The category is used in the ArcGIS interface to group parameters for tools with a lot of parameters.
- (optional) add a line for tool-specific properties (e.g.: ``archetypes = comfort architecture HVAC internal-loads``)


Example::

    [data-helper]
    archetypes = comfort architecture HVAC internal-loads
    archetypes.type = MultiChoiceParameter
    archetypes.choices = comfort architecture HVAC internal-loads
    archetypes.help = List of archetypes to process


.. _kebab-case: http://wiki.c2.com/?KebabCase
.. _snake_case: https://en.wikipedia.org/wiki/Snake_case

Step 5: Add an ArcGIS interface (optional)
------------------------------------------

In general, all you need to do to add an ArcGIS interface for your script is to list 'arcgis' as one of the interfaces
in the ``scripts.yml`` file. The module :py:mod:`cea.interfaces.arcgis.CityEnergyAnalyst` creates subclasses of
:py:class:`cea.interfaces.arcgis.arcgishelper.CeaTool` for each such script.

Should you want to modify the behavior, you can overwrite that definition simply by adding your own implementation of
that class. To do so, create a class with the same name as your script (the ``name`` property) by removing the dashes,
appending "Tool" and uppercasing the first letter of each word. Example: ``multi-criteria-analysis`` would become
``MultiCriteriaAnalysisTool`` and you would define the class like this::

    class MultiCriteriaAnalysisTool(CeaTool):
        def __init__(self):
            self.cea_tool = 'multi-criteria-analysis'
            self.label = 'Multicriteria analysis'
            self.description = 'Multicriteria analysis'
            self.category = 'Analysis'
            self.canRunInBackground = False


The tools DemandTool and RadiationDaysimTool are implemented in this manner and can be used as examples.

.. note:: You don't need to add your tool to the ``Toolbox.tools`` variable as you would normally need to in an
    ArcGIS python toolbox - the :py:class`cea.interfaces.arcgis.CityEnergyAnalyst.Toolbox` class already implements
    code to find all subclasses of :py:class`cea.interfaces.arcgis.arcgishelper.CeaTool` defined in the same file.