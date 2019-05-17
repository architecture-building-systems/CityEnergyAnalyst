var map;
var zoneJson;
var districtJson;
var zoneLayer;
var districtLayer;
/**
 * Zoom in on the map for the input...
 */

$(document).ready(function() {
    // $.getJSON('http://localhost:5050/inputs/geojson/zone', function(geojson){
    //     console.log(geojson.bbox);
    //     bbox = L.latLng([
    //         (geojson.bbox[1] + geojson.bbox[3]) / 2,
    //         (geojson.bbox[0] + geojson.bbox[2]) / 2]);
    //     map = L.map('mapid').setView(bbox, 16);
    //     L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png',
    //         {attribution: "Data copyright OpenStreetMap contributors"}).addTo(map);
    //     L.geoJSON(geojson, {
    //         onEachFeature: function onEachFeature(feature, layer) {
    //             layer.on('click', function (e) {
    //                 console.log(e);
    //                 console.log(e.target.feature.properties.Name);
    //                 var pk_field = $('#cea-table').bootstrapTable('getOptions').uniqueId;
    //                 var pk = e.target.feature.properties[pk_field];
    //                 var row = $('#cea-table').bootstrapTable('getRowByUniqueId', pk);
    //                 edit_row(row);
    //             });
    //         }
    //     }).addTo(map)
    var getZone = $.getJSON('http://localhost:5050/inputs/geojson/zone', function(json) {
        console.log(json);
        zoneJson = json;
    });

    var getDistrict = $.getJSON('http://localhost:5050/inputs/geojson/district', function(json) {
        console.log(json);
        districtJson = json;
    });

    $.when(getZone, getDistrict).done(function () {
        zoneLayer = new deck.GeoJsonLayer({
            id: 'zone',
            data: zoneJson,
            opacity: 0.5,
            stroked: false,
            filled: true,
            extruded: true,
            wireframe: true,

            getElevation: f => f.properties['height_ag'],
            getFillColor: f => [0, 0, 255],

            pickable: true,
            autoHighlight: true,

            onHover: updateTooltip,
            onClick: editProperties
        });

        districtLayer = new deck.GeoJsonLayer({
            id: 'district',
            data: districtJson,
            opacity: 0.5,
            stroked: false,
            filled: true,
            extruded: true,
            wireframe: true,

            getElevation: f => f.properties['height_ag'],
            getFillColor: f => [255, 0, 0],

            pickable: true,
            autoHighlight: true,

            onHover: updateTooltip,
            onClick: editProperties
        });

        new deck.DeckGL({
            container: 'mapid',
            mapboxApiAccessToken: 'pk.eyJ1IjoidWJlcmRhdGEiLCJhIjoiY2pudzRtaWloMDAzcTN2bzN1aXdxZHB5bSJ9.2bkj3IiRC8wj3jLThvDGdA',
            mapStyle: 'mapbox://styles/mapbox/streets-v11',
            latitude: (zoneJson.bbox[1] + zoneJson.bbox[3]) / 2,
            longitude: (zoneJson.bbox[0] + zoneJson.bbox[2]) / 2,
            zoom: 16,
            pitch: 45,
            layers: [zoneLayer, districtLayer]
        });
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

function updateTooltip({x, y, object}) {
    const tooltip = document.getElementById('tooltip');

    if (object) {
        tooltip.style.top = `${y}px`;
        tooltip.style.left = `${x}px`;
        tooltip.innerHTML = `
        <div><b>Name</b></div>
        <div><div>${object.properties.Name}</div></div>
        `;
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