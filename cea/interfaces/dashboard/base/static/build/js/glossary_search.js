const docsUrl = "https://city-energy-analyst.readthedocs.io/en/latest/";

$("#glossary-search").autocomplete({
    serviceUrl: "/glossary_search",
    dataType: "json",
    groupBy: "category",
    forceFixPosition: true,

    transformResult: function(response) {
        return {
            suggestions: $.map(response, function(dataItem) {
                if (dataItem.SCRIPT === '-') {
                    dataItem.SCRIPT = 'input'
                }
                return {
                    value: dataItem.VARIABLE,
                    data: {
                        category: dataItem.SCRIPT,
                        description: dataItem.DESCRIPTION,
                        unit: dataItem.UNIT,
                        locator: dataItem.LOCATOR_METHOD,
                        filename: dataItem.FILE_NAME
                    }
                };
            })
        };
    },

    formatResult: function (suggestion, currentValue) {
      return `<div style="font-weight: bold">${suggestion.value}</div><div>${suggestion.data.description}</div>`+
          `<div style="font-size: 10px; font-style: italic">${suggestion.data.filename}</div>`;
    },

    onSelect: function (suggestion) {
        var type = suggestion.data.category === "input" ? "input" : "output";
        console.log(type);
        console.log(suggestion);
        window.open(`${docsUrl}${type}_methods.html?highlight=${suggestion.value}#${suggestion.data.locator.split("_").join("-")}`);
    }
});
