#!/usr/bin/env python3
"""
Utility script to compare agent system dual-pipe outputs with legacy originals.

Usage:
    python scripts/compare_dual_pipe_outputs.py --street "Anton-Bruckner-Straße"
    python scripts/compare_dual_pipe_outputs.py --scenario Demo_Parkstrasse_DH

The script prints a summary of differences for:
  - Dashboard HTML
  - Interactive map HTML
  - Network stats JSON
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
LEGACY_ROOT = PROJECT_ROOT.parent / "street_final_copy_3"


def _sanitize_street_dirname(street: str) -> str:
    safe = street.strip()
    if not safe:
        return "Unknown_Street"
    safe = safe.replace("/", "_")
    safe = safe.replace(" ", "-")
    return safe


def _slug_from_scenario(scenario: str) -> str:
    return scenario.replace(" ", "_")


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def diff_text(left: str, right: str, label_left: str, label_right: str) -> list[str]:
    diff = difflib.unified_diff(
        left.splitlines(),
        right.splitlines(),
        fromfile=label_left,
        tofile=label_right,
        lineterm="",
    )
    return list(diff)


def compare_html(agent_path: Path, legacy_path: Path, title: str) -> None:
    print(f"\n=== {title} ===")
    if not agent_path.exists():
        print(f"[agent] missing: {agent_path}")
        return
    if not legacy_path.exists():
        print(f"[legacy] missing: {legacy_path}")
        return

    agent_html = agent_path.read_text(encoding="utf-8")
    legacy_html = legacy_path.read_text(encoding="utf-8")

    if agent_html == legacy_html:
        print("No differences detected.")
        return

    diff = diff_text(agent_html, legacy_html, str(agent_path), str(legacy_path))
    if diff:
        print("\n".join(diff[:200]))
        if len(diff) > 200:
            print(f"... (diff truncated, total {len(diff)} lines)")
    else:
        print("Diff too large or no textual differences captured.")


def compare_json(agent_path: Path, legacy_path: Path, title: str) -> None:
    print(f"\n=== {title} ===")
    agent_data = _load_json(agent_path)
    legacy_data = _load_json(legacy_path)
    if not agent_data or not legacy_data:
        print(f"Agent data found: {bool(agent_data)}, Legacy data found: {bool(legacy_data)}")
        return

    missing = [key for key in legacy_data if key not in agent_data]
    if missing:
        print(f"Keys missing from agent stats: {missing}")

    for key in legacy_data:
        if key in agent_data and agent_data[key] != legacy_data[key]:
            print(f"{key}: agent={agent_data[key]!r}, legacy={legacy_data[key]!r}")


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare agent dual-pipe outputs with legacy data")
    parser.add_argument(
        "--street",
        help="Street name (e.g., 'Anton-Bruckner-Straße'). Matches legacy folder names.",
    )
    parser.add_argument(
        "--scenario",
        help="Scenario name (e.g., 'Demo_Parkstrasse_DH').",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum diff lines to display for HTML comparisons (default: 200).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_parser().parse_args(argv or sys.argv[1:])
    if not args.street and not args.scenario:
        print("Provide --street or --scenario (or both).")
        return 1

    streets = []
    if args.street:
        streets.append(args.street)

    scenarios = []
    if args.scenario:
        scenarios.append(args.scenario)

    for street in streets:
        street_slug = _sanitize_street_dirname(street)
        agent_street_dir = PROJECT_ROOT / "street_analysis_outputs" / street_slug
        legacy_street_dir = LEGACY_ROOT / "street_analysis_outputs" / street

        print(f"\n### Street comparison: {street} ###")
        compare_html(
            agent_street_dir / f"dual_pipe_dashboard_dual_pipe_{street_slug}.html",
            legacy_street_dir / f"dual_pipe_dashboard_dual_pipe_{street}.html",
            "Dashboard HTML",
        )
        compare_html(
            agent_street_dir / f"dual_pipe_map_dual_pipe_{street_slug}.html",
            legacy_street_dir / f"dual_pipe_map_dual_pipe_{street}.html",
            "Interactive Map HTML",
        )
        compare_json(
            agent_street_dir / f"dual_network_stats_dual_pipe_{street_slug}.json",
            legacy_street_dir / f"dual_network_stats_dual_pipe_{street}.json",
            "Network Stats JSON",
        )

    for scenario in scenarios:
        scenario_slug = _slug_from_scenario(scenario)
        agent_dir = PROJECT_ROOT / "results_test" / "routing" / scenario
        legacy_dir = LEGACY_ROOT / "street_analysis_outputs"

        print(f"\n### Scenario comparison: {scenario} ###")

        # Attempt to identify matching legacy street folder
        legacy_stats = None
        for path in legacy_dir.glob("*/dual_network_stats_dual_pipe_*.json"):
            if scenario_slug in path.name:
                legacy_stats = path
                break

        if legacy_stats:
            compare_json(
                agent_dir / f"dual_network_stats_dual_pipe_{scenario_slug}.json",
                legacy_stats,
                "Network Stats JSON",
            )
        else:
            print("No legacy stats JSON found matching scenario name.")

    print("\nComparison complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

