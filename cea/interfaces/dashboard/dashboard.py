from __future__ import division

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd

import cea.config
import cea.inputlocator

from cea.plots.variable_naming import COLOR

config = cea.config.Configuration()
locator = cea.inputlocator.InputLocator(config.scenario)

print('dashboard: reading data')
zone_building_names = locator.get_zone_building_names()
data_frames = {building: pd.read_csv(locator.get_demand_results_file(building)).set_index("DATE")
               for building in zone_building_names}
print('dashboard: building interface')

app = dash.Dash()

app.layout = html.Div([
    html.Div([

        html.Div([
            dcc.Dropdown(
                id='zone-building-name',
                options=[{'label': i, 'value': i} for i in zone_building_names],
                value=zone_building_names[0]
            ),
        ],
            style={'width': '49%', 'display': 'inline-block'}),

    ], style={
        'borderBottom': 'thin lightgrey solid',
        'backgroundColor': 'rgb(250, 250, 250)',
        'padding': '10px 5px'
    }),

    html.Div([
        dcc.Graph(
            id='load-curve',
        )
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
    html.Div([
        dcc.Graph(
            id='load-duration-curve',
        )
    ], style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'}),
])


@app.callback(
    dash.dependencies.Output('load-curve', 'figure'),
    [dash.dependencies.Input('zone-building-name', 'value') ])
def update_load_curve(building_name):
    print('updating for %s' % building_name)
    df = data_frames[building_name]
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh", "T_int_C", "T_ext_C"]
    data = []
    for field in analysis_fields:
        y = df[field].values
        if field in ["T_int_C", "T_ext_C"]:
            trace = go.Scatter(x=df.index, y=y, name=field.split('_C', 1)[0], yaxis='y2', opacity=0.2)
        else:
            trace = go.Scatter(x=df.index, y=y, name=field.split('_', 1)[0],
                               marker=dict(color=COLOR[field.split('_', 1)[0]]))
        data.append(trace)

    return {
        'data': data,
        'layout': go.Layout(
            title="Load Curve for Building " + building_name,
            xaxis={
                'rangeselector': {
                    'buttons': [
                        dict(count=1, label='1d', step='day', stepmode='backward'),
                        dict(count=1, label='1w', step='week', stepmode='backward'),
                        dict(count=1, label='1m', step='month', stepmode='backward'),
                        dict(count=6, label='6m', step='month', stepmode='backward'),
                        dict(count=1, label='1y', step='year', stepmode='backward'),
                        dict(step='all')
                    ]
                },
                'rangeslider': {},
                'type': 'date',
            },
            yaxis={
                'title': 'Load [kW]',
            },
            yaxis2={
                'title': 'Temperature [C]',
                'overlaying': 'y',
                'side': 'right'
            },
            margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
            height=450,
            hovermode='closest'
        )
    }


# only compute this once
duration = range(8760)
x = [(a - min(duration)) / (max(duration) - min(duration)) * 100 for a in duration]

@app.callback(
    dash.dependencies.Output('load-duration-curve', 'figure'),
    [dash.dependencies.Input('zone-building-name', 'value') ])
def update_load_duration_curve(building_name):
    analysis_fields = ["Ef_kWh", "Qhsf_kWh", "Qwwf_kWh", "Qcsf_kWh"]
    data = []
    data_frame = data_frames[building_name]
    for field in analysis_fields:
        df = data_frame.sort_values(by=field, ascending=False)
        y = df[field].values
        trace = go.Scatter(x=x, y=y, name=field.split('_', 1)[0], fill='tozeroy', opacity=0.8,
                           marker=dict(color=COLOR[field.split('_', 1)[0]]))
        print('field: %s - y: %s' % (field, y))
        print(trace)
        data.append(trace)
    return {
        'data': data,
        'layout': go.Layout(
            #title="Load Duration Curve for Building %s" % building_name,
            xaxis={
                'title': 'Duration Normalized [%]',
                'domain': [0, 1]
            },
            yaxis={
                'title': 'Load [kW]',
                'domain': [0.0, 0.7]
            },
            margin={'l': 40, 'b': 30, 't': 10, 'r': 0},
            height=450,
            hovermode='closest'
        )
    }

if __name__ == '__main__':
    app.run_server()
