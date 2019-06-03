{% for locator_method, underline, used_by in headers -%}
{{locator_method}}
{{underline}}
The following file is used by scripts: {{used_by}}
{%- for LOC_METH, file_name in details -%}
{%- if LOC_METH == locator_method %}
.. csv-table:: **{{file_name}}**
    :header: "Variable", "Description", "Unit", "Type", "Values"
    :widths: 10,40,6,6,10
{%- endif %}
{%- for SCRIPT, LOCATOR_METHOD, FILE_NAME, VARIABLE, DESCRIPTION, UNIT, VALUES, TYPE, COLOR in tuples -%}
{% if locator_method == LOCATOR_METHOD and file_name == FILE_NAME %}
     {{VARIABLE}},{{DESCRIPTION}},{{UNIT}},{{TYPE}},{{VALUES}}
{%- endif -%}
{% endfor %}
{%- endfor %}
{% endfor %}