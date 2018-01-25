/*
dashboard.js - handle events on the dashboard.html template.
 */

function load_plot(plot_name) {
    $("#plotdiv").load("/plot/" + plot_name + "/" + $('#building-select').find(':selected').text());
}