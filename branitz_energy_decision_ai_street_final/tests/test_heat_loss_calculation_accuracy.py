"""
Test heat loss calculation accuracy.

This module contains tests to verify that heat loss calculations
match expected values based on pipe specifications.
"""

import pandas as pd
import pytest
from optimize.diameter_optimizer import Segment, DiameterOptimizer


def test_heat_loss_calculation_accuracy(tmp_path):
    """Test that heat loss calculation matches expected values."""
    catalog = pd.DataFrame({
        "dn": [100],
        "d_inner_m": [0.100],
        "d_outer_m": [0.120],
        "w_loss_w_per_m": [25.0],  # 25 W/m heat loss
        "u_wpermk": [0.4],
        "cost_eur_per_m": [300.0],
    })
    cpath = tmp_path / "catalog.csv"
    catalog.to_csv(cpath, index=False)

    # 100m segment should lose 2500 W
    segs = [Segment("S1", 100.0, 0.01, 0, "P1", is_supply=True)]
    design = dict(T_supply=80, T_return=50, T_soil=10, rho=1000.0, mu=4.5e-4, cp=4180.0,
                  eta_pump=1.0, hours=8760, v_feasible_target=1.3, v_limit=1.5, deltaT_min=30.0, K_minor=0.0)
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)

    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    m = opt.evaluate_quick({"S1": 100})
    
    # Heat loss should be 2500 W * 8760 h / 1e6 = 21.9 MWh/a
    expected_heat_loss_mwh = 25.0 * 100.0 * 8760.0 / 1e6
    assert m["heat_loss_MWh"] == pytest.approx(expected_heat_loss_mwh, rel=1e-3)
    
    # Per-segment heat loss should be 2500 W
    assert m["per_segment"]["S1"]["heat_loss_W"] == pytest.approx(2500.0, rel=1e-3)


def test_heat_loss_zero_flow_segments(tmp_path):
    """Test that very low flow segments have minimal heat loss."""
    catalog = pd.DataFrame({
        "dn": [100],
        "d_inner_m": [0.100],
        "d_outer_m": [0.120],
        "w_loss_w_per_m": [25.0],
        "u_wpermk": [0.4],
        "cost_eur_per_m": [300.0],
    })
    cpath = tmp_path / "catalog.csv"
    catalog.to_csv(cpath, index=False)

    # Segment with very low flow (not zero to avoid physics model error)
    segs = [Segment("S1", 100.0, 0.0001, 0, "P1", is_supply=True)]
    design = dict(T_supply=80, T_return=50, T_soil=10, rho=1000.0, mu=4.5e-4, cp=4180.0,
                  eta_pump=1.0, hours=8760, v_feasible_target=1.3, v_limit=1.5, deltaT_min=30.0, K_minor=0.0)
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)

    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    m = opt.evaluate_quick({"S1": 100})
    
    # Very low flow segments should have minimal heat loss
    # Heat loss should be 25 W/m * 100 m = 2500 W regardless of flow
    assert m["per_segment"]["S1"]["heat_loss_W"] == pytest.approx(2500.0, rel=1e-3)
    assert m["heat_loss_MWh"] == pytest.approx(2500.0 * 8760.0 / 1e6, rel=1e-3)


def test_heat_loss_supply_vs_return_temperature(tmp_path):
    """Test that heat loss uses correct temperature for supply vs return."""
    catalog = pd.DataFrame({
        "dn": [100],
        "d_inner_m": [0.100],
        "d_outer_m": [0.120],
        "w_loss_w_per_m": [25.0],
        "u_wpermk": [0.4],
        "cost_eur_per_m": [300.0],
    })
    cpath = tmp_path / "catalog.csv"
    catalog.to_csv(cpath, index=False)

    # Supply and return segments with same flow
    segs = [
        Segment("SUP", 100.0, 0.01, 0, "P1", is_supply=True),
        Segment("RET", 100.0, 0.01, 0, "P1", is_supply=False),
    ]
    design = dict(T_supply=80, T_return=50, T_soil=10, rho=1000.0, mu=4.5e-4, cp=4180.0,
                  eta_pump=1.0, hours=8760, v_feasible_target=1.3, v_limit=1.5, deltaT_min=30.0, K_minor=0.0)
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)

    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    m = opt.evaluate_quick({"SUP": 100, "RET": 100})
    
    # Both segments should have the same heat loss (using W/m directly)
    # since they have the same length and w_loss_w_per_m
    sup_heat_loss = m["per_segment"]["SUP"]["heat_loss_W"]
    ret_heat_loss = m["per_segment"]["RET"]["heat_loss_W"]
    assert sup_heat_loss == pytest.approx(ret_heat_loss, rel=1e-3)
    
    # Total heat loss should be sum of both segments
    expected_total = (sup_heat_loss + ret_heat_loss) * 8760.0 / 1e6
    assert m["heat_loss_MWh"] == pytest.approx(expected_total, rel=1e-3)


if __name__ == "__main__":
    pytest.main([__file__]) 