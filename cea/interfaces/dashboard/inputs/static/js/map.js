var map;
var zoneJson;
var districtJson;
var zoneLayer;
var districtLayer;

var deckgl;
var layers = [];
var extruded = false;
var currentViewState;

$(document).ready(function() {

    var getZone = $.getJSON('http://localhost:5050/inputs/geojson/zone', function (json) {
        console.log(json);
        zoneJson = json;
    }).fail(function () {
        console.log("Get zone failed.")
    });

    var getDistrict = $.getJSON('http://localhost:5050/inputs/geojson/district', function (json) {
        console.log(json);
        districtJson = json;
    }).fail(function () {
        console.log("Get district failed.")
    }).done();

    $.when(getZone, getDistrict).always(function () {

        if (zoneJson !== null) {
            createZoneLayer();
        }

        if (districtJson !== null) {
            createDistrictLayer();
        }

        currentViewState = {latitude: (zoneJson.bbox[1] + zoneJson.bbox[3]) / 2,
            longitude: (zoneJson.bbox[0] + zoneJson.bbox[2]) / 2,
            zoom: 16};
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
    layers = [];
    createDistrictLayer();
    createZoneLayer();
    deckgl.setProps({ layers: [...layers], controller: {dragRotate: extruded},
        viewState:{...currentViewState, pitch: pitch, bearing: bearing, transitionDuration: 300} });
}

function createDistrictLayer() {
    districtLayer = new deck.GeoJsonLayer({
        id: 'district',
        data: districtJson,
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
    layers.push(districtLayer);
}

function createZoneLayer() {
    zoneLayer = new deck.GeoJsonLayer({
        id: 'zone',
        data: zoneJson,
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
    layers.push(zoneLayer);
}