/*jslint browser:true */
/*global $, Tabulator, io, console */

$(document).ready(function () {
    "use strict";
    load_plot();
});

function load_plot() {
    "use strict";
    $(".cea-plot").map(function () {
        let dashboard_index = this.dataset.ceaDashboardIndex;
        let plot_index = this.dataset.ceaPlotIndex;
        let x_content_id = `#x_content-${dashboard_index}-${plot_index}`;
        let x_table_id = "#x_table-" + dashboard_index + "-" + plot_index;


        $.get(`../../div/${dashboard_index}/${plot_index}`, function (data) {
            $(x_content_id).children().replaceWith(data);
        }).fail(function (data) {
            $(x_content_id).children().replaceWith(`ERROR: ${$(data.responseText).filter('p').text()}`);
            console.log("error creating plot:");
            console.log(data);
        });

        $.get("../../table/" + dashboard_index + "/" + plot_index, function (data) {
            $(x_table_id).children().replaceWith(data);
        }).fail(function (data) {
            $(x_table_id).children().replaceWith("");
            console.log("error creating plot:");
            console.log(data);
        });
    });
}

$("#parameters-buildings").on("changed.bs.select", function (e) {
    "use strict";
    load_plot();
});