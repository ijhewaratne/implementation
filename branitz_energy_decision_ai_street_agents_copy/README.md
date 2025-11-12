# Branitz Energy Decision AI - Agent System

A sophisticated multi-agent system for urban energy planning with **real physics-based simulations** using pandapipes (District Heating) and pandapower (Heat Pumps). Natural language interface powered by AI agents, backed by accurate engineering calculations.

## ⚡ **NEW: Real Physics Simulations**

This system now includes **production-grade energy simulations**:
- ✅ **Real pandapipes** hydraulic + thermal simulation for District Heating
- ✅ **Real pandapower** 3-phase power flow for Heat Pump grid analysis
- ✅ **12-13 detailed KPIs** from each simulation (not placeholders!)
- ✅ **Automatic fallback** to estimates if simulations fail
- ✅ **Configuration-driven** - easily adjust parameters via YAML files

## 🤖 Agent Architecture

The system consists of **7 specialized agents** working together:

### **1. EnergyPlannerAgent** 🎯
- **Role**: Master orchestrator and delegation manager
- **Function**: Analyzes user requests and delegates to appropriate specialist agents
- **Tools**: None (delegation only)

### **2. CentralHeatingAgent (CHA)** 🔥
- **Role**: District Heating specialist
- **Function**: Executes complete DH scenario analysis
- **Tools**: Building extraction, network creation, simulation, visualization, analysis

### **3. DecentralizedHeatingAgent (DHA)** ❄️
- **Role**: Heat Pump specialist  
- **Function**: Executes complete HP scenario analysis
- **Tools**: Building extraction, network creation, simulation, visualization, analysis

### **4. ComparisonAgent (CA)** ⚖️
- **Role**: Scenario comparison expert
- **Function**: Runs both DH and HP scenarios and provides side-by-side comparison
- **Tools**: Scenario comparison

### **5. AnalysisAgent (AA)** 📊
- **Role**: Comprehensive analysis specialist
- **Function**: Runs complete end-to-end analysis with visualization
- **Tools**: Complete analysis pipeline

### **6. DataExplorerAgent (DEA)** 🔍
- **Role**: Data exploration and results management
- **Function**: Helps users explore available data and results
- **Tools**: Street listing, results listing, KPI analysis

### **7. EnergyGPT** 🧠
- **Role**: AI-powered analysis and reporting
- **Function**: Generates natural language insights from KPI data
- **Tools**: KPI analysis

## 🚀 Quick Start

### 1. Environment Setup
```bash
conda activate branitz_env
cd branitz_energy_decision_ai_street_agents

# Install simulation libraries (for real physics)
pip install pandapipes pandapower geopandas shapely pandas folium branca pyyaml
```

### 2. Enable Real Simulations (Optional)

**By default, the system uses safe placeholder simulations.**

To enable real physics-based simulations:

```bash
# Edit config/feature_flags.yaml
# Change: use_real_simulations: false
# To:     use_real_simulations: true
```

### 3. Run the Agent System
```bash
python run_agent_system.py
```

### 4. Verify Real Simulations Are Active

Check the console output:
```
→ Using REAL pandapipes simulation  ← You'll see this!
  Running pandapipes simulation...
  Simulation converged successfully!
```

### 3. Interactive Usage
The system will present you with options:
- `analyze district heating for [street]` - Run DH scenario
- `analyze heat pumps for [street]` - Run HP scenario
- `compare scenarios for [street]` - Compare both DH and HP
- `comprehensive analysis for [street]` - Full analysis with visualization
- `create interactive map for [scenario]` - **NEW!** Generate HTML map with color gradients
- `create dashboard for [scenario]` - **NEW!** Generate 12-panel summary dashboard
- `create comparison dashboard for [dh] vs [hp]` - **NEW!** DH vs HP comparison
- `create HTML dashboard for [scenario]` - **NEW!** Generate comprehensive HTML web page (Phase 7)
- `show available streets` - List all streets in dataset
- `show results` - List all generated files

