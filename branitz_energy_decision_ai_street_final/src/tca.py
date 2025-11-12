from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from jsonschema import Draft202012Validator

def _read_yaml(p: str) -> dict:
    import yaml
    return yaml.safe_load(Path(p).read_text())

def _validate_json(instance: dict, schema_path: str):
    schema = json.loads(Path(schema_path).read_text())
    Draft202012Validator(schema).validate(instance)

def _read_summary_csv(p: str) -> dict:
    df = pd.read_csv(p)
    def get(metric, col):
        return float(df.loc[df["metric"]==metric, col].values[0])
    return {
        "lcoh_mean": get("lcoh_eur_per_mwh", "mean"),
        "co2_mean": get("co2_kg_per_mwh", "mean"),
        "lcoh_median": get("lcoh_eur_per_mwh", "median"),
        "co2_median": get("co2_kg_per_mwh", "median"),
        "lcoh_p2_5": get("lcoh_eur_per_mwh", "p2_5"),
        "lcoh_p97_5": get("lcoh_eur_per_mwh", "p97_5")
    }

def _calculate_cha_metrics_from_hydraulics(cha_df: pd.DataFrame) -> dict:
    """
    Calculate CHA metrics from actual hydraulic simulation results.
    
    Args:
        cha_df: CHA segments DataFrame with hydraulic simulation data
        
    Returns:
        dict: Enhanced CHA metrics including hydraulic and thermal performance
    """
    try:
        # Check if enhanced hydraulic data is available
        has_hydraulic_data = all(col in cha_df.columns for col in 
                                ["q_loss_Wm", "mdot_kg_s", "t_seg_c", "pipe_category"])
        
        if has_hydraulic_data:
            # Enhanced calculation using hydraulic simulation data
            
            # DH losses percentage (thermal losses as percentage of total heat)
            total_thermal_loss_w = (cha_df["q_loss_Wm"] * cha_df["length_m"]).sum()
            total_heat_demand_w = cha_df["mdot_kg_s"].sum() * 4180 * 30  # cp * delta_T
            dh_losses_pct = (total_thermal_loss_w / max(total_heat_demand_w, 1e-6)) * 100
            
            # Pump power using mass flow rates
            dp_pa = cha_df["dp_bar"] * 1e5
            water_density_kg_m3 = 977.8
            volumetric_flow_m3s = cha_df["mdot_kg_s"] / water_density_kg_m3
            hydraulic_power_w = (dp_pa * volumetric_flow_m3s).clip(lower=0).sum()
            pump_kw = hydraulic_power_w / 1000.0 / 0.75  # Assuming 75% pump efficiency
            
            # Maximum velocity
            max_velocity_ms = float(cha_df["v_ms"].max())
            
            # Maximum pressure drop per 100m
            dp_pa_per_100m = (cha_df["dp_bar"] * 1e5) / (cha_df["length_m"] / 100.0)
            max_pressure_drop_pa_per_m = float(dp_pa_per_100m.max())
            
            # Thermal efficiency
            supply_temp_c = cha_df["t_seg_c"].max()
            return_temp_c = cha_df["t_seg_c"].min()
            ground_temp_c = 10.0
            if supply_temp_c > ground_temp_c:
                thermal_efficiency = (supply_temp_c - return_temp_c) / (supply_temp_c - ground_temp_c)
                thermal_efficiency = min(thermal_efficiency, 1.0)
            else:
                thermal_efficiency = 0.0
            
            # Network length
            network_length_km = float(cha_df["length_m"].sum() / 1000.0)
            
            # Total flow rate
            total_flow_kg_s = float(cha_df["mdot_kg_s"].sum())
            
        else:
            # Fallback to original proxy calculations
            dh_losses_pct = float(cha_df.get("q_loss_Wm", pd.Series([0])).fillna(0).sum() * 1e-3)
            pump_kw = float((cha_df.get("dp_bar", pd.Series([0])) * 1e5 *
                           (cha_df.get("v_ms", pd.Series([0])) * (3.14159*(cha_df.get("d_inner_m", pd.Series([0]))/2)**2))
                          ).sum() / 1000.0)
            max_velocity_ms = float(cha_df.get("v_ms", pd.Series([0])).max())
            max_pressure_drop_pa_per_m = float((cha_df.get("dp_bar", pd.Series([0])) * 1e5).max())
            thermal_efficiency = 0.0
            network_length_km = float(cha_df.get("length_m", pd.Series([0])).sum() / 1000.0)
            total_flow_kg_s = 0.0
        
        return {
            "dh_losses_pct": dh_losses_pct,
            "pump_kw": pump_kw,
            "max_velocity_ms": max_velocity_ms,
            "max_pressure_drop_pa_per_m": max_pressure_drop_pa_per_m,
            "thermal_efficiency": thermal_efficiency,
            "network_length_km": network_length_km,
            "total_flow_kg_s": total_flow_kg_s
        }
        
    except Exception as e:
        # Fallback to safe defaults
        return {
            "dh_losses_pct": 0.0,
            "pump_kw": 0.0,
            "max_velocity_ms": 0.0,
            "max_pressure_drop_pa_per_m": 0.0,
            "thermal_efficiency": 0.0,
            "network_length_km": 0.0,
            "total_flow_kg_s": 0.0
        }

