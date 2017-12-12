$(document).ready(function() {

    select_section('general');

});


function select_section(section_name) {
    $(".selected").removeClass("selected");

    $("#section-editor-" + section_name).addClass("selected");
    $("#section-list-" + section_name).addClass("selected");
}