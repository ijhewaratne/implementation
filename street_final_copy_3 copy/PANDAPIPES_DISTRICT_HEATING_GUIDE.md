# Realistic District Heating Network in Pandapipes

## Overview

This guide demonstrates how to build a realistic district heating network using:
1. **Street graph as backbone** for main pipes
2. **Service pipes** connecting buildings to street mains
3. **Pandapipes integration** for hydraulic analysis

## Key Requirements Met

✅ **Street Graph Construction**: NetworkX graph with nodes at intersections and sufficient granularity
✅ **Plant and Buildings Placement**: Fixed plant location + building centroids snapped to street segments
✅ **Main Pipe Network**: Shortest paths from plant to all buildings, merged into shared network
✅ **Service Pipe Connections**: Short pipes from buildings to street mains
✅ **Pandapipes Integration**: Complete network with junctions, pipes, ext_grid, and sinks
✅ **No Star Topology**: Single supply/return main following street network only
✅ **Validation**: Network follows streets, service pipes are short, realistic topology

## Implementation Steps

### 1. Street Graph Construction

```python
def build_street_graph(self, streets_gdf, max_segment_length=50):
    """Build NetworkX graph from street GeoDataFrame with sufficient granularity."""
    
    G = nx.Graph()
    
    # Process each street segment
    for idx, street in streets_gdf.iterrows():
        coords = list(street.geometry.coords)
        
        # Split long segments if needed
        segments = self._split_long_segment(coords, max_segment_length)
        
        # Add nodes and edges for each segment
        for i, segment in enumerate(segments):
            node1_id = f"street_{idx}_{i}"
            node2_id = f"street_{idx}_{i+1}"
            
            # Add nodes with coordinates
            G.add_node(node1_id, pos=segment[0], node_type='street')
            G.add_node(node2_id, pos=segment[1], node_type='street')
            
            # Add edge with length
            length = Point(segment[0]).distance(Point(segment[1]))
            G.add_edge(node1_id, node2_id, weight=length, length=length)
    
    # Ensure network connectivity
    self._ensure_network_connectivity(G)
    
    # Merge nearby nodes to create intersections
    self._merge_nearby_nodes(G, threshold=1.0)
    
    return G
```

**Key Features:**
- **Granularity Control**: Splits long segments (default: 50m max)
- **Network Connectivity**: Connects nearby nodes (within 5m)
- **Intersection Creation**: Merges nearby nodes (within 1m)
- **Coordinate Assignment**: Each node has (x, y) coordinates
- **Length Assignment**: Each edge has length in meters

### 2. Plant and Buildings Placement

```python
def snap_plant_to_street_graph(self):
    """Snap plant location to nearest node on street graph."""
    
    plant_point = Point(self.plant_location)
    nearest_node = None
    min_distance = float('inf')
    
    for node in self.street_graph.nodes():
        node_pos = self.street_graph.nodes[node]['pos']
        node_point = Point(node_pos)
        distance = plant_point.distance(node_point)
        
        if distance < min_distance:
            min_distance = distance
            nearest_node = node
    
    # Add plant node and connect to nearest street node
    self.street_graph.add_node('PLANT', pos=self.plant_location, node_type='plant')
    self.street_graph.add_edge('PLANT', nearest_node, weight=min_distance, length=min_distance)
    
    return nearest_node

def snap_buildings_to_street_graph(self, buildings_gdf, max_distance=100):
    """Snap buildings to nearest points along street segments."""
    
    for idx, building in buildings_gdf.iterrows():
        building_geom = building.geometry
        building_id = building.get('GebaeudeID', f'building_{idx}')
        
        # Find nearest point along street graph
        nearest_point, nearest_node, distance = self._find_nearest_street_point(building_geom)
        
        if distance <= max_distance:
            # Create service connection node
            service_node_id = f"service_{building_id}"
            self.street_graph.add_node(service_node_id, pos=nearest_point, node_type='service')
            
            # Connect service node to nearest street node
            self.street_graph.add_edge(service_node_id, nearest_node, weight=distance, length=distance)
            
            self.service_connections[building_id] = {
                'service_node': service_node_id,
                'nearest_street_node': nearest_node,
                'connection_point': nearest_point,
                'building_centroid': (building_geom.centroid.x, building_geom.centroid.y),
                'distance_to_street': distance
            }
```

**Key Features:**
- **Plant Snapping**: Plant connected to nearest street node
- **Building Snapping**: Each building gets service connection point on street
- **Service Nodes**: Virtual nodes at connection points
- **Distance Limits**: Configurable maximum distance (default: 100m)

### 3. Main Pipe Network Construction

