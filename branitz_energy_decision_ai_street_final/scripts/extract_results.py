#!/usr/bin/env python3
"""
Results Extractor for Branitz Energy Decision AI
Scans street-scoped artifacts and generates clean Markdown tables with key metrics.
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd


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


def extract_lfa_metrics(slug: str, root: Path) -> Dict[str, str]:
    """Extract LFA metrics from processed/lfa/<slug>/*.json files."""
    metrics = {}
    # Try street-specific directory first, then fallback to general directory
    lfa_dir = root / "processed" / "lfa" / slug if slug else root / "processed" / "lfa"
    
    if not lfa_dir.exists():
        return {"LFA buildings": "NA", "LFA annual heat": "NA"}
    
    # Count buildings and sum annual heat
    json_files = list(lfa_dir.glob("*.json"))
    if not json_files:
        return {"LFA buildings": "NA", "LFA annual heat": "NA"}
    
    total_heat_kwh = 0.0
    for json_file in json_files:
        data = load_json_safe(json_file)
        if data and "series" in data:
            # Sum hourly heat demand (kW) and convert to annual MWh
            annual_kwh = sum(data["series"]) if isinstance(data["series"], list) else 0.0
            total_heat_kwh += annual_kwh
    
    metrics["LFA buildings"] = str(len(json_files))
    metrics["LFA annual heat"] = f"{total_heat_kwh / 1000:.2f} MWh" if total_heat_kwh > 0 else "NA"
    
    return metrics


def extract_cha_metrics(slug: str, root: Path) -> Dict[str, str]:
    """Extract CHA metrics from processed/cha/<slug>/segments.csv and eval/cha/<slug>/hydraulics_check.csv."""
    metrics = {}
    
    # Load segments data - try street-specific first, then general
    if slug:
        segments_path = root / "processed" / "cha" / slug / "segments.csv"
    else:
        segments_path = root / "processed" / "cha" / "segments.csv"
    segments_df = load_csv_safe(segments_path)
    
    if segments_df is not None:
        # Total length
        total_length_km = segments_df["length_m"].sum() / 1000 if "length_m" in segments_df.columns else 0
        metrics["CHA total length"] = f"{total_length_km:.2f} km"
        
        # Supply vs return lengths
        if "pipe_type" in segments_df.columns:
            supply_length = segments_df[segments_df["pipe_type"] == "supply"]["length_m"].sum() / 1000
            return_length = segments_df[segments_df["pipe_type"] == "return"]["length_m"].sum() / 1000
            metrics["CHA supply / return"] = f"{supply_length:.2f} km / {return_length:.2f} km"
        else:
            metrics["CHA supply / return"] = "NA"
        
        # Mean velocity
        if "v_ms" in segments_df.columns:
            mean_velocity = segments_df["v_ms"].mean()
            metrics["CHA mean velocity"] = f"{mean_velocity:.3f} m/s"
        else:
            metrics["CHA mean velocity"] = "NA"
        
        # Max pressure drop
        if "dp_bar" in segments_df.columns:
            max_dp = segments_df["dp_bar"].max()
            metrics["CHA max Δp"] = f"{max_dp:.3f} bar"
        else:
            metrics["CHA max Δp"] = "NA"
    else:
        metrics.update({
            "CHA total length": "NA",
            "CHA supply / return": "NA", 
            "CHA mean velocity": "NA",
            "CHA max Δp": "NA"
        })
    
    # Load hydraulics check - try street-specific first, then general
    if slug:
        hydraulics_path = root / "eval" / "cha" / slug / "hydraulics_check.csv"
    else:
        hydraulics_path = root / "eval" / "cha" / "hydraulics_check.csv"
    hydraulics_df = load_csv_safe(hydraulics_path)
    
    if hydraulics_df is not None and "violations" in hydraulics_df.columns:
        violations = hydraulics_df["violations"].sum()
        metrics["CHA EN 13941 violations"] = str(int(violations))
    else:
        metrics["CHA EN 13941 violations"] = "NA"
    
    return metrics


def extract_dha_metrics(slug: str, root: Path) -> Dict[str, str]:
    """Extract DHA metrics from processed/dha/<slug>/feeder_loads.csv and eval/dha/<slug>/violations.csv."""
    metrics = {}
    
    # Load feeder loads - try street-specific first, then general
    if slug:
        feeders_path = root / "processed" / "dha" / slug / "feeder_loads.csv"
    else:
        feeders_path = root / "processed" / "dha" / "feeder_loads.csv"
    feeders_df = load_csv_safe(feeders_path)
    
    if feeders_df is not None and "utilization_pct" in feeders_df.columns:
        max_utilization = feeders_df["utilization_pct"].max()
        metrics["DHA feeder max utilization"] = f"{max_utilization:.1f} %"
    else:
        metrics["DHA feeder max utilization"] = "NA"
    
    # Load violations - try street-specific first, then general
    if slug:
        violations_path = root / "eval" / "dha" / slug / "violations.csv"
    else:
        violations_path = root / "eval" / "dha" / "violations.csv"
    violations_df = load_csv_safe(violations_path)
    
    if violations_df is not None:
        # Count voltage violations (assuming a 'type' column or similar)
        if "type" in violations_df.columns:
            voltage_violations = len(violations_df[violations_df["type"].str.contains("voltage", case=False, na=False)])
        else:
            voltage_violations = len(violations_df)
        metrics["DHA voltage violations"] = str(voltage_violations)
    else:
        metrics["DHA voltage violations"] = "NA"
    
    return metrics


def extract_eaa_metrics(slug: str, root: Path) -> Dict[str, str]:
    """Extract EAA metrics from eval/te/<slug>/summary.csv."""
    metrics = {}
    
    # Try street-specific first, then general
    if slug:
        summary_path = root / "eval" / "te" / slug / "summary.csv"
        mc_path = root / "eval" / "te" / slug / "mc.parquet"
    else:
        summary_path = root / "eval" / "te" / "summary.csv"
        mc_path = root / "eval" / "te" / "mc.parquet"
    
    summary_df = load_csv_safe(summary_path)
    
    if summary_df is not None:
        # Find LCoH metrics
        lcoh_row = summary_df[summary_df["metric"] == "lcoh_eur_per_mwh"]
        if not lcoh_row.empty:
            mean_lcoh = lcoh_row["mean"].iloc[0]
            p2_5 = lcoh_row["p2_5"].iloc[0]
            p97_5 = lcoh_row["p97_5"].iloc[0]
            metrics["LCoH (mean, 95% CI)"] = f"{mean_lcoh:.1f} [{p2_5:.1f}–{p97_5:.1f}] €/MWh"
        else:
            metrics["LCoH (mean, 95% CI)"] = "NA"
        
        # Find CO₂ metrics
        co2_row = summary_df[summary_df["metric"] == "co2_kg_per_mwh"]
        if not co2_row.empty:
            mean_co2 = co2_row["mean"].iloc[0]
            co2_p2_5 = co2_row["p2_5"].iloc[0]
            co2_p97_5 = co2_row["p97_5"].iloc[0]
            metrics["CO₂ (mean, 95% CI)"] = f"{mean_co2:.2f} [{co2_p2_5:.2f}–{co2_p97_5:.2f}] kg/MWh"
        else:
            metrics["CO₂ (mean, 95% CI)"] = "NA"
    else:
        metrics["LCoH (mean, 95% CI)"] = "NA"
        metrics["CO₂ (mean, 95% CI)"] = "NA"
    
    # Extract sample size from Monte Carlo data
    if mc_path.exists():
        try:
            mc_df = pd.read_parquet(mc_path)
            metrics["Sample size N"] = str(len(mc_df))
        except Exception:
            metrics["Sample size N"] = "NA"
    else:
        metrics["Sample size N"] = "NA"
    
    return metrics


def extract_tca_metrics(slug: str, root: Path) -> Dict[str, str]:
    """Extract TCA metrics from processed/kpi/<slug>/kpi_summary.json."""
    metrics = {}
    
    # Try street-specific first, then general
    if slug:
        kpi_path = root / "processed" / "kpi" / slug / "kpi_summary.json"
    else:
        kpi_path = root / "processed" / "kpi" / "kpi_summary.json"
    kpi_data = load_json_safe(kpi_path)
    
    if kpi_data is not None:
        # Extract decision and rationale
        recommendation = kpi_data.get("recommendation", {})
        preferred_scenario = recommendation.get("preferred_scenario", "NA")
        rationale = recommendation.get("rationale", "NA")
        
        metrics["KPI decision"] = preferred_scenario
        metrics["KPI rationale"] = rationale[:100] + "…" if len(rationale) > 100 else rationale
        
        # Extract additional technical and economic metrics
        economic_metrics = kpi_data.get("economic_metrics", {})
        technical_metrics = kpi_data.get("technical_metrics", {})
        
        metrics["Pump power"] = f"{technical_metrics.get('pump_kw', 0):.2f} kW" if technical_metrics.get('pump_kw') is not None else "NA"
        metrics["DH losses"] = f"{technical_metrics.get('dh_losses_pct', 0):.2f}%" if technical_metrics.get('dh_losses_pct') is not None else "NA"
        metrics["Forecast RMSE"] = f"{technical_metrics.get('forecast_rmse', 0):.3f}" if technical_metrics.get('forecast_rmse') is not None else "NA"
        metrics["Forecast PICP90"] = f"{technical_metrics.get('forecast_picp_90', 0):.3f}" if technical_metrics.get('forecast_picp_90') is not None else "NA"
    else:
        metrics.update({
            "KPI decision": "NA",
            "KPI rationale": "NA",
            "Pump power": "NA",
            "DH losses": "NA",
            "Forecast RMSE": "NA",
            "Forecast PICP90": "NA"
        })
    
    return metrics


def extract_design_constants(slug: str, root: Path) -> Dict[str, str]:
    """Extract design constants and convergence information."""
    metrics = {}
    
    # Extract design constants from EAA config
    eaa_config_path = root / "configs" / "eaa.yml"
    eaa_config = load_yaml_safe(eaa_config_path)
    
    if eaa_config is not None:
        metrics["ΔT (K)"] = f"{eaa_config.get('delta_t_k', 'NA')}"
        metrics["cp (J/kg·K)"] = f"{eaa_config.get('cp_water_j_per_kgk', 'NA')}"
        metrics["Design hours"] = f"{eaa_config.get('design_full_load_hours', 'NA')}"
    else:
        metrics.update({
            "ΔT (K)": "NA",
            "cp (J/kg·K)": "NA", 
            "Design hours": "NA"
        })
    
    # Extract convergence information
    if slug:
        sim_path = root / "eval" / "cha" / slug / "sim.json"
    else:
        sim_path = root / "eval" / "cha" / "sim.json"
    
    sim_data = load_json_safe(sim_path)
    if sim_data is not None:
        converged = sim_data.get("converged", False)
        metrics["Convergence"] = "Yes" if converged else "No"
        if "runtime_s" in sim_data:
            metrics["Runtime (s)"] = f"{sim_data['runtime_s']:.2f}"
    else:
        metrics["Convergence"] = "NA"
        metrics["Runtime (s)"] = "NA"
    
    return metrics


def extract_cop_metrics(slug: str, root: Path) -> Dict[str, str]:
    """Extract COP model and peak electrical power metrics."""
    metrics = {}
    
    # Extract COP model from DHA config
    dha_config_path = root / "configs" / "dha.yml"
    dha_config = load_yaml_safe(dha_config_path)
    
    if dha_config is not None:
        cop_model = dha_config.get("cop_model", "constant")
        metrics["COP model"] = cop_model
        
        # Calculate peak electrical power
        lfa_dir = root / "processed" / "lfa" / slug if slug else root / "processed" / "lfa"
        if lfa_dir.exists():
            json_files = list(lfa_dir.glob("*.json"))
            peak_thermal_kw = 0.0
            
            for json_file in json_files:
                data = load_json_safe(json_file)
                if data and "series" in data:
                    peak_kw = max(data["series"]) if data["series"] else 0.0
                    peak_thermal_kw += peak_kw
            
            # Assume COP = 3.0 for peak calculation (can be made configurable)
            cop_peak = dha_config.get("cop_peak", 3.0)
            peak_electrical_kw = peak_thermal_kw / cop_peak
            metrics["Peak P_el"] = f"{peak_electrical_kw:.1f} kW"
        else:
            metrics["Peak P_el"] = "NA"
    else:
        metrics.update({
            "COP model": "NA",
            "Peak P_el": "NA"
        })
    
    return metrics


def generate_results_table(slug: str, root: Path) -> str:
    """Generate complete results table for a street slug."""
    # Extract metrics from all agents
    all_metrics = {}
    all_metrics.update(extract_lfa_metrics(slug, root))
    all_metrics.update(extract_cha_metrics(slug, root))
    all_metrics.update(extract_dha_metrics(slug, root))
    all_metrics.update(extract_eaa_metrics(slug, root))
    all_metrics.update(extract_tca_metrics(slug, root))
    all_metrics.update(extract_design_constants(slug, root))
    all_metrics.update(extract_cop_metrics(slug, root))
    
    # Generate Markdown table
    table_lines = [
        "# Results — " + slug,
        f"_Generated {datetime.utcnow().isoformat()}Z_",
        "",
        "## Summary Table",
        "",
        "| Metric | Value | Source |",
        "|---|---:|---|"
    ]
    
    # Define source mapping for each metric
    source_mapping = {
        "LFA buildings": f"processed/lfa/{slug}",
        "LFA annual heat": f"processed/lfa/{slug}",
        "CHA total length": f"processed/cha/{slug}/segments.csv",
        "CHA supply / return": "segments.csv",
        "CHA mean velocity": "segments.csv",
        "CHA max Δp": "segments.csv",
        "CHA EN 13941 violations": f"eval/cha/{slug}/hydraulics_check.csv",
        "DHA feeder max utilization": f"processed/dha/{slug}/feeder_loads.csv",
        "DHA voltage violations": f"eval/dha/{slug}/violations.csv",
        "LCoH (mean, 95% CI)": f"eval/te/{slug}/summary.csv",
        "CO₂ (mean, 95% CI)": f"eval/te/{slug}/summary.csv",
        "Sample size N": f"eval/te/{slug}/mc.parquet",
        "KPI decision": f"processed/kpi/{slug}/kpi_summary.json",
        "KPI rationale": "kpi_summary.json",
        "Pump power": "kpi_summary.json",
        "DH losses": "kpi_summary.json",
        "Forecast RMSE": "kpi_summary.json",
        "Forecast PICP90": "kpi_summary.json",
        "ΔT (K)": "configs/eaa.yml",
        "cp (J/kg·K)": "configs/eaa.yml",
        "Design hours": "configs/eaa.yml",
        "Convergence": f"eval/cha/{slug}/sim.json",
        "Runtime (s)": f"eval/cha/{slug}/sim.json",
        "COP model": "configs/dha.yml",
        "Peak P_el": "configs/dha.yml + LFA data"
    }
    
    for metric, value in all_metrics.items():
        source = source_mapping.get(metric, "unknown")
        table_lines.append(f"| {metric} | {value} | {source} |")
    
    table_lines.extend([
        "",
        "## Notes",
        "- Values shown as `NA` were not found in the expected files."
    ])
    
    return "\n".join(table_lines)


def main():
    parser = argparse.ArgumentParser(description="Extract results from Branitz Energy Decision AI artifacts")
    parser.add_argument("--slug", required=True, help="Street slug (e.g., 'luciestrasse')")
    parser.add_argument("--root", default=".", help="Project root directory (default: current directory)")
    parser.add_argument("--outdir", default="docs", help="Output directory for results file (default: docs)")
    
    args = parser.parse_args()
    
    root_path = Path(args.root)
    outdir_path = Path(args.outdir)
    outdir_path.mkdir(exist_ok=True)
    
    # Generate results table
    results_markdown = generate_results_table(args.slug, root_path)
    
    # Print to stdout
    print(results_markdown)
    
    # Write to file
    output_file = outdir_path / f"results_{args.slug}.md"
    output_file.write_text(results_markdown, encoding="utf-8")
    print(f"\n📄 Results written to: {output_file}")


if __name__ == "__main__":
    main()
