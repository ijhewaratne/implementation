"""
Test heat loss temperature dependence for DH optimizer.

This module tests that heat loss calculations correctly depend on
fluid temperature and use appropriate U-value calculations.
"""

import pytest
import pandas as pd
from optimize.diameter_optimizer import Segment, DiameterOptimizer


def test_heat_loss_temperature_dependence(tmp_path):
    """Test that heat loss depends on fluid temperature."""
    catalog = pd.DataFrame({
        "dn": [100],
        "d_inner_m": [0.100],
        "d_outer_m": [0.120],
        "w_loss_w_per_m": [None],  # Use U-value mode instead of direct W/m
        "u_wpermk": [0.4],  # U-value in W/m²K
        "cost_eur_per_m": [300.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    # Test supply vs return temperature effects
    segs = [
        Segment("SUP", 100.0, 0.01, 0, "P1", is_supply=True),
        Segment("RET", 100.0, 0.01, 0, "P1", is_supply=False),
    ]
    
    # Use U-value mode instead of direct W/m
    design = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=1.0, hours=8760, 
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)
    
    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    m = opt.evaluate_quick({"SUP": 100, "RET": 100})
    
    # Supply should have higher heat loss than return (higher temperature)
    sup_loss = m["per_segment"]["SUP"]["heat_loss_W"]
    ret_loss = m["per_segment"]["RET"]["heat_loss_W"]
    
    # Higher temperature = higher heat loss
    assert sup_loss > ret_loss
    
    # Verify the temperature difference effect
    # Supply: T_f = 80°C, T_soil = 10°C, ΔT = 70K
    # Return: T_f = 50°C, T_soil = 10°C, ΔT = 40K
    # Expected ratio: 70/40 = 1.75
    expected_ratio = (80 - 10) / (50 - 10)  # 70/40 = 1.75
    actual_ratio = sup_loss / ret_loss
    assert actual_ratio == pytest.approx(expected_ratio, rel=1e-2)


def test_heat_loss_u_value_calculation(tmp_path):
    """Test U-value based heat loss calculation."""
    catalog = pd.DataFrame({
        "dn": [80, 100],
        "d_inner_m": [0.080, 0.100],
        "d_outer_m": [0.100, 0.120],
        "w_loss_w_per_m": [None, None],  # Use U-value mode
        "u_wpermk": [0.35, 0.4],  # Different U-values
        "cost_eur_per_m": [250.0, 300.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    # Single segment to test U-value calculation
    segs = [Segment("S1", 100.0, 0.01, 0, "P1", is_supply=True)]
    
    design = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=1.0, hours=8760, 
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)
    
    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    
    # Test with different U-values
    m1 = opt.evaluate_quick({"S1": 80})  # U = 0.35 W/m²K
    m2 = opt.evaluate_quick({"S1": 100})  # U = 0.4 W/m²K
    
    loss1 = m1["per_segment"]["S1"]["heat_loss_W"]
    loss2 = m2["per_segment"]["S1"]["heat_loss_W"]
    
    # Higher U-value should result in higher heat loss
    assert loss2 > loss1
    
    # Verify the U-value ratio effect (0.4/0.35 ≈ 1.14)
    expected_ratio = 0.4 / 0.35
    actual_ratio = loss2 / loss1
    assert actual_ratio == pytest.approx(expected_ratio, rel=1e-2)


def test_heat_loss_soil_temperature_effect(tmp_path):
    """Test that heat loss depends on soil temperature."""
    catalog = pd.DataFrame({
        "dn": [100],
        "d_inner_m": [0.100],
        "d_outer_m": [0.120],
        "w_loss_w_per_m": [None],
        "u_wpermk": [0.4],
        "cost_eur_per_m": [300.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    segs = [Segment("S1", 100.0, 0.01, 0, "P1", is_supply=True)]
    
    # Test with different soil temperatures
    design1 = dict(
        T_supply=80, T_return=50, T_soil=5,  # Cold soil
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=1.0, hours=8760, 
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    design2 = dict(
        T_supply=80, T_return=50, T_soil=15,  # Warm soil
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=1.0, hours=8760, 
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)
    
    opt1 = DiameterOptimizer(segs, design1, econ, str(cpath))
    opt2 = DiameterOptimizer(segs, design2, econ, str(cpath))
    
    m1 = opt1.evaluate_quick({"S1": 100})
    m2 = opt2.evaluate_quick({"S1": 100})
    
    loss1 = m1["per_segment"]["S1"]["heat_loss_W"]  # Cold soil
    loss2 = m2["per_segment"]["S1"]["heat_loss_W"]  # Warm soil
    
    # Cold soil should result in higher heat loss
    assert loss1 > loss2
    
    # Verify the temperature difference effect
    # Cold soil: ΔT = 80-5 = 75K
    # Warm soil: ΔT = 80-15 = 65K
    expected_ratio = (80 - 5) / (80 - 15)  # 75/65 ≈ 1.15
    actual_ratio = loss1 / loss2
    assert actual_ratio == pytest.approx(expected_ratio, rel=1e-2)


def test_heat_loss_annual_calculation(tmp_path):
    """Test that annual heat loss is correctly calculated."""
    catalog = pd.DataFrame({
        "dn": [100],
        "d_inner_m": [0.100],
        "d_outer_m": [0.120],
        "w_loss_w_per_m": [25.0],  # Direct W/m mode
        "u_wpermk": [0.4],
        "cost_eur_per_m": [300.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)
    
    segs = [Segment("S1", 100.0, 0.01, 0, "P1", is_supply=True)]
    
    # Test with different annual hours
    design1 = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=1.0, hours=1000,  # 1000 hours
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    design2 = dict(
        T_supply=80, T_return=50, T_soil=10, 
        rho=1000.0, mu=4.5e-4, cp=4180.0,
        eta_pump=1.0, hours=8760,  # 8760 hours
        v_feasible_target=1.3, v_limit=1.5,
        deltaT_min=30.0, K_minor=0.0
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)
    
    opt1 = DiameterOptimizer(segs, design1, econ, str(cpath))
    opt2 = DiameterOptimizer(segs, design2, econ, str(cpath))
    
    m1 = opt1.evaluate_quick({"S1": 100})
    m2 = opt2.evaluate_quick({"S1": 100})
    
    # Per-segment heat loss should be the same (same conditions)
    assert m1["per_segment"]["S1"]["heat_loss_W"] == m2["per_segment"]["S1"]["heat_loss_W"]
    
    # Annual heat loss should scale with hours
    expected_ratio = 8760 / 1000  # 8.76
    actual_ratio = m2["heat_loss_MWh"] / m1["heat_loss_MWh"]
    assert actual_ratio == pytest.approx(expected_ratio, rel=1e-3)


if __name__ == "__main__":
    pytest.main([__file__]) 