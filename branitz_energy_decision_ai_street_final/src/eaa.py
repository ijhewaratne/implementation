from __future__ import annotations
import json, math, os, glob
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd

@dataclass
class EAAConfig:
    n_samples: int = 1000
    seed: int = 42
    cp_water_j_per_kgk: float = 4180
    delta_t_k: float = 30
    design_full_load_hours: float = 2000
    discount_rate: float = 0.06
    lifetime_years: int = 25
    pump_efficiency: float = 0.75
    elec_price_eur_per_kwh: float = 0.22
    grid_co2_kg_per_kwh: float = 0.35
    capex_per_m_eur: dict | None = None
    opex_fraction_of_capex: float = 0.02
    om_fixed_eur_per_mwh: float = 4.0
    annual_heat_mwh_fallback: float = 10000.0
    paths: dict | None = None
    
    # Hydraulic integration settings
    hydraulic_integration: dict | None = None
    cha_input_validation: dict | None = None
    economic_analysis: dict | None = None

def _annuity_factor(r: float, n: int) -> float:
    return (r * (1 + r) ** n) / (((1 + r) ** n) - 1)

def _read_yaml(p: str) -> dict:
    import yaml
    return yaml.safe_load(Path(p).read_text())

def _annual_heat_from_lfa(lfa_dir: str) -> float | None:
    files = sorted(glob.glob(os.path.join(lfa_dir, "*.json")))
    if not files:
        return None
    total_kwh = 0.0
    for f in files:
        try:
            data = json.loads(Path(f).read_text())
            series = data.get("series") or []
            total_kwh += float(np.nansum(series))
        except Exception:
            continue
    return total_kwh / 1000.0  # → MWh

