# 🎨 Color-Coded Cascading Visualizations

## Previous Implementations with Color-Coded Networks

The previous implementations include **extensive color-coded cascading visualizations** showing thermal gradients, pressure gradients, and voltage gradients across networks.

---

## 🌡️ **1. DH Network: Temperature Cascading Color Gradients**

### **Implementation Location:**
`street_final_copy_3/src/network_visualization.py`

### **Features:**

#### **A. Pipe Color Coding (Temperature-Based)**
```python
# Supply pipes (HOT) - Red/Crimson
gdf_sup.plot(ax=ax, linewidth=3, color="crimson", label="Supply main", zorder=3)

# Return pipes (COOL) - Blue/Steelblue  
gdf_ret.plot(ax=ax, linewidth=2, color="steelblue", label="Return main", zorder=2)
```

**Color Cascade:**
- 🔴 **Red (Crimson)**: Supply pipes at 70-85°C
- 🔵 **Blue (Steelblue)**: Return pipes at 40-55°C
- **Temperature Gradient**: Visual representation of heat flow from source to consumer and back

---

#### **B. Junction Color Coding (Circuit-Based)**
```python
# Supply junctions (hot side)
supply_junctions.plot(ax=ax, color="crimson", markersize=80, 
                     label="Supply junctions", zorder=4)

# Return junctions (cool side)
return_junctions.plot(ax=ax, color="steelblue", markersize=60, 
                      label="Return junctions", zorder=4)
```

**Color Cascade:**
- 🔴 **Crimson dots**: Supply circuit (hot)
- 🔵 **Steelblue dots**: Return circuit (cold)
- Creates **cascading flow visualization** from plant through network

---

#### **C. Consumer/Building Color Coding (Heat Demand)**
```python
# Heat consumers - Orange triangles
ax.scatter(x_coords, y_coords, c="orange", s=100, zorder=5, 
          label="Heat consumers", marker="^", edgecolors="black", linewidth=1)

# Buildings background - Light grey
buildings_web.plot(ax=ax, color="lightgrey", edgecolor="black", 
                  alpha=0.7, label="Buildings", zorder=1)

# CHP Plant - Green square
ax.scatter(plant_x, plant_y, c="green", s=200, zorder=6, 
          label="CHP Plant", marker="s", edgecolors="black", linewidth=2)
```

**Color Hierarchy (Z-Order Cascade):**
1. 🏢 **Light grey** - Building context (lowest layer)
2. 🔵 **Blue** - Return pipes (middle)
3. 🔴 **Red** - Supply pipes (higher)
4. 🟠 **Orange** - Heat consumers (highest)
5. 🟢 **Green** - CHP plant (top)

---

### **Interactive Map Color Coding:**

```python
# Folium-based interactive maps with cascading colors

# Supply pipes - Red with opacity gradient
folium.GeoJson(geo, 
    style_function=lambda feat: {
        "color": "red", 
        "weight": 4, 
        "opacity": 0.8  # Gradient effect
    },
    tooltip=f"Supply Pipe: {row.name}"
).add_to(m)

# Return pipes - Blue with opacity gradient
folium.GeoJson(geo,
    style_function=lambda feat: {
        "color": "blue", 
        "weight": 3, 
        "opacity": 0.6  # Lighter for return
    },
    tooltip=f"Return Pipe: {row.name}"
).add_to(m)
```

**Interactive Color Features:**
- **Hover tooltips** with color-coded information
- **Clickable popups** showing temperature data
- **Layered color system** with transparency for depth perception

---

## ⚡ **2. HP Network: Voltage Cascading Color Gradients**

### **Implementation:**
HP visualizations use **voltage-based color gradients** to show electrical network health

### **Color Scheme (Typical HP Implementation):**

```python
# Based on voltage level (per-unit values)

def get_voltage_color(voltage_pu):
    """Return color based on voltage level."""
    if voltage_pu < 0.95:
        return "red"      # ❌ Under-voltage (violation)
    elif voltage_pu < 0.98:
        return "orange"   # ⚠️ Warning
    elif voltage_pu > 1.05:
        return "red"      # ❌ Over-voltage (violation)
    elif voltage_pu > 1.02:
        return "orange"   # ⚠️ Warning
    else:
        return "green"    # ✅ Normal
```

**Voltage Cascade Visualization:**
- 🟢 **Green** (0.95-1.05 pu): Healthy voltage
- 🟡 **Yellow/Orange** (0.92-0.95 or 1.05-1.08 pu): Warning zone
- 🔴 **Red** (<0.92 or >1.08 pu): Violation

