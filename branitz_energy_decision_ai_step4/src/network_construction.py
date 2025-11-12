# network_construction.py
import networkx as nx
import geopandas as gpd
from shapely.geometry import Point
import os
import matplotlib.pyplot as plt
import pandas as pd
from shapely import wkt


def count_edges_with_positions(G):
    count = 0
    edges_with_position = []
    for u, v in G.edges():
        node_u = G.nodes[u]
        node_v = G.nodes[v]
        # Get WKT and check if both nodes have geometry that can be parsed as a Point/LineString/etc.
        try:
            geom_u = node_u.get('geometry')
            geom_v = node_v.get('geometry')
            if geom_u and geom_v:
                # Try parsing both with shapely
                gu = wkt.loads(geom_u)
                gv = wkt.loads(geom_v)
                # Optionally, check if both have x/y (i.e., are Points)
                if hasattr(gu, "x") and hasattr(gv, "x"):
                    count += 1
                    edges_with_position.append((u, v))
        except Exception as e:
            continue
    return count, edges_with_position
def assign_buildings_to_nearest_node(buildings_gdf, nodes_gdf, node_id_col='node_id'):
    # If not already projected, project both to UTM Zone 33N (EPSG:32633), or your local UTM
    # You may need to change 32633 to match your region!
    metric_crs = "EPSG:32633"
    if buildings_gdf.crs is None or not buildings_gdf.crs.is_projected:
        buildings_gdf = buildings_gdf.to_crs(metric_crs)
    if nodes_gdf.crs is None or not nodes_gdf.crs.is_projected:
        nodes_gdf = nodes_gdf.to_crs(metric_crs)

    node_points = nodes_gdf.copy()
    node_points['pt'] = node_points.geometry.centroid

    assignments = []
    for idx, b in buildings_gdf.iterrows():
        b_centroid = b.geometry.centroid
        # Use node_points.reset_index(drop=True) for safe, sequential indices!
        distances = node_points['pt'].distance(b_centroid)
        nearest_idx = distances.idxmin()
        # Use loc, not iloc, for index-safe selection
        if node_id_col in nodes_gdf.columns:
            nearest_node_id = nodes_gdf.loc[nearest_idx, node_id_col]
        else:
            nearest_node_id = nearest_idx
        assignments.append(nearest_node_id)
    buildings_gdf['nearest_node_id'] = assignments
    return buildings_gdf

def build_network(buildings_gdf, streets_gdf, scenario_type='DH', output_path=None, plot_network=False):
    """
    Construct a NetworkX graph for DH or HP scenario.
    """
    G = nx.Graph()

    # Add street nodes and edges
    for idx, row in streets_gdf.iterrows():
        node_id = row['node_id'] if 'node_id' in row else idx
        G.add_node(node_id, geometry=row.geometry, type='street')
    num_nodes = len(G.nodes)
    num_nodes_with_geom = sum(1 for n, d in G.nodes(data=True) if d.get('geometry'))
    print(f"Nodes with geometry: {num_nodes_with_geom} / {num_nodes}")
    # NOTE: Edges creation requires ways/nodes logic from OSM
    # For now, you can connect sequential street nodes as a placeholder
    prev_id = None
    for idx, row in streets_gdf.iterrows():
        node_id = row['node_id'] if 'node_id' in row else idx
        if prev_id is not None:
            G.add_edge(prev_id, node_id, length=row.geometry.length)
        prev_id = node_id

    # Assign each building to its nearest street node/feeder
    buildings_gdf = assign_buildings_to_nearest_street(buildings_gdf, streets_gdf)
    for idx, b in buildings_gdf.iterrows():
        building_id = b['GebaeudeID'] if 'GebaeudeID' in b else idx
        demand = b.get('Heizlast_kW', b.get('demand_kW', 0))
        G.add_node(building_id, geometry=b.geometry, demand=demand, type='building')
        G.add_edge(building_id, b['nearest_street_id'],
                   connection='service_pipe' if scenario_type == 'DH' else 'service_cable')
    missing_from = 0
    missing_to = 0
    for u, v in G.edges():
        if not G.nodes[u].get('geometry'):
            missing_from += 1
        if not G.nodes[v].get('geometry'):
            missing_to += 1
    print(f"Edges missing 'from' geometry: {missing_from}")
    print(f"Edges missing 'to' geometry: {missing_to}")
    # Optionally plot network
    if plot_network:
        plot_network_graph(G)

    # Optionally export network
    if output_path:
        ext = os.path.splitext(output_path)[1].lower()
        if ext == '.graphml':
            nx.write_graphml(G, output_path)
        elif ext == '.gml':
            nx.write_gml(G, output_path)
        elif ext == '.json':
            data = nx.node_link_data(G)
            import json
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        print(f"Network exported to {output_path}")

    return G

import networkx as nx
import os
import pandas as pd

def is_node_id(x):
    """Return True if x looks like a real node ID (int or numeric str)."""
    if isinstance(x, int):
        return True
    if isinstance(x, str):
        # Accepts negative and positive integer strings
        return x.strip("-").isdigit()
    return False

