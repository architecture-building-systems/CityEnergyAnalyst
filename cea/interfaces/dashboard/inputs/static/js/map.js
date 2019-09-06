let map = new MapClass('mapid');

map.init({data: {
        zone: inputstore.getGeojson('zone'),
        district: inputstore.getGeojson('district')
    }});

map.setLayerProps('zone', {
    getFillColor: f => buildingColor(defaultColors.zone, f),
    updateTriggers: {
        getFillColor: inputstore.getSelected()
    },
    onClick: showProperties
});

map.setLayerProps('district', {
    getFillColor: f => buildingColor(defaultColors.district, f),
    updateTriggers: {
        getFillColor: inputstore.getSelected()
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

function buildingColor(color, object) {
    let selected = inputstore.getSelected();
    for(let i = 0; i < selected.length; i++){
        if (object.properties['Name'] === selected[i]) {
            return [255, 255, 0, 255]
        }
    }
    return color
}

function redrawBuildings() {
    map.setLayerProps('zone', {
        updateTriggers: {
            getFillColor: inputstore.getSelected()
        }
    });
    map.setLayerProps('district', {
        updateTriggers: {
            getFillColor: inputstore.getSelected()
        }
    });

    map.redrawBuildings({
        zone: inputstore.getGeojson('zone'),
        district: inputstore.getGeojson('district')
    });
}
