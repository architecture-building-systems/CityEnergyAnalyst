$(document).ready(function() {

    $("#list-data-helper").tab("show");
    
});


/**
 * Run the current script with the parameters shown.
 * @param script
 */
function run_script_js(script) {
    if (backend.is_script_running(script)) {
        // avoid running until previous call is done
        backend.log('disabled');
        return;
    }
    $('#output-' + script).empty();
    $('#run-' + script).attr('disabled', true);
    $('#run-' + script).removeClass('btn-primary');
    $('#run-' + script).addClass('btn-outline-primary');


    parameters = JSON.parse(backend.get_parameters(script));
    data = {};
    for (parameter_name in parameters) {
        data[parameter_name] = read_value(script, parameter_name, parameters[parameter_name])
    }
    backend.run_script(script, JSON.stringify(data));

    setTimeout(function() {
        id = setInterval(function() {
            backend.log('INTERVAL FIRED')
            append_script_output(script);

            if (! backend.is_script_running(script)) {
                backend.log('IS_SCRIPT_RUNNING = FALSE');
                $('#run-' + script).addClass('btn-primary');
                $('#run-' + script).removeClass('btn-outline-primary');
                $('#run-' + script).attr('disabled', false);
                clearInterval(id);
            }
        }, 1000);
    }, 1000);
    backend.log('EXIT run_script_js')
}

function append_script_output(script) {
    backend.log('ENTER append_script_output');
    while (backend.has_output(script)) {
        next_line = backend.next_output(script);
        setTimeout(function (next_line) {
            $('#output-' + script).append(next_line);
        }, 50, next_line);
    }
    backend.log('EXIT append_script_output');
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