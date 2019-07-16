$(document).ready(function () {
    let zone;
    let district;
    let map = new MapClass('map-div');

    let getZone = $.get('/inputs/geojson/zone', function (data) {
        zone = data;
    });

    let getDistrict = $.get('/inputs/geojson/district', function (data) {
        district = data;
    });

    $.when(getZone, getDistrict).done(function () {
        map.init({
            data:{
                zone: zone,
                district: district
            },
            extrude: true
        });
    });
});



