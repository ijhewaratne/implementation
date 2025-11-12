# 🏗️ Branitz Energy Decision AI - System Architecture

## 🎯 **System Overview**

The Branitz Energy Decision AI system is a comprehensive multi-agent framework for intelligent energy analysis, combining advanced AI capabilities with physics-based simulation.

## 🏗️ **High-Level Architecture**

```
┌─────────────────────────────────────────────────────────┐
│                BRANITZ ENERGY DECISION AI               │
│                   Multi-Agent System                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    INPUT LAYER                          │
│  📁 Geographic Data  │  📊 Heat Demand  │  ⚙️ Config    │
│  • Streets (GeoJSON) │  • LFA JSON      │  • YAML      │
│  • Buildings         │  • 8760h Load    │  • Features  │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                 DATA VALIDATION LAYER                   │
│  🔍 Schema Validation  │  📋 Standards  │  ✅ Quality   │
│  • JSON Schema         │  • EN 13941    │  • Checks     │
│  • Format Check        │  • DIN 1988    │  • Metrics    │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                   AGENT ECOSYSTEM                       │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │     CHA     │  │     EAA     │  │     TCA     │     │
│  │ (Centralized│  │ (Economic   │  │ (Technical  │     │
│  │  Heating)   │  │  Analysis)  │  │  Comparison)│     │
│  │             │  │             │  │             │     │
│  │ 🔧 Sizing   │  │ 💰 Costs    │  │ 📊 Compare  │     │
│  │ 🌊 Hydraulic│  │ 🎲 Monte    │  │ 🎯 Decide   │     │
│  │ 🌡️ Thermal  │  │ ⚡ Power    │  │ 📋 Standards│     │
│  │ 🔄 Resize   │  │ 🔥 Loss     │  │ 🏆 Bench    │     │
│  │ ⚙️ Standards│  │ 📊 Sens     │  │ 🤖 AI       │     │
│  │ 🛡️ Fallback │  │ 💼 Finance  │  │ 📈 KPIs     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐                      │
│  │     LFA     │  │     DHA     │                      │
│  │ (Load       │  │ (Decentral  │                      │
│  │  Forecast)  │  │  Heating)   │                      │
│  │             │  │             │                      │
│  │ 📅 8760h    │  │ 🔌 Heat     │                      │
│  │ 📊 Stats    │  │ ⚡ Electric │                      │
│  │ 🏢 Building │  │ 🌱 Individual│                      │
│  │ 🌡️ Weather  │  │ 📈 Perf     │                      │
│  └─────────────┘  └─────────────┘                      │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│              HYDRAULIC SIMULATION ENGINE                │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ PANDAPIPES  │  │   THERMAL   │  │ AUTO-RESIZE │     │
│  │             │  │             │  │             │     │
│  │ 🌊 Flow     │  │ 🌡️ Heat     │  │ 🔄 Iterate  │     │
│  │ 💧 Pressure │  │ 📊 Temp     │  │ 📏 Size     │     │
│  │ ⚡ Velocity │  │ 🔥 Loss     │  │ 🎯 Converge │     │
│  │ 🔧 Network  │  │ 📈 Eff      │  │ 🛡️ Guard    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐                      │
│  │ PUMP POWER  │  │ VALIDATION  │                      │
│  │             │  │             │                      │
│  │ ⚡ Power     │  │ 📋 Schema   │                      │
│  │ 🔧 Eff       │  │ 🏆 Standards│                      │
│  │ 💰 Cost      │  │ ✅ Quality  │                      │
│  └─────────────┘  └─────────────┘                      │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                 INTEGRATION LAYER                       │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   DATA      │  │   CONFIG    │  │ MIGRATION   │     │
│  │ INTEGRATION │  │ MANAGEMENT  │  │  SYSTEM     │     │
│  │             │  │             │  │             │     │
│  │ 🔗 Merge    │  │ ⚙️ YAML     │  │ 🔄 Convert  │     │
│  │ 📊 KPIs     │  │ 🏷️ Flags    │  │ 🛡️ Backward │     │
│  │ 🎯 Sync     │  │ 🌍 Env      │  │ 📋 Schema   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────┐
│                   OUTPUT LAYER                          │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ STRUCTURED  │  │ VISUAL      │  │  REPORTS    │     │
│  │   DATA      │  │ & MAPPING   │  │ & ANALYSIS  │     │
│  │             │  │             │  │             │     │
│  │ 📄 JSON     │  │ 🗺️ Maps     │  │ 📊 KPIs     │     │
│  │ 📊 CSV      │  │ 📈 Charts   │  │ 💰 Costs    │     │
│  │ 🗺️ GeoPKG   │  │ 🎨 Dash     │  │ 🎯 Recs     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

## 🔄 **Data Flow**

```
INPUT → VALIDATION → AGENTS → HYDRAULIC → INTEGRATION → OUTPUT
  │         │         │         │           │          │
  ▼         ▼         ▼         ▼           ▼          ▼
Data    Schema    CHA/EAA/   Pandapipes   Merge    JSON/CSV/
Files   Check     TCA/LFA/   Thermal      KPIs     Maps/
        Standards   DHA      Auto-Resize  Validate Reports
```

## 🎯 **Key Components**

### **1. Agent Ecosystem**
- **CHA**: Centralized Heating Agent with hydraulic simulation
- **EAA**: Economic Analysis Agent with Monte Carlo analysis
- **TCA**: Technical Comparison Agent with decision support
- **LFA**: Load Forecasting Agent with 8760h profiles
- **DHA**: Decentralized Heating Agent with heat pump analysis

### **2. Hydraulic Simulation Engine**
- **Pandapipes**: Full hydraulic simulation
- **Thermal**: Heat transfer and temperature analysis
- **Auto-Resize**: Intelligent pipe sizing
- **Pump Power**: Realistic pump calculations
- **Validation**: Standards compliance checking

### **3. Integration & Output**
- **Data Integration**: Agent result merging
- **Configuration**: YAML-based configuration
- **Migration**: Legacy data conversion
- **Output**: JSON, CSV, maps, reports

## 🔧 **Technical Stack**

- **Python 3.8+**: Core implementation
- **Pandapipes**: Hydraulic simulation
- **GeoPandas**: Geospatial processing
- **NetworkX**: Graph analysis
- **NumPy/SciPy**: Numerical computing
- **Pandas**: Data manipulation
- **Folium**: Interactive mapping
- **PyYAML**: Configuration
- **jsonschema**: Validation

## 🎯 **Key Features**

1. **Advanced Hydraulic Simulation**: Physics-based simulation with pandapipes
2. **Comprehensive Economic Analysis**: Monte Carlo and sensitivity analysis
3. **Intelligent Decision Support**: Multi-agent analysis and recommendations
4. **Robust System Architecture**: Graceful degradation and error handling
5. **Standards Compliance**: EN 13941, DIN 1988, VDI 2067 validation
6. **Data Validation**: Multi-layer validation and quality assurance
7. **Migration Support**: Legacy data conversion and compatibility
8. **Configuration Management**: Flexible configuration and feature flags
