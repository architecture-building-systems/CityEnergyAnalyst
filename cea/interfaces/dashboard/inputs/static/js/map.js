const {DeckGL, GeoJsonLayer} = deck;
var deckgl;
var jsonStore = {};
// Make sure the layers maintain their order
var layers = [new GeoJsonLayer({id:'streets'}), new GeoJsonLayer({id:'dh_networks'}),
    new GeoJsonLayer({id:'dc_networks'}), new GeoJsonLayer({id:'zone'}), new GeoJsonLayer({id:'district'})];
var extruded = false;
var currentViewState;

const lightMap = 'http://www.arcgis.com/sharing/rest/content/items/3e1a00aeae81496587988075fe529f71/resources/styles/root.json';
const darkMap = 'https://www.arcgis.com/sharing/rest/content/items/fc3e102d1c464522820d7f957b19a467/resources/styles/root.json';

const jsonUrls = {
    'zone': '/inputs/geojson/zone',
    'district': '/inputs/geojson/district',
    'streets': '/inputs/geojson/others/streets',
    'dh_networks': '/inputs/geojson/networks/DH',
    'dc_networks': '/inputs/geojson/networks/DC'
};

$(document).ready(function() {
    // Get zone file first. Will not create map if zone file does not exist
    $.getJSON(jsonUrls['zone'], function (json) {
        console.log(json);
        jsonStore['zone'] = json;
        createLayer('zone');
        $('#zone-cb').prop('hidden', false);
        currentViewState = {latitude: (jsonStore['zone'].bbox[1] + jsonStore['zone'].bbox[3]) / 2,
            longitude: (jsonStore['zone'].bbox[0] + jsonStore['zone'].bbox[2]) / 2,
            zoom: 16, bearing: 0, pitch: 0};

        deckgl = new DeckGL({
            container: 'mapid',
            mapStyle: {
                "version": 8,
                "sources": {
                    "osm-tiles": {
                        "type": "raster",
                        "tiles": [
                            "http://a.tile.openstreetmap.org/{z}/{x}/{y}.png",
                            "http://b.tile.openstreetmap.org/{z}/{x}/{y}.png",
                            "http://b.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        ],
                        "tileSize": 256,
                        "attribution": "Map data © OpenStreetMap contributors"
                    }
                },
                "layers": [{
                    "id": "osm-tiles",
                    "type": "raster",
                    "source": "osm-tiles",
                    "minzoom": 0,
                    "maxzoom": 22
                }]
            },
            viewState: currentViewState,
            layers: layers,
            onViewStateChange: ({viewState}) => {
                currentViewState = viewState;
                deckgl.setProps({viewState: currentViewState});
            },
            onDragStart: (info, event) => {
                if (event.rightButton && !extruded) {
                    toggle3D();
                }
            },
            controller: {dragRotate: false}
        });

        // Try to get every other input
        $.each(jsonUrls, function (key, value) {
            $.getJSON(value, function (json) {
                $(`#${key}-cb`).prop('hidden', false);
                console.log(json);
                jsonStore[key] = json;
                createLayer(key);
                deckgl.setProps({ layers: [...layers] });
            }).fail(function () {
                console.log(`Get ${key} failed.`);
            });
        });

        setupButtons();

    }).fail(function () {
        console.log("Get zone failed.");
    });
});

function setupButtons() {
    class dToggle {
      onAdd(map) {
        this._map = map;
        let _this = this;

        this._btn = document.createElement("button");
        this._btn.id = "3d-button"
        this._btn.className = "mapboxgl-ctrl-icon mapboxgl-ctrl-3d";
        this._btn.type = "button";
        this._btn.setAttribute("data-toggle", "tooltip");
        this._btn.setAttribute("title", "Toggle 3D");
        this._btn.onclick = toggle3D;

        this._container = document.createElement("div");
        this._container.className = "mapboxgl-ctrl-group mapboxgl-ctrl";
        this._container.appendChild(this._btn);

        return this._container;
      }

      onRemove() {
        this._container.parentNode.removeChild(this._container);
        this._map = undefined;
      }
    }

    class darkToggle {
      constructor() {
        this._dark = false;
      }
      onAdd(map) {
        this._map = map;
        let _this = this;

        this._btn = document.createElement("button");
        this._btn.id = "dark-button"
        this._btn.className = "mapboxgl-ctrl-icon";
        this._btn.type = "button";
        this._btn.setAttribute("data-toggle", "tooltip");
        this._btn.setAttribute("title", "Toggle Dark map");
        this._btn.onclick = function() {
            this._dark = !this._dark;
            toggleDark(this._dark);
        }
        this._btn.innerHTML = '<i class="fa fa-adjust"></i>';

        this._container = document.createElement("div");
        this._container.className = "mapboxgl-ctrl-group mapboxgl-ctrl";
        this._container.appendChild(this._btn);

        return this._container;
      }

      onRemove() {
        this._container.parentNode.removeChild(this._container);
        this._map = undefined;
      }
    }

    deckgl.getMapboxMap().addControl(new dToggle(), 'top-left');
//    deckgl.getMapboxMap().addControl(new darkToggle(), 'top-left');
}

function toggle3D() {
    extruded = !extruded
    var pitch;
    var bearing;
    if (extruded) {
        pitch = 45;
    } else {
        pitch = 0;
        bearing = 0;
    }

    var className = extruded ? "mapboxgl-ctrl-icon mapboxgl-ctrl-2d" : "mapboxgl-ctrl-icon mapboxgl-ctrl-3d";
    $('#3d-button').prop('class', className);


    createLayer('zone', { visible: $('#zone-toggle').prop('checked') });
    createLayer('district', { visible: $('#district-toggle').prop('checked') });
    deckgl.setProps({ layers: [...layers], controller: {dragRotate: extruded},
        viewState:{...currentViewState, pitch: pitch, bearing: bearing, transitionDuration: 300} });
}

function toggleDark(dark) {
    if (dark) {
        setMapStyle(darkMap);
    } else {
        setMapStyle(lightMap);
    }
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

function updateTooltip({x, y, object, layer}) {
    const tooltip = document.getElementById('tooltip');

    if (object) {
        tooltip.style.top = `${y}px`;
        tooltip.style.left = `${x}px`;
        var innerHTML = '';
        for (let prop in object.properties) {
            innerHTML += `<div><b>${prop}</b>: ${object.properties[prop]}</div>`;
        }
        if (layer.id == 'zone' || layer.id == 'district') {
            var area = turf.area(object);
            innerHTML += `<br><div><b>area</b>: ${Math.round(area * 1000) / 1000}m<sup>2</sup></div>
            <div><b>volume</b>: ${Math.round(area * object.properties['height_ag'] * 1000) / 1000}m<sup>3</sup></div>`;
        }
        if (layer.id == 'dc_networks' || layer.id == 'dh_networks') {
            if (!object.properties.hasOwnProperty("Building")) {
                var length = turf.length(object) * 1000;
                innerHTML += `<br><div><b>length</b>: ${Math.round(length * 1000) / 1000}m</div>`;
            }
        }
        tooltip.innerHTML = innerHTML;
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

function setMapStyle(styleUrl) {
    fetch(styleUrl)
       .then(response => {
          return response.json()
          .then(style => {
             style.sources.esri = {
                type: 'vector',
                maxzoom: 15,
                tiles: [
                  style.sources.esri.url + '/' + 'tile/{z}/{y}/{x}.pbf'
                ],
                attribution: 'Map data © OpenStreetMap contributors, Map layer by Esri'
             };
             console.log(style);
             deckgl.getMapboxMap().setStyle(style);

          })
       })
}
