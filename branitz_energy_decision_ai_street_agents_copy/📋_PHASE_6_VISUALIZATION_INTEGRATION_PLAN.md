# 📋 Phase 6: Color-Coded Cascading Visualization Integration Plan

## Project Overview

**Goal:** Integrate advanced color-coded cascading visualizations from `street_final_copy_3` into the Agent-Based System

**Current Status:**
- ✅ Real simulations integrated (Phase 1-5 complete)
- ✅ Basic PNG visualizations added (Phase 5)
- ❌ Advanced color-coded cascading visualizations NOT integrated
- ❌ Interactive HTML dashboards NOT integrated

**Target:** Production-ready visual analytics with temperature, pressure, and voltage gradients

---

## 🎯 Integration Objectives

### **Primary Goals:**
1. ✅ Add **interactive HTML maps** with temperature/voltage cascading colors
2. ✅ Add **color-coded network visualizations** (DH temperature gradients)
3. ✅ Add **pressure/voltage gradient** overlays
4. ✅ Add **heat demand intensity** color maps
5. ✅ Add **service connection length** gradient visualization
6. ✅ Integrate with **existing agent tools** (no breaking changes)
7. ✅ Maintain **backward compatibility** with current outputs

### **Secondary Goals:**
1. ⏳ Add **12-panel summary dashboard** (matplotlib)
2. ⏳ Add **performance dashboard** with metrics
3. ⏳ Create **comparison dashboards** (DH vs HP)
4. ⏳ Add **hover/click interactivity** on HTML maps

---

## 📊 Current System Architecture

### **Existing Components:**

```
branitz_energy_decision_ai_street_agents/
│
├── src/
│   ├── simulators/
│   │   ├── pandapipes_dh_simulator.py      ✅ Real DH simulation
│   │   ├── pandapower_hp_simulator.py      ✅ Real HP simulation
│   │   └── base.py                         ✅ SimulationResult class
│   │
│   ├── orchestration/
│   │   ├── simulation_cache.py             ✅ Caching system
│   │   └── batch_runner.py                 ✅ Batch processing
│   │
│   └── simulation_runner.py                ✅ Main runner
│
├── energy_tools.py                         ✅ Agent tools
├── kpi_calculator.py                       ✅ KPI extraction
└── results_test/                           ✅ Output directory
```

### **Missing Components:**

```
❌ src/visualization/
❌ src/dashboards/
❌ Interactive HTML output in energy_tools.py
❌ Color-coded map generation
❌ Gradient visualization functions
```

---

## 🗂️ Source Code to Migrate

### **From:** `street_final_copy_3/`

```
street_final_copy_3/
│
├── src/network_visualization.py           ← MIGRATE THIS
│   • create_static_network_map()
│   • create_interactive_network_map()
│   • extract_network_geometries()
│
├── 04_create_pandapipes_interactive_map.py ← MIGRATE THIS
│   • PandapipesNetworkMap class
│   • Color-coded junction visualization
│   • Performance dashboard
│
├── 01_create_summary_dashboard.py         ← MIGRATE THIS
│   • EnhancedNetworkDashboard class
│   • 12-panel dashboard creation
│   • Color-coded KPI visualizations
│
└── 02_create_enhanced_visualizations.py   ← MIGRATE THIS
    • Service connection analysis
    • Comparative visualizations
```

---

## 📐 Integration Architecture

### **New Directory Structure:**

```
branitz_energy_decision_ai_street_agents/
│
├── src/
│   ├── simulators/                         [existing]
│   │
│   ├── visualization/                      [NEW]
│   │   ├── __init__.py
│   │   ├── network_maps.py                 [MIGRATE from network_visualization.py]
│   │   ├── color_gradients.py              [NEW - gradient functions]
│   │   ├── interactive_maps.py             [MIGRATE from 04_create_pandapipes_interactive_map.py]
│   │   └── colormaps.py                    [NEW - color palette definitions]
│   │
│   ├── dashboards/                         [NEW]
│   │   ├── __init__.py
│   │   ├── summary_dashboard.py            [MIGRATE from 01_create_summary_dashboard.py]
│   │   ├── comparison_dashboard.py         [MIGRATE from 02_create_enhanced_visualizations.py]
│   │   └── performance_dashboard.py        [NEW - performance metrics]
│   │
│   └── orchestration/                      [existing]
│
├── energy_tools.py                         [UPDATE - add visualization tools]
├── config/
│   └── visualization_config.yaml           [NEW - visualization settings]
│
└── results_test/
    ├── visualizations/                     [NEW - organized viz outputs]
    │   ├── static/                         [PNG/PDF outputs]
    │   ├── interactive/                    [HTML outputs]
    │   └── dashboards/                     [Dashboard outputs]
    └── ...
```

