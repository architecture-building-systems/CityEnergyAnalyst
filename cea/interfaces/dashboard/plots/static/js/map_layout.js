$(document).ready(function () {
    let zone;
    let surroundings;

    let getZone = $.get('/inputs/geojson/zone', function (data) {
        zone = data;
    });

    let getSurroundings = $.get('/inputs/geojson/surroundings', function (data) {
        surroundings = data;
    });

    $.when(getZone, getSurroundings).always(function () {
        let map = new MapClass('map-div');
        map.init({
            data:{
                zone: zone,
                surroundings: surroundings
            },
            extrude: true
        });
    });
});



