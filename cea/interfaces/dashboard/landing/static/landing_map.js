var map;
var latlngs = [];
var temp = [];
var polygon = L.polygon(latlngs, {color: 'red'});
// var temppoly = L.polygon(temp, {color: 'red'});
var latlon = $("#coordinates").val().split(/[,\s]/);
console.log(latlon)

// const lassoResult = document.querySelector("#lassoResult");

map = L.map('mapid').setView([latlon[0], latlon[latlon.length-1]], 11);

L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png',
    {attribution: "Data copyright OpenStreetMap contributors"}).addTo(map);

map.on('click', onMapClick);

	// Not sure whether to add hover functionality
	// map.on('mousemove', onMapHover);

function goToLocation() {
	var latlon = $("#coordinates").val().split(/[,\s]/);
	map.setView([latlon[0], latlon[latlon.length-1]], 11);
}

function onMapClick(e) {
    latlngs.push(e.latlng)
	map.removeLayer(polygon)
	polygon = L.polygon(latlngs, {color: 'red'})
	polygon.addTo(map);

	// if (typeof latlngs !== 'undefined') {
  	// 	lassoResult.innerHTML = latlngs.toString();
	// }
}

function onMapHover(e) {
	if (latlngs.length !== 0) {
		map.removeLayer(temppoly)
		temp = [...latlngs]
		temp.push(e.latlng)
		temppoly = L.polygon(temp, {color: 'red'})
		temppoly.addTo(map);
	}
}

function removePoly() {
	// lassoResult.innerHTML = "";
	latlngs = [];
	map.removeLayer(polygon);
	// temp = [];
	// map.removeLayer(temppoly);
}

function createPoly(scenario) {
	var r = confirm("Are you sure you want to create the zone file?");

	if (r === true) {
		// TODO: Check if polygon is empty
		var json = polygon.toGeoJSON();
		L.extend(json.properties, polygon.properties);

		$.ajax({
			type: 'POST',
			contentType: 'application/json',
			data: JSON.stringify(json),
			dataType: 'json',
			url: `http://localhost:5050/landing/create-poly?scenario=${scenario}`,
			success: function(response) {
  				if (response.redirect) {
    				window.location.href = response.redirect;
  				}
			},
			error: function(error) {
				console.log(error);
			}
		});
	}
}

$(document)
