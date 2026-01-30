"""
Define atomic changes for district timelines.
Atomic changes are reusable modification templates.
"""
from cea.config import Configuration
from cea.datamanagement.district_level_states.atomic_changes import add_or_update_atomic_change
from cea.datamanagement.district_level_states.state_scenario import create_modify_recipe


def main(config: Configuration) -> None:
    """
    Define or update an atomic change.
    """
    # Get timeline name from Step 0
    timeline_name = config.district_atomic_changes_define.existing_timeline_name
    
    if not timeline_name:
        raise ValueError(
            "No timeline selected. Please complete Step 0 (Select Timeline) first:\n"
            "1. Go to 'Step 0: Select/Create Timeline'\n"
            "2. Select or create a timeline\n"
            "3. Click 'Save Settings'\n"
            "4. Then return to this step"
        )
    
    change_name = config.district_atomic_changes_define.atomic_change_name
    description = config.district_atomic_changes_define.atomic_change_description
    
    if not change_name:
        raise ValueError("Atomic change name is required.")
    
    # Use the existing create_modify_recipe function to build the modifications
    # This reuses all the existing UI for defining building modifications
    modifications = create_modify_recipe(config)
    
    if not modifications:
        raise ValueError("No modifications defined. Please configure at least one modification.")
    
    add_or_update_atomic_change(
        config=config,
        timeline_name=timeline_name,
        change_name=change_name,
        description=description or f"Atomic change: {change_name}",
        modifications=modifications,
    )
    
    print(f"Successfully saved atomic change '{change_name}' to timeline '{timeline_name}'")


if __name__ == '__main__':
    main(Configuration())
