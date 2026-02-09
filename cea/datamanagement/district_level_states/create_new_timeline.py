"""
Step 0: Create a district timeline.
"""
from cea.config import Configuration
from cea.datamanagement.district_level_states.state_scenario import validate_timeline_name
from cea.inputlocator import InputLocator
import os

def main(config: Configuration) -> None:
    timeline_name = config.create_new_timeline.new_timeline_name
    if timeline_name:
        timeline_name = validate_timeline_name(timeline_name)
    
    if not timeline_name:
        raise ValueError(
            "Please select an existing timeline or provide a new timeline name.\n"
            "After making your selection, click 'Save Settings' before proceeding to other steps."
        )
    
    locator = InputLocator(config.scenario)
    timeline_folder = os.path.join(locator.get_district_timeline_container_folder(), timeline_name)
    
    if not os.path.exists(timeline_folder):
        os.makedirs(timeline_folder)
        print(f"Created new timeline: {timeline_name}")
    else:
        raise ValueError(
            f"Timeline '{timeline_name}' already exists. "
            "Please select it as an existing timeline in other steps."
        )
    
    print(f"\nTimeline '{timeline_name}' is ready.")
    print("IMPORTANT: Click 'Save Settings' now before proceeding to:")
    print("  - Step 1: Define Atomic Changes")
    print("  - Step 2: Apply Changes to Years")
    print("  - Step 3: Bake State Scenarios")
    print("  - Step 4: Run Simulations and Generate Emission Timeline results")


if __name__ == '__main__':
    main(Configuration())
