$(document).ready(function() {
    load_plot();
});

function load_plot() {
    $('.cea-plot').map(function() {
        let dashboard_index = this.dataset.ceaDashboardIndex;
        let plot_index = this.dataset.ceaPlotIndex;
        let x_content_id = '#x_content-' + dashboard_index + '-' + plot_index;

        $.get('../../div/' + dashboard_index + '/' + plot_index, function(data){
                $(x_content_id).children().replaceWith(data);
        }).fail(function(data) {
            $(x_content_id).children().replaceWith('ERROR: ' + $(data.responseText).filter('p').text());
            console.log('error creating plot:');
            console.log(data);
        });
    });
}

$('#parameters-buildings').on('changed.bs.select', function (e) {
  load_plot();
});