def flatten_node_ids(val):
    """Always returns a list of node IDs (single or list)."""
    if isinstance(val, list):
        return val
    return [val]

def is_valid_node_id(val, valid_node_ids):
    # Accepts int or str-convertible-to-int and exists in nodes_gdf
    try:
        int_val = int(val)
        return int_val in valid_node_ids
    except:
        return False

def build_network_from_edges_nodes(
    buildings_gdf, edges_gdf, nodes_gdf,
    scenario_type='DH',
    output_path=None,
    plot_network=False
):
    """
    Build a NetworkX graph from explicit edges and nodes (e.g., OSM/GeoJSON),
    and assign all buildings to their nearest node.
    """
    G = nx.Graph()

    # --- 1. Add street nodes ---
    node_id_col = 'node_id' if 'node_id' in nodes_gdf.columns else nodes_gdf.columns[0]
    for idx, node in nodes_gdf.iterrows():
        node_id = node[node_id_col]
        geom = node.geometry
        geom_wkt = geom.wkt if geom is not None and hasattr(geom, 'wkt') else None
        G.add_node(node_id, geometry=geom_wkt, type='street_node')

    # --- 2. Add edges between street nodes ---
    from_col = 'from' if 'from' in edges_gdf.columns else edges_gdf.columns[0]
    to_col   = 'to'   if 'to'   in edges_gdf.columns else edges_gdf.columns[1]
    missing_edges = 0
    total_edges = 0

    valid_node_ids = set(nodes_gdf[node_id_col])
    edges_to_use = []
    for idx, edge in edges_gdf.iterrows():
        from_node = edge[from_col]
        to_node = edge[to_col]
        # Only keep edges where both endpoints are valid node IDs
        if is_valid_node_id(from_node, valid_node_ids) and is_valid_node_id(to_node, valid_node_ids):
            edges_to_use.append(edge)
    # Now use only these edges:
    print(f"Filtered down to {len(edges_to_use)} edges with real node IDs.")

    # --- 3. Assign buildings to nearest node ---
    buildings_gdf = assign_buildings_to_nearest_node(buildings_gdf, nodes_gdf, node_id_col=node_id_col)
    for idx, b in buildings_gdf.iterrows():
        building_id = b.get('GebaeudeID') or f'building_{idx}'
        geom = b.geometry
        geom_wkt = geom.wkt if geom is not None and hasattr(geom, 'wkt') else None
        demand = b.get('Heizlast_kW', b.get('demand_kW', 0))
        nearest_node = b.get('nearest_node_id')
        if not (nearest_node and nearest_node in G.nodes and geom_wkt):
            print(f"Skipping building {building_id} due to missing nearest node or geometry.")
            continue
        G.add_node(building_id, geometry=geom_wkt, demand=demand, type='building')
        G.add_edge(building_id, nearest_node,
                   connection='service_pipe' if scenario_type == 'DH' else 'service_cable')

    print(f"Total valid edges added: {total_edges}")
    print(f"Edges skipped due to missing node: {missing_edges}")

    # --- 4. Optional: Plot the network ---
    if plot_network:
        plot_network_graph(G)

    # --- 5. Export network ---
    if output_path:
        ext = os.path.splitext(output_path)[1].lower()
        if ext == '.graphml':
            nx.write_graphml(G, output_path)
        elif ext == '.gml':
            nx.write_gml(G, output_path)
        elif ext == '.json':
            import json
            data = nx.node_link_data(G)
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        print(f"Network exported to {output_path}")

    return G

# Helper function from previous answer (add if not already in your file)
def plot_network_graph(G):
    pos = {}
    node_colors = []
    for n, d in G.nodes(data=True):
        geom = d.get('geometry', None)
        if isinstance(geom, Point):
            pos[n] = (geom.x, geom.y)
        elif geom is not None and hasattr(geom, 'centroid'):
            c = geom.centroid
            pos[n] = (c.x, c.y)
        else:
            pos[n] = (0, 0)
        node_colors.append('red' if d.get('type') == 'building' else 'blue')
    plt.figure(figsize=(8, 8))
    nx.draw(G, pos, node_color=node_colors, with_labels=False, node_size=10, edge_color='gray', alpha=0.7)
    plt.title("Network Graph")
    plt.show()

def validate_network(G):
    """
    Print/log network integrity information.
    """
    building_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'building']
    disconnected = [n for n in building_nodes if G.degree[n] == 0]
    if disconnected:
        print(f"[Warning] {len(disconnected)} buildings are disconnected: {disconnected[:5]}")
    else:
        print("[OK] All buildings are connected to the network.")

    n_components = nx.number_connected_components(G)
    print(f"[Info] Network has {n_components} connected components.")
    if n_components > 1:
        print("[Warning] Network is not fully connected!")
    # Optionally more checks can be added

# Example usage (replace with config-driven main.py call)
if __name__ == "__main__":
    import yaml

    with open("run_all.yaml") as f:
        config = yaml.safe_load(f)
    buildings = gpd.read_file(config["buildings_file"])
    streets = gpd.read_file(config["osm_file"])
    G = build_network(buildings, streets, scenario_type="DH", output_path="results/dh_network.graphml", plot_network=True)
    validate_network(G)
