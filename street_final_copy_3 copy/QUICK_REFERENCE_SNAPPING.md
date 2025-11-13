# Quick Reference: Building to Street Snapping

## Essential Code Snippets

### 1. Basic Building Snapping
```python
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString
from src import crs_utils

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

### 2. Plant Snapping
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

### 3. Usage Example
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

### 4. NetworkX Integration
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

## Key Points

1. **Use projected CRS** (EPSG:32633) for accurate distance calculations
2. **nearest_points()** finds exact point on street segment, not just nearest node
3. **Record street_segment_id** for later network integration
4. **connection_x/y** are the exact coordinates on the street for service connection
5. **distance_meters** is the service pipe length from building to street

## Output Data Structure

```csv
building_id,building_x,building_y,street_segment_id,connection_x,connection_y,distance_meters
DEBBAL520000w9DJ,456032.83,5734478.23,707,455993.04,5734498.82,23.58
DEBBAL520000w9DK,456037.85,5734509.38,707,456018.76,5734521.54,12.40
```

## Files to Run

```bash
# Simple example
python simple_snapping_example.py

# Comprehensive example with analysis
python building_street_snapping.py
``` 