---

## 🚀 Implementation Plan

### **Phase 6.1: Core Visualization Module** (4-6 hours)

#### **Step 1.1: Create Visualization Module Structure**
```bash
# Create new directories
mkdir -p src/visualization
mkdir -p src/dashboards
mkdir -p results_test/visualizations/{static,interactive,dashboards}
```

**Files to create:**
- `src/visualization/__init__.py`
- `src/visualization/colormaps.py` - Color palette definitions
- `src/visualization/color_gradients.py` - Gradient calculation functions
- `config/visualization_config.yaml` - Visualization settings

**Deliverables:**
- ✅ Basic module structure
- ✅ Color palette constants
- ✅ Configuration file

---

#### **Step 1.2: Migrate Network Map Generator**

**Create:** `src/visualization/network_maps.py`

**Migrate from:** `street_final_copy_3/src/network_visualization.py`

**Functions to migrate:**
1. `extract_network_geometries(net)` - Extract pipes/junctions
2. `create_static_network_map(net, ...)` - PNG with OSM overlay
3. `create_enhanced_network_visualization(net, ...)` - Wrapper

**Adaptations needed:**
- Update imports to use `SimulationResult` from `src.simulators.base`
- Add color gradient support for temperature/pressure
- Integrate with existing output directory structure
- Add error handling for missing dependencies (contextily, folium)

**Code structure:**
```python
# src/visualization/network_maps.py

from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
from .colormaps import NETWORK_COLORS, get_temperature_color, get_pressure_color

class NetworkMapGenerator:
    """Generate static network maps with color gradients."""
    
    def __init__(self, output_dir="results_test/visualizations/static"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_dh_temperature_map(self, simulation_result, buildings_gdf=None):
        """Create DH map with temperature gradient."""
        # Extract network from simulation_result
        # Color supply pipes by temperature (red gradient)
        # Color return pipes by temperature (blue gradient)
        # Add buildings, consumers, plant
        # Save as PNG
        pass
    
    def create_hp_voltage_map(self, simulation_result, buildings_gdf=None):
        """Create HP map with voltage gradient."""
        # Extract network from simulation_result
        # Color buses by voltage (green/yellow/red)
        # Color lines by loading
        # Save as PNG
        pass
```

**Testing:**
- Test with DH simulation result
- Test with HP simulation result
- Verify color gradients display correctly
- Confirm PNG output quality (300 DPI)

**Deliverables:**
- ✅ `network_maps.py` with temperature/voltage gradients
- ✅ Static PNG map generation working
- ✅ Integration tests passing

---

#### **Step 1.3: Migrate Interactive Map Generator**

**Create:** `src/visualization/interactive_maps.py`

**Migrate from:** `street_final_copy_3/04_create_pandapipes_interactive_map.py`

**Class to migrate:**
- `PandapipesNetworkMap` → `InteractiveMapGenerator`

**Functions to migrate:**
1. `create_pandapipes_interactive_map()` → `create_dh_interactive_map()`
2. `_create_simulated_network_visualization()` → `_create_network_layers()`
3. `_add_network_statistics()` - Network stats popup
4. `_add_performance_dashboard()` - Performance metrics

**Enhancements:**
- Load from `SimulationResult` instead of JSON files
- Add real network geometry (not simulated)
- Add temperature gradient color coding
- Add pressure gradient visualization
- Add clickable pipe/junction popups with detailed KPIs

**Code structure:**
```python
# src/visualization/interactive_maps.py

import folium
from folium import plugins
from .colormaps import NETWORK_COLORS, get_temperature_gradient_color

class InteractiveMapGenerator:
    """Generate interactive HTML maps with Folium."""
    
    def __init__(self, output_dir="results_test/visualizations/interactive"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_dh_interactive_map(self, simulation_result, buildings_gdf=None):
        """Create interactive DH map with temperature cascading colors."""
        # Create folium map
        m = folium.Map(location=[center_lat, center_lon], zoom_start=16)
        
        # Add supply pipes (red, color-coded by temperature)
        # Add return pipes (blue, color-coded by temperature)
        # Add junctions with popups (temperature, pressure data)
        # Add heat consumers (orange markers)
        # Add CHP plant (green marker)
        # Add legend
        # Add statistics panel
        # Add performance dashboard
        
        # Save as HTML
        html_file = self.output_dir / f"{scenario_name}_dh_interactive.html"
        m.save(str(html_file))
        return str(html_file)
    
    def create_hp_interactive_map(self, simulation_result, buildings_gdf=None):
        """Create interactive HP map with voltage cascading colors."""
        # Similar structure for HP network
        # Color buses by voltage
        # Color lines by loading
        # Add transformer markers
        # Add violation warnings
        pass
```

