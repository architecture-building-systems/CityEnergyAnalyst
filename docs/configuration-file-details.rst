.. _configuration-file-details:

Configuration File Details
==========================

Let's explore the details of how the configuration file works!

The configuration file edited by the user (``~/cea.config``) is only the tip of the iceberg, resting on a foundation
of the default configuraiton file ``default.config`` file and the class :py:class:`cea.config.Configuration`, which
reads in the default configuration file as well as the user configuration file and makes those parameters available to
the scripts. Each script is provided with an instance of :py:class:`cea.config.Configuration` called ``config``.

Each parameter is defined in a section. Each parameter has a type, which specifies the range of values allowed for that
parameter and also how to read and write them to the configuration file.

Access to parameters through the ``config`` variable happens by section. Since all section names and parameter names
in the configuration file follow the kebab-case_ naming convention, and these are not valid python identifiers, a
translation is made to the snake_case_ naming convention: All hyphens (``-``) are replaced by underscores (``_``).

.. _kebab-case: http://wiki.c2.com/?KebabCase
.. _snake_case: https://en.wikipedia.org/wiki/Snake_case


The syntax is simple::

    "config." + [section] + "." + parameter

The section name is optional for the section ``general``, so ``config.general.scenario`` refers to the same parameter as
``config.scenario``. Note that these parameters can also be set::

    config.scenario = r'C:\hoenggerberg\baseline'

If you want to persist these changes to disk, you need to explicitly save them with
:py:meth:`cea.config.Configuration.save`.

.. note:: It is a bad idea to have multiple instances of :py:class:`cea.config.Configuration`, as if one part of a
    script changes a parameter, this will not be reflected in the other instances. Each CEA script accepts a ``config``
    argument to it's ``main`` function and should only use that.

Overview
--------

.. digraph:: config

  graph [splines=ortho, nodesep=0.1, rankdir="TD"]
  node [shape="record", fontname="Arial", fontsize="8"]
  Configuration -> Section [label=" 0..*"];
  Section -> Parameter [label=" 0..*"];

  Configuration [label="{Configuration|default_config\luser_config\lsections\l|apply_command_line_args()\lsave()\l}"];
  Parameter [label="{Parameter|name\lhelp\lcategory\lsection\lconfig\l|initialize()\lget()\lset()\lencode()\ldecode()\l}"];
  Section [label="{Section|name\lconfig\lparameters\l|__getattr__()\l__setattr()__\l}"];

  {
    rank="same"; Configuration; Section; Parameter;
  }

Initialization of the config object
-----------------------------------

An instance of :py:class:`cea.config.Configuration` is created with an optional ``config_file`` parameter that specifies
the configuration file to load as the user configuration file. This defaults to ``~/cea.config``. This file is parsed
as a :py:class:`ConfigParser.SafeConfigParser`, using the default configuration as a backup for the values and stored
in the attribute ``user_config``. Another :py:class:`ConfigParser.SafeConfigParser` is created for the default
configuration and stored in the attribute ``default_config``.

Next, the ``default_config`` is used to create a dictionary of :py:class`cea.config.Section` objects and each section is
populated with a dictionary of :py:class:`cea.config.Parameter` instances. The default configuration file lists not only
each parameter, but additional keys for each parameter as well. Example::

    [general]
    scenario = C:\reference-case-open\baseline
    scenario.type = PathParameter
    scenario.help = Path to the scenario to run

Using this information, the parameter ``general:scenario`` is assigned a default value of ``C:\reference-case-open\baseline``,
is represented by a subtype of :py:class:`cea.config.Parameter`` called :py:class:`cea.config.PathParameter` and has
a help text "Path to the scenario to run" - which is stored in the ``help`` attribute of the parameter object.

Some subclasses of :py:class:`cea.config.Parameter` have additional configuration, like the `cea.config.ChoiceParameter`::

    [general]
    region = CH
    region.type = ChoiceParameter
    region.choices = CH SIN custom
    region.help = The region to use for the databases (either CH or SIN) - set to "custom" if you want to edit them

When the ``config`` instance is creating the parameters, each parameter object is given a chance to initialize itself
with a call to :py:meth:`cea.config.Parameter.initialize(parser)` with ``parser`` set to the ``default_config``.
Subclasses of ``Parameter`` can override this method to read this additional configuration.

How a value is read from the config file
----------------------------------------

When a script does something like ``config.general.weather``, the ``config.sections`` dictionary is checked for the
section named ``general`` and the ``parameters`` dictionary in that section is checked for a parameter named ``weather``.
The :py:meth:`cea.config.Parameter.get` method is called on that parameter and the result of this call is returned.

Based on the default configuration file, this is defined as::

    [general]
    weather = Zug
    weather.type = WeatherPathParameter
    weather.help = either a full path to a weather file or the name of one of the weather files shipped with the CEA

So the parameter is of type :py:class:`cea.config.WeatherPathParameter`.

Inside the :py:meth:`cea.config.Parameter.get` method, a call is made to :py:meth:`cea.config.Parameter.decode`, passing
in the value read from the user configuration file. Subclasses of ``Parameter`` specify how to encode and decode values
to the configuration file. The semantics are:

- ``decode`` takes a string from a configuration file (or from the command
  line) and returns a typed value (e.g. a ``bool`` if the parameter type is :py:class:`cea.config.BooleanParameter`).
- ``encode`` takes a typed value (e.g. a boolean value) and encodes it to a string that can be stored in the
  configuration file.

In the case of :py:class:`cea.config.WeatherPathParameter`, ``decode`` will ensure that the path to the weather file
exists and, if just the name of a weather file in the CEA weather file database is returned, resolves that to the full
path to that file. Hence, on my system, the value of ``config.weather`` is
``C:\Users\darthoma\Documents\GitHub\CityEnergyAnalyst\cea\databases\weather\Zurich.epw``.

How a value is saved to the config file
---------------------------------------

The mechanism for saving a value to the config file works similarly: :py:meth:`cea.config.Parameter.set` is called,
which in turn calls :py:meth:`cea.config.Parameter.encode` - subclasses can override this to provide type specific
behaviour.

How to create new parameter types
---------------------------------

Steps:

#. subclass :py:class:`cea.config.Parameter`
#. optional: override ``initialize`` to settings
#. optional: override ``encode`` to format the parameter value as a string
#. optional: override ``decode`` to read the parameter value from a string

Check the existing parameter types for ideas!