## 🎨 **NEW: Advanced Visualizations** (Phase 6 & 7)

The system now includes **professional visualizations and comprehensive HTML dashboards**:

### **Interactive HTML Maps** 🗺️
- **Folium/Leaflet.js** web-based maps
- **Temperature cascading gradients** (DH): Red supply pipes → Blue return pipes
- **Voltage cascading gradients** (HP): Green (normal) → Yellow (warning) → Red (violation)
- **Clickable elements** with detailed KPI popups
- **Hover tooltips** with real-time data
- **Statistics panels** and performance dashboards
- **Layer controls** (show/hide network elements)
- **Works on any browser** (desktop & mobile)

### **12-Panel Summary Dashboards** 📊
- **High-resolution** (300 DPI) PNG suitable for reports
- **Comprehensive analysis** in one view:
  - Key Performance Indicators
  - Network topology schematic
  - Thermal/voltage performance
  - Hydraulic/loading metrics
  - Efficiency indicators
  - Technical specifications
  - Performance scores (0-100)
  - Summary statistics
- **Color-coded** performance indicators (green/yellow/red)
- **DH-specific**: Thermal performance, heat losses, hydraulic analysis
- **HP-specific**: Voltage profile, line loading, transformer analysis

### **DH vs HP Comparison Dashboards** ⚖️
- **Side-by-side comparison** of scenarios
- **Economic metrics**: LCoH, CAPEX, OPEX
- **Environmental metrics**: CO₂ emissions
- **Technical metrics**: Network characteristics, efficiency
- **Automated recommendation** with winner highlighting
- **Score breakdown**: Economic, environmental, technical

### **HTML Dashboards** 🌐 **(NEW in Phase 7!)**
- **Comprehensive web pages** combining all information
- **Embedded interactive maps** (iframe) - explore network in-browser
- **Embedded charts** (base64-encoded) - all analysis in one place
- **Professional styling** - gradient backgrounds, shadows, animations
- **Responsive design** - works on desktop, tablet, and mobile
- **JavaScript interactivity** - smooth scrolling, hover effects
- **Self-contained** - single HTML file with everything embedded
- **Open in any browser** - Chrome, Firefox, Safari, Edge
- **Easy to share** - just send the HTML file!

### **Usage Examples**

```bash
# Run analysis
"analyze district heating for Parkstraße"

# Create interactive map
"create interactive map for Parkstrasse_DH"
→ Generates HTML file with temperature gradients

# Create summary dashboard
"create dashboard for Parkstrasse_DH"
→ Generates 12-panel PNG (300 DPI)

# Compare scenarios with dashboard
"compare Parkstrasse_DH and Parkstrasse_HP with dashboard"
→ Generates comparison PNG with automated recommendation

# Create HTML dashboard (Phase 7!)
"create HTML dashboard for Parkstrasse_DH"
→ Generates comprehensive HTML web page with embedded map and charts
```

### **Color-Coded Gradients**

**DH Networks (Temperature-Based):**
- 🔴 **Red (Crimson)** → Supply pipes (70-85°C, hot)
- 🔵 **Blue (SteelBlue)** → Return pipes (40-55°C, cold)
- 🟠 **Orange** → Heat consumers
- 🟢 **Green** → CHP plant

**HP Networks (Voltage-Based):**
- 🟢 **Green** → Normal voltage (0.95-1.05 pu)
- 🟡 **Yellow/Orange** → Warning zone (0.92-0.95 or 1.05-1.08 pu)
- 🔴 **Red** → Violation (<0.92 or >1.08 pu)

**Customization:**
All colors, colormaps, and settings can be customized in `config/visualization_config.yaml` without changing code!

## 🔬 Real Physics Simulations

### **District Heating (DH) - pandapipes**

