"""
Integration regression tests for HP street simulations.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

SNAPSHOT_STREET = "Anton-Bruckner-Straße"
SNAPSHOT_SCENARIO = "hp_with_grid_reinforcement"

EXPECTED_KPI = {
    "min_voltage_pu": 1.0060354,
    "max_line_loading_pct": 81.9490785,
    "avg_line_loading_pct": 0.9135446,
    "transformer_loading_pct": 25.1366275,
    "num_buses": 1438,
    "num_lines": 1448,
    "num_loads": 68,
}


def test_hp_street_regression(tmp_path):
    """
    Run a known street through the HP workflow and compare key KPIs/artefacts.
    """
    pytest.importorskip("pandapower")

    from src.hp.street_workflow import run_hp_street_analysis

    summary = run_hp_street_analysis(
        scenario_name=SNAPSHOT_SCENARIO,
        street_name=SNAPSHOT_STREET,
        buffer_m=50.0,
        force=False,
    )

    result = summary.get("result", {})
    kpi = result.get("kpi", {})
    assert result.get("success"), "HP street analysis should succeed"

    for key, expected in EXPECTED_KPI.items():
        assert key in kpi, f"{key} missing from KPI payload"
        assert kpi[key] == pytest.approx(expected, rel=5e-4), f"{key} drifted"

    exported = summary.get("exported_files", {})
    required_keys = {"buses_results", "lines_results", "kpis", "interactive_map"}
    missing = required_keys - exported.keys()
    assert not missing, f"Missing exported artefacts: {missing}"

    for label, path_str in exported.items():
        path = Path(path_str)
        assert path.exists(), f"Expected artefact {label} missing at {path}"

    kpi_path = Path(exported["kpis"])
    with kpi_path.open("r", encoding="utf-8") as f:
        exported_kpi = json.load(f)
    assert isinstance(exported_kpi, dict)
    assert exported_kpi["min_voltage_pu"] == pytest.approx(EXPECTED_KPI["min_voltage_pu"], rel=5e-4)
    assert exported_kpi["max_line_loading_pct"] == pytest.approx(
        EXPECTED_KPI["max_line_loading_pct"], rel=5e-4
    )

    violations_path = exported.get("violations")
    if kpi.get("voltage_violations", 0) > 0 or kpi.get("overloaded_lines", 0) > 0:
        assert violations_path, "Violations expected but CSV missing"
        assert Path(violations_path).exists(), "Violations CSV path does not exist"
    else:
        assert violations_path in (None, ""), "Unexpected violations CSV generated"