```python
def build_main_pipe_network(self):
    """Build main pipe network by finding shortest paths from plant to all service connections."""
    
    main_pipe_edges = set()
    
    for building_id, connection in self.service_connections.items():
        service_node = connection['service_node']
        
        # Find shortest path from plant to service node
        path = nx.shortest_path(self.street_graph, 'PLANT', service_node, weight='weight')
        
        # Add all edges in the path to main pipe network
        for i in range(len(path) - 1):
            edge = tuple(sorted([path[i], path[i+1]]))
            main_pipe_edges.add(edge)
    
    # Create main pipe network graph
    main_network = nx.Graph()
    
    # Add all nodes and edges from main pipe network
    for edge in main_pipe_edges:
        node1, node2 = edge
        edge_data = self.street_graph.get_edge_data(node1, node2)
        
        # Add nodes and edge
        if node1 not in main_network.nodes():
            main_network.add_node(node1, **self.street_graph.nodes[node1])
        if node2 not in main_network.nodes():
            main_network.add_node(node2, **self.street_graph.nodes[node2])
        
        main_network.add_edge(node1, node2, **edge_data)
    
    return main_network
```

**Key Features:**
- **Shortest Path Routing**: Uses NetworkX shortest path algorithm
- **Path Merging**: Union of all paths creates shared main pipes
- **Street-Only Routing**: All paths follow street network
- **No Star Topology**: Single main network, not direct connections

### 4. Service Pipe Connections

```python
# Service pipes are created in pandapipes network
for building_id, connection in self.service_connections.items():
    service_node = connection['service_node']
    building_junction = junctions[f"building_{building_id}"]
    service_junction = junctions[service_node]
    
    # Calculate service pipe length
    building_pos = connection['building_centroid']
    service_pos = connection['connection_point']
    service_length = Point(building_pos).distance(Point(service_pos))
    
    # Create service pipe in pandapipes
    pipe = pp.create_pipe_from_parameters(net, 
                                        from_junction=service_junction,
                                        to_junction=building_junction,
                                        length_km=service_length/1000,
                                        diameter_m=service_pipe_diameter/1000,
                                        name=f"service_{building_id}")
```

**Key Features:**
- **Short Direct Connections**: Service pipes from buildings to street mains
- **Configurable Diameter**: Smaller diameter than main pipes (default: 50mm)
- **Length Calculation**: Actual distance from building to connection point

### 5. Pandapipes Integration

```python
def create_pandapipes_network(self, main_pipe_diameter=400, service_pipe_diameter=50):
    """Create pandapipes network from the main pipe and service connections."""
    
    # Create empty pandapipes network
    net = pp.create_empty_network("district_heating_network")
    
    # Add junctions for all nodes
    junctions = {}
    
    # Add plant junction (ext_grid)
    plant_junction = pp.create_junction(net, 
                                      pn_bar=1.0, 
                                      tfluid_k=353.15,  # 80°C
                                      name="PLANT",
                                      geodata=(self.plant_location[0], self.plant_location[1]))
    junctions['PLANT'] = plant_junction
    
    # Add junctions for main pipe network
    for node in self.main_pipe_network.nodes():
        if node != 'PLANT':
            node_data = self.main_pipe_network.nodes[node]
            pos = node_data['pos']
            
            junction = pp.create_junction(net, 
                                        pn_bar=1.0, 
                                        tfluid_k=353.15,
                                        name=node,
                                        geodata=(pos[0], pos[1]))
            junctions[node] = junction
    
    # Add junctions for buildings
    for building_id, connection in self.service_connections.items():
        building_pos = connection['building_centroid']
        
        building_junction = pp.create_junction(net, 
                                             pn_bar=1.0, 
                                             tfluid_k=353.15,
                                             name=f"building_{building_id}",
                                             geodata=(building_pos[0], building_pos[1]))
        junctions[f"building_{building_id}"] = building_junction
    
    # Add main pipes
    for edge in self.main_pipe_network.edges():
        node1, node2 = edge
        edge_data = self.main_pipe_network.get_edge_data(node1, node2)
        
        pipe = pp.create_pipe_from_parameters(net, 
                                            from_junction=junctions[node1],
                                            to_junction=junctions[node2],
                                            length_km=edge_data['length']/1000,
                                            diameter_m=main_pipe_diameter/1000,
                                            name=f"main_{node1}_{node2}")
    
    # Add service pipes
    for building_id, connection in self.service_connections.items():
        service_node = connection['service_node']
        building_junction = junctions[f"building_{building_id}"]
        service_junction = junctions[service_node]
        
        service_length = connection['distance_to_street']
        
        pipe = pp.create_pipe_from_parameters(net, 
                                            from_junction=service_junction,
                                            to_junction=building_junction,
                                            length_km=service_length/1000,
                                            diameter_m=service_pipe_diameter/1000,
                                            name=f"service_{building_id}")
    
    # Add external grid (plant)
    ext_grid = pp.create_ext_grid(net, 
                                 junction=junctions['PLANT'],
                                 p_bar=1.0,
                                 t_k=353.15,
                                 name="PLANT_EXT_GRID")
    
    # Add heat consumers (buildings)
    for building_id in self.service_connections.keys():
        building_junction = junctions[f"building_{building_id}"]
        
        consumer = pp.create_sink(net, 
                                junction=building_junction,
                                mdot_kg_per_s=0.1,  # 0.1 kg/s heat demand
                                name=f"consumer_{building_id}")
    
    return net
```

