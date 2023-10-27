import os
import math
import yaml
import pandas as pd
import plotly.graph_objs as go
from PIL import Image
from dash import Dash, dcc, html
from dash.dependencies import Input, Output

import cea.config
import cea.inputlocator
from cea.plots.colors import COLORS_TO_RGB as cea_colors

# Create a Dash app
app = Dash(__name__)

class SupplySystemGraphInfo(object):
    full_category_names = {'primary': 'Heating/Cooling Components',
                           'secondary': 'Supply Components',
                           'tertiary': 'Heat Rejection Components'}
    energy_system_ids = ['0']
    supply_system_ids = {}

    _config = cea.config.Configuration()
    _locator = cea.inputlocator.InputLocator(_config.scenario)
    _category_positions = {'primary': (0.75, 0.5),
                           'secondary': (0.25, 0.75),
                           'tertiary': (0.25, 0.25)}
    _max_category_size = 0.3

    def __init__(self, energy_system_id, supply_system_id):
        # Import the energy systems structure
        self._get_data(energy_system_id, supply_system_id)

        # Define the main categories and their components
        self.categories = {category: [code for code in
                                      self._supply_system_data
                                      [self._supply_system_data["Category"]==category]
                                      ["Component_code"]]
                           for category in self._supply_system_data['Category'].unique()}
        self.components = {code: ComponentGraphInfo(code, self._supply_system_data)
                           for code in self._supply_system_data["Component_code"]}
        self.energy_flows = {energy_carrier: EnergyFlowGraphInfo(energy_carrier, self._supply_system_data)
                             for energy_carrier in self._identify_energy_carriers()}

        # Calculate the category positions, sizes, and spacings of the components
        self.cat_positions = {category: self._category_positions[category]
                              for i, category in enumerate(self.categories.keys())}
        self.cat_sizes = self._calc_category_layout()
        self.ef_anchorpoints = self._calc_energy_flow_anchorpoints()

        pass

    def _get_data(self, energy_system_id, supply_system_id):
        """ Import the supply system data """
        supply_system_file = \
            SupplySystemGraphInfo._locator.get_new_optimization_optimal_supply_system_file(energy_system_id,
                                                                                           supply_system_id)
        raw_supply_system_data = pd.read_csv(supply_system_file)
        self._supply_system_data = raw_supply_system_data[raw_supply_system_data["Capacity_kW"] != 0]

    def _identify_energy_carriers(self):
        """ Identify the unique energy carriers (ecs) present in the supply system """
        main_ecs = self._supply_system_data["Main_energy_carrier_code"]
        other_input_ecs = self._supply_system_data["Other_inputs"]
        other_output_ecs = self._supply_system_data["Other_outputs"]
        unique_ecs = pd.concat([main_ecs, other_input_ecs, other_output_ecs]).unique()
        return unique_ecs

    def _calc_category_layout(self):
        """ Calculate the positions and sizes of the categories and their components"""
        category_sizes = {}

        def round_down(num, digits):
            factor = 10.0 ** digits
            return math.floor(num * factor) / factor

        for category, components in self.categories.items():

            # Calculate the number of rows and icons per row
            number_of_components = len(components)
            number_of_rows = math.ceil(math.sqrt(number_of_components))
            icons_per_row = {row + 1: divmod(number_of_components, number_of_rows)[0] + 1
                             if divmod(number_of_components, number_of_rows)[1] >= row + 1
                             else divmod(number_of_components, number_of_rows)[0]
                             for row in range(number_of_rows)}
            max_nbr_icons_per_row = max(icons_per_row.values())

            # Calculate the size and spacing of the components
            component_icon_size = round_down(2/3 * self._max_category_size / number_of_rows, 2)
            component_icon_spacing = round_down(1/3 * self._max_category_size / (number_of_rows + 1), 2)
            max_edge_spacing = 0.1
            for code in components:
                self.components[code].size = (component_icon_size, component_icon_size)
                component_index = components.index(code) + 1
                self.components[code].calculate_position(self._category_positions[category], icons_per_row,
                                                         component_index, component_icon_size, component_icon_spacing)

            # Calculate the size of the category
            max_edge_row_width = max_nbr_icons_per_row * component_icon_size + \
                                 (max_nbr_icons_per_row - 1) * component_icon_spacing + \
                                 2 * max_edge_spacing
            max_edge_column_height = number_of_rows * component_icon_size + \
                                     (number_of_rows - 1) * component_icon_spacing + \
                                     2 * max_edge_spacing
            row_width = min([max_edge_row_width, self._max_category_size])
            column_height = min([max_edge_column_height, self._max_category_size])
            category_sizes[category] = (row_width, column_height)

        return category_sizes

    def _calc_energy_flow_anchorpoints(self):
        """ Calculate the positions of the energy flows """
        cat_flow_directions = {"primary": {("left", "top"): {"direction": "in",
                                                             "ef_category": "other_absorbers"},
                                           ("left", "bottom"): {"direction": "out",
                                                                "ef_category": "other_generators"},
                                           ("right", "full"): {"direction": "out",
                                                               "ef_category": "main_generators"}},
                               "secondary": {("left", "full"): {"direction": "in",
                                                                "ef_category": "other_absorbers"},
                                             ("right", "top"): {"direction": "out",
                                                                "ef_category": "main_generators"},
                                             ("right", "bottom"): {"direction": "out",
                                                                   "ef_category": "other_generators"}},
                               "tertiary": {("left", "top"): {"direction": "in",
                                                              "ef_category": "other_absorbers"},
                                            ("left", "bottom"): {"direction": "out",
                                                                 "ef_category": "other_generators"},
                                            ("right", "full"): {"direction": "in",
                                                                "ef_category": "main_absorbers"}}}
        cat_anchorpoints = {category: {section : {"ec_codes": []}
                                       for section, flow_directions in sections.items()}
                            for category, sections in cat_flow_directions.items()}

        # Determine the anchorpoints to be set for the primary category
        for category, sections in cat_flow_directions.items():
            # Determine the energy carriers to be included in the anchorpoints
            for section, flow_directions in sections.items():
                cat_anchorpoints[category][section] \
                    = {"ec_codes": [ec_code
                                    for ec_code, energy_flows in self.energy_flows.items()
                                    if category
                                    in energy_flows.instances[flow_directions["ef_category"]].keys()]}

            # Determine the number of anchorpoints to be set on each side
            nbr_anchorpoints_left = sum([len(cat_anchorpoints[category][section]["ec_codes"])
                                         for section in cat_anchorpoints[category].keys()
                                         if section[0] == "left"])
            nbr_anchorpoints_right = sum([len(cat_anchorpoints[category][section]["ec_codes"])
                                          for section in cat_anchorpoints[category].keys()
                                          if section[0] == "right"])

            if nbr_anchorpoints_right + nbr_anchorpoints_left == 0:
                continue

            # Calculate the positions of the anchorpoints
            for section, flow_directions in sections.items():
                if section[0] == "left":
                    x_cooridinate = self.cat_positions[category][0] - 0.5 * self.cat_sizes[category][0]
                    y_edge = 0.5 * self.cat_sizes[category][1] / nbr_anchorpoints_left
                    y_offset = self.cat_sizes[category][1] / nbr_anchorpoints_left
                elif section[0] == "right":
                    x_cooridinate = self.cat_positions[category][0] + 0.5 * self.cat_sizes[category][0]
                    y_edge = 0.5 * self.cat_sizes[category][1] / nbr_anchorpoints_right
                    y_offset = self.cat_sizes[category][1] / nbr_anchorpoints_right
                else:
                    continue

                if section[1] == "top" or section[1] == "full":
                    y_first_coordinate = self.cat_positions[category][1] + 0.5 * self.cat_sizes[category][1] - y_edge
                    y_offset = -y_offset
                elif section[1] == "bottom":
                    y_first_coordinate = self.cat_positions[category][1] - 0.5 * self.cat_sizes[category][1] + y_edge
                else:
                    continue

                cat_anchorpoints[category][section]["positions"] = [(round(x_cooridinate, 2),
                                                                     round(y_first_coordinate + nbr * y_offset, 2))
                                                                    for nbr in range(nbr_anchorpoints_right)]

        # Clear empty dict entries
        cat_anchorpoints = {category: {section: anchorpoints for section, anchorpoints in sections.items()
                                          if anchorpoints["ec_codes"]}
                            for category, sections in cat_anchorpoints.items()}
        cat_anchorpoints = {category: sections for category, sections in cat_anchorpoints.items() if sections != {}}

        # Calculate the paths of the energy flows
        [energy_flow.calculate_paths(cat_anchorpoints) for energy_flow in self.energy_flows.values() if energy_flow]

        return cat_anchorpoints

