from dash import Dash, dcc, html

from dash.dependencies import Input, Output
import plotly.graph_objs as go

# Define the main classes and their positions
classes = {
    "Cooling/Heating Components": (0.8, 0.5),
    "Supply Components": (0.2, 0.8),
    "Heat Exhaustion Components": (0.2, 0.2),
}

# Define component data (image paths and tooltips)
component_data = [
    {"image_path": "cooling_heating.png", "position": classes["Cooling/Heating Components"],
     "tooltip": "Cooling/Heating Component 1"},
    {"image_path": "supply.png", "position": classes["Supply Components"], "tooltip": "Supply Component 1"},
    {"image_path": "heat_exhaustion.png", "position": classes["Heat Exhaustion Components"],
     "tooltip": "Heat Exhaustion Component 1"},
]

# Create a Dash app
app = Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1("Supply System Graphic"),

    dcc.Graph(
        id='supply-system-graph',
        config={'staticPlot': False}
    )
])


# Callback to update the graph
@app.callback(
    Output('supply-system-graph', 'figure'),
    Input('supply-system-graph', 'relayoutData')
)
def update_graph(relayout_data):
    # Create figure
    fig = go.Figure()

    # Add rectangles and text labels for the main classes
    for class_name, (x, y) in classes.items():
        fig.add_shape(
            go.layout.Shape(
                type="rect",
                x0=x - 0.1,
                y0=y - 0.15,
                x1=x + 0.1,
                y1=y + 0.15,
                line=dict(color="blue", width=2),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[x],
                y=[y],
                mode="text",
                text=[class_name],
                textposition="top center",
                textfont=dict(size=12, color="black"),
            )
        )

    # Add component images and tooltips
    for data in component_data:
        fig.add_layout_image(
            source=data["image_path"],
            x=data["position"][0],
            y=data["position"][1],
            xanchor="center",
            yanchor="middle",
            sizex=0.2,
            sizey=0.2,
        )
        fig.add_trace(
            go.Scatter(
                x=[data["position"][0]],
                y=[data["position"][1]],
                mode="text",
                text=[data["tooltip"]],
                textposition="middle center",
                textfont=dict(size=12, color="black"),
            )
        )

    # Set layout
    fig.update_layout(
        xaxis_range=[0, 1],
        yaxis_range=[0, 1],
        xaxis_visible=False,
        yaxis_visible=False,
    )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
