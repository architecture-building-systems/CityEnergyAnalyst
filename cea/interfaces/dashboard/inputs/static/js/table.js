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
            if (inputstore.getSelected()) {
                tempSelection = [...inputstore.getSelected()];
            }
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
    var tool = '';
    if (!inputstore.getData(name).length) {
        placeholder = '<div>File cannot be found.</div>';
        if (name === 'zone') {
            tool = 'zone-helper';
        } else if (name === 'district') {
            tool = 'district-helper';
        } else {
            tool = 'data-helper';
        }

        placeholder += `<div>You can create the file using the <a href="/tools/${tool}">${tool}</a> tool.</div>`;
    } else {
        placeholder = '<div>No matching records found.</div>';
    }

    $(`#${parent}`).append(`<div id="${name}-table"></div>`);
    currentTable = new Tabulator(`#${name}-table`, {
        index: 'Name',
        data: values,
        columns: defineColumns(columns, types),
        placeholder: placeholder,

        layout: (['occupancy','architecture'].includes(name)) ? 'fitDataFill' : 'fitColumns',
        height: '300px',
        cellClick:selectRow,
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
    var name = data.getData()['Name'];
    var column = data.getField();
    var value = data.getValue();

    // Find the layer of the property
    var table = $('.tab.active').attr('id').split('-tab')[0];

    // TODO: Move updates to InputStore class
    // FIXME: Not very efficient. Too many loops to find index of data
    // Update input data
    var row = inputstore.getData(table)[inputstore.getDataID(table, name)];
    row[column] = value;
    if (row['REFERENCE']) {
        row['REFERENCE'] = 'User - assumption';
        $('.tab.active').trigger('click');
    }

    // Update geometries
    if (table === 'zone' || table === 'district') {
        inputstore.getGeojson(table)['features'][inputstore.getGeojsonID(table, name)]['properties'][column] = value;
        if (column === 'height_ag') {
            inputstore.createNewGeojson(table);
            redrawBuildings();
        }
    }

    inputstore.addChange('update', table, data.getData()['Name'], data.getField(), data.getValue());

}

function selectRow(e, cell) {
    var value = cell.getValue();
    if(cell.getField() === 'Name') {
        if (cell.getRow().isSelected()) {
            currentTable.deselectRow(value);
        } else {
            currentTable.selectRow(value);
        }
    }
}

function addToSelection(data, row) {
    var buttons = [$('#clear-button'),$('#delete-button'),$('#edit-button')];
    $.each(buttons, function (_, button) {
        if (data.length) {
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

function showSavingPopup() {

            $.post('save-config/' + script, get_parameter_values(), null, 'json')
                .done(function () {
                    $('#modal-prompt').text('Configuration Saved!')
                    setTimeout(function(){
                        $('#config-modal-prompt').modal('hide');
                        closeSettings();
                    }, 1000);
                });
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

    $('#delete-button').click(function () {
        var selected = inputstore.getSelected();
        var layer = ($('.tab.active').attr('id').split('-tab')[0] !== 'district') ? 'zone':'district';
        var out = '\n';
        $.each(selected, function (_, building) {
            out += `${building}\n`
        });
        if (confirm("This will delete the following buildings from every table:" + out)) {
            inputstore.deleteBuildings(layer, selected);
            $('.tab.active').trigger('click');
        }
    });

    $('#clear-button').click(function () {
        currentTable.deselectRow();
        filterSelection(inputstore.getSelected());
    });

    $('#discard-button').click(function () {
        var changes = inputstore.changes;
        if (!Object.keys(changes['update']).length && !Object.keys(changes['delete']).length) {
            alert('No changes detected');
        } else {
            if (confirm("This will discard all unsaved changes.\n" + inputstore.changesToString())) {
                inputstore.resetChanges();
                $('.tab.active').trigger('click');
            }
        }
    });

    $('#save-button').click(function () {
        var changes = inputstore.changes;
        if (!Object.keys(changes['update']).length && !Object.keys(changes['delete']).length) {
            alert('No changes detected');
        } else {
            if (confirm("Save these changes?\n" +
                "WARNING: Any buildings deleted this way cannot be recovered once saved!\n" +
                inputstore.changesToString())) {
                $('#saving-text').text('Saving Changes...');
                $('#saving-popup').modal({'show': true, 'backdrop': 'static'});

                $.ajax({
                    type: 'POST',
                    url: '/inputs/building-properties',
                    data: JSON.stringify({
                        changes: changes,
                        geojson: inputstore.geojsondata,
                        tables: inputstore.data
                    }),
                    contentType: 'application/json'
                }).done(function (data) {
                    // TODO: Either refresh page or do applyChanges()
                    inputstore.applyChanges(data);

                    $('#saving-text').text('✔ Changes Saved!');
                    setTimeout(function(){
                        $('#saving-popup').modal('hide');
                    }, 1500);
                }).fail(function () {
                    var header =
                        '<button type="button" class="close cea-modal-close" data-dismiss="modal">' +
                        'Back' +
                        '</button>';
                    $('#saving-text').text('Something went wrong');
                    $('#saving-text').append(header);
                });
            }
        }
    });
});