class ComponentGraphInfo(object):
    image_folder_path = os.path.join(os.path.dirname(__file__), "images")
    image_paths = {"code": image_folder_path + "image_path"}
    icon_colors = {"code": cea_colors["red"]}

    def __init__(self, code, supply_system_data):
        self.code = code
        self.type = supply_system_data[supply_system_data["Component_code"]==code]["Component_type"].values[0]
        self.capacity = str(round(supply_system_data[supply_system_data["Component_code"]==code]["Capacity_kW"].values[0],2)) + " kW"
        self.size = (0.2, 0.2)
        self.position = (0.5, 0.5)
        self.color = self.icon_colors[self.code]
        self.ef_anchorpoints = {}

        pass

    def calculate_position(self, cat_position, icons_per_row, component_nbr, component_icon_size, component_icon_spacing):
        """
        Calculates the position of the component icon in the category, i.e. the center-coordinates of the component
        icon. The exact position is calculated by:
        1. Calculating the central axis of the topmost row / the leftmost column by subtracting
            (i-1)/2 * (icon size + icon spacing) from the category's center position,
            where i is the number of rows / columns
        2. Calculating the position of the component icon with respect to that topmost row / leftmost column by adding
            (j-1) * (icon size + icon spacing) to the central axis of that topmost row / leftmost column,
            where j is the row / column the component sits in
        """

        # Calculate the row and column the component will sit in
        row = next(row for row in icons_per_row.keys() if component_nbr <= sum(list(icons_per_row.values())[:row]))
        nbr_rows = max(list(icons_per_row.keys()))
        column = component_nbr - sum(list(icons_per_row.values())[:row-1])
        columns_in_row = icons_per_row[row]

        # Calculate the position of the component (center of the component)
        x = cat_position[0] - \
            (columns_in_row - 1) * (component_icon_size + component_icon_spacing) / 2 + \
            (column - 1) * (component_icon_size + component_icon_spacing)
        y = cat_position[1] + \
            (nbr_rows - 1) * (component_icon_size + component_icon_spacing) / 2 - \
            (row - 1) * (component_icon_size + component_icon_spacing)

        self.position = (round(x, 3), round(y, 3))

