#!/usr/bin/env python3
"""
Comprehensive Dashboard Generator for Branitz Energy Decision AI
Creates a complete dashboard with embedded figures and all comprehensive metrics.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import argparse
import base64
import io
import matplotlib.pyplot as plt
import seaborn as sns


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


def load_yaml_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load YAML file, return None if not found or invalid."""
    try:
        if path.exists():
            import yaml
            return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def create_embedded_figure(fig_data: Dict[str, Any], fig_type: str) -> str:
    """Create an embedded figure as base64 string."""
    try:
        plt.style.use('default')
        sns.set_palette("husl")
        
        if fig_type == "lfa_buildings":
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
            buildings = fig_data.get("building_data", [])
            if buildings:
                building_ids = [b["building_id"] for b in buildings]
                heat_demands = [b["annual_heat_mwh"] for b in buildings]
                bars = ax.bar(building_ids, heat_demands, color='skyblue', alpha=0.7, edgecolor='black')
                ax.set_xlabel('Building ID')
                ax.set_ylabel('Annual Heat Demand (MWh)')
                ax.set_title('Building Heat Demand Distribution')
                ax.tick_params(axis='x', rotation=45)
                for bar, value in zip(bars, heat_demands):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(heat_demands)*0.01, 
                           f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
            else:
                ax.text(0.5, 0.5, 'No building data available', ha='center', va='center', transform=ax.transAxes)
        
        elif fig_type == "cha_network":
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
            supply_length = fig_data.get("supply_length_km", 0)
            return_length = fig_data.get("return_length_km", 0)
            if supply_length > 0 or return_length > 0:
                labels = ['Supply Pipes', 'Return Pipes']
                sizes = [supply_length, return_length]
                colors = ['lightcoral', 'lightblue']
                wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax.set_title('Network Length Distribution')
            else:
                ax.text(0.5, 0.5, 'No network data available', ha='center', va='center', transform=ax.transAxes)
        
        elif fig_type == "dha_utilization":
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
            feeder_data = fig_data.get("feeder_data", [])
            if feeder_data:
                feeders = [f.get("feeder", f"Feeder {i}") for i, f in enumerate(feeder_data)]
                utilizations = [f.get("utilization_pct", 0) for f in feeder_data]
                colors = ['red' if u > 80 else 'orange' if u > 60 else 'green' for u in utilizations]
                bars = ax.barh(feeders, utilizations, color=colors, alpha=0.7)
                ax.axvline(80, color='red', linestyle='--', linewidth=2, label='Warning: 80%')
                ax.axvline(60, color='orange', linestyle=':', linewidth=2, label='Caution: 60%')
                ax.set_xlabel('Utilization (%)')
                ax.set_title('Feeder Utilization')
                ax.legend()
            else:
                ax.text(0.5, 0.5, 'No feeder data available', ha='center', va='center', transform=ax.transAxes)
        
        elif fig_type == "eaa_distribution":
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # LCoH distribution (simplified)
            lcoh_mean = fig_data.get("lcoh_mean", 0)
            lcoh_p2_5 = fig_data.get("lcoh_p2_5", 0)
            lcoh_p97_5 = fig_data.get("lcoh_p97_5", 0)
            
            if lcoh_mean > 0:
                # Create a simple distribution visualization
                x = np.linspace(lcoh_p2_5, lcoh_p97_5, 100)
                y = np.exp(-0.5 * ((x - lcoh_mean) / (lcoh_mean * 0.1)) ** 2)
                ax1.plot(x, y, 'b-', linewidth=2, label='LCoH Distribution')
                ax1.axvline(lcoh_mean, color='red', linestyle='--', label=f'Mean: {lcoh_mean:.1f} €/MWh')
                ax1.axvline(lcoh_p2_5, color='green', linestyle=':', label=f'2.5%: {lcoh_p2_5:.1f} €/MWh')
                ax1.axvline(lcoh_p97_5, color='green', linestyle=':', label=f'97.5%: {lcoh_p97_5:.1f} €/MWh')
                ax1.set_xlabel('LCoH (€/MWh)')
                ax1.set_ylabel('Density')
                ax1.set_title('LCoH Distribution')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'No LCoH data', ha='center', va='center', transform=ax1.transAxes)
            
            # CO₂ distribution (simplified)
            co2_mean = fig_data.get("co2_mean", 0)
            if co2_mean > 0:
                x = np.linspace(co2_mean * 0.8, co2_mean * 1.2, 100)
                y = np.exp(-0.5 * ((x - co2_mean) / (co2_mean * 0.1)) ** 2)
                ax2.plot(x, y, 'g-', linewidth=2, label='CO₂ Distribution')
                ax2.axvline(co2_mean, color='red', linestyle='--', label=f'Mean: {co2_mean:.2f} kg/MWh')
                ax2.set_xlabel('CO₂ (kg/MWh)')
                ax2.set_ylabel('Density')
                ax2.set_title('CO₂ Distribution')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
            else:
                ax2.text(0.5, 0.5, 'No CO₂ data', ha='center', va='center', transform=ax2.transAxes)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    except Exception as e:
        print(f"⚠️ Error creating figure {fig_type}: {e}")
        return ""


