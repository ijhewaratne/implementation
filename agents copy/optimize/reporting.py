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

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

__all__ = ["write_compliance_report", "export_geojson_with_dn"]


def _fmt_currency(eur: float) -> str:
    """
    Format currency value with locale-independent formatting.

    Parameters
    ----------
    eur : float
        Amount in euros

    Returns
    -------
    str
        Formatted currency string (e.g., "€ 1,234,567")
    """
    if pd.isna(eur) or not np.isfinite(eur):
        return "–"

    # Format with thousands separator
    formatted = f"{eur:,.0f}"
    return f"€ {formatted}"


def _fmt_float(x: float, unit: str) -> str:
    """
    Format float value with unit.

    Parameters
    ----------
    x : float
        Value to format
    unit : str
        Unit string

    Returns
    -------
    str
        Formatted value with unit (e.g., "1.23 m/s")
    """
    if pd.isna(x) or not np.isfinite(x):
        return "–"

    # Format with appropriate precision
    if abs(x) < 0.01:
        formatted = f"{x:.3f}"
    elif abs(x) < 1:
        formatted = f"{x:.2f}"
    elif abs(x) < 100:
        formatted = f"{x:.1f}"
    else:
        formatted = f"{x:.0f}"

    return f"{formatted} {unit}"


def write_compliance_report(
    street: str,
    per_seg_df: pd.DataFrame,
    summary: Dict[str, Any],
    out_dir: str,
    *,
    v_limit: float = 1.5,
    deltaT_min: float = 30.0,
) -> str:
    """
    Write HTML compliance report for DH network optimization.

    Parameters
    ----------
    street : str
        Street name (e.g., "Branitzer Allee")
    per_seg_df : pd.DataFrame
        Per-segment data with columns: seg_id, length_m, DN, V_dot_m3s, v_mps,
        dp_Pa, h_m, heat_loss_W, path_id, is_supply
    summary : dict
        Summary metrics with keys: npv_eur, capex_eur, opex_eur_per_a, pump_MWh,
        heat_loss_MWh, v_max, head_required_m, deltaT_design_k, velocity_ok, deltaT_ok
    out_dir : str
        Output directory for HTML file
    v_limit : float, optional
        Velocity limit in m/s, default 1.5
    deltaT_min : float, optional
        Minimum temperature difference in K, default 30.0

    Returns
    -------
    str
        Absolute path to created HTML file

    Raises
    ------
    ValueError
        If required columns or keys are missing
    """
    # Validate required columns
    required_cols = [
        "seg_id",
        "length_m",
        "DN",
        "V_dot_m3s",
        "v_mps",
        "dp_Pa",
        "h_m",
        "heat_loss_W",
        "path_id",
        "is_supply",
    ]
    missing_cols = [col for col in required_cols if col not in per_seg_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in per_seg_df: {missing_cols}")

    # Validate required summary keys
    required_keys = [
        "npv_eur",
        "capex_eur",
        "opex_eur_per_a",
        "pump_MWh",
        "heat_loss_MWh",
        "v_max",
        "head_required_m",
        "deltaT_design_k",
        "velocity_ok",
        "deltaT_ok",
    ]
    missing_keys = [key for key in required_keys if key not in summary]
    if missing_keys:
        raise ValueError(f"Missing required keys in summary: {missing_keys}")

    # Create output directory if it doesn't exist
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Generate safe filename
    safe_street = re.sub(r"[^a-zA-Z0-9\s]", "", street).lower().replace(" ", "_")
    filename = f"compliance_report_{safe_street}.html"
    filepath = out_path / filename

    # Compute pass/fail counts
    velocity_pass = (per_seg_df["v_mps"] <= v_limit).sum()
    velocity_fail = (per_seg_df["v_mps"] > v_limit).sum()
    total_segments = len(per_seg_df)

    # Check for NaN/inf values and log warnings
    numeric_cols = ["length_m", "DN", "V_dot_m3s", "v_mps", "dp_Pa", "h_m", "heat_loss_W"]
    for col in numeric_cols:
        if col in per_seg_df.columns:
            nan_count = per_seg_df[col].isna().sum()
            inf_count = (~np.isfinite(per_seg_df[col])).sum()
            if nan_count > 0 or inf_count > 0:
                logger.warning(f"Column {col} has {nan_count} NaN and {inf_count} inf values")

    # Determine EN 13941 badge status
    velocity_badge = "pass" if (summary["velocity_ok"] and velocity_fail == 0) else "fail"
    deltaT_badge = (
        "pass" if (summary["deltaT_ok"] and summary["deltaT_design_k"] >= deltaT_min) else "fail"
    )

    # Truncate table if too large
    max_rows = 200
    table_df = per_seg_df.head(max_rows)
    table_note = (
        f"Showing first {len(table_df)} of {len(per_seg_df)} rows"
        if len(per_seg_df) > max_rows
        else ""
    )

    # Generate HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DH Network Compliance Report - {street}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0 0 10px 0;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 0.9em;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .kpi-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }}
        .kpi-card h3 {{
            margin: 0 0 10px 0;
            color: #495057;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .kpi-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #2c3e50;
        }}
        .compliance-section {{
            margin-bottom: 30px;
        }}
        .compliance-section h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
        }}
        .badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .badge.pass {{
            background: #16a34a;
            color: #fff;
        }}
        .badge.fail {{
            background: #dc2626;
            color: #fff;
        }}
        .table-container {{
            overflow-x: auto;
            margin-top: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }}
        th, td {{
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .table-note {{
            font-size: 0.8em;
            color: #6c757d;
            margin-top: 10px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>District Heating Network Compliance Report</h1>
            <p><strong>Street:</strong> {street}</p>
            <p class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="kpi-grid">
            <div class="kpi-card">
                <h3>Net Present Value</h3>
                <div class="kpi-value">{_fmt_currency(summary['npv_eur'])}</div>
            </div>
            <div class="kpi-card">
                <h3>Capital Expenditure</h3>
                <div class="kpi-value">{_fmt_currency(summary['capex_eur'])}</div>
            </div>
            <div class="kpi-card">
                <h3>Annual Operating Cost</h3>
                <div class="kpi-value">{_fmt_currency(summary['opex_eur_per_a'])}</div>
            </div>
            <div class="kpi-card">
                <h3>Pump Energy</h3>
                <div class="kpi-value">{_fmt_float(summary['pump_MWh'], 'MWh/a')}</div>
            </div>
            <div class="kpi-card">
                <h3>Heat Loss</h3>
                <div class="kpi-value">{_fmt_float(summary['heat_loss_MWh'], 'MWh/a')}</div>
            </div>
            <div class="kpi-card">
                <h3>Maximum Velocity</h3>
                <div class="kpi-value">{_fmt_float(summary['v_max'], 'm/s')}</div>
            </div>
            <div class="kpi-card">
                <h3>Required Pump Head</h3>
                <div class="kpi-value">{_fmt_float(summary['head_required_m'], 'm')}</div>
            </div>
            <div class="kpi-card">
                <h3>Design ΔT</h3>
                <div class="kpi-value">{_fmt_float(summary['deltaT_design_k'], 'K')}</div>
            </div>
        </div>
        
        <div class="compliance-section">
            <h2>EN 13941 Compliance</h2>
            <p><strong>Velocity Limit:</strong> <span class="badge {velocity_badge}">{velocity_badge.upper()}</span></p>
            <p><strong>Temperature Difference:</strong> <span class="badge {deltaT_badge}">{deltaT_badge.upper()}</span></p>
            <p><strong>Velocity Compliance:</strong> {velocity_pass} of {total_segments} segments pass (limit: {v_limit} m/s)</p>
            <p><strong>Temperature Compliance:</strong> Design ΔT of {_fmt_float(summary['deltaT_design_k'], 'K')} (minimum: {deltaT_min} K)</p>
        </div>
        
        <div class="compliance-section">
            <h2>Per-Segment Details</h2>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Segment ID</th>
                            <th>Length (m)</th>
                            <th>DN</th>
                            <th>Flow (m³/s)</th>
                            <th>Velocity (m/s)</th>
                            <th>Δp (Pa)</th>
                            <th>Head (m)</th>
                            <th>Heat Loss (W)</th>
                            <th>Path ID</th>
                            <th>Supply</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Add table rows
    for _, row in table_df.iterrows():
        html_content += f"""
                        <tr>
                            <td>{row['seg_id']}</td>
                            <td>{_fmt_float(row['length_m'], 'm')}</td>
                            <td>{row['DN'] if pd.notna(row['DN']) else '–'}</td>
                            <td>{_fmt_float(row['V_dot_m3s'], 'm³/s')}</td>
                            <td>{_fmt_float(row['v_mps'], 'm/s')}</td>
                            <td>{_fmt_float(row['dp_Pa'], 'Pa')}</td>
                            <td>{_fmt_float(row['h_m'], 'm')}</td>
                            <td>{_fmt_float(row['heat_loss_W'], 'W')}</td>
                            <td>{row['path_id']}</td>
                            <td>{'Yes' if row['is_supply'] else 'No'}</td>
                        </tr>
"""

    html_content += f"""
                    </tbody>
                </table>
                {f'<p class="table-note">{table_note}</p>' if table_note else ''}
            </div>
        </div>
    </div>
</body>
</html>
"""

    # Write HTML file
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"Compliance report written to: {filepath}")
    return str(filepath.absolute())


def export_geojson_with_dn(net_lines_gdf: Any, assignment: Dict[str, int], out_path: str) -> str:
    """
    Export GeoJSON with optimized diameter assignments.

    Parameters
    ----------
    net_lines_gdf : geopandas.GeoDataFrame
        Network lines with columns seg_id, geometry
    assignment : dict
        Mapping of seg_id to DN (diameter nominal)
    out_path : str
        Output path for GeoJSON file

    Returns
    -------
    str
        Absolute path to created GeoJSON file

    Raises
    ------
    ImportError
        If geopandas is not available
    ValueError
        If required columns are missing or assignment is empty
    """
    try:
        import geopandas as gpd
    except ImportError:
        raise ImportError("GeoJSON export requires geopandas. Install with: pip install geopandas")

    # Validate inputs
    if not assignment:
        raise ValueError("Assignment dictionary cannot be empty")

    if "seg_id" not in net_lines_gdf.columns:
        raise ValueError("GeoDataFrame missing required column: seg_id")

    if "geometry" not in net_lines_gdf.columns:
        raise ValueError("GeoDataFrame missing required column: geometry")

    # Create output directory if it doesn't exist
    out_filepath = Path(out_path)
    out_filepath.parent.mkdir(parents=True, exist_ok=True)

    # Create a copy and add DN column
    result_gdf = net_lines_gdf.copy()
    result_gdf["DN"] = None

    # Assign DN values
    missing_segments = []
    for seg_id, dn in assignment.items():
        mask = result_gdf["seg_id"] == seg_id
        if mask.any():
            result_gdf.loc[mask, "DN"] = dn
        else:
            missing_segments.append(seg_id)

    # Log warnings for missing segments
    if missing_segments:
        logger.warning(
            f"Assignment contains {len(missing_segments)} segments not found in GeoDataFrame: {missing_segments[:5]}{'...' if len(missing_segments) > 5 else ''}"
        )

    # Write GeoJSON
    result_gdf.to_file(out_path, driver="GeoJSON")

    logger.info(f"GeoJSON exported to: {out_path}")
    return str(Path(out_path).absolute())
