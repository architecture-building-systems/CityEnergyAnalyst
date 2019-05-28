{% for locator_method, underline in headers %}
{{locator_method}}
{{underline}}
.. csv-table::
    :header: "File:Sheet","Variable", "Description", "Unit", "Type", "Values"
{% for SCRIPT, LOCATOR_METHOD, FILE_NAME, VARIABLE, DESCRIPTION, UNIT, VALUES, TYPE, COLOR in tuples -%}
{% if locator_method == LOCATOR_METHOD %}
    {{FILE_NAME}},{{VARIABLE}},{{DESCRIPTION}},{{UNIT}},{{TYPE}},{{VALUES}}
{%- endif %}
{%- endfor %}
{% endfor %}