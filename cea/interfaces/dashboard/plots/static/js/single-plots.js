$(document).ready(function() {
    $('.cea-plot').map(function() {
        var plot_name = this.id;
        load_plot(plot_name);
    });
});

function load_plot(plot_name) {
    buildings = $('#parameters-buildings').val();
    if (buildings === null) {
        buildings = [];
    }
    $.get('../div/' + plot_name, {'buildings': JSON.stringify(buildings)}, function(data){
            $('#x_content-' + plot_name).children().replaceWith(data);
    });
}

$('#parameters-buildings').on('changed.bs.select', function (e) {
  $('.cea-plot').map(function() {
        var plot_name = this.id;
        load_plot(plot_name);
    });
});