**What It Does:**
- Creates hydraulic network model with supply/return circuits
- Calculates pressure drops and flow rates in each pipe
- Models heat exchangers at consumer buildings
- Computes temperature losses along network
- Estimates pump energy consumption

**KPIs Extracted (12 total):**
- Heat supply: Total heat (MWh), peak load (kW)
- Hydraulics: Pressure drops (bar), pump energy (kWh)
- Thermal: Supply temperatures (°C), heat losses (%)
- Network: Junction/pipe counts, total length (km)

**Example Result:**
```
Total heat supplied: 234.5 MWh
Max pressure drop: 0.42 bar
Pump energy: 4,823 kWh
Network: 32 junctions, 30 pipes (1.2 km)
Execution time: 12.3s
```

### **Heat Pump (HP) - pandapower**

**What It Does:**
- Creates 3-phase LV electrical distribution network
- Models MV/LV transformer and cables
- Adds heat pump loads (thermal power / COP)
- Runs power flow to calculate voltages and currents
- Detects constraint violations (voltage, overloads)

**KPIs Extracted (13 total):**
- Voltage: Min/max/avg voltage (pu), violations
- Loading: Line loadings (%), overloads
- Transformer: Loading (%), overload status
- Losses: Grid losses (MW), loss percentage (%)
- Network: Bus/line/load counts

**Example Result:**
```
Min voltage: 0.948 pu
Max line loading: 78.3%
Transformer loading: 65.4%
Voltage violations: 2 buses
Total losses: 0.023 MW (3.2%)
Execution time: 8.7s
```

### **Simulation Mode Indicator**

Every result now includes:
```python
result = {
    "mode": "real",        # or "placeholder"
    "success": True,
    "kpi": {...},          # Detailed KPIs
    "warnings": [...]      # Any issues detected
}
```

### **HP Street Workflow Inputs & Configuration**

The HP street workflow mirrors the proven `street_final_copy_3/HP New` implementation. To reproduce the Branitz case studies ensure the following artefacts exist under `data/`:

- `branitzer_siedlung_ns_v3_ohne_UW.json` – LV nodes/ways backbone exported from OSM
- `gebaeude_lastphasenV2.json` – base electrical load catalogue (values often in **MW**)
- `output_branitzer_siedlungV11.json` – building footprints/centroids (fallback: the workflow can derive centroids from `branitzer_siedlung.osm`)

Key configuration knobs (tweak either via CLI or the scenario/simulation YAMLs):

| Parameter | Location | Purpose |
|-----------|----------|---------|
| `buffer_m` | `run_hp_street_workflow(street, buffer_m=…)` | Radius around the selected street used to filter buildings (default 50 m) |
| `hp_thermal_kw` | `config/simulation_config.yaml` / scenario JSON | Thermal power per building injected for HP rollout |
| `hp_cop` | same | Converts thermal to electrical load (`P_el = kW_th / COP`) |
| `hp_three_phase` | same | Toggle balanced 3-phase vs. single-phase HP allocation (imbalance study) |
| `load_profile_name` | `scenarios/hp_with_grid_reinforcement_scenario.json` | Selects the slice from `gebaeude_lastphasenV2.json` (e.g. `winter_werktag_abendspitze`) |
| `load_profile_file` / `nodes_file` | scenario JSON | Points to the Branitz load catalogue and LV topology exports |
| `baseline_scenario` / `variant_scenario` | `compare_hp_variants` tool | Choose which two HP scenarios to compare (e.g. `hp_base_case` vs `hp_with_grid_reinforcement`) |

One-line example using the new agent tool:

```python
from energy_tools import run_hp_street_workflow
print(run_hp_street_workflow("Anton-Bruckner-Straße", buffer_m=50.0))

from energy_tools import compare_hp_variants
print(compare_hp_variants("Anton-Bruckner-Straße"))
```

The response returns min voltage, max loading, transformer loading, violation counts, connected-building totals, and direct links to the exported artefacts.

### **Interpreting HP Outputs**

