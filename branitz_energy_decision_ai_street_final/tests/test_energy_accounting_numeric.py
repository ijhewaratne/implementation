"""
Test pump energy and heat loss numeric consistency.
"""

import pytest
import pandas as pd
from optimize.diameter_optimizer import Segment, DiameterOptimizer


def test_pump_and_heatloss_numeric(tmp_path):
    """Test pump energy and heat loss numeric consistency."""
    catalog = pd.DataFrame({
        "dn": [80],
        "d_inner_m": [0.080],
        "d_outer_m": [0.100],
        "w_loss_w_per_m": [50.0],
        "u_wpermk": [0.4],
        "cost_eur_per_m": [200.0],
    })
    cpath = tmp_path / "catalog.csv"
    catalog.to_csv(cpath, index=False)

    seg = Segment("S1", length_m=200.0, V_dot_m3s=0.010, Q_seg_W=0, path_id="P1", is_supply=True)
    design = dict(T_supply=80, T_return=50, T_soil=10, rho=1000.0, mu=4.5e-4, cp=4180.0,
                  eta_pump=0.5, hours=1000, v_feasible_target=1.3, v_limit=1.5, deltaT_min=30.0, K_minor=0.0)
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)

    opt = DiameterOptimizer([seg], design, econ, str(cpath))
    m = opt.evaluate_quick({"S1": 80})

    # Heat loss MWh ≈ Σ (w_loss[W/m] * length[m]) * hours / 1e6
    expected_loss_mwh = 50.0 * 200.0 * design["hours"] / 1e6
    assert m["heat_loss_MWh"] == pytest.approx(expected_loss_mwh, rel=1e-6)

    # Pump MWh ≈ (dp_worst[Pa] * Vdot_worst[m³/s] * hours) / (eta * 1e6)
    # Pull worst-path dp & Vdot from reported stats
    pid_worst = max(m["path_stats"], key=lambda pid: m["path_stats"][pid]["dp_Pa"])
    dp = m["path_stats"][pid_worst]["dp_Pa"]
    vdot = m["path_stats"][pid_worst]["V_dot_peak_m3s"]
    expected_pump_mwh = dp * vdot * design["hours"] / (design["eta_pump"] * 1e6)
    assert m["pump_MWh"] == pytest.approx(expected_pump_mwh, rel=1e-3) 