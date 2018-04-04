/**
 * Functions to run a tool from the tools page.
 */

function cea_run(script) {
    $('.cea-modal-close').attr('disabled', 'disabled');
    $('#cea-console-output-body').text('');
    $('#cea-console-output').modal({'show': true, 'backdrop': 'static'});
    $.getJSON('start/' + script, {}, function(data) {
        setTimeout(update_output, 100, script);
    });
}

/**
 * Update the div#cea-console-output-body with the output of the script until it is done.
 * @param script
 */
function update_output(script) {
    $.getJSON('is-alive/' + script, {}, function(is_alive) {
       if (is_alive) {
           $.getJSON('read/' + script, {}, function(msg) {
              $('#cea-console-output-body').append(msg.message);
              setTimeout(update_output, 100, script);
           });
       }
       else {
           $('.cea-modal-close').removeAttr('disabled');
       }
    });
}