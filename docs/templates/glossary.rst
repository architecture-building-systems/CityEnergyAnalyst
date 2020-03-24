{% for lm in schemas %}
{{lm}}
{% for c in lm %}-{% endfor %}

The following file is used by these scripts: {{used_by|join(",")}}

{% if "columns" in schemas[lm]["schema"] %}
.. csv-table:: ``{{schemas[lm]["file_path"]}}``
    :header: "Variable", "Description"
    {% for col in schemas[lm]["schema"]["columns"] %}{{col}}, {{schemas[lm]["schema"]["columns"][col]["description"]}}{% endfor %}
{% else %}
{% for ws in schemas[lm]["schema"] %}

.. csv-table:: ``{{schemas[lm]["file_path"]}}`` Worksheet: ``{{ws}}``
    :header: "Variable", "Description"
    {% for col in schemas[lm]["schema"][ws]["columns"] %}{{col}}, {{schemas[lm]["schema"][ws]["columns"][col]["description"]}}{% endfor %}

{% endfor %}
{% endif %}
{% endfor %}
