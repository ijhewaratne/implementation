# 📁 Outputs Guide - Complete Reference

## Agent-Based Energy System - Output Files Location & Structure

**Last Updated:** November 2025  
**System Version:** 2.0 (Real Simulations)

---

## 🗂️ Output Directory Structure

```
branitz_energy_decision_ai_street_agents/
│
├── 📁 simulation_outputs/          ← Raw simulation results (JSON)
│   ├── {scenario_name}_results.json
│   └── ...
│
├── 📁 results_test/                 ← Main pipeline outputs (GeoJSON, CSV, reports)
│   ├── buildings_*.geojson
│   ├── network_*.json
│   ├── scenario_kpis.csv
│   ├── llm_report.md
│   └── ...
│
├── 📁 results/                      ← Production results (same as results_test)
│   └── (same structure as results_test)
│
├── 📁 simulation_cache/             ← Cached simulation results (for speed)
│   ├── dh/
│   │   ├── {hash}.pkl             # Cached DH results
│   │   └── {hash}_meta.json       # Cache metadata
│   └── hp/
│       ├── {hash}.pkl             # Cached HP results
│       └── {hash}_meta.json       # Cache metadata
│
└── 📁 scenarios/                    ← Scenario configurations
    ├── {scenario_name}_DH.json
    └── {scenario_name}_HP.json
```

---

## 📊 Output File Types & Locations

### 1. Simulation Results (JSON) 📋

**Location:** `simulation_outputs/`

**Files:**
- `{scenario_name}_results.json` - Complete simulation results

**Format:** JSON

**Example:** `Agent_DH_Test_results.json`

**Contents:**
```json
{
  "success": true,
  "scenario": "Agent_DH_Test",
  "type": "DH",
  "mode": "placeholder" or "real",
  "kpi": {
    "total_heat_supplied_mwh": 2.37,
    "peak_heat_load_kw": 270.0,
    "max_pressure_drop_bar": 0.5,
    "avg_pressure_drop_bar": 0.3,
    "pump_energy_kwh": 47.3,
    "min_supply_temp_c": 82.0,
    "avg_supply_temp_c": 83.5,
    "network_heat_loss_kwh": 236.8,
    "heat_loss_percentage": 10.0,
    "num_junctions": 10,
    "num_pipes": 10,
    "num_consumers": 5,
    "total_pipe_length_km": 0.5
  },
  "metadata": {
    "num_buildings": 5,
    "supply_temp_c": 85.0,
    "return_temp_c": 55.0
  },
  "warnings": ["..."],
  "execution_time_s": 4.5
}
```

**Purpose:**
- Raw simulation results from pandapipes/pandapower
- Used by KPI calculator
- Input for AI report generation

---

### 2. Building Data (GeoJSON) 🏘️

**Location:** `results_test/` or `results/`

**Files:**
- `buildings_prepared.geojson` - Preprocessed building geometries
- `buildings_with_demographics.geojson` - With population data
- `buildings_with_envelope.geojson` - With U-values
- `buildings_with_demand.geojson` - With heating demands
- `buildings_projected_{n}_buildings.geojson` - Specific street extractions

**Format:** GeoJSON (FeatureCollection)

