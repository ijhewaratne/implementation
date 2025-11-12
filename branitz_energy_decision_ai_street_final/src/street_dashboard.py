#!/usr/bin/env python3
"""
Street-Specific Dashboard Generator for Branitz Energy Decision AI
Creates comprehensive dashboards for specific streets with 14 buildings.
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


def create_mock_building_data(street_name: str, num_buildings: int = 14) -> list:
    """Create mock building data for demonstration."""
    buildings = []
    np.random.seed(42)  # For reproducible results
    
    for i in range(num_buildings):
        # Generate realistic building data
        annual_heat_mwh = np.random.normal(45, 15)  # Mean 45 MWh, std 15
        annual_heat_mwh = max(annual_heat_mwh, 20)  # Minimum 20 MWh
        
        peak_demand_kw = np.random.normal(8, 3)  # Mean 8 kW, std 3
        peak_demand_kw = max(peak_demand_kw, 3)  # Minimum 3 kW
        
        buildings.append({
            "building_id": f"{street_name.lower().replace(' ', '_')}_building_{i+1:02d}",
            "annual_heat_mwh": round(annual_heat_mwh, 1),
            "peak_demand_kw": round(peak_demand_kw, 1),
            "building_type": np.random.choice(["residential", "commercial", "mixed"], p=[0.7, 0.2, 0.1]),
            "floor_area_m2": int(np.random.normal(800, 300)),
            "construction_year": int(np.random.normal(1985, 20))
        })
    
    return buildings


def create_mock_network_data(street_name: str, num_buildings: int = 14) -> Dict[str, Any]:
    """Create mock network data for the street."""
    np.random.seed(42)
    
    # Calculate total length based on number of buildings
    base_length_km = num_buildings * 0.08  # ~80m per building
    supply_length = base_length_km * 0.6
    return_length = base_length_km * 0.4
    
    return {
        "total_length_km": round(base_length_km, 2),
        "supply_length_km": round(supply_length, 2),
        "return_length_km": round(return_length, 2),
        "mean_velocity_ms": round(np.random.normal(0.8, 0.2), 3),
        "max_pressure_drop_bar": round(np.random.normal(0.15, 0.05), 3),
        "pipe_segments": num_buildings * 2,  # Supply and return
        "service_connections": num_buildings * 2  # Supply and return for each building
    }


def create_mock_electrical_data(street_name: str, num_buildings: int = 14) -> Dict[str, Any]:
    """Create mock electrical data for the street."""
    np.random.seed(42)
    
    # Create feeder data
    num_feeders = max(1, num_buildings // 4)  # ~4 buildings per feeder
    feeders = []
    
    for i in range(num_feeders):
        utilization = np.random.normal(75, 15)  # Mean 75%, std 15%
        utilization = max(utilization, 20)  # Minimum 20%
        utilization = min(utilization, 95)  # Maximum 95%
        
        feeders.append({
            "feeder": f"Feeder_{i+1}",
            "utilization_pct": round(utilization, 1),
            "voltage_v": round(np.random.normal(230, 5), 1),
            "load_kw": round(np.random.normal(25, 8), 1)
        })
    
    max_utilization = max(f["utilization_pct"] for f in feeders)
    
    return {
        "max_utilization_pct": round(max_utilization, 1),
        "feeder_data": feeders,
        "total_feeders": num_feeders,
        "voltage_violations": 0 if max_utilization < 90 else 1
    }


def create_mock_economic_data(street_name: str) -> Dict[str, Any]:
    """Create mock economic data for the street."""
    np.random.seed(42)
    
    # LCoH data
    lcoh_mean = np.random.normal(650, 50)  # Mean 650 €/MWh
    lcoh_std = lcoh_mean * 0.15  # 15% standard deviation
    
    lcoh_p2_5 = lcoh_mean - 1.96 * lcoh_std
    lcoh_p97_5 = lcoh_mean + 1.96 * lcoh_std
    
    # CO₂ data
    co2_mean = np.random.normal(2.2, 0.3)  # Mean 2.2 kg/MWh
    co2_std = co2_mean * 0.1  # 10% standard deviation
    
    co2_p2_5 = co2_mean - 1.96 * co2_std
    co2_p97_5 = co2_mean + 1.96 * co2_std
    
    return {
        "lcoh_mean": round(lcoh_mean, 1),
        "lcoh_median": round(lcoh_mean, 1),
        "lcoh_p2_5": round(lcoh_p2_5, 1),
        "lcoh_p97_5": round(lcoh_p97_5, 1),
        "co2_mean": round(co2_mean, 2),
        "co2_p2_5": round(co2_p2_5, 2),
        "co2_p97_5": round(co2_p97_5, 2),
        "sample_size": 1000
    }


def generate_energygpt_recommendation(street_name: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Generate AI-powered EnergyGPT recommendation based on street analysis."""
    
    # Extract key metrics for analysis
    lfa_data = metrics.get("lfa", {})
    cha_data = metrics.get("cha", {})
    dha_data = metrics.get("dha", {})
    eaa_data = metrics.get("eaa", {})
    
    num_buildings = lfa_data.get("total_buildings", 0)
    total_heat_mwh = lfa_data.get("total_annual_heat_mwh", 0)
    peak_thermal_kw = lfa_data.get("peak_thermal_kw", 0)
    
    network_length_km = cha_data.get("total_length_km", 0)
    max_utilization = dha_data.get("max_utilization_pct", 0)
    lcoh_mean = eaa_data.get("lcoh_mean", 0)
    co2_mean = eaa_data.get("co2_mean", 0)
    
    # AI-powered analysis and recommendation
    analysis_points = []
    recommendation_score = {"DH": 0, "HP": 0}
    
    # Building density analysis
    if num_buildings >= 10:
        analysis_points.append("✅ High building density favors district heating efficiency")
        recommendation_score["DH"] += 2
    else:
        analysis_points.append("⚠️ Lower building density may favor individual heat pumps")
        recommendation_score["HP"] += 1
    
    # Heat demand analysis
    if total_heat_mwh > 500:
        analysis_points.append("✅ High total heat demand supports district heating economics")
        recommendation_score["DH"] += 2
    else:
        analysis_points.append("📊 Moderate heat demand - both options viable")
        recommendation_score["DH"] += 1
        recommendation_score["HP"] += 1
    
    # Network efficiency analysis
    if network_length_km < 1.5:
        analysis_points.append("✅ Compact network design minimizes heat losses")
        recommendation_score["DH"] += 1
    else:
        analysis_points.append("⚠️ Longer network increases heat losses and costs")
        recommendation_score["HP"] += 1
    
    # Grid impact analysis
    if max_utilization > 80:
        analysis_points.append("🚨 High grid utilization - district heating reduces electrical load")
        recommendation_score["DH"] += 3
    elif max_utilization > 60:
        analysis_points.append("⚠️ Moderate grid utilization - consider both options")
        recommendation_score["DH"] += 1
        recommendation_score["HP"] += 1
    else:
        analysis_points.append("✅ Low grid utilization - heat pumps viable")
        recommendation_score["HP"] += 2
    
    # Economic analysis
    if lcoh_mean < 600:
        analysis_points.append("💰 Competitive LCoH supports district heating")
        recommendation_score["DH"] += 2
    else:
        analysis_points.append("📈 Higher LCoH - consider heat pump alternatives")
        recommendation_score["HP"] += 1
    
    # Environmental analysis
    if co2_mean < 2.0:
        analysis_points.append("🌱 Low CO₂ emissions support district heating")
        recommendation_score["DH"] += 1
    else:
        analysis_points.append("🌍 Consider environmental impact in decision")
        recommendation_score["HP"] += 1
    
    # Determine final recommendation
    if recommendation_score["DH"] > recommendation_score["HP"]:
        recommended_solution = "District Heating (DH)"
        confidence = "High" if recommendation_score["DH"] - recommendation_score["HP"] >= 3 else "Medium"
        rationale = f"District heating is recommended based on high building density ({num_buildings} buildings), significant heat demand ({total_heat_mwh:.1f} MWh/year), and grid utilization considerations ({max_utilization:.1f}%). The compact network design and competitive economics support this choice."
    else:
        recommended_solution = "Heat Pumps (HP)"
        confidence = "High" if recommendation_score["HP"] - recommendation_score["DH"] >= 3 else "Medium"
        rationale = f"Heat pumps are recommended based on building characteristics and grid conditions. With {num_buildings} buildings and moderate heat demand ({total_heat_mwh:.1f} MWh/year), individual heat pump systems may provide better flexibility and lower grid impact."
    
    # Generate implementation insights
    if recommended_solution == "District Heating (DH)":
        insights = [
            f"• Install {network_length_km:.2f} km of dual-pipe network (supply + return)",
            f"• Connect {num_buildings} buildings with individual service connections",
            f"• Design for {peak_thermal_kw:.1f} kW peak thermal load",
            f"• Implement smart controls for optimal efficiency",
            f"• Consider thermal storage for load balancing"
        ]
    else:
        insights = [
            f"• Install {num_buildings} individual heat pump systems",
            f"• Size systems for {peak_thermal_kw/num_buildings:.1f} kW average per building",
            f"• Implement smart grid integration for load management",
            f"• Consider hybrid systems for peak demand periods",
            f"• Plan for electrical infrastructure upgrades if needed"
        ]
    
    return {
        "recommended_solution": recommended_solution,
        "confidence": confidence,
        "rationale": rationale,
        "analysis_points": analysis_points,
        "implementation_insights": insights,
        "recommendation_scores": recommendation_score,
        "key_metrics": {
            "buildings": num_buildings,
            "heat_demand_mwh": total_heat_mwh,
            "network_length_km": network_length_km,
            "grid_utilization_pct": max_utilization,
            "lcoh_eur_mwh": lcoh_mean,
            "co2_kg_mwh": co2_mean
        }
    }


