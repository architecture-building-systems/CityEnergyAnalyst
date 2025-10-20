import os
import re
import math
import yaml
import pandas as pd
import plotly.graph_objs as go
from PIL import Image

import cea.config
import cea.inputlocator
from cea.plots.colors import COLORS_TO_RGB as cea_colors

class SupplySystemGraphInfo(object):
    full_category_names = {'primary': 'Heating/Cooling Components',
                           'secondary': 'Supply Components',
                           'tertiary': 'Heat Rejection Components'}

    _category_positions = {'primary': (0.75, 0.5),
                           'secondary': (0.25, 0.75),
                           'tertiary': (0.25, 0.25)}
    _max_category_size = 0.3

    def __init__(self, energy_system_id, supply_system_id, locator):
        # Store the locator as an instance variable
        self._locator = locator

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
        self.sinks_and_sources = {side: SourceAndSinkGraphInfo.position_icons(side, sources_or_sinks)
                                  for side, sources_or_sinks in self._idenfify_sinks_and_sources().items()}
        self.consumer = ConsumerGraphInfo(supply_system_id)

        # Calculate the category positions, sizes, and spacings of the components
        self.cat_positions = {category: self._category_positions[category]
                              for i, category in enumerate(self.categories.keys())}
        self.cat_sizes = self._calc_category_layout()
        self.ef_anchorpoints = self._calc_energy_flow_anchorpoints()

        pass

    def _get_data(self, energy_system_id, supply_system_id):
        """ Import the supply system data """
        supply_system_file = \
            self._locator.get_new_optimization_optimal_supply_system_file(energy_system_id,
                                                                          supply_system_id)
        raw_supply_system_data = pd.read_csv(supply_system_file)
        for column in ["Main_energy_carrier_code", "Other_inputs", "Other_outputs"]:
            raw_supply_system_data[column] = pd.Series([ecs.split(', ')
                                                        for ecs in raw_supply_system_data[column].array
                                                        if isinstance(ecs, str)])
        self._supply_system_data = raw_supply_system_data[raw_supply_system_data["Capacity_kW"] != 0]

    def _identify_energy_carriers(self):
        """ Identify the unique energy carriers (ecs) present in the supply system """
        all_ecs = []
        for column in ["Main_energy_carrier_code", "Other_inputs", "Other_outputs"]:
            column_ecs = [ec for ecs in self._supply_system_data[column].array if isinstance(ecs, list) for ec in ecs]
            all_ecs += column_ecs
        unique_ecs = list(set(all_ecs))
        return unique_ecs

    def _idenfify_sinks_and_sources(self):
        """ Identify the sinks and sources of the supply system """
        ec_cat_to_sinks = [re.sub(r"\d+", "_", energy_carrier)
                           for energy_carrier, energy_flow in self.energy_flows.items()
                           if any([link[1] == 'sinks' for link in energy_flow.links])]
        ec_cat_from_sources = [re.sub(r"\d+", "_", energy_carrier)
                               for energy_carrier, energy_flow in self.energy_flows.items()
                               if any([link[0] == 'sources' for link in energy_flow.links])]

        sinks_and_sources = {'sinks': [{'code': SourceAndSinkGraphInfo.ec_to_code_mapping['Sinks'][ec_cat],
                                        'associated_ec': ec_cat}
                                       for ec_cat in ec_cat_to_sinks],
                             'sources': [{'code': SourceAndSinkGraphInfo.ec_to_code_mapping['Sources'][ec_cat],
                                          'associated_ec': ec_cat}
                                         for ec_cat in ec_cat_from_sources]}

        return sinks_and_sources

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
                                                             "linked_categories": ["sources", "secondary"]},
                                           ("left", "bottom"): {"direction": "out",
                                                                "linked_categories": ["tertiary", "sinks"]},
                                           ("right", "full"): {"direction": "out",
                                                               "linked_categories": ["consumer"]}},
                               "secondary": {("left", "top"): {"direction": "in",
                                                               "linked_categories": ["sources"]},
                                             ("left", "bottom"): {"direction": "out",
                                                                  "linked_categories": ["sinks"]},
                                             ("right", "top"): {"direction": "out",
                                                                "linked_categories": ["primary"]},
                                             ("right", "bottom"): {"direction": "out",
                                                                   "linked_categories": ["tertiary"]}},
                               "tertiary": {("left", "top"): {"direction": "in",
                                                              "linked_categories": ["sources"]},
                                            ("left", "bottom"): {"direction": "out",
                                                                 "linked_categories": ["sinks"]},
                                            ("right", "full"): {"direction": "in",
                                                               "linked_categories": ["primary", "secondary"]}}}
        cat_anchorpoints = {category: {section : {"ec_codes": []}
                                       for section, flow_directions in sections.items()}
                            for category, sections in cat_flow_directions.items()}

        # Determine the anchorpoints to be set for each category
        for category, sections in cat_flow_directions.items():
            # Determine the energy carriers to be included in the anchorpoints
            for section, flow_directions in sections.items():
                if flow_directions['direction'] == "in":
                    ef_links = [tuple([link_cat, category]) for link_cat in flow_directions['linked_categories']]
                else:
                    ef_links = [tuple([category, link_cat]) for link_cat in flow_directions['linked_categories']]
                cat_anchorpoints[category][section] \
                    = {"ec_codes": [ec_code
                                    for ec_code, energy_flows in self.energy_flows.items()
                                    if any([link in ef_links for link in energy_flows.links])]}

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
            for section in sections.keys():
                if section[0] == "left" and nbr_anchorpoints_left > 0:
                    x_cooridinate = self.cat_positions[category][0] - 0.5 * self.cat_sizes[category][0]
                    y_edge = 0.5 * self.cat_sizes[category][1] / nbr_anchorpoints_left
                    y_offset = self.cat_sizes[category][1] / nbr_anchorpoints_left
                elif section[0] == "right" and nbr_anchorpoints_right > 0:
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

                nbr_anchorpoints_in_section = len(cat_anchorpoints[category][section]["ec_codes"])
                cat_anchorpoints[category][section]["positions"] = [(round(x_cooridinate, 2),
                                                                     round(y_first_coordinate + nbr * y_offset, 2))
                                                                    for nbr in range(nbr_anchorpoints_in_section)]

        # Clear empty dict entries
        cat_anchorpoints = {category: {section: anchorpoints for section, anchorpoints in sections.items()
                                          if anchorpoints["ec_codes"]}
                            for category, sections in cat_anchorpoints.items()}
        cat_anchorpoints = {category: sections for category, sections in cat_anchorpoints.items() if sections != {}}

        # Calculate exact anchorpoints for sources and sinks
        ecs_from_sources = [energy_flow.energy_carrier for energy_flow in self.energy_flows.values()
                            if any([link[0] == 'sources' for link in energy_flow.links])]
        ecs_from_specific_sources = {source.code: [ec for ec in ecs_from_sources
                                                   if re.sub(r"\d+", "_", ec) == source.ec_category_code]
                                     for source in self.sinks_and_sources['sources'].values()}
        [source.set_anchorpoints(ecs_from_specific_sources[source.code])
         for source in self.sinks_and_sources['sources'].values()]

        ecs_to_sinks = [energy_flow.energy_carrier for energy_flow in self.energy_flows.values()
                        if any([link[1] == 'sinks' for link in energy_flow.links])]
        ecs_to_specific_sinks = {sink.code: [ec for ec in ecs_to_sinks
                                             if re.sub(r"\d+", "_", ec) == sink.ec_category_code]
                                 for sink in self.sinks_and_sources['sinks'].values()}
        [sink.set_anchorpoints(ecs_to_specific_sinks[sink.code])
         for sink in self.sinks_and_sources['sinks'].values()]

        # Calculate exact anchorpoints for consumer
        ecs_to_consumer = [energy_flow.energy_carrier for energy_flow in self.energy_flows.values()
                           if any([link[1] == 'consumer' for link in energy_flow.links])]
        self.consumer.set_anchorpoints(ecs_to_consumer)


        # Calculate the paths of the energy flows
        [energy_flow.calculate_paths(cat_anchorpoints, self)
         for energy_flow in self.energy_flows.values() if energy_flow]

        return cat_anchorpoints

