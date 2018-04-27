$(document).ready(function() {
    $('.cea-plot').map(function() {
        var plot_name = this.id;
        load_plot(plot_name);
    });
});

function load_plot(plot_name) {
    buildings = $('#parameters-buildings').val()
    alert(plot_name);
    $.get('../div/' + plot_name, {'buildings': buildings}, function(data){
            $('#x_content-' + plot_name).replaceWith(data);
    });
}

$('#parameters-buildings').on('changed.bs.select', function (e) {
  $('.cea-plot').map(function() {
        var plot_name = this.id;
        load_plot(plot_name);
    });
});