var currentTable;
var tempSelection;
var editform = $('#cea-column-editor-form');
const OCCUPANCY_ALERT = 'Remember to run data-helper after editing occupancy to reflect the changes to other building properties.';
let executedAlert = false;

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

    let editCallback = {};
    if (name === 'occupancy') {
        editCallback.dataEdited = showOccupancyAlert;
    }

    $(`#${parent}`).append(`<div id="${name}-table"></div>`);
    currentTable = new Tabulator(`#${name}-table`, {
        index: 'Name',
        data: values,
        columns: defineColumns(columns, types),
        placeholder: placeholder,

        layout: (['occupancy','architecture'].includes(name)) ? 'fitDataFill' : 'fitColumns',
        height: '300px',
        cellClick: selectRow,
        cellEdited: updateData,
        rowSelectionChanged: addToSelection,

        ...editCallback
    });

    createTooltip();

    $('#select-all-button').prop('disabled', !values.length);
    $('#filter-button').prop('disabled', !values.length);
}

function defineColumns(columns, column_types) {
    var out = [];
    var editor = '';
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
    var table = $('.tab.active').data('name');

    // TODO: Move updates to InputStore class
    // FIXME: Not very efficient. Too many loops to find index of data
    // Update table data
    var row = currentTable.getRow(name).getData();
    row[column] = value;
    if (row['REFERENCE']) {
        row['REFERENCE'] = 'User - assumption';
        $('.tab.active').trigger('click');
    }

    // Update geometries
    if (table === 'zone' || table === 'district') {
        var properties = inputstore.getGeojson(table)['features'][inputstore.getGeojsonID(table, name)]['properties'];
        properties[column] = value;
        if (properties['REFERENCE']) {
            properties['REFERENCE'] = 'User - assumption';
        }
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

function createTooltip() {
    var table = $('.tab.active').data('name');

    $.each(inputstore.getColumns(table), function (_, column) {
        var glossary = inputstore.glossary[column];
        if (glossary) {
            $(`.tabulator-col-title:contains("${column}")`)
                .attr('data-toggle', 'tooltip')
                .attr('data-placement', 'top')
                .attr('data-container', 'body')
                .attr('data-html', true)
                .prop('title', `DESCRIPTION: ${glossary['DESCRIPTION']}<br>UNIT: ${glossary['UNIT']}`)
                .tooltip();
        }
    });
}

function showOccupancyAlert() {
    if (!executedAlert) {
        executedAlert = true;
        alert(OCCUPANCY_ALERT);
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

    $('#edit-button').click(function () {
        var table = $('.tab.active').data('name');
        var columns = inputstore.getColumns(table);

        $('#cea-column-editor .modal-title').text(`Editing ${table} table`);

        if (table === 'occupancy') {
            $('#cea-column-editor-form').on('submit', showOccupancyAlert);
        }

        // TODO: Add input validation
        editform.empty();
        $.each(columns, function (_, column) {
            var type = (inputstore.getColumnTypes(table)[column] === 'str') ? 'text':'number';
            if (column !== 'Name' && column !== 'REFERENCE') {
                var input =
                    `<div class="form-group">` +
                      `<label class="control-label col-md-3 col-sm-3 col-xs-12" for="cea-input-${ column }">${ column }</label>` +
                      `<div class="col-md-6 col-sm-6 col-xs-12">` +
                        `<input type="${ type }" id="cea-input-${ column }" name="${ column }" placeholder="unchanged"
                               class="form-control col-md-7 col-xs-12">` +
                      `</div>` +
                    `</div>`;
                editform.append(input);
                if (type === 'text') {
                    $(`#cea-input-${ column }`).prop('pattern', '[T][0-9]+')
                        .prop('title', 'T[number]');
                } else if (type === 'number') {
                    $(`#cea-input-${ column }`).prop('step', 'any')
                        .prop('min', '0');
                }
            }
        });

        $('#cea-column-editor').on('shown.bs.modal', function () {
            new Tabulator("#selected-buildings", {
                data: currentTable.getSelectedData(),
                columns: currentTable.getColumnDefinitions(),
                layout:"fitColumns",
                height: 200
            });
        }).modal({'show': true, 'backdrop': 'static'});
    });

    $('#delete-button').click(function () {
        var selected = inputstore.getSelected();
        var layer = ($('.tab.active').data('name') !== 'district') ? 'zone':'district';
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
            var deletemsg = Object.keys(changes['delete']).length ? "WARNING: Any buildings deleted this way cannot be recovered once saved!\n":"";
            if (confirm("Save these changes?\n"+ deletemsg +inputstore.changesToString())) {
                $('#saving-text').text('Saving Changes...');
                $('#saving-popup').modal({'show': true, 'backdrop': 'static'});

                $.ajax({
                    type: 'POST',
                    url: '/inputs/building-properties',
                    data: JSON.stringify({
                        changes: changes,
                        geojson: inputstore.geojsondata,
                        tables: inputstore.data,
                        crs: inputstore.crs
                    }),
                    contentType: 'application/json'
                }).done(function (data) {
                    // TODO: Either refresh page or do applyChanges()
                    inputstore.applyChanges(data);
                   redrawBuildings();

                    $('#saving-text').text('✔ Changes Saved!');
                    setTimeout(function(){
                        $('#saving-popup').modal('hide');
                    }, 1500);
                }).fail(function () {
                    var header =
                        '<button type="button" class="close cea-modal-close" data-dismiss="modal">' +
                        'Back' +
                        '</button>';
                    $('#saving-text').text('Something went wrong')
                        .append(header);
                });
            }
        }
    });

    editform.submit(function (e) {
        e.preventDefault();
        var table = $('.tab.active').data('name');
        var props = {};
        var form = editform.serialize().split('&');
        $.each(form, function (_, prop) {
            var temp = prop.split('=');
            if (temp[1] !== '') {
                var value = temp[1];
                if (inputstore.getColumnTypes(table)[temp[0]] !== 'str'){
                    value = Number(value);
                }
                props[temp[0]] = value;
            }
        });

        var data = [];
        $.each(inputstore.getSelected(), function (_, building) {
            // Add to changes
            $.each(props, function (key, value) {
                inputstore.addChange('update', table, building, key, value);
            });

            // Update table data
            var out = {Name: building, ...props};
            var row = currentTable.getRow(building).getData();
            if (row['REFERENCE']) {
                out['REFERENCE'] = 'User - assumption';
            }
            data.push(out);

            // Update geojsons
            // FIXME: Copied from updateData()
            if (table === 'zone' || table === 'district') {
                Object.assign(inputstore.getGeojson(table)['features'][inputstore.getGeojsonID(table, building)]['properties'], out);
            }
        });

        if (props['height_ag']) {
            inputstore.createNewGeojson(table);
           redrawBuildings();
        }

        currentTable.updateData(data);

        $('#cea-column-editor').modal('hide');
    });
});

window.addEventListener("beforeunload", function (e) {
    var confirmationMessage = 'There are still some unsaved changes.' +
        'Any unsaved changes will be discarded';

    if (Object.keys(inputstore.changes['update']).length || Object.keys(inputstore.changes['delete']).length) {
        e.returnValue = confirmationMessage;
        return  confirmationMessage;
    }
});