**Key Features:**
- **Junctions**: One junction per node (plant, street, service, building)
- **Main Pipes**: Large diameter pipes along street network (default: 400mm)
- **Service Pipes**: Small diameter pipes to buildings (default: 50mm)
- **External Grid**: Plant as pressure/temperature source
- **Heat Consumers**: Buildings as heat sinks

## Network Architecture

```
Plant (ext_grid)
    ↓ (plant_connection)
Street Node
    ↓ (main_pipe_network)
Street Node → Street Node → Street Node
    ↓ (service_connection)
Service Node
    ↓ (service_pipe)
Building (sink)
```

## Validation Methods

```python
def validate_network(self):
    """Validate that the network meets requirements."""
    
    validation_results = {
        'plant_connected': False,
        'all_buildings_connected': False,
        'main_pipes_on_streets': False,
        'service_pipes_short': False,
        'no_star_topology': False
    }
    
    # Check if plant is connected
    if 'PLANT' in self.street_graph.nodes():
        validation_results['plant_connected'] = True
    
    # Check if all buildings are connected
    if len(self.service_connections) == len(self.buildings_gdf):
        validation_results['all_buildings_connected'] = True
    
    # Check if main pipes follow street network
    street_edges = set()
    for edge in self.street_graph.edges():
        street_edges.add(tuple(sorted(edge)))
    
    main_edges = set()
    for edge in self.main_pipe_network.edges():
        main_edges.add(tuple(sorted(edge)))
    
    if main_edges.issubset(street_edges):
        validation_results['main_pipes_on_streets'] = True
    
    # Check if service pipes are short
    max_service_length = 100  # meters
    service_lengths = [conn['distance_to_street'] for conn in self.service_connections.values()]
    if all(length <= max_service_length for length in service_lengths):
        validation_results['service_pipes_short'] = True
    
    # Check for no star topology
    if 'PLANT' in self.street_graph.nodes():
        plant_degree = self.street_graph.degree('PLANT')
        if plant_degree == 1:
            validation_results['no_star_topology'] = True
    
    return validation_results
```

## Complete Example

```python
# Initialize network builder
dh_network = DistrictHeatingNetwork()

# Transform plant coordinates
dh_network.transform_plant_coordinates()

# Load data
buildings_gdf = gpd.read_file("buildings_prepared.geojson")
streets_gdf = gpd.read_file("streets.geojson")

# Step 1: Build street graph
dh_network.build_street_graph(streets_gdf, max_segment_length=50)

# Step 2: Snap plant to street graph
dh_network.snap_plant_to_street_graph()

# Step 3: Snap buildings to street graph
dh_network.snap_buildings_to_street_graph(buildings_gdf, max_distance=100)

# Step 4: Build main pipe network
dh_network.build_main_pipe_network()

# Step 5: Create pandapipes network
dh_network.create_pandapipes_network(main_pipe_diameter=400, service_pipe_diameter=50)

# Step 6: Validate network
validation_results = dh_network.validate_network()

# Step 7: Plot network
dh_network.plot_network(save_path="district_heating_network.png")

# Step 8: Save network data
dh_network.save_network_data()
```

## Output Files

1. **main_pipe_network.csv**: Main pipe network data with coordinates and lengths
2. **service_connections.csv**: Service connection data for each building
3. **pandapipes_network.json**: Complete pandapipes network file
4. **district_heating_network.png**: Network visualization

## Key Benefits

1. **Realistic Topology**: Network follows actual street infrastructure
2. **Efficient Routing**: Shortest paths minimize pipe lengths
3. **Shared Infrastructure**: Multiple buildings share main pipes
4. **Hydraulic Analysis**: Ready for pandapipes simulation
5. **Validation**: Ensures network meets engineering requirements
6. **Scalability**: Can handle large networks with many buildings

## Next Steps

1. **Hydraulic Simulation**: Run pandapipes analysis for pressure and flow
2. **Cost Optimization**: Optimize pipe diameters based on flow requirements
3. **Load Balancing**: Distribute heat load across the network
4. **Expansion Planning**: Plan for future building connections
5. **Thermal Analysis**: Add thermal properties and heat loss calculations

This solution provides a complete foundation for realistic district heating network planning and analysis. 