/* get list of plots to work on... */

$(document).ready(function() {
    load_all_plots();

    var categories = JSON.parse($('#cea-dashboard-add-plot').attr('data-cea-categories'));
    console.log('assigned categories!');
    console.log(categories);

    $('#cea-plot-category').on('change', function(e){
        let category_label = $("option:selected", this);
        let category_name = this.value;
        console.log(categories[valueSelected]['plots'])
    });

    $('#cea-dashboard-edit-plot').on('show.bs.modal', function (e) {
        let plot_index = e.relatedTarget.dataset.plotIndex;
        let dashboard_index = e.relatedTarget.dataset.dashboardIndex;
        let url = 'plot-parameters/' + dashboard_index + '/' + plot_index;
        $.get(url, function (data) {
            $('#cea-dashboard-edit-plot-form').html(data);
            $('#cea-dashboard-edit-plot-form').attr('action', url);
            $('#cea-dashboard-edit-plot-form').attr('method', 'POST');
            $('.selectpicker').selectpicker({'actionsBox': true});
        }).fail(function (data) {
            console.log('something went terribly wrong?!');
            console.log(data);
        });
    });
});


$(document).resize(function() {
    console.log('resizing!');
    load_all_plots();
});

function load_all_plots() {
    $('.cea-plot').map(function() {
        let dashboard_index = this.dataset.ceaDashboardIndex;
        let plot_index = this.dataset.ceaPlotIndex;
        let x_content_id = '#x_content-' + dashboard_index + '-' + plot_index;

        $.get('../div/' + dashboard_index + '/' + plot_index, function(data){
                $(x_content_id).children().replaceWith(data);
        }).fail(function(data) {
            $(x_content_id).children().replaceWith('ERROR: ' + $(data.responseText).filter('p').text());
            console.log('error creating plot:');
            console.log(data);
        });
    });
}

function cea_rename_dashboard() {

}