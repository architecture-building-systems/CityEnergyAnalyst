import os
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

import cea.config
import cea.inputlocator

# Create a Dash app
app = Dash(__name__)

class SupplySystemGraphInfo(object):
    energy_system_ids = ['0']
    supply_system_ids = {}

    _config = cea.config.Configuration()
    _locator = cea.inputlocator.InputLocator(_config.scenario)

    def __init__(self, energy_system_id, supply_system_id):
        # Import the energy systems structure
        self._get_data(energy_system_id, supply_system_id)

        # Define the main categories and their positions
        self.categories = {category: [code for code in
                                      self._supply_system_data
                                      [self._supply_system_data["Component_category"]==category]
                                      ["Component_code"]]
                           for category in self._supply_system_data['Component_category'].unique()}
        self.cat_positions = {category: (0.2, 0.8 - 0.2 * i) for i, category in enumerate(self.categories.keys())}
        self.components = {code: ComponentGraphInfo(code, self._supply_system_data)
                           for code in self._supply_system_data["Component_code"]}

        pass

    def _get_data(self, energy_system_id, supply_system_id):
        supply_system_file = \
            SupplySystemGraphInfo._locator.get_new_optimization_optimal_supply_system_file(energy_system_id,
                                                                                           supply_system_id)
        self._supply_system_data = pd.read_csv(supply_system_file)

class ComponentGraphInfo(object):
    image_folder_path = "C:/Users/nimathia/Documents/GitHub/CityEnergyAnalyst/CityEnergyAnalyst/cea/plots/optimization_new/images/"
    image_paths = {"AC1": image_folder_path + "dxChiller_icon.png",
                   "AC2": image_folder_path + "dxChiller_icon.png",
                   "CH1": image_folder_path + "vcChiller_icon.png",
                   "CH2": image_folder_path + "vcChiller_icon.png",
                   "ACH1": image_folder_path + "absorptionChiller_icon.png",
                   "ACH2": image_folder_path + "absorptionChiller_icon.png",
                   "ACH3": image_folder_path + "absorptionChiller_icon.png",
                   "BO1": image_folder_path + "boiler_icon.png",
                   "BO2": image_folder_path + "boiler_icon.png",
                   "BO3": image_folder_path + "boiler_icon.png",
                   "CT1": image_folder_path + "coolingTower_icon.png",
                   "CT2": image_folder_path + "coolingTower_icon.png",
                   "HP1": image_folder_path + "dxChiller_icon.png",
                   "HP2": image_folder_path + "dxChiller_icon.png",
                   "HP3": image_folder_path + "dxChiller_icon.png",
                   "OEHR1": image_folder_path + "generator_icon.png",
                   "OEHR2": image_folder_path + "generator_icon.png",
                   "FORC1": image_folder_path + "generator_icon.png",
                   "CCGT1": image_folder_path + "gasTurbine_icon.png",
                   "TES1": image_folder_path + "storage_icon.png",
                   }
    def __init__(self, code, supply_system_data):
        self.code = code
        self.type = supply_system_data[supply_system_data["Component_code"]==code]["Component_type"].values[0]
        self.capacity = str(round(supply_system_data[supply_system_data["Component_code"]==code]["Capacity_kW"].values[0],2)) + " kW"
        self.position = (0.8, 0.5)
        pass

def main():
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    des_supply_systems_dict = {}
    des_solution_folders = locator.get_new_optimization_des_solution_folders()
    for district_energy_system in des_solution_folders:
        supply_systems = locator.get_new_optimization_optimal_supply_system_ids(district_energy_system)
        des_supply_systems_dict[district_energy_system] = supply_systems

    SupplySystemGraphInfo.energy_system_ids = des_solution_folders
    SupplySystemGraphInfo.supply_system_ids = des_supply_systems_dict

    update_graph(des_solution_folders[0], des_supply_systems_dict[des_solution_folders[0]][0])

    return None

def set_up_graph(dash_application=app):
    # Define the layout of the app
    dash_application.layout = html.Div([
        html.H1("Supply System Graphic"),

        dcc.Dropdown(options=SupplySystemGraphInfo.energy_system_ids, id='energy-system-id',
                     placeholder="Select an optimal energy system"),

        dcc.Dropdown(options=SupplySystemGraphInfo.supply_system_ids, id='supply-system-id',
                     placeholder="Select a supply system"),

        dcc.Graph(
            id='supply-system-graph',
            config={'staticPlot': False}
        )
    ])

    return dash_application

#Update the supply-system-id dropdown menu
@app.callback(
    Output('supply-system-id', 'options'),
    [Input('energy-system-id', 'value')]
)
def update_supply_system_dropdown(energy_system_id):
    return [i for i in SupplySystemGraphInfo.supply_system_ids[energy_system_id]]


# Callback to update the graph
@app.callback(
    Output('supply-system-graph', 'figure'),
    [Input('energy-system-id', 'value'), Input('supply-system-id', 'value')]
)
def update_graph(energy_system_id, supply_system_id):
    # Define a corresponding supply system graph info object
    supply_system = SupplySystemGraphInfo(energy_system_id, supply_system_id)

    # Create figure
    fig = go.Figure()

    # Add rectangles and text labels for the main classes
    for category in supply_system.categories.keys():
        x, y = supply_system.cat_positions[category]
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
                text=[category],
                textposition="top center",
                textfont=dict(size=12, color="black"),
            )
        )

    # Add component images and tooltips
    for code, component in supply_system.components.items():
        fig.add_layout_image(
            source=ComponentGraphInfo.image_paths[code],
            x=component.position[0],
            y=component.position[1],
            xanchor="center",
            yanchor="middle",
            sizex=0.2,
            sizey=0.2,
        )
        fig.add_trace(
            go.Scatter(
                x=[component.position[0]],
                y=[component.position[1]],
                mode="text",
                text=[component.type + "\n" + component.capacity],
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
    main()
    app = set_up_graph(app)
    app.run_server(debug=True)
