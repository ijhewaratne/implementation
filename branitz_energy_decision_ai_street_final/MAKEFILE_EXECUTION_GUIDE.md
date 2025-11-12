# 🚀 Complete Makefile Execution Guide

## 📋 **Prerequisites**

### 1. Environment Setup
```bash
# Activate the conda environment
conda activate branitz_env

# Navigate to project directory
cd /Users/ishanthahewaratne/Documents/Research/branitz_energy_decision_ai_street_final

# Verify you're in the correct directory
pwd
ls -la Makefile
```

### 2. System Verification
```bash
# Check if all required tools are available
python --version
make --version
conda list | grep -E "(pandapipes|pandapower|geopandas|folium)"
```

---

## 🎯 **Step-by-Step Execution Guide**

### **Phase 1: System Verification**
```bash
# 1. Verify system integrity
make verify

# Expected output:
# ✅ Linting complete
# ✅ Formatting check complete  
# ✅ Tests passed
# ✅ Schema validation complete
```

### **Phase 2: Complete End-to-End Analysis**

#### **Option A: Full System Run (Recommended)**
```bash
# Run complete end-to-end analysis
make run-branitz

# This will execute:
# 1. LFA (Load Forecasting Agent)
# 2. CHA (Centralized Heating Agent) + DHA (Decentralized Heating Agent) in parallel
# 3. CHA output validation
# 4. TE (Techno-Economic Analysis)
# 5. KPI generation
# 6. CAA (Comprehensive Analysis Agent)
```

#### **Option B: Individual Agent Execution**
```bash
# Step 1: Load Forecasting
make lfa

# Step 2: Parallel execution of CHA and DHA
make -j 2 cha dha

# Step 3: Validate CHA outputs
make validate-cha-output

# Step 4: Techno-Economic Analysis
make te

# Step 5: KPI Generation
make kpi

# Step 6: Comprehensive Analysis
make caa
```

### **Phase 3: User Request Processing**

#### **Option A: Street-Specific Analysis**
```bash
# For specific street analysis
make run-street STREET="Parkstraße"

# This will run a focused analysis for the specified street
```

#### **Option B: Interactive Street Comparison**
```bash
# Launch interactive street comparison tool
make street-compare

# This opens an interactive menu where you can:
# - Select streets to compare
# - View DH vs HP analysis
# - Get recommendations
```

#### **Option C: Web-Based Interface**
```bash
# Launch web-based street comparison
make street-compare-web

# Opens a web interface in your browser
```

#### **Option D: Command-Line Interface**
```bash
# Launch command-line street comparison
make street-compare-cli

# Provides a text-based interface for street selection
```

### **Phase 4: Results and Visualization**

#### **View Results**
```bash
# List available streets with results
make street-list

# Generate comprehensive dashboard
make dashboard

# Generate results dashboard for specific analysis
make results-dashboard SLUG="your_analysis_slug"
```

#### **Generate Reports**
```bash
# Generate comprehensive figures
make figures SLUG="your_analysis_slug"

# Generate combined dashboard with tabs
make combined-dashboard

# Generate street-specific dashboard
make street-dashboard STREET="Parkstraße" BUILDINGS="building_data.csv"
```

---

## 🔧 **Advanced Options**

### **Simulation-Only Runs**
```bash
# Run only CHA hydraulic simulation
make cha-simulation-only

# Run only DHA electrical analysis
make dha-interactive
```

### **Validation and Testing**
```bash
# Validate CHA outputs
make validate-cha-output

# Run enhanced agent system
make enhanced-agents

# Test enhanced agents
make test-enhanced-agents
```

### **ADK System (Alternative)**
```bash
# Run ADK-based agent system
make test-adk-config
make test-adk-runner
make test-adk-input INPUT="your_input"
make test-adk-analysis STREET="Parkstraße" TYPE="DH"
```

---

## 📊 **Expected Outputs**

### **File Structure After Execution**
```
processed/
├── lfa/                    # Load forecasting results
├── cha/                    # Centralized heating results
│   ├── *.csv              # Network data
│   ├── cha.gpkg           # Geospatial data
│   ├── cha_kpis.json      # Key performance indicators
│   └── network_map.html   # Interactive map
├── dha/                    # Decentralized heating results
│   └── feeder_loads.csv   # Electrical load data
├── kpi/                    # Key performance indicators
│   ├── kpi_summary.json   # Summary results
│   └── kpi_report_*.json  # Street-specific reports
└── te/                     # Techno-economic analysis
    ├── mc.parquet         # Monte Carlo results
    └── summary.csv        # Economic summary

docs/
├── comprehensive_dashboard.html
├── system_dashboard.html
└── street_dashboard_*.html

eval/
├── cha/                    # CHA validation results
├── dha/                    # DHA validation results
└── te/                     # Economic analysis results
```