def _calculate_pump_efficiency_metrics(cha_df: pd.DataFrame) -> dict:
    """
    Calculate pump efficiency metrics from hydraulic simulation data.
    
    Args:
        cha_df: CHA segments DataFrame with hydraulic simulation data
        
    Returns:
        dict: Pump efficiency metrics
    """
    try:
        # Check if enhanced hydraulic data is available
        has_hydraulic_data = all(col in cha_df.columns for col in 
                                ["mdot_kg_s", "dp_bar", "v_ms", "d_inner_m"])
        
        if has_hydraulic_data:
            # Calculate pump power using mass flow rates
            dp_pa = cha_df["dp_bar"] * 1e5
            water_density_kg_m3 = 977.8
            volumetric_flow_m3s = cha_df["mdot_kg_s"] / water_density_kg_m3
            hydraulic_power_w = (dp_pa * volumetric_flow_m3s).clip(lower=0).sum()
            
            # Pump efficiency (assumed 75% for now, could be configurable)
            pump_efficiency = 0.75
            pump_power_w = hydraulic_power_w / pump_efficiency
            
            # Specific pump power (kW per kg/s)
            total_flow_kg_s = cha_df["mdot_kg_s"].sum()
            if total_flow_kg_s > 0:
                specific_pump_power = (pump_power_w / 1000.0) / total_flow_kg_s
            else:
                specific_pump_power = 0.0
                
        else:
            # Fallback calculation
            pump_power_w = (cha_df.get("dp_bar", pd.Series([0])) * 1e5 *
                          (cha_df.get("v_ms", pd.Series([0])) * (3.14159*(cha_df.get("d_inner_m", pd.Series([0]))/2)**2))
                         ).sum()
            pump_efficiency = 0.75
            total_flow_kg_s = 0.0
            specific_pump_power = 0.0
        
        return {
            "pump_efficiency": pump_efficiency,
            "specific_pump_power": specific_pump_power
        }
        
    except Exception:
        return {
            "pump_efficiency": 0.75,
            "specific_pump_power": 0.0
        }

