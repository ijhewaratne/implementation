"""
Test worst-path head aggregation with multiple paths and Pa→m head consistency.
"""

import math
import pandas as pd
import pytest
from optimize.diameter_optimizer import Segment, DiameterOptimizer


def test_worst_path_multi_and_head_units(tmp_path):
    """Test worst path head aggregation with multiple paths and Pa→m head consistency."""
    catalog = pd.DataFrame({
        "dn": [100, 150],
        "d_inner_m": [0.10, 0.15],
        "d_outer_m": [0.12, 0.18],
        "w_loss_w_per_m": [45.0, 60.0],
        "u_wpermk": [0.4, 0.4],
        "cost_eur_per_m": [300.0, 500.0]
    })
    cpath = tmp_path / "catalog.csv"
    catalog.to_csv(cpath, index=False)

    segs = [
        Segment("S1", length_m=100.0, V_dot_m3s=0.010, Q_seg_W=100000, path_id="P1", is_supply=True),
        Segment("S2", length_m=200.0, V_dot_m3s=0.015, Q_seg_W=200000, path_id="P2", is_supply=True),
    ]
    design = dict(T_supply=80, T_return=50, T_soil=10, rho=1000.0, mu=4.5e-4, cp=4180.0,
                  eta_pump=1.0, hours=1000, v_feasible_target=1.3, v_limit=1.5, deltaT_min=30.0, K_minor=0.0)
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)

    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    m = opt.evaluate_quick({"S1": 100, "S2": 150})

    # Worst path equals the max dp among paths
    ps = m["path_stats"]
    dp_vals = {pid: ps[pid]["dp_Pa"] for pid in ps}
    dp_max = max(dp_vals.values())
    assert m["dp_path_max_Pa"] == pytest.approx(dp_max, rel=1e-6)

    # Head conversion: h ≈ dp / (rho * g)
    g = 9.81
    assert m["head_required_m"] == pytest.approx(dp_max / (design["rho"] * g), rel=1e-3) 