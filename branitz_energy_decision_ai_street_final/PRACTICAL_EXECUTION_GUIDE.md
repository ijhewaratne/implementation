# 🚀 Practical Makefile Execution Guide

## 📋 **Quick Start Commands**

### **1. Environment Setup**
```bash
# Navigate to project directory
cd /Users/ishanthahewaratne/Documents/Research/branitz_energy_decision_ai_street_final

# Activate conda environment
conda activate branitz_env

# Verify Makefile exists
ls -la Makefile
```

### **2. View Available Commands**
```bash
# Show all available make targets
make help
```

---

## 🎯 **Main Execution Options**

### **Option A: Complete End-to-End Analysis**
```bash
# Run the complete system (recommended)
make run-branitz

# This executes:
# 1. LFA (Load Forecasting)
# 2. CHA (Centralized Heating) + DHA (Decentralized Heating) in parallel
# 3. CHA validation
# 4. TE (Techno-Economic Analysis)
# 5. KPI generation
# 6. CAA (Comprehensive Analysis)
```

### **Option B: Street-Specific Analysis**
```bash
# Analyze specific street
make run-street STREET="Parkstraße"

# Or use thesis data for specific street
make thesis-data-street STREET="Parkstraße"
```

### **Option C: Interactive Street Comparison**
```bash
# Launch interactive street comparison tool
make street-compare

# This opens a menu where you can:
# - Select streets to compare
# - Choose DH vs HP analysis
# - View results and recommendations
```

### **Option D: Web-Based Interface**
```bash
# Launch web-based street comparison
make street-compare-web

# Opens in your browser with interactive interface
```

---

## 🔧 **Individual Agent Execution**

### **Step-by-Step Manual Execution**
```bash
# 1. Load Forecasting Agent
make lfa

# 2. Centralized Heating Agent (with pandapipes)
make cha

# 3. Decentralized Heating Agent (with pandapower)
make dha

# 4. Validate CHA outputs
make validate-cha-output

# 5. Techno-Economic Analysis
make te

# 6. KPI Generation
make kpi

# 7. Comprehensive Analysis
make caa
```

### **Simulation-Only Runs**
```bash
# Run only CHA hydraulic simulation
make cha-simulation-only

# Run only DHA electrical analysis
make dha-interactive
```

---

## 📊 **Results and Visualization**

### **View Results**
```bash
# List available streets
make street-list

# Generate comprehensive dashboard
make dashboard

# Generate combined dashboard with tabs
make combined-dashboard

# Generate comprehensive dashboard with figures
make comprehensive-dashboard
```

### **Street-Specific Dashboards**
```bash
# Generate dashboard for specific street
make street-dashboard STREET="Parkstraße" BUILDINGS="data/buildings.csv"

# Generate results dashboard
make results-dashboard SLUG="your_analysis_slug"

# Generate figures
make figures SLUG="your_analysis_slug"
```

---

## 🎯 **User Request Examples**

### **Example 1: Complete Analysis for Parkstraße**
```bash
# 1. Run complete analysis
make run-branitz

# 2. Launch street comparison
make street-compare
# Select "Parkstraße" from the menu

# 3. View results
open processed/kpi/kpi_summary.json
open processed/cha/network_map.html
```

### **Example 2: Focused Street Analysis**
```bash
# 1. Run focused analysis
make run-street STREET="Parkstraße"

# 2. Generate street dashboard
make street-dashboard STREET="Parkstraße" BUILDINGS="data/buildings.csv"

# 3. View results
open docs/street_dashboard_parkstraße.html
```

### **Example 3: Web-Based Analysis**
```bash
# 1. Launch web interface
make street-compare-web

# 2. In browser:
#    - Select streets to compare
#    - Choose analysis type (DH vs HP)
#    - View interactive results
#    - Download reports
```

---

## 🚀 **ADK System (Alternative)**

### **ADK-Based Execution**
```bash
# Test ADK configurations
make test-adk-config

# Test ADK runner
make test-adk-runner

# Test single input processing
make test-adk-input INPUT="analyze district heating for Parkstraße"

# Test analysis capabilities
make test-adk-analysis STREET="Parkstraße" TYPE="DH"

# Run enhanced agents
make enhanced-agents

# Test enhanced agents
make test-enhanced-agents
```

---

## 📈 **Performance and Optimization**

### **Fast Mode**
```bash
# Run with limited scope for testing
FAST=1 make run-branitz
```

### **Parallel Execution**
```bash
# Run CHA and DHA in parallel (already included in run-branitz)
make -j 2 cha dha
```

