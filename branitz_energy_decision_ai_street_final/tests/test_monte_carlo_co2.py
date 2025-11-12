"""
CO2 extensions for Monte Carlo economics: shape, determinism, and quantiles.
"""

import pandas as pd
from econ.monte_carlo import run_monte_carlo


def _tiny_inputs():
    segments_df = pd.DataFrame({
        "seg_id": ["S1", "S2"],
        "length_m": [120.0, 150.0],
        "DN": [80, 100],
        "pump_MWh": [40.0, 60.0],     # 100 MWh el total
        "heat_loss_MWh": [30.0, 50.0] # 80 MWh th total
    })
    catalog_df = pd.DataFrame({
        "dn": [80, 100],
        "cost_eur_per_m": [150.0, 220.0],
    })
    assignment = {"S1": 80, "S2": 100}
    design = {}
    econ = {"price_el": 0.25, "cost_heat_prod": 55.0, "years": 30, "r": 0.04}
    return assignment, segments_df, design, econ, catalog_df


def test_co2_shapes_and_monotone_quantiles_default_n():
    # default n=500
    assignment, segments_df, design, econ, catalog_df = _tiny_inputs()
    res = run_monte_carlo(assignment, segments_df, design, econ, catalog_df, seed=123)

    assert len(res["co2_tons"]) == 500
    s = res["summary"]
    assert "co2_p10" in s and "co2_p50" in s and "co2_p90" in s
    assert s["co2_p10"] <= s["co2_p50"] <= s["co2_p90"]


def test_co2_determinism_with_seed():
    assignment, segments_df, design, econ, catalog_df = _tiny_inputs()
    # lower n to keep test speedy but still non-trivial
    r1 = run_monte_carlo(assignment, segments_df, design, econ, catalog_df, n=64, seed=777)
    r2 = run_monte_carlo(assignment, segments_df, design, econ, catalog_df, n=64, seed=777)

    # identical summaries and first few samples
    assert r1["summary"]["co2_p50"] == r2["summary"]["co2_p50"]
    assert r1["co2_tons"][:5] == r2["co2_tons"][:5] 