import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from typing import Any, Literal, cast

import geopandas as gpd
import pandas as pd

from cea.config import Configuration
from cea.datamanagement.archetypes_mapper import archetypes_mapper
from cea.datamanagement.database.envelope_lookup import EnvelopeLookup
from cea.datamanagement.databases_verification import verify_input_geometry_zone
from cea.datamanagement.district_pathways.pathway_integrity import (
    check_district_pathway_log_yaml_integrity,
    merge_modify_recipes,
)
from cea.datamanagement.district_pathways.envelope_topology import (
    validate_three_layer_topology,
)
from cea.datamanagement.district_pathways.pathway_log import (
    add_year_in_pathway_yaml,
    del_year_in_pathway_yaml,
    load_pathway_log_yaml,
    save_pathway_log_yaml,
)
from cea.datamanagement.district_pathways.pathway_status import (
    collect_state_phase_status,
    record_baked_state,
    record_simulated_state,
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


@dataclass
class DistrictStateYear:
    """Represents a single state year definition and its on-disk realisation (if any)."""
    pathway_name: str
    year: int
    modifications: ModifyRecipe
    main_locator: InputLocator

    def state_folder(self) -> str:
        return self.main_locator.get_state_in_time_scenario_folder(self.pathway_name, int(self.year))

    def signature_path(self) -> str:
        return os.path.join(
            self.state_folder(), ".district_pathway_signature.json"
        )

    def exists_on_disk(self) -> bool:
        return os.path.exists(self.state_folder())

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

        status = str(rec.get("simulation_status") or "").strip().lower()
        if status:
            return status != "simulated"

        # Backward compatibility for older records without simulation_status.
        return not bool(rec.get("simulated_at"))

    def mark_simulated(
        self,
        *,
        workflow: list[dict[str, Any]] | None = None,
    ) -> None:
        rec = self.read_signature_record() or {"year": int(self.year)}
        now = str(pd.Timestamp.now())
        rec["simulated_at"] = now
        rec["simulation_status"] = "simulated"
        if workflow is not None:
            rec["simulated_workflow"] = workflow
        self.write_signature_record(rec)

    def simulate(
        self,
        main_config: Configuration,
        *,
        workflow: list[dict[str, Any]],
        mark_simulated: bool = True,
        recorded_workflow: list[dict[str, Any]] | None = None,
    ) -> None:
        """Run the standard simulation workflow for this state year.

        This is a state-level operation: it executes the workflow in the `state_{year}` scenario and then
        optionally updates the per-state status file to mark the state as simulated.

        Note:
            `mark_simulated` and `recorded_workflow` are still needed even though the Step 4
            wrapper no longer exposes a pending-only mode. Step 4 now runs in two passes
            (`base workflow` first, then `post-demand workflow`), so the first pass must not
            label the state as fully simulated before the second pass finishes.
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
            isinstance(scenario_config.emissions.year_end, int)
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

        if mark_simulated:
            self.mark_simulated(
                workflow=recorded_workflow if recorded_workflow is not None else workflow
            )

    def mark_built(self) -> None:
        path = self.signature_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        rec = {
            "year": int(self.year),
            "built_at": str(pd.Timestamp.now()),
            # A rebuilt / newly built state needs simulation.
            "simulation_status": "needs_simulation",
            "simulated_at": None,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)


class DistrictEvolutionPathway:
    """Manage district evolution pathway definitions (YAML) and materialise state scenarios from them.
    The config points to the main scenario; the pathway_name selects which district evolution pathway to manage."""

    def __init__(self, config: Configuration, pathway_name: str):
        self.config = config
        self.main_locator = InputLocator(config.scenario)
        self.pathway_name = validate_pathway_name(pathway_name)
        # Ensure the district evolution pathway folder exists for first-time runs.
        os.makedirs(self.main_locator.get_district_pathway_folder(self.pathway_name), exist_ok=True)
        self.log_data: dict[int, dict[str, Any]] = load_pathway_log_yaml(
            self.main_locator,
            allow_missing=True,
            allow_empty=True,
            pathway_name=self.pathway_name,
        )

    def list_state_years_on_disk(self) -> list[int]:
        """Return sorted list of state years present under `district_pathways/{pathway_name}/state_YYYY/`."""
        years: list[int] = []
        pathway_folder = self.main_locator.get_district_pathway_folder(self.pathway_name)
        if not os.path.exists(pathway_folder):
            return years
        for name in os.listdir(pathway_folder):
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
        """Compute which years should have a ``state_{year}`` folder.

        A year is required if something *happens* at that year:
        - A building is constructed (effective construction year from lifecycle intervals).
        - A building is demolished.
        - A modification or building event is defined in the YAML log.

        Years where buildings merely *exist* (carried over from an earlier construction)
        but nothing changes are excluded.
        """
        intervals = self.get_building_lifecycle_intervals()

        # Collect years where a lifecycle event occurs
        event_years: set[int] = set()
        for ivs in intervals.values():
            for start, end in ivs:
                event_years.add(start)
                if end is not None:
                    event_years.add(end)

        # Also include log years with actual content (modifications or building events)
        for year in self.log_data.keys():
            entry = self.log_data.get(int(year), {}) or {}
            events = entry.get("building_events", {}) or {}
            has_content = (
                bool(entry.get("modifications"))
                or bool(events.get("new_buildings"))
                or bool(events.get("demolished_buildings"))
            )
            if has_content:
                event_years.add(int(year))

        # Filter out years with no active buildings
        return sorted(
            year for year in event_years
            if any(
                self._is_building_active(name, year, intervals)
                for name in intervals
            )
        )

    def get_explicit_building_events(self, year: int) -> dict[str, list[str]]:
        entry = self.log_data.get(int(year), {}) or {}
        events = entry.get("building_events", {}) or {}
        return {
            "new_buildings": sorted(
                {str(value) for value in (events.get("new_buildings", []) or [])}
            ),
            "demolished_buildings": sorted(
                {
                    str(value)
                    for value in (events.get("demolished_buildings", []) or [])
                }
            ),
        }

    def get_building_lifecycle_intervals(self) -> dict[str, list[tuple[int, int | None]]]:
        """Return {building_name: [(start, end), ...]} lifecycle intervals.

        Walk all events chronologically. Each construction starts a new interval.
        Each demolition ends the current interval. Supports unlimited rebuild cycles.

        Rules:
        - zone.shp ``year`` provides the initial construction year.
        - A ``new_buildings`` event overrides/sets the construction year.
        - A ``demolished_buildings`` event ends the current interval.
        - A ``new_buildings`` event AFTER a demolition starts a new interval (rebuild).
        - ``end`` is ``None`` if the building is never demolished after last construction.
        - All year boundaries are Jan 1: ``demolition_year == construction_year`` means the
          building never exists during that interval.
        """
        base_years = self.get_building_construction_years()
        intervals: dict[str, list[tuple[int, int | None]]] = {
            name: [(year, None)] for name, year in base_years.items()
        }

        for year in sorted(int(y) for y in self.log_data.keys()):
            events = self.get_explicit_building_events(int(year))

            # Process demolitions first (so rebuild in same year works)
            for name in events["demolished_buildings"]:
                name = str(name)
                if name in intervals and intervals[name]:
                    last = intervals[name][-1]
                    if last[1] is None:  # open interval
                        intervals[name][-1] = (last[0], int(year))

            # Process constructions
            for name in events["new_buildings"]:
                name = str(name)
                if name not in intervals:
                    intervals[name] = [(int(year), None)]
                else:
                    last = intervals[name][-1]
                    if last[1] is not None:
                        # Previously demolished — rebuild (new interval)
                        intervals[name].append((int(year), None))
                    else:
                        # Still alive — update construction year (retime)
                        intervals[name][-1] = (int(year), last[1])

        return intervals

    def _is_building_active(self, name: str, year: int, intervals: dict[str, list[tuple[int, int | None]]] | None = None) -> bool:
        """Check if a building is active at a given year based on lifecycle intervals."""
        if intervals is None:
            intervals = self.get_building_lifecycle_intervals()
        for start, end in intervals.get(name, []):
            if start <= year and (end is None or end > year):
                return True
        return False

    def get_manual_new_building_years(self) -> dict[str, int]:
        """Return the latest manual construction year per building."""
        out: dict[str, int] = {}
        for year in sorted(int(y) for y in self.log_data.keys()):
            events = self.get_explicit_building_events(int(year))
            for building_name in events["new_buildings"]:
                out[str(building_name)] = int(year)
        return out

    def get_building_demolition_years(self) -> dict[str, int]:
        """Return the latest demolition year per building."""
        out: dict[str, int] = {}
        for year in sorted(int(y) for y in self.log_data.keys()):
            events = self.get_explicit_building_events(int(year))
            for building_name in events["demolished_buildings"]:
                out[str(building_name)] = int(year)
        return out

    def get_effective_construction_years(self) -> dict[str, int]:
        """Return the latest effective construction year per building.

        For buildings with multiple lifecycle intervals, returns the start of the last interval.
        """
        intervals = self.get_building_lifecycle_intervals()
        return {
            name: ivs[-1][0]
            for name, ivs in intervals.items()
            if ivs
        }

    def get_derived_stock_new_buildings(self, year: int) -> list[str]:
        base_construction_years = self.get_building_construction_years()
        manual_new_years = self.get_manual_new_building_years()
        demolition_years = self.get_building_demolition_years()
        return sorted(
            building_name
            for building_name, construction_year in base_construction_years.items()
            if int(construction_year) == int(year)
            and (
                building_name not in manual_new_years
                # Keep stock entry if the building is also demolished at the manual year
                # (demolish+rebuild), since the original stock construction is still valid
                or (
                    building_name in demolition_years
                    and demolition_years[building_name] == manual_new_years[building_name]
                )
            )
        )

    def get_combined_building_events(self, year: int) -> dict[str, list[str]]:
        explicit_events = self.get_explicit_building_events(int(year))
        return {
            "new_buildings": sorted(
                set(explicit_events["new_buildings"])
                | set(self.get_derived_stock_new_buildings(int(year)))
            ),
            "demolished_buildings": explicit_events["demolished_buildings"],
        }

    def get_active_buildings_by_year(self) -> dict[int, list[str]]:
        intervals = self.get_building_lifecycle_intervals()
        out: dict[int, list[str]] = {}

        for year in self.required_state_years():
            active = [
                name
                for name in intervals
                if self._is_building_active(name, int(year), intervals)
            ]
            out[int(year)] = sorted(active)

        return out

    def ensure_state_years_exist(
        self,
        years: list[int],
        *,
        update_yaml: bool = True,
    ) -> dict[int, dict[str, Any]]:
        """Ensure `state_{year}` folders exist for all requested years.

        - Creates missing `state_{year}` folders by copying inputs.
        - Syncs building existence from cumulative stock + pathway building events.
        - Ensures YAML entries exist (empty modifications by default).

        Returns the (possibly updated) YAML log data in memory.
        """
        existing_years = set(self.list_state_years_on_disk())
        years_sorted = sorted(set(int(y) for y in years))
        active_buildings_by_year = self.get_active_buildings_by_year()
        for year in years_sorted:
            if year not in existing_years:
                create_state_in_time_scenario(
                    self.config,
                    pathway_name=self.pathway_name,
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

            sync_buildings_in_event_scenario(
                self.config,
                self.pathway_name,
                year,
                active_buildings=set(active_buildings_by_year.get(int(year), [])),
            )

        if update_yaml:
            self.save()

        return self.log_data

    def ensure_year(self, year: int) -> None:
        if year not in self.log_data:
            self.log_data[year] = {
                "created_at": str(pd.Timestamp.now()),
                "modifications": {},
            }

    def ensure_manual_year(self, year: int) -> None:
        self.ensure_year(year)
        entry = self.log_data.get(year, {}) or {}
        entry.setdefault("created_at", str(pd.Timestamp.now()))
        entry.setdefault("modifications", {})
        self.log_data[year] = entry

    def apply_year_modifications(self, year: int, modify_recipe: ModifyRecipe) -> None:
        self.ensure_year(year)
        entry = self.log_data.get(year, {}) or {}
        current = entry.get("modifications", {}) or {}
        entry["modifications"] = merge_modify_recipes(current, modify_recipe)
        entry["latest_modified_at"] = str(pd.Timestamp.now())
        self.log_data[year] = entry

    def update_year_building_events(
        self,
        year: int,
        *,
        new_buildings: list[str],
        demolished_buildings: list[str],
    ) -> None:
        valid_buildings = set(self.get_building_construction_years().keys())
        clean_new = sorted(
            {str(value) for value in new_buildings if str(value).strip()}
        )
        clean_demolished = sorted(
            {
                str(value)
                for value in demolished_buildings
                if str(value).strip()
            }
        )

        unknown = (set(clean_new) | set(clean_demolished)) - valid_buildings
        if unknown:
            raise ValueError(
                f"Unknown building names: {', '.join(sorted(unknown))}"
            )

        # Clean up: remove buildings from new_buildings in other years
        # when they are being retimed to this year (avoids duplicate construction events)
        if clean_new:
            for other_year in list(self.log_data.keys()):
                if int(other_year) == int(year):
                    continue
                other_entry = self.log_data.get(int(other_year), {}) or {}
                other_events = other_entry.get("building_events", {}) or {}
                other_new = other_events.get("new_buildings", []) or []
                if other_new:
                    cleaned = [b for b in other_new if b not in clean_new]
                    if len(cleaned) != len(other_new):
                        other_events["new_buildings"] = cleaned
                        other_entry["building_events"] = other_events
                        self.log_data[int(other_year)] = other_entry

        self.ensure_year(year)
        entry = self.log_data.get(int(year), {}) or {}
        existing_events = entry.get("building_events", {}) or {}

        # Replace the event types being written, preserve the other type.
        # e.g. writing new_buildings replaces existing new_buildings but keeps demolished_buildings.
        result_new = clean_new if clean_new else list(existing_events.get("new_buildings", []) or [])
        result_demolished = clean_demolished if clean_demolished else list(existing_events.get("demolished_buildings", []) or [])

        if result_new or result_demolished:
            entry["building_events"] = {
                "new_buildings": result_new,
                "demolished_buildings": result_demolished,
            }
        else:
            entry.pop("building_events", None)
        entry["latest_modified_at"] = str(pd.Timestamp.now())
        self.log_data[int(year)] = entry

    def save(self) -> None:
        for year, entry in list(self.log_data.items()):
            cleaned_entry = (entry or {}).copy()
            cleaned_entry.pop("manual_state", None)
            self.log_data[year] = cleaned_entry

        # Remove empty entries (no modifications, no building events)
        for year in list(self.log_data.keys()):
            entry = self.log_data.get(year, {}) or {}
            events = entry.get("building_events", {}) or {}
            has_new = bool(events.get("new_buildings"))
            has_demolished = bool(events.get("demolished_buildings"))
            has_modifications = bool(entry.get("modifications"))
            if not has_new and not has_demolished and not has_modifications:
                del self.log_data[year]

        save_pathway_log_yaml(self.main_locator, self.log_data, pathway_name=self.pathway_name)

    def sync_year_entries_from_required_years(self, years: list[int]) -> None:
        for year in sorted(set(int(y) for y in years)):
            entry = self.log_data.get(year, {}) or {}
            if not entry:
                continue
            if entry.get("created_at") in (None, "", "null"):
                entry["created_at"] = str(pd.Timestamp.now())
            entry.setdefault("modifications", {})
            self.log_data[year] = entry

    def state_years(self) -> list[DistrictStateYear]:
        years = sorted(self.log_data.keys())
        out: list[DistrictStateYear] = []
        for y in years:
            entry = self.log_data.get(y, {}) or {}
            mods = entry.get("modifications", {}) or {}
            out.append(
                DistrictStateYear(
                    pathway_name=self.pathway_name, year=int(y), modifications=mods, main_locator=self.main_locator
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

    def source_payload_for_year(self, year: int) -> dict[str, Any]:
        return {
            "year": int(year),
            "cumulative_modifications": self.cumulative_by_year().get(int(year), {}),
            "explicit_building_events": self.get_explicit_building_events(int(year)),
            "combined_building_events": self.get_combined_building_events(int(year)),
            "active_buildings": self.get_active_buildings_by_year().get(int(year), []),
        }

    def source_log_hash_for_year(self, year: int) -> str:
        payload = self.source_payload_for_year(int(year))
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def bake_states_from_log(self) -> None:
        years = self.required_state_years()
        if not years:
            raise ValueError(
                "No district event years or building construction years found."
            )

        print(
            "Building pathway state scenarios from the district evolution pathway log...",
            flush=True,
        )
        print(f"Years to build: {years}", flush=True)

        cumulative = self.cumulative_by_year()
        active_buildings_by_year = self.get_active_buildings_by_year()

        built_years: list[int] = []
        skipped_years: list[int] = []

        for year in years:
            # Skip years that are already baked and up to date
            state = DistrictStateYear(
                pathway_name=self.pathway_name,
                year=int(year),
                modifications=self.log_data.get(int(year), {}).get("modifications", {})
                or {},
                main_locator=self.main_locator,
            )
            signature = state.read_signature_record() or {}
            status = collect_state_phase_status(
                self.main_locator,
                pathway_name=self.pathway_name,
                year=int(year),
                source_log_hash=self.source_log_hash_for_year(int(year)),
                signature=signature,
            )
            phase = status.get("primary_phase", "none")
            stale = status.get("has_stale_phase", False)
            if phase in ("baked", "simulated") and not stale:
                skipped_years.append(int(year))
                print(f"- state_{int(year)}: up to date, skipping", flush=True)
                continue

            year_recipe = cumulative.get(int(year), {})

            state_folder = state.state_folder()
            print(f"- Building state_{int(year)}...", flush=True)

            # Rebuild the state folder deterministically to avoid code drift in envelope codes.
            if os.path.exists(state_folder):
                shutil.rmtree(state_folder, ignore_errors=True)

            create_state_in_time_scenario(
                self.config, self.pathway_name, int(year), update_yaml=False
            )

            sync_buildings_in_event_scenario(
                self.config,
                self.pathway_name,
                int(year),
                active_buildings=set(active_buildings_by_year.get(int(year), [])),
                effective_construction_years=self.get_effective_construction_years(),
            )

            # Apply cumulative archetype modifications if specified
            if year_recipe:
                _apply_state_construction_changes(
                    self.config,
                    self.pathway_name,
                    int(year),
                    year_recipe,
                )
                print(
                    "  Applied cumulative modifications from the pathway log",
                    flush=True,
                )
            else:
                print(
                    "  No modifications for this year (baseline state)",
                    flush=True,
                )

            # Verify consistency: databases and properties must be in sync
            # This final check ensures the state is ready for simulation
            print(
                "  State databases and building properties are consistent",
                flush=True,
            )

            state.mark_built()
            signature = state.read_signature_record() or {}
            record_baked_state(
                self.main_locator,
                pathway_name=self.pathway_name,
                year=int(year),
                built_at=str(signature.get("built_at") or pd.Timestamp.now()),
                source_log_hash=self.source_log_hash_for_year(int(year)),
            )
            built_years.append(int(year))

        print("District state materialisation finished.", flush=True)
        print(f"Created/updated: {len(built_years)} | Skipped (up to date): {len(skipped_years)}", flush=True)
        if built_years:
            print(f"Years created/updated: {built_years}", flush=True)
        if skipped_years:
            print(f"Years skipped: {skipped_years}", flush=True)

        print(
            f"Pathway folder: {self.main_locator.get_district_pathway_folder(pathway_name=self.pathway_name)}",
            flush=True,
        )
        print(
            f"Log file: {self.main_locator.get_district_pathway_log_file(pathway_name=self.pathway_name)}",
            flush=True,
        )
        print(
            "Each built state folder contains simulation status metadata in '.district_pathway_signature.json'.",
            flush=True,
        )

        check_district_pathway_log_yaml_integrity(self.config, self.pathway_name)

    def simulate_states(
        self,
        *,
        simulation_mode: Literal["pending", "all"],
        workflow: list[dict[str, Any]],
        state_workflows: dict[int, list[dict[str, Any]]] | None = None,
    ) -> None:
        """Simulate pathway states.

        - `pending`: simulate only states that have not been simulated yet, or whose construction changes
          mean results are out of date.
        - `all`: simulate every `state_{year}` folder present in the selected pathway.

        Note:
            The dedicated Step 4 wrapper in `state_simulation/main.py` no longer calls this helper,
            because thermal-network reuse makes Step 4 state years interdependent and it now
            orchestrates a two-pass `all` run directly. This method remains available as a
            generic pathway helper for other callers.

        This updates both:
        - per-state status files (`.district_pathway_signature.json`)
        - the district evolution pathway log (`district_pathway_log.yml`) with timestamps / workflow metadata.

        Args:
            simulation_mode: "pending" or "all"
            workflow: Default workflow to use for all states (fallback)
            state_workflows: Optional dict mapping year -> custom workflow for that state
                           If provided, uses custom workflow for each year; otherwise uses default workflow
        """
        # Validate that all state folders match YAML before simulation
        check_district_pathway_log_yaml_integrity(self.config, self.pathway_name)

        if simulation_mode not in {"pending", "all"}:
            raise ValueError(
                f"Invalid simulation mode: {simulation_mode}. Expected one of: pending, all"
            )

        state_years = self.list_state_years_on_disk()
        if not state_years:
            raise ValueError(
                "No pathway states found in the district evolution pathway folder."
            )
        state_years.sort()

        if simulation_mode == "pending":
            years_to_simulate = [
                y
                for y in state_years
                if DistrictStateYear(
                    pathway_name=self.pathway_name, year=int(y), modifications={}, main_locator=self.main_locator
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
                    "State year {year} exists in the district evolution pathway folder, but it is missing from the district evolution pathway log.".format(
                        year=year
                    )
                )

            # Use state-specific workflow if provided, otherwise use default
            year_workflow = workflow
            if state_workflows and int(year) in state_workflows:
                year_workflow = state_workflows[int(year)]
                print(f"Using custom workflow for state {year}")

            print(f"Simulating pathway state for year {year}...")
            DistrictStateYear(
                pathway_name=self.pathway_name, year=int(year), modifications={}, main_locator=self.main_locator
            ).simulate(self.config, workflow=year_workflow)

            # Log metadata in the YAML log.
            entry = self.log_data.get(int(year), {}) or {}
            entry["simulation_workflow"] = year_workflow
            simulated_at = str(pd.Timestamp.now())
            entry["latest_simulated_at"] = simulated_at
            self.log_data[int(year)] = entry
            record_simulated_state(
                self.main_locator,
                pathway_name=self.pathway_name,
                year=int(year),
                simulated_at=simulated_at,
                source_log_hash=self.source_log_hash_for_year(int(year)),
                workflow=year_workflow,
            )

            simulated_years.append(int(year))
            print(f"Simulation for pathway state year {year} completed.")

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
    pathway_name: str,
    year_of_state: int,
    *,
    update_yaml: bool = True,
) -> None:
    """
    Create a new pathway state scenario based on the current scenario.
    Parameters:
        config (Configuration): The configuration object containing the current scenario settings.
        pathway_name (str): The name of the pathway.
        year_of_state (int): The year of the pathway state. If a building year is larger than
        this year, it will not be included in the pathway state.
    Returns:
        None
    """
    main_locator = InputLocator(config.scenario)
    state_scenario_folder = main_locator.get_state_in_time_scenario_folder(
        pathway_name=pathway_name, year_of_state=year_of_state
    )
    input_folder_path = main_locator.get_input_folder()
    state_locator = InputLocator(state_scenario_folder)
    # Copy all files from the input folder to the pathway-state folder.
    shutil.copytree(
        input_folder_path, state_locator.get_input_folder(), dirs_exist_ok=True
    )  # make sure existing files are overwritten
    if update_yaml:
        add_year_in_pathway_yaml(config, year_of_state, pathway_name=pathway_name)
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


def remove_state_in_time_scenario(config: Configuration, pathway_name: str, year_of_state: int) -> None:
    """Delete an existing pathway state scenario."""
    locator = InputLocator(config.scenario)
    state_scenario_folder = locator.get_state_in_time_scenario_folder(pathway_name, year_of_state)
    shutil.rmtree(state_scenario_folder, ignore_errors=True)
    del_year_in_pathway_yaml(config, year_of_state, pathway_name=pathway_name)
    return None


def delete_unexisting_buildings_from_event_scenario(
    config: Configuration, pathway_name: str, year_of_state: int
) -> list[str]:
    """
    Remove buildings not yet born in the specified state year and regenerate building properties.
    
    This function:
    1. Identifies buildings whose construction year is after year_of_state
    2. Deletes them from zone.shp geometry
    3. Deletes their schedule files
    4. Regenerates all building property files (supply, architecture, etc.) from archetypes
       for the remaining buildings
    
    Parameters:
        config: Configuration object containing the main scenario settings
        pathway_name: Name of the pathway
        year_of_state: The state year - buildings with construction year > this will be deleted
        
    Returns:
        List of building names that were deleted
        
    Note: This function ensures building properties are consistent with zone.shp after deletion.
    """
    locator = InputLocator(config.scenario)
    state_scenario_folder = locator.get_state_in_time_scenario_folder(pathway_name, year_of_state)
    state_locator = InputLocator(state_scenario_folder)
    
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

    # Delete schedule files for removed buildings
    for building_name in buildings_to_delete:
        delete_building_schedule(state_locator, building_name)

    # Remove buildings from zone.shp geometry
    geometry_gdf, _, _ = shapefile_to_WSG_and_UTM(state_locator.get_zone_geometry())
    geometry_gdf.set_index("name", inplace=True)
    geometry_gdf = geometry_gdf.drop(buildings_to_delete, errors="ignore")
    verify_input_geometry_zone(geometry_gdf.reset_index())
    geometry_gdf.to_file(state_locator.get_zone_geometry())

    # Regenerate building properties from archetypes
    # This removes deleted buildings from property CSV files and ensures consistency
    _regenerate_building_properties_from_archetypes(state_locator)

    return buildings_to_delete


def sync_buildings_in_event_scenario(
    config: Configuration,
    pathway_name: str,
    year_of_state: int,
    *,
    active_buildings: set[str],
    effective_construction_years: dict[str, int] | None = None,
) -> list[str]:
    """Sync a copied state scenario to the expected building set for that year.

    The state folder is created from the full main-scenario inputs, so this helper only needs to
    remove buildings that should not exist in the baked state, update the ``year`` column to
    reflect effective construction years (e.g. after a demolish+rebuild), and then regenerate
    dependent per-building inputs from the remaining archetypes.
    """
    locator = InputLocator(config.scenario)
    state_scenario_folder = locator.get_state_in_time_scenario_folder(
        pathway_name, year_of_state
    )
    state_locator = InputLocator(state_scenario_folder)

    if not os.path.exists(state_locator.get_zone_geometry()):
        raise FileNotFoundError(
            f"Event scenario folder for year {year_of_state} does not exist."
        )

    geometry_gdf, _, _ = shapefile_to_WSG_and_UTM(state_locator.get_zone_geometry())
    geometry_gdf.set_index("name", inplace=True)

    current_buildings = set(str(name) for name in geometry_gdf.index)
    buildings_to_delete = sorted(current_buildings - set(active_buildings))

    for building_name in buildings_to_delete:
        delete_building_schedule(state_locator, building_name)

    geometry_gdf = geometry_gdf.loc[
        geometry_gdf.index.intersection(sorted(active_buildings))
    ]

    # Update year column to reflect effective construction years from lifecycle intervals
    if effective_construction_years and "year" in geometry_gdf.columns:
        for building_name in geometry_gdf.index:
            if str(building_name) in effective_construction_years:
                geometry_gdf.at[building_name, "year"] = effective_construction_years[str(building_name)]

    verify_input_geometry_zone(geometry_gdf.reset_index())
    geometry_gdf.to_file(state_locator.get_zone_geometry())
    _regenerate_building_properties_from_archetypes(state_locator)
    return buildings_to_delete


def delete_building_schedule(state_locator: InputLocator, building_name: str) -> None:
    """
    Delete the schedule file related to a specific building in the pathway state.
    This includes the following file:
    - building schedule file (`locator.get_building_weekly_schedules(building_name)`)
    """
    schedule_file_path = state_locator.get_building_weekly_schedules(building_name)
    if os.path.exists(schedule_file_path):
        os.remove(schedule_file_path)
    return None


def _apply_state_construction_changes(
    config: Configuration,
    pathway_name: str,
    year_of_state: int,
    modify_recipe: dict[str, dict[str, dict[str, float | int | str]]],
) -> bool:
    """Apply construction changes to the state scenario archetype databases and regenerate building properties.

    This function atomically performs the following:

    1. **Modify archetype databases** (in the state folder's `inputs/database/`):
       - Reads `construction_types.csv` to get archetype â†’ component code mappings
       - For `construction_type` fields (e.g., `type_win`, `supply_type_hs`): updates values directly
       - For envelope components (wall/roof/base/floor): creates NEW envelope rows with modified
         materials/thicknesses, then updates the archetype's `type_{component}` pointer to the new code
       - Saves both `construction_types.csv` and envelope CSVs (wall.csv, roof.csv, floor.csv)

    2. **Regenerate per-building property files** (in `inputs/building-properties/`):
       - Calls `archetypes_mapper` to derive building properties from the modified archetypes
       - Updates: architecture.dbf, air_conditioning_systems.csv, indoor_comfort.csv,
         internal_loads.csv, supply.csv, and schedule files
       - Buildings don't store envelope data directly â€” they reference archetypes

    Parameters:
        config: Configuration object pointing to the main scenario
        pathway_name: Name of the district evolution pathway
        year_of_state: The year of the state folder to modify (e.g., 2030 â†’ state_2030/)
        modify_recipe: Nested dict specifying modifications::

            {
                "ARCHETYPE_NAME": {
                    "construction_type": {  # Direct fields on construction_types.csv
                        "type_win": "WIN_CODE",
                        "supply_type_hs": "SUPPLY_CODE",
                        ...
                    },
                    "wall": {  # Creates new envelope row, updates type_wall pointer
                        "material_name_1": "concrete_xyz",
                        "thickness_1_m": 0.15,
                        "Service_Life": 50,
                        ...
                    },
                    "roof": {...},
                    "base": {...},  # Maps to floor.csv
                    "floor": {...},
                }
            }

            - Outer keys: archetype names (must exist in construction_types.csv)
            - Middle keys: "construction_type" or component names (wall/roof/base/floor)
            - Inner keys: field names matching database columns
            - Values: new values (None = keep existing)

        use_transaction: If True, takes a snapshot before modifications and restores on error.
            Set to False during bake (folder is freshly created, no need for rollback).

    Returns:
        True if any database values were actually modified, False otherwise.

    Raises:
        ValueError: If modify_recipe is empty or an archetype/field doesn't exist in the databases

    Note:
        This function does NOT update the district evolution pathway YAML log. The caller (typically
        `bake_states_from_log`) is responsible for managing the YAML log separately.
    """
    archetypes_to_modify = modify_recipe.keys()
    if not archetypes_to_modify:
        raise ValueError(
            f"No archetypes specified for modification in state_{year_of_state}. "
            "modify_recipe must contain at least one archetype."
        )

    main_locator = InputLocator(config.scenario)
    state_scenario_folder = main_locator.get_state_in_time_scenario_folder(
        pathway_name, year_of_state
    )
    state_locator = InputLocator(state_scenario_folder)

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
                    new_row["description"] = (
                        f"Modified {component} for archetype {archetype} in year {year_of_state}, "
                        f"based on {code_current}, fields: {', '.join(modifications.keys())}"
                    )
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
        
        # Regenerate building properties from modified archetypes
        # This ensures per-building CSV files reflect the archetype changes
        _regenerate_building_properties_from_archetypes(state_locator)
        
        return True
    except Exception:
        raise


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
    config_section_name: str = 'pathway_intervention_templates_define',
) -> dict[str, dict[str, dict[str, float | int | str]]]:
    """
    Build modification recipe, pruning None-valued fields and empty components / archetypes.
    
    Args:
        config: Configuration object
        config_section_name: Name of the config section to read from (default: 'pathway_intervention_templates_define')
    """
    config_section = getattr(config, config_section_name)
    archetypes_to_modify = config_section.archetypes
    if not archetypes_to_modify:
        raise ValueError(
            "No archetypes specified for modification in the pathway state."
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


def validate_pathway_name(pathway_name: str) -> str:
    """
    Validate pathway name to ensure it can be used as a folder name.
    
    Parameters:
        pathway_name (str): The pathway name to validate.
    
    Returns:
        str: The validated pathway name (stripped of whitespace).
    
    Raises:
        ValueError: If the pathway name is empty or contains invalid characters.
    """
    if not pathway_name or not str(pathway_name).strip():
        raise ValueError("Pathway name cannot be empty.")
    
    pathway_name = str(pathway_name).strip()
    
    # Check for invalid filesystem characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    if any(char in pathway_name for char in invalid_chars):
        raise ValueError(
            f"Pathway name contains invalid characters. "
            f"Avoid: {' '.join(invalid_chars)}"
        )
    
    # Check for reserved names on Windows
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    if pathway_name.upper() in reserved_names:
        raise ValueError(
            f"Pathway name '{pathway_name}' is a reserved system name. "
            "Please choose a different name."
        )
    
    # Check for names that start or end with periods or spaces (problematic on Windows)
    if pathway_name.startswith('.') or pathway_name.endswith('.'):
        raise ValueError("Pathway name cannot start or end with a period.")
    
    return pathway_name
