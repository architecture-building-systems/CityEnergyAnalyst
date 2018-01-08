$(document).ready(function() {

    $("#list-general-list").tab("show");
    
});

/**
 * Calls back to Backend.save_section after collecting the values from all the controls.
 * @param section
 */
function save_section_js(section) {
    parameters = JSON.parse(backend.get_parameters(section));
    data = {};
    for (parameter_name in parameters) {
        data[parameter_name] = read_value(section, parameter_name, parameters[parameter_name])
    }
    backend.save_section(section, JSON.stringify(data));
}

/**
 * Read out the value of the parameter as defined by the form input - this depends on the parameter_type.
 *
 * @param section
 * @param parameter_name
 * @param parameter_type
 */
function read_value(section, parameter_name, parameter_type) {
    value = null;
    switch (parameter_type) {
        case "ChoiceParameter":
            value = $('#' + section + '-' + parameter_name)[0].value;
            break;
        case "WeatherPathParameter":
            value = $('#' + section + '-' + parameter_name)[0].value;
            break;
        case "BooleanParameter":
            value = $('#' + section + '-' + parameter_name)[0].checked;
            break;
        case "PathParameter":
            value = $('#' + section + '-' + parameter_name)[0].value;
            break;
        case "MultiChoiceParameter":
            value = $('#' + section + '-' + parameter_name).val();
            break;
        case "SubfoldersParameter":
            value = $('#' + section + '-' + parameter_name).val();
            break;
        default:
            // handle the default case
            value = $('#' + section + '-' + parameter_name)[0].value;
    }
    return value;
}