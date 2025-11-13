# Plant and Building Snapping Summary

## Plant Location Setup

```python
# Plant coordinates in WGS84
PLANT_LAT, PLANT_LON = 51.76274, 14.3453979

def transform_plant_coordinates():
    """Transform plant coordinates from WGS84 to UTM."""
    from pyproj import Transformer
    
    # Create transformer from WGS84 to UTM Zone 33N (EPSG:32633)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)
    
    # Transform coordinates
    plant_x, plant_y = transformer.transform(PLANT_LON, PLANT_LAT)
    
    print(f"Plant coordinates:")
    print(f"  WGS84: {PLANT_LAT:.6f}, {PLANT_LON:.6f}")
    print(f"  UTM: {plant_x:.2f}, {plant_y:.2f}")
    
    return plant_x, plant_y

# Usage
plant_x, plant_y = transform_plant_coordinates()
# Result: UTM: 454824.25, 5734852.72
```

## 1. Plant Snapping to Nearest Network Node

```python
def snap_plant_to_network_node(plant_x, plant_y, street_network, streets_gdf):
    """Snap plant to the nearest node in the street network."""
    
    plant_point = Point(plant_x, plant_y)
    
    # Find nearest network node
    nearest_node = None
    min_distance = float('inf')
    nearest_node_coords = None
    
    for node in street_network.nodes():
        node_coords = street_network.nodes[node]['pos']
        node_point = Point(node_coords)
        distance = plant_point.distance(node_point)
        
        if distance < min_distance:
            min_distance = distance
            nearest_node = node
            nearest_node_coords = node_coords
    
    # Find which street segment contains this node
    street_segment_id = None
    for idx, street in streets_gdf.iterrows():
        street_geom = street.geometry
        if street_geom.distance(Point(nearest_node_coords)) < 1.0:  # Within 1 meter
            street_segment_id = idx
            break
    
    plant_connection = {
        'building_id': 'PLANT',
        'plant_x': plant_x,
        'plant_y': plant_y,
        'nearest_node_id': nearest_node,
        'nearest_node_x': nearest_node_coords[0],
        'nearest_node_y': nearest_node_coords[1],
        'street_segment_id': street_segment_id,
        'distance_to_node': min_distance,
        'connection_line': LineString([plant_point, Point(nearest_node_coords)])
    }
    
    return plant_connection

# Usage
plant_connection = snap_plant_to_network_node(plant_x, plant_y, street_network, streets_gdf)
# Result: Plant snapped to node node_486_0, distance: 906.87m
```

## 2. Building Snapping to Street Segments + Network Nodes

```python
def snap_buildings_to_street_segments(buildings_gdf, streets_gdf, street_network, max_distance=100):
    """Snap buildings to nearest street segments and find corresponding network nodes."""
    
    # Ensure projected CRS for accurate distances
    buildings_proj = crs_utils.ensure_projected_crs(buildings_gdf, "EPSG:32633", "Buildings")
    streets_proj = crs_utils.ensure_projected_crs(streets_gdf, "EPSG:32633", "Streets")
    
    connections = []
    
    for idx, building in buildings_proj.iterrows():
        building_geom = building.geometry
        building_id = building.get('GebaeudeID', f'building_{idx}')
        
        # STEP 1: Find nearest street segment
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
            # STEP 2: Find nearest network node to the connection point
            nearest_node = None
            nearest_node_coords = None
            min_node_distance = float('inf')
            
            for node in street_network.nodes():
                node_coords = street_network.nodes[node]['pos']
                node_point = Point(node_coords)
                node_distance = nearest_point.distance(node_point)
                
                if node_distance < min_node_distance:
                    min_node_distance = node_distance
                    nearest_node = node
                    nearest_node_coords = node_coords
            
            connection = {
                'building_id': building_id,
                'building_x': building_geom.centroid.x,
                'building_y': building_geom.centroid.y,
                'street_segment_id': nearest_street_idx,
                'connection_point_x': nearest_point.x,
                'connection_point_y': nearest_point.y,
                'nearest_node_id': nearest_node,
                'nearest_node_x': nearest_node_coords[0],
                'nearest_node_y': nearest_node_coords[1],
                'distance_to_street': min_distance,
                'distance_to_node': min_node_distance,
                'service_line': LineString([building_geom.centroid, nearest_point]),
                'connection_to_node': LineString([nearest_point, Point(nearest_node_coords)])
            }
            connections.append(connection)
    
    return pd.DataFrame(connections)

# Usage
connections_df = snap_buildings_to_street_segments(buildings_gdf, streets_gdf, street_network, max_distance=100)
```

## 3. Complete Example

```python
# Transform plant coordinates
plant_x, plant_y = transform_plant_coordinates()

# Load data
buildings_gdf = gpd.read_file("buildings_prepared.geojson")
streets_gdf = gpd.read_file("streets.geojson")

# Create street network (using your preferred method)
street_network = create_network_from_geodataframe(streets_gdf, max_edge_length=50)

# Snap plant to nearest network node
plant_connection = snap_plant_to_network_node(plant_x, plant_y, street_network, streets_gdf)

# Snap buildings to street segments and find nearest nodes
connections_df = snap_buildings_to_street_segments(buildings_gdf, streets_gdf, street_network, max_distance=100)

# Create network with service connections
network_with_services = street_network.copy()

# Add plant connection
network_with_services.add_edge(
    'PLANT', 
    plant_connection['nearest_node_id'],
    weight=plant_connection['distance_to_node'],
    edge_type='plant_connection'
)

# Add building service connections
for _, connection in connections_df.iterrows():
    network_with_services.add_edge(
        connection['building_id'],
        connection['nearest_node_id'],
        weight=connection['distance_to_node'],
        edge_type='service_connection'
    )
```

## Results Summary

### Plant Connection
- **Plant Location**: WGS84 (51.76274, 14.3453979) → UTM (454824.25, 5734852.72)
- **Nearest Node**: node_486_0 (455727.93, 5734776.73)
- **Distance**: 906.87m
- **Street Segment**: 486

### Building Connections
- **14 buildings** successfully snapped
- **Average distance to street**: 14.86m
- **Average distance to node**: 12.45m
- **Total service length**: 208.01m

### Key Data Fields

**For each building:**
- `connection_point_x/y`: Exact point on street for service connection
- `nearest_node_id`: Network node for routing
- `distance_to_street`: Distance from building to street
- `distance_to_node`: Distance from connection point to network node
- `street_segment_id`: Street segment where building connects

**For plant:**
- `nearest_node_id`: Network node for main connection
- `distance_to_node`: Distance from plant to network
- `street_segment_id`: Street segment containing the node

## Output Files

- `building_network_connections.csv` - Building connection data with nodes
- `plant_network_connection.csv` - Plant connection data
- `building_service_lines.geojson` - Service line geometries
- `plant_connection_line.geojson` - Plant connection geometry
- `plant_building_network_connections.png` - Visualization

## Network Integration

The resulting `network_with_services` contains:
- Original street network nodes and edges
- Plant connected to nearest network node
- Each building connected to nearest network node
- All connections labeled with `edge_type` for routing

This provides a complete network for district heating routing from plant to buildings via the street network. 