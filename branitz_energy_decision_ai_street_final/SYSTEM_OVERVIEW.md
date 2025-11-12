# 🏗️ Branitz Energy Decision AI - Complete System Overview

## 🎯 **System Purpose**
A comprehensive multi-agent energy infrastructure analysis platform that compares **District Heating (DH)** vs **Heat Pumps (HP)** for urban energy planning, providing physics-based simulations, interactive visualizations, and AI-powered recommendations.

---

## 🏛️ **System Architecture**

### **Fork-Join DAG Data Flow**
```
                  ┌──────────────────────────┐
                  │  Heat Demand Analysis    │
                  │  (Thesis Data Integration)│
                  │  processed/lfa/*.json    │
                  └─────────────┬────────────┘
                                │  fan-out
                ┌───────────────┴───────────────┐
                │                               │
┌──────────────▼──────────────┐   ┌────────────▼──────────────┐
│ CHA — Centralized Heating   │   │ DHA — Decentralized/HP     │
│ (district heating network)  │   │ (electric grid impact)     │
│ uses heat demand → ṁ sinks │   │ uses heat demand → electric│
│ (design hours) in pandapipes│   │ load (via COP) into pandapower│
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

## 🤖 **Multi-Agent System**

### **Core Agents (Production System)**
1. **Heat Demand Analysis** (LFA Replacement)
   - **Input**: TRY weather data + building physics
   - **Output**: 8760-hour heat demand profiles
   - **Technology**: Physics-based calculations

2. **Centralized Heating Agent (CHA)**
   - **Function**: District heating network design & simulation
   - **Technology**: Pandapipes, NetworkX, Folium
   - **Output**: Network topology, hydraulic analysis, interactive maps

3. **Decentralized Heating Agent (DHA)**
   - **Function**: Heat pump grid impact analysis
   - **Technology**: Pandapower, electrical load analysis
   - **Output**: Grid utilization, voltage analysis, electrical maps

4. **Economics Analysis Agent (EAA)**
   - **Function**: Monte Carlo cost & emissions analysis
   - **Technology**: Statistical modeling, cost optimization
   - **Output**: LCoH distributions, CO₂ analysis

5. **Techno-Economic Analysis Agent (TCA)**
   - **Function**: KPI generation & decision support
   - **Technology**: Schema validation, decision algorithms
   - **Output**: Comprehensive KPIs, recommendations

6. **Comprehensive Analysis Agent (CAA)**
   - **Function**: Artifact bundling & DoD validation
   - **Technology**: File management, validation
   - **Output**: Diagnostics bundles, compliance reports

### **Enhanced Agents (AI-Powered)**
7. **EnergyPlannerAgent** 🎯
   - **Role**: Master orchestrator and delegation manager
   - **AI**: Gemini-powered natural language interface

8. **EnergyGPT** 🧠
   - **Role**: AI-powered KPI analysis and recommendations
   - **AI**: Real-time Gemini API integration
   - **Function**: Natural language insights from data

9. **Specialist Agents** (CHA, DHA, Comparison, Analysis, DataExplorer)
   - **AI**: Gemini-powered analysis and tool delegation
   - **Function**: Intelligent scenario analysis and comparison

---

## 📊 **Data Sources & Processing**

### **Primary Data Sources**
1. **TRY Weather Data** (8760 hours)
   - Source: `thesis-data-2/wetter-data/`
   - Format: TRY .dat files
   - Usage: Temperature-dependent heat demand

2. **Building Physics Data**
   - Source: `thesis-data-2/pipes-sim/ergebnis_momentane_heizleistungV3.json`
   - Format: Physics-based heating calculations
   - Usage: Realistic heat demand profiles

3. **Geospatial Data**
   - Streets: `agents copy/data/geojson/strassen_mit_adressenV3.geojson`
   - Buildings: `agents copy/data/geojson/hausumringe_mit_adressenV3.geojson`
   - Usage: Network topology, building connections

4. **Electrical Infrastructure**
   - Source: `thesis-data-2/power-sim/` and `thesis-data-2/load-profile-generator/`
   - Format: Grid topology, load profiles
   - Usage: Heat pump electrical analysis

### **Data Processing Pipeline**
1. **Thesis Data Integration** → LFA-compatible JSON files
2. **Street-Specific Filtering** → Targeted building subsets
3. **Physics-Based Calculations** → Realistic energy profiles
4. **Network Construction** → Infrastructure topology
5. **Simulation Execution** → Pandapipes/Pandapower analysis
6. **Results Aggregation** → KPI generation and reporting

---

## 🛠️ **Technology Stack**

### **Core Technologies**
- **Python 3.9+** - Main programming language
- **Pandas/NumPy** - Data processing and analysis
- **GeoPandas** - Geospatial data handling
- **NetworkX** - Network topology and routing
- **Matplotlib/Seaborn** - Data visualization
- **Folium** - Interactive mapping

### **Simulation Engines**
- **Pandapipes** - District heating hydraulic simulation
- **Pandapower** - Electrical power flow analysis
- **Monte Carlo** - Statistical analysis and uncertainty quantification

### **AI & Machine Learning**
- **Google Gemini API** - Natural language processing and analysis
- **SimpleAgent Framework** - Custom agent implementation
- **ADK Framework** - Agent Development Kit (optional)

### **Web Technologies**
- **HTML/CSS/JavaScript** - Interactive dashboards
- **Chart.js** - Dynamic charting
- **Jinja2** - Template rendering
- **Markdown** - Report generation

### **Data Formats**
- **JSON** - Agent communication and configuration
- **CSV/Parquet** - Tabular data storage
- **GeoJSON** - Geospatial data exchange
- **YAML** - Configuration management

---

## 🎮 **User Interfaces**

### **Command Line Interface**
```bash
# Full system execution
make run-branitz                    # Complete pipeline
make run-street STREET="An der Bahn" # Street-specific analysis