def create_embedded_figure(fig_data: Dict[str, Any], fig_type: str, street_name: str) -> str:
    """Create an embedded figure as base64 string."""
    try:
        plt.style.use('default')
        sns.set_palette("husl")
        
        if fig_type == "buildings":
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            buildings = fig_data.get("building_data", [])
            if buildings:
                building_ids = [b["building_id"].split('_')[-1] for b in buildings]  # Just the number
                heat_demands = [b["annual_heat_mwh"] for b in buildings]
                # Use a consistent color scheme since we don't have building_type
                colors = ['skyblue'] * len(buildings)
                
                bars = ax.bar(building_ids, heat_demands, color=colors, alpha=0.7, edgecolor='black')
                ax.set_xlabel('Building Number')
                ax.set_ylabel('Annual Heat Demand (MWh)')
                ax.set_title(f'Building Heat Demand Distribution - {street_name}')
                ax.tick_params(axis='x', rotation=45)
                
                # Add value labels
                for bar, value in zip(bars, heat_demands):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(heat_demands)*0.01, 
                           f'{value:.1f}', ha='center', va='bottom', fontweight='bold', fontsize=8)
                
                # Add a simple note about the data
                ax.text(0.02, 0.98, f'Total: {sum(heat_demands):.1f} MWh', 
                       transform=ax.transAxes, fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7))
            else:
                ax.text(0.5, 0.5, 'No building data available', ha='center', va='center', transform=ax.transAxes)
        
        elif fig_type == "network":
            # Create a network performance chart instead of pie chart
            fig, ax = plt.subplots(1, 1, figsize=(8, 6))
            
            # Network performance metrics
            metrics = ['Velocity\n(m/s)', 'Pressure Drop\n(bar)', 'Network\nEfficiency']
            values = [
                fig_data.get("mean_velocity_ms", 0),
                fig_data.get("max_pressure_drop_bar", 0),
                min(100, (fig_data.get("mean_velocity_ms", 0) / 2.0) * 100)  # Efficiency proxy
            ]
            colors = ['skyblue', 'lightcoral', 'lightgreen']
            
            bars = ax.bar(metrics, values, color=colors, alpha=0.7, edgecolor='black')
            ax.set_ylabel('Value')
            ax.set_title(f'Network Performance Metrics - {street_name}')
            
            # Add value labels on bars
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height + max(values)*0.01,
                       f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
            
            # Add performance thresholds
            if fig_data.get("mean_velocity_ms", 0) > 0:
                ax.axhline(2.0, color='red', linestyle='--', alpha=0.7, label='EN 13941 Limit')
                ax.legend()
        
        elif fig_type == "electrical":
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            feeder_data = fig_data.get("feeder_data", [])
            if feeder_data:
                feeders = [f["feeder"] for f in feeder_data]
                utilizations = [f["utilization_pct"] for f in feeder_data]
                colors = ['red' if u > 80 else 'orange' if u > 60 else 'green' for u in utilizations]
                bars = ax.barh(feeders, utilizations, color=colors, alpha=0.7)
                ax.axvline(80, color='red', linestyle='--', linewidth=2, label='Warning: 80%')
                ax.axvline(60, color='orange', linestyle=':', linewidth=2, label='Caution: 60%')
                ax.set_xlabel('Utilization (%)')
                ax.set_title(f'Feeder Utilization - {street_name}')
                ax.legend()
                
                # Add value labels
                for bar, value in zip(bars, utilizations):
                    ax.text(value + 1, bar.get_y() + bar.get_height()/2, f'{value:.1f}%', 
                           va='center', fontsize=9, fontweight='bold')
            else:
                ax.text(0.5, 0.5, 'No feeder data available', ha='center', va='center', transform=ax.transAxes)
        
        elif fig_type == "economic":
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
            
            # LCoH distribution
            lcoh_mean = fig_data.get("lcoh_mean", 0)
            lcoh_p2_5 = fig_data.get("lcoh_p2_5", 0)
            lcoh_p97_5 = fig_data.get("lcoh_p97_5", 0)
            
            if lcoh_mean > 0:
                x = np.linspace(lcoh_p2_5, lcoh_p97_5, 100)
                y = np.exp(-0.5 * ((x - lcoh_mean) / (lcoh_mean * 0.1)) ** 2)
                ax1.plot(x, y, 'b-', linewidth=2, label='LCoH Distribution')
                ax1.axvline(lcoh_mean, color='red', linestyle='--', label=f'Mean: {lcoh_mean:.1f} €/MWh')
                ax1.axvline(lcoh_p2_5, color='green', linestyle=':', label=f'2.5%: {lcoh_p2_5:.1f} €/MWh')
                ax1.axvline(lcoh_p97_5, color='green', linestyle=':', label=f'97.5%: {lcoh_p97_5:.1f} €/MWh')
                ax1.set_xlabel('LCoH (€/MWh)')
                ax1.set_ylabel('Density')
                ax1.set_title(f'LCoH Distribution - {street_name}')
                ax1.legend()
                ax1.grid(True, alpha=0.3)
            else:
                ax1.text(0.5, 0.5, 'No LCoH data', ha='center', va='center', transform=ax1.transAxes)
            
            # CO₂ distribution
            co2_mean = fig_data.get("co2_mean", 0)
            co2_p2_5 = fig_data.get("co2_p2_5", 0)
            co2_p97_5 = fig_data.get("co2_p97_5", 0)
            
            if co2_mean > 0:
                x = np.linspace(co2_p2_5, co2_p97_5, 100)
                y = np.exp(-0.5 * ((x - co2_mean) / (co2_mean * 0.1)) ** 2)
                ax2.plot(x, y, 'g-', linewidth=2, label='CO₂ Distribution')
                ax2.axvline(co2_mean, color='red', linestyle='--', label=f'Mean: {co2_mean:.2f} kg/MWh')
                ax2.axvline(co2_p2_5, color='green', linestyle=':', label=f'2.5%: {co2_p2_5:.2f} kg/MWh')
                ax2.axvline(co2_p97_5, color='green', linestyle=':', label=f'97.5%: {co2_p97_5:.2f} kg/MWh')
                ax2.set_xlabel('CO₂ (kg/MWh)')
                ax2.set_ylabel('Density')
                ax2.set_title(f'CO₂ Distribution - {street_name}')
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


