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
 * restore default values to all the parameter fields in a section. This updates the config file too.
 * @param section
 */
function restore_defaults_js(section) {
    // default_parameters maps parameter_name to {'type', 'value'}
    default_parameters = JSON.parse(backend.get_default_parameters(section));
    for (parameter_name in default_parameters) {
        write_value(section, parameter_name, default_parameters[parameter_name]);
    }

    // make sure this section is saved to the config file
    save_section_js(section);
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
        case "JsonParameter":
            value = JSON.parse($('#' + section + '-' + parameter_name).val());
            break;
        default:
            // handle the default case
            value = $('#' + section + '-' + parameter_name)[0].value;
    }
    return value;
}

function write_value(section, parameter_name, parameter_dict) {
    parameter_type = parameter_dict['type'];
    parameter_value = parameter_dict['value'];
    parameter_raw = parameter_dict['raw'];

    switch (parameter_type) {
        case "ChoiceParameter":
            $('#' + section + '-' + parameter_name)[0].value = parameter_value;
            break;
        case "WeatherPathParameter":
            $('#' + section + '-' + parameter_name)[0].value = parameter_raw;
            break;
        case "BooleanParameter":
            $('#' + section + '-' + parameter_name)[0].checked = parameter_value;
            break;
        case "PathParameter":
            $('#' + section + '-' + parameter_name)[0].value = parameter_raw;
            break;
        case "MultiChoiceParameter":
            $('#' + section + '-' + parameter_name).val(parameter_value);
            break;
        case "SubfoldersParameter":
            $('#' + section + '-' + parameter_name).val(parameter_value);
            break;
        default:
            // handle the default case
            $('#' + section + '-' + parameter_name)[0].value = parameter_raw;
    }
}