# CRS Utilities for Branitz Energy Decision AI

This document explains how to use the Coordinate Reference System (CRS) utilities to ensure accurate distance calculations in your energy analysis workflow.

## 🎯 Why CRS Matters

**Problem**: Geographic coordinate systems (like WGS84/EPSG:4326) are not suitable for distance calculations because:
- Distances are distorted at different latitudes
- Units are in degrees, not meters
- Calculations can be significantly inaccurate

**Solution**: Use projected coordinate systems (like UTM) for:
- Accurate distance measurements in meters
- Proper area calculations
- Reliable spatial analysis

## 📦 What's Included

### 1. Core CRS Utilities (`src/crs_utils.py`)

```python
from src import crs_utils

# Check CRS information
info = crs_utils.check_crs_info(gdf, "My Data")

# Convert to projected CRS
gdf_proj = crs_utils.ensure_projected_crs(gdf, target_crs="EPSG:32633")

# Ensure both datasets use same CRS
buildings_proj, streets_proj = crs_utils.ensure_same_crs(buildings_gdf, streets_gdf)

# Quick compatibility check
ready = crs_utils.quick_crs_check(buildings_gdf, streets_gdf)
```

### 2. Integrated Data Preparation (`src/data_preparation.py`)

```python
from src import data_preparation

# Load and prepare data with automatic CRS handling
buildings_gdf, edges_gdf, nodes_gdf, graph = data_preparation.load_and_prepare_data(
    buildings_file="data/geojson/buildings.geojson",
    osm_file="data/osm/streets.osm",
    output_dir="results",
    ensure_projected=True  # Automatically convert to UTM
)
```

### 3. Standalone CRS Checker (`check_and_fix_crs.py`)

```bash
# Check and fix CRS issues
python check_and_fix_crs.py --demo-distances

# Use specific output directory
python check_and_fix_crs.py --output-dir results_test
```

## 🚀 Quick Start

### Option 1: Use the Integrated Pipeline

The main pipeline now automatically handles CRS conversion:

```bash
# Run the full pipeline with automatic CRS handling
python main.py --config config_interactive_run.yaml
```

### Option 2: Manual CRS Handling

```python
import geopandas as gpd
from src import crs_utils

# Load your data
buildings_gdf = gpd.read_file("results_test/buildings_prepared.geojson")
streets_gdf = gpd.read_file("results_test/streets.geojson")

# Check current CRS
print(f"Buildings CRS: {buildings_gdf.crs}")
print(f"Streets CRS: {streets_gdf.crs}")

# Convert to same projected CRS
buildings_proj, streets_proj = crs_utils.ensure_same_crs(buildings_gdf, streets_gdf)

# Now you can do accurate distance calculations
distance = buildings_proj.iloc[0].geometry.distance(streets_proj.iloc[0].geometry)
print(f"Distance: {distance:.2f} meters")
```

### Option 3: Run Examples

```bash
# Run the example script to see all features
python example_crs_usage.py
```

## 🔧 Key Functions

### `check_crs_info(gdf, name)`
Returns detailed CRS information:
```python
info = crs_utils.check_crs_info(gdf, "Buildings")
print(info)
# Output:
# {
#     'name': 'Buildings',
#     'crs': EPSG:4326,
#     'crs_name': 'WGS 84',
#     'is_projected': False,
#     'is_geographic': True,
#     'needs_conversion': True,
#     'warning': 'Geographic CRS detected. Convert to projected CRS...'
# }
```

### `ensure_same_crs(buildings_gdf, streets_gdf)`
Ensures both datasets use the same projected CRS:
```python
buildings_proj, streets_proj = crs_utils.ensure_same_crs(buildings_gdf, streets_gdf)
# Both will be in UTM Zone 33N (EPSG:32633) for your region
```

