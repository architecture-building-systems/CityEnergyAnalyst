"""
Apply atomic changes to a specific year in a district timeline.

This tool updates the YAML log file only - it does NOT materialise state folders.
Use Step 3 (Bake Scenario Evolution States) to create state folders from the log.
"""
from cea.config import Configuration
from cea.datamanagement.district_level_states.atomic_changes import resolve_atomic_changes_to_recipe
from cea.datamanagement.district_level_states.state_scenario import DistrictEventTimeline


def main(config: Configuration) -> None:
    """
    Apply selected atomic changes to a specific year (updates YAML log only).
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
    timeline = DistrictEventTimeline(config, timeline_name)
    try:
        merged_recipe = resolve_atomic_changes_to_recipe(
            locator=timeline.main_locator,
            timeline_name=timeline_name,
            change_names=atomic_changes,
        )
    except ValueError as e:
        print(f"Error: {e}")
        raise
    
    # Update the YAML log file only (does not materialise state folders)
    timeline.apply_year_modifications(year_of_state, merged_recipe)
    timeline.save()
    
    print(f"Successfully updated timeline log for year {year_of_state}")
    print(f"Applied changes: {', '.join(atomic_changes)}")
    print(f"Log file: {timeline.main_locator.get_district_timeline_log_file(timeline_name)}")
    print("\nNext step: Use Step 3 (Bake Scenario Evolution States) to materialise state folders from the log.")


if __name__ == '__main__':
    main(Configuration())