**Testing:**
- Generate HTML maps for DH scenarios
- Generate HTML maps for HP scenarios
- Test interactivity (click, hover, zoom)
- Verify color gradients in browser
- Test on mobile devices

**Deliverables:**
- ✅ `interactive_maps.py` with full functionality
- ✅ HTML map generation working
- ✅ Interactive features working (tested in browser)

---

### **Phase 6.2: Dashboard Module** (3-5 hours)

#### **Step 2.1: Migrate Summary Dashboard**

**Create:** `src/dashboards/summary_dashboard.py`

**Migrate from:** `street_final_copy_3/01_create_summary_dashboard.py`

**Class to migrate:**
- `EnhancedNetworkDashboard` → `SummaryDashboard`

**Functions to migrate:**
1. `create_summary_dashboard()` - 12-panel figure
2. `_plot_kpi_summary()` - KPI bars
3. `_plot_network_topology()` - Schematic
4. `_plot_service_analysis()` - Service connections
5. (+ 9 more panel functions)

**Adaptations:**
- Load from `SimulationResult` instead of JSON
- Support both DH and HP scenarios
- Add color-coded gradients to panels
- Enhance with new KPIs from real simulations

**Code structure:**
```python
# src/dashboards/summary_dashboard.py

import matplotlib.pyplot as plt
import seaborn as sns

class SummaryDashboard:
    """Create 12-panel comprehensive summary dashboard."""
    
    def __init__(self, output_dir="results_test/visualizations/dashboards"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_dh_summary(self, simulation_result):
        """Create DH summary dashboard with 12 panels."""
        fig = plt.figure(figsize=(24, 18))
        
        # 12 panels with color-coded visualizations
        # 1. KPI summary
        # 2. Network topology
        # 3. Service connections
        # 4. Heat demand distribution
        # 5. Efficiency metrics
        # 6. Service length distribution
        # 7. Network density
        # 8. Hydraulic performance
        # 9. Comparative advantages
        # 10. Technical specs
        # 11. Cost efficiency
        # 12. Summary statistics
        
        save_path = self.output_dir / f"{scenario_name}_summary_dashboard.png"
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        return str(save_path)
    
    def create_hp_summary(self, simulation_result):
        """Create HP summary dashboard with 12 panels."""
        # Similar for HP with voltage/loading panels
        pass
```

**Testing:**
- Generate dashboard for DH scenario
- Generate dashboard for HP scenario
- Verify all 12 panels render correctly
- Check color gradients in each panel
- Validate PNG quality (300 DPI)

**Deliverables:**
- ✅ `summary_dashboard.py` with 12-panel creation
- ✅ DH and HP dashboard generation working
- ✅ High-quality PNG output

---

#### **Step 2.2: Create Comparison Dashboard**

**Create:** `src/dashboards/comparison_dashboard.py`

**Functionality:**
- Side-by-side DH vs HP comparison
- Economic metrics comparison (LCoH, CAPEX, OPEX)
- Environmental metrics (CO₂ emissions)
- Technical feasibility scores
- Color-coded bars/charts showing differences

**Code structure:**
```python
# src/dashboards/comparison_dashboard.py

class ComparisonDashboard:
    """Create DH vs HP comparison dashboards."""
    
    def create_comparison(self, dh_result, hp_result):
        """Create side-by-side comparison dashboard."""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # Panel 1: LCoH comparison (bar chart)
        # Panel 2: CO2 comparison (bar chart)
        # Panel 3: CAPEX/OPEX comparison
        # Panel 4: Network metrics
        # Panel 5: Efficiency comparison
        # Panel 6: Recommendation
        
        save_path = self.output_dir / f"comparison_dashboard.png"
        fig.savefig(save_path, dpi=300, bbox_inches="tight")
        return str(save_path)
```