class ComponentGraphInfo(object):
    image_folder_path = os.path.join(os.path.dirname(__file__), "images")
    component_image_folder = os.path.join(image_folder_path, "component_img")
    image_paths = {"code": image_folder_path + "image_path"}
    icon_colors = {"code": cea_colors["red"]}

    def __init__(self, code, supply_system_data):
        self.code = code
        self.type = supply_system_data[supply_system_data["Component_code"]==code]["Component_type"].values[0]
        self.capacity = str(round(supply_system_data[supply_system_data["Component_code"]==code]["Capacity_kW"].values[0],2)) + " kW"
        self.size = (0.2, 0.2)
        self.position = (0.5, 0.5)
        self.color = self.icon_colors.get(self.code, self.icon_colors.get("unknown", cea_colors["grey"]))  # Use unknown component color as fallback
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

class SourceAndSinkGraphInfo(object):

    _image_folder_path = os.path.join(os.path.dirname(__file__), "images")
    sources_and_sinks_image_folder = os.path.join(_image_folder_path, "sources_and_sinks_img")
    ec_to_code_mapping = {"Consumers": {"energy_carrier_category": "icon_code"}}
    image_paths = {"icon_code": sources_and_sinks_image_folder + "icon_file_name"}
    _max_space_for_icons = 0.4
    _max_icon_size = 0.2
    _border_distance = - 0.1

    def __init__(self, code, energy_carrier_category_code):
        self.code = code
        self.ec_category_code = energy_carrier_category_code
        self.size = (0.2, 0.2)
        self.position = (0.5, 0.5)
        self.anchorpoints = {}

    @staticmethod
    def position_icons(side, sources_or_sinks):
        # Calculate the upper and lower bound of the area where the sink/source icons can be placed
        if side == "sources":
            y_upper_bound = 1 - (0.5 - SourceAndSinkGraphInfo._max_space_for_icons) / 2
        elif side == "sinks":
            y_upper_bound = 0.5 - (0.5 - SourceAndSinkGraphInfo._max_space_for_icons) / 2
        else:
            raise ValueError("side must be either 'sources' or 'sinks'")

        # Calculate the size of the icons
        nbr_icons = len(sources_or_sinks)
        icons = {}
        if nbr_icons == 0:
            return icons
        else:
            calculated_icon_size = 2/3 * SourceAndSinkGraphInfo._max_space_for_icons / nbr_icons
            icon_spacing = 1/3 * SourceAndSinkGraphInfo._max_space_for_icons / nbr_icons
            icon_size = round(min(nbr_icons * calculated_icon_size + (nbr_icons - 1) * icon_spacing,
                                  SourceAndSinkGraphInfo._max_icon_size), 2)

        # Calculate the position of the icons and create their corresponding SourceAndSinkGraphInfo objects
        for i, source_or_sink in enumerate(sources_or_sinks):
            icon = SourceAndSinkGraphInfo(source_or_sink["code"], source_or_sink["associated_ec"])
            icon.size = (icon_size, icon_size)

            # Calculate the position of the icon
            x = SourceAndSinkGraphInfo._border_distance - icon_size / 2
            y = y_upper_bound - (icon_size + icon_spacing) * i - icon_size / 2
            icon.position = (round(x, 3), round(y, 3))

            icons[icon.code] = icon

        return icons

    def set_anchorpoints(self, ec_code_list):
        """ Set anchorpoints for each individual energy carrier drawn from the source / absorbed by the sink """
        for i, ec_code in enumerate(ec_code_list):
            x = self.position[0] + self.size[0] / 2
            y_spacing = self.size[1] / (len(ec_code_list) + 1)
            y = self.position[1] - self.size[1] / 2 + y_spacing * (i + 1)
            self.anchorpoints[ec_code] = (round(x, 3), round(y, 3))

