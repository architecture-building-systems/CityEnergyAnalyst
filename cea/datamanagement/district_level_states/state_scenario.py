import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from typing import Any, Literal, cast

import geopandas as gpd
import pandas as pd
import yaml

from cea.config import Configuration
from cea.datamanagement.archetypes_mapper import archetypes_mapper
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.datamanagement.databases_verification import verify_input_geometry_zone
from cea.datamanagement.district_level_states.state_transaction import (
    snapshot_state_year_files,
)
from cea.datamanagement.district_level_states.timeline_integrity import (
    check_district_timeline_log_yaml_integrity,
    compute_state_year_missing_modifications,
    merge_modify_recipes,
)
from cea.datamanagement.district_level_states.envelope_topology import (
    validate_three_layer_topology,
)
from cea.datamanagement.district_level_states.timeline_log import (
    add_year_in_yaml,
    del_year_in_yaml,
    load_log_yaml,
    save_log_yaml,
)
from cea.inputlocator import InputLocator
from cea.utilities.standardize_coordinates import shapefile_to_WSG_and_UTM

ModifyRecipe = dict[str, dict[str, dict[str, Any]]]


def _validate_three_layer_topology_row(
    row: pd.Series,
    *,
    year_of_state: int,
    archetype: str,
    component: str,
    envelope_db_name: str,
    code: str,
) -> None:
    errors = validate_three_layer_topology(
        row,
        year_of_state=year_of_state,
        archetype=archetype,
        component=component,
        envelope_ref=f"envelope DB '{envelope_db_name}' row '{code}'",
    )
    if errors:
        raise ValueError(errors[0])


