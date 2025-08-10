from cea.config import Configuration
from cea.inputlocator import InputLocator



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

    if region != "Switzerland":
        raise ValueError("Currently, only the 'Switzerland' region is supported.")
    
    if region == "Switzerland":
        construction_helper_switzerland(config, locator)

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