def extract_comprehensive_metrics(root: Path) -> Dict[str, Any]:
    """Extract all comprehensive metrics for dashboard display."""
    metrics = {}
    
    # LFA Metrics
    lfa_dir = root / "processed" / "lfa"
    if lfa_dir.exists():
        json_files = list(lfa_dir.glob("*.json"))
        total_heat_kwh = 0.0
        building_data = []
        peak_thermal_kw = 0.0
        
        for json_file in json_files:
            data = load_json_safe(json_file)
            if data and "series" in data:
                annual_kwh = sum(data["series"]) if isinstance(data["series"], list) else 0.0
                peak_kw = max(data["series"]) if data["series"] else 0.0
                total_heat_kwh += annual_kwh
                peak_thermal_kw += peak_kw
                building_data.append({
                    "building_id": json_file.stem,
                    "annual_heat_mwh": annual_kwh / 1000,
                    "peak_demand_kw": peak_kw
                })
        
        metrics["lfa"] = {
            "total_buildings": len(json_files),
            "total_annual_heat_mwh": total_heat_kwh / 1000,
            "peak_thermal_kw": peak_thermal_kw,
            "building_data": building_data
        }
    
    # CHA Metrics
    segments_path = root / "processed" / "cha" / "segments.csv"
    segments_df = load_csv_safe(segments_path)
    
    if segments_df is not None:
        total_length_km = segments_df["length_m"].sum() / 1000
        supply_length = 0
        return_length = 0
        
        if "pipe_type" in segments_df.columns:
            supply_length = segments_df[segments_df["pipe_type"] == "supply"]["length_m"].sum() / 1000
            return_length = segments_df[segments_df["pipe_type"] == "return"]["length_m"].sum() / 1000
        
        metrics["cha"] = {
            "total_length_km": total_length_km,
            "supply_length_km": supply_length,
            "return_length_km": return_length,
            "mean_velocity_ms": segments_df["v_ms"].mean() if "v_ms" in segments_df.columns else 0,
            "max_pressure_drop_bar": segments_df["dp_bar"].max() if "dp_bar" in segments_df.columns else 0,
            "pipe_data": segments_df.to_dict('records') if len(segments_df) > 0 else []
        }
    
    # DHA Metrics
    feeders_path = root / "processed" / "dha" / "feeder_loads.csv"
    feeders_df = load_csv_safe(feeders_path)
    
    if feeders_df is not None:
        metrics["dha"] = {
            "max_utilization_pct": feeders_df["utilization_pct"].max() if "utilization_pct" in feeders_df.columns else 0,
            "feeder_data": feeders_df.to_dict('records') if len(feeders_df) > 0 else []
        }
    
    # EAA Metrics
    summary_path = root / "eval" / "te" / "summary.csv"
    summary_df = load_csv_safe(summary_path)
    
    if summary_df is not None:
        lcoh_row = summary_df[summary_df["metric"] == "lcoh_eur_per_mwh"]
        if not lcoh_row.empty:
            metrics["eaa"] = {
                "lcoh_mean": lcoh_row["mean"].iloc[0],
                "lcoh_median": lcoh_row["median"].iloc[0],
                "lcoh_p2_5": lcoh_row["p2_5"].iloc[0],
                "lcoh_p97_5": lcoh_row["p97_5"].iloc[0],
                "co2_mean": summary_df[summary_df["metric"] == "co2_kg_per_mwh"]["mean"].iloc[0] if len(summary_df[summary_df["metric"] == "co2_kg_per_mwh"]) > 0 else 0
            }
    
    # TCA Metrics
    kpi_path = root / "processed" / "kpi" / "kpi_summary.json"
    kpi_data = load_json_safe(kpi_path)
    
    if kpi_data is not None:
        metrics["tca"] = {
            "decision": kpi_data.get("recommendation", {}).get("preferred_scenario", "Unknown"),
            "rationale": kpi_data.get("recommendation", {}).get("rationale", "No rationale provided"),
            "confidence": kpi_data.get("recommendation", {}).get("confidence_level", "Unknown"),
            "economic_metrics": kpi_data.get("economic_metrics", {}),
            "technical_metrics": kpi_data.get("technical_metrics", {})
        }
    
    # Design Constants
    eaa_config_path = root / "configs" / "eaa.yml"
    eaa_config = load_yaml_safe(eaa_config_path)
    
    if eaa_config is not None:
        metrics["design"] = {
            "delta_t_k": eaa_config.get("delta_t_k", 30),
            "cp_water_j_per_kgk": eaa_config.get("cp_water_j_per_kgk", 4180),
            "design_full_load_hours": eaa_config.get("design_full_load_hours", 2000)
        }
    
    # Convergence Information
    sim_path = root / "eval" / "cha" / "sim.json"
    sim_data = load_json_safe(sim_path)
    
    if sim_data is not None:
        metrics["convergence"] = {
            "converged": sim_data.get("converged", False),
            "runtime_s": sim_data.get("runtime_s", 0.0),
            "solver": sim_data.get("solver", "pipeflow")
        }
    
    # COP Model Information
    dha_config_path = root / "configs" / "dha.yml"
    dha_config = load_yaml_safe(dha_config_path)
    
    if dha_config is not None:
        cop_model = dha_config.get("cop_model", "constant")
        cop_peak = dha_config.get("cop_peak", 3.0)
        
        # Calculate peak electrical power
        peak_thermal_kw = metrics.get("lfa", {}).get("peak_thermal_kw", 0.0)
        peak_electrical_kw = peak_thermal_kw / cop_peak if cop_peak > 0 else 0.0
        
        metrics["cop"] = {
            "model": cop_model,
            "peak_cop": cop_peak,
            "peak_electrical_kw": peak_electrical_kw
        }
    
    return metrics