### `get_distance_calculator(buildings_gdf, streets_gdf)`
Creates a function for calculating distances:
```python
calc_distances = crs_utils.get_distance_calculator(buildings_gdf, streets_gdf)
results = calc_distances()
# Returns list of dicts with building_id, nearest_street, distance_meters
```

## 📍 Recommended CRS for Your Region

For the Branitz/Cottbus area in Germany:
- **UTM Zone 33N**: `EPSG:32633` (recommended for analysis)
- **ETRS89 / UTM zone 33N**: `EPSG:25833` (German standard)
- **Web Mercator**: `EPSG:3857` (for web mapping)

The utilities automatically detect and use UTM Zone 33N for your data.

## 🔄 Integration with Existing Code

### Before (Problematic):
```python
# This can give inaccurate results
buildings_gdf = gpd.read_file("buildings.geojson")
streets_gdf = gpd.read_file("streets.geojson")
distance = buildings_gdf.iloc[0].geometry.distance(streets_gdf.iloc[0].geometry)
```

### After (Accurate):
```python
# This ensures accurate results
from src import crs_utils
buildings_gdf = gpd.read_file("buildings.geojson")
streets_gdf = gpd.read_file("streets.geojson")
buildings_proj, streets_proj = crs_utils.ensure_same_crs(buildings_gdf, streets_gdf)
distance = buildings_proj.iloc[0].geometry.distance(streets_proj.iloc[0].geometry)
```

## 🛠️ Advanced Usage

### Custom CRS Conversion
```python
# Convert to specific CRS
web_mercator = crs_utils.ensure_projected_crs(gdf, "EPSG:3857", "My Data")

# Convert between different projected CRS
utm_33n = crs_utils.ensure_projected_crs(web_mercator, "EPSG:32633", "My Data")
```

### Batch Processing
```python
# Process multiple files with same CRS
files = ["file1.geojson", "file2.geojson", "file3.geojson"]
target_crs = "EPSG:32633"

for file_path in files:
    gdf = gpd.read_file(file_path)
    gdf_proj = crs_utils.ensure_projected_crs(gdf, target_crs, f"File: {file_path}")
    # Process gdf_proj...
```

### Save with CRS Information
```python
# Save with explicit CRS
crs_utils.save_with_crs(gdf_proj, "output.geojson")
```

## 🐛 Troubleshooting

### Common Issues

1. **"No CRS defined"**
   ```python
   # Solution: Set CRS explicitly
   gdf.crs = "EPSG:4326"  # If you know it's WGS84
   ```

2. **"Cannot determine target CRS"**
   ```python
   # Solution: Specify target CRS manually
   gdf_proj = crs_utils.ensure_projected_crs(gdf, "EPSG:32633", "My Data")
   ```

3. **"Error converting CRS"**
   ```python
   # Solution: Check if geometries are valid
   gdf = gdf[gdf.geometry.is_valid]
   gdf_proj = crs_utils.ensure_projected_crs(gdf, "EPSG:32633", "My Data")
   ```

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check CRS step by step
info = crs_utils.check_crs_info(gdf, "Debug")
print(info)
```

## 📊 Performance Notes

- **Small datasets** (< 1000 features): CRS conversion is nearly instant
- **Medium datasets** (1000-10000 features): ~1-5 seconds
- **Large datasets** (> 10000 features): Consider processing in chunks

## 🔗 Related Files

- `src/crs_utils.py` - Core CRS utilities
- `src/data_preparation.py` - Updated with CRS handling
- `main.py` - Updated pipeline with automatic CRS conversion
- `check_and_fix_crs.py` - Standalone CRS checker
- `example_crs_usage.py` - Usage examples

## 📚 Further Reading

- [GeoPandas CRS Documentation](https://geopandas.org/en/stable/docs/user_guide/projections.html)
- [EPSG Codes](https://epsg.io/) - Find appropriate CRS for your region
- [UTM Zones](https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system) - Understanding UTM coordinate systems

---

**Remember**: Always use projected CRS for distance calculations, and ensure both datasets use the same CRS for accurate results! 