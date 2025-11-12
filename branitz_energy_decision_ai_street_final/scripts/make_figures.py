#!/usr/bin/env python3
"""
Figure Generator for Branitz Energy Decision AI
Creates comprehensive figures for hydraulics, electrical, and economic analysis.
"""

import argparse
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from datetime import datetime


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


def create_hydraulics_figures(slug: str, root: Path, outdir: Path) -> None:
    """Create hydraulics figures (velocity and pressure drop distributions)."""
    # Load segments data
    if slug:
        segments_path = root / "processed" / "cha" / slug / "segments.csv"
    else:
        segments_path = root / "processed" / "cha" / "segments.csv"
    
    segments_df = load_csv_safe(segments_path)
    if segments_df is None or len(segments_df) == 0:
        print(f"⚠️ No segments data found for {slug}")
        return
    
    # Set up the figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle(f'Hydraulics Analysis - {slug if slug else "System"}', fontsize=16, fontweight='bold')
    
    # Velocity distribution
    if "v_ms" in segments_df.columns:
        velocities = segments_df["v_ms"].dropna()
        if len(velocities) > 0:
            ax1.hist(velocities, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax1.axvline(velocities.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {velocities.mean():.3f} m/s')
            ax1.axvline(2.0, color='orange', linestyle=':', linewidth=2, label='EN 13941 Limit: 2.0 m/s')
            ax1.set_xlabel('Velocity (m/s)')
            ax1.set_ylabel('Frequency')
            ax1.set_title('Velocity Distribution')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(0.5, 0.5, 'No velocity data', ha='center', va='center', transform=ax1.transAxes)
    else:
        ax1.text(0.5, 0.5, 'No velocity data', ha='center', va='center', transform=ax1.transAxes)
    
    # Pressure drop distribution
    if "dp_bar" in segments_df.columns:
        pressure_drops = segments_df["dp_bar"].dropna()
        if len(pressure_drops) > 0:
            ax2.hist(pressure_drops, bins=20, alpha=0.7, color='lightcoral', edgecolor='black')
            ax2.axvline(pressure_drops.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean: {pressure_drops.mean():.3f} bar')
            ax2.axvline(0.5, color='orange', linestyle=':', linewidth=2, label='Typical Limit: 0.5 bar')
            ax2.set_xlabel('Pressure Drop (bar)')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Pressure Drop Distribution')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'No pressure drop data', ha='center', va='center', transform=ax2.transAxes)
    else:
        ax2.text(0.5, 0.5, 'No pressure drop data', ha='center', va='center', transform=ax2.transAxes)
    
    plt.tight_layout()
    
    # Save figure
    output_path = outdir / f"fig3_hydraulics_{slug if slug else 'system'}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Created hydraulics figure: {output_path}")


def create_electrical_figures(slug: str, root: Path, outdir: Path) -> None:
    """Create electrical figures (feeder utilization bar chart)."""
    # Load feeder data
    if slug:
        feeders_path = root / "processed" / "dha" / slug / "feeder_loads.csv"
    else:
        feeders_path = root / "processed" / "dha" / "feeder_loads.csv"
    
    feeders_df = load_csv_safe(feeders_path)
    if feeders_df is None or len(feeders_df) == 0:
        print(f"⚠️ No feeder data found for {slug}")
        return
    
    # Set up the figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    fig.suptitle(f'Feeder Utilization Analysis - {slug if slug else "System"}', fontsize=16, fontweight='bold')
    
    if "utilization_pct" in feeders_df.columns:
        # Sort feeders by utilization
        feeders_sorted = feeders_df.sort_values("utilization_pct", ascending=True)
        
        # Create bar chart
        bars = ax.barh(range(len(feeders_sorted)), feeders_sorted["utilization_pct"], 
                      color=['red' if x > 80 else 'orange' if x > 60 else 'green' for x in feeders_sorted["utilization_pct"]])
        
        # Add threshold lines
        ax.axvline(80, color='red', linestyle='--', linewidth=2, label='Warning Threshold: 80%')
        ax.axvline(60, color='orange', linestyle=':', linewidth=2, label='Caution Threshold: 60%')
        
        # Customize plot
        ax.set_yticks(range(len(feeders_sorted)))
        if "feeder" in feeders_sorted.columns:
            ax.set_yticklabels(feeders_sorted["feeder"])
        else:
            ax.set_yticklabels([f"Feeder {i+1}" for i in range(len(feeders_sorted))])
        
        ax.set_xlabel('Utilization (%)')
        ax.set_title('Top Feeder Utilization')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, feeders_sorted["utilization_pct"])):
            ax.text(value + 1, i, f'{value:.1f}%', va='center', fontsize=9)
    else:
        ax.text(0.5, 0.5, 'No utilization data', ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    
    # Save figure
    output_path = outdir / f"fig4_electrical_{slug if slug else 'system'}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Created electrical figure: {output_path}")


