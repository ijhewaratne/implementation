import json
import os
import re
import sys
from pathlib import Path

import pandas as pd
import pytest
import yaml


PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from energy_tools import optimize_network_routing, create_interactive_map  # noqa: E402


SCENARIO_NAME = "Demo_Parkstrasse_DH"
ROUTING_DIR = PROJECT_ROOT / "results_test" / "routing" / SCENARIO_NAME
LEGACY_DIR = PROJECT_ROOT / "tests" / "data" / "legacy_routing"
LEGACY_DUAL_DIR = PROJECT_ROOT / "tests" / "data" / "legacy_dual_pipe"
SCENARIO_RESULTS_FILE = PROJECT_ROOT / "simulation_outputs" / f"{SCENARIO_NAME}_results.json"


def _get_street_name_and_slug():
    street_name = SCENARIO_NAME
    if SCENARIO_RESULTS_FILE.exists():
        with open(SCENARIO_RESULTS_FILE, "r", encoding="utf-8") as f:
            payload = json.load(f)
        street_name = payload.get("street_name") or street_name
    slug = street_name.strip().replace("/", "_").replace(" ", "-")
    return street_name, slug


@pytest.fixture(scope="module")
def ensure_dual_pipe_outputs():
    """Run routing and map generation so artefacts exist for regression checks."""
    ROUTING_DIR.mkdir(parents=True, exist_ok=True)
    optimize_network_routing.func(SCENARIO_NAME)
    create_interactive_map.func(SCENARIO_NAME)
    return ROUTING_DIR


def test_supply_return_pairing_and_offsets(ensure_dual_pipe_outputs):
    topology_path = ensure_dual_pipe_outputs / "dual_topology.json"
    assert topology_path.exists(), "dual_topology.json should be generated"

    with open(topology_path, "r", encoding="utf-8") as f:
        topology = json.load(f)

    supply_pipes = [p for p in topology["pipes"] if p.get("type") == "supply"]
    return_pipes = [p for p in topology["pipes"] if p.get("type") == "return"]

    assert len(supply_pipes) == len(return_pipes) > 0

    from collections import defaultdict

    return_lookup = defaultdict(list)
    for pipe in return_pipes:
        building_id = pipe.get("building_id")
        return_lookup[building_id].append(pipe)

    for supply in supply_pipes:
        building_id = supply.get("building_id")
        candidates = return_lookup.get(building_id, [])
        assert candidates, f"Missing return segments for building {building_id}"

        supply_coords = tuple(supply["coords"])
        reversed_supply_coords = tuple(reversed(supply_coords))

        match = None
        for candidate in candidates:
            if tuple(candidate["coords"]) == reversed_supply_coords:
                match = candidate
                break

        assert match is not None, f"No matching return segment for supply segment {supply['id']}"
        assert supply.get("street_name") == match.get("street_name")
        assert supply.get("highway_type") == match.get("highway_type")
        assert pytest.approx(supply.get("length_m", 0.0), abs=0.01) == match.get("length_m", 0.0)


def test_temperature_and_pressure_ranges(ensure_dual_pipe_outputs):
    thermal_path = ensure_dual_pipe_outputs / "routing_thermal_profile.json"
    assert thermal_path.exists(), "Thermal profile JSON should be generated"

    with open("config/simulation_config.yaml", "r", encoding="utf-8") as f:
        sim_config = yaml.safe_load(f) or {}
    dh_config = sim_config.get("district_heating", {})
    supply_temp = float(dh_config.get("supply_temp_c", 70.0))
    return_temp = float(dh_config.get("return_temp_c", 40.0))
    supply_pressure = float(dh_config.get("supply_pressure_bar", 6.0) or 6.0)

    with open(thermal_path, "r", encoding="utf-8") as f:
        thermal_data = json.load(f)

    temperatures = [row["temperature_c"] for row in thermal_data]
    pressures = [row["pressure_bar"] for row in thermal_data]

    assert all(return_temp - 0.5 <= temp <= supply_temp + 0.5 for temp in temperatures)
    assert all(1.0 - 0.1 <= pressure <= supply_pressure + 0.1 for pressure in pressures)
    assert min(temperatures) >= return_temp - 0.5
    assert max(temperatures) <= supply_temp + 0.5


def test_interactive_map_contains_dual_pipe_sections(ensure_dual_pipe_outputs):
    html_path = PROJECT_ROOT / "results_test" / "visualizations" / "interactive" / f"{SCENARIO_NAME}_dh_interactive.html"
    assert html_path.exists(), "Interactive map HTML should exist"

    html_content = html_path.read_text(encoding="utf-8")

    expected_snippets = [
        "Network Legend",
        "Dual-Pipe Routing Summary",
        "Thermal & Hydraulic Profile",
        "Supply Pipes",
        "Return Pipes",
    ]
    for snippet in expected_snippets:
        assert snippet in html_content


def test_routing_outputs_align_with_legacy_structure(ensure_dual_pipe_outputs):
    current_paths = pd.read_csv(ensure_dual_pipe_outputs / "routing_paths.csv")
    legacy_paths = pd.read_csv(LEGACY_DIR / "routing_paths.csv")

    current_analysis = pd.read_csv(ensure_dual_pipe_outputs / "routing_analysis.csv")
    legacy_analysis = pd.read_csv(LEGACY_DIR / "routing_analysis.csv")

    assert set(legacy_paths.columns).issubset(set(current_paths.columns))
    assert set(legacy_analysis.columns).issubset(set(current_analysis.columns))

    assert len(current_paths) >= len(legacy_paths)
    assert current_analysis.loc[0, "successful_connections"] >= legacy_analysis.loc[0, "successful_connections"]


