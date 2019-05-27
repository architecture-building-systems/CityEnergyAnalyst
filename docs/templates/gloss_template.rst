{% for locator_method, underline in headers %}
{{locator_method}}
{{underline}}
.. csv-table::
    :header: "Variable", "Description", "Unit", "Values", "Type"
{% for SCRIPT, LOCATOR_METHOD, FILE_NAME, VARIABLE, DESCRIPTION, UNIT, VALUES, TYPE, COLOR in tuples -%}
{% if locator_method == LOCATOR_METHOD %}
    {{VARIABLE}},{{DESCRIPTION}},{{UNIT}},{{VALUES}},{{TYPE}}
{% endif %}
{%- endfor %}
{% endfor %}