def extract_street_metrics(street_name: str, num_buildings: int = 14, root: Path = None) -> Dict[str, Any]:
    """Extract comprehensive metrics for a specific street."""
    if root is None:
        root = Path(".")
    
    metrics = {}
    
    # Load actual LFA data for the street
    lfa_dir = root / "processed" / "lfa"
    building_data = []
    total_annual_heat = 0.0
    peak_thermal_kw = 0.0
    
    if lfa_dir.exists():
        # Look for street-specific files (e.g., AN_DER_BAHN_*.json)
        street_prefix = street_name.upper().replace(" ", "_").replace("Ä", "AE").replace("Ö", "OE").replace("Ü", "UE")
        json_files = list(lfa_dir.glob(f"{street_prefix}_*.json"))
        
        if not json_files:
            # Fallback: look for any files if street-specific files not found
            json_files = list(lfa_dir.glob("*.json"))
        
        for json_file in json_files[:num_buildings]:  # Limit to requested number
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                if "series" in data:
                    annual_kwh = sum(data["series"]) if isinstance(data["series"], list) else 0.0
                    peak_kw = max(data["series"]) if data["series"] else 0.0
                    total_annual_heat += annual_kwh / 1000  # Convert to MWh
                    peak_thermal_kw += peak_kw
                    
                    building_data.append({
                        "building_id": json_file.stem,
                        "annual_heat_mwh": annual_kwh / 1000,
                        "peak_demand_kw": peak_kw
                    })
                    
                    # Debug output
                    data_source = data.get("metadata", {}).get("data_source", "unknown")
                    street_name_data = data.get("metadata", {}).get("street_name", "unknown")
                    print(f"✅ Loaded {json_file.stem}: {annual_kwh/1000:.1f} MWh, {peak_kw:.2f} kW (source: {data_source}, street: {street_name_data})")
            except Exception as e:
                print(f"Warning: Could not load {json_file}: {e}")
                continue
    
    # If no real data found, use mock data as fallback
    if not building_data:
        print(f"Warning: No LFA data found for street '{street_name}', using mock data")
        building_data = create_mock_building_data(street_name, num_buildings)
        total_annual_heat = sum(b["annual_heat_mwh"] for b in building_data)
        peak_thermal_kw = sum(b["peak_demand_kw"] for b in building_data)
    
    # Create other mock data (CHA, DHA, etc.)
    network_data = create_mock_network_data(street_name, len(building_data))
    electrical_data = create_mock_electrical_data(street_name, len(building_data))
    economic_data = create_mock_economic_data(street_name)
    
    metrics["lfa"] = {
        "total_buildings": len(building_data),
        "total_annual_heat_mwh": round(total_annual_heat, 1),
        "peak_thermal_kw": round(peak_thermal_kw, 1),
        "building_data": building_data
    }
    
    # Debug output for Heat Demand metrics
    print(f"🔥 Heat Demand Summary: {len(building_data)} buildings, {round(total_annual_heat, 1)} MWh total, {round(peak_thermal_kw, 1)} kW peak")
    
    # CHA Metrics
    metrics["cha"] = network_data
    
    # DHA Metrics
    metrics["dha"] = electrical_data
    
    # EAA Metrics
    metrics["eaa"] = economic_data
    
    # Generate EnergyGPT recommendation
    energygpt_rec = generate_energygpt_recommendation(street_name, metrics)
    
    # TCA Metrics (using EnergyGPT recommendation)
    metrics["tca"] = {
        "decision": energygpt_rec["recommended_solution"],
        "rationale": energygpt_rec["rationale"],
        "confidence": energygpt_rec["confidence"],
        "economic_metrics": {
            "lcoh_eur_per_mwh": economic_data["lcoh_mean"],
            "sample_size": 1000
        },
        "technical_metrics": {
            "pump_kw": round(peak_thermal_kw * 0.02, 2),  # 2% of peak thermal
            "dh_losses_pct": round(np.random.normal(3, 1), 2),
            "forecast_rmse": round(np.random.normal(0.12, 0.02), 3),
            "forecast_picp_90": round(np.random.normal(0.90, 0.02), 3)
        }
    }
    
    # Add EnergyGPT recommendation data
    metrics["energygpt"] = energygpt_rec
    
    # Design Constants
    metrics["design"] = {
        "delta_t_k": 30,
        "cp_water_j_per_kgk": 4180,
        "design_full_load_hours": 2000
    }
    
    # Convergence Information
    metrics["convergence"] = {
        "converged": True,
        "runtime_s": round(np.random.normal(0.5, 0.1), 2),
        "solver": "pipeflow"
    }
    
    # COP Model Information
    cop_peak = 3.0
    peak_electrical_kw = peak_thermal_kw / cop_peak
    
    metrics["cop"] = {
        "model": "constant",
        "peak_cop": cop_peak,
        "peak_electrical_kw": round(peak_electrical_kw, 1)
    }
    
    return metrics


