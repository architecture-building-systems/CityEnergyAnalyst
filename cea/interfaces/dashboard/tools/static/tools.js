/**
 * Functions to run a tool from the tools page.
 */

function cea_run(script) {
    $('.cea-modal-close').attr('disabled', 'disabled').removeClass('btn-danger').removeClass('btn-success');
    $('#cea-console-output-body').text('');
    $('#cea-console-output').modal({'show': true, 'backdrop': 'static'});
    $.post('start/' + script, $('#cea-tool-parameters').serialize(), function(data) {
        setTimeout(update_output, 100, script);
    }, 'json');
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