def test_dual_network_stats_export(ensure_dual_pipe_outputs):
    stats_file = ensure_dual_pipe_outputs / "dual_network_stats_Demo_Parkstrasse_DH.json"
    assert stats_file.exists()

    with open(stats_file, "r", encoding="utf-8") as f:
        current_stats = json.load(f)
    with open(LEGACY_DUAL_DIR / "dual_network_stats_reference.json", "r", encoding="utf-8") as f:
        legacy_stats = json.load(f)

    assert set(legacy_stats.keys()).issubset(set(current_stats.keys()))
    assert current_stats["dual_pipe_system"] is True
    assert current_stats["street_based_routing"] is True
    assert current_stats["total_supply_length_km"] > 0
    assert current_stats["total_return_length_km"] > 0


def test_dual_pipe_csv_exports(ensure_dual_pipe_outputs):
    _, street_slug = _get_street_name_and_slug()
    supply_csv = ensure_dual_pipe_outputs / f"dual_supply_pipes_dual_pipe_{street_slug}.csv"
    return_csv = ensure_dual_pipe_outputs / f"dual_return_pipes_dual_pipe_{street_slug}.csv"
    service_csv = ensure_dual_pipe_outputs / f"dual_service_connections_dual_pipe_{street_slug}.csv"

    for path in (supply_csv, return_csv, service_csv):
        assert path.exists()

    supply_df = pd.read_csv(supply_csv)
    return_df = pd.read_csv(return_csv)
    service_df = pd.read_csv(service_csv)

    legacy_supply_cols = pd.read_csv(LEGACY_DUAL_DIR / "dual_supply_columns_reference.csv").columns
    legacy_service_cols = pd.read_csv(LEGACY_DUAL_DIR / "dual_service_columns_reference.csv").columns

    assert set(legacy_supply_cols).issubset(set(supply_df.columns))
    assert set(legacy_supply_cols).issubset(set(return_df.columns))
    assert set(legacy_service_cols).issubset(set(service_df.columns))

    assert supply_df["length_m"].sum() > 0
    assert return_df["length_m"].sum() > 0
    assert service_df["distance_to_street"].sum() >= 0


def test_simulation_results_and_report(ensure_dual_pipe_outputs):
    sim_json = ensure_dual_pipe_outputs / "pandapipes_simulation_results_Demo_Parkstrasse_DH.json"
    report_md = ensure_dual_pipe_outputs / "dual_pipe_report_Demo_Parkstrasse_DH.md"

    assert sim_json.exists()
    assert report_md.exists()

    with open(sim_json, "r", encoding="utf-8") as f:
        sim_data = json.load(f)

    assert "supply_temperature_c" in sim_data
    assert "return_temperature_c" in sim_data

    content = report_md.read_text(encoding="utf-8")
    assert "Dual-Pipe District Heating Report" in content
    assert "Generated Files" in content


def test_legacy_copies_exist(ensure_dual_pipe_outputs):
    street_dir = PROJECT_ROOT / "street_analysis_outputs" / "Parkstrasse"
    assert street_dir.exists()
    legacy_map = street_dir / "dual_pipe_map_dual_pipe_Parkstrasse.html"
    legacy_dash = street_dir / "dual_pipe_dashboard_dual_pipe_Parkstrasse.html"
    assert legacy_map.exists()
    assert legacy_dash.exists()


def test_dashboard_lists_generated_files(ensure_dual_pipe_outputs):
    html_path = PROJECT_ROOT / "results_test" / "visualizations" / "html_dashboards" / f"{SCENARIO_NAME}_dh_html_dashboard.html"
    assert html_path.exists()
    html_content = html_path.read_text(encoding="utf-8")
    assert "📂 Generated Files" in html_content
    assert "dual_supply_pipes_dual_pipe_Parkstrasse.csv" in html_content
    assert "dual_pipe_report_dual_pipe_Parkstrasse.md" in html_content


def test_sizing_fallback_when_engine_fails(monkeypatch):
    import energy_tools as energy_tools_module  # noqa: PLC0415

    real_runner = energy_tools_module.run_cha_sizing_from_topology

    def failing_runner(*args, **kwargs):  # noqa: ANN001, ANN003
        raise RuntimeError("Intentional sizing failure for fallback test")

    monkeypatch.setattr("energy_tools.run_cha_sizing_from_topology", failing_runner)

    try:
        optimize_network_routing.func(SCENARIO_NAME, force_recompute=True)
        topology_path = ROUTING_DIR / "dual_topology.json"
        assert topology_path.exists()
        topology = json.loads(topology_path.read_text(encoding="utf-8"))
        assert topology.get("stats", {}).get("sizing_fallback_used") is True
        fallback_segments = [pipe for pipe in topology.get("pipes", []) if pipe.get("sizing_status") == "fallback"]
        assert fallback_segments, "Expected fallback sizing segments to be flagged"
        sizing_meta = topology.get("sizing", {})
        assert sizing_meta.get("status") == "fallback"
    finally:
        monkeypatch.setattr("energy_tools.run_cha_sizing_from_topology", real_runner)
        optimize_network_routing.func(SCENARIO_NAME, force_recompute=True)


