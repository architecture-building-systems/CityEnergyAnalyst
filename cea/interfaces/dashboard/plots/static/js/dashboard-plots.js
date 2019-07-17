/* get list of plots to work on... */

$(document).ready(function() {
    load_all_plots();

    var categories = JSON.parse($('#cea-dashboard-add-plot').attr('data-cea-categories'));
    console.log("assigned categories!");
    console.log(categories);

    $("[id|=cea-plot-category]").on("change", function(e){
        let category_name = this.value;
        $("[id|=cea-plot-name]").empty();
        $.each(categories[category_name]["plots"], function(i, p){
            console.log(p);
            $("[id|=cea-plot-name]").append($("<option></option>").attr("value", p.id).text(p.name));
        });

        console.log(categories[category_name]["plots"]);
    });

    $("#cea-dashboard-edit-plot").on("show.bs.modal", function (e) {
        let plot_index = e.relatedTarget.dataset.plotIndex;
        let dashboard_index = e.relatedTarget.dataset.dashboardIndex;
        let url = "plot-parameters/" + dashboard_index + "/" + plot_index;
        $.get(url, function (data) {
            $("#cea-dashboard-edit-plot-form").html(data)
                .attr("action", url)
                .attr("method", "POST");
            $(".selectpicker").selectpicker({"actionsBox": true});
            $(".js-switch").each(function(_, checkbox){
                console.log("setting up Switchery");
                console.log(checkbox);
                switcher = new Switchery(checkbox);
            });
        }).fail(function (data) {
            console.log("something went terribly wrong?!");
            console.log(data);
        });
    });

    $("#cea-dashboard-replace-plot").on("show.bs.modal", function (e) {
        let plot_index = e.relatedTarget.dataset.plotIndex;
        let dashboard_index = e.relatedTarget.dataset.dashboardIndex;
        console.log(plot_index, dashboard_index);
        let url = "replace-plot/" + dashboard_index + "/" + plot_index;
        $("#cea-dashboard-replace-plot-form").attr("action", url)
            .attr("method", "POST");
    });

    $("#cea-dashboard-edit-plot-form").submit(function (e) {
        e.preventDefault();
        $.post($("#cea-dashboard-edit-plot-form").attr("action"), get_parameter_values(), function(data){
            console.log(data);
            location.reload();
        }, "json");
        return false;
    });

    $("#dashboard-selector").val(window.location.href.split('/').pop().replace(/[^0-9]/g, ''))
        .change(function () {
            if($(this).val() === "manage") {
                window.location.href = "./" + "manage";
            } else if($(this).val() !== "new") {
                window.location.href = "./" + $(this).val();
            }
        });
});

function load_all_plots() {
    $(".cea-plot").map(function() {
        let dashboard_index = this.dataset.ceaDashboardIndex;
        let plot_index = this.dataset.ceaPlotIndex;
        let x_content_id = "#x_content-" + dashboard_index + "-" + plot_index;
        let x_table_id = "#x_table-" + dashboard_index + "-" + plot_index;

        $.get("../div/" + dashboard_index + "/" + plot_index, function(data){
            $(x_content_id).children().replaceWith(data);
            $('#table-btn-'+plot_index).show();
        }).fail(function(data) {
            // Server error
            if (data.status === 500) {
                $(x_content_id).children().replaceWith("ERROR: " + $(data.responseText).filter("p").text());
                console.log("error creating plot: "+x_content_id);
                console.log(data);
            }
            // Missing files
            if (data.status === 404) {
                $(x_content_id).children().replaceWith(data.responseText);
            }
        });

        // $.get("../table/" + dashboard_index + "/" + plot_index, function(data){
        //         $(x_table_id).children().replaceWith(data);
        // }).fail(function(data) {
        //     $(x_table_id).children().replaceWith("");
        //     console.log("error creating plot:");
        //     console.log(data);
        // });
    });
}

function add_new_dashboard() {
    $.get("new", function (html) {
        $("#cea-prompt .modal-content").html(html);
        $("#cea-prompt").modal({"show": true, "backdrop": "static"});
    });
}

function duplicate_dashboard(dashboard_index) {
    $.post('./duplicate/'+dashboard_index, function (response) {
        console.log(response);
    });
}

function open_table(element) {
    let style = document.styleSheets[0].ownerNode.cloneNode();
    let height = 500;
    let width = 900;
    let table = window.open("../table/" + element.dataset.dashboardIndex + "/" + element.dataset.plotIndex,
        'popUpWindow', 'height='+height+',width='+width+',location=no,menubar=no,status=no,titlebar=no,resizable');
    table.onload = function() {
        table.document.title = 'City Energy Analyst | ' + element.dataset.plotTitle + ' Table';
        table.document.body.innerHTML = '<h1>'+element.dataset.plotTitle+'</h1><br>' + table.document.body.innerHTML;
        table.document.head.append(style);
    }
}

window.addEventListener('resize', function () {
    console.log('resizing');
    $.each($('.plotly-graph-div.js-plotly-plot'), function (index) {
        Plotly.Plots.resize($(this).attr('id'));
    });
});