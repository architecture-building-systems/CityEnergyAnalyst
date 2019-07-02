const docsUrl = 'https://city-energy-analyst.readthedocs.io/en/latest/';

$('#glossary').autocomplete({
    serviceUrl: '/glossary_search',
    dataType: 'json',
    groupBy: 'category',
    width: 'flex',
    forceFixPosition: true,

    transformResult: function(response) {
        return {
            suggestions: $.map(response, function(dataItem) {
                return { value: dataItem.VARIABLE, data: { category: dataItem.SCRIPT,
                        description: dataItem.DESCRIPTION, locator: dataItem.LOCATOR_METHOD} };
            })
        };
    },

    formatResult: function (suggestion, currentValue) {
      return '<div>'+suggestion.value+'</div><small>'+suggestion.data.description+'</small>';
    },

    onSelect: function (suggestion) {
        var type = 'input';
        window.open(`${docsUrl}${type}_methods.html?highlight=${suggestion.value}#${suggestion.data.locator.split('_').join('-')}`);
    }
});
