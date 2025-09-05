import os
import pandas as pd
from cea.config import Configuration
from cea.inputlocator import InputLocator

ref = {"Switzerland": "KBOB_2022v7"}

mapping_path = os.path.join(os.path.dirname(__file__), "data", "material_mapping.csv")


def read_db_swiss():
    material_mapping = pd.read_csv(
        mapping_path,
        dtype={"Switzerland": str},
    )
    db = pd.read_csv(
        os.path.join(os.path.dirname(__file__), "data", "kbob_material.csv"),
        usecols=[
            "ID",
            "name",
            "GHG_emission_total",
            "GHG_emission_production",
            "GHG_emission_recycling",
            "biogenic_carbon_in_product",
        ],
        dtype={"ID": str},
    )
    material_mapping_aug = material_mapping.merge(
        db, left_on="Switzerland", right_on="ID"
    )
    material_mapping_aug.drop(columns=["Switzerland"], inplace=True)

    return material_mapping_aug


def assemble_components(section, material_db):
    layers = [
        section["cladding-type"].get(),
        section["insulation-type"].get(),
        section["building-structure-type"].get(),
    ]
    mat_indexed = material_db.set_index("type", drop=False)

    wall_exterior = mat_indexed.loc[layers].reset_index(drop=True)
    wall_exterior.loc[1, "thickness"] = (
        section["insulation-thickness"].get() / 100
    )  # cm to m

    wall_interior = wall_exterior.copy()
    # thickness of interior should be half of exterior for every layer
    wall_interior.loc[:, "thickness"] = wall_interior["thickness"] / 2
    wall_interior.loc[1, "thickness"] = 0  # no insulation

    roof = wall_exterior.copy()
    roof.loc[:, "thickness"] = roof["thickness"] * 1.5
    roof.loc[0, :] = mat_indexed.loc["bitumen"]

    ceiling = wall_exterior.copy()
    ceiling.loc[:, "thickness"] = ceiling["thickness"] * 1.2
    ceiling.loc[1, "thickness"] = 0  # no insulation

    floor = wall_exterior.copy()
    floor.loc[:, "thickness"] = floor["thickness"] * 1.3
    floor.loc[0, :] = mat_indexed.loc["bitumen"]

    return {
        "wall_exterior": {"layers": wall_exterior},
        "wall_interior": {"layers": wall_interior},
        "roof": {"layers": roof},
        "ceiling": {"layers": ceiling},
        "floor": {"layers": floor},
    }


def calc_component_data(components):
    # calculate U value, GHG per m2 and embodied biogenic carbon
    for component_name, component in components.items():
        layers = component["layers"]
        layers["R_value"] = layers["thickness"] / layers["lambda"]
        u_value = 1 / layers["R_value"].sum()
        layers["GHG_per_m2"] = (
            layers["GHG_emission_total"]  # GHG emissions in kgCO2/kg
            * layers["density"]  # Density in kg/m3
            * layers["thickness"]  # Thickness in m
        )
        GHG_per_m2 = layers["GHG_per_m2"].sum()
        layers["biogenic_carbon_per_m2"] = (
            layers["biogenic_carbon_in_product"]  # Biogenic carbon in kgC/kg
            * layers["density"]
            * layers["thickness"]
        )
        biogenic_carbon_per_m2 = layers["biogenic_carbon_per_m2"].sum()
        biogenic_co2_per_m2 = -(
            biogenic_carbon_per_m2 * 44 / 12
        )  # Convert to CO2 equivalent and negate to show storage

        component["u_value"] = u_value
        component["GHG_per_m2"] = GHG_per_m2
        component["biogenic_co2_per_m2"] = biogenic_co2_per_m2

        print(f"\nComponent: \t\t{component_name}")
        print(f"U-value: \t\t{u_value:.2f} W/m2K")
        print(f"GHG emissions: \t\t{GHG_per_m2:.2f} kgCO2/m2")
        print(f"Biogenic carbon: \t{biogenic_co2_per_m2:.2f} kgCO2/m2")


