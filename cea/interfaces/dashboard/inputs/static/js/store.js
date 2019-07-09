class InputStore {
    constructor(store) {
        this.tables = store['tables'];
        this.geojsons = store['geojsons'];
        this.columns = store['columns'];
        this.column_types = store['column_types'];
        this.glossary = store['glossary'];
        this.crs = store['crs'];
        this.changes = {update:{},delete:{}};

        this.data = {};
        this.geojsondata = {};
        this.selected = [];

        this.generateGeojsonData();
        this.generateData();
    }

    getColumns(table) {
        return this.columns[table]
    }

    getColumnTypes(table) {
        return this.column_types[table]
    }

    getData(table) {
        return this.data[table]
    }

    getSelected() {
        return this.selected
    }

    setSelected(array) {
        this.selected = array;
    }

    getGeojson(layer) {
        return this.geojsondata[layer]
    }

    createNewGeojson(layer) {
        this.geojsondata[layer] = JSON.parse(JSON.stringify(this.geojsondata[layer]));
    }

    getGeojsonID(layer, building) {
        var features = this.geojsondata[layer]['features'];
        return features.findIndex(x => x['properties']['Name'] === building);
    }

    // TODO: Process change here, remove change if same as default
    addChange(method, table, building, column, value) {
        var change = {[column]:value};
        if (method === 'update') {
            //Check if update is the same as default
            if (this.tables[table][building][column] === value) {
                delete this.changes[method][table][building][column];
                if (!Object.keys(this.changes[method][table][building]).length) {
                    delete this.changes[method][table][building];
                }
            } else {
                this.changes[method][table] = this.changes[method][table] || {};
                this.changes[method][table][building] = this.changes[method][table][building] || {};
                Object.assign(this.changes[method][table][building], change);
            }
            console.log(this.changes);
        }

    }

    changesToString() {
        var out = '';

        if (!$.isEmptyObject(this.changes['update'])) {
            out += '\nUPDATED:\n';
            $.each(this.changes['update'], function (table, buildings) {
                out += `${table}:\n`;
                $.each(buildings, function (name, properties) {
                    out += `${name}: `;
                    $.each(properties, function (property, value) {
                        out += `${property}:${value} `;
                    });
                    out += '\n';
                });
                out += '\n';
            });
        }

        if (!$.isEmptyObject(this.changes['delete'])) {
            out += '\nDELETED:\n';
            $.each(this.changes['delete'], function (layer, buildings) {
                out += `${layer}:\n${buildings}\n\n`;
            });
            out += '\n';
        }

        return out;
    }

    generateGeojsonData() {
        this.geojsondata = JSON.parse(JSON.stringify(this.geojsons));
    }

    generateData() {
        var _this = this;
        $.each(_this.tables, function (property, table) {
            var out = [];
            $.each(table, function (building, columns) {
                out.push({'Name': building, ...columns});
            });
            _this.data[property] = [...out];
        });
    }

    // TODO: Remove buidling from changes if being deleted
    deleteBuildings(layer, buildings) {
        this.changes['delete'][layer] = this.changes['delete'][layer] || [];
        this.changes['delete'][layer].push(...buildings);
        var _this = this;
        $.each(buildings, function (_, building) {
            if (layer === 'district') {
                _this.data[layer] = _this.data[layer].filter(x => x['Name'] !== building);
            } else {
                $.each(_this.data, function (table_name, table) {
                    if (table_name !== 'district') {
                        _this.data[table_name] = table.filter(x => x['Name'] !== building);
                    }
                });
            }
            _this.geojsondata[layer]['features'] = _this.geojsondata[layer]['features'].filter(x => x['properties']['Name'] !== building);
        });
        this.geojsondata = JSON.parse(JSON.stringify(this.geojsondata));
    }

    resetChanges() {
        this.changes = {update:{},delete:{}};
        this.generateData();
        this.generateGeojsonData();
    }

    applyChanges(data) {
        var _this = this;
        if (Object.keys(data['tables']).length) {
            $.each(data['tables'], function (table, columns) {
                _this.tables[table] = columns;
            })
        }

        if (Object.keys(data['geojsons']).length) {
            $.each(data['geojsons'], function (table, props) {
                console.log('props',props);
                if (Object.keys(props).length) {
                    _this.geojsons[table] = props;
                } else {
                    delete _this.geojsons[table];
                }

            })
        }

        this.resetChanges();
    }
}