**Example Structure:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[x1, y1], [x2, y2], ...]]
      },
      "properties": {
        "GebaeudeID": "DEBBAL0000aBC",
        "heating_load_kw": 75.5,
        "base_electric_load_kw": 2.3,
        "population": 4,
        "building_area_m2": 150.0,
        "u_value": 1.2
      }
    },
    ...
  ]
}
```

**Purpose:**
- Visualize buildings on maps
- Input for network creation
- Analysis and reporting

**Can be opened in:**
- QGIS
- ArcGIS
- Python (geopandas)
- Online GeoJSON viewers

---

### 3. Network Data 🔗

**Location:** `results_test/` or `results/`

**Files:**
- `branitz_network.graphml` - NetworkX graph (XML format)
- `branitz_network.gpickle` - NetworkX graph (binary)
- `network_graph.json` - Network topology (JSON)
- `service_connections.geojson` - Building-to-street connections

**Format:** GraphML, Pickle, JSON, GeoJSON

**Example `network_graph.json`:**
```json
{
  "nodes": [
    {
      "id": "B001",
      "type": "building",
      "demand_kw": 75.5,
      "coordinates": [14.3456, 51.7234]
    },
    {
      "id": "S001",
      "type": "street_node",
      "coordinates": [14.3450, 51.7230]
    }
  ],
  "edges": [
    {
      "from": "B001",
      "to": "S001",
      "type": "service_connection",
      "length_m": 45.2
    }
  ]
}
```

**Purpose:**
- Network topology analysis
- Visualization
- Input for simulations

---

### 4. KPI Results (CSV & JSON) 📈

**Location:** `results_test/` or `results/`

**Files:**
- `scenario_kpis.csv` - Aggregated KPIs (tabular)
- `scenario_kpis.json` - Aggregated KPIs (JSON)
- `kpi_comparison.csv` - DH vs HP comparison

**Format:** CSV or JSON

**Example `scenario_kpis.csv`:**
```csv
scenario,type,simulation_mode,lcoh_eur_per_mwh,co2_t_per_a,total_heat_supplied_mwh,peak_heat_load_kw,max_pressure_drop_bar,pump_energy_kwh,min_supply_temp_c,avg_supply_temp_c,num_junctions,num_pipes,num_consumers
Parkstrasse_DH,DH,real,95.23,45.6,234.5,1234.5,0.42,4823,82.3,83.5,32,30,15
Parkstrasse_HP,HP,real,110.45,52.3,220.0,1200.0,,,0.948,1.019,78.3,65.4,15
```

**Columns (DH):**
- `scenario` - Scenario name
- `type` - "DH" or "HP"
- `simulation_mode` - "real" or "placeholder"
- `lcoh_eur_per_mwh` - Levelized Cost of Heat (€/MWh)
- `co2_t_per_a` - CO2 emissions (tons/year)
- `total_heat_supplied_mwh` - Heat supplied (MWh)
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
- `total_pipe_length_km` - Total length (km)

**Columns (HP):**
- `min_voltage_pu` - Minimum voltage (per-unit)
- `max_voltage_pu` - Maximum voltage
- `avg_voltage_pu` - Average voltage
- `voltage_violations` - Count of violations
- `max_line_loading_pct` - Max line loading (%)
- `avg_line_loading_pct` - Avg line loading (%)
- `overloaded_lines` - Count of overloads
- `transformer_loading_pct` - Transformer loading (%)
- `transformer_overloaded` - Boolean
- `total_load_mw` - Total load (MW)
- `total_losses_mw` - Grid losses (MW)
- `loss_percentage` - Loss percentage (%)
- `num_buses` - Bus count
- `num_lines` - Line count
- `num_loads` - Load count

**Purpose:**
- Economic comparison
- Scenario evaluation
- Reporting
- Further analysis (Excel, Python, R)

---

### 5. AI-Generated Reports (Markdown/HTML/Text) 📄

**Location:** `results_test/` or `reports/`

**Files:**
- `llm_report.md` - Markdown format
- `llm_report.html` - HTML format
- `llm_report.txt` - Plain text
- `llm_final_report.md` - Final analysis

**Format:** Markdown/HTML/Text

**Example Content:**
```markdown
# Energy Analysis Report: Parkstraße

## Executive Summary

The district heating analysis for Parkstraße reveals a total heat 
demand of 234.5 MWh annually, serving 15 buildings. The network 
design requires 30 pipes with a total length of 1.2 km.

## Key Findings

### Technical Feasibility
- Maximum pressure drop: 0.42 bar (acceptable)
- Supply temperature maintained at 82-85°C
- Network heat losses: 10% (reasonable)