class ConsumerGraphInfo(object):

    image_folder_path = os.path.join(os.path.dirname(__file__), "images")
    consumer_image_folder = os.path.join(image_folder_path, "consumer_img")
    image_paths = {"icon_code": consumer_image_folder + "icon_file_name"}

    def __init__(self, supply_system_id):
        self.supply_system_id = supply_system_id
        self.category = self._determine_category()
        self.size = (0.2, 0.2)
        self.position = (1.2, 0.5)
        self.anchorpoints = {}

    def _determine_category(self):
        """ Determine if the supply system id corresponds to a building or a district """
        if re.match(r"N\d{4}", self.supply_system_id):
            return "district"
        else:
            return "building"

    def set_anchorpoints(self, ec_code_list):
        """ Set anchorpoints for each individual energy carrier delivered to the consumer """
        for i, ec_code in enumerate(ec_code_list):
            x = self.position[0] - self.size[0] / 2
            y_spacing = self.size[1] / (len(ec_code_list) + 1)
            y = self.position[1] - self.size[1] / 2 + y_spacing * (i + 1)
            self.anchorpoints[ec_code] = (round(x, 3), round(y, 3))


class EnergyFlowGraphInfo(object):

    # Paths mapping
    paths_mapping = {("primary", "consumer"): (("right", "full"), "consumer"),
                     ("secondary", "primary"): (("right", "top"), ("left", "top")),
                     ("primary", "tertiary"): (("left", "bottom"), ("right", "full")),
                     ("secondary", "tertiary"): (("right", "bottom"), ("right", "full")),
                     ("tertiary", "sinks"): (("left", "bottom"), "sinks"),
                     ("secondary", "sinks"): (("left", "bottom"), "sinks"),
                     ("sources", "primary"): ("sources", ("left", "top")),
                     ("sources", "secondary"): ("sources", ("left", "top")),
                     ("sources", "tertiary"): ("sources", ("left", "top"))}
    colors_and_hues = {}

    def __init__(self, energy_carrier, supply_system_data):
        self.energy_carrier = energy_carrier
        self.instances = self._register_instances(supply_system_data)
        self.color = self._assign_color()
        self.hue = self._assign_hue()
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
        indexes_of_main_generators = [i for i, main_ecs in generator_components["Main_energy_carrier_code"].items()
                                      if isinstance(main_ecs, list) and self.energy_carrier in main_ecs]
        main_generators_of_ec = generator_components.loc[indexes_of_main_generators, :]
        self.instances["main_generators"] = {category: [row["Component_code"] for index, row
                                                        in main_generators_of_ec.iterrows()
                                                        if row["Category"] == category]
                                             for category in main_generators_of_ec["Category"].unique()}

        # 2. Identify the components and categories that are operated to absorb/reject the energy carrier
        absorber_components = supply_system_data[supply_system_data["Main_side"] == "input"]
        indexes_of_main_absorbers = [i for i, main_ecs in absorber_components["Main_energy_carrier_code"].items()
                                     if isinstance(main_ecs, list) and self.energy_carrier in main_ecs]
        main_absorbers_of_ec = absorber_components.loc[indexes_of_main_absorbers, :]
        self.instances["main_absorbers"] = {category: [row["Component_code"] for index, row
                                                        in main_absorbers_of_ec.iterrows()
                                                        if row["Category"] == category]
                                             for category in main_absorbers_of_ec["Category"].unique()}

        # 3. Identify the components and categories that produce the energy carrier as a by-product
        indexes_of_other_generators = [i for i, ecs in supply_system_data["Other_outputs"].items()
                                       if isinstance(ecs, list) and self.energy_carrier in ecs]
        other_generators_of_ec = supply_system_data.loc[indexes_of_other_generators, :]
        self.instances["other_generators"] = {category: [row["Component_code"] for index, row
                                                         in other_generators_of_ec.iterrows()
                                                         if row["Category"] == category]
                                              for category in other_generators_of_ec["Category"].unique()}

        # 4. Identify the components and categories that absorb/reject the energy carrier as a by-product
        #       (or simply to be able to operate)
        indexes_of_other_absorbers = [i for i, ecs in supply_system_data["Other_inputs"].items()
                                      if isinstance(ecs, list) and self.energy_carrier in ecs]
        other_absorbers_of_ec = supply_system_data.loc[indexes_of_other_absorbers, :]
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
            if category == "secondary":
                if "primary" in self.instances["other_absorbers"].keys():
                    links.append(("secondary", "primary"))
                else:
                    links.append(("secondary", "sinks"))
            if category == "tertiary":
                links.append(("tertiary", "sinks"))

        for category in self.instances["other_absorbers"].keys():
            if category == "primary" and "secondary" not in self.instances["main_generators"].keys():
                links.append(("sources", "primary"))
            elif category == "secondary":
                links.append(("sources", "secondary"))
            elif category == "tertiary":
                links.append(("sources", "tertiary"))

        return links

    def _assign_color(self):
        """ Assigns a color to the energy carrier """
        return cea_colors[self.colors_and_hues[self.energy_carrier]["color"]]

    def _assign_hue(self):
        """ Assigns a hue to the energy carrier """
        return cea_colors[self.colors_and_hues[self.energy_carrier]["hue"]]

    def calculate_paths(self, category_anchorpoints, supply_system):
        """ Calculates the paths of the energy flow """
        # Initialize the paths dictionary
        self.paths = {}

        # Identify the relevant anchorpoints (and remove empty/irrelevant sections from the dictionary)
        relevant_cat_anchorpoints = {category: {section: [anchorpoints["positions"][i]
                                                          for i, ec in enumerate(anchorpoints["ec_codes"])
                                                          if ec == self.energy_carrier]
                                                for section, anchorpoints in sections.items()}
                                     for category, sections in category_anchorpoints.items()}
        relevant_cat_anchorpoints = {category: {section: anchorpoint for section, anchorpoint in sections.items()
                                                if anchorpoint}
                                     for category, sections in relevant_cat_anchorpoints.items()}
        relevant_cat_anchorpoints = {category: sections for category, sections in relevant_cat_anchorpoints.items()
                                     if sections}

        # Identify relevant sources and sinks and add their anchorpoints to the list of relevant anchorpoints
        relevant_sources = [source for source in supply_system.sinks_and_sources['sources'].values()
                            if self.energy_carrier in source.anchorpoints.keys()]
        relevant_sinks = [sink for sink in supply_system.sinks_and_sources['sinks'].values()
                          if self.energy_carrier in sink.anchorpoints.keys()]

        relevant_source_anchorpoints = {source.code: source.anchorpoints[self.energy_carrier] for source in relevant_sources}
        relevant_sink_anchorpoints = {sink.code: sink.anchorpoints[self.energy_carrier] for sink in relevant_sinks}

        # Calculate the paths
        for link in self.links:
            # Determine the start and end positions of the path
            if link[0] == "sources":
                start_position = list(relevant_source_anchorpoints.values())
            else:
                start_position = relevant_cat_anchorpoints[link[0]][EnergyFlowGraphInfo.paths_mapping[link][0]]

            if link[1] == "sinks":
                end_position = list(relevant_sink_anchorpoints.values())
            elif link[1] == "consumer":
                end_position = supply_system.consumer.anchorpoints[self.energy_carrier]
            else:
                end_position = relevant_cat_anchorpoints[link[1]][EnergyFlowGraphInfo.paths_mapping[link][1]]

            self.paths[link] = self._calculate_path(start_position, end_position)

        return self.paths


    def _calculate_path(self, start_position, end_position):
        """ Calculates the path of the energy flow between two anchorpoints """
        # If the start or end positions come as a list (i.e. multiple anchorpoints), take only the first one
        if isinstance(start_position, list):
            start_position = start_position[0]
        if isinstance(end_position, list):
            end_position = end_position[0]

        path = {"x": [], "y": []}
        x_intermediate_1 = round(start_position[0] + 1/5 * (end_position[0] - start_position[0]), 3)
        x_intermediate_2 = round(start_position[0] + 4/5 * (end_position[0] - start_position[0]), 3)

        path["x"] = [start_position[0], x_intermediate_1, x_intermediate_2, end_position[0]]
        path["y"] = [start_position[1], start_position[1], end_position[1], end_position[1]]
        return path

