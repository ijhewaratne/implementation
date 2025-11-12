import pandas as pd
from optimize.diameter_optimizer import Segment, DiameterOptimizer

def test_custom_deltaT_min_violation(tmp_path):
    catalog = pd.DataFrame({
        "dn":[80],
        "d_inner_m":[0.080],
        "d_outer_m":[0.100],
        "w_loss_w_per_m":[50.0],
        "u_wpermk":[0.4],
        "cost_eur_per_m":[200.0],
    })
    cpath = tmp_path/"catalog.csv"; catalog.to_csv(cpath, index=False)

    segs = [Segment("S1", 100.0, 0.01, 0, "P1", True)]
    design = dict(T_supply=80.0, T_return=50.0,  # ΔT_design = 30
                  T_soil=10.0, rho=983.0, mu=4.5e-4, cp=4180.0,
                  eta_pump=0.65, hours=1000, v_feasible_target=1.3, v_limit=1.5,
                  deltaT_min=35.0, K_minor=0.0)
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=30, r=0.04, o_and_m_rate=0.01)

    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    m = opt.evaluate_quick({"S1":80})
    assert m["deltaT_ok"] is False  # 30 < 35 → violation 