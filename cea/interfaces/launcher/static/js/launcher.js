$(document).ready(function() {

    $("#list-data-helper").tab("show");
    
});

/**
 * Run the current script with the parameters shown.
 * @param script
 */
function run_script_js(script) {

    parameters = JSON.parse(backend.get_parameters(script));
    data = {};
    for (parameter_name in parameters) {
        data[parameter_name] = read_value(script, parameter_name, parameters[parameter_name])
    }
    backend.run_script(script, JSON.stringify(data));
}

/**
 * Read out the value of the parameter as defined by the form input - this depends on the parameter_type.
 *
 * @param script
 * @param parameter_name
 * @param parameter_type
 */
function read_value(script, parameter_name, parameter_type) {
    value = null;
    switch (parameter_type) {
        case "ChoiceParameter":
            value = $('#' + script + '-' + parameter_name)[0].value;
            break;
        case "WeatherPathParameter":
            value = $('#' + script + '-' + parameter_name)[0].value;
            break;
        case "BooleanParameter":
            value = $('#' + script + '-' + parameter_name)[0].checked;
            break;
        case "PathParameter":
            value = $('#' + script + '-' + parameter_name)[0].value;
            break;
        case "MultiChoiceParameter":
            value = $('#' + script + '-' + parameter_name).val();
            break;
        case "SubfoldersParameter":
            value = $('#' + script + '-' + parameter_name).val();
            break;
        default:
            // handle the default case
            value = $('#' + script + '-' + parameter_name)[0].value;
    }
    return value;
}

/**
 * Append a message to the output div for the script
 * @param script
 * @param message
 */
function add_message_js(script, message) {
    //alert(message);
    $('#output-' + script).append(atob(message));
}

function clear(script) {
    $('#output-' + script).empty();
}