def create_economic_figures(slug: str, root: Path, outdir: Path) -> None:
    """Create economic figures (LCoH and CO₂ distributions)."""
    # Load Monte Carlo data
    if slug:
        mc_path = root / "eval" / "te" / slug / "mc.parquet"
    else:
        mc_path = root / "eval" / "te" / "mc.parquet"
    
    if not mc_path.exists():
        print(f"⚠️ No Monte Carlo data found for {slug}")
        return
    
    try:
        mc_df = pd.read_parquet(mc_path)
    except Exception as e:
        print(f"⚠️ Error loading Monte Carlo data: {e}")
        return
    
    # Set up the figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle(f'Economic Analysis - {slug if slug else "System"}', fontsize=16, fontweight='bold')
    
    # LCoH distribution
    if "lcoh_eur_per_mwh" in mc_df.columns:
        lcoh_data = mc_df["lcoh_eur_per_mwh"].dropna()
        if len(lcoh_data) > 0:
            # Create violin plot
            parts = ax1.violinplot([lcoh_data], positions=[1], showmeans=True, showmedians=True)
            parts['bodies'][0].set_facecolor('lightblue')
            parts['bodies'][0].set_alpha(0.7)
            
            # Add statistics
            mean_val = lcoh_data.mean()
            median_val = lcoh_data.median()
            p2_5 = lcoh_data.quantile(0.025)
            p97_5 = lcoh_data.quantile(0.975)
            
            ax1.axhline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.1f} €/MWh')
            ax1.axhline(median_val, color='blue', linestyle='-', linewidth=2, label=f'Median: {median_val:.1f} €/MWh')
            ax1.axhline(p2_5, color='green', linestyle=':', linewidth=2, label=f'2.5%: {p2_5:.1f} €/MWh')
            ax1.axhline(p97_5, color='green', linestyle=':', linewidth=2, label=f'97.5%: {p97_5:.1f} €/MWh')
            
            ax1.set_ylabel('LCoH (€/MWh)')
            ax1.set_title('LCoH Distribution')
            ax1.set_xticks([1])
            ax1.set_xticklabels(['LCoH'])
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        else:
            ax1.text(0.5, 0.5, 'No LCoH data', ha='center', va='center', transform=ax1.transAxes)
    else:
        ax1.text(0.5, 0.5, 'No LCoH data', ha='center', va='center', transform=ax1.transAxes)
    
    # CO₂ distribution
    if "co2_kg_per_mwh" in mc_df.columns:
        co2_data = mc_df["co2_kg_per_mwh"].dropna()
        if len(co2_data) > 0:
            # Create violin plot
            parts = ax2.violinplot([co2_data], positions=[1], showmeans=True, showmedians=True)
            parts['bodies'][0].set_facecolor('lightgreen')
            parts['bodies'][0].set_alpha(0.7)
            
            # Add statistics
            mean_val = co2_data.mean()
            median_val = co2_data.median()
            p2_5 = co2_data.quantile(0.025)
            p97_5 = co2_data.quantile(0.975)
            
            ax2.axhline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f} kg/MWh')
            ax2.axhline(median_val, color='blue', linestyle='-', linewidth=2, label=f'Median: {median_val:.2f} kg/MWh')
            ax2.axhline(p2_5, color='green', linestyle=':', linewidth=2, label=f'2.5%: {p2_5:.2f} kg/MWh')
            ax2.axhline(p97_5, color='green', linestyle=':', linewidth=2, label=f'97.5%: {p97_5:.2f} kg/MWh')
            
            ax2.set_ylabel('CO₂ Emissions (kg/MWh)')
            ax2.set_title('CO₂ Distribution')
            ax2.set_xticks([1])
            ax2.set_xticklabels(['CO₂'])
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        else:
            ax2.text(0.5, 0.5, 'No CO₂ data', ha='center', va='center', transform=ax2.transAxes)
    else:
        ax2.text(0.5, 0.5, 'No CO₂ data', ha='center', va='center', transform=ax2.transAxes)
    
    plt.tight_layout()
    
    # Save figure
    output_path = outdir / f"fig6_economic_{slug if slug else 'system'}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Created economic figure: {output_path}")


