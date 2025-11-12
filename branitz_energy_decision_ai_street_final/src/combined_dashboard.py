#!/usr/bin/env python3
"""
Combined Dashboard Generator for Branitz Energy Decision AI
Creates a comprehensive dashboard with both system overview and detailed results.
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


def load_yaml_safe(path: Path) -> Optional[Dict[str, Any]]:
    """Safely load YAML file, return None if not found or invalid."""
    try:
        if path.exists():
            import yaml
            return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return None


def extract_combined_metrics(root: Path) -> Dict[str, Any]:
    """Extract comprehensive metrics for combined dashboard."""
    metrics = {}
    
    # LFA Metrics
    lfa_dir = root / "processed" / "lfa"
    if lfa_dir.exists():
        json_files = list(lfa_dir.glob("*.json"))
        total_heat_kwh = 0.0
        building_data = []
        
        for json_file in json_files:
            data = load_json_safe(json_file)
            if data and "series" in data:
                annual_kwh = sum(data["series"]) if isinstance(data["series"], list) else 0.0
                total_heat_kwh += annual_kwh
                building_data.append({
                    "building_id": json_file.stem,
                    "annual_heat_mwh": annual_kwh / 1000,
                    "peak_demand_kw": max(data["series"]) if data["series"] else 0
                })
        
        metrics["lfa"] = {
            "total_buildings": len(json_files),
            "total_annual_heat_mwh": total_heat_kwh / 1000,
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


def generate_combined_dashboard_html(metrics: Dict[str, Any], output_path: Path) -> str:
    """Generate comprehensive combined dashboard HTML."""
    
    # Extract data for easier access
    lfa_data = metrics.get("lfa", {})
    cha_data = metrics.get("cha", {})
    dha_data = metrics.get("dha", {})
    eaa_data = metrics.get("eaa", {})
    tca_data = metrics.get("tca", {})
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Branitz Energy Decision AI - Combined Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" />
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
        
        .nav-tabs {{
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 10px;
        }}
        
        .nav-tab {{
            padding: 15px 30px;
            margin: 0 5px;
            background: transparent;
            border: none;
            color: white;
            border-radius: 10px;
            cursor: pointer;
            font-size: 1.1rem;
            transition: all 0.3s ease;
        }}
        
        .nav-tab.active {{
            background: rgba(255,255,255,0.2);
            font-weight: bold;
        }}
        
        .nav-tab:hover {{
            background: rgba(255,255,255,0.15);
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
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
        
        .chart-container {{
            position: relative;
            height: 300px;
            margin-top: 20px;
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
        
        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        .results-table th,
        .results-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .results-table th {{
            background: #f7fafc;
            font-weight: bold;
            color: #4a5568;
        }}
        
        .results-table tr:hover {{
            background: #f7fafc;
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
            
            .nav-tabs {{
                flex-direction: column;
            }}
            
            .nav-tab {{
                margin: 2px 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ Branitz Energy Decision AI</h1>
            <p>Comprehensive System Dashboard & Analysis Results</p>
        </div>
        
        <div class="nav-tabs">
            <button class="nav-tab active" onclick="showTab('overview')">📊 System Overview</button>
            <button class="nav-tab" onclick="showTab('results')">📋 Detailed Results</button>
            <button class="nav-tab" onclick="showTab('charts')">📈 Analytics</button>
        </div>
        
        <!-- System Overview Tab -->
        <div id="overview" class="tab-content active">
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
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Detailed Results Tab -->
        <div id="results" class="tab-content">
            <div class="card full-width">
                <h2>📋 Detailed Results Summary</h2>
                <table class="results-table">
                    <thead>
                        <tr>
                            <th>Agent</th>
                            <th>Metric</th>
                            <th>Value</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td rowspan="2">LFA</td>
                            <td>Buildings Analyzed</td>
                            <td>{lfa_data.get('total_buildings', 0)}</td>
                            <td><span class="status-indicator status-good"></span>Active</td>
                        </tr>
                        <tr>
                            <td>Annual Heat Demand</td>
                            <td>{lfa_data.get('total_annual_heat_mwh', 0):.2f} MWh</td>
                            <td><span class="status-indicator status-good"></span>Complete</td>
                        </tr>
                        <tr>
                            <td rowspan="4">CHA</td>
                            <td>Total Network Length</td>
                            <td>{cha_data.get('total_length_km', 0):.2f} km</td>
                            <td><span class="status-indicator status-good"></span>Complete</td>
                        </tr>
                        <tr>
                            <td>Supply / Return Length</td>
                            <td>{cha_data.get('supply_length_km', 0):.2f} / {cha_data.get('return_length_km', 0):.2f} km</td>
                            <td><span class="status-indicator status-good"></span>Complete</td>
                        </tr>
                        <tr>
                            <td>Mean Velocity</td>
                            <td>{cha_data.get('mean_velocity_ms', 0):.3f} m/s</td>
                            <td><span class="status-indicator {'status-warning' if cha_data.get('mean_velocity_ms', 0) > 2.0 else 'status-good'}"></span>{'Warning' if cha_data.get('mean_velocity_ms', 0) > 2.0 else 'Good'}</td>
                        </tr>
                        <tr>
                            <td>Max Pressure Drop</td>
                            <td>{cha_data.get('max_pressure_drop_bar', 0):.3f} bar</td>
                            <td><span class="status-indicator {'status-warning' if cha_data.get('max_pressure_drop_bar', 0) > 0.5 else 'status-good'}"></span>{'Warning' if cha_data.get('max_pressure_drop_bar', 0) > 0.5 else 'Good'}</td>
                        </tr>
                        <tr>
                            <td>DHA</td>
                            <td>Max Feeder Utilization</td>
                            <td>{dha_data.get('max_utilization_pct', 0):.1f}%</td>
                            <td><span class="status-indicator {'status-warning' if dha_data.get('max_utilization_pct', 0) > 80 else 'status-good'}"></span>{'Warning' if dha_data.get('max_utilization_pct', 0) > 80 else 'Good'}</td>
                        </tr>
                        <tr>
                            <td rowspan="3">EAA</td>
                            <td>LCoH Mean</td>
                            <td>{eaa_data.get('lcoh_mean', 0):.1f} €/MWh</td>
                            <td><span class="status-indicator status-good"></span>Complete</td>
                        </tr>
                        <tr>
                            <td>LCoH 95% CI</td>
                            <td>[{eaa_data.get('lcoh_p2_5', 0):.1f} - {eaa_data.get('lcoh_p97_5', 0):.1f}] €/MWh</td>
                            <td><span class="status-indicator status-good"></span>Complete</td>
                        </tr>
                        <tr>
                            <td>CO₂ Emissions</td>
                            <td>{eaa_data.get('co2_mean', 0):.2f} kg/MWh</td>
                            <td><span class="status-indicator status-good"></span>Complete</td>
                        </tr>
                        <tr>
                            <td>TCA</td>
                            <td>Recommended Scenario</td>
                            <td>{tca_data.get('decision', 'Unknown')}</td>
                            <td><span class="status-indicator status-good"></span>Decision Made</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Analytics Tab -->
        <div id="charts" class="tab-content">
            <div class="dashboard-grid">
                <div class="card">
                    <h2>📊 Building Heat Demand</h2>
                    <div class="chart-container">
                        <canvas id="lfaChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🌡️ Network Length Distribution</h2>
                    <div class="chart-container">
                        <canvas id="chaChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h2>⚡ Feeder Utilization</h2>
                    <div class="chart-container">
                        <canvas id="dhaChart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h2>💰 LCoH Distribution</h2>
                    <div class="chart-container">
                        <canvas id="eaaChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="timestamp">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
        </div>
    </div>

    <script>
        function showTab(tabName) {{
            // Hide all tab contents
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(tab => tab.classList.remove('active'));
            
            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.nav-tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }}
        
        // LFA Chart - Building Heat Demand
        const lfaCtx = document.getElementById('lfaChart').getContext('2d');
        const lfaData = {json.dumps([b['annual_heat_mwh'] for b in lfa_data.get('building_data', [])])};
        const lfaLabels = {json.dumps([b['building_id'] for b in lfa_data.get('building_data', [])])};
        
        new Chart(lfaCtx, {{
            type: 'bar',
            data: {{
                labels: lfaLabels,
                datasets: [{{
                    label: 'Annual Heat Demand (MWh)',
                    data: lfaData,
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Heat Demand (MWh)'
                        }}
                    }}
                }}
            }}
        }});
        
        // CHA Chart - Pipe Length Distribution
        const chaCtx = document.getElementById('chaChart').getContext('2d');
        new Chart(chaCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['Supply Pipes', 'Return Pipes'],
                datasets: [{{
                    data: [{cha_data.get('supply_length_km', 0):.2f}, {cha_data.get('return_length_km', 0):.2f}],
                    backgroundColor: ['rgba(255, 99, 132, 0.8)', 'rgba(54, 162, 235, 0.8)'],
                    borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)'],
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }}
                }}
            }}
        }});
        
        // DHA Chart - Feeder Utilization
        const dhaCtx = document.getElementById('dhaChart').getContext('2d');
        const dhaData = {json.dumps([f['utilization_pct'] for f in dha_data.get('feeder_data', [])])};
        const dhaLabels = {json.dumps([f.get('feeder', f'Feeder {i}') for i, f in enumerate(dha_data.get('feeder_data', []))])};
        
        new Chart(dhaCtx, {{
            type: 'line',
            data: {{
                labels: dhaLabels,
                datasets: [{{
                    label: 'Feeder Utilization (%)',
                    data: dhaData,
                    borderColor: 'rgba(255, 159, 64, 1)',
                    backgroundColor: 'rgba(255, 159, 64, 0.2)',
                    tension: 0.4,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Utilization (%)'
                        }}
                    }}
                }}
            }}
        }});
        
        // EAA Chart - LCoH Distribution
        const eaaCtx = document.getElementById('eaaChart').getContext('2d');
        new Chart(eaaCtx, {{
            type: 'bar',
            data: {{
                labels: ['Mean', 'Median', '2.5%', '97.5%'],
                datasets: [{{
                    label: 'LCoH (€/MWh)',
                    data: [
                        {eaa_data.get('lcoh_mean', 0):.1f},
                        {eaa_data.get('lcoh_median', 0):.1f},
                        {eaa_data.get('lcoh_p2_5', 0):.1f},
                        {eaa_data.get('lcoh_p97_5', 0):.1f}
                    ],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.8)',
                        'rgba(54, 162, 235, 0.8)',
                        'rgba(255, 206, 86, 0.8)',
                        'rgba(255, 99, 132, 0.8)'
                    ],
                    borderColor: [
                        'rgba(75, 192, 192, 1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(255, 99, 132, 1)'
                    ],
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'LCoH (€/MWh)'
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html_content


def main():
    parser = argparse.ArgumentParser(description="Generate combined dashboard for Branitz Energy Decision AI")
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--output", default="docs/combined_dashboard.html", help="Output HTML file path")
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("🔍 Extracting combined system metrics...")
    metrics = extract_combined_metrics(root_path)
    
    print("🎨 Generating combined dashboard HTML...")
    html_content = generate_combined_dashboard_html(metrics, output_path)
    
    print("💾 Writing dashboard to file...")
    output_path.write_text(html_content, encoding="utf-8")
    
    print(f"✅ Combined dashboard generated successfully!")
    print(f"📄 Output file: {output_path}")
    print(f"🌐 Open in browser: file://{output_path.absolute()}")


if __name__ == "__main__":
    main()