def _integrate_thermal_performance(cha_df: pd.DataFrame) -> dict:
    """
    Integrate thermal performance metrics from hydraulic simulation data.
    
    Args:
        cha_df: CHA segments DataFrame with hydraulic simulation data
        
    Returns:
        dict: Thermal performance metrics
    """
    try:
        # Check if enhanced thermal data is available
        has_thermal_data = all(col in cha_df.columns for col in 
                              ["q_loss_Wm", "length_m", "t_seg_c"])
        
        if has_thermal_data:
            # Calculate total thermal losses
            thermal_losses_w = (cha_df["q_loss_Wm"] * cha_df["length_m"]).sum()
            thermal_losses_kw = thermal_losses_w / 1000.0
            
            # Temperature drop
            supply_temp_c = cha_df["t_seg_c"].max()
            return_temp_c = cha_df["t_seg_c"].min()
            temperature_drop_k = supply_temp_c - return_temp_c
            
            # Thermal loss factor (ratio of actual to theoretical losses)
            # This could be used to assess insulation effectiveness
            theoretical_losses_w = thermal_losses_w  # For now, assume actual = theoretical
            thermal_loss_factor = 1.0
            
        else:
            # Fallback values
            thermal_losses_kw = 0.0
            temperature_drop_k = 0.0
            thermal_loss_factor = 1.0
        
        return {
            "thermal_losses_kw": thermal_losses_kw,
            "temperature_drop_k": temperature_drop_k,
            "thermal_loss_factor": thermal_loss_factor
        }
        
    except Exception:
        return {
            "thermal_losses_kw": 0.0,
            "temperature_drop_k": 0.0,
            "thermal_loss_factor": 1.0
        }

def _validate_cha_input_requirements(cha_df: pd.DataFrame, requirements: dict) -> tuple[bool, list[str]]:
    """
    Validate CHA input requirements.
    
    Args:
        cha_df: CHA segments DataFrame
        requirements: CHA input requirements configuration
        
    Returns:
        tuple: (is_valid, missing_requirements)
    """
    missing_requirements = []
    
    # Check schema validation requirement
    if requirements.get("schema_validation", False):
        # Check if enhanced hydraulic data is available
        required_cols = ["q_loss_Wm", "mdot_kg_s", "t_seg_c", "pipe_category"]
        missing_cols = [col for col in required_cols if col not in cha_df.columns]
        if missing_cols:
            missing_requirements.append(f"Missing hydraulic simulation columns: {missing_cols}")
    
    # Check required KPIs
    required_kpis = requirements.get("required_kpis", [])
    if required_kpis:
        # Calculate metrics to check if KPIs can be computed
        cha_metrics = _calculate_cha_metrics_from_hydraulics(cha_df)
        pump_metrics = _calculate_pump_efficiency_metrics(cha_df)
        thermal_metrics = _integrate_thermal_performance(cha_df)
        
        # Combine all metrics
        all_metrics = {**cha_metrics, **pump_metrics, **thermal_metrics}
        
        # Map requested KPI names to actual metric names
        kpi_mapping = {
            "v_max_ms": "max_velocity_ms",
            "dp100m_max_pa": "max_pressure_drop_pa_per_m",
            "pump_kw": "pump_kw",
            "thermal_efficiency": "thermal_efficiency"
        }
        
        missing_kpis = []
        for kpi in required_kpis:
            actual_kpi = kpi_mapping.get(kpi, kpi)
            if actual_kpi not in all_metrics:
                missing_kpis.append(kpi)
        
        if missing_kpis:
            missing_requirements.append(f"Missing required KPIs: {missing_kpis}")
    
    is_valid = len(missing_requirements) == 0
    return is_valid, missing_requirements

