let map = new MapClass('mapid');

map.init({data: {
        zone: inputstore.getGeojson('zone'),
        district: inputstore.getGeojson('district')
    }});

map.setLayerProps('zone', {
    getFillColor: f => buildingColor(map.colors.zone, 'zone', f),
    updateTriggers: {
        getFillColor: [inputstore.getSelected.bind(inputstore), map.getNetworkType]
    },
    onClick: showProperties
});

map.setLayerProps('district', {
    getFillColor: f => buildingColor(map.colors.district,'district', f),
    updateTriggers: {
        getFillColor: inputstore.getSelected.bind(inputstore)
    },
    onClick: showProperties
});


function showProperties({object, layer}, event) {
    // console.log('object', object, layer);
    // console.log('event', event);

    let selected = inputstore.getSelected();
    let index = -1;
    if (event.srcEvent.ctrlKey && event.leftButton) {
        index = selected.findIndex(x => x === object.properties['Name']);
        if (index !== -1) {
            selected.splice(index, 1);
        } else {
            selected.push(object.properties['Name']);
        }
    } else {
        selected = [object.properties['Name']];
    }

    if (layer.id === 'district') {
        $('#district-tab').trigger('click');
    } else if (layer.id === 'zone' && $('#district-tab').hasClass('active') || !currentTable.getData().length) {
        $('#zone-tab').trigger('click');
    }

    // Select the building in the table
    currentTable.deselectRow();
    if (selected.length) {
        if (index === -1) {
            currentTable.scrollToRow(object.properties['Name']);
        }
        currentTable.selectRow(selected);
    } else {
        inputstore.setSelected(['']);
        redrawBuildings();
    }
}

function buildingColor(color, layer, object) {
    const buildingName = object.properties['Name'];
    if(inputstore.getSelected().includes(buildingName)) return [255, 255, 0, 255];

    const networkType = map.getNetworkType();
    if(networkType && layer === 'zone') {
        const connectedBuildings = map.data[networkType].properties.connected_buildings;
        if(connectedBuildings.includes(buildingName)) return map.colors[networkType];
    }

    return color
}

function redrawBuildings() {
    map.redraw();
}