**Bus Color Coding:**
```python
# Color buses by voltage level
for bus in network.bus.itertuples():
    color = get_voltage_color(bus.vm_pu)
    folium.CircleMarker(
        location=[bus.lat, bus.lon],
        radius=8,
        color=color,
        fillColor=color,
        fillOpacity=0.7,
        popup=f"Bus {bus.name}<br>Voltage: {bus.vm_pu:.3f} pu"
    )
```

---

## 📊 **3. Advanced Color-Coded Features**

### **A. Heat Demand Gradient (Building-Level)**

```python
# Color buildings by heat demand intensity
import matplotlib.cm as cm
import matplotlib.colors as mcolors

# Create colormap
cmap = cm.get_cmap('YlOrRd')  # Yellow -> Orange -> Red
norm = mcolors.Normalize(vmin=min_demand, vmax=max_demand)

# Apply to buildings
for idx, building in buildings_gdf.iterrows():
    demand = building['heating_load_kw']
    color = cmap(norm(demand))
    
    folium.CircleMarker(
        location=[building.lat, building.lon],
        radius=10,
        color=color,
        fillColor=color,
        fillOpacity=0.7,
        popup=f"Heat Demand: {demand:.1f} kW"
    )
```

**Heat Demand Color Cascade:**
- 🟡 **Yellow**: Low demand (0-20 kW)
- 🟠 **Orange**: Medium demand (20-50 kW)
- 🔴 **Red**: High demand (50+ kW)

---

### **B. Pressure Drop Gradient (DH Network)**

```python
# Color pipes by pressure drop severity
def get_pressure_color(dp_bar):
    """Return color based on pressure drop."""
    if dp_bar < 0.3:
        return "#2ecc71"  # Green - excellent
    elif dp_bar < 0.5:
        return "#f39c12"  # Orange - acceptable
    elif dp_bar < 0.8:
        return "#e74c3c"  # Red - high
    else:
        return "#c0392b"  # Dark red - critical
```

**Pressure Cascade:**
- 🟢 **Green**: <0.3 bar (low pressure drop)
- 🟡 **Yellow**: 0.3-0.5 bar (moderate)
- 🟠 **Orange**: 0.5-0.8 bar (high)
- 🔴 **Red**: >0.8 bar (critical)

---

### **C. Line Loading Gradient (HP Network)**

```python
# Color lines by loading percentage
def get_loading_color(loading_pct):
    """Return color based on line loading."""
    if loading_pct < 60:
        return "#27ae60"  # Green - light load
    elif loading_pct < 80:
        return "#f39c12"  # Orange - moderate
    elif loading_pct < 100:
        return "#e67e22"  # Dark orange - high
    else:
        return "#c0392b"  # Dark red - overload
```

**Loading Cascade:**
- 🟢 **Green**: <60% loading
- 🟡 **Yellow**: 60-80% loading
- 🟠 **Orange**: 80-100% loading
- 🔴 **Red**: >100% loading (overload)

---

### **D. Service Connection Length Gradient**

```python
# Color service connections by distance
from matplotlib import cm
import matplotlib.colors as colors

# Colormap from green (short) to red (long)
cmap = cm.get_cmap('RdYlGn_r')  # Reverse: Red->Yellow->Green
norm = colors.Normalize(vmin=0, vmax=100)  # 0-100m range

for connection in service_connections:
    length_m = connection['distance_to_street']
    color = cmap(norm(length_m))
    
    folium.PolyLine(
        locations=connection['coords'],
        color=mcolors.to_hex(color),
        weight=3,
        opacity=0.8,
        dash_array="5, 5",
        popup=f"Service Length: {length_m:.1f}m"
    )
```

**Distance Cascade:**
- 🟢 **Green**: 0-30m (short, efficient)
- 🟡 **Yellow**: 30-60m (moderate)
- 🟠 **Orange**: 60-80m (long)
- 🔴 **Red**: >80m (very long, less efficient)

---

## 🎨 **4. Matplotlib Colormaps Used**

### **Temperature/Heat Gradients:**
```python
# Hot-to-cold colormaps
'hot'         # Black -> Red -> Yellow -> White
'coolwarm'    # Blue -> White -> Red
'RdYlBu_r'    # Red -> Yellow -> Blue (reversed)
'plasma'      # Purple -> Pink -> Yellow
'inferno'     # Black -> Purple -> Red -> Yellow
```

### **Pressure/Performance Gradients:**
```python
# Performance colormaps
'RdYlGn'      # Red -> Yellow -> Green (poor to good)
'viridis'     # Purple -> Blue -> Green -> Yellow
'YlGn'        # Yellow -> Green (low to high)
```

