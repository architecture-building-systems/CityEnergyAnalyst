var deckgl;
var jsonStore = {};
var layers = [];
var extruded = true;
var currentViewState;

$(document).ready(function() {

    var getZone = $.getJSON('http://localhost:5050/inputs/geojson/zone', function (json) {
        console.log(json);
        jsonStore['zone'] = json;
    }).fail(function () {
        console.log("Get zone failed.")
    });

    var getDistrict = $.getJSON('http://localhost:5050/inputs/geojson/district', function (json) {
        console.log(json);
        jsonStore['district'] = json;
    }).fail(function () {
        console.log("Get district failed.")
    });

    var getStreets = $.getJSON('http://localhost:5050/inputs/geojson/others/streets', function (json) {
        console.log(json);
        jsonStore['streets'] = json;
    }).fail(function () {
        console.log("Get streets failed.")
    });

    $.when(getZone, getDistrict, getStreets).always(function () {
        currentViewState = {latitude: 0, longitude: 0, zoom: 0};
        if (jsonStore['zone'] !== undefined) {
            createZoneLayer();
            currentViewState = {latitude: (jsonStore['zone'].bbox[1] + jsonStore['zone'].bbox[3]) / 2,
            longitude: (jsonStore['zone'].bbox[0] + jsonStore['zone'].bbox[2]) / 2,
            zoom: 16};
        }

        if (jsonStore['district'] !== undefined) {
            createDistrictLayer();
        }

        if (jsonStore['streets'] !== undefined) {
            createStreetsLayer();
        }

        deckgl = new deck.DeckGL({
            container: 'mapid',
            mapboxApiAccessToken: 'pk.eyJ1IjoidWJlcmRhdGEiLCJhIjoiY2pudzRtaWloMDAzcTN2bzN1aXdxZHB5bSJ9.2bkj3IiRC8wj3jLThvDGdA',
            mapStyle: 'mapbox://styles/mapbox/streets-v11',
            viewState: currentViewState,
            layers: layers,
            onViewStateChange: ({viewState}) => {
                currentViewState = viewState;
                deckgl.setProps({viewState: currentViewState});
            },
            controller: {dragRotate: false}
        });
        toggle3D();
    });
});

function toggle3D() {
    extruded = !extruded;
    var pitch;
    var bearing;
    if (extruded) {
        pitch = 45;
    } else {
        pitch = 0;
        bearing = 0;
    }

    createDistrictLayer();
    createZoneLayer();
    deckgl.setProps({ layers: [...layers], controller: {dragRotate: extruded},
        viewState:{...currentViewState, pitch: pitch, bearing: bearing, transitionDuration: 300} });
}

function createDistrictLayer() {
    var districtLayer = new deck.GeoJsonLayer({
        id: 'district',
        data: jsonStore['district'],
        opacity: 0.5,
        extruded: extruded,
        wireframe: true,

        getElevation: f => f.properties['height_ag'],
        getFillColor: [255, 0, 0],

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,
        onClick: editProperties
    });

    layers = layers.filter(layer => layer.id!=='district');
    layers.push(districtLayer);
}

function createZoneLayer() {
    var zoneLayer = new deck.GeoJsonLayer({
        id: 'zone',
        data: jsonStore['zone'],
        opacity: 0.5,
        extruded: extruded,
        wireframe: true,

        getElevation: f => f.properties['height_ag'],
        getFillColor: [0, 0, 255],

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,
        onClick: editProperties
    });
    layers = layers.filter(layer => layer.id!=='zone');
    layers.push(zoneLayer);
}

function createStreetsLayer() {
    var streetsLayer = new deck.GeoJsonLayer({
        id: 'streets',
        data: jsonStore['streets'],

        getLineColor: [255, 0, 0],
        getLineWidth: 3,

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,
        onClick: editProperties
    });
    layers = layers.filter(layer => layer.id!=='streets');
    layers.push(streetsLayer);
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