const {DeckGL, GeoJsonLayer} = deck;
const lightMap = {
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
};

const darkMap = {
    "version": 8,
    "sources": {
        "carto-tiles": {
            "type": "raster",
            "tiles": [
                "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
                "https://cartodb-basemaps-b.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
                "https://cartodb-basemaps-c.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png"
            ],
            "tileSize": 256,
            "attribution": "Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL."
        }
    },
    "layers": [{
        "id": "carto-tiles",
        "type": "raster",
        "source": "carto-tiles",
        "minzoom": 0,
        "maxzoom": 22
    }]
};

const jsonURLs = {
    'streets': '/inputs/geojson/others/streets',
    'dh_networks': '/inputs/geojson/networks/DH',
    'dc_networks': '/inputs/geojson/networks/DC'
};

class MapClass {
    constructor(container = 'map') {
        this.data = {};
        this.layerProps = {};

        this.cameraOptions = {};
        this.currentViewState = {
            latitude: 0,
            longitude: 0,
            zoom: 0, bearing: 0, pitch: 0
        };

        this.mapStyles = {light: lightMap, dark: darkMap};
        this.layers = [new GeoJsonLayer({id:'streets'}), new GeoJsonLayer({id:'dh_networks'}),
            new GeoJsonLayer({id:'dc_networks'}), new GeoJsonLayer({id:'zone'}), new GeoJsonLayer({id:'district'})];

        this.deckgl = new DeckGL({
            container: container,
            mapStyle: this.mapStyles.light,
            viewState: this.currentViewState,
            layers: this.layers,
            onViewStateChange: ({viewState}) => {
                this.currentViewState = viewState;
                this.deckgl.setProps({viewState: this.currentViewState});
            },

            controller: {dragRotate: false}
        });

        $(`#${container}`).attr('oncontextmenu', 'return false;')
            .append('<div id="map-tooltip"></div>')
            .append('<div id="layers-group">');
    }

    init({data = {}, urls = {}, extrude = false} = {}) {
        let _this = this;
        if (data.hasOwnProperty('zone') || this.data.hasOwnProperty('zone')) {
            this.data.zone = data.zone;
            $.each(data, function (layer) {
                console.log(layer, data[layer]);
                _this.addLayer(layer, data[layer]);
            });

            this.calculateCamera();

            setupButtons(this);

            this.currentViewState = {
                ...this.currentViewState,
                zoom: this.cameraOptions.zoom,
                latitude: this.cameraOptions.center.lat,
                longitude: this.cameraOptions.center.lng
            };

            this.deckgl.getMapboxMap().once('styledata', function () {
                _this.setCamera({
                    transitionDuration: 300,
                    onTransitionEnd: () => {
                        extrude && $('#3d-button').trigger('click')
                    }
                });
                $('.mapboxgl-ctrl-icon[data-toggle="tooltip"]').tooltip();
            });

            let _jsonURLs = jsonURLs;
            if (Object.keys(urls).length) {
                _jsonURLs =  urls;
            }
            $.each(_jsonURLs, function (key, value) {
                $.getJSON(value, function (json) {
                    console.log(key, json);
                    _this.addLayer(key, json);
                }).fail(function () {
                    console.log(`Get ${key} failed.`);
                });
            });

        } else {
            console.error('Please enter a zone geojson file')
        }
    }

    setLayerProps(layer, props) {
        if (this.data.hasOwnProperty(layer)) {
            this.layerProps[layer] = {
                ...this.layerProps[layer],
                ...props,
            };
            this.renderLayer(layer);
        } else {
            console.error('Layer ' + layer + ' does not exist')
        }
    }

    addLayer(layer, data) {
        let _this = this;
        this.data = {
            ...this.data,
            [layer]: data
        };
        $('#layers-group').append(`<span><input id='${layer}-toggle' type='checkbox' name='layer-toggle' value='${layer}' checked>` +
            `<label for='${layer}-toggle'>${layer}</label></span>`);
        $(`#${layer}-toggle`).change(function () {
            _this.renderLayer(layer);
        });
        this.renderLayer(layer);
    }

    renderLayer(layer) {
        this.layers = createLayer(layer, this.layers, this.data[layer], this.layerProps[layer]);
        this.deckgl.setProps({ layers: [...this.layers] });
    }

    redrawBuildings(data={}) {
        this.data = {
            ...this.data,
            ...data
        };
        this.renderLayer('zone');
        this.renderLayer('district');
    }

