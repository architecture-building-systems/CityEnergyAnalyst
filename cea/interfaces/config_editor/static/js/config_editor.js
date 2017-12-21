$(document).ready(function() {

    $("#list-general-list").tab("show");

});

/**
 * Calls back to Backend.save_section after collecting the values from all the controls.
 * @param section
 */
function save_section_js(section) {
    alert(section);
}