def main(config):
    locator = cea.inputlocator.InputLocator(config.scenario)
    
    # Find and use the latest optimization run
    optimization_path = locator.get_optimization_results_folder()
    if os.path.exists(optimization_path):
        run_folders = [f for f in os.listdir(optimization_path) if f.startswith('centralized_run_')]
        if run_folders:
            latest_run_num = max([int(f.split('_')[-1]) for f in run_folders])
            locator.optimization_run = latest_run_num
            print(f"Using latest optimization run: centralized_run_{latest_run_num}")

    # Load the image library
    image_lib_yml = os.path.join(ComponentGraphInfo.image_folder_path, 'image_lib.yml')
    image_lib_dicts = yaml.load(open(image_lib_yml, "rb"), Loader=yaml.CLoader)
    component_images_lib = image_lib_dicts['Components']
    sources_and_sinks_images_lib = image_lib_dicts['SinksAndSources']
    consumers_images_lib = image_lib_dicts['Consumers']
    energy_carrier_images_lib = image_lib_dicts['EnergyCarriers']

    # Assign relevant information to the ComponentGraphInfo class variables
    ComponentGraphInfo.image_paths = {key: os.path.join(ComponentGraphInfo.component_image_folder, value['icon'])
                                      for key, value in component_images_lib.items()}
    ComponentGraphInfo.icon_colors = {key: cea_colors[value['color']]
                                      for key, value in component_images_lib.items()}

    # Assign relevant information to the SourcesAndSinksGraphInfo class variables
    SourceAndSinkGraphInfo.ec_to_code_mapping = sources_and_sinks_images_lib['EnergyCarrierToIconCode']
    SourceAndSinkGraphInfo.image_paths = {icon_code:
                                              os.path.join(SourceAndSinkGraphInfo.sources_and_sinks_image_folder,
                                                           file_name)
                                          for icon_code, file_name in sources_and_sinks_images_lib['IconFiles'].items()}

    # Assign relevant information to the ConsumerGraphInfo class variables
    ConsumerGraphInfo.image_paths = {icon_code:
                                         os.path.join(ConsumerGraphInfo.consumer_image_folder, file_name)
                                     for icon_code, file_name in consumers_images_lib['IconFiles'].items()}

    # Assign relevant information to the EnergyCarrierGraphInfo class variables
    EnergyFlowGraphInfo.colors_and_hues = energy_carrier_images_lib

    # Load the supply system data
    des_supply_systems_dict = {}
    des_solution_folders = locator.get_new_optimization_des_solution_folders()
    for district_energy_system in des_solution_folders:
        supply_systems = locator.get_new_optimization_optimal_supply_system_ids(district_energy_system)
        des_supply_systems_dict[district_energy_system] = supply_systems

    # Generate plots for all energy systems and supply systems
    print("\nGenerating supply system graphics...")
    print(f"Found {len(des_solution_folders)} energy system(s)")

    figures = {}
    for energy_system_id in des_solution_folders:
        supply_systems = des_supply_systems_dict[energy_system_id]
        print(f"\nEnergy System: {energy_system_id}")
        print(f"  Supply systems: {len(supply_systems)}")

        for supply_system_id in supply_systems:
            print(f"    Generating graphic for {supply_system_id}...")
            fig = create_supply_system_graph(energy_system_id, supply_system_id, locator)

            # Store the figure
            key = f"{energy_system_id}_{supply_system_id}"
            figures[key] = fig

    # Create combined figure with dropdowns
    if figures:
        print("\nCreating combined figure with dropdown menus...")
        combined_fig = create_combined_figure_with_dropdowns(figures, des_supply_systems_dict)

        return combined_fig

    return None