def _canonical_json(obj: Any) -> str:
    """Create a stable JSON representation for hashing / signatures."""

    def _normalise(v: Any) -> Any:
        if isinstance(v, dict):
            return {
                str(k): _normalise(v[k]) for k in sorted(v.keys(), key=str)
            }
        if isinstance(v, list):
            return [_normalise(x) for x in v]
        if isinstance(v, float):
            # Keep signatures stable across JSON float formatting.
            return float(v)
        return v

    return json.dumps(
        _normalise(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def _recipe_signature(recipe: ModifyRecipe) -> str:
    payload = _canonical_json(recipe).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class DistrictStateYear:
    """Represents a single state year definition and its on-disk realisation (if any)."""
    timeline_name: str
    year: int
    modifications: ModifyRecipe
    main_locator: InputLocator

    def state_folder(self) -> str:
        return self.main_locator.get_state_in_time_scenario_folder(self.timeline_name, int(self.year))

    def signature_path(self) -> str:
        return os.path.join(
            self.state_folder(), ".district_timeline_signature.json"
        )

    def exists_on_disk(self) -> bool:
        return os.path.exists(self.state_folder())

    def read_applied_signature(self) -> str | None:
        path = self.signature_path()
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                rec = json.load(f) or {}
            sig = rec.get("applied_signature")
            return str(sig) if sig else None
        except Exception:
            return None

    def read_signature_record(self) -> dict[str, Any] | None:
        path = self.signature_path()
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                rec = json.load(f) or {}
            return rec if isinstance(rec, dict) else None
        except Exception:
            return None

    def write_signature_record(self, rec: dict[str, Any]) -> None:
        path = self.signature_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)

    def needs_simulation(self) -> bool:
        rec = self.read_signature_record()
        if not rec:
            return True
        applied = rec.get("applied_signature")
        simulated = rec.get("simulated_signature")
        if not applied:
            return True
        return simulated != applied

    def mark_simulated(
        self,
        *,
        workflow: list[dict[str, Any]] | None = None,
    ) -> None:
        rec = self.read_signature_record() or {"year": int(self.year)}
        now = str(pd.Timestamp.now())
        rec["simulated_at"] = now
        rec["simulated_signature"] = rec.get("applied_signature")
        rec["simulation_status"] = "simulated"
        if workflow is not None:
            rec["simulated_workflow"] = workflow
        self.write_signature_record(rec)

    def simulate(
        self,
        main_config: Configuration,
        *,
        workflow: list[dict[str, Any]],
    ) -> None:
        """Run the standard simulation workflow for this state year.

        This is a state-level operation: it executes the workflow in the `state_{year}` scenario and then
        updates the signature file to mark the state as simulated.
        """
        from copy import deepcopy

        from cea.workflows.workflow import do_config_step, do_script_step

        state_folder = self.state_folder()
        if not os.path.exists(state_folder):
            raise FileNotFoundError(
                f"State folder for year {self.year} does not exist: {state_folder}"
            )

        scenario_config = deepcopy(main_config)
        scenario_config.scenario = state_folder
        if (
            type(scenario_config.emissions.year_end) is int
            and int(self.year) > scenario_config.emissions.year_end
        ):
            scenario_config.emissions.year_end = int(self.year)

        for i, step in enumerate(workflow):
            if "script" in step:
                do_script_step(scenario_config, i, step, trace_input=False)
            elif "config" in step:
                do_config_step(scenario_config, step)
            else:
                raise ValueError(
                    "Invalid step configuration: {i} - {step}".format(i=i, step=step)
                )

        self.mark_simulated(workflow=workflow)

    def write_applied_signature(
        self, *, signature: str
    ) -> None:
        path = self.signature_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        rec = {
            "year": int(self.year),
            "applied_signature": str(signature),
            "built_at": str(pd.Timestamp.now()),
            # A rebuilt / newly built state needs simulation.
            "simulation_status": "needs_simulation",
            "simulated_at": None,
            "simulated_signature": None,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)


class DistrictEventTimeline:
    """Manage district timeline definitions (YAML) and materialise state scenarios from them.
    The config points to the main scenario; the timeline_name selects which district timeline to manage."""

    def __init__(self, config: Configuration, timeline_name: str):
        self.config = config
        self.main_locator = InputLocator(config.scenario)
        self.timeline_name = validate_timeline_name(timeline_name)
        # Ensure the district timeline folder exists for first-time runs.
        os.makedirs(self.main_locator.get_district_timeline_folder(self.timeline_name), exist_ok=True)
        self.log_data: dict[int, dict[str, Any]] = load_log_yaml(
            self.main_locator,
            allow_missing=True,
            allow_empty=True,
            timeline_name=self.timeline_name,
        )

    def list_state_years_on_disk(self) -> list[int]:
        """Return sorted list of state years present under `district_timelines/{timeline_name}/state_YYYY/`."""
        years: list[int] = []
        timeline_folder = self.main_locator.get_district_timeline_folder(self.timeline_name)
        if not os.path.exists(timeline_folder):
            return years
        for name in os.listdir(timeline_folder):
            if not name.startswith("state_"):
                continue
            try:
                years.append(int(name.replace("state_", "")))
            except ValueError:
                continue
        years.sort()
        return years

    def get_building_construction_years(self) -> dict[str, int]:
        """Return {building_name: construction_year} from `zone.shp`.

        Requires a `year` attribute in the geometry.
        """
        zone = gpd.read_file(self.main_locator.get_zone_geometry())
        if "name" not in zone.columns:
            raise ValueError("Zone geometry is missing required 'name' column.")
        if "year" not in zone.columns:
            raise ValueError("Zone geometry is missing required 'year' column.")

        out: dict[str, int] = {}
        for _, row in zone.iterrows():
            name = str(row["name"])
            y = row["year"]
            if y is None:
                continue
            try:
                out[name] = int(y)
            except Exception as e:
                raise ValueError(
                    f"Invalid construction year for building '{name}': {y}"
                ) from e
        return out

    def required_state_years(self) -> list[int]:
        """Compute which years should have a `state_{year}` folder.

        Rules:
        - Always include all years present in YAML log.
        - Always include all distinct building construction years from `zone.shp`.

        This ensures operational timelines capture both policy/standard changes and building births.
        """
        years_from_log = set(int(y) for y in self.log_data.keys())
        years_from_buildings = set(self.get_building_construction_years().values())
        return sorted(years_from_log | years_from_buildings)

    def ensure_state_years_exist(
        self,
        years: list[int],
        *,
        update_yaml: bool = True,
        regenerate_building_properties: bool = True,
        update_building_events: bool = True,
    ) -> dict[int, dict[str, Any]]:
        """Ensure `state_{year}` folders exist for all requested years.

        - Creates missing `state_{year}` folders by copying inputs.
        - Removes buildings not yet built in that year.
        - Ensures YAML entries exist (empty modifications by default).
        - Optionally logs `building_events` (derived from `zone.shp` construction years).

        Returns the (possibly updated) YAML log data in memory.
        """
        construction_years = self.get_building_construction_years()
        existing_years = set(self.list_state_years_on_disk())
        years_sorted = sorted(set(int(y) for y in years))

        prev_buildings: set[str] | None = None
        for year in years_sorted:
            if year not in existing_years:
                create_state_in_time_scenario(
                    self.config,
                    timeline_name=self.timeline_name,
                    year_of_state=year,
                    update_yaml=False,
                )
                if update_yaml:
                    self.log_data.setdefault(
                        year, {"created_at": None, "modifications": {}}
                    )

            if update_yaml:
                entry = self.log_data.get(year, {}) or {}
                # Don't leave created_at empty (e.g., legacy year 2000 entries)
                if entry.get("created_at") in (None, "", "null"):
                    entry["created_at"] = str(pd.Timestamp.now())
                entry.setdefault("modifications", {})
                self.log_data[year] = entry

            delete_unexisting_buildings_from_event_scenario(self.config, self.timeline_name, year)
            state_locator = InputLocator(
                self.main_locator.get_state_in_time_scenario_folder(self.timeline_name, year)
            )
            if regenerate_building_properties:
                _regenerate_building_properties_from_archetypes(state_locator)

            current_buildings = set(state_locator.get_zone_building_names())
            born = sorted(b for b in current_buildings if construction_years.get(b) == year)
            if prev_buildings is not None:
                demolished = sorted(prev_buildings - current_buildings)
            else:
                demolished = []

            if update_yaml and update_building_events:
                entry = self.log_data.get(year, {}) or {}
                building_events = entry.get("building_events", {}) or {}

                building_events.setdefault("new_buildings", [])
                existing_born = set(
                    str(x) for x in building_events.get("new_buildings", []) or []
                )
                for b in born:
                    if b not in existing_born:
                        building_events["new_buildings"].append(b)

                building_events.setdefault("demolished_buildings", [])
                existing_demolished = set(
                    str(x)
                    for x in building_events.get("demolished_buildings", []) or []
                )
                for b in demolished:
                    if b not in existing_demolished:
                        building_events["demolished_buildings"].append(b)

                entry["building_events"] = building_events
                self.log_data[year] = entry

            prev_buildings = current_buildings

        if update_yaml:
            self.save()

        return self.log_data

    def ensure_year(self, year: int) -> None:
        if year not in self.log_data:
            self.log_data[year] = {
                "created_at": str(pd.Timestamp.now()),
                "modifications": {},
            }

    def apply_year_modifications(self, year: int, modify_recipe: ModifyRecipe) -> None:
        self.ensure_year(year)
        entry = self.log_data.get(year, {}) or {}
        current = entry.get("modifications", {}) or {}
        entry["modifications"] = merge_modify_recipes(current, modify_recipe)
        entry["latest_modified_at"] = str(pd.Timestamp.now())
        self.log_data[year] = entry

    def save(self) -> None:
        save_log_yaml(self.main_locator, self.log_data, timeline_name=self.timeline_name)

    def state_years(self) -> list[DistrictStateYear]:
        years = sorted(self.log_data.keys())
        out: list[DistrictStateYear] = []
        for y in years:
            entry = self.log_data.get(y, {}) or {}
            mods = entry.get("modifications", {}) or {}
            out.append(
                DistrictStateYear(
                    timeline_name=self.timeline_name, year=int(y), modifications=mods, main_locator=self.main_locator
                )
            )
        return out

    def cumulative_by_year(self) -> dict[int, ModifyRecipe]:
        cumulative: ModifyRecipe = {}
        out: dict[int, ModifyRecipe] = {}
        for y in self.required_state_years():
            entry = self.log_data.get(y, {}) or {}
            year_modifications = entry.get("modifications", {}) or {}
            cumulative = merge_modify_recipes(cumulative, year_modifications)
            out[int(y)] = cumulative
        return out

    def bake_states_from_log(self) -> None:
        years = self.required_state_years()
        if not years:
            raise ValueError(
                "No district event years or building construction years found."
            )

        # Ensure YAML entries exist for all required years (including construction-only years)
        for year in years:
            self.ensure_year(year)
        self.save()

        print("Building district state scenarios from the district timeline log...")
        print(f"Years to build: {years}")

        cumulative = self.cumulative_by_year()

        built_years: list[int] = []

        for year in years:
            year_recipe = cumulative.get(int(year), {})
            expected_sig = _recipe_signature(year_recipe)
            state = DistrictStateYear(
                timeline_name=self.timeline_name,
                year=int(year),
                modifications=self.log_data.get(int(year), {}).get("modifications", {})
                or {},
                main_locator=self.main_locator,
            )

            state_folder = state.state_folder()
            print(f"- Building state_{int(year)}... ")

            # Rebuild the state folder deterministically to avoid code drift in envelope codes.
            if os.path.exists(state_folder):
                shutil.rmtree(state_folder, ignore_errors=True)

            create_state_in_time_scenario(
                self.config, self.timeline_name, int(year), update_yaml=False
            )

            # Make the state-year reflect building existence (birth years) before generating properties.
            delete_unexisting_buildings_from_event_scenario(self.config, self.timeline_name, int(year))

            if year_recipe:
                _apply_state_construction_changes(
                    self.config,
                    self.timeline_name,
                    int(year),
                    year_recipe,
                    use_transaction=False,
                )

            state.write_applied_signature(signature=expected_sig)
            built_years.append(int(year))

        print("District state materialisation finished.")
        print(f"Created/updated: {len(built_years)} years")
        if built_years:
            print(f"Years created/updated: {built_years}")

        print(f"Timeline folder: {self.main_locator.get_district_timeline_folder(timeline_name=self.timeline_name)}")
        print(f"Log file: {self.main_locator.get_district_timeline_log_file(timeline_name=self.timeline_name)}")
        print(
            "Each built state folder contains an applied signature in '.district_timeline_signature.json'."
        )

        # After building, the existing integrity check becomes meaningful again.
        check_district_timeline_log_yaml_integrity(self.config, self.timeline_name)

    def simulate_states(
        self,
        *,
        simulation_mode: Literal["pending", "all"],
        workflow: list[dict[str, Any]],
        state_workflows: dict[int, list[dict[str, Any]]] | None = None,
    ) -> None:
        """Simulate state-in-time scenarios.

        - `pending`: simulate only states that have not been simulated yet, or whose construction changes
          mean results are out of date.
        - `all`: simulate every `state_{year}` folder present in `district_timeline_states`.

        This updates both:
        - per-state signature files (`.district_timeline_signature.json`)
        - the district timeline log (`district_timeline_log.yml`) with timestamps / workflow metadata.

        Args:
            simulation_mode: "pending" or "all"
            workflow: Default workflow to use for all states (fallback)
            state_workflows: Optional dict mapping year -> custom workflow for that state
                           If provided, uses custom workflow for each year; otherwise uses default workflow
        """
        if simulation_mode not in {"pending", "all"}:
            raise ValueError(
                f"Invalid simulation mode: {simulation_mode}. Expected one of: pending, all"
            )

        state_years = self.list_state_years_on_disk()
        if not state_years:
            raise ValueError(
                "No state-in-time scenarios found in the district timeline folder."
            )
        state_years.sort()

        if simulation_mode == "pending":
            years_to_simulate = [
                y
                for y in state_years
                if DistrictStateYear(
                    timeline_name=self.timeline_name, year=int(y), modifications={}, main_locator=self.main_locator
                ).needs_simulation()
            ]
        else:
            years_to_simulate = list(state_years)

        print("State-in-time simulations started.")
        print(f"Mode: {simulation_mode}")
        print(f"Found state years: {state_years}")
        print(f"Years to simulate: {years_to_simulate}")

        if not years_to_simulate:
            print("Nothing to simulate: all state years are up to date.")
            return

        simulated_years: list[int] = []
        skipped_years = [y for y in state_years if y not in set(years_to_simulate)]

        for year in years_to_simulate:
            if year not in self.log_data:
                raise ValueError(
                    "State year {year} exists in the district timeline folder, but it is missing from the district timeline log.".format(
                        year=year
                    )
                )

            # Use state-specific workflow if provided, otherwise use default
            year_workflow = workflow
            if state_workflows and int(year) in state_workflows:
                year_workflow = state_workflows[int(year)]
                print(f"Using custom workflow for state {year}")

            print(f"Simulating state-in-time scenario for year {year}...")
            DistrictStateYear(
                timeline_name=self.timeline_name, year=int(year), modifications={}, main_locator=self.main_locator
            ).simulate(self.config, workflow=year_workflow)

            # Log metadata in the YAML log.
            entry = self.log_data.get(int(year), {}) or {}
            entry["simulation_workflow"] = year_workflow
            entry["latest_simulated_at"] = str(pd.Timestamp.now())
            self.log_data[int(year)] = entry

            simulated_years.append(int(year))
            print(f"Simulation for state-in-time scenario year {year} completed.")

        self.save()

        print("State-in-time simulations finished.")
        print(f"Simulated: {len(simulated_years)} years")
        if simulated_years:
            print(f"Years simulated: {simulated_years}")
        print(f"Skipped: {len(skipped_years)} years")
        if skipped_years:
            print(f"Years skipped: {skipped_years}")


def create_state_in_time_scenario(
    config: Configuration,
    timeline_name: str,
    year_of_state: int,
    *,
    update_yaml: bool = True,
) -> None:
    """
    Create a new state-in-time scenario based on the current scenario.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        timeline_name (str): The name of the timeline.
        year_of_state (int): The year of the event scenario. If a building year is larger than
        this year, it will not be included in the event scenario.
        event_content (dict): A dictionary containing the content of the event scenario.
    Returns:
        None
    """
    main_locator = InputLocator(config.scenario)
    state_scenario_folder = main_locator.get_state_in_time_scenario_folder(
        timeline_name=timeline_name, year_of_state=year_of_state
    )
    input_folder_path = main_locator.get_input_folder()
    state_locator = InputLocator(state_scenario_folder)
    # copy all files from the input folder to the event scenario folder
    shutil.copytree(
        input_folder_path, state_locator.get_input_folder(), dirs_exist_ok=True
    )  # make sure existing files are overwritten
    if update_yaml:
        add_year_in_yaml(config, year_of_state, timeline_name=timeline_name)
    return None


def _regenerate_building_properties_from_archetypes(locator: InputLocator) -> None:
    """Regenerate building-properties inputs from archetypes.

    This enforces the "archetypes are canonical" assumption: per-building inputs (envelope, hvac, internal loads,
    comfort, supply and schedules) are derived from zone.shp + archetype databases for that state-year.
    """
    list_buildings = locator.get_zone_building_names()
    if not list_buildings:
        return
    archetypes_mapper(
        locator,
        update_architecture_dbf=True,
        update_air_conditioning_systems_dbf=True,
        update_indoor_comfort_dbf=True,
        update_internal_loads_dbf=True,
        update_supply_systems_dbf=True,
        update_schedule_operation_cea=True,
        list_buildings=list_buildings,
    )


def remove_state_in_time_scenario(config: Configuration, timeline_name: str, year_of_state: int) -> None:
    """
    Delete an existing event scenario.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        year_of_state (int): The year of the event scenario to be deleted.
    Returns:
        None
    """
    locator = InputLocator(config.scenario)
    event_scenario_folder = locator.get_state_in_time_scenario_folder(timeline_name, year_of_state)
    shutil.rmtree(event_scenario_folder, ignore_errors=True)
    del_year_in_yaml(config, year_of_state, timeline_name=timeline_name)
    return None


def delete_unexisting_buildings_from_event_scenario(
    config: Configuration, timeline_name: str, year_of_state: int
) -> list[str]:
    """
    Delete buildings from the event scenario that do not yet exist in the specified event year.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        year_of_state (int): The year of the event scenario. If a building year is larger than this year, it will be deleted from the event scenario.
    Returns:
        list[str]: A list of building names that were deleted from the event scenario.
    """
    locator = InputLocator(config.scenario)
    event_scenario_folder = locator.get_state_in_time_scenario_folder(timeline_name, year_of_state)
    # ensure the event scenario folder exists
    state_locator = InputLocator(event_scenario_folder)
    if not os.path.exists(state_locator.get_zone_geometry()):
        raise FileNotFoundError(
            f"Event scenario folder for year {year_of_state} does not exist."
        )

    buildings_to_delete = []
    buildings_gdf_current = gpd.read_file(locator.get_zone_geometry())
    for _, building in buildings_gdf_current.iterrows():
        building_year = building.get("year", None)

        if building_year is not None and building_year > year_of_state:
            buildings_to_delete.append(building["name"])

    # delete all files related to the buildings to delete
    for building_name in buildings_to_delete:
        delete_building_schedule(state_locator, building_name)

    # delete buildings from geometry file
    geometry_gdf, _, _ = shapefile_to_WSG_and_UTM(state_locator.get_zone_geometry())
    geometry_gdf.set_index("name", inplace=True)
    geometry_gdf = geometry_gdf.drop(buildings_to_delete, errors="ignore")
    verify_input_geometry_zone(geometry_gdf.reset_index())
    geometry_gdf.to_file(state_locator.get_zone_geometry())

    monthly_multiplier_df_path = (
        state_locator.get_building_weekly_schedules_monthly_multiplier_csv()
    )
    envelope_df_path = state_locator.get_building_architecture()
    hvac_df_path = state_locator.get_building_air_conditioning()
    indoor_comfort_df_path = state_locator.get_building_comfort()
    internal_loads_df_path = state_locator.get_building_internal()
    supply_df_path = state_locator.get_building_supply()
    # delete building row from all dfs
    for df_path in [
        monthly_multiplier_df_path,
        envelope_df_path,
        hvac_df_path,
        indoor_comfort_df_path,
        internal_loads_df_path,
        supply_df_path,
    ]:
        if os.path.exists(df_path):
            df = pd.read_csv(df_path, index_col="name")
            df = df.drop(buildings_to_delete, errors="ignore")
            df.to_csv(df_path)

    return buildings_to_delete


def delete_building_schedule(state_locator: InputLocator, building_name: str) -> None:
    """
    Delete the schedule file related to a specific building in the event scenario.
    This includes the following file:
    - building schedule file (`locator.get_building_occupancy_schedule(building_name)`)
    """
    schedule_file_path = state_locator.get_building_weekly_schedules(building_name)
    if os.path.exists(schedule_file_path):
        os.remove(schedule_file_path)
    return None


def modify_state_construction(
    config: Configuration,
    timeline_name: str,
    year_of_state: int,
    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]],
    *,
    log_data: dict[int, dict[str, Any]] | None = None,
) -> None:
    """
    Modify the construction recipe of buildings in the event scenario based on the provided modification dictionary.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        year_of_state (int): The year of the event scenario.
        modify_recipe (dict): A dictionary specifying the material-based modifications to be made to the construction recipes.
            For example:
            ```
            {
                "STANDARD1": {
                    "wall": {
                        "material_name_1": "phenolic_resin_pf",
                        "thickness_1_m": 0.08,
                        "material_name_2": "steel_sheet_galvanised",
                        "thickness_2_m": 0.002,
                        "material_name_3": "concrete_1_percent_steel_reinforcement",
                        "thickness_3_m": 0.10,
                        "Service_Life": 30
                    },
                    "roof": {
                        "material_name_1": "phenolic_resin_pf",
                        "thickness_1_m": None,  # keep current value
                        "material_name_2": None, # keep current value
                        "thickness_2_m": None,   # keep current value
                        "material_name_3": None, # keep current value
                        "thickness_3_m": 0.12,
                        "Service_Life": None     # keep current value
                    },
                    "base": {
                        "material_name_1": "glass_wool_supafil",
                        "thickness_1_m": 0.02,
                        "material_name_2": "brass_bronze_sheet",
                        "thickness_2_m": 0.0,
                        "material_name_3": "stainless_steel_sheet_tinned",
                        "thickness_3_m": 0.0
                    }
                }
            }
            ```
            Note that the outer dictionary keys are archetype names,
            the middle dictionary keys are component types.
            Field names must match the envelope database column keys
            (e.g., `material_name_1`, `thickness_1_m`, `Service_Life`).
    Returns:
        None
    """
    modified = _apply_state_construction_changes(
        config,
        timeline_name=timeline_name,
        year_of_state=year_of_state,
        modify_recipe=modify_recipe,
    )
    if not modified:
        print(
            f"No modifications were made to the envelope database in year {year_of_state}."
        )
        return
    # Store only the changed fields (delta) for record-keeping.
    if log_data is None:
        log_modifications(config, timeline_name, year_of_state, modify_recipe)
    else:
        _log_modifications_in_memory(log_data, year_of_state, modify_recipe)
    return None


