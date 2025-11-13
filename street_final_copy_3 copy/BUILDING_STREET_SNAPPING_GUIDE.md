# Building to Street Network Snapping Guide

This guide explains how to snap buildings and plants to street networks to create service connection points for district heating systems.

## Overview

The goal is to find the closest point along any street segment (not just intersections) for each building, which will serve as the service connection location for district heating pipes.

## Key Concepts

### 1. **Nearest Point on Street Segment**
- Use `shapely.ops.nearest_points()` to find the closest point between a building and a street segment
- This gives you the exact point along the street geometry, not just the nearest node
- More realistic than snapping to intersections only

### 2. **Service Connection Data**
For each building, record:
- `building_id`: Building identifier
- `street_segment_id`: Which street segment the building connects to
- `connection_x/y`: Exact coordinates of the connection point on the street
- `distance_meters`: Distance from building to street
- `service_line`: Geometry of the service connection line

### 3. **Coordinate Reference System (CRS)**
- **Critical**: Use projected CRS (e.g., UTM EPSG:32633) for accurate distance calculations
- Geographic CRS (EPSG:4326) gives incorrect distances
- Our `crs_utils` module handles this automatically

## Code Examples

### Basic Snapping Function

```python
def snap_buildings_to_streets(buildings_gdf, streets_gdf, max_distance=100):
    """Snap buildings to nearest street segments."""
    
    # Ensure projected CRS for accurate distances
    buildings_proj = crs_utils.ensure_projected_crs(buildings_gdf, "EPSG:32633", "Buildings")
    streets_proj = crs_utils.ensure_projected_crs(streets_gdf, "EPSG:32633", "Streets")
    
    connections = []
    
    for idx, building in buildings_proj.iterrows():
        building_geom = building.geometry
        building_id = building.get('GebaeudeID', f'building_{idx}')
        
        # Find nearest street segment
        min_distance = float('inf')
        nearest_street_idx = None
        nearest_point = None
        
        for street_idx, street in streets_proj.iterrows():
            street_geom = street.geometry
            
            # Find nearest points between building and street
            building_point, street_point = nearest_points(building_geom, street_geom)
            distance = building_point.distance(street_point)
            
            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_street_idx = street_idx
                nearest_point = street_point
        
        if nearest_point is not None:
            connection = {
                'building_id': building_id,
                'building_x': building_geom.centroid.x,
                'building_y': building_geom.centroid.y,
                'street_segment_id': nearest_street_idx,
                'connection_x': nearest_point.x,
                'connection_y': nearest_point.y,
                'distance_meters': min_distance,
                'service_line': LineString([building_geom.centroid, nearest_point])
            }
            connections.append(connection)
    
    return pd.DataFrame(connections)
```

### Plant Snapping

```python
def snap_plant_to_streets(plant_location, streets_gdf, max_distance=100):
    """Snap plant to nearest street segment."""
    
    # Convert to Point if needed
    if isinstance(plant_location, (tuple, list)):
        plant_point = Point(plant_location[0], plant_location[1])
    else:
        plant_point = plant_location
    
    # Ensure projected CRS
    streets_proj = crs_utils.ensure_projected_crs(streets_gdf, "EPSG:32633", "Streets")
    
    min_distance = float('inf')
    nearest_street_idx = None
    nearest_point = None
    
    for street_idx, street in streets_proj.iterrows():
        street_geom = street.geometry
        
        # Find nearest points between plant and street
        plant_closest, street_closest = nearest_points(plant_point, street_geom)
        distance = plant_closest.distance(street_closest)
        
        if distance < min_distance and distance <= max_distance:
            min_distance = distance
            nearest_street_idx = street_idx
            nearest_point = street_closest
    
    if nearest_point is not None:
        return {
            'building_id': 'PLANT',
            'building_x': plant_point.x,
            'building_y': plant_point.y,
            'street_segment_id': nearest_street_idx,
            'connection_x': nearest_point.x,
            'connection_y': nearest_point.y,
            'distance_meters': min_distance,
            'service_line': LineString([plant_point, nearest_point])
        }
    
    return None
```

## Usage Examples

### 1. Basic Usage

```python
# Load data
buildings_gdf = gpd.read_file("buildings_prepared.geojson")
streets_gdf = gpd.read_file("streets.geojson")

# Snap buildings to streets
connections_df = snap_buildings_to_streets(buildings_gdf, streets_gdf, max_distance=100)

# Snap plant to streets
plant_location = buildings_gdf.geometry.unary_union.centroid
plant_connection = snap_plant_to_streets(plant_location, streets_gdf, max_distance=100)

# Save results
connections_df.to_csv("building_connections.csv", index=False)
```

### 2. With NetworkX Integration

```python
# After creating street network with NetworkX
import networkx as nx

# Snap buildings to streets first
connections_df = snap_buildings_to_streets(buildings_gdf, streets_gdf)

# Then connect to network nodes for routing
for _, connection in connections_df.iterrows():
    connection_point = Point(connection['connection_x'], connection['connection_y'])
    
    # Find nearest network node
    nearest_node = None
    min_dist = float('inf')
    
    for node in G.nodes():
        node_coords = G.nodes[node]['pos']
        node_point = Point(node_coords)
        dist = connection_point.distance(node_point)
        
        if dist < min_dist:
            min_dist = dist
            nearest_node = node
    
    # Add service connection edge
    G.add_edge(connection['building_id'], nearest_node, 
               weight=connection['distance_meters'],
               edge_type='service_connection')
```

## Output Data Structure

### Building Connections CSV
```csv
building_id,building_x,building_y,street_segment_id,connection_x,connection_y,distance_meters
DEBBAL520000w9DJ,456032.83,5734478.23,707,455993.04,5734498.82,23.58
DEBBAL520000w9DK,456037.85,5734509.38,707,456018.76,5734521.54,12.40
```

### Plant Connection CSV
```csv
building_id,building_x,building_y,street_segment_id,connection_x,connection_y,distance_meters
PLANT,456023.13,5734455.86,122,455981.77,5734446.27,42.46
```

## Key Benefits

1. **Realistic Connections**: Finds exact points along street segments, not just intersections
2. **Accurate Distances**: Uses projected CRS for precise distance calculations
3. **Flexible Integration**: Works with both GeoDataFrames and NetworkX graphs
4. **Complete Data**: Records all necessary information for service pipe design
5. **Visualization**: Includes plotting functions for verification

## Next Steps

1. **Service Pipe Design**: Use connection points as endpoints for service pipes
2. **Network Routing**: Connect service points to street network nodes
3. **Cost Calculation**: Calculate pipe lengths and costs based on distances
4. **Optimization**: Optimize connection points for minimal total pipe length
5. **Validation**: Verify connections meet engineering standards

## Files Created

- `building_street_snapping.py` - Comprehensive snapping class with analysis
- `simple_snapping_example.py` - Basic example showing key concepts
- `BUILDING_STREET_SNAPPING_GUIDE.md` - This guide

## Output Files

- `building_connections.csv` - Tabular connection data
- `building_connections.geojson` - Service line geometries
- `plant_connection.csv` - Plant connection data
- `plant_connection.geojson` - Plant service line geometry
- `simple_snapping_results.png` - Visualization of connections

## Running the Examples

```bash
# Activate environment
conda activate branitz_env

# Run comprehensive example
python building_street_snapping.py

# Run simple example
python simple_snapping_example.py
```

This approach provides a solid foundation for creating realistic service connections in district heating network planning. 