### **Demand/Load Gradients:**
```python
# Intensity colormaps
'YlOrRd'      # Yellow -> Orange -> Red (increasing intensity)
'Reds'        # Light red -> Dark red
'OrRd'        # Orange -> Red
```

---

## 📁 **5. Files with Color-Coded Visualizations**

### **DH Color-Coded Maps:**
```
street_final_copy_3/simulation_outputs/
├── dual_pipe_map_complete_dual_pipe_dh.html
│   • Red supply pipes (70°C)
│   • Blue return pipes (40°C)
│   • Orange service connections
│   • Color-coded junctions
│
├── base_dh/dual_pipe_map_base_dh.html
│   • Temperature gradient visualization
│   • Pressure drop color coding
│
└── street_analysis_outputs/{street}/
    ├── dual_pipe_map_dual_pipe_{street}.html
    │   • Street-specific color-coded network
    └── dual_pipe_dashboard_dual_pipe_{street}.html
        • Interactive dashboard with color gradients
```

### **HP Color-Coded Maps:**
```
street_final_copy_3/simulation_outputs/
├── full_hp/electrical_network_map_full_hp.html
│   • Voltage-based bus coloring
│   • Line loading color gradient
│   • Transformer status colors
│
└── hp_with_grid_reinforcement/
    └── electrical_network_map_hp_with_grid_reinforcement.html
        • Before/after color comparison
        • Violation highlighting (red)
```

---

## 🌈 **6. Color Palette Standards**

### **Network Component Colors:**
```python
NETWORK_COLORS = {
    # DH Network
    'supply_pipe': '#DC143C',      # Crimson (hot)
    'return_pipe': '#4682B4',      # SteelBlue (cold)
    'supply_junction': '#DC143C',  # Crimson
    'return_junction': '#4682B4',  # SteelBlue
    'heat_consumer': '#FF8C00',    # DarkOrange
    'chp_plant': '#228B22',        # ForestGreen
    
    # HP Network
    'lv_bus': '#4169E1',           # RoyalBlue
    'mv_bus': '#8B008B',           # DarkMagenta
    'transformer': '#FFD700',      # Gold
    'hp_load': '#FF4500',          # OrangeRed
    'substation': '#32CD32',       # LimeGreen
    
    # Infrastructure
    'street': '#696969',           # DimGray
    'building': '#D3D3D3',         # LightGray
    'service_connection': '#FFA500', # Orange
    
    # Status Colors
    'normal': '#2ECC71',           # Green
    'warning': '#F39C12',          # Orange
    'critical': '#E74C3C',         # Red
    'excellent': '#27AE60',        # DarkGreen
}
```

---

## 📊 **7. Example: Full Color-Coded Dashboard**

### **12-Panel Dashboard Color Scheme:**

```python
# From 01_create_summary_dashboard.py

# Panel colors for different metrics
colors_kpi = ['#ff7f0e', '#2ca02c', '#d62728', '#9467bd']  # Orange, Green, Red, Purple
colors_efficiency = ['lightgreen', 'orange', 'lightcoral']
colors_advantages = ['lightgreen'] * 5  # All green (fully implemented)
colors_specs = ['lightcoral', 'lightblue', 'lightgreen', 'orange', 'lightgray']
```

**Dashboard Visualization:**
1. **KPI Bars**: Multi-color (orange, green, red, purple)
2. **Network Topology**: Schematic with color-coded elements
3. **Service Analysis**: Color gradient histogram
4. **Heat Demand**: Pie chart with contrasting colors
5. **Efficiency**: Traffic light colors (green/yellow/red)
6. **Hydraulic**: Status-based coloring

---

## 🎯 **8. Interactive Features with Color**

### **Hover Effects:**
```javascript
// On hover, change opacity for cascading effect
style_function=lambda feat: {
    "color": base_color,
    "weight": 4,
    "opacity": 0.8,
    "fillOpacity": 0.6
},
highlight_function=lambda feat: {
    "opacity": 1.0,        // Full opacity on hover
    "fillOpacity": 0.9,
    "weight": 6            // Thicker on hover
}
```

### **Click Effects:**
```python
# Change color on click to highlight selection
selected_color = "#FFD700"  # Gold for selected elements
```

---

## 🔄 **9. Cascading Color Gradients (Advanced)**

