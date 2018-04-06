/**
 * Functions to run a tool from the tools page.
 */

function cea_run(script) {
    $('.cea-modal-close').attr('disabled', 'disabled').removeClass('btn-danger').removeClass('btn-success');
    $('#cea-console-output-body').text('');
    $('#cea-console-output').modal({'show': true, 'backdrop': 'static'});
    $.post('start/' + script, get_parameter_values(), function(data) {
        setTimeout(update_output, 100, script);
    }, 'json');
}

/**
 * Read the values of all the parameters.
 *
 * NOTE: Depends on the variable $PARAMETERS being set in the tool.html template.
 */
function get_parameter_values() {
    var result = {};
    for (var parameter_name in $PARAMETERS) {
        console.log('Reading parameter: ' + parameter_name);
        result[parameter_name] = read_value(parameter_name, $PARAMETERS[parameter_name]);
    }
    console.log(result);
    return result;
}

/**
 * Update the div#cea-console-output-body with the output of the script until it is done.
 * @param script
 */
function update_output(script) {
    $.getJSON('read/' + script, {}, function(msg) {
       if (msg === null) {
           $.getJSON('is-alive/' + script, {}, function(msg) {
               if (msg) {
                   setTimeout(update_output, 100, script);
               } else {
                   $('.cea-modal-close').removeAttr('disabled');
                   $.getJSON('exitcode/' + script, {}, function(msg){
                      if (msg === 0) {
                          $('.cea-modal-close').addClass('btn-success');
                      } else {
                          $('.cea-modal-close').addClass('btn-danger');
                      }
                   });
               }
           });

       }
       else {
           $('#cea-console-output-body').append(msg.message);
           setTimeout(update_output, 100, script);
       }
    });
}

/**
 * Read out the value of the parameter as defined by the form input - this depends on the parameter_type.
 *
 * @param script
 * @param parameter_name
 * @param parameter_type
 */
function read_value(parameter_name, parameter_type) {
    value = null;
    switch (parameter_type) {
        case "ChoiceParameter":
            value = $('#' + parameter_name)[0].value;
            break;
        case "WeatherPathParameter":
            value = $('#' + parameter_name)[0].value;
            break;
        case "BooleanParameter":
            value = $('#' + parameter_name)[0].checked;
            break;
        case "PathParameter":
            value = $('#' + parameter_name)[0].value;
            break;
        case "MultiChoiceParameter":
            value = $('#' + parameter_name).val();
            break;
        case "SubfoldersParameter":
            value = $('#' + parameter_name).val();
            break;
        case "JsonParameter":
            value = JSON.parse($('#' + parameter_name).val());
            break;
        default:
            // handle the default case
            value = $('#' + parameter_name)[0].value;
    }
    return value;
}