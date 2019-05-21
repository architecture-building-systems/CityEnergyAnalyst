$('#glossary').autocomplete({
    serviceUrl: '/glossary_search',
    dataType: 'json',
    groupBy: 'category',
    width: 'flex',
    forceFixPosition: true,

    transformResult: function(response) {
        return {
            suggestions: $.map(response, function(dataItem) {
                return { value: dataItem.VARIABLE, data: { category: dataItem.CATEGORY,
                        description: dataItem.SHORT_DESCRIPTION } };
            })
        };
    },

    formatResult: function (suggestion, currentValue) {
      return '<div>'+suggestion.value+'</div><small>'+suggestion.data.description+'</small>';
    }
    // onSelect: function (suggestion) {
    //     alert('You selected: ' + suggestion.value + ', ' + suggestion.data);
    // }
});