def _validate_cha_hydraulic_output(cha_df: pd.DataFrame, config: dict = None) -> bool:
    """
    Validate CHA hydraulic output format and data quality.
    
    Args:
        cha_df: CHA segments DataFrame with hydraulic simulation results
        config: Validation configuration dictionary
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    try:
        # Get validation configuration
        validation_config = config or {}
        validate_ranges = validation_config.get("validate_data_ranges", True)
        validate_categories = validation_config.get("validate_pipe_categories", True)
        required_columns = validation_config.get("required_columns", [
            "length_m", "d_inner_m", "v_ms", "dp_bar", "q_loss_Wm", 
            "mdot_kg_s", "t_seg_c", "pipe_category"
        ])
        
        # Check required columns
        required_cols = set(required_columns)
        if not required_cols.issubset(cha_df.columns):
            return False
        
        # Check data types and ranges if enabled
        if validate_ranges:
            if not (cha_df["length_m"] > 0).all():
                return False
            if not (cha_df["d_inner_m"] > 0).all():
                return False
            if not (cha_df["v_ms"] >= 0).all():
                return False
            if not (cha_df["dp_bar"] >= 0).all():
                return False
            if not (cha_df["q_loss_Wm"] >= 0).all():
                return False
            if not (cha_df["mdot_kg_s"] >= 0).all():
                return False
            if not (cha_df["t_seg_c"] > 0).all():
                return False
        
        # Check pipe categories if enabled
        if validate_categories:
            valid_categories = {"mains", "distribution", "services"}
            if not set(cha_df["pipe_category"]).issubset(valid_categories):
                return False
        
        return True
        
    except Exception:
        return False

def _calculate_enhanced_pump_power(cha_df: pd.DataFrame, cfg: EAAConfig) -> float:
    """
    Calculate enhanced pump power using hydraulic simulation data.
    
    Formula: P_pump = Σ(Δp_i · V_dot_i) / η
    where:
    - P_pump = pump power (W)
    - Δp_i = pressure drop in pipe i (Pa)
    - V_dot_i = volumetric flow rate in pipe i (m³/s)
    - η = pump efficiency
    
    Args:
        cha_df: CHA segments DataFrame with hydraulic data
        cfg: EAA configuration
        
    Returns:
        float: Total pump power in watts
    """
    try:
        # Get hydraulic integration configuration
        hydraulic_config = cfg.hydraulic_integration or {}
        use_actual_pump_power = hydraulic_config.get("use_actual_pump_power", True)
        pump_efficiency = hydraulic_config.get("pump_efficiency", cfg.pump_efficiency)
        water_density_kg_m3 = hydraulic_config.get("water_density_kg_m3", 977.8)
        
        # Method 1: Use mass flow rate and pressure drop directly (if enabled)
        if use_actual_pump_power and "mdot_kg_s" in cha_df.columns and "dp_bar" in cha_df.columns:
            # Convert pressure drop from bar to Pa
            dp_pa = cha_df["dp_bar"] * 1e5
            
            # Calculate volumetric flow rate: V_dot = m_dot / ρ
            volumetric_flow_m3s = cha_df["mdot_kg_s"] / water_density_kg_m3
            
            # Calculate hydraulic power: P_hydraulic = Δp · V_dot
            hydraulic_power_W = (dp_pa * volumetric_flow_m3s).clip(lower=0).sum()
            
            # Calculate pump power: P_pump = P_hydraulic / η
            pump_power_W = hydraulic_power_W / max(pump_efficiency, 1e-6)
            
            return float(pump_power_W)
        
        # Method 2: Fallback to original calculation
        elif {"v_ms", "d_inner_m", "dp_bar"}.issubset(cha_df.columns):
            area = math.pi * (cha_df["d_inner_m"] / 2) ** 2
            flow_m3s = cha_df["v_ms"] * area
            dp_pa = cha_df["dp_bar"] * 1e5
            hydraulic_power_W = (dp_pa * flow_m3s).clip(lower=0).sum()
            pump_power_W = hydraulic_power_W / max(pump_efficiency, 1e-6)
            return float(pump_power_W)
        
        else:
            return 0.0
            
    except Exception:
        return 0.0

def _calculate_thermal_losses(cha_df: pd.DataFrame, cfg: EAAConfig = None) -> float:
    """
    Calculate total thermal losses from hydraulic simulation data.
    
    Formula: Q_loss = Σ(q_loss_Wm_i · length_m_i) · thermal_loss_factor
    where:
    - Q_loss = total thermal loss (W)
    - q_loss_Wm_i = thermal loss per meter for pipe i
    - length_m_i = length of pipe i
    - thermal_loss_factor = configuration factor for thermal losses
    
    Args:
        cha_df: CHA segments DataFrame with thermal data
        cfg: EAA configuration
        
    Returns:
        float: Total thermal losses in watts
    """
    try:
        # Get hydraulic integration configuration
        hydraulic_config = cfg.hydraulic_integration if cfg else {}
        use_thermal_losses = hydraulic_config.get("use_thermal_losses", True)
        thermal_loss_factor = hydraulic_config.get("thermal_loss_factor", 1.0)
        
        if use_thermal_losses and "q_loss_Wm" in cha_df.columns and "length_m" in cha_df.columns:
            # Calculate total thermal loss: Q_loss = Σ(q_loss_Wm · length_m) · factor
            total_thermal_loss_W = (cha_df["q_loss_Wm"] * cha_df["length_m"]).sum() * thermal_loss_factor
            return float(total_thermal_loss_W)
        else:
            return 0.0
            
    except Exception:
        return 0.0

def _integrate_hydraulic_kpis(cha_df: pd.DataFrame, cfg: EAAConfig = None) -> dict:
    """
    Integrate hydraulic KPIs from CHA simulation data.
    
    Args:
        cha_df: CHA segments DataFrame with hydraulic data
        cfg: EAA configuration
        
    Returns:
        dict: Hydraulic KPIs including max velocity, pressure drop, thermal efficiency
    """
    try:
        # Get configuration
        hydraulic_config = cfg.hydraulic_integration if cfg else {}
        ground_temperature_c = hydraulic_config.get("ground_temperature_c", 10.0)
        
        kpis = {}
        
        # Maximum velocity
        if "v_ms" in cha_df.columns:
            kpis["v_max_ms"] = float(cha_df["v_ms"].max())
        
        # Maximum pressure drop per 100m
        if "dp_bar" in cha_df.columns and "length_m" in cha_df.columns:
            # Convert to Pa per 100m
            dp_pa_per_100m = (cha_df["dp_bar"] * 1e5) / (cha_df["length_m"] / 100.0)
            kpis["dp100m_max_pa"] = float(dp_pa_per_100m.max())
        
        # Thermal efficiency calculation
        if "t_seg_c" in cha_df.columns:
            supply_temp_c = cha_df["t_seg_c"].max()
            return_temp_c = cha_df["t_seg_c"].min()
            temp_drop_c = supply_temp_c - return_temp_c
            
            # Thermal efficiency = (supply_temp - return_temp) / (supply_temp - ground_temp)
            if supply_temp_c > ground_temperature_c:
                thermal_efficiency = temp_drop_c / (supply_temp_c - ground_temperature_c)
                kpis["thermal_efficiency"] = float(min(thermal_efficiency, 1.0))
            else:
                kpis["thermal_efficiency"] = 0.0
        
        # Total mass flow rate
        if "mdot_kg_s" in cha_df.columns:
            kpis["total_flow_kg_s"] = float(cha_df["mdot_kg_s"].sum())
        
        # Network length
        if "length_m" in cha_df.columns:
            kpis["network_length_km"] = float(cha_df["length_m"].sum() / 1000.0)
        
        # Temperature drop
        if "t_seg_c" in cha_df.columns:
            kpis["dt_k"] = float(cha_df["t_seg_c"].max() - cha_df["t_seg_c"].min())
        
        return kpis
        
    except Exception:
        return {}

def run(config_path: str = "configs/eaa.yml") -> dict:
    cfgd = _read_yaml(config_path)
    cfg = EAAConfig(**cfgd, **{})  # dataclass init

    paths = cfg.paths or {}
    cha_csv = paths.get("cha_segments", "processed/cha/segments.csv")
    dha_csv = paths.get("dha_feeders", "processed/dha/feeder_loads.csv")
    lfa_dir = paths.get("lfa_dir", "processed/lfa")
    out_mc = paths.get("out_mc", "eval/te/mc.parquet")
    out_summary = paths.get("out_summary", "eval/te/summary.csv")
    Path(out_mc).parent.mkdir(parents=True, exist_ok=True)
    Path(out_summary).parent.mkdir(parents=True, exist_ok=True)

    # --- Inputs (join) ---
    df_cha = pd.read_csv(cha_csv)
    df_dha = pd.read_csv(dha_csv)
    
    # Get validation configuration
    validation_config = cfg.cha_input_validation or {}
    validate_before_processing = validation_config.get("validate_before_processing", True)
    fail_on_validation_error = validation_config.get("fail_on_validation_error", True)
    
    # Fail-fast contract checks - Enhanced for hydraulic simulation
    required_cha = {"length_m", "d_inner_m", "v_ms", "dp_bar", "q_loss_Wm", 
                   "mdot_kg_s", "t_seg_c", "pipe_category"}
    missing_cha = required_cha - set(df_cha.columns)
    if missing_cha:
        raise ValueError(f"CHA segments missing columns: {sorted(missing_cha)}")
    
    # Validate CHA hydraulic output format if enabled
    if validate_before_processing:
        validation_result = _validate_cha_hydraulic_output(df_cha, validation_config)
        if not validation_result and fail_on_validation_error:
            raise ValueError("CHA hydraulic output validation failed")
        elif not validation_result:
            print("⚠️ CHA hydraulic output validation failed, continuing with warnings")

    required_dha = {"utilization_pct"}
    missing_dha = required_dha - set(df_dha.columns)
    if missing_dha:
        raise ValueError(f"DHA feeder loads missing columns: {sorted(missing_dha)}")

    # Enhanced pumping energy calculation with hydraulic simulation data
    pump_power_W = _calculate_enhanced_pump_power(df_cha, cfg)

    # Calculate thermal losses from hydraulic simulation
    thermal_losses_kw = _calculate_thermal_losses(df_cha, cfg)
    
    # Annualize pumping energy (design hour → rough scaling)
    # If you later store hourly sums, replace this with measured kWh.
    flh = float(cfgd.get("design_full_load_hours", 2000))
    annual_pumping_kwh = (pump_power_W / 1000.0) * flh
    annual_thermal_losses_mwh = (thermal_losses_kw / 1000.0) * flh

    # Capex proxy: length * unit cost by diameter band
    def unit_cost(d_m: float) -> float:
        ce = cfg.capex_per_m_eur or {}
        if d_m < 0.10:  return ce.get("lt_0_100mm", ce.get("default", 450))
        if d_m < 0.20:  return ce.get("lt_0_200mm", ce.get("default", 450))
        return ce.get("gte_0_200mm", ce.get("default", 450))

    if "length_m" in df_cha.columns and "d_inner_m" in df_cha.columns:
        capex_eur = float((df_cha["length_m"] * df_cha["d_inner_m"].apply(unit_cost)).sum())
    else:
        capex_eur = 0.0

    # Opex (excluding pumping elec): fraction of capex + fixed €/MWh
    opex_eur_per_yr_fixed = capex_eur * cfg.opex_fraction_of_capex
    
    # Enhanced economic analysis with thermal losses and hydraulic factors
    economic_config = cfg.economic_analysis or {}
    include_thermal_losses = economic_config.get("include_thermal_losses", True)
    include_hydraulic_kpis = economic_config.get("include_hydraulic_kpis", True)
    thermal_loss_cost_eur_per_mwh = economic_config.get("thermal_loss_cost_eur_per_mwh", 0.15)
    pump_maintenance_factor = economic_config.get("pump_maintenance_factor", 0.05)
    
    # Calculate additional costs from thermal losses
    thermal_loss_cost_eur_per_yr = 0.0
    if include_thermal_losses and annual_thermal_losses_mwh > 0:
        thermal_loss_cost_eur_per_yr = annual_thermal_losses_mwh * thermal_loss_cost_eur_per_mwh
    
    # Calculate pump maintenance costs
    pump_maintenance_cost_eur_per_yr = 0.0
    if pump_power_W > 0:
        # Estimate pump cost based on power (rough estimate: €1000/kW)
        pump_cost_eur = (pump_power_W / 1000.0) * 1000.0
        pump_maintenance_cost_eur_per_yr = pump_cost_eur * pump_maintenance_factor
    
    # Integrate hydraulic KPIs for enhanced analysis
    hydraulic_kpis = _integrate_hydraulic_kpis(df_cha, cfg)
    
    # Annual heat (MWh) - robust derivation
    ann_mwh = _annual_heat_from_lfa(lfa_dir)
    if not ann_mwh:
        ann_mwh = cfg.annual_heat_mwh_fallback
    annual_heat_mwh = ann_mwh

    # --- Monte Carlo (vectorized) ---
    np.random.seed(cfg.seed)
    n = int(cfg.n_samples)

    # Sample multipliers (mild lognormal uncertainty)
    capex_mult = np.random.lognormal(mean=0.0, sigma=0.15, size=n)
    elec_price = np.random.lognormal(mean=np.log(cfg.elec_price_eur_per_kwh), sigma=0.10, size=n)
    grid_ci = np.random.lognormal(mean=np.log(cfg.grid_co2_kg_per_kwh), sigma=0.10, size=n)

    ann_fac = _annuity_factor(cfg.discount_rate, cfg.lifetime_years)
    ann_capex = capex_eur * ann_fac * capex_mult
    pumping_cost = annual_pumping_kwh * elec_price
    opex_fixed = opex_eur_per_yr_fixed + (cfg.om_fixed_eur_per_mwh * annual_heat_mwh)
    
    # Add enhanced costs
    thermal_loss_cost = thermal_loss_cost_eur_per_yr
    pump_maintenance_cost = pump_maintenance_cost_eur_per_yr
    total_opex = opex_fixed + thermal_loss_cost + pump_maintenance_cost

    lcoh_eur_per_mwh = (ann_capex + pumping_cost + total_opex) / max(annual_heat_mwh, 1e-9)
    co2_kg_per_mwh = (annual_pumping_kwh * grid_ci) / max(annual_heat_mwh, 1e-9)

    mc = pd.DataFrame({
        "lcoh_eur_per_mwh": lcoh_eur_per_mwh,
        "co2_kg_per_mwh": co2_kg_per_mwh,
    })
    # write MC
    try:
        Path(out_mc).parent.mkdir(parents=True, exist_ok=True)
        mc.to_parquet(out_mc, index=False)
    except Exception:
        # fallback if pyarrow missing
        mc.to_csv(Path(out_mc).with_suffix(".csv"), index=False)

    # Enhanced summary with hydraulic data and new costs
    def p(x, q): return float(np.percentile(x, q))
    summary = pd.DataFrame({
        "metric": ["lcoh_eur_per_mwh","co2_kg_per_mwh"],
        "mean": [float(np.mean(lcoh_eur_per_mwh)), float(np.mean(co2_kg_per_mwh))],
        "median": [float(np.median(lcoh_eur_per_mwh)), float(np.median(co2_kg_per_mwh))],
        "p2_5": [p(lcoh_eur_per_mwh,2.5), p(co2_kg_per_mwh,2.5)],
        "p97_5": [p(lcoh_eur_per_mwh,97.5), p(co2_kg_per_mwh,97.5)],
        "annual_pumping_kwh": [annual_pumping_kwh, annual_pumping_kwh],
        "annual_heat_mwh": [annual_heat_mwh, annual_heat_mwh],
        "annual_thermal_losses_mwh": [annual_thermal_losses_mwh, annual_thermal_losses_mwh],
        "pump_power_kw": [pump_power_W/1000.0, pump_power_W/1000.0],
        "thermal_losses_kw": [thermal_losses_kw, thermal_losses_kw],
        "max_velocity_ms": [hydraulic_kpis.get("v_max_ms", 0), hydraulic_kpis.get("v_max_ms", 0)],
        "max_pressure_drop_pa_per_m": [hydraulic_kpis.get("dp100m_max_pa", 0), hydraulic_kpis.get("dp100m_max_pa", 0)],
        "thermal_efficiency": [hydraulic_kpis.get("thermal_efficiency", 0), hydraulic_kpis.get("thermal_efficiency", 0)],
        "thermal_loss_cost_eur_per_yr": [thermal_loss_cost_eur_per_yr, thermal_loss_cost_eur_per_yr],
        "pump_maintenance_cost_eur_per_yr": [pump_maintenance_cost_eur_per_yr, pump_maintenance_cost_eur_per_yr],
        "total_enhanced_opex_eur_per_yr": [total_opex, total_opex]
    })
    summary.to_csv(out_summary, index=False)

    # feeder utilization (for TCA later)
    feeder_max_util_pct = float(pd.to_numeric(df_dha.get("utilization_pct", pd.Series([0])), errors="coerce").max())
    return {
        "out_mc": str(out_mc),
        "out_summary": str(out_summary),
        "feeder_max_utilization_pct": feeder_max_util_pct,
        "hydraulic_kpis": hydraulic_kpis,
        "pump_power_kw": pump_power_W / 1000.0,
        "thermal_losses_kw": thermal_losses_kw,
        "annual_thermal_losses_mwh": annual_thermal_losses_mwh,
        "thermal_loss_cost_eur_per_yr": thermal_loss_cost_eur_per_yr,
        "pump_maintenance_cost_eur_per_yr": pump_maintenance_cost_eur_per_yr,
        "total_enhanced_opex_eur_per_yr": total_opex,
        "enhanced_lcoh_eur_per_mwh": float(np.mean(lcoh_eur_per_mwh)),
        "enhanced_co2_kg_per_mwh": float(np.mean(co2_kg_per_mwh))
    }

if __name__ == "__main__":
    print(run())
