function weather_name_clicked(weather_name) {
    $.get('weather/' + weather_name, {}, function(data){
        console.log(data);
        $('#weather-path').val(data);
    });
}