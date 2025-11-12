"""
Reporting and Geo Export Helpers for DH Optimizer

This module provides utilities for generating compliance reports and exporting
optimized network geometries with diameter assignments.

Expected schemas:
- per_seg_df: pandas.DataFrame with columns seg_id, length_m, DN, V_dot_m3s, v_mps, 
  dp_Pa, h_m, heat_loss_W, path_id, is_supply
- summary: dict with keys npv_eur, capex_eur, opex_eur_per_a, pump_MWh, heat_loss_MWh,
  v_max, head_required_m, deltaT_design_k, velocity_ok, deltaT_ok
- net_lines_gdf: geopandas.GeoDataFrame with columns seg_id, geometry

All functions return absolute file paths to created files.
"""

from __future__ import annotations
from pathlib import Path
import html
import pandas as pd

def write_compliance_report(
    street: str,
    per_seg_df: pd.DataFrame,
    summary: dict,
    out_dir: str,
    v_limit: float = 1.5,
    deltaT_min: float = 30.0,
) -> str:
    """
    Write a compact HTML report with KPIs and a per-segment table.
    Returns absolute file path.
    """
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    report_path = out / "compliance_report.html"

    def badge(ok: bool) -> str:
        return f'<span class="badge {"ok" if ok else "fail"}'> + ("PASS" if ok else "FAIL") + "</span>"

    # KPIs
    vel_ok = bool(summary.get("velocity_ok", False))
    dT_ok  = bool(summary.get("deltaT_ok", False))
    pump   = summary.get("pump_MWh", 0.0)
    hloss  = summary.get("heat_loss_MWh", 0.0)
    v_max  = summary.get("v_max", 0.0)
    head_m = summary.get("head_required_m", 0.0)
    npv_e  = summary.get("npv_eur", None)
    capex  = summary.get("capex_eur", None)
    opex_a = summary.get("opex_eur_per_a", None)
    mc     = summary.get("monte_carlo", None)

    # Simple HTML
    html_txt = f"""<html><head><meta charset="utf-8"><style>
    body{{font-family:system-ui,Arial,sans-serif;margin:16px}}
    .kpis{{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:12px}}
    .card{{border:1px solid #e5e7eb;border-radius:12px;padding:12px;min-width:200px}}
    .badge.ok{{background:#16a34a;color:#fff;padding:2px 8px;border-radius:12px}}
    .badge.fail{{background:#dc2626;color:#fff;padding:2px 8px;border-radius:12px}}
    table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #e5e7eb;padding:6px;text-align:left}}
    </style></head><body>
    <h1>Compliance Report — {html.escape(street)}</h1>
    <div class="kpis">
      <div class="card"><div><strong>Velocity (≤ {v_limit} m/s)</strong></div><div>{badge(vel_ok)}</div><div>v_max={v_max:.2f}</div></div>
      <div class="card"><div><strong>Temperature Difference (≥ {deltaT_min} K)</strong></div><div>{badge(dT_ok)}</div><div>ΔT_design={summary.get("deltaT_design_k",0):.1f}</div></div>
      <div class="card"><div><strong>Pump Energy</strong></div><div>{pump:.2f} MWh/a</div></div>
      <div class="card"><div><strong>Heat Loss</strong></div><div>{hloss:.2f} MWh/a</div></div>
      <div class="card"><div><strong>Head Required</strong></div><div>{head_m:.2f} m</div></div>
      <div class="card"><div><strong>NPV</strong></div><div>{f"{npv_e:,.0f} €" if npv_e is not None else "–"}</div></div>
      <div class="card"><div><strong>CapEx / OpEx</strong></div><div>{f"{capex:,.0f} €" if capex is not None else "–"} / {f"{opex_a:,.0f} €/a" if opex_a is not None else "–"}</div></div>
    </div>
    """
    # Monte Carlo band if available
    if isinstance(mc, dict) and mc:
        html_txt += "<div class='card'><div><strong>Monte Carlo (NPV)</strong></div>"
        for k in ("npv_p10","npv_p50","npv_p90"):
            if k in mc:
                html_txt += f"<div>{k}: {mc[k]:,.0f} €</div>"
        html_txt += "</div>"

    # Per-segment table
    html_txt += "<h2>Segments</h2><table><thead><tr>"
    for c in per_seg_df.columns:
        html_txt += f"<th>{html.escape(str(c))}</th>"
    html_txt += "</tr></thead><tbody>"
    for _, row in per_seg_df.iterrows():
        html_txt += "<tr>" + "".join(f"<td>{html.escape(str(row[c]))}</td>" for c in per_seg_df.columns) + "</tr>"
    html_txt += "</tbody></table></body></html>"

    report_path.write_text(html_txt, encoding="utf-8")
    return str(report_path.resolve())

def export_geojson_with_dn(per_seg_df: pd.DataFrame, out_path: str) -> str:
    """
    Export per-segment data as GeoJSON.
    If geometry column exists and geopandas is available, use it; otherwise emit FeatureCollection with properties only.
    """
    out = Path(out_path); out.parent.mkdir(parents=True, exist_ok=True)
    try:
        import geopandas as gpd  # optional
        if "geometry" in per_seg_df.columns:
            gpd.GeoDataFrame(per_seg_df, geometry="geometry", crs=getattr(per_seg_df, "crs", None)).to_file(out, driver="GeoJSON")
            return str(out.resolve())
    except Exception:
        pass
    # properties-only fallback
    import json
    feats = []
    for _, r in per_seg_df.iterrows():
        props = {k: (None if pd.isna(v) else v) for k,v in r.items() if k != "geometry"}
        feats.append({"type":"Feature","geometry":None,"properties":props})
    fc = {"type":"FeatureCollection","features":feats}
    out.write_text(json.dumps(fc, indent=2), encoding="utf-8")
    return str(out.resolve()) 