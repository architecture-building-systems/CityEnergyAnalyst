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

function cea_save_config(script) {
    $('#cea-save-config-modal').modal({'show': true, 'backdrop': 'static'});
    $.post('save-config/' + script, get_parameter_values(), null, 'json');
    $('#cea-save-config-modal').modal('hide');
}


/**
 * Read the values of all the parameters.
 *
 * NOTE: Depends on the variable $PARAMETERS being set in the tool.html template.
 */
function get_parameter_values() {
    var result = {};
    $('.cea-parameter').not('bootstrap-select').each((index, element) => {
        console.log('Reading parameter: ' + element.id);
        result[element.id] = read_value(element);
    });
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
function read_value(element) {
    let value = null;
    switch (element.dataset.ceaParameterTypename) {
        case "ChoiceParameter":
        case "ScenarioNameParameter":
            value = $(element)[0].value;
            break;
        case "WeatherPathParameter":
            value = $(element)[0].value;
            break;
        case "BooleanParameter":
            value = $(element)[0].checked;
            break;
        case "PathParameter":
            value = $(element)[0].value;
            break;
        case "MultiChoiceParameter":
        case "BuildingsParameter":
            value = $(element).val();
            if (value) {
                value = value.join();
            }
            else {
                value = [];
            }
            break;
        case "SubfoldersParameter":
            value = $(element).val();
            break;
        case "JsonParameter":
            value = JSON.parse($(element).val());
            break;
        default:
            // handle the default case
            value = $(element)[0].value;
    }
    return value;
}

/**
 * Show an open file dialog for a cea FileParameter and update the contents of the
 * input field.
 *
 * @param parameter_name
 */
function show_open_file_dialog(parameter_fqname,) {
    $.get('open-file-dialog/' + parameter_fqname, {}, function(html) {
        $('#cea-file-dialog .modal-content').html(html);
        $('#cea-file-dialog').modal({'show': true, 'backdrop': 'static'});
    });
}

/**
 * Navigate the open file dialog to a new folder.
 * @param parameter_fqname
 */
function file_dialog_navigate_to(parameter_fqname, current_folder, folder) {
    $.get('open-file-dialog/' + parameter_fqname, {current_folder: current_folder, folder: folder}, function(html) {
        $('#cea-file-dialog .modal-content').html(html);
    });
}

/**
 * User selected a file, highlight it.
 * @param link
 * @param file
 */
function select_file(link) {
    $('.cea-file-listing a').removeClass('bg-primary');
    $(link).addClass('bg-primary');
    $('#cea-file-dialog-select-button').prop('disabled', false);
}

/**
 * Save the selected file name (full path) to the input[type=text] with the id <target_id>.
 * @param target_id
 */
function save_file_name(target_id) {
    // figure out file path
    var file_path = $('.cea-file-listing a.bg-primary').data('save-file-path');
    $('#' + target_id).val(file_path);
}

function select_weather_file(target_id, selected_element) {
    var weather_file_path = $(selected_element).data('save-file-path');
    $('#' + target_id).val(weather_file_path);
}

/**
 * Show an open folder dialog for a cea PathParameter and update the contents of the
 * input field.
 *
 * @param parameter_name
 */
function show_open_folder_dialog(parameter_fqname,) {
    $.get('open-folder-dialog/' + parameter_fqname, {}, function(html) {
        $('#cea-folder-dialog .modal-content').html(html);
        $('#cea-folder-dialog').modal({'show': true, 'backdrop': 'static'});
    });
}

/**
 * Navigate the open file dialog to a new folder.
 * @param parameter_fqname
 * @param current_folder
 * @param folder
 */
function folder_dialog_navigate_to(parameter_fqname, current_folder, folder) {
    $.get('open-folder-dialog/' + parameter_fqname, {current_folder: current_folder, folder: folder}, function(html) {
        $('#cea-folder-dialog .modal-content').html(html);
    });
}

/**
 * Save the selected folder name (full path) to the input[type=text] with the id <target_id>.
 * @param target_id
 * @param folder_path
 */
function save_folder_name(target_id, folder_path) {
    // figure out folder path
    $('#' + target_id).val(folder_path);
}

/**
 * Some parameters need special treatment...
 */
$(document)