Each run writes a consistent set of artefacts under `street_analysis_outputs/<Street>/hp/<Scenario>/`:

- `*_lines_results.geojson` – LV segments with `loading_pct`, `length_m`, and a categorical `loading_status`
- `*_buses_results.geojson` – LV buses with `voltage_pu`, `load_kw`, `voltage_status`, and `is_transformer`
- `*_kpis.json` – Snapshot of the headline KPIs (min voltage, max loading, transformer loading, losses, element counts)
- `*_violations.csv` – Generated when voltage or loading thresholds are breached (`undervoltage` and `line_overload` severities)
- `*_hp_lv_map.html` – Folium map showing voltage gradients on buses and loading gradients on lines (red elements highlight violations)

Legacy interpretation tips still apply:

- **Red lines** indicate overloaded segments; **amber** shows segments approaching the limit.
- **Red buses** highlight voltages below `limits.voltage_min_pu` (see `config/simulation_config.yaml`).
- Set `hp_thermal_kw = 0` to baseline the existing LV grid without extra HP demand.
- Toggle `hp_three_phase = False` to observe worst-case single-phase imbalance.
- Use the KPI JSON and violations CSV to support reinforcement recommendations (cable upsizing, parallel feeders, transformer upgrades, etc.).

## 🛠️ Available Tools

### **Data Exploration Tools**
- `get_all_street_names()` - Lists all 27 available streets
- `get_building_ids_for_street(street_name)` - Extracts building IDs for a street
- `list_available_results()` - Shows all generated files

### **Network & Visualization Tools**
- `create_network_graph(building_ids, output_dir)` - Creates building network
- `create_network_visualization(output_dir)` - Generates high-quality plots (PNG + PDF)

### **Simulation & Analysis Tools** (⚡ Now with real physics!)
- `run_simulation_pipeline(building_ids, scenario_type)` - **Runs real pandapipes/pandapower**
- `run_complete_analysis(street_name, scenario_type)` - Complete end-to-end with **real simulations**
- `compare_scenarios(street_name)` - Compares DH vs HP with **real calculations**
- `analyze_kpi_report(kpi_path)` - AI-powered KPI analysis
- `run_hp_street_workflow(street_name, scenario="hp_with_grid_reinforcement")` - Advanced HP street workflow with KPI/artefact digest
- `compare_hp_variants(street_name, base="hp_base_case", variant="hp_with_grid_reinforcement")` - Run two HP scenarios for the same street and report KPI deltas

## 📋 Example Usage

### **District Heating Analysis**
```
🎯 Your request: analyze district heating for Parkstraße

🤔 Planner Agent is thinking...
🎯 Planner delegated to CentralHeatingAgent.

⚡ CentralHeatingAgent is executing your request...
TOOL: Searching for buildings on 'Parkstraße'...
TOOL: Found 15 buildings.
TOOL: Creating network graph for 15 buildings...
TOOL: Starting pipeline for 15 buildings. Scenario type: DH
TOOL: Creating network visualization...
TOOL: Analyzing KPI report...

📊 CentralHeatingAgent Response:
[Complete analysis results]

🔍 Running additional analysis...
📈 Analyzing KPI report...
📋 AI Analysis:
[AI-generated insights]

✅ Request completed successfully!
```

### **Scenario Comparison**
```
🎯 Your request: compare scenarios for Liebermannstraße

🤔 Planner Agent is thinking...
🎯 Planner delegated to ComparisonAgent.

⚡ ComparisonAgent is executing your request...
TOOL: Comparing DH and HP scenarios for 'Liebermannstraße'...

📊 ComparisonAgent Response:
=== SCENARIO COMPARISON FOR LIEBERMANNSTRASSE ===
Buildings Analyzed: 105

DISTRICT HEATING (DH) SCENARIO:
[DH results]

HEAT PUMP (HP) SCENARIO:
[HP results]

KPI COMPARISON:
[Detailed comparison table]

RECOMMENDATION:
• Cost: Heat Pumps are 37.6% cheaper (€110.37 vs €176.88/MWh)
• Emissions: District Heating produces 12.18 fewer tons CO₂/year
• Recommendation: Heat Pumps based on cost priority

✅ Request completed successfully!
```

