#!/usr/bin/env python3
"""
CLI: Integrate NPV-based DN optimization with DH system artifacts.

Flags (per exposé):
  --optimize-dn          run diameter optimization (default: on when --catalog is provided)
  --catalog PATH         CSV pipe catalog
  --segments-csv PATH    CSV with columns: seg_id,length_m,V_dot_m3s,Q_seg_W,path_id,is_supply[,DN]
  --street NAME          optional street name (for report labelling)
  --out-dir PATH         output directory (default: results_test/npv_dh)
  --report-html NAME     report filename (default: compliance_report.html)
  --export-geojson PATH  optional GeoJSON export path (properties-only if no geometry available)
  --monte-carlo N        run Monte Carlo economics with N trials (default: 0 = skip)
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

try:
    # Preferred local optimizer API
    from optimize.diameter_optimizer import Segment, DiameterOptimizer
except Exception:
    Segment = None
    DiameterOptimizer = None

from optimize.per_seg import build_per_segment_df
from optimize.reporting import write_compliance_report, export_geojson_with_dn

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="integrate_npv_with_dh_system",
                                description="NPV–DH diameter optimization & reporting")
    p.add_argument("--optimize-dn", action="store_true", default=False,
                   help="Run DN optimization (enabled automatically when --catalog is set)")
    p.add_argument("--catalog", type=Path, help="Pipe catalog CSV")
    p.add_argument("--segments-csv", type=Path, help="Segments CSV (seg_id,length_m,V_dot_m3s,Q_seg_W,path_id,is_supply[,DN])")
    p.add_argument("--street", type=str, default="Unnamed Street", help="Street label for reports")
    p.add_argument("--out-dir", type=Path, default=Path("results_test/npv_dh"), help="Output directory")
    p.add_argument("--report-html", type=str, default="compliance_report.html", help="Report filename")
    p.add_argument("--export-geojson", type=Path, help="Write per-segment GeoJSON to this path")
    p.add_argument("--monte-carlo", type=int, default=0, help="Trials for Monte Carlo (0 = skip)")
    # Minimal design/econ knobs
    p.add_argument("--T-supply", type=float, default=80.0)
    p.add_argument("--T-return", type=float, default=50.0)
    p.add_argument("--hours", type=float, default=3000.0)
    p.add_argument("--v-target", type=float, default=1.3)
    p.add_argument("--v-limit", type=float, default=1.5)
    p.add_argument("--deltaT-min", type=float, default=30.0)
    p.add_argument("--eta-pump", type=float, default=0.65)
    p.add_argument("--price-el", type=float, default=0.25)
    p.add_argument("--cost-heat", type=float, default=55.0)
    p.add_argument("--years", type=int, default=30)
    p.add_argument("--discount", type=float, default=0.04)
    return p

def _read_segments_csv(path: Path) -> list:
    df = pd.read_csv(path)
    required = {"seg_id","length_m","V_dot_m3s","Q_seg_W","path_id","is_supply"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"--segments-csv missing columns: {sorted(missing)}")
    segs = []
    for _, r in df.iterrows():
        segs.append(Segment(
            seg_id=str(r["seg_id"]),
            length_m=float(r["length_m"]),
            V_dot_m3s=float(r["V_dot_m3s"]),
            Q_seg_W=float(r["Q_seg_W"]),
            path_id=str(r["path_id"]),
            is_supply=bool(r["is_supply"]),
        ))
    return segs

def _greedy_assign_dn(segments: list, catalog_df: pd.DataFrame, v_limit: float) -> dict[str,int]:
    """
    Fallback if DiameterOptimizer.run() is unavailable:
    For each segment, pick the smallest DN whose v <= v_limit (approximate via inner diameter area).
    """
    import math
    # build per-DN area
    cand = [(int(r["dn"]), float(r["d_inner_m"])) for _, r in catalog_df.iterrows()]
    cand.sort(key=lambda x: x[1])  # ascending diameter
    assignment = {}
    for s in segments:
        A_req = None
        if s.V_dot_m3s > 0:
            v_req = v_limit
            A_req = s.V_dot_m3s / v_req
        chosen_dn = cand[-1][0]  # largest as fallback
        for dn, d_inner in cand:
            area = math.pi*(d_inner**2)/4.0
            if A_req is None or area >= A_req:
                chosen_dn = dn
                break
        assignment[s.seg_id] = chosen_dn
    return assignment

def main(argv=None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.catalog is None:
        ap.error("--catalog is required")
    if Segment is None or DiameterOptimizer is None:
        ap.error("optimize.diameter_optimizer not importable in this environment")

    catalog_df = pd.read_csv(args.catalog)
    # segments: CSV is explicit & robust for CI; other sources can be wired later
    if not args.segments_csv:
        ap.error("--segments-csv required for this CLI (no street extractor wired)")
    segments = _read_segments_csv(args.segments_csv)

    design = dict(
        T_supply=args.T_supply, T_return=args.T_return, T_soil=10.0,
        rho=983.0, mu=4.5e-4, cp=4180.0, eta_pump=args.eta_pump,
        hours=args.hours, v_feasible_target=args.v_target, v_limit=args.v_limit,
        deltaT_min=args.deltaT_min, K_minor=1.0,
    )
    econ = dict(price_el=args.price_el, cost_heat_prod=args.cost_heat,
                years=args.years, r=args.discount, o_and_m_rate=0.01)

    # Run optimization
    opt = DiameterOptimizer(segments, design, econ, str(args.catalog))
    if hasattr(opt, "run") and (args.optimize_dn or args.catalog):
        assignment, metrics, _ = opt.run()
    else:
        assignment = _greedy_assign_dn(segments, catalog_df, args.v_limit)
        metrics = opt.evaluate_quick(assignment)

    per_seg_df = build_per_segment_df(segments, metrics)

    # Optional Monte Carlo
    mc_summary = None
    if args.monte_carlo and args.monte_carlo > 0:
        try:
            from econ.monte_carlo import run_monte_carlo
            mc = run_monte_carlo(assignment, per_seg_df, design, econ, catalog_df, n=int(args.monte_carlo))
            mc_summary = mc.get("summary", {})
        except Exception as e:
            mc_summary = {"error": str(e)}

    # Build summary for report
    summary = dict(
        npv_eur=metrics.get("npv_eur"),
        capex_eur=metrics.get("capex_eur"),
        opex_eur_per_a=metrics.get("opex_eur_per_a"),
        pump_MWh=metrics.get("pump_MWh"),
        heat_loss_MWh=metrics.get("heat_loss_MWh"),
        v_max=metrics.get("v_max"),
        head_required_m=metrics.get("head_required_m"),
        deltaT_design_k=design["T_supply"]-design["T_return"],
        velocity_ok=metrics.get("velocity_ok"),
        deltaT_ok=metrics.get("deltaT_ok"),
        monte_carlo=mc_summary,
    )

    report_path = write_compliance_report(
        street=args.street,
        per_seg_df=per_seg_df,
        summary=summary,
        out_dir=str(args.out_dir),
        v_limit=args.v_limit,
        deltaT_min=args.deltaT_min,
    )

    if args.export_geojson:
        try:
            export_geojson_with_dn(per_seg_df, str(args.export_geojson))
        except Exception as e:
            (args.out_dir / "geojson_export_error.txt").write_text(str(e), encoding="utf-8")

    # Save assignment + metrics JSON for debugging
    (args.out_dir / "assignment.json").write_text(json.dumps(assignment, indent=2), encoding="utf-8")
    (args.out_dir / "metrics.json").write_text(json.dumps({k: float(v) if isinstance(v,(int,float)) else v
                                                          for k,v in metrics.items()}, indent=2), encoding="utf-8")
    print(f"✅ Report: {report_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main()) 