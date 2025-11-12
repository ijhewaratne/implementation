# Quick Start Guide
## Agent-Based Energy System with Real Simulations

**Ready in 5 minutes!** ⏱️

---

## Step 1: Activate Environment (30 seconds)

```bash
conda activate branitz_env
cd branitz_energy_decision_ai_street_agents
```

---

## Step 2: Install Dependencies (2 minutes)

```bash
# Required for real simulations
pip install pandapipes pandapower geopandas shapely pyyaml

# Should see:
# Successfully installed pandapipes-x.x.x pandapower-x.x.x ...
```

**Already installed?** Skip this step!

---

## Step 3: Choose Your Mode (10 seconds)

### Option A: **Fast Testing** (Uses Placeholders)

```bash
# No changes needed!
# Default config uses placeholders (instant results)
```

### Option B: **Real Physics** (Recommended)

```bash
# Edit: config/feature_flags.yaml
# Line 7: Change from
use_real_simulations: false

# To:
use_real_simulations: true
```

**Save the file.**

---

## Step 4: Run the System (30 seconds)

```bash
python run_agent_system.py
```

You should see:

```
============================================================
BRANITZ ENERGY DECISION AI - AGENT SYSTEM
============================================================

Available commands:
  analyze district heating for [street]
  analyze heat pumps for [street]
  compare scenarios for [street]
  show available streets
  show results

🎯 Your request:
```

---

## Step 5: Test with Example (1 minute)

Type:
```
show available streets
```

You'll see 27 streets. Then try:

```
analyze district heating for Parkstraße
```

### Expected Output (Real Mode):

```
🤔 Planner Agent is thinking...
🎯 Planner delegated to CentralHeatingAgent.

⚡ CentralHeatingAgent is executing your request...
TOOL: Searching for buildings on 'Parkstraße'...
TOOL: Found 15 buildings.

Running DH simulation: Parkstrasse_DH_85C
============================================================
  → Using REAL pandapipes simulation  ← Real physics!
  Loading buildings from: results_test/buildings_prepared.geojson
  Loaded 15 buildings
  Supply temp: 85°C, Return temp: 55°C
  Validating inputs...
  Creating network...
    Total heat demand: 1,234.5 kW
    Selected heat source: Building B042
    Network created: 32 junctions, 30 pipes, 14 heat exchangers
  Running simulation...
    Running pandapipes simulation (hydraulic + thermal)...
    Simulation converged successfully!
  ✅ Simulation complete: 12.3s

📊 CentralHeatingAgent Response:
District Heating Analysis Complete for Parkstraße

KEY FINDINGS:
• Total heat demand: 234.5 MWh/year
• Network: 30 pipes (1.2 km total)
• Maximum pressure drop: 0.42 bar
• Pump energy: 4,823 kWh/year
• Supply temperature: 82-85°C

RECOMMENDATION:
District heating is technically feasible.
Expected LCoH: €95/MWh
CO2 emissions: 45 tons/year

✅ Request completed successfully!
```

### Expected Output (Placeholder Mode):

```
→ Using PLACEHOLDER simulation  ← Fast estimates
  Placeholder: 15 buildings, 1234.5 kW total demand
⚠️  Warning: Using placeholder - results are estimates only!
```

---

## Troubleshooting

### "Using PLACEHOLDER" but I want REAL

**Check:** `config/feature_flags.yaml` line 7
- Must be: `use_real_simulations: true`
- Save file and restart system

### "pandapipes not found"

**Install:**
```bash
conda activate branitz_env
pip install pandapipes pandapower
```

### Simulation fails / errors

**Solution:** System automatically falls back to placeholder
- Check warnings in output
- See logs for details

---

## What's Next?

### Analyze Your Streets

```
analyze district heating for Liebermannstraße
analyze heat pumps for Petzoldstraße
compare scenarios for Parkstraße
```

### Explore Results

```
show results
```

Shows all generated files:
- `scenario_kpis.csv` - Performance indicators
- `llm_report.md` - AI-generated analysis
- `*.geojson` - Network visualizations
- `*.png` - Network maps

### Configure Parameters

Edit `config/simulation_config.yaml`:

```yaml
district_heating:
  supply_temp_c: 90  # Try higher temperature
  
heat_pump:
  hp_thermal_kw: 8.0  # Try larger heat pumps
  hp_cop: 3.5         # Try better COP
```

---

## Advanced Usage

### Run Tests

```bash
# Unit tests
python tests/unit/test_dh_simulator.py
python tests/unit/test_hp_simulator.py

# Integration tests
python tests/integration/test_full_agent_workflow.py
```

### Direct Simulation (Without Agents)

```python
from src.simulators import DistrictHeatingSimulator
import geopandas as gpd

buildings = gpd.read_file("buildings.geojson")

config = {"supply_temp_c": 85, "return_temp_c": 55}
sim = DistrictHeatingSimulator(config)

sim.validate_inputs(buildings)
sim.create_network(buildings)
result = sim.run_simulation()

print(f"Heat: {result.kpi['total_heat_supplied_mwh']} MWh")
```

---

## Key Files

| File | Purpose |
|------|---------|
| `config/feature_flags.yaml` | Toggle real/placeholder |
| `config/simulation_config.yaml` | Physical parameters |
| `run_agent_system.py` | Main entry point |
| `src/simulation_runner.py` | Simulation execution |
| `README.md` | Full documentation |
| `docs/CONFIGURATION_GUIDE.md` | Detailed config help |

---

## Quick Reference

### Commands
```bash
conda activate branitz_env          # Activate environment
python run_agent_system.py          # Start system
python tests/unit/test_dh_simulator.py  # Test DH
python tests/unit/test_hp_simulator.py  # Test HP
```

### Configuration
```yaml
# Toggle real/placeholder
config/feature_flags.yaml → use_real_simulations: true/false

# Adjust parameters
config/simulation_config.yaml → supply_temp_c, hp_thermal_kw, etc.
```

### Results
```
simulation_outputs/  # Detailed results (JSON)
results_test/        # KPIs, reports, visualizations
```

---

**That's it! You're ready to go!** 🚀

For detailed information, see:
- `README.md` - Full documentation
- `docs/CONFIGURATION_GUIDE.md` - Configuration reference
- `ARCHITECTURE_DESIGN.md` - System design

**Need help?** Check `docs/` directory or run tests to verify setup.

