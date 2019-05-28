const {DeckGL, GeoJsonLayer} = deck;
var deckgl;
var jsonStore = {};
// Make sure the layers maintain their order
var layers = [new GeoJsonLayer({id:'streets'}), new GeoJsonLayer({id:'dh_networks'}),
    new GeoJsonLayer({id:'dc_networks'}), new GeoJsonLayer({id:'zone'}), new GeoJsonLayer({id:'district'})];
var extruded = false;
var currentViewState;

const jsonUrls = {
    'zone': 'http://localhost:5050/inputs/geojson/zone',
    'district': 'http://localhost:5050/inputs/geojson/district',
    'streets': 'http://localhost:5050/inputs/geojson/others/streets',
    'dh_networks': 'http://localhost:5050/inputs/geojson/networks/DH',
    'dc_networks': 'http://localhost:5050/inputs/geojson/networks/DC'
};

$(document).ready(function() {
    // Get zone file first. Will not create map if zone file does not exist
    $.getJSON(jsonUrls['zone'], function (json) {
        console.log(json);
        jsonStore['zone'] = json;
        createLayer('zone');
        currentViewState = {latitude: (jsonStore['zone'].bbox[1] + jsonStore['zone'].bbox[3]) / 2,
            longitude: (jsonStore['zone'].bbox[0] + jsonStore['zone'].bbox[2]) / 2,
            zoom: 16, bearing: 0, pitch: 0};

        deckgl = new DeckGL({
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

        // Try to get every other input
        $.each(jsonUrls, function (key, value) {
            $.getJSON(value, function (json) {
                console.log(json);
                jsonStore[key] = json;
                createLayer(key);
                deckgl.setProps({ layers: [...layers] });
            }).fail(function () {
                console.log(`Get ${key} failed.`);
            });
        });

        setTimeout(function() {
            console.log(layers)
        }, 5000);

    }).fail(function () {
        console.log("Get zone failed.");
        $('#zone-toggle').prop('disabled', true);
        $('#district-toggle').prop('disabled', true);
        $('#streets-toggle').prop('disabled', true);
        $('#dh_networks-toggle').prop('disabled', true);
        $('#dc_networks-toggle').prop('disabled', true);
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

    createLayer('zone', { visible: $('#zone-toggle').prop('checked') });
    createLayer('district', { visible: $('#district-toggle').prop('checked') });
    deckgl.setProps({ layers: [...layers], controller: {dragRotate: extruded},
        viewState:{...currentViewState, pitch: pitch, bearing: bearing, transitionDuration: 300} });
}

function toggleLayer(obj) {
    if (obj.checked) {
        createLayer(obj.value, { visible: true });
    } else {
        createLayer(obj.value, { visible: false });
    }
    deckgl.setProps({ layers: [...layers] });
}

function createLayer(name, options={}) {
    switch(name) {
        case 'zone':
            createZoneLayer(options);
            break;
        case 'district':
            createDistrictLayer(options);
            break;
        case 'streets':
            createStreetsLayer(options);
            break;
        case 'dh_networks':
            createDHNetworksLayer(options);
            break;
        case 'dc_networks':
            createDCNetworksLayer(options);
            break;
    }
}

function createDistrictLayer(options={}) {
    layers = layers.filter(layer => layer.id!=='district');

    layers.splice(4, 0, new GeoJsonLayer({
        id: 'district',
        data: jsonStore['district'],
        opacity: 0.5,
        extruded: extruded,
        wireframe: true,
        filled: true,

        getElevation: f => f.properties['height_ag'],
        getFillColor: [255, 0, 0],

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,
        onClick: editProperties,

        ...options
    }));
}

function createZoneLayer(options={}) {
    layers = layers.filter(layer => layer.id!=='zone');

    layers.splice(3, 0, new GeoJsonLayer({
        id: 'zone',
        data: jsonStore['zone'],
        opacity: 0.5,
        extruded: extruded,
        wireframe: true,
        filled: true,

        getElevation: f => f.properties['height_ag'],
        getFillColor: [0, 0, 255],

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,
        onClick: editProperties,

        ...options
    }));
}

function createStreetsLayer(options={}) {
    layers = layers.filter(layer => layer.id!=='streets');
    layers.splice(0, 0, new GeoJsonLayer({
        id: 'streets',
        data: jsonStore['streets'],

        getLineColor: [255, 0, 0],
        getLineWidth: 3,

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,
        onClick: editProperties,

        ...options
    }));
}

function createDHNetworksLayer(options={}) {
    layers = layers.filter(layer => layer.id!=='dh_networks');
    layers.splice(1, 0, new GeoJsonLayer({
        id: 'dh_networks',
        data: jsonStore['dh_networks'],
        stroked: false,
        filled: true,

        getLineColor: [0, 255, 0],
        getFillColor: f => nodeFillColor(f.properties['Type']),
        getLineWidth: 3,
        getRadius: 3,

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,
        onClick: editProperties,

        ...options
    }));
}

function createDCNetworksLayer(options={}) {
    layers = layers.filter(layer => layer.id!=='dc_networks');
    layers.splice(2, 0, new GeoJsonLayer({
        id: 'dc_networks',
        data: jsonStore['dc_networks'],
        stroked: false,
        filled: true,

        getLineColor: [0, 255, 244],
        getFillColor: f => nodeFillColor(f.properties['Type']),
        getLineWidth: 3,
        getRadius: 3,

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,
        onClick: editProperties,

        ...options
    }));
}

function updateTooltip({x, y, object}) {
    const tooltip = document.getElementById('tooltip');

    if (object) {
        tooltip.style.top = `${y}px`;
        tooltip.style.left = `${x}px`;
        var innerHTML = '';
        for (let prop in object.properties) {
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

function nodeFillColor(type) {
    if (type === 'NONE') {
        return [100, 100, 100]
    } else if (type === 'CONSUMER') {
        return [255, 255, 255]
    } else if (type === 'PLANT') {
        return [0, 0, 0]
    }
}
