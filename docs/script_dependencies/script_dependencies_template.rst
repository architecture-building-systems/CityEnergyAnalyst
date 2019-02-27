Script input and output files
=============================
This section aims to clarify the files used (inputs) or created (outputs) by each script, along with the methods used
to access this data.

TO DO: run trace for all scripts.

{% for script, underline, digraph in dependencies%}
{{script}}
{{underline}}
.. graphviz::

    {{digraph}}
{% endfor %}