### **Batch Processing**
```bash
# Run enhanced agents in batch mode
make batch-enhanced-agents
```

---

## 🔍 **System Verification**

### **Pre-Execution Checks**
```bash
# Verify system integrity
make verify

# Check if all components are working
python -c "import pandapipes; print('Pandapipes OK')"
python -c "import pandapower; print('Pandapower OK')"
python -c "import geopandas; print('GeoPandas OK')"
```

### **Post-Execution Validation**
```bash
# Check if results were generated
ls -la processed/kpi/
ls -la processed/cha/
ls -la docs/

# Verify key files exist
test -f processed/kpi/kpi_summary.json && echo "✅ KPI summary exists"
test -f processed/cha/network_map.html && echo "✅ Network map exists"
test -f docs/comprehensive_dashboard.html && echo "✅ Dashboard exists"
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Issue 1: Makefile not found**
```bash
# Solution: Ensure correct directory
pwd
# Should show: /Users/ishanthahewaratne/Documents/Research/branitz_energy_decision_ai_street_final

# If not, navigate there:
cd /Users/ishanthahewaratne/Documents/Research/branitz_energy_decision_ai_street_final
```

#### **Issue 2: Environment not activated**
```bash
# Solution: Activate conda environment
conda activate branitz_env

# Verify:
conda info --envs
```

#### **Issue 3: Missing dependencies**
```bash
# Solution: Install required packages
conda install -c conda-forge pandapipes pandapower geopandas folium

# Or use pip:
pip install pandapipes pandapower geopandas folium
```

#### **Issue 4: Permission errors**
```bash
# Solution: Fix permissions
chmod -R 755 processed/
chmod -R 755 docs/
```

#### **Issue 5: Simulation failures**
```bash
# Solution: Check configuration files
cat configs/cha.yml
cat configs/dha.yml

# Run with fallback mode (automatic)
make cha  # Falls back to topology-only if pandapipes fails
make dha  # Falls back to heuristic if pandapower fails
```

---

## 📊 **Expected Outputs**

### **Key Result Files**
- **`processed/kpi/kpi_summary.json`** - Main results summary
- **`processed/cha/network_map.html`** - Interactive network visualization
- **`processed/cha/cha_kpis.json`** - Hydraulic simulation results
- **`docs/comprehensive_dashboard.html`** - Complete system dashboard
- **`docs/street_dashboard_*.html`** - Street-specific dashboards

### **Directory Structure**
```
processed/
├── lfa/                    # Load forecasting results
├── cha/                    # Centralized heating results
│   ├── *.csv              # Network data
│   ├── cha.gpkg           # Geospatial data
│   ├── cha_kpis.json      # KPIs
│   └── network_map.html   # Interactive map
├── dha/                    # Decentralized heating results
│   └── feeder_loads.csv   # Electrical loads
├── kpi/                    # Key performance indicators
│   ├── kpi_summary.json   # Summary
│   └── kpi_report_*.json  # Street reports
└── te/                     # Techno-economic analysis
    ├── mc.parquet         # Monte Carlo results
    └── summary.csv        # Economic summary

docs/
├── comprehensive_dashboard.html
├── system_dashboard.html
└── street_dashboard_*.html
```

---

## 🎉 **Success Indicators**

### **Successful Execution**
- ✅ All make targets complete without errors
- ✅ `processed/kpi/kpi_summary.json` is created
- ✅ `processed/cha/network_map.html` is generated
- ✅ `docs/comprehensive_dashboard.html` is available
- ✅ No error messages in terminal

### **Expected Runtime**
- **Full system run**: 5-15 minutes
- **Individual agents**: 1-5 minutes each
- **Street comparison**: 30 seconds - 2 minutes
- **Dashboard generation**: 1-3 minutes

---

## 🔄 **Complete Workflow Example**

```bash
# 1. Setup
cd /Users/ishanthahewaratne/Documents/Research/branitz_energy_decision_ai_street_final
conda activate branitz_env

# 2. Verify system
make verify

# 3. Run complete analysis
make run-branitz

# 4. Launch street comparison
make street-compare

# 5. View results
open processed/kpi/kpi_summary.json
open processed/cha/network_map.html
open docs/comprehensive_dashboard.html

# 6. Generate additional reports
make dashboard
make comprehensive-dashboard
```

This guide provides everything you need to run the complete Makefile process with user requests. The system includes physics-based simulations (pandapipes for CHA, pandapower for DHA) and provides comprehensive DH vs HP analysis with interactive visualizations and recommendations.

