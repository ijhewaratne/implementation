# System Outputs Guide
## Complete Reference for All Output Files and Locations

**Last Updated:** November 2025  
**System Version:** 2.0 (Real Simulations + Enhancements)

---

## 📁 Output Directory Structure

```
branitz_energy_decision_ai_street_agents/
│
├── 📂 simulation_outputs/          ← Raw simulation results (JSON)
│   ├── {scenario_name}_results.json
│   └── ...
│
├── 📂 results_test/                ← Pipeline outputs (main results)
│   ├── 📊 KPIs and Reports
│   ├── 🗺️ GeoJSON Files
│   ├── 📈 Visualizations
│   └── 🔧 Intermediate Files
│
├── 📂 results/                     ← Production results (when using full dataset)
│   └── (same structure as results_test)
│
├── 📂 simulation_cache/            ← Cached simulation results
│   ├── dh/                         ← DH cache files
│   └── hp/                         ← HP cache files
│
├── 📂 scenarios/                   ← Scenario configuration files
│   └── {scenario}.json
│
└── 📂 reports/                     ← Legacy reports
    └── llm_report.md
```

---

## 📊 Output File Types & Purposes

### 1. Simulation Results (simulation_outputs/)

**Location:** `simulation_outputs/`

**Files Generated:**
```
{scenario_name}_results.json         ← Main simulation output
```

**Format:** JSON

**Content Example:**
```json
{
  "success": true,
  "scenario": "Parkstrasse_DH_85C",
  "type": "DH",
  "mode": "real",
  "kpi": {
    "total_heat_supplied_mwh": 234.5,
    "peak_heat_load_kw": 1234.5,
    "max_pressure_drop_bar": 0.42,
    "avg_pressure_drop_bar": 0.28,
    "pump_energy_kwh": 4823,
    "min_supply_temp_c": 82.3,
    "avg_supply_temp_c": 84.1,
    "network_heat_loss_kwh": 23.4,
    "heat_loss_percentage": 10.0,
    "num_junctions": 32,
    "num_pipes": 30,
    "num_consumers": 15,
    "total_pipe_length_km": 1.2
  },
  "metadata": {
    "num_consumers": 15,
    "heat_source_building": "B042",
    "total_demand_kw": 1234.5,
    "supply_temp_c": 85.0,
    "return_temp_c": 55.0,
    "network_summary": {
      "num_junctions": 32,
      "num_pipes": 30,
      "num_heat_exchangers": 15,
      "num_sinks": 1,
      "num_ext_grids": 1
    }
  },
  "warnings": [],
  "execution_time_s": 12.3
}
```

**Purpose:** Raw simulation output with all calculated KPIs

**Used By:** KPI calculator, reporting tools

---

### 2. KPI Reports (results_test/)

**Location:** `results_test/scenario_kpis.csv` and `scenario_kpis.json`

**Format:** CSV + JSON

**Content (scenario_kpis.csv):**
```csv
scenario,type,simulation_mode,lcoh_eur_per_mwh,co2_t_per_a,total_heat_supplied_mwh,max_pressure_drop_bar,pump_energy_kwh,min_voltage_pu,max_line_loading_pct,...

Parkstrasse_DH,DH,real,95.23,45.2,234.5,0.42,4823,,,82.3,84.1,23.4,10.0,32,30,15,1.2
Parkstrasse_HP,HP,real,110.45,52.3,,,,0.948,78.3,1.019,1.0,0.985,2,65.4,false,1.234,0.023,3.2
```

**Columns:**

**Common:**
- `scenario` - Scenario name
- `type` - "DH" or "HP"
- `simulation_mode` - "real" or "placeholder"
- `lcoh_eur_per_mwh` - Levelized Cost of Heat (€/MWh)
- `co2_t_per_a` - CO2 emissions (tons/year)