**Deliverables:**
- ✅ Comparison dashboard creation
- ✅ Economic/environmental metrics comparison
- ✅ Recommendation engine

---

### **Phase 6.3: Integration with Agent Tools** (2-3 hours)

#### **Step 3.1: Add Visualization Tools to Agent System**

**Update:** `energy_tools.py`

**Add new tools:**

```python
# energy_tools.py

@tool
def create_interactive_map(
    scenario_name: str,
    visualization_type: str = "temperature"
) -> str:
    """
    Create interactive HTML map with color-coded cascading visualization.
    
    Args:
        scenario_name: Name of the scenario (e.g., "Parkstrasse_DH")
        visualization_type: Type of visualization - "temperature", "pressure", or "voltage"
    
    Returns:
        Path to generated HTML file
    """
    from src.visualization.interactive_maps import InteractiveMapGenerator
    
    # Load simulation results
    results_file = f"simulation_outputs/{scenario_name}_results.json"
    with open(results_file) as f:
        result = json.load(f)
    
    # Generate interactive map
    map_gen = InteractiveMapGenerator()
    
    if result['type'] == 'DH':
        html_file = map_gen.create_dh_interactive_map(result)
    else:
        html_file = map_gen.create_hp_interactive_map(result)
    
    return f"Interactive map created: {html_file}"

@tool
def create_summary_dashboard(scenario_name: str) -> str:
    """
    Create comprehensive 12-panel summary dashboard.
    
    Args:
        scenario_name: Name of the scenario
    
    Returns:
        Path to generated PNG dashboard
    """
    from src.dashboards.summary_dashboard import SummaryDashboard
    
    # Load simulation results
    results_file = f"simulation_outputs/{scenario_name}_results.json"
    with open(results_file) as f:
        result = json.load(f)
    
    # Generate dashboard
    dashboard = SummaryDashboard()
    
    if result['type'] == 'DH':
        png_file = dashboard.create_dh_summary(result)
    else:
        png_file = dashboard.create_hp_summary(result)
    
    return f"Summary dashboard created: {png_file}"

@tool
def create_comparison_dashboard(
    dh_scenario: str,
    hp_scenario: str
) -> str:
    """
    Create DH vs HP comparison dashboard.
    
    Args:
        dh_scenario: Name of DH scenario
        hp_scenario: Name of HP scenario
    
    Returns:
        Path to generated comparison dashboard
    """
    from src.dashboards.comparison_dashboard import ComparisonDashboard
    
    # Load both results
    with open(f"simulation_outputs/{dh_scenario}_results.json") as f:
        dh_result = json.load(f)
    with open(f"simulation_outputs/{hp_scenario}_results.json") as f:
        hp_result = json.load(f)
    
    # Generate comparison
    dashboard = ComparisonDashboard()
    png_file = dashboard.create_comparison(dh_result, hp_result)
    
    return f"Comparison dashboard created: {png_file}"
```

**Update agent definitions:**

```python
# agents.py

# Add to CentralHeatingAgent tools
central_heating_agent = Agent(
    tools=[
        run_complete_dh_analysis,
        create_network_visualization,
        create_interactive_map,        # NEW
        create_summary_dashboard,      # NEW
        # ...
    ]
)

# Add to DecentralizedHeatingAgent tools
decentralized_heating_agent = Agent(
    tools=[
        run_complete_hp_analysis,
        create_network_visualization,
        create_interactive_map,        # NEW
        create_summary_dashboard,      # NEW
        # ...
    ]
)

# Add to ComparisonAgent tools
comparison_agent = Agent(
    tools=[
        compare_scenarios,
        create_comparison_dashboard,   # NEW
        # ...
    ]
)
```

**Deliverables:**
- ✅ New visualization tools added to `energy_tools.py`
- ✅ Agent definitions updated
- ✅ Tools accessible to LLM agents

---

#### **Step 3.2: Update Simulation Runner**

**Update:** `src/simulation_runner.py`

**Enhancements:**
- Automatically generate interactive HTML map after simulation
- Optionally generate summary dashboard
- Store paths in `SimulationResult.visualization_files`

```python
# src/simulation_runner.py

def run_pandapipes_simulation(scenario):
    # ... existing simulation code ...
    
    if result.success:
        # Generate visualizations automatically
        from src.visualization.interactive_maps import InteractiveMapGenerator
        
        map_gen = InteractiveMapGenerator()
        html_file = map_gen.create_dh_interactive_map(result)
        
        # Add to result
        result.visualization_files = {
            'interactive_map': html_file
        }
    
    return result.to_dict()
```