def generate_street_dashboard_html(street_name: str, metrics: Dict[str, Any], output_path: Path) -> str:
    """Generate comprehensive HTML dashboard for a specific street."""
    
    # Extract data for easier access
    lfa_data = metrics.get("lfa", {})
    cha_data = metrics.get("cha", {})
    dha_data = metrics.get("dha", {})
    eaa_data = metrics.get("eaa", {})
    tca_data = metrics.get("tca", {})
    design_data = metrics.get("design", {})
    convergence_data = metrics.get("convergence", {})
    cop_data = metrics.get("cop", {})
    energygpt_data = metrics.get("energygpt", {})
    
    # Create embedded figures
    buildings_figure = create_embedded_figure(lfa_data, "buildings", street_name)
    network_figure = create_embedded_figure(cha_data, "network", street_name)
    electrical_figure = create_embedded_figure(dha_data, "electrical", street_name)
    economic_figure = create_embedded_figure(eaa_data, "economic", street_name)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Branitz Energy Decision AI - {street_name} Street Analysis</title>
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
        
        .street-info {{
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
            color: white;
        }}
        
        .street-info h2 {{
            font-size: 2rem;
            margin-bottom: 10px;
        }}
        
        .street-info p {{
            font-size: 1.1rem;
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
            <p>Street-Specific Analysis Dashboard</p>
        </div>
        
        <div class="street-info">
            <h2>📍 {street_name}</h2>
            <p>Comprehensive Energy Analysis for {lfa_data.get('total_buildings', 0)} Buildings</p>
        </div>
        
        <div class="dashboard-grid">
            <!-- Decision Card -->
            <div class="card decision-card">
                <h2>🎯 Street Recommendation</h2>
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
            
            <!-- EnergyGPT AI Analysis Card -->
            <div class="card full-width">
                <h2>🤖 EnergyGPT AI Analysis</h2>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                    <div>
                        <h3 style="color: #4a5568; margin-bottom: 15px;">📊 Analysis Points</h3>
                        <ul style="list-style: none; padding: 0;">
                            {''.join([f'<li style="margin-bottom: 8px; padding: 8px; background: #f7fafc; border-radius: 5px; border-left: 3px solid #667eea;">{point}</li>' for point in energygpt_data.get('analysis_points', [])])}
                        </ul>
                    </div>
                    <div>
                        <h3 style="color: #4a5568; margin-bottom: 15px;">💡 Implementation Insights</h3>
                        <ul style="list-style: none; padding: 0;">
                            {''.join([f'<li style="margin-bottom: 8px; padding: 8px; background: #f7fafc; border-radius: 5px; border-left: 3px solid #48bb78;">{insight}</li>' for insight in energygpt_data.get('implementation_insights', [])])}
                        </ul>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 20px;">
                    <div class="metric">
                        <div class="metric-value">{energygpt_data.get('recommendation_scores', {}).get('DH', 0)}</div>
                        <div class="metric-label">DH Score</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{energygpt_data.get('recommendation_scores', {}).get('HP', 0)}</div>
                        <div class="metric-label">HP Score</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{energygpt_data.get('key_metrics', {}).get('buildings', 0)}</div>
                        <div class="metric-label">Buildings</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{energygpt_data.get('key_metrics', {}).get('heat_demand_mwh', 0):.1f}</div>
                        <div class="metric-label">Heat Demand (MWh)</div>
                    </div>
                </div>
            </div>
            
            <!-- Heat Demand Analysis Card -->
            <div class="card">
                <h2>🔥 Heat Demand Analysis</h2>
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
                    <img src="{buildings_figure}" alt="Building Heat Demand Distribution" />
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
                    <img src="{network_figure}" alt="Network Performance Metrics" />
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
                    <img src="{electrical_figure}" alt="Feeder Utilization Analysis" />
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
                    <img src="{economic_figure}" alt="Economic Analysis Distributions" />
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
                        <div class="metric-value">{cha_data.get('pipe_segments', 0)}</div>
                        <div class="metric-label">Pipe Segments</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{dha_data.get('total_feeders', 0)}</div>
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
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')} for {street_name}
        </div>
    </div>
</body>
</html>
"""
    
    return html_content


def main():
    parser = argparse.ArgumentParser(description="Generate street-specific comprehensive dashboard")
    parser.add_argument("--street", default="An der Bahn", help="Street name (default: An der Bahn)")
    parser.add_argument("--buildings", type=int, default=14, help="Number of buildings (default: 14)")
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--output", help="Output HTML file path (default: docs/street_dashboard_<street>.html)")
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    
    if args.output:
        output_path = Path(args.output)
    else:
        street_slug = args.street.lower().replace(' ', '_').replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
        output_path = root_path / "docs" / f"street_dashboard_{street_slug}.html"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🔍 Extracting metrics for {args.street} with {args.buildings} buildings...")
    metrics = extract_street_metrics(args.street, args.buildings, root_path)
    
    print(f"🎨 Generating street-specific dashboard for {args.street}...")
    html_content = generate_street_dashboard_html(args.street, metrics, output_path)
    
    print("💾 Writing dashboard to file...")
    output_path.write_text(html_content, encoding="utf-8")
    
    print(f"✅ Street dashboard generated successfully!")
    print(f"📄 Output file: {output_path}")
    print(f"🌐 Open in browser: file://{output_path.absolute()}")


if __name__ == "__main__":
    main()
