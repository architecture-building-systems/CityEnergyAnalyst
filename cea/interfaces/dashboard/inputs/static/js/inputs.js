
$(document).ready(function() {

    $('#cea-table').on('click-row.bs.table', function(e, row, $element, field) {
        edit_row(row);
    });

    /* save table state to hidden field "cea-table-data" */
    $('#cea-save-changes-form').submit(function(){
        $('#cea-table-data').val(JSON.stringify($('#cea-table').bootstrapTable('getData', false)));
        return true;
    });
});



var row_being_edited = null;

/**
 * Show the modal dialog for editing a row
 *
 * @param rowid - the name (PK) of the row being edited
 */
function edit_row(row) {
    row_being_edited = row;
    var pk_field = $('#cea-table').bootstrapTable('getOptions').uniqueId;
    var pk = row[pk_field];
    $('#cea-row-name').text(pk);
    for (i in Object.keys(row)) {
        column = Object.keys(row)[i];
        $('#cea-input-' + column).val(row[column]);
    }

    $('#cea-row-editor').modal({'show': true, 'backdrop': 'static'});
}

function cea_save_row_to_table() {
    for (i in Object.keys(row_being_edited)) {
        column = Object.keys(row_being_edited)[i];
        row_being_edited[column] = $('#cea-input-' + column).val();
    }
    let pk_field = $('#cea-table').bootstrapTable('getOptions').uniqueId;
    $('#cea-table').bootstrapTable('updateByUniqueId', {uniqueId: row_being_edited[pk_field], row: row_being_edited});
}

function updateTooltip({x, y, object}) {
    const tooltip = document.getElementById('tooltip');

    if (object) {
        tooltip.style.top = `${y}px`;
        tooltip.style.left = `${x}px`;
        var innerHTML = '';
        for (prop in object.properties) {
            innerHTML += `<div><b>${prop}</b>: ${object.properties[prop]}</div>`
        }
        tooltip.innerHTML = innerHTML
    } else {
        tooltip.innerHTML = '';
    }
}

function editProperties({object}) {
    console.log(object.properties.Name);
    var pk_field = $('#cea-table').bootstrapTable('getOptions').uniqueId;
    var pk = object.properties[pk_field];
    var row = $('#cea-table').bootstrapTable('getRowByUniqueId', pk);
    edit_row(row);
}