**DH-Specific:**
- `total_heat_supplied_mwh` - Heat delivered (MWh)
- `peak_heat_load_kw` - Peak demand (kW)
- `max_pressure_drop_bar` - Max pressure drop (bar)
- `avg_pressure_drop_bar` - Avg pressure drop (bar)
- `pump_energy_kwh` - Pump consumption (kWh)
- `min_supply_temp_c` - Min temperature (°C)
- `avg_supply_temp_c` - Avg temperature (°C)
- `network_heat_loss_kwh` - Heat losses (kWh)
- `heat_loss_percentage` - Loss percentage (%)
- `num_junctions` - Junction count
- `num_pipes` - Pipe count
- `num_consumers` - Consumer count
- `total_pipe_length_km` - Network length (km)

**HP-Specific:**
- `min_voltage_pu` - Minimum voltage (per-unit)
- `max_voltage_pu` - Maximum voltage (per-unit)
- `avg_voltage_pu` - Average voltage (per-unit)
- `voltage_violations` - Violation count
- `max_line_loading_pct` - Max line loading (%)
- `avg_line_loading_pct` - Avg line loading (%)
- `overloaded_lines` - Overload count
- `transformer_loading_pct` - Transformer loading (%)
- `transformer_overloaded` - Boolean flag
- `total_load_mw` - Total electrical load (MW)
- `total_losses_mw` - Grid losses (MW)
- `loss_percentage` - Loss percentage (%)
- `num_buses` - Bus count
- `num_lines` - Line count
- `num_loads` - Load count

**Purpose:** Aggregated KPIs for analysis and reporting

**Used By:** LLM reporter, visualization tools, comparisons

---

### 3. AI Reports (results_test/)

**Location:** `results_test/llm_report.md` (and .txt, .html versions)

**Format:** Markdown (+ TXT, HTML)

**Content Example:**
```markdown
# Energy Analysis Report: Parkstraße District Heating

## Executive Summary

The district heating scenario for Parkstraße demonstrates technical feasibility
with a total heat demand of 234.5 MWh annually...

## Key Findings

### Network Performance
- Total heat supplied: 234.5 MWh/year
- Peak heat load: 1,234.5 kW
- Network length: 1.2 km (30 pipes)
- Maximum pressure drop: 0.42 bar (acceptable)

### Economic Analysis
- Levelized Cost of Heat (LCoH): €95.23/MWh
- Annual pump energy: 4,823 kWh
- Network heat losses: 23.4 kWh (10%)

### Environmental Impact
- CO2 emissions: 45.2 tons/year
- Emissions intensity: 193 kg CO2/MWh

## Recommendations

The district heating network is technically feasible for Parkstraße.
The pressure drop of 0.42 bar is within acceptable limits...

[Generated by GPT-4 from real simulation KPIs]
```

**Purpose:** Human-readable analysis with AI insights

**Used By:** Decision makers, stakeholders, reports

---

### 4. GeoJSON Visualization Files (results_test/)

**Location:** `results_test/`

**Files:**
```
buildings_projected.geojson          ← Building footprints
service_connections.geojson          ← Building-to-street connections
street_projected.geojson             ← Street network
dh_junctions.geojson                 ← DH network nodes (NEW!)
hp_buses.geojson                     ← HP electrical buses (NEW!)
```

**Format:** GeoJSON (can be opened in QGIS, ArcGIS, web maps)

