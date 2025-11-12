"""
Test velocity limit enforcement for DH optimizer.

This module tests that velocity limits are properly enforced when
flow rates would exceed the 1.5 m/s limit.
"""

import pytest
import pandas as pd
from optimize.diameter_optimizer import Segment, DiameterOptimizer


def test_velocity_limit_enforcement(tmp_path):
    """Test that velocity limits are properly enforced."""
    catalog = pd.DataFrame({
        "dn": [50, 80, 100],
        "d_inner_m": [0.050, 0.080, 0.100],
        "d_outer_m": [0.063, 0.100, 0.120],
        "w_loss_w_per_m": [20.0, 30.0, 40.0],
        "u_wpermk": [0.4, 0.4, 0.4],
        "cost_eur_per_m": [150.0, 250.0, 300.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    # High flow rate that will exceed 1.5 m/s with small DN
    segs = [Segment("S1", 100.0, 0.05, 0, "P1", is_supply=True)]  # High flow: 0.05 m³/s
    
    design = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=0.65, hours=1000, 
        v_feasible_target=1.3, v_limit=1.5,  # 1.5 m/s limit
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=30, r=0.04, o_and_m_rate=0.01)
    
    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    
    # Test with small DN that will cause high velocity
    m = opt.evaluate_quick({"S1": 50})  # Small DN for high flow
    
    # Should violate velocity limit
    assert m["velocity_ok"] is False  # Should violate limit
    assert m["v_max"] > 1.5  # Should exceed 1.5 m/s limit
    
    # Test with larger DN that should be within limit
    m2 = opt.evaluate_quick({"S1": 100})  # Larger DN for same flow
    
    # Should be within velocity limit
    assert m2["velocity_ok"] is True  # Should be within limit
    assert m2["v_max"] <= 1.5  # Should not exceed 1.5 m/s limit
    
    # Verify that larger DN has lower velocity
    assert m2["v_max"] < m["v_max"]


def test_velocity_target_respect(tmp_path):
    """Test that initial feasible assignment respects velocity target."""
    catalog = pd.DataFrame({
        "dn": [50, 80, 100],
        "d_inner_m": [0.050, 0.080, 0.100],
        "d_outer_m": [0.063, 0.100, 0.120],
        "w_loss_w_per_m": [20.0, 30.0, 40.0],
        "u_wpermk": [0.4, 0.4, 0.4],
        "cost_eur_per_m": [150.0, 250.0, 300.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    # Moderate flow rate
    segs = [Segment("S1", 150.0, 0.02, 0, "P1", is_supply=True)]  # 0.02 m³/s
    
    design = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=0.65, hours=1000, 
        v_feasible_target=1.3, v_limit=1.5,  # Target 1.3 m/s
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=30, r=0.04, o_and_m_rate=0.01)
    
    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    
    # Get initial feasible assignment
    assignment = opt.initial_feasible()
    m = opt.evaluate_quick(assignment)
    
    # Should respect velocity target
    assert m["v_max"] <= design["v_feasible_target"] + 1e-6  # Within target
    assert m["velocity_ok"] is True  # Should be within limit


def test_velocity_edge_cases(tmp_path):
    """Test velocity calculations at edge cases."""
    catalog = pd.DataFrame({
        "dn": [25, 50, 100],
        "d_inner_m": [0.025, 0.050, 0.100],
        "d_outer_m": [0.035, 0.063, 0.120],
        "w_loss_w_per_m": [15.0, 20.0, 40.0],
        "u_wpermk": [0.4, 0.4, 0.4],
        "cost_eur_per_m": [100.0, 150.0, 300.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    # Very high flow rate
    segs = [Segment("S1", 50.0, 0.10, 0, "P1", is_supply=True)]  # 0.10 m³/s
    
    design = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=0.65, hours=1000, 
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=30, r=0.04, o_and_m_rate=0.01)
    
    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    
    # Test with smallest DN - should definitely violate
    m_small = opt.evaluate_quick({"S1": 25})
    assert m_small["velocity_ok"] is False
    assert m_small["v_max"] > 1.5
    
    # Test with largest DN - should be within limit
    m_large = opt.evaluate_quick({"S1": 100})
    assert m_large["velocity_ok"] is True
    assert m_large["v_max"] <= 1.5
    
    # Verify velocity decreases with increasing DN
    assert m_large["v_max"] < m_small["v_max"]


if __name__ == "__main__":
    pytest.main([__file__]) 