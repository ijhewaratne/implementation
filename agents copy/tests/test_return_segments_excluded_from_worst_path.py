import pandas as pd, pytest
from optimize.diameter_optimizer import Segment, DiameterOptimizer


def test_returns_excluded_in_worst_path(tmp_path):
    catalog = pd.DataFrame(
        {
            "dn": [100],
            "d_inner_m": [0.100],
            "d_outer_m": [0.120],
            "w_loss_w_per_m": [45.0],
            "u_wpermk": [0.4],
            "cost_eur_per_m": [300.0],
        }
    )
    cpath = tmp_path / "catalog.csv"
    catalog.to_csv(cpath, index=False)

    segs = [
        Segment("SUP", length_m=100.0, V_dot_m3s=0.01, Q_seg_W=0, path_id="P1", is_supply=True),
        Segment(
            "RET", length_m=1e6, V_dot_m3s=0.50, Q_seg_W=0, path_id="P99", is_supply=False
        ),  # absurd return
    ]
    design = dict(
        T_supply=80,
        T_return=50,
        T_soil=10,
        rho=1000.0,
        mu=4.5e-4,
        cp=4180.0,
        eta_pump=1.0,
        hours=10,
        v_feasible_target=1.3,
        v_limit=1.5,
        deltaT_min=30.0,
        K_minor=0.0,
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)

    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    m = opt.evaluate_quick({"SUP": 100, "RET": 100})
    # Only P1 must appear; RET path (P99) should not influence path_stats or dp_path_max_Pa
    assert set(m["path_stats"].keys()) == {"P1"}
    assert m["dp_path_max_Pa"] == pytest.approx(m["path_stats"]["P1"]["dp_Pa"])