def _apply_state_construction_changes(
    config: Configuration,
    timeline_name: str,
    year_of_state: int,
    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]],
    *,
    trigger_year: int | None = None,
    use_transaction: bool = True,
) -> bool:
    """Apply construction changes to the state scenario databases.

    Returns True if any database values were modified.

    NOTE: This does not write to the district timeline YAML. Callers must log appropriately.
    """
    archetypes_to_modify = modify_recipe.keys()
    if not archetypes_to_modify:
        remove_state_in_time_scenario(config, timeline_name, year_of_state)
        raise ValueError(
            f"No archetypes specified for modification in the event scenario. The state-in-time scenario for year {year_of_state} has been deleted."
        )

    main_locator = InputLocator(config.scenario)
    state_scenario_folder = main_locator.get_state_in_time_scenario_folder(
        timeline_name, year_of_state
    )
    state_locator = InputLocator(state_scenario_folder)

    snapshot = snapshot_state_year_files(state_locator) if use_transaction else None

    try:
        archetype_df = pd.read_csv(
            state_locator.get_database_archetypes_construction_type(),
            index_col="const_type",
        )
        envelope_lookup = EnvelopeLookup.from_locator(state_locator)
        dbs_overall_modified = 0
        for archetype in archetypes_to_modify:
            if archetype not in archetype_df.index:
                raise ValueError(
                    f"Archetype '{archetype}' not found in construction type database."
                )
            for component, modifications in modify_recipe[archetype].items():
                db_modified = 0
                if component == "construction_type":
                    # These fields live directly on the construction types database.
                    for field, new_value in (modifications or {}).items():
                        if new_value is None:
                            continue
                        if field not in archetype_df.columns:
                            raise ValueError(
                                f"Construction types database has no column '{field}' (archetype '{archetype}')."
                            )
                        archetype_df.at[archetype, field] = str(new_value)
                        db_modified += 1
                    dbs_overall_modified += db_modified
                    continue

                code_current = archetype_df.at[archetype, f"type_{component}"]
                # create a new component code by "(capitalized component)_(archetype)_YEAR_(event_year)"
                envelope_db_name = "floor" if component == "base" else component
                component_db = envelope_lookup._df_for(envelope_db_name)
                code_new = (
                    f"{envelope_db_name.capitalize()}_{archetype}_YEAR_{year_of_state}"
                )

                if code_new in component_db.index:
                    code_new = shift_code_name_plus1(component_db, code_new)
                new_row = cast(pd.Series, component_db.loc[code_current].copy())
                new_row.name = code_new

                for field, new_value in modifications.items():
                    if new_value is not None:
                        if field.startswith("material_name_") or field.startswith(
                            "thickness_"
                        ):
                            component_field_name = field
                        else:
                            component_field_name = envelope_lookup._col(
                                envelope_db_name, field
                            )
                        new_row[component_field_name] = new_value
                        db_modified += 1

                if db_modified:
                    _validate_three_layer_topology_row(
                        new_row,
                        year_of_state=year_of_state,
                        archetype=archetype,
                        component=component,
                        envelope_db_name=envelope_db_name,
                        code=code_new,
                    )
                    description_new = (
                        f"Modified {component} for archetype {archetype} in year {year_of_state}, based on {code_current}, "
                        f"fields modified: {', '.join(modifications.keys())}"
                    )
                    if trigger_year is not None:
                        description_new += f" (reconciled due to year {trigger_year})"
                    new_row["description"] = description_new
                    component_db.loc[new_row.name, :] = new_row
                    archetype_df.at[archetype, f"type_{component}"] = code_new

                dbs_overall_modified += db_modified

        if not dbs_overall_modified:
            return False

        archetype_df.reset_index(inplace=True)
        archetype_df.to_csv(
            state_locator.get_database_archetypes_construction_type(), index=False
        )
        envelope_lookup.envelope.save(state_locator)
        return True
    except Exception:
        if snapshot is not None:
            snapshot.restore()
        raise


