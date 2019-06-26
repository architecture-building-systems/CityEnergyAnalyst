var currentTable;
var tempSelection;

// Add onclick function to tabs
$("[id$=-tab]").each(function () {
    $(this).click(function(){
        var oldtable = $('.tab.active').data('name') || 'zone';
        $('.tab').removeClass("active");
        $(this).addClass("active");

        // Remember scroll position
        var scroll = $('.tabulator-tableHolder').scrollTop();

        // Store previously selected buildings before creating new table
        if (inputstore.getData(oldtable).length) {
            tempSelection = [...inputstore.getSelected()];
        }

        var name = $(this).data('name');
        $('#property-table').empty();
        createTable("property-table",`${name}`,
            inputstore.getData(name),
            inputstore.getColumns(name),
            inputstore.getColumnTypes(name)
        );

        // Restore previous selected
        inputstore.setSelected(tempSelection);
        if (inputstore.getSelected()) {
            currentTable.selectRow(inputstore.getSelected());
        }
        filterSelection(inputstore.getSelected());

        currentTable.redraw();
        $('.tabulator-tableHolder').scrollTop(scroll);

    });
});

function createTable(parent, name, values, columns, types) {
    var placeholder = '';
    if (!inputstore.getData(name).length) {
        placeholder = '<div>File cannot be found.</div>' +
            '<div>You can create the file using the <a href="/tools/data-helper">data-helper</a> tool.</div>'
    } else {
        placeholder = '<div>No matching records found.</div>'
    }

    $(`#${parent}`).append(`<div id="${name}-table"></div>`);
    currentTable = new Tabulator(`#${name}-table`, {
        index: 'Name',
        data: values,
        columns: defineColumns(columns, types),
        placeholder: placeholder,

        selectable:true,
        layout: 'fitDataFill',
        height: '300px',
        cellEdited: updateData,
        rowSelectionChanged: addToSelection

    });

    $('#select-all-button').prop('disabled', !values.length);
    $('#filter-button').prop('disabled', !values.length);
}

function defineColumns(columns, column_types) {
    out = [];
    $.each(columns, function (index, column) {
        if (column === 'Name' || column === 'REFERENCE') {
            out.push({title: column, field: column});
        } else {
            if (column_types[column] === 'str') {
                editor = "input";
            } else  {
                editor = "number";
            }
            out.push({title: column, field: column, editor: editor});
        }
    });
    return out
}

function updateData(data) {
    var data = data.getData();
    console.log(data);

    // Find the layer of the property
    var layer = '';
    $("[id$=-tab]").each(function () {
        if ($(this).hasClass('active')) {
            layer = $(this).attr('id').split('-')[0];
        }
    });

    if (layer === 'zone' || layer === 'district') {
        inputstore.getGeojson(layer)['features']['properties'][data.getField()] = data.getValue();
        // Update inputs
        inputs['tables'][selectedBuilding.layer][data.getData()['Name']][data.getField()] = data.getValue();
        //
        geojsons = JSON.parse(JSON.stringify(geojsons));
        selectedBuilding['object'] = geojsons[selectedBuilding.layer]['features'][selectedBuilding.object.id];
    }
    // // Update geojsons
    // inputstore.getGeojson(selectedBuilding.layer)['features'][selectedBuilding.object.id]
    //     ['properties'][data.getField()] = data.getValue();
    // // Update inputs
    // inputs['tables'][selectedBuilding.layer][data.getData()['Name']][data.getField()] = data.getValue();
    //     //
    // geojsons = JSON.parse(JSON.stringify(geojsons));
    // selectedBuilding['object'] = geojsons[selectedBuilding.layer]['features'][selectedBuilding.object.id];


    // inputstore.addChange(
    //     {
    //         update: {
    //             [inputstore.getSelected().layer]: {
    //                 [data.getData()['Name']]: {
    //                     [data.getField()]: {
    //                         value: data.getValue()
    //                     }
    //                 }
    //             }
    //         }
    //     });

    redrawBuildings();
}

function addToSelection(data, row) {
    var buttons = [$('#clear-button'),$('#delete-button'),$('#edit-button')];
    var selection = data.length;
    $.each(buttons, function (_, button) {
        if (selection) {
            button.show();
        } else {
            button.hide();
        }
    });

    var out = [];
    $.each(data, function (_, building) {
        out.push(building['Name']);
    });

    inputstore.setSelected(out);
    if (currentTable) {
        var scroll = $('.tabulator-tableHolder').scrollTop();
        filterSelection(out);
        $('.tabulator-tableHolder').scrollTop(scroll);
    }

    redrawBuildings();
}

function filterSelection(selection) {
    if ($('#filter-button').hasClass('btn-success')){
        currentTable.setFilter("Name", "in", selection);
    } else {
        currentTable.clearFilter();
    }
}

$(window).load(function () {
    $('#cea-inputs').show();

    $('#zone-tab').trigger('click');

    $('#select-all-button').click(function () {
        currentTable.selectRow();
    }).show();

    $('#filter-button').click(function () {
        $(this).toggleClass('btn-success');
        filterSelection(inputstore.getSelected());
    });

    $('#clear-button').click(function () {
        currentTable.deselectRow();
        filterSelection(inputstore.getSelected());
    });
});