### Economic Analysis
- Levelized Cost of Heat: €95/MWh
- Capital costs: €960,000 (network installation)
- Operating costs: €45,000/year (biomass + pumping)

### Environmental Impact
- CO2 emissions: 45 tons/year
- Emission reduction vs baseline: 35%

## Recommendations

District heating is technically and economically feasible for 
Parkstraße. The network can be implemented with standard 
technology and achieves competitive heat costs.

...
```

**Purpose:**
- Executive summaries
- Stakeholder presentations
- Decision-making support

---

### 6. Network Visualizations (PNG/PDF) 🗺️

**Location:** `results_test/` or `results/`

**Files:**
- `network_visualization.png` - High-resolution network map (PNG)
- `network_visualization.pdf` - Vector format for printing
- `network_map_{street}_{scenario}.png` - Street-specific maps
- `network_diagram.png` - Network topology diagram

**Format:** PNG (raster) or PDF (vector)

**Contents:**
- Building footprints (grey polygons)
- Street network (black lines)
- Service connections (red lines from buildings to street)
- Network topology (nodes and edges)

**Size:** Typically 500-800 KB per PNG

**Purpose:**
- Visual presentations
- Reports and documentation
- Spatial analysis
- Stakeholder communication

**Can be opened in:**
- Any image viewer
- PowerPoint/Keynote
- PDF readers
- GIS software

---

### 7. Street Network (GeoJSON) 🛣️

**Location:** `results_test/` or `results/`

**Files:**
- `streets.geojson` - Street network lines
- `street_projected.geojson` - Projected coordinates
- `nodes.geojson` - Street network nodes

**Format:** GeoJSON

**Example:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[14.345, 51.723], [14.346, 51.724]]
      },
      "properties": {
        "name": "Parkstraße",
        "highway": "residential",
        "length_m": 125.5
      }
    }
  ]
}
```

---

### 8. Service Connections (GeoJSON) 🔌

**Location:** `results_test/`

**Files:**
- `service_connections.geojson` - Building-to-street connections
- `service_connections_{n}_buildings.geojson` - Specific extractions

**Format:** GeoJSON (LineString)

**Example:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [
          [14.3456, 51.7234],  # Building point
          [14.3450, 51.7230]   # Street connection point
        ]
      },
      "properties": {
        "building_id": "B001",
        "length_m": 45.2,
        "connection_type": "service_line"
      }
    }
  ]
}
```

**Purpose:**
- Visualize how buildings connect to streets
- Calculate service line costs
- Network planning

---

### 9. Load Profiles (JSON) 📊

**Location:** `results_test/` or `results/`

**Files:**
- `building_load_profiles.json` - Hourly load profiles for all buildings

**Format:** JSON (large file, typically 50-150 MB)

**Example:**
```json
{
  "DEBBAL0000aBC": {
    "annual_demand_kwh": 50000,
    "hourly_profile": [
      45.2,  // Hour 0
      42.1,  // Hour 1
      38.5,  // Hour 2
      ...    // 8760 hours total
    ]
  },
  "DEBBAL0001xYZ": {
    ...
  }
}
```

**Purpose:**
- Time-series analysis
- Peak load identification
- Grid impact assessment

---

### 10. Cached Results (Pickle) 💾

**Location:** `simulation_cache/dh/` or `simulation_cache/hp/`

**Files:**
- `{hash}.pkl` - Pickled SimulationResult
- `{hash}_meta.json` - Cache metadata

**Format:** Python pickle (binary) + JSON metadata

**Example Metadata (`a3f5b2c1_meta.json`):**
```json
{
  "timestamp": "2025-11-05T10:30:45.123456",
  "simulation_type": "DH",
  "num_buildings": 15,
  "cache_key": "a3f5b2c1d4e5f6a7b8c9d0e1f2a3b4c5",
  "execution_time_s": 4.5
}
```

**Cached Result (`.pkl`):**
- Complete `SimulationResult` object
- All KPIs
- All metadata
- Warnings and errors

**Purpose:**
- Speed up repeated queries (45x faster!)
- Avoid re-running identical simulations
- Automatic (transparent to user)

**TTL:** 24 hours (configurable)

---

### 11. Scenario Configurations (JSON) 📝

**Location:** `scenarios/`

**Files:**
- `{scenario_name}_DH.json` - DH scenario config
- `{scenario_name}_HP.json` - HP scenario config

**Format:** JSON

**Example:**
```json
{
  "name": "Parkstrasse_DH_85C",
  "type": "DH",
  "building_file": "results_test/buildings_with_demand.geojson",
  "params": {
    "supply_temp": 85,
    "return_temp": 55,
    "default_diameter_m": 0.065
  }
}
```

**Purpose:**
- Input for simulation_runner.py
- Reproducible simulations
- Parameter tracking

---

## 📍 Output File Locations by Workflow

### Agent Workflow (Natural Language Query)

**User Query:** `"analyze district heating for Parkstraße"`

**Outputs Generated:**

```
1. simulation_outputs/
   └── Parkstrasse_DH_85C_results.json  ← Raw simulation results