### **Key Result Files**
- **`processed/kpi/kpi_summary.json`** - Main results summary
- **`processed/cha/network_map.html`** - Interactive network visualization
- **`docs/comprehensive_dashboard.html`** - Complete system dashboard
- **`processed/cha/cha_kpis.json`** - Hydraulic simulation results

---

## 🎯 **User Request Examples**

### **Example 1: Complete Street Analysis**
```bash
# 1. Run complete analysis
make run-branitz

# 2. Compare specific street
make street-compare
# Then select "Parkstraße" from the menu

# 3. View results
open processed/kpi/kpi_summary.json
open processed/cha/network_map.html
```

### **Example 2: Focused Street Analysis**
```bash
# 1. Run focused analysis for specific street
make run-street STREET="Parkstraße"

# 2. Generate street-specific dashboard
make street-dashboard STREET="Parkstraße" BUILDINGS="data/buildings.csv"

# 3. View results
open docs/street_dashboard_parkstraße.html
```

### **Example 3: Web-Based Analysis**
```bash
# 1. Launch web interface
make street-compare-web

# 2. In the web interface:
#    - Select streets to compare
#    - Choose analysis type (DH vs HP)
#    - View interactive results
#    - Download reports
```

---

## 🚨 **Troubleshooting**

### **Common Issues and Solutions**

#### **Issue 1: Makefile not found**
```bash
# Solution: Ensure you're in the correct directory
pwd
# Should show: /Users/ishanthahewaratne/Documents/Research/branitz_energy_decision_ai_street_final

# If not, navigate there:
cd /Users/ishanthahewaratne/Documents/Research/branitz_energy_decision_ai_street_final
```

#### **Issue 2: Environment not activated**
```bash
# Solution: Activate conda environment
conda activate branitz_env

# Verify activation
conda info --envs
```

#### **Issue 3: Missing dependencies**
```bash
# Solution: Install missing packages
conda install -c conda-forge pandapipes pandapower geopandas folium

# Or use pip
pip install pandapipes pandapower geopandas folium
```

#### **Issue 4: Permission errors**
```bash
# Solution: Check file permissions
ls -la processed/
chmod -R 755 processed/
```

#### **Issue 5: Simulation failures**
```bash
# Solution: Check configuration
cat configs/cha.yml
cat configs/dha.yml

# Run with fallback mode
make cha  # Will fallback to topology-only if pandapipes fails
make dha  # Will fallback to heuristic if pandapower fails
```

---

## 📈 **Performance Tips**

### **Optimization Options**
```bash
# Run with fast mode (limited scope)
FAST=1 make run-branitz

# Run specific components only
make cha  # Only CHA
make dha  # Only DHA
make te   # Only economic analysis
```

### **Parallel Execution**
```bash
# Run CHA and DHA in parallel (default in run-branitz)
make -j 2 cha dha

# Run multiple streets in parallel
make -j 4 street-dashboard STREET="Street1" BUILDINGS="buildings1.csv" &
make -j 4 street-dashboard STREET="Street2" BUILDINGS="buildings2.csv" &
make -j 4 street-dashboard STREET="Street3" BUILDINGS="buildings3.csv" &
make -j 4 street-dashboard STREET="Street4" BUILDINGS="buildings4.csv" &
wait
```

---

## 🎉 **Success Indicators**

### **Successful Execution Signs**
- ✅ All make targets complete without errors
- ✅ `processed/kpi/kpi_summary.json` is created
- ✅ `processed/cha/network_map.html` is generated
- ✅ `docs/comprehensive_dashboard.html` is available
- ✅ No error messages in terminal output

### **Expected Runtime**
- **Full system run**: 5-15 minutes (depending on network size)
- **Individual agents**: 1-5 minutes each
- **Street comparison**: 30 seconds - 2 minutes
- **Dashboard generation**: 1-3 minutes

---

## 🔄 **Complete Workflow Example**

```bash
# 1. Setup
conda activate branitz_env
cd /Users/ishanthahewaratne/Documents/Research/branitz_energy_decision_ai_street_final

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
make figures SLUG="branitz_analysis"
```

This guide provides everything you need to run the complete Makefile process with user requests. The system will handle physics-based simulations (pandapipes for CHA, pandapower for DHA) and provide comprehensive DH vs HP analysis with interactive visualizations and recommendations.