**Content Example (dh_junctions.geojson):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [14.3654, 51.7542]  // lon, lat
      },
      "properties": {
        "id": 0,
        "name": "plant_supply",
        "pressure_bar": 6.0,
        "temperature_c": 85.0
      }
    },
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [14.3658, 51.7545]
      },
      "properties": {
        "id": 1,
        "name": "supply_B001",
        "pressure_bar": 5.58,
        "temperature_c": 84.2
      }
    }
    // ... more junctions
  ]
}
```

**Purpose:** Spatial visualization of network results

**Used By:** GIS software, web mapping, visualization tools

---

### 5. Network Visualization Images (results_test/)

**Location:** `results_test/`

**Files:**
```
network_visualization.png            ← High-res network map
network_visualization.pdf            ← Vector format for printing
network_map_{street}_{scenario}.png  ← Street-specific maps
network_diagram.png                  ← Network topology
```

**Format:** PNG (raster), PDF (vector)

**Content:** 
- Building footprints
- Street network
- Service connections (buildings to street)
- Pipes/cables with color coding
- Temperature/voltage gradients

**Purpose:** Visual presentation of network layout

**Used By:** Reports, presentations, documentation

---

### 6. Network Data Files (results_test/)

**Location:** `results_test/`

**Files:**
```
branitz_network.graphml              ← NetworkX graph (XML format)
branitz_network.gpickle              ← NetworkX graph (pickle format)
network_graph_{n}_buildings.json     ← Building network topology
```

**Format:** GraphML (XML), Pickle, JSON

**Content (network_graph.json):**
```json
{
  "nodes": [
    {
      "id": "B001",
      "type": "building",
      "heating_load_kw": 75.5,
      "coordinates": [14.3654, 51.7542]
    },
    {
      "id": "street_node_123",
      "type": "street",
      "coordinates": [14.3656, 51.7543]
    }
  ],
  "edges": [
    {
      "from": "B001",
      "to": "street_node_123",
      "length_m": 25.3,
      "type": "service_connection"
    }
  ]
}
```

**Purpose:** Network topology for analysis and simulation

**Used By:** Network construction, simulation input

---

### 7. Building Data Files (results_test/)

**Location:** `results_test/`

**Processing Pipeline:**

```
buildings_prepared.geojson
  ↓ (add demographics)
buildings_with_demographics.geojson
  ↓ (calculate U-values)
buildings_with_envelope.geojson
  ↓ (calculate demand)
buildings_with_demand.geojson  ← Final building data
```

**Content (buildings_with_demand.geojson):**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[14.365, 51.754], ...]]
      },
      "properties": {
        "GebaeudeID": "DEBBAL000001XY",
        "population": 3,
        "building_type": "residential",
        "construction_year": 1975,
        "u_value_wall": 1.2,
        "u_value_roof": 0.8,
        "heating_load_kw": 75.5,
        "annual_heat_demand_kwh": 45230,
        "base_electric_load_kw": 2.5
      }
    }
    // ... more buildings
  ]
}
```

**Purpose:** Complete building dataset with all calculated properties

**Used By:** Simulations, visualizations, analysis

---

### 8. Load Profiles (results_test/)

**Location:** `results_test/building_load_profiles.json`

**Format:** JSON

**Content:**
```json
{
  "DEBBAL000001XY": {
    "hourly_profile_h0": [
      0.45, 0.42, 0.38, 0.35, ..., 0.62  // 8760 values (1 year)
    ],
    "annual_demand_kwh": 45230,
    "peak_load_kw": 75.5
  },
  "DEBBAL000002AB": {
    "hourly_profile_h0": [...],
    "annual_demand_kwh": 38950,
    "peak_load_kw": 65.2
  }
  // ... all buildings
}
```

**Purpose:** Hourly load profiles for dynamic analysis

**Used By:** Time-series analysis, peak load calculations

---

### 9. Cache Files (simulation_cache/)

**Location:** `simulation_cache/{dh|hp}/`

**Files:**
```
{hash}.pkl              ← Pickled SimulationResult
{hash}_meta.json        ← Cache metadata
```

**Naming:** Files are named with MD5 hash of inputs

**Example (metadata):**
```json
{
  "timestamp": "2025-11-05T10:30:45.123456",
  "simulation_type": "DH",
  "num_buildings": 15,
  "cache_key": "a3f5b2c1d4e6f7a8b9c0d1e2f3a4b5c6",
  "execution_time_s": 12.3
}
```

**Purpose:** Speed up repeated queries (45x faster!)

**Lifetime:** 24 hours (configurable in feature_flags.yaml)

---

## 🗺️ Complete Output Locations Map

### By Output Type

#### Simulation Results 🔬

```
simulation_outputs/
├── Test_DH_Integration_results.json
├── Test_HP_Integration_results.json
├── Comparison_DH_results.json
├── Comparison_HP_results.json
├── Agent_DH_Test_results.json
├── Agent_HP_Test_results.json
└── {scenario_name}_results.json

Purpose: Raw simulation outputs (JSON)
Contains: All KPIs, metadata, warnings
Generated by: simulation_runner.py
```

#### KPI & Economic Analysis 📊

