# Configuration Guide
## Agent-Based Energy System - Real Simulations

**Version:** 2.0 (With Real Physics)  
**Date:** November 2025

---

## Overview

The Agent System is now controlled by **two YAML configuration files** that allow you to:
- Toggle between real physics and placeholder simulations
- Adjust physical parameters (temperatures, voltages, etc.)
- Control performance features (caching, progress tracking)
- Set operational limits and thresholds

---

## Configuration Files

### 1. Feature Flags (`config/feature_flags.yaml`)

**Purpose:** Control which features are enabled/disabled

**Location:** `config/feature_flags.yaml`

#### Master Switches

```yaml
features:
  use_real_simulations: false  # ← MASTER SWITCH
  # Set to true to enable real pandapipes/pandapower
  # Set to false to use fast placeholders
```

#### Individual Simulation Toggles

```yaml
  use_real_dh: true     # Enable real DH when master switch is ON
  use_real_hp: false    # Enable real HP when master switch is ON
  # Allows staged deployment: turn on DH first, then HP later
```

#### Performance Features

```yaml
  enable_caching: true          # Cache simulation results (future)
  cache_ttl_hours: 24           # Cache validity period
  
  enable_progress_tracking: true  # Show progress during simulation
  enable_parallel_execution: false  # Run multiple streets at once (future)
```

#### Error Handling

```yaml
  fallback_on_error: true   # If real simulation fails, use placeholder
  strict_mode: false        # If true, fail fast without fallback
```

#### Logging

```yaml
logging:
  level: "INFO"              # DEBUG, INFO, WARNING, ERROR
  log_simulations: true      # Log detailed simulation steps
  log_cache_operations: true # Log cache hits/misses
```

---

### 2. Simulation Parameters (`config/simulation_config.yaml`)

**Purpose:** Set physical and technical parameters

**Location:** `config/simulation_config.yaml`

#### District Heating Configuration

```yaml
district_heating:
  # Temperature settings
  supply_temp_c: 85.0        # Supply temperature (°C)
  return_temp_c: 55.0        # Return temperature (°C)
  # Typical range: 70-95°C supply, 40-60°C return
  
  network:
    pipe_roughness_mm: 0.1   # Steel pipe roughness (mm)
    default_diameter_m: 0.065  # Pipe diameter (m) - DN65
    insulation_thickness_mm: 30
    ambient_temp_c: 10       # Ground temperature (°C)
    
  plant:
    supply_pressure_bar: 6.0  # Plant supply pressure (bar)
    min_pressure_bar: 2.0     # Minimum required pressure
    pump_efficiency: 0.75     # Pump efficiency (0-1)
  
  simulation:
    solver: "pipeflow"        # pandapipes solver
    mode: "all"               # "hydraulic", "thermal", or "all"
    max_iterations: 100
    tolerance: 1.0e-6
```

#### Heat Pump Configuration

```yaml
heat_pump:
  # Heat pump specifications
  hp_thermal_kw: 6.0         # Thermal power per building (kW)
  hp_cop: 2.8                # Coefficient of Performance
  hp_three_phase: true       # 3-phase balanced vs single-phase
  
  grid:
    mv_voltage_kv: 20.0      # Medium voltage (kV)
    lv_voltage_kv: 0.4       # Low voltage (kV)
    transformer_mva: 0.63    # Transformer capacity (MVA)
  
  cables:
    default_type: "NAYY 4x150 SE"  # Standard LV cable
    max_length_m: 500
  
  limits:
    voltage_min_pu: 0.90     # Minimum voltage (per-unit)
    voltage_max_pu: 1.10     # Maximum voltage
    line_loading_max_pct: 100.0  # Maximum line loading (%)
  
  simulation:
    solver: "nr"             # Newton-Raphson
    use_3ph: true            # Use 3-phase solver
    max_iterations: 100
```

#### Validation Rules

```yaml
validation:
  min_buildings: 2           # Minimum buildings for simulation
  max_buildings: 500         # Maximum (performance limit)
  
  dh:
    min_heat_demand_kw: 1.0
    max_heat_demand_kw: 500.0
  
  hp:
    min_base_load_kw: 0.5
    max_total_load_mw: 2.0
```

---

## Common Configuration Scenarios

### Scenario 1: Enable Real Simulations (Production)

```yaml
# config/feature_flags.yaml
features:
  use_real_simulations: true   # ← Turn ON
  use_real_dh: true
  use_real_hp: true
  fallback_on_error: true      # Keep fallback for safety
```

**Result:** All simulations use real physics

### Scenario 2: Development/Testing (Fast)

```yaml
# config/feature_flags.yaml
features:
  use_real_simulations: false  # ← Keep OFF
```

**Result:** Fast placeholder simulations for quick testing

### Scenario 3: DH Only (Staged Rollout)

```yaml
# config/feature_flags.yaml
features:
  use_real_simulations: true
  use_real_dh: true
  use_real_hp: false  # ← HP still uses placeholder
```

**Result:** Real DH, placeholder HP

### Scenario 4: Higher DH Temperatures

```yaml
# config/simulation_config.yaml
district_heating:
  supply_temp_c: 95.0  # ← Increase from 85°C
  return_temp_c: 60.0  # ← Increase from 55°C
```

**Result:** Simulations use higher temperature differential