def _update_decision_logic_with_hydraulics(metrics: dict) -> tuple[str, list[str]]:
    """
    Update decision logic to include hydraulic and thermal performance metrics.
    
    Args:
        metrics: Dictionary containing all relevant metrics and thresholds
        
    Returns:
        tuple: (recommendation, rationale_list)
    """
    rec = "Hybrid"
    rationale = []
    
    # Extract metrics
    feeder_max_utilization_pct = metrics["feeder_max_utilization_pct"]
    max_velocity_ms = metrics["max_velocity_ms"]
    max_pressure_drop_pa_per_m = metrics["max_pressure_drop_pa_per_m"]
    thermal_efficiency = metrics["thermal_efficiency"]
    pump_efficiency = metrics["pump_efficiency"]
    specific_pump_power = metrics["specific_pump_power"]
    thermal_losses_kw = metrics["thermal_losses_kw"]
    temperature_drop_k = metrics["temperature_drop_k"]
    lcoh_mean = metrics["lcoh_mean"]
    thresholds = metrics["thresholds"]
    
    # Enhanced decision logic with hydraulic and thermal considerations
    
    # 1. Feeder utilization check (existing logic)
    if feeder_max_utilization_pct >= thresholds["feeder_utilization_warn_pct"]:
        rec = "DH"
        rationale.append(
            f"Feeder utilization {feeder_max_utilization_pct:.1f}% ≥ "
            f"{thresholds['feeder_utilization_warn_pct']}% threshold."
        )
    
    # 2. Hydraulic performance checks (using hydraulic_thresholds if available)
    hydraulic_thresholds = metrics.get("hydraulic_thresholds", {})
    if hydraulic_thresholds:
        # Use hydraulic_thresholds section
        max_velocity_threshold = hydraulic_thresholds.get("max_velocity_ms", 2.0)
        max_pressure_drop_threshold = hydraulic_thresholds.get("max_pressure_drop_pa_per_m", 500)
        min_thermal_efficiency_threshold = hydraulic_thresholds.get("min_thermal_efficiency", 0.85)
        max_pump_power_threshold = hydraulic_thresholds.get("max_pump_power_kw", 1000)
    else:
        # Fallback to main thresholds section
        max_velocity_threshold = thresholds.get("max_velocity_ms", 2.5)
        max_pressure_drop_threshold = thresholds.get("max_pressure_drop_pa_per_m", 500)
        min_thermal_efficiency_threshold = thresholds.get("min_thermal_efficiency", 0.6)
        max_pump_power_threshold = thresholds.get("max_pump_power_kw", 1000)
    
    if max_velocity_ms > max_velocity_threshold:
        if rec == "Hybrid":
            rec = "HP"  # Prefer HP if DH has hydraulic issues
        rationale.append(
            f"High velocity {max_velocity_ms:.1f} m/s > {max_velocity_threshold} m/s threshold indicates potential hydraulic issues."
        )
    
    if max_pressure_drop_pa_per_m > max_pressure_drop_threshold:
        if rec == "Hybrid":
            rec = "HP"
        rationale.append(
            f"High pressure drop {max_pressure_drop_pa_per_m:.0f} Pa/m > {max_pressure_drop_threshold} Pa/m threshold indicates system stress."
        )
    
    # 3. Thermal performance checks
    if thermal_efficiency < min_thermal_efficiency_threshold:
        if rec == "Hybrid":
            rec = "HP"
        rationale.append(
            f"Low thermal efficiency {thermal_efficiency:.2f} < {min_thermal_efficiency_threshold} threshold indicates poor heat transfer."
        )
    
    # 3.5. Pump power checks (using hydraulic_thresholds)
    pump_power_kw = metrics.get("pump_power_kw", 0)
    if pump_power_kw > max_pump_power_threshold:
        if rec == "Hybrid":
            rec = "HP"
        rationale.append(
            f"High pump power {pump_power_kw:.1f} kW > {max_pump_power_threshold} kW threshold indicates excessive energy consumption."
        )
    
    max_thermal_losses_threshold = thresholds.get("max_thermal_losses_kw", 100)
    if thermal_losses_kw > max_thermal_losses_threshold:
        if rec == "Hybrid":
            rec = "HP"
        rationale.append(
            f"High thermal losses {thermal_losses_kw:.1f} kW > {max_thermal_losses_threshold} kW threshold indicate poor insulation."
        )
    
    # 4. Pump efficiency checks
    max_specific_pump_power_threshold = thresholds.get("max_specific_pump_power_kw_per_kg_s", 2.0)
    if specific_pump_power > max_specific_pump_power_threshold:
        if rec == "Hybrid":
            rec = "HP"
        rationale.append(
            f"High specific pump power {specific_pump_power:.2f} kW/(kg/s) > {max_specific_pump_power_threshold} kW/(kg/s) threshold indicates inefficient pumping."
        )
    
    # 5. Economic considerations
    max_lcoh_threshold = thresholds.get("max_lcoh_eur_per_mwh", 500)
    if lcoh_mean > max_lcoh_threshold:
        if rec == "Hybrid":
            rec = "HP"
        rationale.append(
            f"High LCOH €{lcoh_mean:.0f}/MWh > €{max_lcoh_threshold}/MWh threshold makes DH less economically attractive."
        )
    
    # 6. Default rationale if no specific issues found
    if not rationale:
        rationale.append("Both feasible; Hybrid recommended to hedge uncertainty.")
    
    return rec, rationale