def _append_future_year_reconciliation_in_memory(
    trigger_year: int,
    affected_year: int,
    applied_recipe: dict[str, dict[str, dict[str, Any]]],
    *,
    log_data: dict[int, dict[str, Any]],
) -> None:
    entry = log_data.get(affected_year, {})
    reconciliations = entry.get("reconciliations", []) or []
    now = str(pd.Timestamp.now())
    reconciliations.append(
        {
            "trigger_year": trigger_year,
            "applied_at": now,
            "modifications": applied_recipe,
        }
    )
    entry["reconciliations"] = reconciliations
    entry["latest_reconciled_at"] = now
    log_data[affected_year] = entry


def _list_existing_state_years(main_locator: InputLocator, timeline_name: str) -> list[int]:
    years: list[int] = []
    district_timeline_folder = main_locator.get_district_timeline_folder(timeline_name=timeline_name)
    if not os.path.exists(district_timeline_folder):
        return years

    for folder_name in os.listdir(district_timeline_folder):
        if not folder_name.startswith("state_"):
            continue
        year_str = folder_name.replace("state_", "")
        try:
            years.append(int(year_str))
        except ValueError:
            print(
                f"Warning: Invalid state-in-time folder name '{folder_name}' in district timeline folder."
            )
    years.sort()
    return years


