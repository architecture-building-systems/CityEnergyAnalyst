import pandas as pd
from cea.config import Configuration
from cea.inputlocator import InputLocator

# Use DataFrame for component parameters
component_properties = ["material", "thickness", "k_value", "density", "specific_heat"]
default_component_params = pd.DataFrame(
    [[None for _ in component_properties] for _ in range(3)],
    columns=component_properties
)
default_construction_params = {
    "prefix": None,
    "wall": default_component_params.copy(),
    "roof": default_component_params.copy(),
    "floor": default_component_params.copy(),
    "u_value": None,
    "a_value": None,
}

def construction_helper_switzerland(config: Configuration, locator: InputLocator):

    def find_db_swiss(locator: InputLocator, structure_type: str):
        pass

    # 1. get structure type and name
    section = config.sections["construction_helper"].parameters
    structure_type = section["structure_type"].get()

    construct_swiss = default_component_params.copy()

    if structure_type in ["masonry", "concrete", "wood", "steel"]:
        values = find_db_swiss(locator, structure_type)
        construct_swiss.loc[1, component_properties] = values
    else:
        raise ValueError(f"Unknown structure type: {structure_type}")


def construction_helper(config: Configuration, locator: InputLocator):
    """_summary_

    :param config: _description_
    :type config: Configuration
    :param locator: _description_
    :type locator: InputLocator
    """
    section = config.sections["construction_helper"].parameters
    prefix = section["database_prefix"].get()
    region = section["database_region"].get()

    if not prefix:
        raise ValueError("Database prefix is required.")

    if region == "Switzerland":
        construction_helper_switzerland(config, locator)
    else:
        raise NotImplementedError(
            f"Construction helper not implemented for region: {region}"
        )


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