```
results_test/
├── scenario_kpis.csv          ← Main KPI table (CSV)
├── scenario_kpis.json         ← Main KPI table (JSON)
├── llm_report.md              ← AI-generated analysis
├── llm_report.txt             ← Plain text version
└── llm_report.html            ← HTML version

Purpose: Aggregated KPIs + economic/environmental analysis
Contains: LCoH, CO2, all simulation KPIs
Generated by: kpi_calculator.py, llm_reporter.py
```

#### Spatial Data (GeoJSON) 🗺️

```
results_test/
├── buildings_with_demand.geojson     ← Final building data
├── streets.geojson                   ← Street network
├── nodes.geojson                     ← Street nodes
├── service_connections.geojson       ← Building connections
├── buildings_projected.geojson       ← Building footprints
├── street_projected.geojson          ← Projected streets
├── dh_junctions.geojson              ← DH network nodes (NEW!)
└── hp_buses.geojson                  ← HP electrical buses (NEW!)

Purpose: Spatial visualization
Contains: Geometries + attributes
Generated by: Simulators, network tools
```

#### Visualizations 📈

```
results_test/
├── network_visualization.png         ← Main network map (PNG)
├── network_visualization.pdf         ← Vector version (PDF)
├── network_map_{street}_{type}.png   ← Street-specific maps
└── network_diagram.png               ← Topology diagram

Purpose: Visual representation
Contains: Network maps with color coding
Generated by: Visualization tools
```

#### Network Topology 🕸️

```
results_test/
├── branitz_network.graphml           ← NetworkX graph (XML)
├── branitz_network.gpickle           ← NetworkX graph (binary)
└── network_graph_{n}_buildings.json  ← JSON topology

Purpose: Network structure for analysis
Contains: Nodes, edges, properties
Generated by: network_construction.py
```

#### Cache Storage 💾

```
simulation_cache/
├── dh/
│   ├── a3f5b2c1...pkl                ← Cached DH result
│   ├── a3f5b2c1...meta.json          ← Cache metadata
│   └── ...
└── hp/
    ├── d4e5f6a7...pkl                ← Cached HP result
    ├── d4e5f6a7...meta.json          ← Cache metadata
    └── ...

Purpose: Performance optimization
Contains: Pickled SimulationResult objects
Generated by: cache_manager.py
Lifetime: 24 hours (default)
```

---

## 📋 File Generation Flow

### Complete Workflow

```
User Query
  ↓
Agent System
  ↓
energy_tools.run_simulation_pipeline()
  ↓
main.py (10-step pipeline)
  ↓
┌─────────────────────────────────────────────┐
│ Step 1-7: Data Preparation                  │
│   Outputs:                                  │
│   ├─ buildings_prepared.geojson            │
│   ├─ buildings_with_demographics.geojson   │
│   ├─ buildings_with_envelope.geojson       │
│   ├─ buildings_with_demand.geojson         │
│   ├─ building_load_profiles.json           │
│   ├─ branitz_network.graphml               │
│   └─ streets.geojson, nodes.geojson        │
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│ Step 8: Simulation Runner (NEW!)            │
│   Outputs:                                  │
│   ├─ simulation_outputs/{name}_results.json│
│   ├─ results_test/dh_junctions.geojson     │ ← NEW!
│   └─ results_test/hp_buses.geojson         │ ← NEW!
│                                             │
│ + Cache (if enabled):                       │
│   └─ simulation_cache/{type}/{hash}.pkl    │ ← NEW!
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│ Step 9: KPI Calculator                      │
│   Outputs:                                  │
│   ├─ scenario_kpis.csv                      │
│   └─ scenario_kpis.json                     │
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│ Step 10: LLM Reporter                       │
│   Outputs:                                  │
│   ├─ llm_report.md                          │
│   ├─ llm_report.txt                         │
│   └─ llm_report.html                        │
└─────────────────────────────────────────────┘
  ↓
┌─────────────────────────────────────────────┐
│ Visualization Tools                         │
│   Outputs:                                  │
│   ├─ network_visualization.png              │
│   ├─ network_visualization.pdf              │
│   └─ network_map_{street}_{type}.png       │
└─────────────────────────────────────────────┘
```

---

## 🔍 Output File Details

