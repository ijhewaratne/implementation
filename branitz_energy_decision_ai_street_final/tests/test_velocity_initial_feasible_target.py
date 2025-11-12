"""
Test that initial feasible assignment respects the 1.3 m/s target.
"""

import pytest, pandas as pd
from optimize.diameter_optimizer import Segment, DiameterOptimizer

def test_initial_feasible_respects_velocity_target(tmp_path):
    catalog = pd.DataFrame({
        "dn":[40,50],
        "d_inner_m":[0.040,0.050],
        "d_outer_m":[0.050,0.063],
        "w_loss_w_per_m":[20.0,24.0],
        "u_wpermk":[0.4,0.4],
        "cost_eur_per_m":[110.0,120.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)

    segs = [Segment("S1", length_m=150.0, V_dot_m3s=0.0021, Q_seg_W=0, path_id="P1", is_supply=True)]
    design = dict(T_supply=80, T_return=50, T_soil=10, rho=983.0, mu=4.5e-4, cp=4180.0,
                  eta_pump=0.65, hours=1000, v_feasible_target=1.3, v_limit=1.5,
                  deltaT_min=30.0, K_minor=0.0)
    econ   = dict(price_el=0.25, cost_heat_prod=55.0, years=30, r=0.04, o_and_m_rate=0.01)

    opt = DiameterOptimizer(segs, design, econ, str(cpath))

    # The initial_feasible method exists, so we can test it

    assignment = opt.initial_feasible()
    m = opt.evaluate_quick(assignment)
    assert m["v_max"] <= design["v_feasible_target"] + 1e-6 