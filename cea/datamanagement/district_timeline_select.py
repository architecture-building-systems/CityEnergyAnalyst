"""
Step 0: Select or create a district timeline.
This step must be completed and saved before proceeding to other timeline steps.
"""
from cea.config import Configuration
from cea.datamanagement.district_level_states.state_scenario import validate_timeline_name


def main(config: Configuration) -> None:
    """
    Select or create a timeline. The timeline name will be saved to config
    and referenced by subsequent steps.
    """
    timeline_name = config.district_timeline_select.existing_timeline_name
    if not timeline_name:
        timeline_name = config.district_timeline_select.new_timeline_name
        if timeline_name:
            timeline_name = validate_timeline_name(timeline_name)
    
    if not timeline_name:
        raise ValueError(
            "Please select an existing timeline or provide a new timeline name.\n"
            "After making your selection, click 'Save Settings' before proceeding to other steps."
        )
    
    # Create timeline folder if it doesn't exist
    from cea.inputlocator import InputLocator
    import os
    
    locator = InputLocator(config.scenario)
    timeline_folder = os.path.join(locator.get_district_timeline_container_folder(), timeline_name)
    
    if not os.path.exists(timeline_folder):
        os.makedirs(timeline_folder)
        print(f"Created new timeline: {timeline_name}")
    else:
        print(f"Using existing timeline: {timeline_name}")
    
    print(f"\n✓ Timeline '{timeline_name}' is ready.")
    print("IMPORTANT: Click 'Save Settings' now before proceeding to:")
    print("  - Step 1: Define Atomic Changes")
    print("  - Step 2: Apply Changes to Years")
    print("  - Step 3: Bake State Scenarios")
    print("  - Step 4: Run Simulations")


if __name__ == '__main__':
    main(Configuration())
