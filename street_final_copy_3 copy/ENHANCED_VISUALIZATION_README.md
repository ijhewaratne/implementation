# Enhanced Network Visualization with Street Map Overlays

This document describes the enhanced network visualization capabilities added to the Branitz Energy Decision AI system, which allow you to overlay your district heating (DH) network on actual street maps.

## 🗺️ Overview

The enhanced visualization system provides two main approaches for displaying DH networks with street context:

1. **Static Maps** - High-quality PNG images with OSM street overlay using GeoPandas + Contextily
2. **Interactive Maps** - Web-based interactive maps using Folium that can be opened in any browser

## 🚀 Quick Start

### Installation

First, install the additional dependencies:

```bash
pip install contextily folium
```

Or update your environment:

```bash
conda activate branitz_env
pip install -r requirements.txt
```

### Basic Usage

#### 1. Demo Network Visualization

Test the enhanced visualization with a demo network:

```bash
python enhanced_visualization_demo.py --demo --static --interactive
```

This will create:
- `simulation_outputs/street_map_dh_demo_network.png` - Static map with street overlay
- `simulation_outputs/interactive_dh_demo_network.html` - Interactive map

#### 2. Real Street Analysis

For existing street analysis results:

```bash
python enhanced_visualization_demo.py --street "Bleyerstraße" --static
```

#### 3. Integrated with Pipeline

The enhanced visualization is automatically integrated into the simulation pipeline. When you run:

```bash
python interactive_run_enhanced.py
```

The system will now generate both enhanced static and interactive maps alongside the basic network plots.

## 📊 Static Maps (GeoPandas + Contextily)

### Features

- **OSM Street Overlay**: Real street network from OpenStreetMap
- **High Resolution**: 300 DPI output suitable for reports and presentations
- **Automatic Coordinate Transformation**: Converts from local CRS to Web Mercator
- **Building Context**: Shows buildings as background context
- **Professional Styling**: Clean, publication-ready visualizations

### Output Elements

- **Red lines**: Supply pipes (thicker)
- **Blue lines**: Return pipes (thinner)
- **Red dots**: Supply junctions
- **Blue dots**: Return junctions
- **Orange triangles**: Heat consumers (buildings)
- **Green square**: CHP Plant
- **Statistics box**: Key network parameters

### Example Output

```
simulation_outputs/street_map_dh_street_Bleyerstraße.png
```

## 🌐 Interactive Maps (Folium)

### Features

- **Web-based**: Open in any modern web browser
- **Pan & Zoom**: Navigate around the network interactively
- **Clickable Elements**: Get detailed information about pipes, junctions, and consumers
- **Multiple Layers**: Toggle between different map providers
- **Export Capabilities**: Save views or take screenshots

### Interactive Elements

- **Hover Tooltips**: See pipe names and junction information
- **Click Popups**: Detailed information about network components
- **Legend**: Built-in legend explaining the color coding
- **Responsive Design**: Works on desktop and mobile devices

### Example Output

```
simulation_outputs/interactive_dh_street_Bleyerstraße.html
```

## 🔧 Technical Details

### Coordinate Systems

The system automatically handles coordinate transformations:

1. **Input**: Local projected CRS (e.g., EPSG:25833 for Germany)
2. **Processing**: Web Mercator (EPSG:3857) for OSM compatibility
3. **Output**: Properly aligned with street maps

### Dependencies

#### Required
- `geopandas` - Spatial data handling
- `matplotlib` - Static plotting
- `pandapipes` - Network simulation

#### Enhanced Features
- `contextily` - OSM tile overlays for static maps
- `folium` - Interactive web maps
- `pyproj` - Coordinate transformations

### File Structure

```
src/
├── network_visualization.py     # Enhanced visualization module
├── simulation_runner.py         # Updated to use enhanced viz
└── ...

simulation_outputs/
├── dh_street_[NAME].png         # Basic network plot (legacy)
├── street_map_dh_[NAME].png     # Enhanced static map
└── interactive_dh_[NAME].html   # Interactive map

enhanced_visualization_demo.py   # Standalone demo script
```

## 🎨 Customization

### Static Map Customization

You can customize the static maps by modifying the `create_static_network_map` function:

