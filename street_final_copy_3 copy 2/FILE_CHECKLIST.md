# 📋 Enhanced Simulation System - File Checklist

## ⭐ **ESSENTIAL FILES (Must Have)**

### **🎯 Primary Scripts**
- [ ] `enhanced_simulation_runner.py` - **MAIN SCRIPT**
- [ ] `requirements.txt` - Python dependencies
- [ ] `config_interactive_run.yaml` - Configuration

### **📁 Core Data**
- [ ] `data/geojson/hausumringe_mit_adressenV3.geojson` - **PRIMARY BUILDING DATA**
- [ ] `data/osm/branitzer_siedlung.osm` - Street network
- [ ] `data/json/building_population_resultsV6.json` - Population data

### **🔧 Source Modules**
- [ ] `src/simulation_runner.py` - Original framework
- [ ] `src/scenario_manager.py` - Scenario management
- [ ] `src/network_construction.py` - Network building
- [ ] `src/data_preparation.py` - Data preprocessing

## 🚀 **EXECUTION SCRIPTS**

### **Interactive Runners**
- [ ] `interactive_dual_pipe_runner_enhanced.py`
- [ ] `interactive_dual_pipe_runner_fixed.py`
- [ ] `interactive_dual_pipe_runner.py`
- [ ] `interactive_run_enhanced.py`

### **Network Creation**
- [ ] `create_complete_dual_pipe_dh_network_improved.py`
- [ ] `create_complete_dual_pipe_dh_network.py`
- [ ] `create_proper_street_based_dh_network.py`
- [ ] `create_realistic_dh_network.py`

### **Simulation Scripts**
- [ ] `simulate_dual_pipe_dh_network_final.py`
- [ ] `simulate_dual_pipe_dh_network_fixed.py`
- [ ] `simulate_dual_pipe_dh_network.py`
- [ ] `pandapipes_district_heating.py`

## 📊 **SCENARIO FILES**

### **Generated Scenarios**
- [ ] `scenarios/base_dh_scenario.json`
- [ ] `scenarios/low_temp_dh_scenario.json`
- [ ] `scenarios/full_hp_scenario.json`
- [ ] `scenarios/hp_with_grid_reinforcement_scenario.json`
- [ ] `scenarios/dual_pipe_Wilhelm-Busch-Straße_scenario.json`

### **Building Data**
- [ ] `scenarios/buildings_base_dh.geojson`
- [ ] `scenarios/buildings_low_temp_dh.geojson`
- [ ] `scenarios/buildings_full_hp.geojson`
- [ ] `scenarios/buildings_Wilhelm-Busch-Straße.geojson`

## 🎨 **VISUALIZATION SCRIPTS**

### **Interactive Maps**
- [ ] `create_interactive_map.py`
- [ ] `create_real_interactive_map.py`
- [ ] `create_pandapipes_interactive_map.py`
- [ ] `create_detailed_interactive_map.py`

### **Enhanced Visualizations**
- [ ] `create_enhanced_visualizations.py`
- [ ] `create_summary_dashboard.py`
- [ ] `enhanced_visualization_demo.py`

## 🔧 **UTILITY SCRIPTS**

### **Network Analysis**
- [ ] `shortest_path_routing.py`
- [ ] `plant_building_snapping.py`
- [ ] `building_street_snapping.py`
- [ ] `street_network_builder.py`

### **Data Processing**
- [ ] `extract_street_buildings.py`
- [ ] `check_and_fix_crs.py`
- [ ] `example_crs_usage.py`

### **Demo and Testing**
- [ ] `demo_custom_temps.py`
- [ ] `demo_automated_workflow.py`
- [ ] `test_small_network.py`
- [ ] `simple_network_example.py`

## 📁 **SOURCE MODULES (src/)**

### **Analysis Modules**
- [ ] `src/building_attributes.py`
- [ ] `src/demand_calculation.py`
- [ ] `src/envelope_and_uvalue.py`
- [ ] `src/kpi_calculator.py`

### **Load Profile Generators**
- [ ] `src/h0_load_profile_generator.py`
- [ ] `src/g5_load_profile_generator.py`
- [ ] `src/l0_load_profile_generator.py`
- [ ] `src/g0_to_g6_load_profile_generator.py`
- [ ] `src/mixed_h0g0_load_profile_generator.py`

### **Utilities**
- [ ] `src/crs_utils.py`
- [ ] `src/network_visualization.py`
- [ ] `src/llm_reporter.py`

## 📊 **OUTPUT DIRECTORIES**

### **Results**
- [ ] `simulation_outputs/` - Main simulation results
- [ ] `results_test/` - Test outputs
- [ ] `street_analysis_outputs/` - Street-specific analysis
- [ ] `demo_outputs/` - Demo visualizations

### **Cache**
- [ ] `cache/` - Cached intermediate results

## 🚀 **QUICK START COMMANDS**

```bash
# Install dependencies
pip install -r requirements.txt

# Interactive mode (recommended)
python enhanced_simulation_runner.py --interactive

# Batch mode with existing scenarios
python enhanced_simulation_runner.py --scenarios scenarios/base_dh_scenario.json

# Multiple scenarios
python enhanced_simulation_runner.py --scenarios scenarios/*.json

# Parallel processing
python enhanced_simulation_runner.py --scenarios scenarios/*.json --no_parallel
```

## ✅ **VERIFICATION CHECKLIST**

### **Before Running**
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Primary data files present (`data/geojson/hausumringe_mit_adressenV3.geojson`)
- [ ] Configuration file exists (`config_interactive_run.yaml`)
- [ ] Main script accessible (`enhanced_simulation_runner.py`)

### **After Running**
- [ ] Simulation outputs generated (`simulation_outputs/`)
- [ ] Interactive maps created (`.html` files)
- [ ] Network statistics saved (`.json` files)
- [ ] Summary report generated (`simulation_summary_report.json`)

---

**🎯 Ready to run comprehensive dual-pipe district heating network analysis!** 