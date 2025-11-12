#!/usr/bin/env python3
"""
Command line orchestrator for the dual-pipe visualization workflow.

This mirrors the behaviour of the legacy interactive runner by:
  1. Running network routing (`optimize_network_routing`)
  2. Generating the interactive Folium map (`create_interactive_map`)
  3. Creating the dual-pipe HTML dashboard (`create_html_dashboard`)

It also mirrors the legacy directory structure by ensuring artefacts are
available under `street_analysis_outputs/<Street>/`.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from energy_tools import (  # noqa: E402
    optimize_network_routing,
    create_interactive_map,
    create_html_dashboard,
)
SIM_OUTPUT_DIR = PROJECT_ROOT / "simulation_outputs"


def _load_street_name_from_results(scenario: str) -> str:
    results_path = SIM_OUTPUT_DIR / f"{scenario}_results.json"
    if not results_path.exists():
        return scenario
    try:
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("street_name") or scenario
    except Exception:
        return scenario


def _find_scenarios_for_street(street: str) -> list[str]:
    street_lower = street.strip().lower()
    matches: list[str] = []
    for json_path in SIM_OUTPUT_DIR.glob("*_results.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue
        if data.get("street_name", "").lower() == street_lower:
            matches.append(json_path.name.replace("_results.json", ""))
    return matches


def _list_available_scenarios() -> list[str]:
    scenarios: list[str] = []
    for json_path in sorted(SIM_OUTPUT_DIR.glob("*_results.json")):
        scenarios.append(json_path.name.replace("_results.json", ""))
    return scenarios


def _legacy_outputs_exist(street_name: str) -> bool:
    from energy_tools import _legacy_map_name, _legacy_dashboard_name, _ensure_street_output_dir  # type: ignore

    street_dir = _ensure_street_output_dir(street_name)
    map_path = street_dir / _legacy_map_name(street_name)
    dashboard_path = street_dir / _legacy_dashboard_name(street_name)
    return map_path.exists() and dashboard_path.exists()


def run_workflow_for_scenario(scenario: str, force: bool = False, size_pipes: bool = False) -> None:
    print(f"\n=== Running dual-pipe workflow for scenario: {scenario} ===")
    street_name = _load_street_name_from_results(scenario)

    if not force and not size_pipes and _legacy_outputs_exist(street_name):
        print(f"Skipping {scenario}: legacy artefacts already exist for '{street_name}'. Use --force to regenerate.")
        return

    if size_pipes and not force:
        print("🔧 --size-pipes requested; rerunning routing to refresh CHA sizing artefacts.")

    force_recompute = force or size_pipes

    print(optimize_network_routing.func(scenario, force_recompute=force_recompute))
    print(create_interactive_map.func(scenario, force_recompute=force_recompute))
    print(create_html_dashboard.func(scenario, force_recompute=force_recompute))
    print(f"Completed scenario '{scenario}'\n")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dual-pipe workflow runner")
    parser.add_argument(
        "--scenario",
        action="append",
        dest="scenarios",
        help="Scenario name(s) to process (repeatable).",
    )
    parser.add_argument(
        "--street",
        action="append",
        dest="streets",
        help="Street name(s) to process, matching simulation outputs (repeatable).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all scenarios with available simulation outputs.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if legacy artefacts already exist.",
    )
    parser.add_argument(
        "--size-pipes",
        action="store_true",
        help="Recompute CHA pipe sizing between routing and visualization steps.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    if args.list:
        scenarios = _list_available_scenarios()
        if scenarios:
            print("Available scenarios:")
            for scenario in scenarios:
                street = _load_street_name_from_results(scenario)
                print(f"  - {scenario} ({street})")
        else:
            print("No simulation outputs found.")
        return 0

    scenarios_to_run: list[str] = []

    if args.all:
        scenarios_to_run.extend(_list_available_scenarios())

    if args.scenarios:
        scenarios_to_run.extend(args.scenarios)

    if args.streets:
        for street in args.streets:
            matches = _find_scenarios_for_street(street)
            if not matches:
                print(f"⚠️  No scenarios found for street '{street}'.")
            else:
                scenarios_to_run.extend(matches)

    scenarios_to_run = list(dict.fromkeys(scenarios_to_run))  # preserve order, remove duplicates

    if not scenarios_to_run:
        print("No scenarios specified. Use --scenario, --street, or --all (or --list to see options).")
        return 1

    for scenario in scenarios_to_run:
        run_workflow_for_scenario(scenario, force=args.force, size_pipes=args.size_pipes)

    print("Dual-pipe workflow complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

