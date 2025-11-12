import pandas as pd, pytest
from optimize.diameter_optimizer import Segment, DiameterOptimizer


def test_pump_energy_uses_worst_path(tmp_path):
    catalog = pd.DataFrame(
        {
            "dn": [100, 150],
            "d_inner_m": [0.100, 0.150],
            "d_outer_m": [0.120, 0.180],
            "w_loss_w_per_m": [40.0, 60.0],
            "u_wpermk": [0.4, 0.4],
            "cost_eur_per_m": [300.0, 500.0],
        }
    )
    cpath = tmp_path / "catalog.csv"
    catalog.to_csv(cpath, index=False)

    segs = [
        # Two SUPPLY paths with different flow/length -> different dp & Vdot
        Segment("S1", length_m=200.0, V_dot_m3s=0.012, Q_seg_W=0, path_id="P1", is_supply=True),
        Segment("S2", length_m=100.0, V_dot_m3s=0.020, Q_seg_W=0, path_id="P2", is_supply=True),
    ]
    design = dict(
        T_supply=80,
        T_return=50,
        T_soil=10,
        rho=1000.0,
        mu=4.5e-4,
        cp=4180.0,
        eta_pump=0.6,
        hours=2000,
        v_feasible_target=1.3,
        v_limit=1.5,
        deltaT_min=30.0,
        K_minor=0.0,
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=1, r=0.0, o_and_m_rate=0.0)

    opt = DiameterOptimizer(segs, design, econ, str(cpath))
    m = opt.evaluate_quick({"S1": 100, "S2": 150})

    # Identify worst path from stats
    worst_pid = max(m["path_stats"], key=lambda pid: m["path_stats"][pid]["dp_Pa"])
    dp = m["path_stats"][worst_pid]["dp_Pa"]
    vdot = m["path_stats"][worst_pid]["V_dot_peak_m3s"]

    expected = dp * vdot * design["hours"] / (design["eta_pump"] * 1e6)
    assert m["pump_MWh"] == pytest.approx(expected, rel=1e-3)
