const docsUrl = "https://city-energy-analyst.readthedocs.io/en/latest/";

$("#glossary").autocomplete({
    serviceUrl: "/glossary_search",
    dataType: "json",
    groupBy: "category",
    width: "flex",
    forceFixPosition: true,

    transformResult: function(response) {
        return {
            suggestions: $.map(response, function(dataItem) {
                if (dataItem.SCRIPT === '-') {
                    dataItem.SCRIPT = 'input'
                }
                return { value: dataItem.VARIABLE, data: { category: dataItem.SCRIPT,
                        description: dataItem.DESCRIPTION, unit: dataItem.UNIT, locator: dataItem.LOCATOR_METHOD} };
            })
        };
    },

    formatResult: function (suggestion, currentValue) {
      return '<div>'+suggestion.value+'</div><small>'+suggestion.data.description+'</small>';
    },

    onSelect: function (suggestion) {
        var type = suggestion.data.category === "input" ? "input" : "output";
        console.log(type);
        console.log(suggestion);
        window.open(`${docsUrl}${type}_methods.html?highlight=${suggestion.value}#${suggestion.data.locator.split("_").join("-")}`);
    }
});