## 🎯 Agent Capabilities

### **Intelligent Delegation**
- Automatically routes requests to appropriate specialists
- Handles natural language queries
- Provides clear feedback on agent selection

### **Comprehensive Analysis**
- Building extraction and validation
- Network graph creation with minimum spanning trees
- Energy demand calculation
- Load profile generation
- Multi-scenario simulation
- KPI calculation and comparison
- AI-powered insights and recommendations

### **High-Quality Visualization**
- Network topology maps
- Building-to-street connections
- Service line layouts
- Multiple output formats (PNG, PDF, GeoJSON)

### **Data Management**
- Automatic file organization
- Result tracking and listing
- Error handling and recovery
- Progress feedback

## 🔧 Technical Features

### **Multi-Agent Coordination**
- Specialized agent roles
- Tool sharing and coordination
- Error handling and recovery
- Progress tracking

### **Comprehensive Toolset**
- 9 specialized tools
- Automatic tool chaining
- Result validation
- File management

### **User Experience**
- Natural language interface
- Clear progress indicators
- Comprehensive error messages
- Helpful suggestions

## 📊 Output Files

The system generates the same comprehensive outputs as the main system:

### **Network Files**
- `network_graph_*.json` - Building network topology
- `service_connections_*.geojson` - Building-to-street connections
- `buildings_projected_*.geojson` - Building geometries

### **Analysis Files**
- `scenario_kpis.csv` - Key performance indicators
- `scenario_kpis.json` - KPI data in JSON format
- `llm_final_report.md` - AI-generated analysis report

### **Visualization Files**
- `network_visualization.png` - High-resolution network map
- `network_visualization.pdf` - Vector format for printing

## 🚀 Advanced Usage

### **Testing Mode**
```bash
# Test individual agents
python run_agent_system.py test

# Test complete pipeline
python run_agent_system.py pipeline
```

### **Custom Analysis**
The agents can handle various request formats:
- "analyze central heating for Parkstraße"
- "run heat pump simulation for Liebermannstraße"
- "compare district heating vs heat pumps for Petzoldstraße"
- "show me all available streets"
- "what results do we have?"

## 🔍 Troubleshooting

### **Common Issues**
1. **Missing Dependencies**: Ensure `branitz_env` is activated
2. **File Not Found**: Check data file paths in configuration
3. **Agent Errors**: Review agent responses for specific issues
4. **Tool Failures**: Check tool output for detailed error messages

### **Error Recovery**
- Agents automatically handle most errors
- System provides clear error messages
- Failed operations can be retried
- Partial results are preserved

## 🎯 Key Advantages

### **vs. Main System**
- **Intelligent Delegation**: Automatically routes to appropriate specialists
- **Natural Language Interface**: More user-friendly interaction
- **Specialized Expertise**: Each agent has deep knowledge in their domain
- **Better Error Handling**: More robust error recovery
- **Enhanced Visualization**: Automatic plot generation and saving

### **vs. Traditional Tools**
- **AI-Powered Analysis**: Natural language insights and recommendations
- **Comprehensive Coverage**: End-to-end analysis pipeline
- **Multi-Scenario Comparison**: Side-by-side DH vs HP analysis
- **Interactive Exploration**: Easy data and result exploration

## 📈 Performance

- **Speed**: Optimized agent delegation reduces processing time
- **Accuracy**: Specialized agents provide more focused analysis
- **Reliability**: Robust error handling and recovery
- **Scalability**: Modular design supports easy expansion

The agent system provides the same comprehensive energy analysis capabilities as the main system, but with enhanced user experience, intelligent delegation, and specialized expertise through its multi-agent architecture.
