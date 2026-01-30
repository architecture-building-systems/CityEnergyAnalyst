"""
Apply atomic changes to a specific year in a district timeline.
"""
from cea.config import Configuration
from cea.datamanagement.district_level_states.atomic_changes import resolve_atomic_changes_to_recipe
from cea.datamanagement.district_level_states.state_scenario import modify_state_construction
from cea.inputlocator import InputLocator


def main(config: Configuration) -> None:
    """
    Apply selected atomic changes to a specific year.
    """
    # Get timeline name from Step 0
    timeline_name = config.district_events_apply_changes.existing_timeline_name
    
    if not timeline_name:
        raise ValueError(
            "No timeline selected. Please complete Step 0 (Select Timeline) first:\n"
            "1. Go to 'Step 0: Select/Create Timeline'\n"
            "2. Select or create a timeline\n"
            "3. Click 'Save Settings'\n"
            "4. Then return to this step"
        )
    
    year_of_state = config.district_events_apply_changes.year_of_state
    atomic_changes = config.district_events_apply_changes.atomic_changes
    
    if not year_of_state:
        raise ValueError("Year is required. Please specify which year to apply changes to.")
    
    if not atomic_changes:
        raise ValueError("No atomic changes selected. Please select at least one atomic change to apply.")
    
    print(f"Applying {len(atomic_changes)} atomic change(s) to year {year_of_state} in timeline '{timeline_name}'...")
    
    # Resolve atomic changes to a single merged recipe
    locator = InputLocator(config.scenario)
    try:
        merged_recipe = resolve_atomic_changes_to_recipe(
            locator=locator,
            timeline_name=timeline_name,
            change_names=atomic_changes,
        )
    except ValueError as e:
        print(f"Error: {e}")
        raise
    
    # Apply the merged recipe to the year
    modify_state_construction(
        config=config,
        timeline_name=timeline_name,
        year_of_state=year_of_state,
        modify_recipe=merged_recipe,
    )
    
    print(f"Successfully applied atomic changes to year {year_of_state}")
    print(f"Applied changes: {', '.join(atomic_changes)}")


if __name__ == '__main__':
    main(Configuration())