### Simulation Results JSON Structure

**File:** `simulation_outputs/{scenario}_results.json`

**Full Structure:**
```json
{
  // Status
  "success": boolean,              // Did simulation succeed?
  "scenario": string,              // Scenario name
  "type": "DH" | "HP",            // Simulation type
  "mode": "real" | "placeholder", // Which simulator was used
  
  // Key Performance Indicators
  "kpi": {
    // DH KPIs (if type="DH")
    "total_heat_supplied_mwh": float,
    "peak_heat_load_kw": float,
    "max_pressure_drop_bar": float,
    "avg_pressure_drop_bar": float,
    "pump_energy_kwh": float,
    "min_supply_temp_c": float,
    "avg_supply_temp_c": float,
    "network_heat_loss_kwh": float,
    "heat_loss_percentage": float,
    "num_junctions": int,
    "num_pipes": int,
    "num_consumers": int,
    "total_pipe_length_km": float,
    
    // HP KPIs (if type="HP")
    "min_voltage_pu": float,
    "max_voltage_pu": float,
    "avg_voltage_pu": float,
    "voltage_violations": int,
    "max_line_loading_pct": float,
    "avg_line_loading_pct": float,
    "overloaded_lines": int,
    "transformer_loading_pct": float,
    "transformer_overloaded": boolean,
    "total_load_mw": float,
    "total_losses_mw": float,
    "loss_percentage": float,
    "num_buses": int,
    "num_lines": int,
    "num_loads": int
  },
  
  // Additional Information
  "metadata": {
    "num_consumers": int,
    "heat_source_building": string,  // DH only
    "transformer_location": string,   // HP only
    "total_demand_kw": float,
    "supply_temp_c": float,          // DH only
    "return_temp_c": float,          // DH only
    "hp_thermal_kw": float,          // HP only
    "hp_cop": float,                 // HP only
    "network_summary": object,
    "exported_files": object
  },
  
  // Diagnostics
  "warnings": [string],              // Any warnings
  "error": string | null,            // Error message if failed
  "execution_time_s": float          // How long it took
}
```

---

## 📁 Output Directory Usage Guide

### results_test/ (Test/Development)

**When Used:** 
- During development
- When using `run_all_test.yaml` config
- For testing with subset of buildings

**Contents:**
- All pipeline outputs
- All visualizations
- All reports
- Test scenario files

**Size:** Can grow to several MB with many tests

### results/ (Production)

**When Used:**
- Production runs
- When using `run_all.yaml` config
- For full dataset analysis

**Contents:**
- Same structure as results_test/
- Production-scale outputs
- Final deliverables

**Size:** Can grow to 100+ MB with full dataset

### simulation_outputs/ (Simulation Raw Data)

**When Used:**
- Every simulation run
- Both test and production

**Contents:**
- Raw JSON simulation results
- One file per scenario
- All KPIs and metadata

**Size:** ~10-50 KB per file

### simulation_cache/ (Performance)

**When Used:**
- When `enable_caching: true` in config
- Automatic (transparent)

**Contents:**
- Pickled simulation results
- Metadata JSON files
- Organized by type (dh/, hp/)

**Size:** ~50-200 KB per cached simulation

**Maintenance:**
- Auto-expires after 24 hours
- Can be manually cleared
- Safe to delete entire directory

---

## 🎯 How to Access Outputs

### Option 1: Direct File Access

```bash
# View KPI CSV
cat results_test/scenario_kpis.csv

# View AI report
cat results_test/llm_report.md

# View simulation result
cat simulation_outputs/Parkstrasse_DH_results.json | jq '.kpi'
```

### Option 2: Load in Python

```python
import json
import pandas as pd
import geopandas as gpd

# Load simulation result
with open("simulation_outputs/Parkstrasse_DH_results.json") as f:
    result = json.load(f)
    print(f"Heat: {result['kpi']['total_heat_supplied_mwh']} MWh")

# Load KPI table
kpis = pd.read_csv("results_test/scenario_kpis.csv")
print(kpis)

# Load GeoJSON
buildings = gpd.read_file("results_test/buildings_with_demand.geojson")
print(buildings[['GebaeudeID', 'heating_load_kw']])
```