def create_sensitivity_figures(slug: str, root: Path, outdir: Path) -> None:
    """Create sensitivity analysis figures (tornado chart)."""
    # Load sensitivity data
    if slug:
        sensitivity_path = root / "eval" / "apa" / slug / "sensitivity.csv"
    else:
        sensitivity_path = root / "eval" / "apa" / "sensitivity.csv"
    
    if not sensitivity_path.exists():
        print(f"⚠️ No sensitivity data found for {slug}")
        return
    
    sensitivity_df = load_csv_safe(sensitivity_path)
    if sensitivity_df is None or len(sensitivity_df) == 0:
        print(f"⚠️ No sensitivity data found for {slug}")
        return
    
    # Set up the figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    fig.suptitle(f'Sensitivity Analysis - {slug if slug else "System"}', fontsize=16, fontweight='bold')
    
    # Create tornado chart
    if "parameter" in sensitivity_df.columns and "change_pct" in sensitivity_df.columns:
        # Sort by absolute change
        sensitivity_df["abs_change"] = sensitivity_df["change_pct"].abs()
        sensitivity_sorted = sensitivity_df.sort_values("abs_change", ascending=True)
        
        # Create horizontal bar chart
        y_pos = range(len(sensitivity_sorted))
        colors = ['red' if x < 0 else 'blue' for x in sensitivity_sorted["change_pct"]]
        
        bars = ax.barh(y_pos, sensitivity_sorted["change_pct"], color=colors, alpha=0.7)
        
        # Customize plot
        ax.set_yticks(y_pos)
        ax.set_yticklabels(sensitivity_sorted["parameter"])
        ax.set_xlabel('Change in LCoH (%)')
        ax.set_title('Tornado Chart - Parameter Sensitivity')
        ax.axvline(0, color='black', linestyle='-', linewidth=1)
        ax.grid(True, alpha=0.3)
        
        # Add value labels
        for i, (bar, value) in enumerate(zip(bars, sensitivity_sorted["change_pct"])):
            ax.text(value + (1 if value >= 0 else -1), i, f'{value:.1f}%', 
                   va='center', ha='left' if value >= 0 else 'right', fontsize=9)
    else:
        ax.text(0.5, 0.5, 'No sensitivity data', ha='center', va='center', transform=ax.transAxes)
    
    plt.tight_layout()
    
    # Save figure
    output_path = outdir / f"fig8_sensitivity_{slug if slug else 'system'}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Created sensitivity figure: {output_path}")