**Deliverables:**
- ✅ Auto-generation of visualizations
- ✅ Visualization paths in results
- ✅ Backward compatibility maintained

---

### **Phase 6.4: Configuration & Color Palettes** (1-2 hours)

#### **Step 4.1: Create Color Palette Module**

**Create:** `src/visualization/colormaps.py`

```python
# src/visualization/colormaps.py

"""Color palette definitions for network visualizations."""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import cm
import numpy as np

# Network component colors
NETWORK_COLORS = {
    # DH Network (Temperature-based)
    'supply_pipe': '#DC143C',        # Crimson (hot)
    'return_pipe': '#4682B4',        # SteelBlue (cold)
    'supply_junction': '#DC143C',    # Crimson
    'return_junction': '#4682B4',    # SteelBlue
    'heat_consumer': '#FF8C00',      # DarkOrange
    'chp_plant': '#228B22',          # ForestGreen
    'service_connection': '#FFA500', # Orange
    
    # HP Network (Voltage-based)
    'lv_bus': '#4169E1',             # RoyalBlue
    'mv_bus': '#8B008B',             # DarkMagenta
    'transformer': '#FFD700',        # Gold
    'hp_load': '#FF4500',            # OrangeRed
    'substation': '#32CD32',         # LimeGreen
    'power_line': '#696969',         # DimGray
    
    # Infrastructure
    'street': '#696969',             # DimGray
    'building': '#D3D3D3',           # LightGray
    
    # Status Colors
    'normal': '#2ECC71',             # Green
    'warning': '#F39C12',            # Orange
    'critical': '#E74C3C',           # Red
    'excellent': '#27AE60',          # DarkGreen
}

def get_temperature_color(temp_c, t_min=40, t_max=90):
    """Get color for temperature value using hot colormap."""
    cmap = cm.get_cmap('hot')
    norm = mcolors.Normalize(vmin=t_min, vmax=t_max)
    return mcolors.to_hex(cmap(norm(temp_c)))

def get_pressure_color(pressure_bar, p_min=0, p_max=5):
    """Get color for pressure value using RdYlGn_r colormap."""
    cmap = cm.get_cmap('RdYlGn')
    norm = mcolors.Normalize(vmin=p_min, vmax=p_max)
    return mcolors.to_hex(cmap(norm(pressure_bar)))

def get_voltage_color(voltage_pu):
    """Get color for voltage value (green/yellow/red)."""
    if voltage_pu < 0.95 or voltage_pu > 1.05:
        return NETWORK_COLORS['critical']  # Red
    elif voltage_pu < 0.98 or voltage_pu > 1.02:
        return NETWORK_COLORS['warning']   # Orange
    else:
        return NETWORK_COLORS['normal']    # Green

def get_loading_color(loading_pct):
    """Get color for line loading percentage."""
    if loading_pct > 100:
        return NETWORK_COLORS['critical']  # Red
    elif loading_pct > 80:
        return NETWORK_COLORS['warning']   # Orange
    else:
        return NETWORK_COLORS['normal']    # Green

def get_heat_demand_color(demand_kw, min_demand=0, max_demand=100):
    """Get color for heat demand using YlOrRd colormap."""
    cmap = cm.get_cmap('YlOrRd')
    norm = mcolors.Normalize(vmin=min_demand, vmax=max_demand)
    return mcolors.to_hex(cmap(norm(demand_kw)))

def get_service_length_color(length_m):
    """Get color for service connection length (green=short, red=long)."""
    cmap = cm.get_cmap('RdYlGn_r')  # Reversed: Red->Yellow->Green
    norm = mcolors.Normalize(vmin=0, vmax=100)
    return mcolors.to_hex(cmap(norm(length_m)))

# Colormap presets for different visualizations
COLORMAPS = {
    'temperature': 'hot',          # Temperature gradients
    'pressure': 'RdYlGn',          # Pressure (red=low, green=high)
    'voltage': 'RdYlGn',           # Voltage (red=violation, green=normal)
    'heat_demand': 'YlOrRd',       # Heat demand intensity
    'service_length': 'RdYlGn_r',  # Service length (reversed)
    'loading': 'RdYlGn_r',         # Line loading
}
```

**Deliverables:**
- ✅ Complete color palette definitions
- ✅ Color gradient functions
- ✅ Consistent color scheme across all visualizations