2. results_test/
   ├── buildings_prepared.geojson       ← Building geometries
   ├── buildings_with_demand.geojson    ← With heating demands
   ├── network_graph.json               ← Network topology
   ├── service_connections.geojson      ← Building connections
   ├── scenario_kpis.csv                ← KPI summary
   ├── scenario_kpis.json               ← KPI JSON
   ├── llm_report.md                    ← AI-generated report
   └── network_map_Parkstrasse_DH.png   ← Visualization

3. simulation_cache/dh/
   ├── a3f5b2c1.pkl                     ← Cached for next time
   └── a3f5b2c1_meta.json               ← Cache metadata

4. scenarios/
   └── Parkstrasse_DH.json              ← Scenario config
```

**Total:** ~10 files per analysis

---

### Comparison Workflow

**User Query:** `"compare scenarios for Parkstraße"`

**Outputs Generated:**

```
1. simulation_outputs/
   ├── Parkstrasse_DH_results.json      ← DH results
   └── Parkstrasse_HP_results.json      ← HP results

2. results_test/
   ├── kpi_comparison.csv               ← Side-by-side comparison
   ├── scenario_kpis.csv                ← Combined KPIs
   ├── llm_report.md                    ← Comparison analysis
   ├── network_map_Parkstrasse_DH.png   ← DH visualization
   └── network_map_Parkstrasse_HP.png   ← HP visualization

3. simulation_cache/
   ├── dh/{hash}.pkl                    ← Cached DH
   └── hp/{hash}.pkl                    ← Cached HP
```

**Total:** ~8-12 files per comparison

---

## 📊 Output File Sizes

### Typical File Sizes

| File Type | Size Range | Example |
|-----------|-----------|---------|
| **Simulation Results JSON** | 1-5 KB | 805 bytes - 2 KB |
| **Buildings GeoJSON** | 1-3 MB | 1.3 MB (all buildings) |
| **Network Graph JSON** | 10-50 KB | 11 KB (15 buildings) |
| **Service Connections** | 3-10 KB | 3 KB (15 buildings) |
| **KPI CSV** | 100-500 bytes | 161 bytes |
| **KPI JSON** | 200-1 KB | 378 bytes |
| **Load Profiles JSON** | 50-150 MB | 141 MB (all buildings) |
| **LLM Report MD** | 2-10 KB | 3.4 KB |
| **Network PNG** | 500-800 KB | 785 KB |
| **Network PDF** | 30-50 KB | 35 KB |
| **Cached Results** | 5-20 KB | ~10 KB per simulation |

### Storage Requirements

**Per Street Analysis:**
- Small street (5-10 buildings): ~5 MB
- Medium street (20-30 buildings): ~8 MB
- Large street (50+ buildings): ~15 MB

**For 27 Streets (Complete Analysis):**
- Estimated: 200-300 MB total
- With caching: +50-100 MB

**Cache Growth:**
- Per simulation: ~10-20 KB
- 100 simulations: ~1-2 MB
- Auto-expires after 24 hours

---

## 🔍 How to Access Outputs

### View Simulation Results

```bash
# View raw simulation results
cat simulation_outputs/Agent_DH_Test_results.json