# Individual components
make thesis-data                    # Heat demand generation
make cha                           # District heating analysis
make dha                           # Heat pump analysis
make te                            # Economic analysis
make kpi                           # KPI generation

# Enhanced AI agents
make enhanced-agents               # AI-powered analysis
make egpt PROMPT="analyze results" # EnergyGPT analysis
```

### **Interactive Dashboards**
1. **System Dashboard** (`docs/system_dashboard.html`)
   - Comprehensive system overview
   - All agent metrics and status
   - Interactive charts and visualizations

2. **Results Dashboard** (`docs/results_dashboard.html`)
   - Focused results presentation
   - Street-specific or system-wide views
   - Metric cards and performance indicators

3. **Street Dashboard** (`docs/street_dashboard_*.html`)
   - Street-specific analysis
   - Building-level details
   - AI-powered recommendations
   - Interactive maps and charts

4. **Combined Dashboard** (`docs/combined_dashboard.html`)
   - Tabbed interface
   - Multiple analysis views
   - Integrated reporting

### **Interactive Maps**
- **District Heating Maps**: Supply/return networks, hydraulic profiles
- **Electrical Grid Maps**: Feeder utilization, voltage analysis
- **Building Analysis Maps**: Heat demand, connection points
- **Layer Controls**: Toggle visibility, street selection

---

## 📁 **File Structure**

```
branitz_energy_decision_ai_street_final/
├── src/                          # Core system modules
│   ├── cha.py                   # Centralized Heating Agent
│   ├── dha.py                   # Decentralized Heating Agent
│   ├── eaa.py                   # Economics Analysis Agent
│   ├── tca.py                   # Techno-Economic Analysis Agent
│   ├── enhanced_agents.py       # AI-powered agents
│   ├── simple_gemini_agent.py   # Gemini API integration
│   ├── thesis_data_integration.py # LFA replacement
│   └── dashboard_*.py           # Dashboard generators
├── configs/                      # Configuration files
│   ├── cha.yml                  # CHA configuration
│   ├── dha.yml                  # DHA configuration
│   ├── eaa.yml                  # EAA configuration
│   ├── gemini_config.yml        # Gemini API configuration
│   └── thesis_data.yml          # Data integration config
├── processed/                    # Generated artifacts
│   ├── lfa/                     # Heat demand data
│   ├── cha/                     # District heating results
│   ├── dha/                     # Heat pump results
│   └── kpi/                     # Key performance indicators
├── eval/                        # Evaluation and metrics
│   ├── te/                      # Economic analysis results
│   └── caa/                     # Comprehensive analysis
├── docs/                        # Generated documentation
│   ├── *_dashboard.html         # Interactive dashboards
│   └── figures/                 # Generated visualizations
├── scripts/                     # Utility scripts
│   ├── extract_results.py       # Results extraction
│   └── make_figures.py          # Figure generation
├── thesis-data-2/               # Raw data sources
│   ├── wetter-data/             # TRY weather data
│   ├── pipes-sim/               # Building physics data
│   └── power-sim/               # Electrical infrastructure
├── agents copy/                 # Legacy agent implementations
└── Makefile                     # Build and execution commands
```

---

## 🔧 **Configuration & Setup**

### **Environment Setup**
```bash
# Activate conda environment
conda activate branitz_env

# Install dependencies
pip install google-generativeai pandas geopandas networkx matplotlib folium