---

#### **Step 4.2: Create Visualization Configuration**

**Create:** `config/visualization_config.yaml`

```yaml
# config/visualization_config.yaml

visualization:
  # Enable/disable visualization features
  enabled: true
  auto_generate_on_simulation: true
  
  # Output settings
  output_dir: "results_test/visualizations"
  static_dir: "results_test/visualizations/static"
  interactive_dir: "results_test/visualizations/interactive"
  dashboard_dir: "results_test/visualizations/dashboards"
  
  # Static map settings
  static:
    enabled: true
    dpi: 300
    format: "png"
    include_street_map: true
    street_map_provider: "OpenStreetMap.Mapnik"  # OSM, CartoDB.Positron, etc.
    figsize: [15, 12]
  
  # Interactive map settings
  interactive:
    enabled: true
    zoom_start: 16
    tiles: "OpenStreetMap"
    include_statistics_panel: true
    include_performance_dashboard: true
    include_legend: true
  
  # Dashboard settings
  dashboard:
    enabled: true
    summary_panels: 12
    figsize: [24, 18]
    dpi: 300
    include_logo: false
  
  # Color settings
  colors:
    dh_supply: "#DC143C"       # Crimson
    dh_return: "#4682B4"       # SteelBlue
    hp_normal: "#2ECC71"       # Green
    hp_warning: "#F39C12"      # Orange
    hp_critical: "#E74C3C"     # Red
    
  # Temperature gradient settings
  temperature:
    colormap: "hot"
    min_temp_c: 40
    max_temp_c: 90
    
  # Pressure gradient settings
  pressure:
    colormap: "RdYlGn"
    min_pressure_bar: 0
    max_pressure_bar: 5
    
  # Voltage gradient settings
  voltage:
    colormap: "RdYlGn"
    min_voltage_pu: 0.9
    max_voltage_pu: 1.1
    violation_low: 0.95
    violation_high: 1.05
    
  # Dependencies
  dependencies:
    contextily_required: false  # Optional for OSM overlays
    folium_required: true       # Required for interactive maps
```

**Deliverables:**
- ✅ Visualization configuration file
- ✅ Flexible settings for different output types
- ✅ Easy customization without code changes

---

### **Phase 6.5: Testing & Documentation** (2-3 hours)

#### **Step 5.1: Create Integration Tests**

**Create:** `tests/integration/test_visualization_integration.py`

```python
# tests/integration/test_visualization_integration.py

import pytest
from pathlib import Path
import json

class TestVisualizationIntegration:
    """Test visualization integration with agent system."""
    
    def test_dh_interactive_map_generation(self, sample_dh_result):
        """Test DH interactive map creation."""
        from src.visualization.interactive_maps import InteractiveMapGenerator
        
        map_gen = InteractiveMapGenerator()
        html_file = map_gen.create_dh_interactive_map(sample_dh_result)
        
        assert Path(html_file).exists()
        assert Path(html_file).suffix == '.html'
        
        # Check HTML content
        with open(html_file) as f:
            content = f.read()
            assert 'folium' in content.lower()
            assert 'supply' in content.lower()
            assert 'return' in content.lower()
    
    def test_hp_interactive_map_generation(self, sample_hp_result):
        """Test HP interactive map creation."""
        from src.visualization.interactive_maps import InteractiveMapGenerator
        
        map_gen = InteractiveMapGenerator()
        html_file = map_gen.create_hp_interactive_map(sample_hp_result)
        
        assert Path(html_file).exists()
        assert 'voltage' in open(html_file).read().lower()
    
    def test_summary_dashboard_generation(self, sample_dh_result):
        """Test summary dashboard creation."""
        from src.dashboards.summary_dashboard import SummaryDashboard
        
        dashboard = SummaryDashboard()
        png_file = dashboard.create_dh_summary(sample_dh_result)
        
        assert Path(png_file).exists()
        assert Path(png_file).suffix == '.png'
        
        # Check file size (should be substantial for 300 DPI)
        assert Path(png_file).stat().st_size > 100000  # > 100 KB
    
    def test_agent_tool_integration(self):
        """Test visualization tools accessible to agents."""
        from energy_tools import create_interactive_map, create_summary_dashboard
        
        # Check tools are callable
        assert callable(create_interactive_map)
        assert callable(create_summary_dashboard)
    
    def test_color_gradients(self):
        """Test color gradient functions."""
        from src.visualization.colormaps import (
            get_temperature_color,
            get_pressure_color,
            get_voltage_color
        )
        
        # Test temperature colors
        hot_color = get_temperature_color(85)  # Should be reddish
        cold_color = get_temperature_color(45)  # Should be darker
        assert hot_color != cold_color
        
        # Test voltage colors
        normal_voltage = get_voltage_color(1.0)   # Should be green
        low_voltage = get_voltage_color(0.92)     # Should be red
        assert normal_voltage != low_voltage
```

