#!/usr/bin/env python3
"""
CLI orchestrator for street-level heat pump simulations.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.hp.street_selection import (
    DEFAULT_OSM_PATH,
    list_available_streets,
    select_street_interactive,
)
from src.hp.street_workflow import run_hp_street_analysis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run street-focused heat pump (LV) simulations."
    )
    parser.add_argument(
        "--scenario",
        default="hp_with_grid_reinforcement",
        help="HP scenario name (without .json). Default: hp_with_grid_reinforcement",
    )
    parser.add_argument(
        "--street",
        action="append",
        dest="streets",
        help="Street name to simulate (repeatable).",
    )
    parser.add_argument(
        "--buffer-m",
        type=float,
        default=40.0,
        help="Buffer distance (meters) around street to include buildings.",
    )
    parser.add_argument(
        "--osm",
        type=Path,
        default=DEFAULT_OSM_PATH,
        help="Path to OSM file for street geometry (default: data/osm/branitzer_siedlung.osm).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Launch interactive street selection.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available streets and exit.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-run even if cached results exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list:
        print("\nAvailable streets:\n")
        for meta in list_available_streets(args.osm):
            print(
                f"- {meta.name} ({meta.total_length_km:.2f} km, "
                f"{meta.num_segments} segments, types: {', '.join(meta.highway_types)})"
            )
        return 0

    streets: List[str] = []
    if args.streets:
        streets.extend(args.streets)

    if args.interactive:
        selected = select_street_interactive(args.osm)
        if selected:
            streets.append(selected)

    if not streets:
        print("No streets specified. Use --street or --interactive (or --list to inspect options).")
        return 1

    results = []
    for street in streets:
        print("\n" + "=" * 80)
        print(f"Running street simulation for: {street}")
        print("=" * 80)
        try:
            result = run_hp_street_analysis(
                scenario_name=args.scenario,
                street_name=street,
                buffer_m=args.buffer_m,
                force=args.force,
                osm_path=args.osm,
            )
            results.append(result)
            metadata = result.get("metadata", {})
            kpi = result.get("result", {}).get("kpi", {})
            print(f"  Buildings included: {metadata.get('filtered_buildings')} / {metadata.get('total_buildings')}")
            print(f"  Min voltage (pu): {kpi.get('min_voltage_pu', 'n/a')}")
            print(f"  Max line loading (%): {kpi.get('max_line_loading_pct', 'n/a')}")
            print(f"  Output directory: {result.get('output_dir')}")
        except Exception as exc:
            print(f"  ❌ Failed to run simulation for street '{street}': {exc}")

    if results:
        output_summary = Path("simulation_outputs") / "hp_street_batch_summary.json"
        with output_summary.open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nSummary written to {output_summary}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


