"""Step 0: Create a district evolution pathway."""

import os

from cea.config import Configuration
from cea.datamanagement.district_pathways.pathway_state import validate_pathway_name
from cea.inputlocator import InputLocator


def main(config: Configuration) -> None:
    pathway_name = config.create_new_pathway.new_pathway_name
    if pathway_name:
        pathway_name = validate_pathway_name(pathway_name)
    
    if not pathway_name:
        raise ValueError(
            "Please select an existing pathway or provide a new pathway name.\n"
            "After making your selection, click 'Save Settings' before proceeding to other steps."
        )
    
    locator = InputLocator(config.scenario)
    pathway_folder = os.path.join(
        locator.get_district_pathway_container_folder(),
        pathway_name,
    )
    
    if not os.path.exists(pathway_folder):
        os.makedirs(pathway_folder)
        print(f"Created new pathway: {pathway_name}")
    else:
        raise ValueError(
            f"Pathway '{pathway_name}' already exists. "
            "Please select it as an existing pathway in other steps."
        )
    
    print(f"\nPathway '{pathway_name}' is ready.")
    print("IMPORTANT: Click 'Save Settings' now before proceeding to:")
    print("  - Step 1: Define Intervention Templates")
    print("  - Step 2: Apply Intervention Templates to Years")
    print("  - Step 3: Bake Pathway States")
    print("  - Step 4: Simulate Pathway and Generate Pathway Emissions Timeline results")


if __name__ == '__main__':
    main(Configuration())
