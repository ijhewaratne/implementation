"""
Dual-pipe workflow orchestrator.

Provides utility functions and a CLI entrypoint to execute the full dual-pipe
visualisation pipeline (routing, interactive map, HTML dashboard) for one or
more scenarios, mirroring the behaviour of the legacy interactive runners.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from energy_tools import (
    optimize_network_routing,
    create_interactive_map,
    create_html_dashboard,
)


DEFAULT_RESULTS_DIR = Path("results_test")
SIM_OUTPUTS_DIR = Path("simulation_outputs")


def discover_available_scenarios() -> List[str]:
    """
    Return a list of scenario names detected in the workspace.

    Priority order:
    1. scenario names listed in results_test/scenario_kpis.csv (column 'scenario')
    2. filenames present in simulation_outputs/*_results.json
    """
    scenarios: List[str] = []
    kpi_file = DEFAULT_RESULTS_DIR / "scenario_kpis.csv"
    if kpi_file.exists():
        try:
            with open(kpi_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    scenario = row.get("scenario")
                    if scenario:
                        scenarios.append(scenario.strip())
        except Exception as exc:  # pragma: no cover - informational
            print(f"⚠️  Unable to read {kpi_file}: {exc}")

    if scenarios:
        return sorted(set(scenarios))

    if SIM_OUTPUTS_DIR.exists():
        for path in SIM_OUTPUTS_DIR.glob("*_results.json"):
            name = path.name.replace("_results.json", "")
            scenarios.append(name)

    return sorted(set(scenarios))


def should_skip(step_output: Path, force: bool) -> bool:
    return step_output.exists() and not force


def run_dual_pipe_workflow(
    scenario_name: str,
    *,
    force: bool = False,
    run_routing: bool = True,
    run_map: bool = True,
    run_dashboard: bool = True,
) -> dict:
    """
    Execute the dual-pipe workflow for a scenario.

    Returns a dictionary describing generated artefacts.
    """
    results: dict = {
        "scenario": scenario_name,
        "routing": None,
        "map": None,
        "dashboard": None,
        "skip_reason": {},
    }

    scenario_results_file = SIM_OUTPUTS_DIR / f"{scenario_name}_results.json"
    if not scenario_results_file.exists():
        raise FileNotFoundError(
            f"Simulation results not found for scenario '{scenario_name}' "
            f"at {scenario_results_file}"
        )

    routing_dir = DEFAULT_RESULTS_DIR / "routing" / scenario_name
    routing_dir.mkdir(parents=True, exist_ok=True)

    # --- Routing -----------------------------------------------------------
    routing_output = routing_dir / "dual_topology.json"
    if run_routing and not should_skip(routing_output, force):
        routing_msg = optimize_network_routing.func(scenario_name)
        results["routing"] = routing_msg
    else:
        results["skip_reason"]["routing"] = "cached"

    # --- Map ---------------------------------------------------------------
    map_output = DEFAULT_RESULTS_DIR / "visualizations" / "interactive" / f"{scenario_name}_dh_interactive.html"
    if run_map and not should_skip(map_output, force):
        map_msg = create_interactive_map.func(scenario_name)
        results["map"] = map_msg
    else:
        results["skip_reason"]["map"] = "cached"

    # --- Dashboard --------------------------------------------------------
    dashboard_output = DEFAULT_RESULTS_DIR / "visualizations" / "html_dashboards" / f"{scenario_name}_dh_html_dashboard.html"
    if run_dashboard and not should_skip(dashboard_output, force):
        dash_msg = create_html_dashboard.func(scenario_name)
        results["dashboard"] = dash_msg
    else:
        results["skip_reason"]["dashboard"] = "cached"

    return results


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the dual-pipe routing, map, and dashboard workflow."
    )
    parser.add_argument(
        "--scenario",
        "-s",
        action="append",
        dest="scenarios",
        help="Scenario name to process (can be supplied multiple times).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all detected scenarios (from scenario_kpis.csv or simulation_outputs).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run workflow even if outputs already exist.",
    )
    parser.add_argument(
        "--skip-routing",
        action="store_true",
        help="Skip the routing step.",
    )
    parser.add_argument(
        "--skip-map",
        action="store_true",
        help="Skip interactive map generation.",
    )
    parser.add_argument(
        "--skip-dashboard",
        action="store_true",
        help="Skip dashboard generation.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)

    available = discover_available_scenarios()
    if args.list:
        print("Available scenarios:")
        for name in available:
            print(f" - {name}")
        return 0

    scenarios: List[str] = []
    if args.all:
        scenarios = available
    if args.scenarios:
        scenarios.extend(args.scenarios)
    scenarios = sorted(set(filter(None, scenarios)))

    if not scenarios:
        print("No scenarios specified. Use --scenario NAME or --all. (--list to view options)")
        return 1

    print(f"Running dual-pipe workflow for {len(scenarios)} scenario(s)...")
    success = True

    for scenario in scenarios:
        print(f"\n=== {scenario} ===")
        try:
            outputs = run_dual_pipe_workflow(
                scenario,
                force=args.force,
                run_routing=not args.skip_routing,
                run_map=not args.skip_map,
                run_dashboard=not args.skip_dashboard,
            )
            for key in ("routing", "map", "dashboard"):
                message = outputs.get(key)
                if message:
                    print(f"[{key}] {message.splitlines()[0]}")
                elif outputs["skip_reason"].get(key):
                    print(f"[{key}] skipped ({outputs['skip_reason'][key]})")
        except FileNotFoundError as exc:
            print(f"❌ {exc}")
            success = False
        except Exception as exc:  # pragma: no cover - defensive
            print(f"❌ Unexpected error for {scenario}: {exc}")
            success = False

    return 0 if success else 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())

