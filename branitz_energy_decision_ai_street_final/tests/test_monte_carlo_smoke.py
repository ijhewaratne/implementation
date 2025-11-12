"""
Smoke test for Monte Carlo economics.
"""

import pytest
import pandas as pd
from econ.monte_carlo import run_monte_carlo


def test_monte_carlo_smoke():
    """Build tiny segments & catalog; run with n=30; assert list lengths, summary keys, determinism with fixed seed."""
    # Tiny segments dataframe
    segments_df = pd.DataFrame({
        'seg_id': ['S1', 'S2'],
        'length_m': [100.0, 150.0],
        'DN': [80, 100],
        'pump_MWh': [50.0, 75.0],
        'heat_loss_MWh': [25.0, 35.0]
    })
    
    # Tiny catalog dataframe
    catalog_df = pd.DataFrame({
        'dn': [80, 100],
        'cost_eur_per_m': [150.0, 200.0]
    })
    
    # Assignment dictionary
    assignment = {'S1': 80, 'S2': 100}
    
    # Design parameters
    design = {'temperature_supply': 80, 'temperature_return': 50}
    
    # Economic parameters
    econ = {
        'price_el': 0.25,
        'cost_heat_prod': 55.0,
        'years': 30,
        'r': 0.04
    }
    
    # Run Monte Carlo with small n
    result = run_monte_carlo(assignment, segments_df, design, econ, catalog_df, n=30, seed=42)
    
    # Assert list lengths
    assert len(result["npv"]) == 30
    assert len(result["lcoh"]) == 30
    assert len(result["pump_mwh"]) == 30
    assert len(result["heat_loss_mwh"]) == 30
    
    # Assert summary keys
    summary = result["summary"]
    assert "npv_p50" in summary
    assert "npv_p10" in summary
    assert "npv_p90" in summary
    
    # Assert summary values are reasonable
    assert summary["npv_p10"] <= summary["npv_p50"] <= summary["npv_p90"]
    # Note: NPV can be positive or negative depending on parameters
    
    # Assert pump and heat loss values are consistent
    assert all(x == 125.0 for x in result["pump_mwh"])  # 50 + 75
    assert all(x == 60.0 for x in result["heat_loss_mwh"])  # 25 + 35


def test_monte_carlo_determinism():
    """Test determinism with fixed seed."""
    segments_df = pd.DataFrame({
        'seg_id': ['S1'],
        'length_m': [100.0],
        'DN': [80],
        'pump_MWh': [50.0],
        'heat_loss_MWh': [25.0]
    })
    
    catalog_df = pd.DataFrame({
        'dn': [80],
        'cost_eur_per_m': [150.0]
    })
    
    assignment = {'S1': 80}
    design = {'temperature_supply': 80}
    econ = {'price_el': 0.25, 'years': 30, 'r': 0.04}
    
    # Run twice with same seed
    result1 = run_monte_carlo(assignment, segments_df, design, econ, catalog_df, n=10, seed=42)
    result2 = run_monte_carlo(assignment, segments_df, design, econ, catalog_df, n=10, seed=42)
    
    # Results should be identical
    assert result1["npv"][0] == result2["npv"][0]
    assert result1["summary"]["npv_p50"] == result2["summary"]["npv_p50"]


def test_monte_carlo_defaults():
    """Test Monte Carlo with minimal data and defaults."""
    segments_df = pd.DataFrame({
        'seg_id': ['S1'],
        'length_m': [100.0],
        'DN': [80]
        # No pump_MWh or heat_loss_MWh columns
    })
    
    catalog_df = pd.DataFrame({
        'dn': [80],
        'cost_eur_per_m': [150.0]
    })
    
    assignment = {'S1': 80}
    design = {}
    econ = {}
    
    result = run_monte_carlo(assignment, segments_df, design, econ, catalog_df, n=5, seed=42)
    
    # Should work with defaults
    assert len(result["npv"]) == 5
    assert len(result["lcoh"]) == 5
    assert "npv_p50" in result["summary"]


def test_monte_carlo_co2_and_n_default():
    """Test CO2 distributions and default n=500."""
    import pandas as pd
    from econ.monte_carlo import run_monte_carlo
    seg = pd.DataFrame({"seg_id": ["S1"], "length_m": [100.0], "DN": [80],
                        "pump_MWh": [10.0], "heat_loss_MWh": [20.0]})
    cat = pd.DataFrame({"dn": [80], "cost_eur_per_m": [100.0]})
    res = run_monte_carlo({"S1": 80}, seg, {}, {"co2_el_t_per_mwh": 0.4, "co2_heat_t_per_mwh": 0.2}, cat)  # n defaults to 500
    assert len(res["co2_tonnes"]) == 500
    assert abs(res["summary"]["co2_p50"] - (10*0.4 + 20*0.2)) < 1e-9 