class EnergyFlowGraphInfo(object):

    def __init__(self, energy_carrier, supply_system_data):
        self.energy_carrier = energy_carrier
        self.instances = self._register_instances(supply_system_data)
        self.links = self._determine_links()
        self.paths = {}

        pass

    def _register_instances(self, supply_system_data):
        """ Registers the instances where the energy carrier appears in the supply system in a dictionary """
        # Initialize the dictionary
        self.instances = {}

        # Identify components and categories that input or output the given energy carrier
        # 1. Identify the components and categories that are operated to produce the energy carrier
        generator_components = supply_system_data[supply_system_data["Main_side"] == "output"]
        main_generators_of_ec = generator_components[generator_components["Main_energy_carrier_code"] ==
                                                     self.energy_carrier]
        self.instances["main_generators"] = {category: [row["Component_code"] for index, row
                                                        in main_generators_of_ec.iterrows()
                                                        if row["Category"] == category]
                                             for category in main_generators_of_ec["Category"].unique()}

        # 2. Identify the components and categories that are operated to absorb/reject the energy carrier
        absorber_components = supply_system_data[supply_system_data["Main_side"] == "input"]
        main_absorbers_of_ec = absorber_components[absorber_components["Main_energy_carrier_code"] ==
                                                   self.energy_carrier]
        self.instances["main_absorbers"] = {category: [row["Component_code"] for index, row
                                                        in main_absorbers_of_ec.iterrows()
                                                        if row["Category"] == category]
                                             for category in main_absorbers_of_ec["Category"].unique()}

        # 3. Identify the components and categories that produce the energy carrier as a by-product
        other_generator_of_ec = supply_system_data[supply_system_data["Other_outputs"] == self.energy_carrier]
        self.instances["other_generators"] = {category: [row["Component_code"] for index, row
                                                         in other_generator_of_ec.iterrows()
                                                         if row["Category"] == category]
                                              for category in other_generator_of_ec["Category"].unique()}

        # 4. Identify the components and categories that absorb/reject the energy carrier as a by-product
        #       (or simply to be able to operate)
        other_absorbers_of_ec = supply_system_data[supply_system_data["Other_inputs"] == self.energy_carrier]
        self.instances["other_absorbers"] = {category: [row["Component_code"] for index, row
                                                        in other_absorbers_of_ec.iterrows()
                                                        if row["Category"] == category]
                                             for category in other_absorbers_of_ec["Category"].unique()}

        return self.instances

    def _determine_links(self):
        """ Determines which categories are linked by an energy flow """

        # Identify the connected energy carriers
        links = []
        for category in self.instances["main_generators"].keys():
            if category == "primary":
                links.append(("primary", "consumer"))
            elif category == "secondary" and "primary" in self.instances["other_absorbers"].keys():
                links.append(("secondary", "primary"))

        for category in self.instances["main_absorbers"].keys():
            if category == "tertiary":
                if "primary" in self.instances["other_generators"].keys():
                    links.append(("primary", "tertiary"))
                elif "secondary" in self.instances["other_generators"].keys():
                    links.append(("secondary", "tertiary"))

        for category in self.instances["other_generators"].keys():
            if category == "secondary" and "primary" in self.instances["other_absorbers"].keys():
                links.append(("secondary", "primary"))
            if category == "tertiary":
                links.append(("tertiary", "environment"))

        for category in self.instances["other_absorbers"].keys():
            if category == "primary":
                links.append(("sources", "primary"))
            elif category == "secondary":
                links.append(("sources", "secondary"))
            elif category == "tertiary":
                links.append(("sources", "tertiary"))

        return links

    def calculate_paths(self, category_anchorpoints):
        """ Calculates the paths of the energy flow """
        # Initialize the paths dictionary
        self.paths = {}

        # Identify the relevant anchorpoints
        relevant_anchorpoints = {category: {section: [anchorpoints["positions"][i]
                                                      for i in range(len(anchorpoints["ec_codes"]))
                                                      if anchorpoints["ec_codes"][i] == self.energy_carrier]
                                            for section, anchorpoints in sections.items()}
                                 for category, sections in category_anchorpoints.items()}
        relevant_anchorpoints = {category: {section: anchorpoints for section, anchorpoints in sections.items()
                                            if anchorpoints}
                                 for category, sections in relevant_anchorpoints.items()}
        relevant_anchorpoints = {category: sections for category, sections in relevant_anchorpoints.items() if sections}

        # Paths mapping
        paths_mapping = {("primary", "consumer"): (("right", "full"), "consumer"),
                         ("secondary", "primary"): (("right", "top"), ("left", "top")),
                         ("primary", "tertiary"): (("left", "bottom"), ("right", "full")),
                         ("secondary", "tertiary"): (("right", "bottom"), ("right", "full")),
                         ("tertiary", "environment"): (("left", "bottom"), "environment"),
                         ("sources", "primary"): ("sources", ("left", "top")),
                         ("sources", "secondary"): ("sources", ("left", "full")),
                         ("sources", "tertiary"): ("sources", ("left", "top"))}

        # Calculate the paths
        for link in self.links:
            new_link = tuple(link)
            # start_position = relevant_anchorpoints[link[0]][paths_mapping[link][0]]
            # end_position = relevant_anchorpoints[link[1]][paths_mapping[link][1]]
            # self.paths[link] = self._calculate_path(start_position, end_position)

        return self.paths


    def _calculate_path(self, start_position, end_position):
        """"""