**Deliverables:**
- ✅ Integration tests for all visualization modules
- ✅ Test coverage > 80%
- ✅ All tests passing

---

#### **Step 5.2: Create Documentation**

**Update:** `README.md`

**Add section:**
```markdown
## 🎨 Advanced Visualizations

The system now includes advanced color-coded cascading visualizations:

### Interactive HTML Maps
- **Temperature gradients** for DH networks
- **Voltage gradients** for HP networks
- **Clickable elements** with detailed KPIs
- **Pan and zoom** capabilities

### Summary Dashboards
- **12-panel comprehensive** analysis
- **Color-coded KPIs** for quick insights
- **High-resolution** (300 DPI) for reports

### Usage
```python
# Generate interactive map
from energy_tools import create_interactive_map
create_interactive_map("Parkstrasse_DH", visualization_type="temperature")

# Generate summary dashboard
from energy_tools import create_summary_dashboard
create_summary_dashboard("Parkstrasse_DH")
```
```

**Create:** `docs/VISUALIZATION_GUIDE.md`

**Content:**
- Complete visualization guide
- All visualization types explained
- Color palette reference
- Customization instructions
- Browser compatibility notes
- Troubleshooting section

**Deliverables:**
- ✅ README updated
- ✅ Complete visualization guide
- ✅ API documentation
- ✅ Usage examples

---

## 📊 Effort Estimation

| Phase | Task | Estimated Hours |
|-------|------|----------------|
| **6.1** | Core Visualization Module | 4-6 hours |
| | Step 1.1: Module structure | 1 hour |
| | Step 1.2: Network map generator | 2-3 hours |
| | Step 1.3: Interactive map generator | 1-2 hours |
| **6.2** | Dashboard Module | 3-5 hours |
| | Step 2.1: Summary dashboard | 2-3 hours |
| | Step 2.2: Comparison dashboard | 1-2 hours |
| **6.3** | Agent Tool Integration | 2-3 hours |
| | Step 3.1: Add visualization tools | 1-2 hours |
| | Step 3.2: Update simulation runner | 1 hour |
| **6.4** | Configuration & Color Palettes | 1-2 hours |
| | Step 4.1: Color palette module | 1 hour |
| | Step 4.2: Configuration file | 0.5-1 hour |
| **6.5** | Testing & Documentation | 2-3 hours |
| | Step 5.1: Integration tests | 1-2 hours |
| | Step 5.2: Documentation | 1 hour |
| **Total** | | **12-19 hours** |

**Estimated Duration:** 2-3 working days

---

## 🎯 Success Criteria

### **Must Have (MVP):**
- ✅ Interactive HTML maps with temperature/voltage gradients
- ✅ Color-coded network visualizations (red/blue for DH, green/yellow/red for HP)
- ✅ Auto-generation on simulation completion
- ✅ Integration with agent tools
- ✅ Backward compatibility (no breaking changes)

### **Should Have:**
- ✅ 12-panel summary dashboards
- ✅ Comparison dashboards (DH vs HP)
- ✅ Performance dashboards with metrics
- ✅ Configuration file for customization
- ✅ Comprehensive documentation

### **Nice to Have:**
- ⏳ Animated temperature cascades
- ⏳ 3D network visualization
- ⏳ Time-series animations
- ⏳ Export to video/GIF
- ⏳ Mobile-responsive dashboards

---

## 🔧 Dependencies

### **Python Packages (Required):**
```bash
# Already installed
geopandas>=0.12.0
matplotlib>=3.5.0
seaborn>=0.12.0
pandas>=1.5.0

# New dependencies
folium>=0.14.0          # Interactive maps
contextily>=1.3.0       # OSM basemap (optional)
branca>=0.6.0           # Folium utilities
```

### **Installation:**
```bash
conda activate branitz_env
pip install folium contextily branca
```