def create_summary_figure(slug: str, root: Path, outdir: Path) -> None:
    """Create a summary figure with key metrics."""
    # Load key data
    kpi_path = root / "processed" / "kpi" / "kpi_summary.json" if not slug else root / "processed" / "kpi" / slug / "kpi_summary.json"
    kpi_data = load_json_safe(kpi_path)
    
    if kpi_data is None:
        print(f"⚠️ No KPI data found for {slug}")
        return
    
    # Set up the figure
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'System Summary - {slug if slug else "System"}', fontsize=18, fontweight='bold')
    
    # Key metrics
    economic_metrics = kpi_data.get("economic_metrics", {})
    technical_metrics = kpi_data.get("technical_metrics", {})
    recommendation = kpi_data.get("recommendation", {})
    
    # Decision summary
    ax1.text(0.5, 0.7, f"Recommended Scenario:", ha='center', va='center', fontsize=16, fontweight='bold', transform=ax1.transAxes)
    ax1.text(0.5, 0.5, f"{recommendation.get('preferred_scenario', 'Unknown')}", ha='center', va='center', 
             fontsize=24, fontweight='bold', color='blue', transform=ax1.transAxes)
    ax1.text(0.5, 0.3, f"Confidence: {recommendation.get('confidence_level', 'Unknown')}", ha='center', va='center', 
             fontsize=12, transform=ax1.transAxes)
    ax1.set_title('System Recommendation')
    ax1.axis('off')
    
    # Economic metrics
    lcoh = economic_metrics.get('lcoh_eur_per_mwh', 0)
    ax2.bar(['LCoH'], [lcoh], color='lightblue', alpha=0.7)
    ax2.set_ylabel('€/MWh')
    ax2.set_title('Levelized Cost of Heat')
    ax2.text(0, lcoh + 5, f'{lcoh:.1f} €/MWh', ha='center', va='bottom', fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # Technical metrics
    pump_kw = technical_metrics.get('pump_kw', 0)
    dh_losses = technical_metrics.get('dh_losses_pct', 0)
    feeder_util = technical_metrics.get('feeder_max_utilization_pct', 0)
    
    metrics = ['Pump Power', 'DH Losses', 'Feeder Util']
    values = [pump_kw, dh_losses, feeder_util]
    colors = ['lightcoral', 'lightgreen', 'orange']
    
    bars = ax3.bar(metrics, values, color=colors, alpha=0.7)
    ax3.set_ylabel('Value')
    ax3.set_title('Technical Metrics')
    ax3.tick_params(axis='x', rotation=45)
    
    # Add value labels
    for bar, value in zip(bars, values):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.01, 
                f'{value:.1f}', ha='center', va='bottom', fontweight='bold')
    ax3.grid(True, alpha=0.3)
    
    # System status
    status_items = [
        f"Buildings: {kpi_data.get('project_info', {}).get('total_buildings', 'N/A')}",
        f"Network Length: {technical_metrics.get('total_length_km', 0):.1f} km",
        f"Convergence: {'Yes' if technical_metrics.get('converged', False) else 'No'}",
        f"Sample Size: {economic_metrics.get('sample_size', 'N/A')}"
    ]
    
    ax4.text(0.1, 0.8, "System Status:", ha='left', va='center', fontsize=14, fontweight='bold', transform=ax4.transAxes)
    for i, item in enumerate(status_items):
        ax4.text(0.1, 0.6 - i*0.15, item, ha='left', va='center', fontsize=12, transform=ax4.transAxes)
    ax4.set_title('System Overview')
    ax4.axis('off')
    
    plt.tight_layout()
    
    # Save figure
    output_path = outdir / f"fig1_summary_{slug if slug else 'system'}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Created summary figure: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive figures for Branitz Energy Decision AI")
    parser.add_argument("--slug", default="", help="Street slug (empty for system overview)")
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--outdir", default="docs", help="Output directory for figures (default: docs)")
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    outdir_path = Path(args.outdir)
    outdir_path.mkdir(exist_ok=True)
    
    print(f"🎨 Generating figures for '{args.slug if args.slug else 'system overview'}'...")
    
    # Set matplotlib style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Generate all figures
    create_summary_figure(args.slug, root_path, outdir_path)
    create_hydraulics_figures(args.slug, root_path, outdir_path)
    create_electrical_figures(args.slug, root_path, outdir_path)
    create_economic_figures(args.slug, root_path, outdir_path)
    create_sensitivity_figures(args.slug, root_path, outdir_path)
    
    print(f"✅ All figures generated successfully in {outdir_path}")


if __name__ == "__main__":
    main()





