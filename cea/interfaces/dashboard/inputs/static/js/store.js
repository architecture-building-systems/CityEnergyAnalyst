class InputStore {
    constructor(store) {
        this.tables = store['tables'];
        this.geojsons = store['geojsons'];
        this.columns = store['columns'];
        this.column_types = store['column_types'];
        this.changes = {};

        this.data = {};
        this.selected = [];
    }

    getColumns(table) {
        return this.columns[table]
    }

    getColumnTypes(table) {
        return this.column_types[table]
    }

    getData(table) {
        var _this = this;
        if (!Object.keys(_this.data).length) {
            $.each(_this.tables, function (property, table) {
                var out = [];
                $.each(table, function (building, columns) {
                    out.push({'Name': building, ...columns});
                });
                _this.data[property] = [...out];
            });
        }
        return this.data[table]
    }

    getSelected() {
        return this.selected
    }

    setSelected(array) {
        this.selected = array;
    }

    getGeojson(type) {
        return this.geojsons[type]
    }

    // TODO: Process change here, remove change if same as default
    addChange(change) {

    }
}