### Scenario 5: Stricter Voltage Limits

```yaml
# config/simulation_config.yaml
heat_pump:
  limits:
    voltage_min_pu: 0.95  # ← Stricter (was 0.90)
    voltage_max_pu: 1.05  # ← Stricter (was 1.10)
```

**Result:** More voltage violations detected

---

## Configuration Priority

When parameters are specified in multiple places, the priority is:

```
1. Scenario JSON params (highest)
   ↓
2. simulation_config.yaml
   ↓
3. Code defaults (lowest)
```

**Example:**

```python
# Code default: supply_temp_c = 85
# config/simulation_config.yaml: supply_temp_c: 90
# scenario.json params: {"supply_temp": 95}
# 
# Result: Uses 95°C (scenario overrides config file)
```

---

## Advanced Configuration

### Adjusting Solver Parameters

For difficult networks that don't converge:

```yaml
# config/simulation_config.yaml
district_heating:
  simulation:
    max_iterations: 200      # ← Increase from 100
    tolerance: 1.0e-5        # ← Relax from 1e-6
```

### Adjusting Performance

```yaml
# config/feature_flags.yaml
performance:
  cache_directory: "simulation_cache"
  max_cache_size_mb: 2000    # Increase cache size
  
  timeouts:
    simulation_s: 600        # Increase timeout for large networks
```

### Debug Mode

```yaml
# config/feature_flags.yaml
logging:
  level: "DEBUG"             # ← Change from INFO
  log_simulations: true
  
development:
  save_networks: true        # Save network objects for inspection
  export_debug_data: true    # Export intermediate results
```

---

## Troubleshooting

### Issue: "Using PLACEHOLDER simulation" but you want REAL

**Solution:**
```yaml
# config/feature_flags.yaml
features:
  use_real_simulations: true  # ← Set to true
```

### Issue: Simulation convergence failures

**Solution 1 - Enable fallback:**
```yaml
fallback_on_error: true  # Auto-switches to placeholder
```

**Solution 2 - Adjust solver:**
```yaml
district_heating:
  simulation:
    max_iterations: 200
    tolerance: 1.0e-5
```

### Issue: Simulations too slow

**Solution:**
```yaml
# Use placeholders for testing
use_real_simulations: false

# Or enable caching (when implemented)
enable_caching: true
```

### Issue: Missing pandapipes/pandapower

**Solution:**
```bash
conda activate branitz_env
pip install pandapipes pandapower
```

**Or:** System automatically uses placeholders if libraries missing

---

## Configuration Best Practices

### 1. Start with Defaults
- Use provided `feature_flags.yaml` and `simulation_config.yaml`
- Don't modify unless you have a specific reason

### 2. Staged Rollout
```
Step 1: Test with placeholders (use_real_simulations: false)
Step 2: Enable DH only (use_real_dh: true, use_real_hp: false)
Step 3: Enable HP (use_real_hp: true)
Step 4: Production (all real)
```

### 3. Keep Fallback Enabled
```yaml
fallback_on_error: true  # Always keep this ON for robustness
```

### 4. Adjust Parameters Gradually
- Change one parameter at a time
- Test after each change
- Document why you changed it

### 5. Version Control
```bash
# Commit your config changes
git add config/*.yaml
git commit -m "Update DH supply temp to 90°C"
```

---

## Parameter Reference

### District Heating Typical Values

| Parameter | Typical Range | Default | Notes |
|-----------|--------------|---------|-------|
| `supply_temp_c` | 70-95°C | 85°C | Higher = more losses |
| `return_temp_c` | 40-60°C | 55°C | Lower = better efficiency |
| `supply_pressure_bar` | 4-8 bar | 6 bar | Depends on network size |
| `pipe_roughness_mm` | 0.05-0.5 mm | 0.1 mm | Steel = 0.1, PEX = 0.007 |

### Heat Pump Typical Values

| Parameter | Typical Range | Default | Notes |
|-----------|--------------|---------|-------|
| `hp_thermal_kw` | 4-12 kW | 6 kW | Per building |
| `hp_cop` | 2.5-4.0 | 2.8 | Lower in winter |
| `voltage_min_pu` | 0.85-0.95 | 0.90 | European standard: ±10% |
| `line_loading_max_pct` | 80-100% | 100% | Conservative: 80% |

---

## Configuration Examples

### Example 1: Low-Temperature District Heating

```yaml
# config/simulation_config.yaml
district_heating:
  supply_temp_c: 70.0  # Low-temp network
  return_temp_c: 40.0
```

### Example 2: High-COP Heat Pumps (Summer)

```yaml
# config/simulation_config.yaml
heat_pump:
  hp_cop: 4.0  # Better performance in summer
```

### Example 3: Conservative Electrical Limits

```yaml
# config/simulation_config.yaml
heat_pump:
  limits:
    voltage_min_pu: 0.95
    voltage_max_pu: 1.05
    line_loading_max_pct: 80.0  # 80% instead of 100%
```

---

## See Also

- `ARCHITECTURE_DESIGN.md` - System architecture
- `docs/INTERFACE_SPEC.md` - Technical specifications
- `IMPLEMENTATION_STATUS.md` - Current implementation status

---

**Last Updated:** November 2025  
**Version:** 2.0 (Real Simulations Edition)

