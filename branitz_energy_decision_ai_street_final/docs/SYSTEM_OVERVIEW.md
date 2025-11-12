# 🏗️ BRANITZ ENERGY DECISION AI - SYSTEM OVERVIEW

## 📊 Multi-Agent Pipeline Architecture

### **Fork-Join Data Flow**

**Fork–join data flow.** LFA produces 8760-h heat series per building. CHA (pandapipes) and DHA (pandapower) consume LFA **in parallel**: CHA converts heat to mass-flow sinks via $\dot m = \frac{Q_{kW}\cdot1000}{c_p\Delta T}$, DHA converts to electric load via $P_{el} = \frac{Q}{COP(h)}$. EAA **joins** CHA+DHA outputs and runs a vectorized Monte Carlo to estimate $\mathrm{LCoH}$ and CO₂ (mean, median, 95% CI). TCA validates the KPI contract and emits a schema-compliant decision JSON with rationale; CAA bundles diagnostics.

### **Core Dataflow: Fork-Join DAG (LFA → {CHA, DHA} → EAA → TCA → CAA)**

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           BRANITZ ENERGY DECISION AI                            │
│                              Multi-Agent Pipeline (DAG)                         │
└─────────────────────────────────────────────────────────────────────────────────┘

                 ┌──────────────────────────┐
                 │  LFA — Load forecasts    │
                 │  per building (8760 h)   │
                 │  processed/lfa/*.json    │
                 └─────────────┬────────────┘
                               │  fan-out
               ┌───────────────┴───────────────┐
               │                               │
┌──────────────▼──────────────┐   ┌────────────▼──────────────┐
│ CHA — Centralized Heating   │   │ DHA — Decentralized/HP     │
│ (district heating network)  │   │ (electric grid impact)     │
│ uses LFA → ṁ sinks (design │   │ uses LFA → electric load   │
│ /top-N hours) in pandapipes │   │ (via COP) into pandapower  │
│ processed/cha/*             │   │ processed/dha/*            │
└──────────────┬──────────────┘   └────────────┬──────────────┘
               │                               │
               └───────────────┬───────────────┘  join
                               │
                   ┌───────────▼───────────┐
                   │ EAA — Economics/TE    │
                   │ Monte Carlo LCoH & CO₂│
                   │ eval/te/*             │
                   └───────────┬───────────┘
                               │
                   ┌───────────▼───────────┐
                   │ TCA — KPI/Decision    │
                   │ processed/kpi/*.json  │
                   └───────────┬───────────┘
                               │
                   ┌───────────▼───────────┐
                   │ CAA — DoD + Bundle    │
                   │ eval/caa/diagnostics  │
                   └────────────────────────┘
```

---

## 🤖 Agent Specifications

### **1. Load Forecasting Agent (LFA)**
- **Module**: `agents/lfa.py`
- **Makefile Target**: `make lfa`
- **Purpose**: Generate 8760-hour load forecasts for all buildings
- **Input**: Building data, weather data, historical consumption
- **Output**: `processed/lfa/*.json` (individual building forecasts)
- **Schema**: `schemas/lfa_demand.schema.json`

### **2. Centralized Heating Agent (CHA)**
- **Module**: `src/cha.py`, `src/cha_interactive.py`
- **Makefile Targets**: `make cha`, `make cha-interactive`
- **Purpose**: District heating network design and hydraulic simulation
- **Input**: LFA forecasts (heat → mass flows), building data, street network
- **Transform**: 
  - Convert LFA heat to mass flow: `ṁ_kg/s = (Q_kW * 1000) / (c_p * ΔT)`
  - Map building_id → nearest junction (service connections)
  - Create pandapipes sinks with `ṁ_kg/s`; run `pp.pipeflow`
- **Output**: 
  - `processed/cha/segments.csv` - Network segments
  - `eval/cha/hydraulics_check.csv` - Velocity & pressure compliance
  - `processed/cha/*.gpkg` - Geospatial network data
  - `processed/cha/*.html` - Interactive maps and dashboards
- **Simulation**: Pandapipes hydraulic analysis

### **3. Decentralized Heating Agent (DHA)**
- **Module**: `src/dha.py`, `src/dha_interactive.py`
- **Makefile Targets**: `make dha`, `make dha-interactive`
- **Purpose**: Heat pump feasibility analysis and power flow simulation
- **Input**: LFA forecasts (heat → electric load), building data, power infrastructure
- **Transform**:
  - Convert heat to electric load: `P_el_kW[h] = Q_kW[h] / COP[h]`
  - Aggregate to feeders; run heuristic utilization or pandapower power-flow
- **Output**:
  - `processed/dha/feeder_loads.csv` - Feeder load analysis
  - `eval/dha/violations.csv` - Power quality violations
  - `processed/dha/*.html` - Interactive maps and dashboards
- **Simulation**: Pandapower load flow analysis

### **4. Economics Analysis Agent (EAA)**
- **Module**: `src/te.py` (referenced in Makefile)
- **Makefile Target**: `make te`
- **Purpose**: Monte Carlo LCoH and CO₂ emissions analysis
- **Input**: CHA results (capex, pumping energy), DHA results (grid upgrades, electrical energy), LFA totals
- **Transform**: Vectorized Monte Carlo (≥500/1000 samples) over cost/energy/CO₂ drivers
- **Output**:
  - `eval/te/mc.parquet` - Monte Carlo simulation results
  - `eval/te/summary.csv` - LCoH & CO₂ statistics

### **5. Techno-Economic Analysis Agent (TCA)**
- **Module**: `src/te.py` (referenced in Makefile)
- **Makefile Target**: `make te`
- **Purpose**: KPI generation and decision support
- **Input**: EAA summary + selected CHA/DHA KPIs + forecast quality
- **Output**:
  - `processed/kpi/kpi_summary.json` - Key performance indicators
- **Schema**: `schemas/kpi_summary.schema.json`

### **6. Comprehensive Analysis Agent (CAA)**
- **Module**: `src/caa.py`
- **Makefile Target**: `make caa`
- **Purpose**: Bundle all artifacts and generate diagnostics
- **Input**: All previous agent outputs
- **Output**: `eval/caa/diagnostics.zip` - Complete analysis bundle

---

## 📁 Key Artifacts & Data Contracts

### **Input Data Sources**
```
data/
├── geojson/
│   └── hausumringe_mit_adressenV3.geojson  # Building data (2079 buildings)
├── processed/
│   ├── power_*.geojson                     # Power infrastructure (OSM data)
│   └── weather.parquet                     # Weather data
└── raw/                                    # Raw input data
```

### **LFA Artifacts (Fan-out to CHA & DHA)**
```
processed/lfa/
├── B001.json                               # Building 1: 8760h load forecast
├── B002.json                               # Building 2: 8760h load forecast
├── ...
└── B050.json                               # Building 50: 8760h load forecast

Schema: schemas/lfa_demand.schema.json
Contract: Both CHA & DHA read the same LFA artifacts
```

### **CHA Artifacts (Parallel with DHA)**
```
processed/cha/
├── segments.csv                            # Network segments data
├── cha.gpkg                               # Geospatial network (QGIS compatible)
├── network_map.html                       # Interactive network map
├── supply_pipes.csv                       # Supply pipe network
├── return_pipes.csv                       # Return pipe network
└── service_connections.csv                # Building connections

eval/cha/
├── hydraulics_check.csv                   # Velocity & pressure compliance
└── simplified_hydraulics_check.csv        # Pandapipes simulation results

Street-specific outputs:
├── An_der_Bahn/
│   ├── buildings_An_der_Bahn.geojson
│   ├── dual_pipe_dashboard_*.html
│   └── dual_pipe_map_*.html
└── Böcklinplatz/
    ├── buildings_Böcklinplatz.geojson
    ├── comprehensive_dashboard_*.html
    └── enhanced_dashboard_*.html
```

### **DHA Artifacts (Parallel with CHA)**
```
processed/dha/
├── feeder_loads.csv                       # Feeder load analysis
└── [Street_Name]/
    ├── buildings_analysis.geojson         # Building analysis results
    ├── dha_interactive_map_*.html         # Interactive power flow map
    └── dha_dashboard_*.html               # Comprehensive dashboard

eval/dha/
└── violations.csv                         # Power quality violations
```

### **EAA Artifacts (Join Point)**
```
eval/te/
├── mc.parquet                            # Monte Carlo simulation results
└── summary.csv                           # LCoH & CO₂ statistics
```

### **TCA Artifacts**
```
processed/kpi/
└── kpi_summary.json                      # Key performance indicators

Schema: schemas/kpi_summary.schema.json
```

### **CAA Artifacts**
```
eval/caa/
└── diagnostics.zip                       # Complete analysis bundle
    ├── manifest.json                     # Analysis metadata
    ├── processed/                        # All processed artifacts
    ├── eval/                            # All evaluation results
    └── docs/                            # Generated reports
```

---

## 🔄 Enhanced Multi-Agent System

### **Simplified Multi-Agent Architecture**
```
┌─────────────────────────────────────────────────────────────────┐
│                    Enhanced Multi-Agent System                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────┐
│ EnergyPlanner   │ ◄─── User Request
│    Agent        │
└─────────────────┘
         │
         ▼ (Delegation)
┌─────────────────┐
│ Specialist      │
│    Agents       │
└─────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│   CHA   │ │   DHA   │ │   CA    │ │   DEA   │
│District │ │Heat Pump│ │Compare  │ │Explore  │
│Heating  │ │Analysis │ │Scenarios│ │Data     │
└─────────┘ └─────────┘ └─────────┘ └─────────┘
    │           │           │           │
    ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────┐
│              Enhanced Tools                     │
│  • Real power infrastructure integration       │
│  • Interactive map generation                  │
│  • Comprehensive dashboard creation            │
│  • Street-following routing                    │
│  • Pandapipes/Pandapower simulation           │
└─────────────────────────────────────────────────┘
```

### **Enhanced Agent Modules**
- **`src/simplified_agent_system.py`** - Multi-agent orchestration
- **`src/enhanced_agents.py`** - ADK-based agent definitions
- **`src/enhanced_tools.py`** - Comprehensive analysis tools

### **Interactive Capabilities**
- **Natural Language Interface** - "analyze heat pump feasibility for Parkstraße"
- **Real-time Agent Delegation** - Automatic routing to specialist agents
- **Interactive Maps** - Multi-layer Folium visualizations
- **Comprehensive Dashboards** - HTML reports with embedded visualizations

---

## 🚀 Execution Commands

### **Individual Agent Execution**
```bash
make lfa              # Load forecasting
make cha              # District heating analysis
make dha              # Heat pump analysis
make te               # Techno-economic analysis
make caa              # Comprehensive analysis
```

### **Interactive Systems**
```bash
make cha-interactive  # Interactive district heating
make dha-interactive  # Interactive heat pump analysis
```

### **Multi-Agent System**
```bash
make enhanced-agents      # Full multi-agent system
make test-enhanced-agents # Test all agents
```

### **End-to-End Pipeline**
```bash
make run-branitz      # Complete LFA→{CHA,DHA}→EAA→TCA→CAA pipeline
```

### **Parallel Execution (Fork-Join)**
```bash
# CHA and DHA can run in parallel after LFA completes
make -j 2 cha dha     # Parallel execution of CHA and DHA
```

---

## 📋 Data Contracts & Practical Alignment

### **LFA → (CHA & DHA) [Fan-out]**

**Files**: `processed/lfa/{building_id}.json`
**Schema (essentials)**:
- `x-version` (semver), `building_id`
- `series` (len 8760, kW), `q10`, `q90`
- `metadata.forecast_date`, `model_version`

> Both CHA & DHA read the **same** LFA artifacts. No dependency between CHA and DHA.

### **CHA Transform (Heat → Mass Flows)**
- **Input**: LFA per-building hourly heat: `Q_kW[h]`
- **Transform**: 
  - Pick **design hour** or **top-N peak hours**
  - Convert heat to mass flow: `ṁ_kg/s = (Q_kW * 1000) / (c_p * ΔT)`
  - Map **building_id → nearest junction** (service connections)
  - Create pandapipes **sinks** with `ṁ_kg/s`; run `pp.pipeflow`

### **DHA Transform (Heat → Electric Load)**
- **Input**: LFA per-building hourly heat: `Q_kW[h]`
- **Transform**:
  - Convert heat to electric load: `P_el_kW[h] = Q_kW[h] / COP[h]`
  - Aggregate to feeders; run heuristic utilization or **pandapower** power-flow

### **EAA Transform (Join Point)**
- **Input**: CHA results (capex, pumping energy), DHA results (grid upgrades, electrical energy), LFA totals
- **Transform**: Vectorized **Monte Carlo** (≥500/1000 samples) over cost/energy/CO₂ drivers

### **Practical Alignment Details**
- **ID Mapping**: Ensure `building_id` in LFA JSON matches IDs used by CHA (service-connection mapping) and DHA (feeder assignment)
- **Time Indexing**: All hourly series use the same **timezone** and **index origin** (e.g., UTC or Europe/Berlin)
- **Design/Top-N Hours**: For CHA, choose hours from the **same LFA series** used by DHA; document ΔT and COP assumptions per hour
- **Contracts**: Keep `x-version` in schemas and bump with MIGRATIONS.md when changing fields

---

## 📋 Schema Contracts

### **LFA Demand Schema** (`schemas/lfa_demand.schema.json`)
```json
{
  "type": "object",
  "properties": {
    "building_id": {"type": "string"},
    "forecast_hours": {"type": "integer"},
    "demand_profile": {
      "type": "array",
      "items": {"type": "number"}
    },
    "metadata": {
      "type": "object",
      "properties": {
        "scenario": {"type": "string"},
        "timestamp": {"type": "string"}
      }
    }
  }
}
```

### **KPI Summary Schema** (`schemas/kpi_summary.schema.json`)
```json
{
  "type": "object",
  "properties": {
    "analysis_date": {"type": "string"},
    "scenario": {"type": "string"},
    "metrics": {
      "type": "object",
      "properties": {
        "lcoh_eur_per_mwh": {"type": "number"},
        "co2_emissions_t_per_a": {"type": "number"},
        "capex_eur": {"type": "number"},
        "opex_eur": {"type": "number"}
      }
    }
  }
}
```

---

## ✅ Verification & Quality Assurance

### **Definition of Done (DoD)**
- **Schema Validation** - All JSON outputs validated against schemas
- **Artifact Presence** - Required files generated and accessible
- **Simulation Convergence** - Pandapipes/Pandapower simulations successful
- **Interactive Functionality** - Maps and dashboards working
- **Data Integrity** - Real infrastructure data properly integrated

### **Testing Commands**
```bash
make verify              # Lint + format + tests + schema validation
make test-enhanced-agents # Multi-agent system testing
```

---

## 🎯 Key Features

### **Real Data Integration**
- ✅ **OpenStreetMap Power Infrastructure** - Real substations, lines, plants
- ✅ **Building Data** - 2079 real buildings from Cottbus
- ✅ **Street Network** - Actual street geometry for routing

### **Advanced Simulations**
- ✅ **Pandapipes** - Hydraulic analysis for district heating
- ✅ **Pandapower** - Load flow analysis for heat pumps
- ✅ **Street-Following Routing** - Realistic network construction

### **Interactive Visualizations**
- ✅ **Multi-Layer Maps** - Buildings, infrastructure, networks
- ✅ **Layer Control** - Toggle visibility of different elements
- ✅ **Comprehensive Dashboards** - Technical and economic metrics

### **Multi-Agent Coordination**
- ✅ **Intelligent Delegation** - Automatic agent selection
- ✅ **Natural Language Interface** - User-friendly interaction
- ✅ **Comprehensive Analysis** - End-to-end pipeline execution

## 🔍 Verification Commands

### **One-liners for Cursor to verify the fork-join DAG**

**LFA present for multiple buildings**:
```python
from pathlib import Path
lfa_files = list(Path("processed/lfa").glob("*.json"))
assert len(lfa_files) > 0
print(f"Found {len(lfa_files)} LFA files")
```

**CHA & DHA independence**:
```python
# CHA and DHA succeed when LFA exists; neither reads the other's outputs
# (pseudo-check: look for file reads)
import subprocess
result = subprocess.run(['grep', '-r', 'processed/dha', 'src/cha*'], 
                       capture_output=True, text=True)
assert result.returncode != 0, "CHA should not read DHA outputs"

result = subprocess.run(['grep', '-r', 'processed/cha', 'src/dha*'], 
                       capture_output=True, text=True)
assert result.returncode != 0, "DHA should not read CHA outputs"
```

**Join at EAA/TCA**:
```python
# EAA should read processed/cha/* and processed/dha/*; TCA should read EAA + CHA/DHA
import os
assert os.path.exists("processed/cha/segments.csv"), "CHA outputs missing"
assert os.path.exists("processed/dha/feeder_loads.csv"), "DHA outputs missing"
assert os.path.exists("eval/te/summary.csv"), "EAA outputs missing"
assert os.path.exists("processed/kpi/kpi_summary.json"), "TCA outputs missing"
```

### **Parallel Execution Verification**
```bash
# Test parallel execution capability
make -j 2 cha dha  # Should run CHA and DHA in parallel
```

---

## 🎯 Summary

This system represents a complete transformation from legacy single-agent approaches to a sophisticated **fork-join DAG** multi-agent platform with:

- ✅ **Real Data Integration** - OpenStreetMap power infrastructure
- ✅ **Advanced Simulations** - Pandapipes/Pandapower with convergence
- ✅ **Interactive Visualizations** - Multi-layer maps with layer control
- ✅ **Multi-Agent Coordination** - Intelligent delegation system
- ✅ **Schema Validation** - JSON contracts for all artifacts
- ✅ **Natural Language Interface** - User-friendly interaction
- ✅ **Parallel Execution** - CHA and DHA can run independently after LFA
- ✅ **Fork-Join Architecture** - LFA fans out to CHA & DHA, they join at EAA