    calculateCamera() {
        let points = [];
        if (this.data.hasOwnProperty('zone')) {
            let bbox = this.data.zone.bbox;
            points.push([bbox[0],bbox[1]],[bbox[2],bbox[3]])
        }
        if (this.data.hasOwnProperty('district')) {
            let bbox = this.data.district.bbox;
            points.push([bbox[0],bbox[1]],[bbox[2],bbox[3]])
        }
        let bbox = turf.bbox(turf.multiPoint(points));
        this.cameraOptions = this.deckgl.getMapboxMap().cameraForBounds(
            [[bbox[0], bbox[1]], [bbox[2], bbox[3]]],
            {padding: 30, maxZoom: 18}
        );

        return bbox
    }

    setCamera(options={}) {
        this.deckgl.setProps({
            viewState: {
                ...this.currentViewState,
                ...options
            }
        });
    }


    // redrawAll() {
    //     this.redrawBuildings();
    //     this.renderLayer('streets');
    //     this.renderLayer('dc_networks');
    //     this.renderLayer('dh_networks');
    // }
}

function createLayer(name, layers, data, props={}) {
    switch(name) {
        case 'zone':
            return createZoneLayer(layers, data, props);
        case 'district':
            return createDistrictLayer(layers, data, props);
        case 'streets':
            return createStreetsLayer(layers, data, props);
        case 'dc_networks':
            return createDCNetworksLayer(layers, data, props);
        case 'dh_networks':
            return createDHNetworksLayer(layers, data, props);
    }
}

function createZoneLayer(_layers, data, props={}) {
    let id = 'zone';
    let layers = _layers.filter(layer => layer.id!==id);
    layers.splice(3, 0, new GeoJsonLayer({
        id: id,
        data: data,
        opacity: 0.5,
        wireframe: true,
        filled: true,
        visible: $(`#${id}-toggle`).prop('checked'),

        getElevation: f => f.properties['height_ag'],
        getFillColor: [0, 0, 255],

        pickable: true,
        autoHighlight: true,
        highlightColor: [255, 255, 0, 128],

        onHover: updateTooltip,

        ...props
    }));

    return layers
}

function createDistrictLayer(_layers, data, props={}) {
    let id = 'district';
    let layers = _layers.filter(layer => layer.id!==id);
    layers.splice(4, 0, new GeoJsonLayer({
        id: id,
        data: data,
        opacity: 0.5,
        wireframe: true,
        filled: true,
        visible: $(`#${id}-toggle`).prop('checked'),

        getElevation: f => f.properties['height_ag'],
        getFillColor: [255, 0, 0],

        pickable: true,
        autoHighlight: true,
        highlightColor: [255, 255, 0, 128],

        onHover: updateTooltip,

        ...props
    }));

    return layers
}

function createStreetsLayer(_layers, data, props={}) {
    let id = 'streets';
    let layers = _layers.filter(layer => layer.id!==id);
    layers.splice(0, 0, new GeoJsonLayer({
        id: id,
        data: data,
        visible: $(`#${id}-toggle`).prop('checked'),

        getLineColor: [255, 0, 0],
        getLineWidth: 3,

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,

        ...props
    }));

    return layers
}

function createDCNetworksLayer(_layers, data, props={}) {
    let id = 'dc_networks';
    let layers = _layers.filter(layer => layer.id!==id);
    layers.splice(2, 0, new GeoJsonLayer({
        id: id,
        data: data,
        stroked: false,
        filled: true,
        visible: $(`#${id}-toggle`).prop('checked'),

        getLineColor: [0, 255, 255],
        getFillColor: f => nodeFillColor(f.properties['Type']),
        getLineWidth: 3,
        getRadius: 3,

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,

        ...props
    }));

    return layers
}

function createDHNetworksLayer(_layers, data, props={}) {
    let id = 'dh_networks';
    let layers = _layers.filter(layer => layer.id!==id);
    layers.splice(1, 0, new GeoJsonLayer({
        id: id,
        data: data,
        stroked: false,
        filled: true,
        visible: $(`#${id}-toggle`).prop('checked'),

        getLineColor: [0, 255, 0],
        getFillColor: f => nodeFillColor(f.properties['Type']),
        getLineWidth: 3,
        getRadius: 3,

        pickable: true,
        autoHighlight: true,

        onHover: updateTooltip,

        ...props
    }));

    return layers
}

