CEA Scripts
===========
CEA relies on a number of scripts to perform tasks, which may share dependencies.
This section aims to clarify the databases created or used by each script, along with the methods used
to access this data.

{% for script, underline, digraph in dependencies%}
{{script}}
{{underline}}

{{digraph}}
    {% endfor %}