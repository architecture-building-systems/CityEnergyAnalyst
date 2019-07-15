var map = new MapClass('map-div');

$.get('/inputs/geojson/zone', function (data) {
    map.init({data:{zone: data}});
}).then(function () {
    $.get('/inputs/geojson/district', function (data) {
        map.addLayer('district', data)
    });
});