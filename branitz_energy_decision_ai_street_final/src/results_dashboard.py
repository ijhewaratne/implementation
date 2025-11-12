#!/usr/bin/env python3
"""
Results Dashboard Generator for Branitz Energy Decision AI
Creates a focused dashboard specifically for displaying extracted results.
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import argparse


def load_json_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load JSON file, return None if not found or invalid."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def load_csv_safe(path: Path) -> Optional[pd.DataFrame]:
    """Safely load CSV file, return None if not found or invalid."""
    try:
        if path.exists():
            return pd.read_csv(path)
    except Exception:
        pass
    return None


def extract_results_metrics(slug: str, root: Path) -> Dict[str, str]:
    """Extract results metrics using the same logic as the results extractor."""
    metrics = {}
    
    # LFA Metrics
    lfa_dir = root / "processed" / "lfa" / slug if slug else root / "processed" / "lfa"
    if lfa_dir.exists():
        json_files = list(lfa_dir.glob("*.json"))
        total_heat_kwh = 0.0
        for json_file in json_files:
            data = load_json_safe(json_file)
            if data and "series" in data:
                annual_kwh = sum(data["series"]) if isinstance(data["series"], list) else 0.0
                total_heat_kwh += annual_kwh
        
        metrics["lfa_buildings"] = str(len(json_files))
        metrics["lfa_annual_heat"] = f"{total_heat_kwh / 1000:.2f} MWh" if total_heat_kwh > 0 else "NA"
    else:
        metrics["lfa_buildings"] = "NA"
        metrics["lfa_annual_heat"] = "NA"
    
    # CHA Metrics
    if slug:
        segments_path = root / "processed" / "cha" / slug / "segments.csv"
    else:
        segments_path = root / "processed" / "cha" / "segments.csv"
    segments_df = load_csv_safe(segments_path)
    
    if segments_df is not None:
        total_length_km = segments_df["length_m"].sum() / 1000 if "length_m" in segments_df.columns else 0
        metrics["cha_total_length"] = f"{total_length_km:.2f} km"
        
        if "pipe_type" in segments_df.columns:
            supply_length = segments_df[segments_df["pipe_type"] == "supply"]["length_m"].sum() / 1000
            return_length = segments_df[segments_df["pipe_type"] == "return"]["length_m"].sum() / 1000
            metrics["cha_supply_return"] = f"{supply_length:.2f} km / {return_length:.2f} km"
        else:
            metrics["cha_supply_return"] = "NA"
        
        metrics["cha_mean_velocity"] = f"{segments_df['v_ms'].mean():.3f} m/s" if "v_ms" in segments_df.columns else "NA"
        metrics["cha_max_dp"] = f"{segments_df['dp_bar'].max():.3f} bar" if "dp_bar" in segments_df.columns else "NA"
    else:
        metrics.update({
            "cha_total_length": "NA",
            "cha_supply_return": "NA",
            "cha_mean_velocity": "NA",
            "cha_max_dp": "NA"
        })
    
    # DHA Metrics
    if slug:
        feeders_path = root / "processed" / "dha" / slug / "feeder_loads.csv"
    else:
        feeders_path = root / "processed" / "dha" / "feeder_loads.csv"
    feeders_df = load_csv_safe(feeders_path)
    
    if feeders_df is not None and "utilization_pct" in feeders_df.columns:
        max_utilization = feeders_df["utilization_pct"].max()
        metrics["dha_max_utilization"] = f"{max_utilization:.1f} %"
    else:
        metrics["dha_max_utilization"] = "NA"
    
    # EAA Metrics
    if slug:
        summary_path = root / "eval" / "te" / slug / "summary.csv"
    else:
        summary_path = root / "eval" / "te" / "summary.csv"
    summary_df = load_csv_safe(summary_path)
    
    if summary_df is not None:
        lcoh_row = summary_df[summary_df["metric"] == "lcoh_eur_per_mwh"]
        if not lcoh_row.empty:
            mean_lcoh = lcoh_row["mean"].iloc[0]
            p2_5 = lcoh_row["p2_5"].iloc[0]
            p97_5 = lcoh_row["p97_5"].iloc[0]
            metrics["lcoh_ci"] = f"{mean_lcoh:.1f} [{p2_5:.1f}–{p97_5:.1f}] €/MWh"
        else:
            metrics["lcoh_ci"] = "NA"
    else:
        metrics["lcoh_ci"] = "NA"
    
    # TCA Metrics
    if slug:
        kpi_path = root / "processed" / "kpi" / slug / "kpi_summary.json"
    else:
        kpi_path = root / "processed" / "kpi" / "kpi_summary.json"
    kpi_data = load_json_safe(kpi_path)
    
    if kpi_data is not None:
        recommendation = kpi_data.get("recommendation", {})
        metrics["kpi_decision"] = recommendation.get("preferred_scenario", "NA")
        metrics["kpi_rationale"] = recommendation.get("rationale", "NA")
    else:
        metrics["kpi_decision"] = "NA"
        metrics["kpi_rationale"] = "NA"
    
    return metrics


def generate_results_dashboard_html(slug: str, metrics: Dict[str, str], output_path: Path) -> str:
    """Generate focused results dashboard HTML."""
    
    # Determine status indicators
    def get_status_indicator(value, threshold=None, reverse=False):
        if value == "NA":
            return "status-unknown"
        try:
            if threshold is not None:
                numeric_value = float(value.split()[0])  # Extract numeric part
                if reverse:
                    return "status-good" if numeric_value <= threshold else "status-warning"
                else:
                    return "status-good" if numeric_value <= threshold else "status-warning"
        except:
            pass
        return "status-good"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Branitz Energy Decision AI - Results Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.15);
        }}
        
        .card h2 {{
            color: #4a5568;
            margin-bottom: 20px;
            font-size: 1.4rem;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .metric-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        
        .metric {{
            text-align: center;
            padding: 20px;
            background: #f7fafc;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            position: relative;
        }}
        
        .metric-value {{
            font-size: 1.8rem;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 5px;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-indicator {{
            position: absolute;
            top: 10px;
            right: 10px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
        
        .status-good {{ background-color: #48bb78; }}
        .status-warning {{ background-color: #ed8936; }}
        .status-error {{ background-color: #f56565; }}
        .status-unknown {{ background-color: #a0aec0; }}
        
        .decision-card {{
            grid-column: 1 / -1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .decision-card h2 {{
            color: white;
            border-bottom-color: rgba(255,255,255,0.3);
        }}
        
        .decision-content {{
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            align-items: center;
        }}
        
        .decision-main {{
            text-align: center;
        }}
        
        .decision-scenario {{
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .decision-rationale {{
            font-size: 1.1rem;
            line-height: 1.6;
            opacity: 0.95;
        }}
        
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        
        .summary-stat {{
            text-align: center;
            padding: 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }}
        
        .summary-stat-value {{
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .summary-stat-label {{
            font-size: 0.9rem;
            opacity: 0.8;
        }}
        
        .timestamp {{
            text-align: center;
            color: rgba(255,255,255,0.7);
            margin-top: 30px;
            font-size: 0.9rem;
        }}
        
        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
            }}
            
            .decision-content {{
                grid-template-columns: 1fr;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Branitz Energy Decision AI</h1>
            <p>Results Dashboard - {slug if slug else 'System Overview'}</p>
        </div>
        
        <div class="dashboard-grid">
            <!-- Decision Card -->
            <div class="card decision-card">
                <h2>🎯 System Recommendation</h2>
                <div class="decision-content">
                    <div class="decision-main">
                        <div class="decision-scenario">{metrics.get('kpi_decision', 'Unknown')}</div>
                        <div class="summary-stats">
                            <div class="summary-stat">
                                <div class="summary-stat-value">{metrics.get('lfa_buildings', '0')}</div>
                                <div class="summary-stat-label">Buildings</div>
                            </div>
                            <div class="summary-stat">
                                <div class="summary-stat-value">{metrics.get('cha_total_length', '0 km').split()[0]}</div>
                                <div class="summary-stat-label">Network (km)</div>
                            </div>
                            <div class="summary-stat">
                                <div class="summary-stat-value">{metrics.get('dha_max_utilization', '0%').split()[0]}</div>
                                <div class="summary-stat-label">Max Utilization</div>
                            </div>
                        </div>
                    </div>
                    <div class="decision-rationale">
                        <strong>Rationale:</strong><br>
                        {metrics.get('kpi_rationale', 'No rationale provided')}
                    </div>
                </div>
            </div>
            
            <!-- LFA Card -->
            <div class="card">
                <h2>📊 Load Forecasting Agent (LFA)</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <span class="status-indicator {get_status_indicator(metrics.get('lfa_buildings', '0'))}"></span>
                        <div class="metric-value">{metrics.get('lfa_buildings', 'NA')}</div>
                        <div class="metric-label">Buildings Analyzed</div>
                    </div>
                    <div class="metric">
                        <span class="status-indicator {get_status_indicator(metrics.get('lfa_annual_heat', '0 MWh'))}"></span>
                        <div class="metric-value">{metrics.get('lfa_annual_heat', 'NA')}</div>
                        <div class="metric-label">Annual Heat Demand</div>
                    </div>
                </div>
            </div>
            
            <!-- CHA Card -->
            <div class="card">
                <h2>🌡️ Centralized Heating Agent (CHA)</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <span class="status-indicator {get_status_indicator(metrics.get('cha_total_length', '0 km'))}"></span>
                        <div class="metric-value">{metrics.get('cha_total_length', 'NA')}</div>
                        <div class="metric-label">Total Network Length</div>
                    </div>
                    <div class="metric">
                        <span class="status-indicator {get_status_indicator(metrics.get('cha_supply_return', '0 km / 0 km'))}"></span>
                        <div class="metric-value">{metrics.get('cha_supply_return', 'NA')}</div>
                        <div class="metric-label">Supply / Return</div>
                    </div>
                    <div class="metric">
                        <span class="status-indicator {get_status_indicator(metrics.get('cha_mean_velocity', '0 m/s'), 2.0)}"></span>
                        <div class="metric-value">{metrics.get('cha_mean_velocity', 'NA')}</div>
                        <div class="metric-label">Mean Velocity</div>
                    </div>
                    <div class="metric">
                        <span class="status-indicator {get_status_indicator(metrics.get('cha_max_dp', '0 bar'), 0.5)}"></span>
                        <div class="metric-value">{metrics.get('cha_max_dp', 'NA')}</div>
                        <div class="metric-label">Max Pressure Drop</div>
                    </div>
                </div>
            </div>
            
            <!-- DHA Card -->
            <div class="card">
                <h2>⚡ Decentralized Heating Agent (DHA)</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <span class="status-indicator {get_status_indicator(metrics.get('dha_max_utilization', '0%'), 80)}"></span>
                        <div class="metric-value">{metrics.get('dha_max_utilization', 'NA')}</div>
                        <div class="metric-label">Max Feeder Utilization</div>
                    </div>
                </div>
            </div>
            
            <!-- EAA Card -->
            <div class="card">
                <h2>💰 Economics Analysis Agent (EAA)</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <span class="status-indicator {get_status_indicator(metrics.get('lcoh_ci', '0 €/MWh'))}"></span>
                        <div class="metric-value">{metrics.get('lcoh_ci', 'NA')}</div>
                        <div class="metric-label">LCoH (95% CI)</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="timestamp">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
    </div>
</body>
</html>
"""
    
    return html_content


def main():
    parser = argparse.ArgumentParser(description="Generate results dashboard for Branitz Energy Decision AI")
    parser.add_argument("--slug", default="", help="Street slug (empty for system overview)")
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--output", default="docs/results_dashboard.html", help="Output HTML file path")
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Extracting results metrics for '{args.slug if args.slug else 'system overview'}'...")
    metrics = extract_results_metrics(args.slug, root_path)
    
    print("🎨 Generating results dashboard HTML...")
    html_content = generate_results_dashboard_html(args.slug, metrics, output_path)
    
    print("💾 Writing dashboard to file...")
    output_path.write_text(html_content, encoding="utf-8")
    
    print(f"✅ Results dashboard generated successfully!")
    print(f"📄 Output file: {output_path}")
    print(f"🌐 Open in browser: file://{output_path.absolute()}")


if __name__ == "__main__":
    main()