```python
from src.network_visualization import create_static_network_map

# Custom static map
static_file = create_static_network_map(
    net=network,
    scenario_name="My Scenario",
    output_dir="custom_output",
    include_street_map=True,  # Set to False for no street overlay
    buildings_gdf=buildings   # Optional building context
)
```

### Interactive Map Customization

Customize interactive maps:

```python
from src.network_visualization import create_interactive_network_map

# Custom interactive map
interactive_file = create_interactive_network_map(
    net=network,
    scenario_name="My Scenario",
    output_dir="custom_output",
    buildings_gdf=buildings  # Optional building context
)
```

### Map Providers

You can change the map provider in the static maps:

```python
# In network_visualization.py, modify the ctx.add_basemap call:
ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron)  # Light theme
ctx.add_basemap(ax, source=ctx.providers.CartoDB.DarkMatter)  # Dark theme
ctx.add_basemap(ax, source=ctx.providers.Stamen.Terrain)  # Terrain
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Contextily Installation Issues

```bash
# On macOS with conda
conda install -c conda-forge contextily

# On Linux/Windows
pip install contextily
```

#### 2. Coordinate System Errors

If you see coordinate transformation errors:

```python
# Check your network's CRS
print(f"Network CRS: {net.junction.crs}")
print(f"Buildings CRS: {buildings_gdf.crs}")
```

#### 3. Memory Issues with Large Networks

For very large networks, you can disable street overlays:

```python
static_file = create_static_network_map(
    net=network,
    scenario_name="Large Network",
    include_street_map=False  # Disable OSM overlay
)
```

#### 4. Folium Not Working

Ensure you have the latest version:

```bash
pip install --upgrade folium
```

### Error Messages

- `"contextily not available"`: Install with `pip install contextily`
- `"folium not available"`: Install with `pip install folium`
- `"Coordinate transformation failed"`: Check your input CRS
- `"No buildings found"`: Ensure building data is properly loaded

## 📈 Performance Considerations

### Static Maps
- **Small networks** (< 50 buildings): ~5-10 seconds
- **Medium networks** (50-200 buildings): ~10-30 seconds
- **Large networks** (> 200 buildings): ~30-60 seconds

### Interactive Maps
- **Small networks**: ~2-5 seconds
- **Medium networks**: ~5-15 seconds
- **Large networks**: ~15-30 seconds

### Memory Usage
- Static maps: ~100-500 MB depending on network size
- Interactive maps: ~50-200 MB depending on network size

## 🔄 Integration with Existing Workflow

The enhanced visualization is seamlessly integrated into the existing workflow:

1. **Interactive Run**: `interactive_run_enhanced.py` now generates enhanced maps
2. **Simulation Pipeline**: `simulation_runner.py` automatically creates enhanced visualizations
3. **Backward Compatibility**: Basic plots are still generated for compatibility

### Automatic Generation

When you run the simulation pipeline, you'll now get:

```
simulation_outputs/
├── dh_street_Bleyerstraße.png           # Basic plot (legacy)
├── street_map_dh_street_Bleyerstraße.png # Enhanced static
├── interactive_dh_street_Bleyerstraße.html # Interactive
└── street_Bleyerstraße_results.json     # Results data
```

## 🎯 Use Cases

### 1. Urban Planning
- Show DH network feasibility in real street context
- Identify optimal pipe routing along existing streets
- Assess building density and connection potential

### 2. Stakeholder Communication
- Interactive maps for public presentations
- High-quality static maps for reports
- Easy sharing via web links

### 3. Technical Analysis
- Detailed network inspection with street context
- Identify potential construction challenges
- Plan construction phases

### 4. Decision Support
- Compare different street scenarios
- Assess network efficiency in real context
- Support investment decisions

## 🚀 Future Enhancements

Planned improvements:

1. **3D Visualization**: Add height information for underground pipes
2. **Time Series**: Show network evolution over time
3. **Cost Overlay**: Display construction costs on the map
4. **Environmental Impact**: Show CO2 savings visualization
5. **Mobile App**: Native mobile application for field use

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review the demo script for working examples
3. Ensure all dependencies are properly installed
4. Check that your data is in the correct coordinate system

---

*This enhanced visualization system transforms your DH network analysis from abstract technical diagrams into practical, context-rich maps that support real-world decision making.* 