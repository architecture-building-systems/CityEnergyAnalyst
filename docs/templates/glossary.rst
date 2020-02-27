{% for locator_method, underline, used_by in locators %}
{{locator_method}}
{{underline}}

The following file is used by scripts: {{used_by}}

{% for LOC_METH, file_name in details -%}
{% if LOC_METH == locator_method %}

.. csv-table:: **{{file_name}}**
    :header: "Variable", "Description"
{% for SCRIPT, LOCATOR_METHOD, WORKSHEET, VARIABLE, DESCRIPTION, UNIT, VALUES, TYPE, COLOR, FILE_NAME in glossary_data -%}
{% if locator_method == LOCATOR_METHOD and file_name == FILE_NAME %}
     {{VARIABLE}},{{DESCRIPTION}} - Unit: {{UNIT}}
{%- endif -%}
{% endfor %}
{% endif %}
{%- endfor %}
{% endfor %}