def create_supply_system_graph(energy_system_id, supply_system_id, locator):
    # Define a corresponding supply system graph info object
    if energy_system_id is None or supply_system_id is None:
        return go.Figure()
    else:
        supply_system = SupplySystemGraphInfo(energy_system_id, supply_system_id, locator)

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
        # Use the unknown component icon as fallback for missing component images
        icon_path = ComponentGraphInfo.image_paths.get(code, ComponentGraphInfo.image_paths.get("unknown"))
        if icon_path is None:
            raise ValueError(f"No icon path found for component '{code}' and 'unknown' fallback is not defined")
        if not os.path.exists(icon_path):
            raise FileNotFoundError(f"Icon file not found: {icon_path}")
        icon = Image.open(icon_path)
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

    # Add sink and source images and tooltips
    for sinks_or_sources in supply_system.sinks_and_sources.values():
        for code, sink_or_source in sinks_or_sources.items():
            icon = Image.open(SourceAndSinkGraphInfo.image_paths[code])
            fig.add_layout_image(
                source=icon,
                xref="x",
                yref="y",
                x=sink_or_source.position[0],
                y=sink_or_source.position[1],
                xanchor="center",
                yanchor="middle",
                sizex=sink_or_source.size[0],
                sizey=sink_or_source.size[1],
            )

    # Add consumer image
    icon = Image.open(ConsumerGraphInfo.image_paths[supply_system.consumer.category])
    fig.add_layout_image(
        source=icon,
        xref="x",
        yref="y",
        x=supply_system.consumer.position[0],
        y=supply_system.consumer.position[1],
        xanchor="center",
        yanchor="middle",
        sizex=supply_system.consumer.size[0],
        sizey=supply_system.consumer.size[1],
    )

    # Draw Energy Flow Paths
    for ec_code, energy_flow in supply_system.energy_flows.items():
        show_legend = True
        for path_description, path_coordinates in energy_flow.paths.items():
            fig.add_trace(
                go.Scatter(
                    name=ec_code,
                    x=path_coordinates['x'],
                    y=path_coordinates['y'],
                    mode="lines",
                    line=dict(color=energy_flow.hue, width=8),
                    text=[f'{ec_code}'],
                    hoverinfo='text',
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=12,
                        font_family="Rockwell"
                    ),
                    showlegend=show_legend,
                    legendgroup=ec_code,
                )
            )
            show_legend = False
            fig.add_trace(
                go.Scatter(
                    name=ec_code,
                    x=path_coordinates['x'],
                    y=path_coordinates['y'],
                    mode="lines",
                    line=dict(color=energy_flow.color, width=2),
                    text=[f'{ec_code}'],
                    hoverinfo='text',
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=12,
                        font_family="Rockwell"
                    ),
                    showlegend=show_legend,
                    legendgroup=ec_code,
                )
            )

    # Set layout
    fig.update_layout(
        height=1000,
        width=1700,
        xaxis_range=[-0.35, 1.35],
        yaxis_range=[0, 1],
        xaxis_visible=False,
        yaxis_visible=False,
    )

    return fig


