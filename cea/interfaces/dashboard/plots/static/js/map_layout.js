$(document).ready(function () {
    let zone;
    let district;

    let getZone = $.get('/inputs/geojson/zone', function (data) {
        zone = data;
    });

    let getDistrict = $.get('/inputs/geojson/district', function (data) {
        district = data;
    });

    $.when(getZone, getDistrict).always(function () {
        let map = new MapClass('map-div');
        map.init({
            data:{
                zone: zone,
                district: district
            },
            extrude: true
        });
    });
});