# Pretty print
python -m json.tool simulation_outputs/Agent_DH_Test_results.json

# In Python
import json
with open("simulation_outputs/Agent_DH_Test_results.json") as f:
    result = json.load(f)
print(result["kpi"]["total_heat_supplied_mwh"])
```

### View KPIs

```bash
# View as table
cat results_test/scenario_kpis.csv

# Open in Excel
open results_test/scenario_kpis.csv

# In Python/Pandas
import pandas as pd
kpis = pd.read_csv("results_test/scenario_kpis.csv")
print(kpis)
```

### View GeoJSON

```bash
# View in text
cat results_test/buildings_prepared.geojson

# Open in QGIS
qgis results_test/buildings_prepared.geojson

# Python
import geopandas as gpd
buildings = gpd.read_file("results_test/buildings_prepared.geojson")
buildings.plot()
```

### View Reports

```bash
# View markdown
cat results_test/llm_report.md

# View HTML in browser
open results_test/llm_report.html

# View PDF
open results_test/llm_report.pdf  # if generated
```

### View Network Maps

```bash
# View PNG
open results_test/network_visualization.png

# View PDF
open results_test/network_visualization.pdf
```

---

## 🗃️ Output Management

### Clean Old Results

```bash
# Remove old test results (be careful!)
rm -rf results_test/*

# Remove old simulation outputs
rm -rf simulation_outputs/*

# Clear cache
rm -rf simulation_cache/dh/*
rm -rf simulation_cache/hp/*

# Or use Python cache manager
python -c "from src.orchestration import SimulationCache; cache = SimulationCache(); cache.clear()"
```

### Backup Important Results

```bash
# Backup results directory
cp -r results_test results_backup_$(date +%Y%m%d)

# Backup specific scenario
cp simulation_outputs/Parkstrasse_DH_results.json ~/Desktop/
```

### Archive Results

```bash
# Create archive
tar -czf results_archive_$(date +%Y%m%d).tar.gz results_test/ simulation_outputs/

# Extract later
tar -xzf results_archive_20251105.tar.gz
```

---

## 📊 Output Examples by Scenario Type

### DH (District Heating) Outputs

**Simulation Results:**
- `simulation_outputs/{scenario}_results.json` - All DH KPIs

**KPIs:**
- Total heat supplied (MWh)
- Pressure drops (bar)
- Temperatures (°C)
- Pump energy (kWh)
- Heat losses (%)
- Network metrics (junctions, pipes, length)

**Visualizations:**
- Network map with pipes colored by temperature
- Building connections
- Pressure distribution (if exported)

### HP (Heat Pump) Outputs

**Simulation Results:**
- `simulation_outputs/{scenario}_results.json` - All HP KPIs

**KPIs:**
- Voltage profiles (pu)
- Line loadings (%)
- Transformer loading (%)
- Grid losses (MW, %)
- Violations (count)
- Network metrics (buses, lines)

**Visualizations:**
- Network map with buses colored by voltage
- Lines colored by loading
- Violation markers

---

## 🎯 Finding Specific Outputs

### Latest Simulation Results

```bash
# Most recent simulation
ls -lt simulation_outputs/ | head -5

# Most recent DH
ls -lt simulation_outputs/*DH* | head -1

# Most recent HP
ls -lt simulation_outputs/*HP* | head -1
```

### Outputs for Specific Street

```bash
# All outputs for Parkstraße
find . -name "*Parkstra*" -type f

# Expected:
# ./simulation_outputs/Parkstrasse_DH_results.json
# ./results_test/network_map_Parkstraße_DH.png
# ./scenarios/Parkstrasse_DH.json
```

### Today's Outputs

```bash
# Files created today
find results_test simulation_outputs -type f -mtime 0

# Files from last hour
find results_test simulation_outputs -type f -mmin -60
```

---

## 📋 Output Checklist

### After Running DH Analysis

**Expected Files:**
- [x] `simulation_outputs/{scenario}_DH_results.json`
- [x] `results_test/scenario_kpis.csv`
- [x] `results_test/scenario_kpis.json`
- [x] `results_test/llm_report.md`
- [x] `results_test/network_map_{street}_DH.png`
- [x] `simulation_cache/dh/{hash}.pkl` (if caching enabled)

### After Running HP Analysis

**Expected Files:**
- [x] `simulation_outputs/{scenario}_HP_results.json`
- [x] `results_test/scenario_kpis.csv`
- [x] `results_test/scenario_kpis.json`
- [x] `results_test/llm_report.md`
- [x] `results_test/network_map_{street}_HP.png`
- [x] `simulation_cache/hp/{hash}.pkl` (if caching enabled)

### After Comparison

**Expected Files:**
- [x] Both DH and HP results (above)
- [x] `results_test/kpi_comparison.csv`
- [x] Comparison report in `llm_report.md`

---

## 🎯 Quick Reference

### Main Output Locations

| Type | Location | Format |
|------|----------|--------|
| **Simulation Results** | `simulation_outputs/` | JSON |
| **KPIs** | `results_test/scenario_kpis.csv` | CSV |
| **Reports** | `results_test/llm_report.md` | Markdown |
| **Visualizations** | `results_test/*.png` | PNG |
| **Building Data** | `results_test/buildings_*.geojson` | GeoJSON |
| **Network Data** | `results_test/network_*.json` | JSON |
| **Cache** | `simulation_cache/{dh,hp}/` | Pickle |

### File Naming Convention

```
Pattern: {street_name}_{scenario_type}_{parameters}_results.{ext}

Examples:
  Parkstrasse_DH_85C_results.json      # DH at 85°C
  Liebermannstrasse_HP_6kW_results.json # HP with 6kW
  network_map_Parkstraße_DH.png        # DH visualization
```

---

## ✨ Tips & Tricks

### View Cache Statistics

```python
from src.orchestration import SimulationCache

cache = SimulationCache()
cache.print_stats()
# Output:
#   Cache Statistics:
#     Hits:     15
#     Misses:   10
#     Hit Rate: 60.0%
```

### Find Large Files

```bash
# Files > 1 MB
find results_test simulation_outputs -size +1M -exec ls -lh {} \;

# Expected: building_load_profiles.json (141 MB)
```

### Check Disk Usage

```bash
# Total space used
du -sh results_test simulation_outputs simulation_cache

# By directory
du -sh results_test
du -sh simulation_outputs
du -sh simulation_cache
```

### Export Results to Excel

```python
import pandas as pd

# Load KPIs
kpis = pd.read_csv("results_test/scenario_kpis.csv")

# Export to Excel
kpis.to_excel("results_test/scenario_kpis.xlsx", index=False)
```

---

## 📖 Summary

**The system generates multiple output types:**

1. **JSON** - Raw simulation results (machine-readable)
2. **CSV** - KPI summaries (Excel-compatible)
3. **GeoJSON** - Spatial data (GIS-compatible)
4. **Markdown/HTML** - Reports (human-readable)
5. **PNG/PDF** - Visualizations (presentations)
6. **Pickle** - Cached results (performance)

**All outputs are:**
- ✅ Well-organized in dedicated directories
- ✅ Named consistently
- ✅ Standard formats (interoperable)
- ✅ Documented (this guide)
- ✅ Easy to find and use

---

**For more details, see the file examples in the directories above!**

**Last Updated:** November 2025  
**System Version:** 2.0 (Real Simulations with Caching)