def write_component_data(section, components, locator: InputLocator):

    # write exterior and interior wall
    db_walls = pd.read_csv(locator.get_database_assemblies_envelope_wall())

    wall_exterior = pd.DataFrame(
        [[
            f"{section['construction-description'].get()}: external wall on timestamp {pd.Timestamp.now()}",  # description
            count_user_defined_components(db_walls, "WALL_UE"),  # code
            components["wall_exterior"]["u_value"],  # U_wall
            0.3,  # a_wall
            0.9,  # e_wall
            0.7,  # r_wall
            components["wall_exterior"]["GHG_per_m2"],  # GHG_wall_kgCO2m2
            components["wall_exterior"]["biogenic_co2_per_m2"],  # GHG_biogenic_wall_kgCO2m2
            30,  # Service_Life_wall
            get_reference_string(section, components, "wall_exterior"),  # Reference
            mapping_path,  # Reference U-Value
        ]],
        columns=db_walls.columns,
    )

    wall_interior = pd.DataFrame(
        [[
            f"{section['construction-description'].get()}: interior wall on timestamp {pd.Timestamp.now()}",  # description
            count_user_defined_components(db_walls, "WALL_UI"),  # code
            components["wall_interior"]["u_value"],  # U_wall
            0.6,  # a_wall
            0.95,  # e_wall
            0.4,  # r_wall
            components["wall_interior"]["GHG_per_m2"],  # GHG_wall_kgCO2m2
            components["wall_interior"]["biogenic_co2_per_m2"],  # GHG_biogenic_wall_kgCO2m2
            30,  # Service_Life_wall
            get_reference_string(section, components, "wall_interior"),  # Reference
            mapping_path,  # Reference U-Value
        ]],
        columns=db_walls.columns,
    )
    db_walls = pd.concat([db_walls, wall_exterior, wall_interior], ignore_index=True)
    db_walls.to_csv(locator.get_database_assemblies_envelope_wall(), index=False)

    # write roof
    db_roofs = pd.read_csv(locator.get_database_assemblies_envelope_roof())
    roof_data = pd.DataFrame(
        [[
            f"{section['construction-description'].get()}: roof on timestamp {pd.Timestamp.now()}",  # description
            count_user_defined_components(db_roofs, "ROOF_U"),  # code
            components["roof"]["u_value"],  # U_roof
            0.25,  # a_roof
            0.85,  # e_roof
            0.94,  # r_roof
            components["roof"]["GHG_per_m2"],  # GHG_roof_kgCO2m2
            components["roof"]["biogenic_co2_per_m2"],  # GHG_biogenic_roof_kgCO2m2
            60,  # Service_Life_roof
            get_reference_string(section, components, "roof"),  # Reference
            mapping_path,  # Reference U-Value
        ]],
        columns=db_roofs.columns,
    )
    db_roofs = pd.concat([db_roofs, roof_data], ignore_index=True)
    db_roofs.to_csv(locator.get_database_assemblies_envelope_roof(), index=False)

    # write floor and ceiling
    db_floors = pd.read_csv(locator.get_database_assemblies_envelope_floor())
    floor_data = pd.DataFrame(
        [[
            f"{section['construction-description'].get()}: floor on timestamp {pd.Timestamp.now()}",  # description
            count_user_defined_components(db_floors, "FLOOR_U"),  # code
            components["floor"]["u_value"],  # U_base
            components["floor"]["GHG_per_m2"],  # GHG_floor_kgCO2m2
            components["floor"]["biogenic_co2_per_m2"],  # GHG_biogenic_floor_kgCO2m2
            60,  # Service_Life_floor
            get_reference_string(section, components, "floor"),  # Reference
            mapping_path,  # unnamed
        ]],
        columns=db_floors.columns,
    )
    ceiling_data = pd.DataFrame(
        [[
            f"{section['construction-description'].get()}: ceiling on timestamp {pd.Timestamp.now()}",  # description
            count_user_defined_components(db_floors, "CEIL_U"),  # code
            components["ceiling"]["u_value"],  # U_ceiling
            components["ceiling"]["GHG_per_m2"],  # GHG_ceiling_kgCO2m2
            components["ceiling"]["biogenic_co2_per_m2"],  # GHG_biogenic_ceiling_kgCO2m2
            60,  # Service_Life_ceiling
            get_reference_string(section, components, "ceiling"),  # Reference
            mapping_path,  # unnamed
        ]],
        columns=db_floors.columns,
    )
    db_floors = pd.concat([db_floors, floor_data, ceiling_data], ignore_index=True)
    db_floors.to_csv(locator.get_database_assemblies_envelope_floor(), index=False)


def get_reference_string(section, components, component_name):
    layers = components[component_name]["layers"]
    layer_names_in_string = " + ".join(layers["name"].tolist())
    layer_thickness_in_string = " + ".join(layers["thickness"].astype(str).tolist())
    reference_string = (
        f"database: {ref[section['database-region'].get()]} | "
        + f"layers: {layer_names_in_string} | "
        + f"thickness: {layer_thickness_in_string} in meters"
    )
    return reference_string


def count_user_defined_components(db, code_prefix):
    n = db[db["code"].str.startswith(code_prefix)].shape[0]
    return code_prefix + f"_{n + 1}"


def construction_helper(config: Configuration, locator: InputLocator):
    section = config.sections["construction-helper"].parameters
    description = section["construction-description"].get()
    region = section["database-region"].get()

    if not description:
        raise ValueError("Database description is required.")

    if region == "Switzerland":
        material_db = read_db_swiss()
    else:
        raise NotImplementedError(
            f"Construction helper not implemented for region: {region}"
        )

    components = assemble_components(section, material_db)
    calc_component_data(components)
    write_component_data(section, components, locator)


def main(config: Configuration):
    """Script runner wrapper.

    :param config: Loaded CEA configuration to pass to the helper.
    :type config: cea.config.Configuration
    """
    # Note: InputLocator expects a scenario path string, not a Configuration object
    locator = InputLocator(config.scenario)
    construction_helper(config, locator)


if __name__ == "__main__":
    main(Configuration())
