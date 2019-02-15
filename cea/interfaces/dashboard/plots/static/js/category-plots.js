/* get list of plots to work on... */

$(document).ready(function() {
    load_all_plots();
});



$(document).resize(function() {
    console.log('resizing!');
    load_all_plots();
});

function load_all_plots() {
    $('.cea-plot').map(function() {
        var category_name = this.dataset.ceaCategory;
        var plot_id = this.dataset.ceaPlot;
        load_plot(category_name, plot_id);
    });
}

function load_plot(category_name, plot_id) {
    $.get('../div/' + category_name + '/' + plot_id, function(data){
            $('#x_content-' + plot_id).replaceWith(data);
    });
}