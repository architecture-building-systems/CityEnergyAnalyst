What are the CEA Scripts?
=========================
CEA relies on a number of scripts which may share dependencies.
This section aims to clarify the files created or used by each script, along with the methods used
to access this data. Scripts can be run via the command line interface (cli) by calling: ``cea script-name``.

The following diagrams are used to visualise the input and output files used by each script, along with the method of access:

.. graphviz::

    digraph example {
        rankdir="LR";
        graph [overlap = false, fontname="arial"];
        "script-name"[style=filled, fillcolor=turquoise3, shape=note, fontsize=20, fontname="arial"]

        node [shape=box, style=filled, color=white, fontsize= 15, fontname=arial, fixedsize=true, width=1.6];
        edge [fontname=arial, fontsize = 15];
        "input_data.file" -> "script-name"[label="inputlocator_method_1"]
        "script-name" -> "output_data.file"[label="inputlocator_method_2"]

            subgraph cluster_0 {
            style=filled;
            shape=box;
            fillcolor=azure2;
            fontsize=20;
            label="relative/path/of/input_data.file";
        "input_data.file"
        }
        subgraph cluster_1 {
            style=filled;
            shape=box;
            fillcolor=azure2;
            fontsize=20;
            label="relative/path/of/output_data.file";
        "output_data.file"
        }
        }

Script Name
^^^^^^^^^^^


Relative File Path
^^^^^^^^^^^^^^^^^^
Config



Inputlocator Method
^^^^^^^^^^^^^^^^^^^
All script requests for reading or writing data are routed through the inputlocator's specific 'get_methods', which join the
current working path with that of the desired input/output file.

Core
----
Currently, the CEA operates using a core set of scripts whose outputs are necessary for the function of
other scripts. They should be run in the following order:

    #.   ``data-helper`` : creates secondary input databases from the default within cea/databases
         (only needs to be run once for each scenario).
    #.   ``radiation-daysim`` : creates the solar insolation data for each building using daysim.
    #.   ``demand`` : creates a demand approximation for each building.

.. graphviz::

    digraph trace_inputlocator {
        rankdir="LR";
        node [shape=box, style=filled, fillcolor=peachpuff]
        graph [overlap = false];
        "data-helper"[style=filled, fillcolor=darkorange];
        "demand"[style=filled, fillcolor=darkorange];
        "radiation-daysim"[style=filled, fillcolor=darkorange];
        "databases/CH/archetypes" -> "data-helper"
        "inputs/building-properties" -> "data-helper"
        "databases/CH/archetypes" -> "demand"
        "inputs/building-properties" -> "demand"
        "databases/CH/systems" -> "demand"
        "databases/CH/lifecycle" -> "demand"
        "outputs/data/solar-radiation" -> "demand"
        "databases/CH/systems" -> "demand"
        "../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather" -> "demand"
        "inputs/building-geometry" -> "demand"
        "inputs/building-properties" -> "radiation-daysim"
        "inputs/building-geometry" -> "radiation-daysim"
        "databases/CH/systems" -> "radiation-daysim"
        "inputs/topography" -> "radiation-daysim"
        "../../users/jack/documents/github/cityenergyanalyst/cea/databases/weather" -> "radiation-daysim"
        "inputs/building-geometry" -> "radiation-daysim"
        "data-helper" -> "inputs/building-properties"
        "demand" -> "outputs/data/demand"
        "radiation-daysim" -> "outputs/data/solar-radiation"
        }

{% for script, underline, digraph in dependencies%}
{{script}}
{{underline}}
.. graphviz::

    {{digraph}}
{% endfor %}