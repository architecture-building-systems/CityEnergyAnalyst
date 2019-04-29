//var mymap = L.map('mapid').setView([51.505, -0.09], 13);
//L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png',
//        {attribution: "Data copyright OpenStreetMap contributors"}).addTo(map);
//}).addTo(mymap);

var map;
var latlngs = [];
var polygon = L.polygon(latlngs, {color: 'red'});

const lassoResult = document.querySelector("#lassoResult");

map = L.map('mapid').setView([1.289440, 103.849983], 12);

	L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png',
            {attribution: "Data copyright OpenStreetMap contributors"}).addTo(map);

	map.on('click', onMapClick);

$(document).ready(function() {
});

function onMapClick(e) {
    latlngs.push(e.latlng)
	// L.polyline(latlngs, {color: 'red'}).addTo(map);
	map.removeLayer(polygon)
	polygon = L.polygon(latlngs, {color: 'red'})
	polygon.addTo(map);
    console.log(latlngs)
	if (typeof latlngs !== 'undefined') {
  		lassoResult.innerHTML = latlngs.toString();
	}
}

function removePoly() {
	latlngs = [];
	map.removeLayer(polygon)
}

function createPoly() {
	// TODO: Check if polygon is empty
	var json = polygon.toGeoJSON();
	L.extend(json.properties, polygon.properties);

	$.ajax({
		type: 'POST',
		contentType: 'application/json',
		data: JSON.stringify(json),
		dataType: 'json',
		url: 'http://localhost:5050/landing/create_poly',
		success: function (e) {
			console.log(e);
		},
		error: function(error) {
			console.log(error);
		}
	});
}