### Option 3: Visualize in GIS

```bash
# Open in QGIS
qgis results_test/buildings_with_demand.geojson \
     results_test/dh_junctions.geojson \
     results_test/streets.geojson

# Or use any GIS software that reads GeoJSON
```

### Option 4: View Reports

```bash
# Markdown report
open results_test/llm_report.md

# HTML report
open results_test/llm_report.html

# Images
open results_test/network_visualization.png
```

---

## 📊 Output Size Estimates

| Output Type | Typical Size | Max Size |
|-------------|-------------|----------|
| **Simulation JSON** | 10-20 KB | 100 KB |
| **KPI CSV** | 1-5 KB | 50 KB |
| **GeoJSON** | 50-500 KB | 5 MB |
| **Network Graph** | 10-50 KB | 500 KB |
| **Load Profiles** | 100-500 KB | 2 MB |
| **Reports (MD/HTML)** | 5-20 KB | 100 KB |
| **Images (PNG)** | 500 KB-2 MB | 10 MB |
| **Cache (per entry)** | 50-200 KB | 1 MB |

**Total per scenario:** 2-10 MB typically

---

## 🔧 Output Management

### Clean Up Old Outputs

```bash
# Clear test results (keep config)
rm -rf results_test/*.geojson results_test/*.json results_test/*.png

# Clear simulation outputs
rm -rf simulation_outputs/*.json

# Clear cache (will regenerate)
rm -rf simulation_cache/dh/* simulation_cache/hp/*

# Full reset (caution!)
rm -rf results_test/* results/* simulation_outputs/* simulation_cache/*/*
```

### Archive Results

```bash
# Archive results with timestamp
tar -czf results_backup_$(date +%Y%m%d).tar.gz results_test/ simulation_outputs/

# Extract later
tar -xzf results_backup_YYYYMMDD.tar.gz
```

---

## 🎯 Key Output Files Reference

### Most Important Files

| File | Location | Purpose | Format |
|------|----------|---------|--------|
| **scenario_kpis.csv** | `results_test/` | All KPIs aggregated | CSV |
| **llm_report.md** | `results_test/` | AI-generated insights | Markdown |
| **buildings_with_demand.geojson** | `results_test/` | Final building data | GeoJSON |
| **{scenario}_results.json** | `simulation_outputs/` | Raw simulation output | JSON |
| **network_visualization.png** | `results_test/` | Network map | PNG |

### New in v2.0 (Real Simulations)

| File | Location | Purpose | NEW? |
|------|----------|---------|------|
| **dh_junctions.geojson** | `results_test/` | DH pressure/temp nodes | ✅ NEW |
| **hp_buses.geojson** | `results_test/` | HP voltage nodes | ✅ NEW |
| **{hash}.pkl** | `simulation_cache/` | Cached results | ✅ NEW |
| **{scenario}_results.json** | `simulation_outputs/` | Enhanced with 25 KPIs | ✅ ENHANCED |

---

## 📖 Example: Analyzing Outputs

### Scenario: "analyze district heating for Parkstraße"

**Outputs Generated:**

```
1. simulation_outputs/Parkstrasse_DH_85C_results.json
   → Raw simulation output with all 12 DH KPIs

2. results_test/scenario_kpis.csv
   → Row added with KPIs + LCoH + CO2

3. results_test/llm_report.md
   → AI analysis: "The network is feasible..."

4. results_test/dh_junctions.geojson
   → Spatial data with pressure/temperature at each node

5. results_test/network_map_Parkstrasse_DH.png
   → Visual network map

6. simulation_cache/dh/{hash}.pkl (if caching enabled)
   → Cached for instant retrieval next time

7. simulation_outputs/Parkstrasse_DH_85C_results.json saved
   → Backup of full results
```

**Total Files Created:** 6-7 files per analysis

---

## 🎯 Finding Your Results

### By Scenario Name

```bash
# Find all outputs for a specific scenario
grep -r "Parkstrasse" simulation_outputs/
grep -r "Parkstrasse" results_test/

# List all files for a street
ls -lh results_test/*Parkstrasse*
ls -lh results_test/network_map_*
```

