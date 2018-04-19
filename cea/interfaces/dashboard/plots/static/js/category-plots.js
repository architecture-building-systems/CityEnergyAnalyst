/* get list of plots to work on... */

$(document).ready(function() {
    $('.cea-plot').map(function() {
        var plot_name = this.id;
        load_plot(plot_name);
    });
});

$(window).resize(function() {
    alert('resizing!');
    $('.cea-plot').map(function() {
        var plot_name = this.id;
        load_plot(plot_name);
    });
});


function load_plot(plot_name) {
    $.get('../div/' + plot_name, function(data){
            $('#x_content-' + plot_name).replaceWith(data);
    });
}