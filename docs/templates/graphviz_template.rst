:orphan:

Script Data Flow
================
This section aims to clarify the files used (inputs) or created (outputs) by each script, along with the methods used
to access this data.

TO DO: run trace for all scripts.

{% for script, underline, digraph in list_of_digraphs %}
{{script}}
{{underline}}
.. graphviz::

    {{digraph}}
{% endfor %}