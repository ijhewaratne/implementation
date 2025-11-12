"""
Smoke test for diameter optimizer.

This module contains a deterministic smoke test for the diameter optimizer
that does not require geopandas/pandapipes dependencies.
"""

import math
import pytest
import pandas as pd
from pathlib import Path
from optimize.diameter_optimizer import Segment, DiameterOptimizer


def test_diameter_optimizer_smoke(tmp_path):
    """Smoke test for the diameter optimizer with synthetic data."""

    # Create synthetic pipe catalog
    catalog_data = {
        "dn": [20, 25, 32, 40, 50, 65, 80, 100, 125, 150],
        "d_inner_m": [0.020, 0.025, 0.032, 0.040, 0.050, 0.065, 0.080, 0.100, 0.125, 0.150],
        "d_outer_m": [0.025, 0.032, 0.040, 0.050, 0.063, 0.080, 0.100, 0.125, 0.156, 0.188],
        "w_loss_w_per_m": [12.0, 15.0, 18.0, 22.0, 26.0, 32.0, 38.0, 45.0, 52.0, 60.0],
        "u_wpermk": [0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4],
        "cost_eur_per_m": [50, 65, 85, 110, 140, 180, 230, 300, 390, 500],
    }

    catalog_df = pd.DataFrame(catalog_data)
    catalog_path = tmp_path / "synthetic_catalog.csv"
    catalog_df.to_csv(catalog_path, index=False)

    # Create 3 segments (two supply forming one path P1, one return with same flow)
    segments = [
        Segment(
            seg_id="S1",
            length_m=120.0,
            V_dot_m3s=0.012,
            Q_seg_W=400000,  # 400 kW
            path_id="P1",
            is_supply=True,
        ),
        Segment(
            seg_id="S2",
            length_m=80.0,
            V_dot_m3s=0.006,
            Q_seg_W=200000,  # 200 kW
            path_id="P1",
            is_supply=True,
        ),
        Segment(
            seg_id="R1",
            length_m=120.0,
            V_dot_m3s=0.012,
            Q_seg_W=400000,  # 400 kW
            path_id="P1",
            is_supply=False,
        ),
    ]

    # Design parameters
    design = {
        "T_supply": 80.0,
        "T_return": 50.0,
        "T_soil": 10.0,
        "rho": 983.0,
        "mu": 4.5e-4,
        "cp": 4180.0,
        "eta_pump": 0.65,
        "hours": 3000,
        "v_feasible_target": 1.3,
        "v_limit": 1.5,
        "deltaT_min": 30.0,
        "K_minor": 1.0,
    }

    # Economic parameters
    econ = {"price_el": 0.25, "cost_heat_prod": 55.0, "years": 30, "r": 0.04, "o_and_m_rate": 0.01}

    # Instantiate optimizer and run
    optimizer = DiameterOptimizer(segments, design, econ, str(catalog_path))
    assignment, metrics, validation = optimizer.run()

    # Assertions
    # 1. Assignment contains all 3 segments with integer DN
    assert len(assignment) == 3
    assert "S1" in assignment
    assert "S2" in assignment
    assert "R1" in assignment
    assert all(isinstance(dn, int) for dn in assignment.values())

    # 2. Velocity and deltaT constraints satisfied
    assert metrics["v_max"] <= 1.5
    assert metrics["deltaT_ok"] is True

    # 3. Economic metrics are positive and finite
    assert metrics["npv_eur"] > 0
    assert math.isfinite(metrics["npv_eur"])
    assert metrics["capex_eur"] > 0
    assert math.isfinite(metrics["capex_eur"])
    assert metrics["opex_eur_per_a"] > 0
    assert math.isfinite(metrics["opex_eur_per_a"])

    # 4. Energy metrics are non-negative and finite
    assert metrics["pump_MWh"] >= 0
    assert math.isfinite(metrics["pump_MWh"])
    assert metrics["heat_loss_MWh"] >= 0
    assert math.isfinite(metrics["heat_loss_MWh"])

    # 5. Validation returns expected structure
    assert validation["ok"] is True
    assert "note" in validation

    # 6. Per-segment data is complete
    assert len(metrics["per_segment"]) == 3
    for seg_id in ["S1", "S2", "R1"]:
        assert seg_id in metrics["per_segment"]
        seg_data = metrics["per_segment"][seg_id]
        assert "dn" in seg_data
        assert "v" in seg_data
        assert "dp" in seg_data
        assert "h" in seg_data
        assert "heat_loss_W" in seg_data

    # 7. Path statistics are available
    assert "P1" in metrics["path_stats"]
    path_data = metrics["path_stats"]["P1"]
    assert "dp_Pa" in path_data
    assert "V_dot_peak_m3s" in path_data

    print(f"✅ Smoke test passed!")
    print(f"   Final NPV: {metrics['npv_eur']:.0f} €")
    print(f"   Assignment: {assignment}")
    print(f"   Max velocity: {metrics['v_max']:.2f} m/s")
    print(f"   Pump energy: {metrics['pump_MWh']:.1f} MWh/a")
    print(f"   Heat loss: {metrics['heat_loss_MWh']:.1f} MWh/a")


if __name__ == "__main__":
    pytest.main([__file__])