### **Optional Dependencies:**
- `plotly` - For interactive charts in dashboards
- `bokeh` - Alternative interactive visualization
- `ipywidgets` - Jupyter notebook interactivity

---

## 🚨 Risks & Mitigation

### **Risk 1: Missing Dependencies**
- **Impact:** Visualization features not working
- **Mitigation:** 
  - Graceful degradation (skip if not available)
  - Clear error messages
  - Fallback to basic visualizations

### **Risk 2: Performance Issues with Large Networks**
- **Impact:** Slow rendering, large file sizes
- **Mitigation:**
  - Simplification for large networks (>200 buildings)
  - Progressive loading for interactive maps
  - Optional disable for very large networks

### **Risk 3: Browser Compatibility**
- **Impact:** Interactive maps not working in some browsers
- **Mitigation:**
  - Test in Chrome, Firefox, Safari, Edge
  - Provide static PNG alternatives
  - Document browser requirements

### **Risk 4: Breaking Changes**
- **Impact:** Existing functionality broken
- **Mitigation:**
  - Thorough integration testing
  - Backward compatibility tests
  - Separate new modules (no modifications to existing)

---

## 🔄 Rollout Strategy

### **Phase 1: Alpha (Internal Testing)**
- Deploy to test environment
- Generate visualizations for sample scenarios
- Verify all features working
- Fix critical bugs

### **Phase 2: Beta (Limited Release)**
- Enable for select scenarios
- Gather feedback
- Performance tuning
- Documentation refinement

### **Phase 3: Production (Full Release)**
- Enable by default for all scenarios
- Update agent system prompts
- Announce new features
- Monitor usage and performance

---

## 📋 Deliverables Checklist

### **Code Deliverables:**
- [ ] `src/visualization/network_maps.py`
- [ ] `src/visualization/interactive_maps.py`
- [ ] `src/visualization/colormaps.py`
- [ ] `src/visualization/color_gradients.py`
- [ ] `src/dashboards/summary_dashboard.py`
- [ ] `src/dashboards/comparison_dashboard.py`
- [ ] `config/visualization_config.yaml`
- [ ] Updated `energy_tools.py` with new tools
- [ ] Updated `agents.py` with new tools

### **Test Deliverables:**
- [ ] `tests/integration/test_visualization_integration.py`
- [ ] `tests/unit/test_network_maps.py`
- [ ] `tests/unit/test_interactive_maps.py`
- [ ] `tests/unit/test_dashboards.py`
- [ ] All tests passing (>80% coverage)

### **Documentation Deliverables:**
- [ ] Updated `README.md`
- [ ] `docs/VISUALIZATION_GUIDE.md`
- [ ] `docs/COLOR_PALETTE_REFERENCE.md`
- [ ] API documentation
- [ ] Usage examples

### **Output Deliverables:**
- [ ] Sample DH interactive map (HTML)
- [ ] Sample HP interactive map (HTML)
- [ ] Sample DH summary dashboard (PNG)
- [ ] Sample HP summary dashboard (PNG)
- [ ] Sample comparison dashboard (PNG)

---

## 🎊 Post-Integration Enhancements

### **Future Improvements (Phase 7+):**
1. **Animated Visualizations**
   - Temperature cascade animations
   - Pressure wave propagation
   - Voltage fluctuation animations

2. **3D Visualizations**
   - 3D network topology
   - Elevation-aware routing
   - Underground pipe depth visualization

3. **Real-Time Dashboards**
   - Live data streaming
   - WebSocket connections
   - Auto-refresh capabilities

4. **Advanced Analytics**
   - Machine learning predictions
   - Optimization suggestions
   - Pattern recognition

5. **Mobile Applications**
   - Native iOS/Android apps
   - Responsive web design
   - Field inspection tools

---

## ✅ Ready to Start?

**Prerequisites:**
1. ✅ Phases 1-5 complete (Real simulations integrated)
2. ✅ Conda environment activated (`branitz_env`)
3. ✅ All dependencies installed
4. ✅ Source files available in `street_final_copy_3/`

**Next Steps:**
1. Review this plan
2. Approve the approach
3. Begin Phase 6.1 implementation
4. Iterative development with testing

---

**Total Project Scope:** 12-19 hours over 2-3 days
**Complexity:** Medium
**Risk Level:** Low (isolated modules, backward compatible)
**Value:** High (advanced visual analytics for decision support)

---

**Ready to proceed with Phase 6.1: Core Visualization Module?** 🚀