def main():
    config = cea.config.Configuration()
    locator = cea.inputlocator.InputLocator(config.scenario)

    # Load the image library
    image_lib_yml = os.path.join(ComponentGraphInfo.image_folder_path, 'image_lib.yml')
    image_lib_dicts = yaml.load(open(image_lib_yml, "rb"), Loader=yaml.CLoader)
    component_images_lib = image_lib_dicts['Components']
    energy_carrier_images_lib = image_lib_dicts['EnergyCarriers']

    # Assign relevant information to the ComponentGraphInfo class variables
    ComponentGraphInfo.image_paths = {key: os.path.join(ComponentGraphInfo.image_folder_path, value['icon'])
                                      for key, value in component_images_lib.items()}
    ComponentGraphInfo.icon_colors = {key: cea_colors[value['color']]
                                      for key, value in component_images_lib.items()}

    # Load the supply system data
    des_supply_systems_dict = {}
    des_solution_folders = locator.get_new_optimization_des_solution_folders()
    for district_energy_system in des_solution_folders:
        supply_systems = locator.get_new_optimization_optimal_supply_system_ids(district_energy_system)
        des_supply_systems_dict[district_energy_system] = supply_systems

    # Assign relevant information to the SupplySystemGraphInfo class variables
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
        cat_width, cat_height = supply_system.cat_sizes[category]
        fig.add_shape(
            go.layout.Shape(
                type="rect",
                x0=x - cat_width / 2,
                y0=y - cat_height / 2,
                x1=x + cat_width / 2,
                y1=y + cat_height / 2,
                line=dict(color=cea_colors["black"], width=2),
            )
        )
        fig.add_annotation(
                x=x,
                y=y + cat_height / 2,
                text=f'{SupplySystemGraphInfo.full_category_names[category]} ({category})',
                font=dict(size=18, family="Rockwell", color="black"),
        )

    # Add component images and tooltips
    for code, component in supply_system.components.items():
        icon = Image.open(ComponentGraphInfo.image_paths[code])
        fig.add_layout_image(
            source=icon,
            xref= "x",
            yref= "y",
            x=component.position[0],
            y=component.position[1],
            xanchor="center",
            yanchor="middle",
            sizex=component.size[0],
            sizey=component.size[1],
        )
        fig.add_trace(
            go.Scatter(
                name=component.code,
                x=[component.position[0]],
                y=[component.position[1]],
                mode="markers",
                marker=dict(symbol='circle',
                            size=component.size[0]*200,
                            color=component.color,
                            ),
                text=[f"{component.type} ({component.code}) \n {component.capacity}"],
                hoverinfo='text',
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12,
                    font_family="Rockwell"
                ),
            )
        )

    # Set layout
    fig.update_layout(
        height=800,
        width=800,
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
