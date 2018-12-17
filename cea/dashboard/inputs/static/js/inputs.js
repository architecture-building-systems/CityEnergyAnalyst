var map;

/**
 * Zoom in on the map for the input...
 */
$(document).ready(function() {
    $.getJSON('http://localhost:5050/inputs/geojson/zone', function(geojson){
        console.log(geojson.bbox);
        bbox = L.latLng([
            (geojson.bbox[1] + geojson.bbox[3]) / 2,
            (geojson.bbox[0] + geojson.bbox[2]) / 2]);
        map = L.map('mapid').setView(bbox, 16);
        L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png',
            {attribution: "Data copyright OpenStreetMap contributors"}).addTo(map);
        L.geoJSON(geojson, {
            onEachFeature: function onEachFeature(feature, layer) {
                layer.on('click', function (e) {
                    console.log(e);
                    console.log(e.target.feature.properties.Name);
                    var pk_field = $('#cea-table').bootstrapTable('getOptions').uniqueId;
                    var pk = e.target.feature.properties[pk_field];
                    var row = $('#cea-table').bootstrapTable('getRowByUniqueId', pk);
                    edit_row(row);
                });
            }
        }).addTo(map)
    });

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