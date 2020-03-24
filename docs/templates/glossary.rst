{% for lm in schemas %}
{{lm}}
{% for c in lm %}-{% endfor %}

path: ``{{schemas[lm]["file_path"]}}``

The following file is used by these scripts: {{ schemas[lm]["used_by"]|map("add_backticks")|join(", ")}}

{% if "columns" in schemas[lm]["schema"] %}
.. csv-table::
    :header: "Variable", "Description"

    {% for col in schemas[lm]["schema"]["columns"] %}``{{col}}``, "{{schemas[lm]["schema"]["columns"][col]["description"]}}"
    {% endfor %}
{% else %}
{% for ws in schemas[lm]["schema"] %}

.. csv-table:: Worksheet: ``{{ws}}``
    :header: "Variable", "Description"

    {% for col in schemas[lm]["schema"][ws]["columns"] %}``{{col}}``, {{schemas[lm]["schema"][ws]["columns"][col]["description"]}}
    {% endfor %}

{% endfor %}
{% endif %}
{% endfor %}
