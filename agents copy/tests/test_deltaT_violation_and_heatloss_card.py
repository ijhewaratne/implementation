"""
Test that ΔT violation triggers FAIL badge and Heat Loss KPI card renders.
"""

import pandas as pd
from optimize.diameter_optimizer import Segment, DiameterOptimizer
from optimize.reporting import write_compliance_report


def test_deltaT_violation_and_heatloss_card(tmp_path):
    """Test that ΔT violation triggers FAIL badge and Heat Loss KPI card renders."""
    # Catalog with known heat loss per m so the KPI is non-zero
    catalog = pd.DataFrame(
        {
            "dn": [80],
            "d_inner_m": [0.080],
            "d_outer_m": [0.100],
            "w_loss_w_per_m": [50.0],
            "u_wpermk": [0.4],
            "cost_eur_per_m": [200.0],
        }
    )
    cpath = tmp_path / "catalog.csv"
    catalog.to_csv(cpath, index=False)

    seg = Segment(
        "S1", length_m=100.0, V_dot_m3s=0.01, Q_seg_W=200000, path_id="P1", is_supply=True
    )
    design = dict(
        T_supply=70.0,
        T_return=45.0,  # ΔT=25 < min30 → violation
        T_soil=10.0,
        rho=983.0,
        mu=4.5e-4,
        cp=4180.0,
        eta_pump=0.65,
        hours=3000,
        v_feasible_target=1.3,
        v_limit=1.5,
        deltaT_min=30.0,
        K_minor=0.0,
    )
    econ = dict(price_el=0.25, cost_heat_prod=55.0, years=30, r=0.04, o_and_m_rate=0.01)

    opt = DiameterOptimizer([seg], design, econ, str(cpath))
    metrics = opt.evaluate_quick({"S1": 80})
    assert metrics["deltaT_ok"] is False

    per_seg_df = pd.DataFrame(
        [
            {
                "seg_id": "S1",
                "length_m": seg.length_m,
                "DN": metrics["per_segment"]["S1"]["dn"],
                "V_dot_m3s": seg.V_dot_m3s,
                "v_mps": metrics["per_segment"]["S1"]["v"],
                "dp_Pa": metrics["per_segment"]["S1"]["dp"],
                "h_m": metrics["per_segment"]["S1"]["h"],
                "heat_loss_W": metrics["per_segment"]["S1"]["heat_loss_W"],
                "path_id": seg.path_id,
                "is_supply": seg.is_supply,
            }
        ]
    )
    summary = dict(
        npv_eur=metrics["npv_eur"],
        capex_eur=metrics["capex_eur"],
        opex_eur_per_a=metrics["opex_eur_per_a"],
        pump_MWh=metrics["pump_MWh"],
        heat_loss_MWh=metrics["heat_loss_MWh"],
        v_max=metrics["v_max"],
        head_required_m=metrics["head_required_m"],
        deltaT_design_k=design["T_supply"] - design["T_return"],
        velocity_ok=metrics["velocity_ok"],
        deltaT_ok=metrics["deltaT_ok"],
    )

    html = write_compliance_report(
        "Test Street",
        per_seg_df,
        summary,
        str(tmp_path),
        v_limit=design["v_limit"],
        deltaT_min=design["deltaT_min"],
    )
    content = (tmp_path / html.split("/")[-1]).read_text(encoding="utf-8")
    assert "Temperature Difference" in content and "FAIL" in content
    assert "Heat Loss" in content  # ensure KPI card rendered
