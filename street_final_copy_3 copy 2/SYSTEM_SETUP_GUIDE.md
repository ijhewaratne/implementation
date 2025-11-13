# 🚀 Enhanced Simulation System - Complete Setup Guide

## 📋 **SYSTEM OVERVIEW**

This enhanced simulation system provides comprehensive dual-pipe district heating network analysis with street-based selection, real pandapipes simulations, and interactive user interfaces.

## 🗂️ **REQUIRED FILES AND SCRIPTS**

### **🎯 CORE EXECUTION SCRIPTS**

#### **1. Main Simulation Runner**
- **`enhanced_simulation_runner.py`** ⭐ **PRIMARY SCRIPT**
  - Interactive street-based scenario generation
  - Batch processing with multiprocessing
  - Real pandapipes simulations
  - Comprehensive result reporting

#### **2. Interactive Runners**
- **`interactive_dual_pipe_runner_enhanced.py`** - Enhanced interactive runner
- **`interactive_dual_pipe_runner_fixed.py`** - Fixed version with error handling
- **`interactive_dual_pipe_runner.py`** - Original interactive runner
- **`interactive_run_enhanced.py`** - Advanced interactive workflow

#### **3. Network Creation Scripts**
- **`create_complete_dual_pipe_dh_network_improved.py`** - Improved dual-pipe network creator
- **`create_complete_dual_pipe_dh_network.py`** - Original dual-pipe network creator
- **`create_proper_street_based_dh_network.py`** - Street-based network creation
- **`create_realistic_dh_network.py`** - Realistic network modeling

#### **4. Simulation Scripts**
- **`simulate_dual_pipe_dh_network_final.py`** - Final pandapipes simulation
- **`simulate_dual_pipe_dh_network_fixed.py`** - Fixed simulation with error handling
- **`simulate_dual_pipe_dh_network.py`** - Original simulation script
- **`pandapipes_district_heating.py`** - Pandapipes integration

### **📁 SOURCE CODE MODULES (`src/`)**

#### **Core Framework**
- **`simulation_runner.py`** - Original batch simulation framework
- **`scenario_manager.py`** - Scenario generation and management
- **`network_construction.py`** - NetworkX graph construction
- **`data_preparation.py`** - Data preprocessing utilities

#### **Analysis Modules**
- **`building_attributes.py`** - Building property calculations
- **`demand_calculation.py`** - Heat demand calculations
- **`envelope_and_uvalue.py`** - Building envelope analysis
- **`kpi_calculator.py`** - Key performance indicators

#### **Load Profile Generators**
- **`h0_load_profile_generator.py`** - H0 profile generation
- **`g5_load_profile_generator.py`** - G5 profile generation
- **`l0_load_profile_generator.py`** - L0 profile generation
- **`g0_to_g6_load_profile_generator.py`** - G0-G6 profile generation
- **`mixed_h0g0_load_profile_generator.py`** - Mixed profile generation

#### **Utilities**
- **`crs_utils.py`** - Coordinate reference system utilities
- **`network_visualization.py`** - Network visualization tools
- **`llm_reporter.py`** - LLM-based reporting

### **🗂️ DATA FILES**

#### **Geospatial Data (`data/`)**
- **`data/geojson/hausumringe_mit_adressenV3.geojson`** ⭐ **PRIMARY BUILDING DATA**
- **`data/geojson/hausumringe_with_gebaeudeid.geojson`** - Building data with IDs
- **`data/geojson/hausumringeV6.geojson`** - Version 6 building data
- **`data/geojson/hausumringe_mit_flurid.geojson`** - Building data with floor IDs
- **`data/osm/branitzer_siedlung.osm`** - OpenStreetMap street network data
- **`data/json/building_population_resultsV6.json`** - Building population data

#### **Configuration Files**
- **`config_interactive_run.yaml`** ⭐ **MAIN CONFIGURATION**
- **`branitz_scenarios.yaml`** - Scenario definitions
- **`requirements.txt`** ⭐ **PYTHON DEPENDENCIES**

### **📊 SCENARIO FILES (`scenarios/`)**

#### **Generated Scenarios**
- **`base_dh_scenario.json`** - Base district heating scenario
- **`low_temp_dh_scenario.json`** - Low temperature DH scenario
- **`full_hp_scenario.json`** - Full heat pump scenario
- **`hp_with_grid_reinforcement_scenario.json`** - HP with grid reinforcement
- **`dual_pipe_Wilhelm-Busch-Straße_scenario.json`** - Street-specific scenario

#### **Building Data**
- **`buildings_base_dh.geojson`** - Buildings for base DH scenario
- **`buildings_low_temp_dh.geojson`** - Buildings for low temp DH
- **`buildings_full_hp.geojson`** - Buildings for full HP scenario
- **`buildings_Wilhelm-Busch-Straße.geojson`** - Street-specific buildings

### **🎨 VISUALIZATION SCRIPTS**

#### **Interactive Maps**
- **`create_interactive_map.py`** - Basic interactive map creation
- **`create_real_interactive_map.py`** - Enhanced interactive maps
- **`create_pandapipes_interactive_map.py`** - Pandapipes network maps
- **`create_detailed_interactive_map.py`** - Detailed network visualization

#### **Enhanced Visualizations**
- **`create_enhanced_visualizations.py`** - Advanced visualization suite
- **`create_summary_dashboard.py`** - Summary dashboard creation
- **`enhanced_visualization_demo.py`** - Visualization demonstrations

### **🔧 UTILITY SCRIPTS**

#### **Network Analysis**
- **`shortest_path_routing.py`** - Shortest path routing algorithms
- **`plant_building_snapping.py`** - Plant and building snapping utilities
- **`building_street_snapping.py`** - Building to street network snapping
- **`street_network_builder.py`** - Street network construction

