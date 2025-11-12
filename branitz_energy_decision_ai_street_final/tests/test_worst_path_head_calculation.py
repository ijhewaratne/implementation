"""
Test worst-path head calculation for DH optimizer.

This module tests that worst-path head calculation correctly identifies
the path with maximum pressure drop among multiple supply paths.
"""

import pytest
import pandas as pd
from optimize.diameter_optimizer import Segment, DiameterOptimizer


def test_worst_path_head_calculation(tmp_path):
    """Test that worst-path head calculation is correct."""
    catalog = pd.DataFrame({
        "dn": [80, 100, 150],
        "d_inner_m": [0.080, 0.100, 0.150],
        "d_outer_m": [0.100, 0.120, 0.180],
        "w_loss_w_per_m": [30.0, 40.0, 60.0],
        "u_wpermk": [0.4, 0.4, 0.4],
        "cost_eur_per_m": [250.0, 300.0, 500.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    # Create 3 supply paths with different characteristics
    segs = [
        Segment("S1", 100.0, 0.01, 0, "P1", is_supply=True),  # Short, low flow
        Segment("S2", 500.0, 0.02, 0, "P2", is_supply=True),  # Long, medium flow  
        Segment("S3", 200.0, 0.03, 0, "P3", is_supply=True),  # Medium, high flow
    ]
    
    design = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=0.65, hours=1000, 
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=30, r=0.04, o_and_m_rate=0.01)
    
    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    
    # Use same DN for all segments to make comparison clear
    m = opt.evaluate_quick({"S1": 100, "S2": 100, "S3": 100})
    
    # Verify worst path is correctly identified
    worst_path = max(m["path_stats"], key=lambda p: m["path_stats"][p]["dp_Pa"])
    assert m["dp_path_max_Pa"] == m["path_stats"][worst_path]["dp_Pa"]
    
    # Verify that dp_path_max_Pa is the maximum among all paths
    all_dps = [m["path_stats"][p]["dp_Pa"] for p in m["path_stats"]]
    assert m["dp_path_max_Pa"] == max(all_dps)
    
    # Verify that head_required_m is calculated from dp_path_max_Pa
    expected_head = m["dp_path_max_Pa"] / (design["rho"] * 9.81)
    assert m["head_required_m"] == pytest.approx(expected_head, rel=1e-6)


def test_worst_path_with_different_dns(tmp_path):
    """Test worst-path calculation with different DN assignments."""
    catalog = pd.DataFrame({
        "dn": [80, 100, 150],
        "d_inner_m": [0.080, 0.100, 0.150],
        "d_outer_m": [0.100, 0.120, 0.180],
        "w_loss_w_per_m": [30.0, 40.0, 60.0],
        "u_wpermk": [0.4, 0.4, 0.4],
        "cost_eur_per_m": [250.0, 300.0, 500.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    # Two paths with different characteristics
    segs = [
        Segment("S1", 200.0, 0.02, 0, "P1", is_supply=True),  # Medium length, medium flow
        Segment("S2", 300.0, 0.015, 0, "P2", is_supply=True),  # Long, lower flow
    ]
    
    design = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=0.65, hours=1000, 
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=30, r=0.04, o_and_m_rate=0.01)
    
    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    
    # Test different DN combinations
    m1 = opt.evaluate_quick({"S1": 80, "S2": 100})  # S1 smaller DN
    m2 = opt.evaluate_quick({"S1": 100, "S2": 80})  # S2 smaller DN
    
    # The path with smaller DN should have higher pressure drop
    dp1_s1 = m1["path_stats"]["P1"]["dp_Pa"]
    dp1_s2 = m1["path_stats"]["P2"]["dp_Pa"]
    dp2_s1 = m2["path_stats"]["P1"]["dp_Pa"]
    dp2_s2 = m2["path_stats"]["P2"]["dp_Pa"]
    
    # Verify that smaller DN causes higher pressure drop
    assert dp1_s1 > dp1_s2  # S1 has smaller DN in m1
    assert dp2_s2 > dp2_s1  # S2 has smaller DN in m2
    
    # Verify worst path is correctly identified in each case
    assert m1["dp_path_max_Pa"] == max(dp1_s1, dp1_s2)
    assert m2["dp_path_max_Pa"] == max(dp2_s1, dp2_s2)


def test_worst_path_pump_energy_calculation(tmp_path):
    """Test that pump energy uses worst-path values correctly."""
    catalog = pd.DataFrame({
        "dn": [80, 100],
        "d_inner_m": [0.080, 0.100],
        "d_outer_m": [0.100, 0.120],
        "w_loss_w_per_m": [30.0, 40.0],
        "u_wpermk": [0.4, 0.4],
        "cost_eur_per_m": [250.0, 300.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    # Two paths with different characteristics
    segs = [
        Segment("S1", 150.0, 0.02, 0, "P1", is_supply=True),  # Higher flow
        Segment("S2", 200.0, 0.01, 0, "P2", is_supply=True),  # Lower flow, longer
    ]
    
    design = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=0.7, hours=2000, 
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=30, r=0.04, o_and_m_rate=0.01)
    
    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    
    m = opt.evaluate_quick({"S1": 80, "S2": 100})
    
    # Identify worst path
    worst_path = max(m["path_stats"], key=lambda p: m["path_stats"][p]["dp_Pa"])
    worst_dp = m["path_stats"][worst_path]["dp_Pa"]
    worst_vdot = m["path_stats"][worst_path]["V_dot_peak_m3s"]
    
    # Calculate expected pump energy from worst path
    expected_pump_mwh = worst_dp * worst_vdot * design["hours"] / (design["eta_pump"] * 1e6)
    
    # Verify pump energy matches worst-path calculation
    assert m["pump_MWh"] == pytest.approx(expected_pump_mwh, rel=1e-3)
    
    # Verify that pump energy is not based on sum of all paths
    total_dp = sum(m["path_stats"][p]["dp_Pa"] for p in m["path_stats"])
    total_vdot = sum(m["path_stats"][p]["V_dot_peak_m3s"] for p in m["path_stats"])
    sum_based_pump = total_dp * total_vdot * design["hours"] / (design["eta_pump"] * 1e6)
    
    # Pump energy should NOT equal sum-based calculation
    assert m["pump_MWh"] != pytest.approx(sum_based_pump, rel=1e-3)


if __name__ == "__main__":
    pytest.main([__file__]) 