# Configure Gemini API
export GEMINI_API_KEY="AIzaSyAy-ybjltiDoqVNT9oU4toNoHbX0-KM0O4"
```

### **Key Configuration Files**
- **`configs/gemini_config.yml`** - Gemini API settings
- **`configs/cha.yml`** - District heating parameters
- **`configs/dha.yml`** - Heat pump analysis settings
- **`configs/eaa.yml`** - Economic analysis parameters
- **`configs/thesis_data.yml`** - Data integration settings

---

## 🚀 **Execution Workflows**

### **1. Complete System Analysis**
```bash
make run-branitz
```
- Generates heat demand from physics-based calculations
- Runs CHA and DHA in parallel (fork-join)
- Performs economic analysis and KPI generation
- Creates comprehensive dashboards and reports

### **2. Street-Specific Analysis**
```bash
make run-street STREET="An der Bahn"
```
- Generates data for specific street only
- Fast execution for testing and demonstration
- Creates street-specific dashboard
- Provides AI-powered recommendations

### **3. AI-Powered Analysis**
```bash
make enhanced-agents
```
- Launches interactive AI agent system
- Natural language interface
- Intelligent delegation to specialist agents
- Real-time Gemini API integration

### **4. Custom Analysis**
```bash
make egpt PROMPT="analyze the KPI report and provide recommendations"
```
- Direct EnergyGPT interaction
- KPI analysis and insights
- Natural language recommendations

---

## 📈 **Outputs & Results**

### **Data Artifacts**
- **Heat Demand**: 8760-hour profiles per building
- **Network Topology**: Supply/return pipes, connections
- **Simulation Results**: Hydraulic and electrical analysis
- **Economic Metrics**: LCoH distributions, CO₂ emissions
- **KPIs**: Comprehensive performance indicators

### **Visualizations**
- **Interactive Maps**: Network topology, building analysis
- **Charts**: Heat demand, utilization, economic distributions
- **Dashboards**: Comprehensive system overviews
- **Reports**: HTML and Markdown documentation

### **AI Insights**
- **Natural Language Analysis**: EnergyGPT recommendations
- **Decision Support**: AI-powered scenario comparison
- **Implementation Guidance**: Actionable insights and next steps

---

## 🎯 **Key Features**

### **✅ Production-Ready**
- Robust error handling and fallback mechanisms
- Schema validation and data integrity checks
- Comprehensive testing and validation
- Definition of Done (DoD) compliance

### **✅ AI-Enhanced**
- Real-time Gemini API integration
- Natural language interface
- Intelligent agent delegation
- AI-powered analysis and recommendations

### **✅ Physics-Based**
- TRY weather data integration
- Realistic building physics calculations
- Accurate simulation engines (Pandapipes/Pandapower)
- Temperature-dependent heat demand

### **✅ Interactive**
- Dynamic HTML dashboards
- Interactive maps with layer controls
- Real-time chart updates
- Street-specific analysis capabilities

### **✅ Scalable**
- Street-level to system-wide analysis
- Parallel processing (CHA/DHA fork-join)
- Modular agent architecture
- Configurable analysis parameters

---

## 🔮 **System Status**

### **✅ Fully Functional Components**
- Heat demand generation (LFA replacement)
- District heating analysis (CHA)
- Heat pump analysis (DHA)
- Economic analysis (EAA/TCA)
- AI-powered agents (EnergyGPT)
- Interactive dashboards
- Street-specific analysis

### **⚠️ Known Limitations**
- CHA GeoJSON processing issues (isolated)
- Some legacy dependencies on questionary
- ADK framework optional (fallback available)

### **🚀 Recent Enhancements**
- Gemini API integration completed
- Physics-based heat demand implemented
- Street-specific analysis pipeline
- Enhanced dashboard system
- AI-powered recommendations

---

## 📞 **Quick Start Guide**

1. **Environment Setup**
   ```bash
   conda activate branitz_env
   ```

2. **Run Complete System**
   ```bash
   make run-branitz
   ```

3. **Test Street-Specific Analysis**
   ```bash
   make run-street STREET="An der Bahn"
   ```

4. **Launch AI Agents**
   ```bash
   make enhanced-agents
   ```

5. **View Results**
   - Open `docs/street_dashboard_an_der_bahn.html` in browser
   - Check `processed/kpi/kpi_summary.json` for KPIs
   - Review `eval/te/summary.csv` for economic analysis

---

**🎉 The Branitz Energy Decision AI system is now a comprehensive, production-ready platform for urban energy infrastructure analysis with AI-powered insights and interactive visualization capabilities!**