def run(config_path: str = "configs/tca.yml") -> dict:
    cfg = _read_yaml(config_path)
    paths = cfg["paths"]
    thr = cfg["thresholds"]
    kpi_out = Path(paths["kpi_out"])
    kpi_out.parent.mkdir(parents=True, exist_ok=True)

    eaa = _read_summary_csv(paths["eaa_summary"])
    cha = pd.read_csv(paths["cha_segments"])
    dha = pd.read_csv(paths["dha_feeders"])
    
    # Validate CHA input requirements if configured
    cha_input_requirements = cfg.get("cha_input_requirements", {})
    if cha_input_requirements:
        is_valid, missing_requirements = _validate_cha_input_requirements(cha, cha_input_requirements)
        if not is_valid:
            print("⚠️ CHA input validation warnings:")
            for req in missing_requirements:
                print(f"   - {req}")
            # Continue with warnings rather than failing

    # Enhanced CHA metrics from hydraulic simulation
    cha_metrics = _calculate_cha_metrics_from_hydraulics(cha)
    dh_losses_pct = cha_metrics["dh_losses_pct"]
    pump_kw = cha_metrics["pump_kw"]
    
    # Additional hydraulic metrics
    max_velocity_ms = cha_metrics["max_velocity_ms"]
    max_pressure_drop_pa_per_m = cha_metrics["max_pressure_drop_pa_per_m"]
    thermal_efficiency = cha_metrics["thermal_efficiency"]
    network_length_km = cha_metrics["network_length_km"]
    total_flow_kg_s = cha_metrics["total_flow_kg_s"]
    
    # Pump efficiency metrics
    pump_metrics = _calculate_pump_efficiency_metrics(cha)
    pump_efficiency = pump_metrics["pump_efficiency"]
    specific_pump_power = pump_metrics["specific_pump_power"]
    
    # Thermal performance metrics
    thermal_metrics = _integrate_thermal_performance(cha)
    thermal_losses_kw = thermal_metrics["thermal_losses_kw"]
    temperature_drop_k = thermal_metrics["temperature_drop_k"]
    thermal_loss_factor = thermal_metrics["thermal_loss_factor"]

    # DHA metric
    feeder_max_utilization_pct = float(pd.to_numeric(dha.get("utilization_pct", pd.Series([0])), errors="coerce").max())

    # Enhanced decision logic with hydraulic and thermal metrics
    rec, rationale = _update_decision_logic_with_hydraulics({
        "feeder_max_utilization_pct": feeder_max_utilization_pct,
        "max_velocity_ms": max_velocity_ms,
        "max_pressure_drop_pa_per_m": max_pressure_drop_pa_per_m,
        "thermal_efficiency": thermal_efficiency,
        "pump_efficiency": pump_efficiency,
        "specific_pump_power": specific_pump_power,
        "thermal_losses_kw": thermal_losses_kw,
        "temperature_drop_k": temperature_drop_k,
        "pump_power_kw": pump_kw,
        "lcoh_mean": eaa["lcoh_mean"],
        "thresholds": thr,
        "hydraulic_thresholds": cfg.get("hydraulic_thresholds", {})
    })

    obj = {
      "project_info": {
        "scenario_name": cfg.get("scenario_name","scenario"),
        "created_utc": pd.Timestamp.utcnow().isoformat(),
        "version": cfg.get("kpi_schema_version","1.0.0")
      },
      "economic_metrics": {
        "lcoh_eur_per_mwh": float(eaa["lcoh_mean"]),
        "npv_eur": 0.0,  # Placeholder - would need NPV calculation
        "capex_eur": 0.0,  # Placeholder - would need capex from EAA
        "opex_eur_per_year": 0.0,  # Placeholder - would need opex from EAA
        "payback_period_years": 0.0  # Placeholder - would need payback calculation
      },
      "technical_metrics": {
        "dh_losses_pct": float(dh_losses_pct),
        "pump_kw": float(max(pump_kw,0.0)),
        "feeder_max_utilization_pct": float(feeder_max_utilization_pct),
        "forecast_rmse": float(cfg.get("forecast_rmse", 0.12)),
        "forecast_picp_90": float(max(0.0, min(1.0, cfg.get("forecast_picp_90", 0.90)))),
        # Enhanced hydraulic metrics
        "max_velocity_ms": float(max_velocity_ms),
        "max_pressure_drop_pa_per_m": float(max_pressure_drop_pa_per_m),
        "thermal_efficiency": float(thermal_efficiency),
        "network_length_km": float(network_length_km),
        "total_flow_kg_s": float(total_flow_kg_s),
        # Pump efficiency metrics
        "pump_efficiency": float(pump_efficiency),
        "specific_pump_power_kw_per_kg_s": float(specific_pump_power),
        # Thermal performance metrics
        "thermal_losses_kw": float(thermal_losses_kw),
        "temperature_drop_k": float(temperature_drop_k),
        "thermal_loss_factor": float(thermal_loss_factor)
      },
      "recommendation": {
        "preferred_scenario": rec,
        "confidence_level": "medium",  # Default confidence level
        "rationale": "; ".join(rationale)
      },
      "sources": [
        paths["eaa_summary"],
        paths["cha_segments"],
        paths["dha_feeders"]
      ]
    }

    # Clamp & guard before writing
    obj["technical_metrics"]["forecast_picp_90"] = float(
        max(0.0, min(1.0, obj["technical_metrics"]["forecast_picp_90"]))
    )
    obj["technical_metrics"]["pump_kw"] = float(max(0.0, obj["technical_metrics"]["pump_kw"]))
    obj["technical_metrics"]["feeder_max_utilization_pct"] = float(
        max(0.0, obj["technical_metrics"]["feeder_max_utilization_pct"])
    )
    
    # Enhanced metrics validation and clamping
    obj["technical_metrics"]["max_velocity_ms"] = float(max(0.0, obj["technical_metrics"]["max_velocity_ms"]))
    obj["technical_metrics"]["max_pressure_drop_pa_per_m"] = float(max(0.0, obj["technical_metrics"]["max_pressure_drop_pa_per_m"]))
    obj["technical_metrics"]["thermal_efficiency"] = float(max(0.0, min(1.0, obj["technical_metrics"]["thermal_efficiency"])))
    obj["technical_metrics"]["network_length_km"] = float(max(0.0, obj["technical_metrics"]["network_length_km"]))
    obj["technical_metrics"]["total_flow_kg_s"] = float(max(0.0, obj["technical_metrics"]["total_flow_kg_s"]))
    obj["technical_metrics"]["pump_efficiency"] = float(max(0.0, min(1.0, obj["technical_metrics"]["pump_efficiency"])))
    obj["technical_metrics"]["specific_pump_power_kw_per_kg_s"] = float(max(0.0, obj["technical_metrics"]["specific_pump_power_kw_per_kg_s"]))
    obj["technical_metrics"]["thermal_losses_kw"] = float(max(0.0, obj["technical_metrics"]["thermal_losses_kw"]))
    obj["technical_metrics"]["temperature_drop_k"] = float(max(0.0, obj["technical_metrics"]["temperature_drop_k"]))
    obj["technical_metrics"]["thermal_loss_factor"] = float(max(0.0, obj["technical_metrics"]["thermal_loss_factor"]))

    # Validate against schema
    _validate_json(obj, cfg["kpi_schema"])

    # Write
    kpi_out.write_text(json.dumps(obj, indent=2))
    return {"kpi": str(kpi_out)}

if __name__ == "__main__":
    print(run())
