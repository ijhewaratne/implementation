# 🎨 Complete Visualization Guide

## Advanced Color-Coded Cascading Visualizations for Energy Networks

**Version:** 2.0 (Phase 6)  
**Last Updated:** November 6, 2025

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Interactive HTML Maps](#interactive-html-maps)
4. [Summary Dashboards](#summary-dashboards)
5. [Comparison Dashboards](#comparison-dashboards)
6. [Color Schemes](#color-schemes)
7. [Configuration](#configuration)
8. [API Reference](#api-reference)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Agent-Based Energy System now includes **professional-grade color-coded cascading visualizations** for both District Heating (DH) and Heat Pump (HP) networks.

###Features:
- 🗺️ **Interactive HTML Maps** - Web-based maps with Folium/Leaflet.js
- 📊 **12-Panel Dashboards** - Comprehensive summary visualizations
- ⚖️ **Comparison Dashboards** - DH vs HP decision support
- 🌈 **Cascading Color Gradients** - Temperature, voltage, pressure visualization
- 🎯 **Professional Quality** - 300 DPI for presentations and reports
- ⚙️ **Fully Configurable** - Customize via YAML without code changes

---

## Quick Start

### **Enable Visualizations**

Edit `config/feature_flags.yaml`:
```yaml
features:
  enable_visualizations: true        # Enable visualization system
  enable_interactive_maps: true       # Enable HTML maps
  enable_dashboards: true             # Enable dashboards
```

### **Generate Your First Visualization**

**Option 1: Through Agent System**
```
User: "create interactive map for Parkstrasse_DH"
→ Generates HTML map with temperature gradients
```

**Option 2: Direct Python API**
```python
from src.visualization import InteractiveMapGenerator

map_gen = InteractiveMapGenerator()
html_file = map_gen.create_dh_interactive_map(net, "Parkstrasse_DH")
# Open results_test/visualizations/interactive/Parkstrasse_DH_dh_interactive.html
```

---

## Interactive HTML Maps

### **What They Are**

Web-based interactive maps built with Folium (Leaflet.js) that can be opened in any modern web browser.

###**Features:**
- **Pan & Zoom** - Navigate around the network
- **Click Elements** - Get detailed KPI popups
- **Hover Tooltips** - See element information
- **Layer Controls** - Toggle network components on/off
- **Statistics Panel** - Fixed panel with network KPIs
- **Performance Dashboard** - Real-time efficiency metrics
- **Multiple Basemaps** - Switch between OSM, CartoDB, etc.

### **For DH Networks:**

**Color Coding:**
- 🔴 **Red pipes** - Supply circuit (70-85°C)
- 🔵 **Blue pipes** - Return circuit (40-55°C)
- 🟠 **Orange triangles** - Heat consumers
- 🟢 **Green square** - CHP plant

**Popup Information:**
```
Supply Pipe: SUP_001
Temperature: 82.5°C
Pressure: 4.8 bar
Length: 125m
```

### **For HP Networks:**

**Color Coding:**
- 🟢 **Green buses** - Normal voltage (0.95-1.05 pu)
- 🟡 **Yellow buses** - Warning zone
- 🔴 **Red buses** - Violations
- 🔵 **Blue lines** - Power lines (color by loading)
- 🟡 **Gold markers** - Transformers

**Popup Information:**
```
Bus 12
Voltage: 0.982 pu
Status: Normal ✅
Connected Loads: 3
```

### **Output Location:**
```
results_test/visualizations/interactive/
├── {scenario}_dh_interactive.html
└── {scenario}_hp_interactive.html
```

### **File Size:** 100-500 KB per HTML file

### **How to Open:**
```bash
# macOS
open results_test/visualizations/interactive/Parkstrasse_DH_dh_interactive.html

# Linux
xdg-open results_test/visualizations/interactive/Parkstrasse_DH_dh_interactive.html

# Windows
start results_test/visualizations/interactive/Parkstrasse_DH_dh_interactive.html

# Or just double-click the HTML file!
```

---

## Summary Dashboards

### **What They Are**

Comprehensive 12-panel summary dashboards that provide complete scenario analysis in a single high-resolution image.

### **12-Panel Layout (3 rows × 4 columns)**

**Row 1 - Overview:**
1. **KPI Summary** - Heat/load, length, consumers, peak
2. **Network Topology** - Schematic diagram
3. **Thermal/Voltage Performance** - Temperature or voltage metrics
4. **Demand/Load Distribution** - Pie chart

**Row 2 - Analysis:**
5. **Hydraulic/Loading Performance** - Pressure or line loading
6. **Network Metrics** - Component counts
7. **Efficiency Indicators** - Network efficiency, losses
8. **Component Analysis** - Pipes/lines breakdown

**Row 3 - Summary:**
9. **Technical Specifications** - Text box with all specs
10. **Performance Scores** - Color-coded scores (0-100)
11. **Loss Analysis** - Heat/grid losses pie chart
12. **Summary Statistics** - Complete text summary

### **Color-Coded Performance Scores:**
- 🟢 **Green** (>80%) - Good performance
- 🟡 **Yellow** (60-80%) - Moderate performance
- 🔴 **Red** (<60%) - Poor performance

### **DH Dashboard Panels:**
- Thermal performance (supply/return temperatures)
- Hydraulic performance (pressure drops, pump energy)
- Heat loss analysis (delivered vs losses)
- Network efficiency (%)

### **HP Dashboard Panels:**
- Voltage profile (min/avg/max with limits)
- Line loading (max/avg/overloads)
- Transformer analysis (loading gauge)
- Violation analysis (counts)

### **Output:**
```
results_test/visualizations/dashboards/
├── {scenario}_dh_summary_dashboard.png   (24" × 18", 300 DPI)
└── {scenario}_hp_summary_dashboard.png   (24" × 18", 300 DPI)
```

### **File Size:** 2-4 MB per PNG

### **Use Cases:**
- Executive summaries
- Technical reports
- Stakeholder presentations
- Project documentation
- Decision support

---

## Comparison Dashboards

### **What They Are**

Side-by-side DH vs HP comparison dashboards with automated recommendations.

### **6-Panel Layout (2 rows × 3 columns)**

**Row 1 - Economics & Environment:**
1. **LCoH Comparison** - Cost comparison with winner highlighted
2. **CO₂ Comparison** - Emissions comparison with winner highlighted
3. **Cost Breakdown** - CAPEX, OPEX, Energy costs side-by-side

**Row 2 - Technical & Recommendation:**
4. **Technical Metrics** - Network characteristics comparison
5. **Efficiency Comparison** - Dual pie charts showing losses
6. **Recommendation** - Automated decision with scores

### **Automated Recommendation:**

Calculates overall scores based on:
- **Economic score** (0-100): Lower LCoH = higher score
- **Environmental score** (0-100): Lower CO₂ = higher score
- **Technical score** (0-100): Better performance = higher score

**Example Output:**
```
Recommendation: HEAT PUMPS
Margin: 5.3 points

Overall Scores:
  District Heating: 76.2/100
  Heat Pumps: 81.5/100

Score Breakdown:
  Economic: DH: 72.1 | HP: 78.5
  Environmental: DH: 75.0 | HP: 82.0
  Technical: DH: 81.5 | HP: 84.0
```

### **Winner Highlighting:**
- **Green border** (3px) around winning bars
- **Color-coded background** for recommendation

### **Output:**
```
results_test/visualizations/dashboards/
└── comparison_{dh}_vs_{hp}.png   (18" × 12", 300 DPI)
```

### **File Size:** 1-2 MB per PNG

---

## Color Schemes

### **DH Network Colors**

| Element | Color | Hex | Purpose |
|---------|-------|-----|---------|
| Supply Pipes | 🔴 Crimson | #DC143C | Hot water (70-85°C) |
| Return Pipes | 🔵 SteelBlue | #4682B4 | Cold water (40-55°C) |
| Supply Junctions | 🔴 Crimson | #DC143C | Hot side junctions |
| Return Junctions | 🔵 SteelBlue | #4682B4 | Cold side junctions |
| Heat Consumers | 🟠 DarkOrange | #FF8C00 | Building connections |
| CHP Plant | 🟢 ForestGreen | #228B22 | Heat source |
| Service Connections | 🟠 Orange | #FFA500 | Service lines |

### **HP Network Colors**

| Element | Color | Hex | Purpose |
|---------|-------|-----|---------|
| LV Buses | 🔵 RoyalBlue | #4169E1 | Low voltage buses |
| MV Buses | 🟣 DarkMagenta | #8B008B | Medium voltage buses |
| Transformers | 🟡 Gold | #FFD700 | MV/LV transformers |
| HP Loads | 🔴 OrangeRed | #FF4500 | Heat pump loads |
| Substations | 🟢 LimeGreen | #32CD32 | Grid connection |
| Power Lines | ⚫ DimGray | #696969 | Electrical lines |

### **Status Colors (Traffic Light System)**

| Status | Color | Hex | When Used |
|--------|-------|-----|-----------|
| Normal | 🟢 Green | #2ECC71 | Good performance, no violations |
| Warning | 🟡 Orange | #F39C12 | Moderate performance, approaching limits |
| Critical | 🔴 Red | #E74C3C | Poor performance, violations |
| Excellent | 🟢 DarkGreen | #27AE60 | Exceptional performance |

### **Matplotlib Colormaps**

| Visualization | Colormap | Range | Use Case |
|---------------|----------|-------|----------|
| Temperature | `hot` | Black→Red→Yellow→White | DH pipe temperatures |
| Pressure | `RdYlGn` | Red→Yellow→Green | Pressure levels |
| Voltage | `RdYlGn` | Red→Yellow→Green | Voltage profile |
| Heat Demand | `YlOrRd` | Yellow→Orange→Red | Demand intensity |
| Service Length | `RdYlGn_r` | Red→Yellow→Green | Connection efficiency |
| Loading | `RdYlGn_r` | Red→Yellow→Green | Line loading |

---

## Configuration

### **Main Config File: `config/visualization_config.yaml`**

**Edit to customize all visualization settings:**

```yaml
visualization:
  # Enable/disable features
  enabled: true
  auto_generate_on_simulation: false
  
  # Output quality
  static:
    dpi: 300              # 300 for print, 150 for screen
    format: "png"         # png, pdf, svg
    
  # Interactive maps
  interactive:
    zoom_start: 16        # Initial zoom level
    tiles: "OpenStreetMap"  # Basemap provider
    
  # Colors
  colors:
    dh_supply: "#DC143C"  # Change supply pipe color
    normal: "#2ECC71"      # Change normal status color
    
  # Gradients
  temperature:
    colormap: "hot"       # Change to plasma, inferno, etc.
    min_temp_c: 40
    max_temp_c: 90
```

### **Feature Flags: `config/feature_flags.yaml`**

**Toggle features on/off:**

```yaml
features:
  enable_visualizations: true            # Master toggle
  auto_generate_visualizations: false    # Auto-create after simulation
  enable_interactive_maps: true          # HTML maps
  enable_dashboards: true                # Dashboards
```

---

## API Reference

### **NetworkMapGenerator**

```python
from src.visualization import NetworkMapGenerator

map_gen = NetworkMapGenerator(output_dir="custom/path")

# Create DH temperature map
png_file = map_gen.create_dh_temperature_map(
    net=pandapipes_network,
    scenario_name="Parkstrasse_DH",
    buildings_gdf=buildings,       # Optional
    include_street_map=True        # OSM overlay
)

# Create HP voltage map
png_file = map_gen.create_hp_voltage_map(
    scenario_name="Parkstrasse_HP",
    buildings_gdf=buildings,
    include_street_map=True
)
```

### **InteractiveMapGenerator**

```python
from src.visualization import InteractiveMapGenerator

map_gen = InteractiveMapGenerator(output_dir="custom/path")

# Create DH interactive map
html_file = map_gen.create_dh_interactive_map(
    net=pandapipes_network,
    scenario_name="Parkstrasse_DH",
    buildings_gdf=buildings,       # Optional
    kpi=kpi_dict                   # Optional
)

# Create HP interactive map
html_file = map_gen.create_hp_interactive_map(
    scenario_name="Parkstrasse_HP",
    buildings_gdf=buildings,
    kpi=kpi_dict
)
```

### **SummaryDashboard**

```python
from src.dashboards import SummaryDashboard

dashboard = SummaryDashboard(output_dir="custom/path")

# Create DH summary
png_file = dashboard.create_dh_summary(
    kpi=kpi_dict,
    scenario_name="Parkstrasse_DH",
    metadata=metadata_dict         # Optional
)

# Create HP summary
png_file = dashboard.create_hp_summary(
    kpi=kpi_dict,
    scenario_name="Parkstrasse_HP",
    metadata=metadata_dict
)
```

### **ComparisonDashboard**

```python
from src.dashboards import ComparisonDashboard

comparison = ComparisonDashboard(output_dir="custom/path")

# Create comparison
png_file = comparison.create_comparison(
    dh_kpi=dh_kpi_dict,
    hp_kpi=hp_kpi_dict,
    dh_scenario_name="Parkstrasse_DH",
    hp_scenario_name="Parkstrasse_HP"
)
```

### **Color Functions**

```python
from src.visualization import (
    get_temperature_color,
    get_pressure_color,
    get_voltage_color,
    get_loading_color,
    get_heat_demand_color
)

# Get colors for values
temp_color = get_temperature_color(85)  # Returns red for 85°C
volt_color = get_voltage_color(0.98)    # Returns green for normal voltage
load_color = get_loading_color(75)      # Returns orange for 75% loading
```

---

## Examples

### **Example 1: Complete DH Analysis with Visualizations**

```python
# 1. Run simulation
from src.simulation_runner import run_pandapipes_simulation

scenario = {
    "name": "Parkstrasse_DH",
    "type": "DH",
    "building_file": "results_test/buildings_prepared.geojson"
}

result = run_pandapipes_simulation(scenario)

# 2. Create interactive map
from src.visualization import InteractiveMapGenerator

map_gen = InteractiveMapGenerator()
html_file = map_gen.create_dh_interactive_map(
    result['net'],
    "Parkstrasse_DH",
    kpi=result['kpi']
)

# 3. Create summary dashboard
from src.dashboards import SummaryDashboard

dashboard = SummaryDashboard()
png_file = dashboard.create_dh_summary(
    result['kpi'],
    "Parkstrasse_DH"
)

print(f"✅ Interactive map: {html_file}")
print(f"✅ Dashboard: {png_file}")
```

### **Example 2: DH vs HP Comparison**

```python
# 1. Load results from both scenarios
import json

with open("simulation_outputs/Parkstrasse_DH_results.json") as f:
    dh_result = json.load(f)

with open("simulation_outputs/Parkstrasse_HP_results.json") as f:
    hp_result = json.load(f)

# 2. Create comparison dashboard
from src.dashboards import ComparisonDashboard

comparison = ComparisonDashboard()
png_file = comparison.create_comparison(
    dh_result['kpi'],
    hp_result['kpi'],
    "Parkstrasse_DH",
    "Parkstrasse_HP"
)

print(f"✅ Comparison dashboard: {png_file}")
```

### **Example 3: Custom Color Scheme**

```python
# Option 1: Edit config/visualization_config.yaml
# Change colors:
#   dh_supply: "#FF0000"  # Bright red
#   dh_return: "#0000FF"  # Bright blue

# Option 2: Use color functions directly
from src.visualization import NETWORK_COLORS

# Override colors in your code
NETWORK_COLORS['supply_pipe'] = '#FF0000'
NETWORK_COLORS['return_pipe'] = '#0000FF'

# Then generate maps normally
```

---

## Troubleshooting

### **Issue 1: "folium not available"**

**Solution:**
```bash
pip install folium branca
```

### **Issue 2: "contextily not available"**

**Solution:** (Optional dependency for OSM basemaps)
```bash
pip install contextily
```

Or disable OSM overlay:
```yaml
# config/visualization_config.yaml
static:
  include_street_map: false
```

### **Issue 3: Large file sizes**

**Solution:** Reduce DPI
```yaml
# config/visualization_config.yaml
static:
  dpi: 150  # Instead of 300
```

### **Issue 4: Slow rendering for large networks**

**Solution:** Enable simplification
```yaml
# config/visualization_config.yaml
performance:
  simplify_threshold: 100  # Simplify networks > 100 buildings
```

### **Issue 5: Interactive map not displaying**

**Check:**
1. HTML file exists
2. Browser allows local file access
3. JavaScript enabled
4. Network connection (for basemap tiles)

**Solution:** Use different basemap
```yaml
interactive:
  tiles: "CartoDB.Positron"  # Doesn't require external connection
```

---

## Tips & Best Practices

### **For Presentations:**
- Use 300 DPI for print quality
- Use summary dashboards for comprehensive view
- Use interactive maps for live demos

### **For Reports:**
- Include summary dashboard as main figure
- Add interactive map link for supplementary materials
- Use comparison dashboard for decision support

### **For Analysis:**
- Start with interactive map to explore
- Use summary dashboard for overview
- Generate comparison for final decision

### **Performance:**
- Disable auto-generation for faster simulations
- Use lower DPI (150) for draft visualizations
- Enable simplification for large networks (>200 buildings)
- Cache frequently used visualizations

---

## Advanced Features

### **Custom Colormaps:**
```python
# Use any matplotlib colormap
from src.visualization import get_temperature_color

color = get_temperature_color(85, colormap='plasma')  # Purple-pink-yellow
color = get_temperature_color(85, colormap='viridis')  # Purple-green-yellow
```

### **Custom Temperature Ranges:**
```python
# Normalize to custom range
color = get_temperature_color(85, t_min=60, t_max=95)
```

### **Cascading Gradients:**
```python
from src.visualization.color_gradients import create_pipe_temperature_gradient

# Create temperature gradient along pipe
coords = [(51.76, 14.34), (51.76, 14.35), (51.76, 14.36)]
segments = create_pipe_temperature_gradient(coords, 85, 75)
# Returns: [(coord1, coord2, color), (coord2, coord3, color), ...]
```

---

## Output File Reference

### **Interactive Maps (HTML):**
```
results_test/visualizations/interactive/
├── {scenario}_dh_interactive.html     (100-500 KB)
└── {scenario}_hp_interactive.html     (100-500 KB)
```

### **Summary Dashboards (PNG):**
```
results_test/visualizations/dashboards/
├── {scenario}_dh_summary_dashboard.png   (2-4 MB, 300 DPI)
└── {scenario}_hp_summary_dashboard.png   (2-4 MB, 300 DPI)
```

### **Comparison Dashboards (PNG):**
```
results_test/visualizations/dashboards/
└── comparison_{dh}_vs_{hp}.png          (1-2 MB, 300 DPI)
```

### **Static Network Maps (PNG):**
```
results_test/visualizations/static/
├── dh_network_{scenario}.png            (1-2 MB, 300 DPI)
└── hp_network_{scenario}.png            (1-2 MB, 300 DPI)
```

---

## FAQ

**Q: Can I change the color scheme?**  
A: Yes! Edit `config/visualization_config.yaml` → `visualization.colors` section.

**Q: Can I disable visualizations?**  
A: Yes! Set `enable_visualizations: false` in `config/feature_flags.yaml`.

**Q: Can I auto-generate maps after each simulation?**  
A: Yes! Set `auto_generate_visualizations: true` in `config/feature_flags.yaml`.

**Q: Can I use different colormaps?**  
A: Yes! Edit `visualization.temperature.colormap` etc. in config. Choose from any [matplotlib colormap](https://matplotlib.org/stable/tutorials/colors/colormaps.html).

**Q: Can I export to PDF instead of PNG?**  
A: Yes! Set `visualization.static.format: "pdf"` in config.

**Q: Do visualizations work offline?**  
A: Mostly yes. Interactive maps need internet for basemap tiles, but you can use CartoDB.Positron which has better offline caching. Static maps work fully offline.

---

## Further Reading

- `📊_DASHBOARDS_FROM_PREVIOUS_IMPLEMENTATIONS.md` - Previous dashboard implementations
- `🎨_COLOR_CODED_VISUALIZATIONS.md` - Detailed color scheme documentation
- `📁_OUTPUTS_GUIDE.md` - Complete output file reference
- `config/visualization_config.yaml` - Full configuration options

---

**Need Help?**  
Check the troubleshooting section above or review the configuration file for available options!

---

**Last Updated:** November 6, 2025  
**Version:** 2.0 (Phase 6 Complete)