#### **Data Processing**
- **`extract_street_buildings.py`** - Street-specific building extraction
- **`check_and_fix_crs.py`** - Coordinate system validation and fixing
- **`example_crs_usage.py`** - CRS usage examples

#### **Demo and Testing**
- **`demo_custom_temps.py`** - Custom temperature demonstrations
- **`demo_automated_workflow.py`** - Automated workflow demonstrations
- **`test_small_network.py`** - Small network testing
- **`simple_network_example.py`** - Simple network examples

## 🚀 **QUICK START COMMANDS**

### **1. Interactive Mode (Recommended)**
```bash
python enhanced_simulation_runner.py --interactive
```

### **2. Batch Mode with Existing Scenarios**
```bash
python enhanced_simulation_runner.py --scenarios scenarios/base_dh_scenario.json
```

### **3. Multiple Scenarios**
```bash
python enhanced_simulation_runner.py --scenarios scenarios/*.json
```

### **4. Parallel Processing**
```bash
python enhanced_simulation_runner.py --scenarios scenarios/*.json --no_parallel
```

## 📦 **DEPENDENCIES**

### **Core Requirements (`requirements.txt`)**
```
pandapipes>=0.8.0
pandapower>=2.14.0
geopandas>=0.12.0
networkx>=2.8.0
numpy>=1.21.0
pandas>=1.3.0
shapely>=1.8.0
scipy>=1.7.0
pyproj>=3.3.0
fiona>=1.8.0
matplotlib>=3.5.0
pyyaml>=6.0
questionary>=1.10.0
osmnx>=1.2.0
contextily>=1.4.0
folium>=0.14.0
```

### **Installation**
```bash
pip install -r requirements.txt
```

## 🎯 **PRIMARY WORKFLOW**

### **1. Interactive Analysis**
1. Run `enhanced_simulation_runner.py --interactive`
2. Select analysis type (individual street, multiple streets, entire region)
3. Choose specific streets or entire region
4. System generates scenarios and runs simulations
5. Results saved to `simulation_outputs/`

### **2. Batch Processing**
1. Prepare scenario JSON files in `scenarios/`
2. Run `enhanced_simulation_runner.py --scenarios scenarios/*.json`
3. System processes all scenarios in parallel
4. Comprehensive summary report generated

### **3. Custom Scenarios**
1. Modify `config_interactive_run.yaml` for custom parameters
2. Use `scenario_manager.py` to generate new scenarios
3. Run with custom scenario files

## 📊 **OUTPUT STRUCTURE**

### **Simulation Outputs (`simulation_outputs/`)**
- **`{scenario_name}/`** - Per-scenario results
  - **`dual_pipe_map_{scenario}.html`** - Interactive network map
  - **`dual_network_stats_{scenario}.json`** - Network statistics
  - **`pandapipes_simulation_results_{scenario}.json`** - Simulation results
  - **`dual_supply_pipes_{scenario}.csv`** - Supply pipe data
  - **`dual_return_pipes_{scenario}.csv`** - Return pipe data
  - **`dual_service_connections_{scenario}.csv`** - Service connections
- **`simulation_summary_report.json`** - Overall summary

### **Test Results (`results_test/`)**
- Test outputs and intermediate results

### **Street Analysis (`street_analysis_outputs/`)**
- Street-specific analysis results

## 🔧 **CONFIGURATION**

### **Main Configuration (`config_interactive_run.yaml`)**
- **Data file paths** - Building, OSM, and demographic data
- **Processing flags** - Enable/disable specific modules
- **Output settings** - Directories and test modes
- **API keys** - LLM integration (if needed)

### **Scenario Configuration (`branitz_scenarios.yaml`)**
- **Scenario definitions** - Technology types and parameters
- **Building selections** - Specific building IDs
- **Profile types** - Load profile configurations

## 🎨 **VISUALIZATION FEATURES**

### **Interactive Maps**
- **Street-based routing** - All connections follow street network
- **Dual-pipe visualization** - Supply and return pipes
- **Building connections** - Service connections to buildings
- **Performance metrics** - Pressure, flow, temperature data

### **Summary Dashboards**
- **KPI overview** - Key performance indicators
- **Network statistics** - Pipe lengths, connections, efficiency
- **Simulation results** - Hydraulic performance metrics

## 🚨 **TROUBLESHOOTING**

### **Common Issues**
1. **CRS Mismatch** - Use `check_and_fix_crs.py`
2. **Network Connectivity** - System automatically fixes disconnected components
3. **JSON Serialization** - Fixed in enhanced runner
4. **Memory Issues** - Use smaller test scenarios first

### **Error Handling**
- **Automatic network connectivity fixes**
- **Graceful handling of missing data**
- **Comprehensive error reporting**
- **Fallback to simplified networks**

## 📈 **PERFORMANCE OPTIMIZATION**

### **Large-Scale Analysis**
- **Multiprocessing** - Parallel scenario processing
- **Simplified networks** - Reduced complexity for pandapipes
- **Caching** - Intermediate results caching
- **Memory management** - Efficient data handling

### **Batch Processing**
- **Scenario batching** - Process multiple scenarios
- **Result aggregation** - Comprehensive summary reports
- **Error isolation** - Failed scenarios don't stop batch

## 🎯 **NEXT STEPS**

1. **Install dependencies** - `pip install -r requirements.txt`
2. **Test with interactive mode** - `python enhanced_simulation_runner.py --interactive`
3. **Explore scenarios** - Check `scenarios/` directory
4. **Customize configuration** - Modify `config_interactive_run.yaml`
5. **Run batch analysis** - Process multiple scenarios

---

**🎉 The enhanced simulation system is ready for comprehensive dual-pipe district heating network analysis!** 