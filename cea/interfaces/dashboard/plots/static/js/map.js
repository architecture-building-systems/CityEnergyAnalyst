$(document).ready(function () {
    let map = new MapClass('map-div');

    let getZone = $.get('/inputs/geojson/zone', function (data) {
        map.addLayer('zone', data);
    });

    let getDistrict = $.get('/inputs/geojson/district', function (data) {
        map.addLayer('district', data);
    });

    $.when(getZone, getDistrict).done(function () {
        map.init({extrude: true});
    });
});



