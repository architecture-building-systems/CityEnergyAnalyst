"""Native dashboard job entry point for validating all baked states in one pathway."""

from __future__ import annotations

from cea.config import Configuration
from cea.datamanagement.district_pathways.job_output import print_pathway_action_output
from cea.datamanagement.district_pathways.pathway_timeline import validate_all_baked_states


def main(config: Configuration) -> dict:
    pathway_name = config.pathway_state_workflow.existing_pathway_name
    if not pathway_name:
        raise ValueError("Select a pathway before validating all states.")

    summary = validate_all_baked_states(config, pathway_name)
    years = [payload["year"] for payload in summary.get("results", [])]
    print(
        f"Validating {len(years)} pathway state(s) for '{pathway_name}'...",
        flush=True,
    )

    for payload in summary.get("results", []):
        print("", flush=True)
        print(f"[{payload['year']}] Running baked-state validation...", flush=True)
        print_pathway_action_output(payload)

    print("", flush=True)
    print(
        "Validation finished. "
        f"Valid: {len(summary['validated_years'])} | Issues: {len(summary['invalid_years'])}",
        flush=True,
    )

    if summary["invalid_years"]:
        for year in summary["invalid_years"]:
            issues = summary["issues_by_year"].get(year, [])
            if issues:
                print(f"- {year}: {len(issues)} issue(s)", flush=True)
            else:
                print(f"- {year}: validation reported issues", flush=True)
        raise ValueError(
            "Validation reported issues for pathway state year(s): "
            + ", ".join(str(year) for year in summary["invalid_years"])
        )

    return summary


if __name__ == "__main__":
    main(Configuration())