def _update_future_state_scenarios_after_year_event(
    config: Configuration,
    timeline_name: str,
    year_of_state: int,
    *,
    log_data: dict[int, dict[str, Any]],
) -> None:
    """Ensure future state scenarios reflect cumulative district evolution.

    If a state year `Y` is created/modified after later years already exist, those later years may become stale.
    This function updates each existing `state_{year}` for year > Y to include cumulative modifications
    (all changes up to and including that year).

    NOTE: The district timeline YAML is not modified for these future years.
    """
    main_locator = InputLocator(config.scenario)
    existing_state_years = _list_existing_state_years(main_locator, timeline_name=timeline_name)
    affected_years = [y for y in existing_state_years if y > year_of_state]
    if not affected_years:
        return

    print(
        "Warning: Creating or modifying an earlier state year updates already-created future years "
        "(including years that may already have been modified before). "
        f"Affected years: {affected_years}."
    )

    missing_in_yaml = [y for y in affected_years if y not in log_data]
    if missing_in_yaml:
        raise ValueError(
            "The following future state years exist in folders but not in the district timeline log file: "
            f"{sorted(missing_in_yaml)}"
        )

    cumulative_by_year: dict[int, dict[str, dict[str, dict[str, Any]]]] = {}
    cumulative: dict[str, dict[str, dict[str, Any]]] = {}
    for year in sorted(log_data.keys()):
        year_entry = log_data.get(year, {}) or {}
        year_modifications = year_entry.get("modifications", {}) or {}
        cumulative = merge_modify_recipes(cumulative, year_modifications)
        cumulative_by_year[year] = cumulative

    all_errors: list[str] = []
    updated_years: list[int] = []
    unchanged_years: list[int] = []

    for future_year in affected_years:
        expected = cumulative_by_year.get(future_year, {})
        missing_recipe, errors = compute_state_year_missing_modifications(
            config, timeline_name, future_year, expected
        )
        all_errors.extend(errors)

        if missing_recipe:
            modified = _apply_state_construction_changes(
                config,
                timeline_name,
                future_year,
                missing_recipe,
                trigger_year=year_of_state,
            )
            if modified:
                _append_future_year_reconciliation_in_memory(
                    trigger_year=year_of_state,
                    affected_year=future_year,
                    applied_recipe=missing_recipe,
                    log_data=log_data,
                )
                updated_years.append(future_year)
            else:
                unchanged_years.append(future_year)
        else:
            unchanged_years.append(future_year)

    if all_errors:
        formatted = "\n".join(f"- {msg}" for msg in all_errors)
        raise ValueError(
            "Errors occurred while updating future state scenarios.\n" + formatted
        )

    if updated_years:
        print(
            "Updated future state scenario databases to include cumulative changes. "
            f"Years updated: {updated_years}."
        )
    if unchanged_years:
        print(
            "No database changes were required for some future years. "
            f"Years unchanged: {unchanged_years}."
        )