function setupButtons(MapClass) {
    const _this = MapClass;

    class dToggle {
        constructor() {
            this._extruded = false;
        }
        onAdd(map) {
            this._map = map;

            this._btn = document.createElement("button");
            this._btn.id = "3d-button";
            this._btn.className = "mapboxgl-ctrl-icon mapboxgl-ctrl-3d";
            this._btn.type = "button";
            this._btn.setAttribute("data-extruded", this._extruded);
            this._btn.setAttribute("data-toggle", "tooltip");
            this._btn.setAttribute("data-placement", "right");
            this._btn.setAttribute("title", "Toggle 3D");
            this._btn.onclick = function () {
                this._extruded = !this._extruded;
                this.setAttribute("data-extruded", this._extruded);
                let pitch;
                let bearing;
                if (this._extruded) {
                    pitch = 45;
                } else {
                    pitch = 0;
                    bearing = 0;
                }

                let className = this._extruded ? "mapboxgl-ctrl-icon mapboxgl-ctrl-2d" : "mapboxgl-ctrl-icon mapboxgl-ctrl-3d";
                $('#3d-button').prop('class', className);

                _this.setLayerProps('zone', {extruded: this._extruded});
                _this.setLayerProps('district', {extruded: this._extruded});
                _this.deckgl.setProps({ controller: {dragRotate: this._extruded},
                    viewState:{..._this.currentViewState, pitch: pitch, bearing: bearing, transitionDuration: 300} });
            };

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

            this._btn = document.createElement("button");
            this._btn.id = "dark-button";
            this._btn.className = "mapboxgl-ctrl-icon";
            this._btn.type = "button";
            this._btn.setAttribute("data-toggle", "tooltip");
            this._btn.setAttribute("data-placement", "right");
            this._btn.setAttribute("title", "Toggle Dark map");
            this._btn.onclick = function() {
                this._dark = !this._dark;
                if (this._dark) {
                    _this.deckgl.getMapboxMap().setStyle(_this.mapStyles.dark);
                } else {
                    _this.deckgl.getMapboxMap().setStyle(_this.mapStyles.light);
                }
            };
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

    class recenterMap {
        onAdd(map) {
            this._map = map;

            this._btn = document.createElement("button");
            this._btn.id = "recenter-button";
            this._btn.className = "mapboxgl-ctrl-icon mapboxgl-ctrl-recenter";
            this._btn.type = "button";
            this._btn.setAttribute("data-toggle", "tooltip");
            this._btn.setAttribute("data-placement", "right");
            this._btn.setAttribute("title", "Center to location");
            this._btn.onclick = function () {
                _this.deckgl.setProps({
                    viewState:{
                        ..._this.currentViewState,
                        zoom: _this.cameraOptions.zoom,
                        latitude: _this.cameraOptions.center.lat,
                        longitude: _this.cameraOptions.center.lng,
                        transitionDuration: 300
                    }
                });
            };

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

    _this.deckgl.getMapboxMap().addControl(new dToggle(), 'top-left');
    _this.deckgl.getMapboxMap().addControl(new darkToggle(), 'top-left');
    _this.deckgl.getMapboxMap().addControl(new recenterMap(), 'top-left');
    _this.deckgl.setProps({
        onDragStart: (info, event) => {
            let dToggleButton = $('#3d-button');
            if (event.rightButton && dToggleButton.attr('data-extruded')==='false') {
                dToggleButton.trigger('click');
            }
        }
    });
}

function updateTooltip({x, y, object, layer}) {
    const tooltip = document.getElementById('map-tooltip');
    if (object) {
        tooltip.style.top = `${y}px`;
        tooltip.style.left = `${x}px`;
        let innerHTML = '';

        if (layer.id === 'zone' || layer.id === 'district') {
            $.each(object.properties, function (key, value)  {
                innerHTML += `<div><b>${key}</b>: ${value}</div>`;
            });
            let area = turf.area(object);
            innerHTML += `<br><div><b>area</b>: ${Math.round(area * 1000) / 1000}m<sup>2</sup></div>` +
                `<div><b>volume</b>: ${Math.round(area * object.properties['height_ag'] * 1000) / 1000}m<sup>3</sup></div>`;
        } else if (layer.id === 'dc_networks' || layer.id === 'dh_networks') {
            if (!object.properties.hasOwnProperty("Building")) {
                let length = turf.length(object) * 1000;
                innerHTML += `<br><div><b>length</b>: ${Math.round(length * 1000) / 1000}m</div>`;
            }
        } else {
            $.each(object.properties, function (key, value) {
                innerHTML += `<div><b>${key}</b>: ${value}</div>`;
            });
        }

        tooltip.innerHTML = innerHTML;
    } else {
        tooltip.innerHTML = '';
    }
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