### By File Type

```bash
# All simulation results
ls -lh simulation_outputs/*.json

# All KPI files
ls -lh results_test/scenario_kpis.*

# All GeoJSON files
ls -lh results_test/*.geojson

# All visualization images
ls -lh results_test/*.png results_test/*.pdf
```

### By Date (Recent Outputs)

```bash
# Most recent simulation outputs
ls -lt simulation_outputs/*.json | head -5

# Most recent results
ls -lt results_test/ | head -10
```

---

## 🔍 Output Verification

### Check Simulation Was Real (Not Placeholder)

```bash
# Look for "mode": "real" in output
cat simulation_outputs/Parkstrasse_DH_results.json | grep '"mode"'

# Should show: "mode": "real"
# If shows: "mode": "placeholder" → using placeholders
```

### Validate KPI Values

```python
import json

# Load result
with open("simulation_outputs/Parkstrasse_DH_results.json") as f:
    result = json.load(f)

# Check mode
assert result["mode"] == "real", "Not using real simulation!"

# Check KPIs are realistic (not placeholder 1234)
assert result["kpi"]["total_heat_supplied_mwh"] != 1234, "Placeholder value!"

print("✅ Real simulation confirmed!")
print(f"Heat: {result['kpi']['total_heat_supplied_mwh']} MWh")
print(f"Pressure: {result['kpi']['max_pressure_drop_bar']} bar")
```

---

## 📊 Output Summary Table

| Output Category | Location | Files | Format | Size | Purpose |
|----------------|----------|-------|--------|------|---------|
| **Simulation Results** | `simulation_outputs/` | 1 per run | JSON | 10-50 KB | Raw output |
| **KPI Tables** | `results_test/` | 2 (CSV+JSON) | CSV/JSON | 1-10 KB | Analysis |
| **AI Reports** | `results_test/` | 3 (MD+TXT+HTML) | Text | 5-20 KB | Insights |
| **Building Data** | `results_test/` | 4 stages | GeoJSON | 100-500 KB | Spatial |
| **Network Data** | `results_test/` | 3 formats | Multiple | 10-100 KB | Topology |
| **Visualizations** | `results_test/` | 2-4 images | PNG/PDF | 500KB-2MB | Presentation |
| **Load Profiles** | `results_test/` | 1 file | JSON | 100-500 KB | Time-series |
| **Cache** | `simulation_cache/` | 2 per entry | PKL/JSON | 50-200 KB | Performance |

**Total per complete analysis:** 2-10 MB

---

## 🎯 Quick Reference

### Where is...?

**Q: Where are the main KPIs?**  
A: `results_test/scenario_kpis.csv` (CSV table)

**Q: Where is the AI analysis?**  
A: `results_test/llm_report.md` (Markdown)

**Q: Where are simulation results?**  
A: `simulation_outputs/{scenario_name}_results.json`

**Q: Where are the maps?**  
A: `results_test/network_visualization.png`

**Q: Where is the GeoJSON for GIS?**  
A: `results_test/*.geojson` (multiple files)

**Q: Where are cached results?**  
A: `simulation_cache/dh/` or `simulation_cache/hp/`

---

## ✨ Summary

**Output Locations:**
- `simulation_outputs/` - Raw simulation JSONs
- `results_test/` - All processed results (main location!)
- `simulation_cache/` - Cached results for speed
- `results/` - Production results (full dataset)

**File Types:**
- JSON (simulation results, network data)
- CSV (KPI tables)
- GeoJSON (spatial data)
- Markdown/HTML (reports)
- PNG/PDF (visualizations)
- PKL (cache files)

**Total Files per Analysis:**
- 6-10 output files
- 2-10 MB total size
- All organized by location and type

**Access:**
- Direct file reading
- Python (pandas, geopandas, json)
- GIS software (QGIS, ArcGIS)
- Text editors (for reports)
- Image viewers (for maps)

---

**See also:**
- `README.md` - Output file descriptions
- `src/simulation_runner.py` - Where outputs are created
- `src/kpi_calculator.py` - KPI generation

---

**Last Updated:** November 2025  
**System Version:** 2.0 (Real Simulations + Caching)