def log_modifications(
    config: Configuration,
    timeline_name: str,
    year_of_state: int,
    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]],
) -> None:
    """
    Log the modifications made to the envelope database in a YAML file for record-keeping.
    Parameters:
        state_locator (InputLocator): The input locator object for the event scenario.
        year_of_state (int): The year of the event scenario.
        modify_recipe (dict): The modification recipe used for the modifications.
    Returns:
        None
    """
    locator = InputLocator(config.scenario)
    yml_path = locator.get_district_timeline_log_file(timeline_name=timeline_name)
    if os.path.exists(yml_path):
        with open(yml_path, "r") as f:
            existing_data: dict[int, dict[str, Any]] = yaml.safe_load(f) or {}
    else:
        existing_data: dict[int, dict[str, Any]] = {}
    current_year_modifications = existing_data.get(year_of_state, {})
    current_modifications = current_year_modifications.setdefault("modifications", {})
    current_year_modifications["modifications"] = merge_modify_recipes(current_modifications, modify_recipe)
    current_year_modifications["latest_modified_at"] = str(pd.Timestamp.now())
    existing_data[year_of_state] = current_year_modifications
    save_log_yaml(locator, existing_data, timeline_name=timeline_name)


def _log_modifications_in_memory(
    log_data: dict[int, dict[str, Any]],
    year_of_state: int,
    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]],
) -> None:
    entry = log_data.get(year_of_state, {})
    current_modifications = entry.setdefault("modifications", {})
    entry["modifications"] = merge_modify_recipes(current_modifications, modify_recipe)
    entry["latest_modified_at"] = str(pd.Timestamp.now())
    log_data[year_of_state] = entry