def create_combined_figure_with_dropdowns(figures_dict, des_supply_systems_dict):
    """
    Creates a single Plotly figure with dropdown menus to select different energy systems and supply systems.

    Args:
        figures_dict: Dictionary with keys as 'energy_system_id_supply_system_id' and values as Plotly figures
        des_supply_systems_dict: Dictionary mapping energy system IDs to lists of supply system IDs

    Returns:
        A combined Plotly figure with dropdown menus
    """
    if not figures_dict:
        return go.Figure()

    # Get the first figure as the base
    first_key = list(figures_dict.keys())[0]
    combined_fig = figures_dict[first_key]

    # Get all energy system IDs
    energy_system_ids = list(des_supply_systems_dict.keys())

    # Create dropdown buttons for each energy system and supply system combination
    dropdown_buttons = []

    for energy_system_id in energy_system_ids:
        supply_system_ids = des_supply_systems_dict[energy_system_id]

        for supply_system_id in supply_system_ids:
            key = f"{energy_system_id}_{supply_system_id}"

            if key not in figures_dict:
                continue

            fig = figures_dict[key]

            # Create a button that will show this specific figure
            # We need to hide all traces and show only the ones for this figure
            button = dict(
                label=f"{energy_system_id} - {supply_system_id}",
                method="update",
                args=[
                    {"visible": [False] * len(combined_fig.data)},  # Will be updated below
                    {"title": f"Supply System: {energy_system_id} - {supply_system_id}"}
                ]
            )
            dropdown_buttons.append((key, button))

    # Now we need to collect all traces from all figures
    all_traces = []
    trace_to_figure = []  # Maps trace index to figure key

    for key in figures_dict.keys():
        fig = figures_dict[key]
        for trace in fig.data:
            all_traces.append(trace)
            trace_to_figure.append(key)

    # Create a new figure with all traces
    combined_fig = go.Figure(data=all_traces)

    # Copy layout from the first figure
    first_fig = figures_dict[first_key]
    combined_fig.update_layout(first_fig.layout)

    # Copy shapes and images from first figure
    if hasattr(first_fig.layout, 'shapes'):
        combined_fig.update_layout(shapes=first_fig.layout.shapes)
    if hasattr(first_fig.layout, 'images'):
        combined_fig.update_layout(images=first_fig.layout.images)

    # Update dropdown buttons with correct visibility
    for key, button in dropdown_buttons:
        # Determine which traces should be visible for this button
        visibility = [trace_to_figure[i] == key for i in range(len(all_traces))]
        button["args"][0]["visible"] = visibility

        # Also need to update shapes and images
        fig = figures_dict[key]
        if hasattr(fig.layout, 'shapes'):
            button["args"][1]["shapes"] = fig.layout.shapes
        if hasattr(fig.layout, 'images'):
            button["args"][1]["images"] = fig.layout.images

    # Set initial visibility (show first figure)
    first_key = list(figures_dict.keys())[0]
    for i, trace_key in enumerate(trace_to_figure):
        combined_fig.data[i].visible = (trace_key == first_key)

    # Add dropdown menu to the layout
    combined_fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=[button for _, button in dropdown_buttons],
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.01,
                xanchor="left",
                y=1.15,
                yanchor="top"
            )
        ],
        title=f"Supply System: {first_key.replace('_', ' - ', 1)}"
    )

    return combined_fig


if __name__ == '__main__':
    config = cea.config.Configuration()
    combined_fig = main(config)

    # Show the combined figure with dropdowns if available
    if combined_fig:
        print("\nDisplaying combined figure with dropdown menus...")
        combined_fig.show(renderer="browser")
    else:
        print("\nNo figures were generated.")