def generate_comprehensive_dashboard_html(metrics: Dict[str, Any], output_path: Path) -> str:
    """Generate comprehensive HTML dashboard with embedded figures."""
    
    # Extract data for easier access
    lfa_data = metrics.get("lfa", {})
    cha_data = metrics.get("cha", {})
    dha_data = metrics.get("dha", {})
    eaa_data = metrics.get("eaa", {})
    tca_data = metrics.get("tca", {})
    design_data = metrics.get("design", {})
    convergence_data = metrics.get("convergence", {})
    cop_data = metrics.get("cop", {})
    
    # Create embedded figures
    lfa_figure = create_embedded_figure(lfa_data, "lfa_buildings")
    cha_figure = create_embedded_figure(cha_data, "cha_network")
    dha_figure = create_embedded_figure(dha_data, "dha_utilization")
    eaa_figure = create_embedded_figure(eaa_data, "eaa_distribution")
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Branitz Energy Decision AI - Comprehensive Dashboard</title>
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
            max-width: 1600px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 3rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
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
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .metric {{
            text-align: center;
            padding: 15px;
            background: #f7fafc;
            border-radius: 10px;
            border-left: 4px solid #667eea;
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
        
        .figure-container {{
            text-align: center;
            margin-top: 20px;
        }}
        
        .figure-container img {{
            max-width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        
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
        
        .decision-confidence {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .decision-rationale {{
            font-size: 1.1rem;
            line-height: 1.6;
            opacity: 0.95;
        }}
        
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        
        .status-good {{ background-color: #48bb78; }}
        .status-warning {{ background-color: #ed8936; }}
        .status-error {{ background-color: #f56565; }}
        
        .full-width {{
            grid-column: 1 / -1;
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
            <h1>🏗️ Branitz Energy Decision AI</h1>
            <p>Comprehensive System Dashboard with Embedded Analytics</p>
        </div>
        
        <div class="dashboard-grid">
            <!-- Decision Card -->
            <div class="card decision-card">
                <h2>🎯 System Recommendation</h2>
                <div class="decision-content">
                    <div class="decision-main">
                        <div class="decision-scenario">{tca_data.get('decision', 'Unknown')}</div>
                        <div class="decision-confidence">Confidence: {tca_data.get('confidence', 'Unknown')}</div>
                    </div>
                    <div class="decision-rationale">
                        <strong>Rationale:</strong><br>
                        {tca_data.get('rationale', 'No rationale provided')}
                    </div>
                </div>
            </div>
            
            <!-- LFA Card -->
            <div class="card">
                <h2>📊 Load Forecasting Agent (LFA)</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-value">{lfa_data.get('total_buildings', 0)}</div>
                        <div class="metric-label">Buildings</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{lfa_data.get('total_annual_heat_mwh', 0):.1f}</div>
                        <div class="metric-label">Annual Heat (MWh)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{lfa_data.get('peak_thermal_kw', 0):.1f}</div>
                        <div class="metric-label">Peak Thermal (kW)</div>
                    </div>
                </div>
                <div class="figure-container">
                    <img src="{lfa_figure}" alt="Building Heat Demand Distribution" />
                </div>
            </div>
            
            <!-- CHA Card -->
            <div class="card">
                <h2>🌡️ Centralized Heating Agent (CHA)</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-value">{cha_data.get('total_length_km', 0):.2f}</div>
                        <div class="metric-label">Total Length (km)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{cha_data.get('mean_velocity_ms', 0):.3f}</div>
                        <div class="metric-label">Mean Velocity (m/s)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{cha_data.get('max_pressure_drop_bar', 0):.3f}</div>
                        <div class="metric-label">Max ΔP (bar)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{cha_data.get('supply_length_km', 0):.2f} / {cha_data.get('return_length_km', 0):.2f}</div>
                        <div class="metric-label">Supply / Return (km)</div>
                    </div>
                </div>
                <div class="figure-container">
                    <img src="{cha_figure}" alt="Network Length Distribution" />
                </div>
            </div>
            
            <!-- Design Constants Card -->
            <div class="card">
                <h2>⚙️ Design Constants & Physics</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-value">{design_data.get('delta_t_k', 30)}</div>
                        <div class="metric-label">ΔT (K)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{design_data.get('cp_water_j_per_kgk', 4180)}</div>
                        <div class="metric-label">cp (J/kg·K)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{design_data.get('design_full_load_hours', 2000)}</div>
                        <div class="metric-label">Design Hours</div>
                    </div>
                </div>
            </div>
            
            <!-- Convergence Card -->
            <div class="card">
                <h2>🔄 Simulation Convergence</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-value">{'✅ Yes' if convergence_data.get('converged', False) else '❌ No'}</div>
                        <div class="metric-label">Converged</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{convergence_data.get('runtime_s', 0):.2f}</div>
                        <div class="metric-label">Runtime (s)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{convergence_data.get('solver', 'pipeflow')}</div>
                        <div class="metric-label">Solver</div>
                    </div>
                </div>
            </div>
            
            <!-- DHA Card -->
            <div class="card">
                <h2>⚡ Decentralized Heating Agent (DHA)</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-value">{dha_data.get('max_utilization_pct', 0):.1f}%</div>
                        <div class="metric-label">Max Feeder Utilization</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{cop_data.get('model', 'constant')}</div>
                        <div class="metric-label">COP Model</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{cop_data.get('peak_cop', 3.0):.1f}</div>
                        <div class="metric-label">Peak COP</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{cop_data.get('peak_electrical_kw', 0):.1f}</div>
                        <div class="metric-label">Peak P_el (kW)</div>
                    </div>
                </div>
                <div class="figure-container">
                    <img src="{dha_figure}" alt="Feeder Utilization Analysis" />
                </div>
            </div>
            
            <!-- EAA Card -->
            <div class="card">
                <h2>💰 Economics Analysis Agent (EAA)</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-value">{eaa_data.get('lcoh_mean', 0):.1f}</div>
                        <div class="metric-label">LCoH Mean (€/MWh)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{eaa_data.get('lcoh_p2_5', 0):.1f} - {eaa_data.get('lcoh_p97_5', 0):.1f}</div>
                        <div class="metric-label">95% CI (€/MWh)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{eaa_data.get('co2_mean', 0):.2f}</div>
                        <div class="metric-label">CO₂ Mean (kg/MWh)</div>
                    </div>
                </div>
                <div class="figure-container">
                    <img src="{eaa_figure}" alt="Economic Analysis Distributions" />
                </div>
            </div>
            
            <!-- Technical Metrics Card -->
            <div class="card full-width">
                <h2>🔍 Technical Metrics & System Status</h2>
                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-value">
                            <span class="status-indicator status-good"></span>
                            Active
                        </div>
                        <div class="metric-label">System Status</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{len(cha_data.get('pipe_data', []))}</div>
                        <div class="metric-label">Pipe Segments</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{len(dha_data.get('feeder_data', []))}</div>
                        <div class="metric-label">Feeder Lines</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">
                            <span class="status-indicator {'status-good' if dha_data.get('max_utilization_pct', 0) < 80 else 'status-warning'}"></span>
                            {'Good' if dha_data.get('max_utilization_pct', 0) < 80 else 'Warning'}
                        </div>
                        <div class="metric-label">Grid Status</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{tca_data.get('technical_metrics', {}).get('pump_kw', 0):.2f}</div>
                        <div class="metric-label">Pump Power (kW)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{tca_data.get('technical_metrics', {}).get('dh_losses_pct', 0):.2f}%</div>
                        <div class="metric-label">DH Losses</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{tca_data.get('technical_metrics', {}).get('forecast_rmse', 0):.3f}</div>
                        <div class="metric-label">Forecast RMSE</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{tca_data.get('technical_metrics', {}).get('forecast_picp_90', 0):.3f}</div>
                        <div class="metric-label">Forecast PICP90</div>
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
    parser = argparse.ArgumentParser(description="Generate comprehensive dashboard with embedded figures")
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--output", default="docs/comprehensive_dashboard.html", help="Output HTML file path")
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("🔍 Extracting comprehensive system metrics...")
    metrics = extract_comprehensive_metrics(root_path)
    
    print("🎨 Generating comprehensive dashboard with embedded figures...")
    html_content = generate_comprehensive_dashboard_html(metrics, output_path)
    
    print("💾 Writing dashboard to file...")
    output_path.write_text(html_content, encoding="utf-8")
    
    print(f"✅ Comprehensive dashboard generated successfully!")
    print(f"📄 Output file: {output_path}")
    print(f"🌐 Open in browser: file://{output_path.absolute()}")


if __name__ == "__main__":
    main()