def shift_code_name_plus1(db, code_prefix):
    existing = set(db.index.astype(str))
    suffix = 1
    candidate = f"{code_prefix}_{suffix}"
    while candidate in existing:
        suffix += 1
        candidate = f"{code_prefix}_{suffix}"
    return candidate


def create_modify_recipe(
    config: Configuration,
    config_section_name: str = 'district_atomic_changes_define',
) -> dict[str, dict[str, dict[str, float | int | str]]]:
    """
    Build modification recipe, pruning None-valued fields and empty components / archetypes.
    
    Args:
        config: Configuration object
        config_section_name: Name of the config section to read from (default: 'district_atomic_changes_define')
    """
    config_section = getattr(config, config_section_name)
    archetypes_to_modify = config_section.archetypes
    if not archetypes_to_modify:
        raise ValueError(
            "No archetypes specified for modification in the event scenario."
        )

    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]] = {}

    for archetype in archetypes_to_modify:
        raw_components = {
            "construction_type": {
                "type_win": config_section.type_win,
                "supply_type_hs": config_section.supply_type_hs,
                "supply_type_cs": config_section.supply_type_cs,
                "supply_type_dhw": config_section.supply_type_dhw,
                "supply_type_el": config_section.supply_type_el,
                "hvac_type_hs": config_section.hvac_type_hs,
                "hvac_type_cs": config_section.hvac_type_cs,
                "hvac_type_dhw": config_section.hvac_type_dhw,
                "hvac_type_ctrl": config_section.hvac_type_ctrl,
                "hvac_type_vent": config_section.hvac_type_vent,
            },
            "wall": {
                "material_name_1": config_section.wall_material_name_1,
                "thickness_1_m": config_section.wall_thickness_1_m,
                "material_name_2": config_section.wall_material_name_2,
                "thickness_2_m": config_section.wall_thickness_2_m,
                "material_name_3": config_section.wall_material_name_3,
                "thickness_3_m": config_section.wall_thickness_3_m,
                "Service_Life": config_section.wall_lifetime,
            },
            "roof": {
                "material_name_1": config_section.roof_material_name_1,
                "thickness_1_m": config_section.roof_thickness_1_m,
                "material_name_2": config_section.roof_material_name_2,
                "thickness_2_m": config_section.roof_thickness_2_m,
                "material_name_3": config_section.roof_material_name_3,
                "thickness_3_m": config_section.roof_thickness_3_m,
                "Service_Life": config_section.roof_lifetime,
            },
            "base": {
                "material_name_1": config_section.base_material_name_1,
                "thickness_1_m": config_section.base_thickness_1_m,
                "material_name_2": config_section.base_material_name_2,
                "thickness_2_m": config_section.base_thickness_2_m,
                "material_name_3": config_section.base_material_name_3,
                "thickness_3_m": config_section.base_thickness_3_m,
                "Service_Life": config_section.base_lifetime,
            },
            "floor": {
                "material_name_1": config_section.floor_material_name_1,
                "thickness_1_m": config_section.floor_thickness_1_m,
                "material_name_2": config_section.floor_material_name_2,
                "thickness_2_m": config_section.floor_thickness_2_m,
                "material_name_3": config_section.floor_material_name_3,
                "thickness_3_m": config_section.floor_thickness_3_m,
                "Service_Life": config_section.floor_lifetime,
            },
        }

        # Construction type edits are code swaps; empty strings are not allowed.
        ct_fields = raw_components.get("construction_type", {})
        for field, value in (ct_fields or {}).items():
            if value is not None and str(value).strip() == "":
                raise ValueError(
                    f"Invalid construction type value for '{field}' in archetype '{archetype}': empty string."
                )

        # Material edits are allowed per-layer.
        # You may change only thickness (keep material) or only material (keep thickness);
        # unspecified values are kept from the current envelope DB entry.
        for component, fields in raw_components.items():
            if component == "construction_type":
                continue
            for i in (1, 2, 3):
                mat = fields[f"material_name_{i}"]
                thk = fields[f"thickness_{i}_m"]

                if mat is not None and str(mat).strip() == "":
                    raise ValueError(
                        f"Invalid {component} material name for layer {i} in archetype '{archetype}': empty string."
                    )
                if thk is not None and thk < 0:
                    raise ValueError(
                        f"Invalid {component} thickness for layer {i} in archetype '{archetype}': {thk}. "
                        "Thickness must be >= 0."
                    )

        # Drop None-valued fields per component
        cleaned_components = {
            comp: {k: v for k, v in fields.items() if v is not None}
            for comp, fields in raw_components.items()
        }

        # Drop empty components
        cleaned_components = {c: f for c, f in cleaned_components.items() if f}

        if cleaned_components:
            modify_recipe[archetype] = cleaned_components

    return modify_recipe


def validate_timeline_name(timeline_name: str) -> str:
    """
    Validate timeline name to ensure it can be used as a folder name.
    
    Parameters:
        timeline_name (str): The timeline name to validate.
    
    Returns:
        str: The validated timeline name (stripped of whitespace).
    
    Raises:
        ValueError: If the timeline name is empty or contains invalid characters.
    """
    if not timeline_name or not str(timeline_name).strip():
        raise ValueError("Timeline name cannot be empty.")
    
    timeline_name = str(timeline_name).strip()
    
    # Check for invalid filesystem characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in timeline_name for char in invalid_chars):
        raise ValueError(
            f"Timeline name contains invalid characters. "
            f"Avoid: {' '.join(invalid_chars)}"
        )
    
    # Check for reserved names on Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    if timeline_name.upper() in reserved_names:
        raise ValueError(
            f"Timeline name '{timeline_name}' is a reserved system name. "
            "Please choose a different name."
        )
    
    # Check for names that start or end with periods or spaces (problematic on Windows)
    if timeline_name.startswith('.') or timeline_name.endswith('.'):
        raise ValueError("Timeline name cannot start or end with a period.")
    
    if timeline_name.endswith(' '):
        raise ValueError("Timeline name cannot end with a space.")
    
    return timeline_name