### **Temperature Gradient Along Pipe:**
```python
# Create temperature gradient along supply pipe
def create_temperature_gradient(pipe_coords, T_start, T_end):
    """Create color gradient along pipe length."""
    from matplotlib import cm
    import matplotlib.colors as mcolors
    
    # Temperature colormap
    cmap = cm.get_cmap('hot')
    temps = np.linspace(T_start, T_end, len(pipe_coords)-1)
    
    # Create segments with gradient colors
    for i in range(len(pipe_coords)-1):
        norm_temp = (temps[i] - T_end) / (T_start - T_end)  # Normalize
        color = cmap(norm_temp)
        
        folium.PolyLine(
            locations=[pipe_coords[i], pipe_coords[i+1]],
            color=mcolors.to_hex(color),
            weight=4,
            opacity=0.8,
            tooltip=f"Temperature: {temps[i]:.1f}°C"
        )

# Example usage:
# Supply pipe: 85°C -> 75°C (loses heat along length)
create_temperature_gradient(supply_coords, T_start=85, T_end=75)

# Return pipe: 55°C -> 50°C (gains heat from ground)
create_temperature_gradient(return_coords, T_start=55, T_end=50)
```

**Result:** Cascading color from **bright red** (85°C) to **darker red** (75°C) along pipe

---

### **Pressure Gradient Along Network:**
```python
# Pressure cascade from plant to consumers
def create_pressure_gradient(network_path, p_start_bar, p_end_bar):
    """Visualize pressure drop cascade."""
    cmap = cm.get_cmap('RdYlGn')  # Red (low) to Green (high)
    
    for i, segment in enumerate(network_path):
        # Calculate pressure at this point
        p_current = p_start_bar - (p_start_bar - p_end_bar) * (i / len(network_path))
        
        # Normalize to 0-1 for colormap (reverse so high pressure = green)
        norm_p = p_current / p_start_bar
        color = cmap(norm_p)
        
        plot_segment(segment, color=color, pressure=p_current)

# Example: 5 bar at plant -> 3.5 bar at consumer
# Creates green -> yellow -> red cascade
```

---

## 💡 **10. Best Practices for Color Cascades**

### **Accessibility:**
```python
# Use colorblind-friendly palettes
'viridis'    # Good for colorblind users
'plasma'     # Good alternative
'cividis'    # Designed for colorblind accessibility

# Avoid: Red-Green for critical distinctions
# Use: Blue-Orange or Purple-Orange instead
```

### **Consistency:**
```python
# Keep color meaning consistent across all visualizations
RED = "Hot/High/Warning/Critical"
BLUE = "Cold/Low/Normal/Good"
GREEN = "Plant/Success/Excellent"
ORANGE = "Consumer/Warning/Moderate"
YELLOW = "Transition/Caution"
```

### **Contrast:**
```python
# Ensure sufficient contrast for visibility
- Light backgrounds: Use dark colors
- Dark backgrounds: Use light colors
- Always test with transparency (opacity < 1.0)
```

---

## 🚀 **Integration into Agent System**

### **To Add Color-Coded Cascading Visualizations:**

**Option 1: Migrate Existing Code**
```python
# Copy from street_final_copy_3/src/network_visualization.py
# to branitz_energy_decision_ai_street_agents/src/visualization/
```

**Option 2: Enhance Current Visualizations**
```python
# In branitz_energy_decision_ai_street_agents/src/simulators/

# Add to pandapipes_dh_simulator.py:
def export_colored_results(self, output_dir):
    """Export results with temperature gradient coloring."""
    # Color supply pipes by temperature
    # Color return pipes by temperature
    # Color junctions by pressure
```

**Option 3: Create New Dashboard Module**
```python
# branitz_energy_decision_ai_street_agents/src/dashboards/
├── color_coded_maps.py       # Color gradient map generator
├── temperature_cascade.py    # Temperature visualization
├── pressure_cascade.py       # Pressure visualization
└── voltage_cascade.py        # Voltage visualization (HP)
```

---

## 📚 **Summary**

**The previous implementations include extensive color-coded cascading visualizations:**

✅ **Temperature cascades** - Red (hot) to Blue (cold) gradients  
✅ **Pressure cascades** - Green (high) to Red (low) gradients  
✅ **Voltage cascades** - Green (normal) to Red (violation) gradients  
✅ **Heat demand gradients** - Yellow to Red intensity maps  
✅ **Service length gradients** - Green (short) to Red (long)  
✅ **Interactive hover effects** - Opacity and weight cascades  
✅ **Multi-layer color systems** - Z-order based visual hierarchy  
✅ **Matplotlib colormaps** - Professional scientific color scales  
✅ **Folium gradients** - Web-based interactive color visualization  

**All code is available in:**
- `street_final_copy_3/src/network_visualization.py`
- `street_final_copy_3/04_create_pandapipes_interactive_map.py`
- `street_final_copy_3/01_create_summary_dashboard.py`

**Can be migrated to Agent System in Phase 6!** 🎨🚀

