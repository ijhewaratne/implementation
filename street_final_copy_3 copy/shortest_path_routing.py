#!/usr/bin/env python3
"""
Shortest Path Routing for District Heating Network

This script demonstrates:
1. Finding shortest paths from plant to building service connections
2. Inserting virtual nodes at service connection points
3. Ensuring routing only along street network (not across open land)
4. Calculating pipe lengths and costs
"""

import geopandas as gpd
import networkx as nx
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from pyproj import Transformer
from src import crs_utils
import os
from collections import defaultdict

# Plant coordinates in WGS84
PLANT_LAT, PLANT_LON = 51.76274, 14.3453979


def transform_plant_coordinates():
    """Transform plant coordinates from WGS84 to UTM."""
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)
    plant_x, plant_y = transformer.transform(PLANT_LON, PLANT_LAT)

    print(f"Plant coordinates:")
    print(f"  WGS84: {PLANT_LAT:.6f}, {PLANT_LON:.6f}")
    print(f"  UTM: {plant_x:.2f}, {plant_y:.2f}")

    return plant_x, plant_y


def create_street_network_with_virtual_nodes(streets_gdf, connections_df, plant_connection):
    """
    Create street network with virtual nodes at service connection points.

    Args:
        streets_gdf: GeoDataFrame of street segments
        connections_df: Building connections DataFrame
        plant_connection: Plant connection dictionary

    Returns:
        NetworkX graph with virtual nodes and routing information
    """
    print("Creating street network with virtual nodes...")

    # Create base network from street segments
    G = nx.Graph()

    # Add street segments as edges
    for idx, street in streets_gdf.iterrows():
        coords = list(street.geometry.coords)
        for i in range(len(coords) - 1):
            node1 = f"street_{idx}_{i}"
            node2 = f"street_{idx}_{i+1}"

            # Add nodes with positions
            G.add_node(node1, pos=coords[i], node_type="street")
            G.add_node(node2, pos=coords[i + 1], node_type="street")

            # Add edge with length as weight
            length = Point(coords[i]).distance(Point(coords[i + 1]))
            G.add_edge(node1, node2, weight=length, edge_type="street", length=length)

    # Connect nearby street nodes to ensure network connectivity
    print("Ensuring network connectivity...")
    street_nodes = [node for node in G.nodes() if G.nodes[node]["node_type"] == "street"]

    for i, node1 in enumerate(street_nodes):
        for j, node2 in enumerate(street_nodes[i + 1 :], i + 1):
            pos1 = G.nodes[node1]["pos"]
            pos2 = G.nodes[node2]["pos"]
            distance = Point(pos1).distance(Point(pos2))

            # Connect nodes that are close but not already connected
            if distance < 5.0 and not G.has_edge(node1, node2):  # 5 meter threshold
                G.add_edge(node1, node2, weight=distance, edge_type="connection", length=distance)

    # Add plant node
    plant_node = "PLANT"
    G.add_node(
        plant_node,
        pos=(plant_connection["plant_x"], plant_connection["plant_y"]),
        node_type="plant",
    )

    # Connect plant to nearest street node
    plant_point = Point(plant_connection["plant_x"], plant_connection["plant_y"])
    nearest_street_node = None
    min_distance = float("inf")

    for node in G.nodes():
        if G.nodes[node]["node_type"] == "street":
            node_pos = G.nodes[node]["pos"]
            node_point = Point(node_pos)
            distance = plant_point.distance(node_point)

            if distance < min_distance:
                min_distance = distance
                nearest_street_node = node

    if nearest_street_node:
        G.add_edge(
            plant_node,
            nearest_street_node,
            weight=min_distance,
            edge_type="plant_connection",
            length=min_distance,
        )
        print(f"✅ Plant connected to street node {nearest_street_node} ({min_distance:.2f}m)")

    # Add virtual nodes at service connection points
    virtual_nodes = {}

    for _, connection in connections_df.iterrows():
        building_id = connection["building_id"]
        connection_point = (connection["connection_point_x"], connection["connection_point_y"])

        # Create virtual node ID
        virtual_node_id = f"virtual_{building_id}"

        # Add virtual node
        G.add_node(
            virtual_node_id,
            pos=connection_point,
            node_type="virtual",
            building_id=building_id,
            connection_point=connection_point,
        )

        # Find nearest street node to connect virtual node
        nearest_street_node = None
        min_distance = float("inf")

        for node in G.nodes():
            if G.nodes[node]["node_type"] == "street":
                node_pos = G.nodes[node]["pos"]
                node_point = Point(node_pos)
                distance = Point(connection_point).distance(node_point)

                if distance < min_distance:
                    min_distance = distance
                    nearest_street_node = node

        if nearest_street_node:
            # Add edge from virtual node to nearest street node
            G.add_edge(
                virtual_node_id,
                nearest_street_node,
                weight=min_distance,
                edge_type="service_connection",
                length=min_distance,
            )

            virtual_nodes[building_id] = {
                "virtual_node_id": virtual_node_id,
                "nearest_street_node": nearest_street_node,
                "distance_to_street": min_distance,
            }

            print(
                f"✅ Virtual node {virtual_node_id} connected to {nearest_street_node} ({min_distance:.2f}m)"
            )

    # Check network connectivity
    connected_components = list(nx.connected_components(G))
    print(f"✅ Network created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    print(f"   - {len([n for n in G.nodes() if G.nodes[n]['node_type'] == 'street'])} street nodes")
    print(
        f"   - {len([n for n in G.nodes() if G.nodes[n]['node_type'] == 'virtual'])} virtual nodes"
    )
    print(f"   - 1 plant node")
    print(f"   - {len(connected_components)} connected components")

    return G, virtual_nodes


def find_shortest_paths_from_plant(G, plant_node="PLANT"):
    """
    Find shortest paths from plant to all virtual nodes (buildings).

    Args:
        G: NetworkX graph with virtual nodes
        plant_node: Plant node identifier

    Returns:
        Dictionary with shortest paths and distances
    """
    print(f"\nFinding shortest paths from plant to all buildings...")

    # Check if plant node exists
    if plant_node not in G.nodes():
        print(f"❌ Plant node {plant_node} not found in network")
        return {}

    # Find all virtual nodes (buildings)
    virtual_nodes = [node for node in G.nodes() if G.nodes[node]["node_type"] == "virtual"]

    print(f"Finding paths to {len(virtual_nodes)} buildings...")

    paths = {}

    for virtual_node in virtual_nodes:
        building_id = G.nodes[virtual_node]["building_id"]

        try:
            # Find shortest path
            path = nx.shortest_path(G, plant_node, virtual_node, weight="weight")
            path_length = nx.shortest_path_length(G, plant_node, virtual_node, weight="weight")

            # Calculate actual pipe length (sum of edge lengths)
            total_pipe_length = 0
            for i in range(len(path) - 1):
                edge_data = G.get_edge_data(path[i], path[i + 1])
                total_pipe_length += edge_data.get("length", 0)

            paths[building_id] = {
                "path": path,
                "path_length": path_length,
                "total_pipe_length": total_pipe_length,
                "virtual_node": virtual_node,
                "num_nodes": len(path),
                "num_edges": len(path) - 1,
            }

            print(f"  ✅ {building_id}: {total_pipe_length:.2f}m via {len(path)} nodes")

        except nx.NetworkXNoPath:
            print(f"  ❌ {building_id}: No path found")
            paths[building_id] = {
                "path": None,
                "path_length": float("inf"),
                "total_pipe_length": float("inf"),
                "virtual_node": virtual_node,
                "num_nodes": 0,
                "num_edges": 0,
            }

    return paths


def analyze_routing_results(paths, connections_df):
    """
    Analyze routing results and calculate network statistics.

    Args:
        paths: Dictionary with shortest paths
        connections_df: Building connections DataFrame

    Returns:
        Dictionary with analysis results
    """
    print(f"\nAnalyzing routing results...")

    # Calculate statistics
    successful_paths = [p for p in paths.values() if p["path"] is not None]
    failed_paths = [p for p in paths.values() if p["path"] is None]

    if successful_paths:
        total_pipe_length = sum(p["total_pipe_length"] for p in successful_paths)
        avg_pipe_length = np.mean([p["total_pipe_length"] for p in successful_paths])
        max_pipe_length = max(p["total_pipe_length"] for p in successful_paths)
        min_pipe_length = min(p["total_pipe_length"] for p in successful_paths)

        # Calculate service connection lengths
        service_lengths = connections_df["distance_to_street"].values
        total_service_length = np.sum(service_lengths)
        avg_service_length = np.mean(service_lengths)

        analysis = {
            "total_buildings": len(paths),
            "successful_connections": len(successful_paths),
            "failed_connections": len(failed_paths),
            "total_main_pipe_length": total_pipe_length,
            "total_service_pipe_length": total_service_length,
            "total_network_length": total_pipe_length + total_service_length,
            "avg_main_pipe_length": avg_pipe_length,
            "avg_service_pipe_length": avg_service_length,
            "max_main_pipe_length": max_pipe_length,
            "min_main_pipe_length": min_pipe_length,
            "success_rate": len(successful_paths) / len(paths) * 100,
        }

        print(f"✅ Routing Analysis:")
        print(f"   - Total buildings: {analysis['total_buildings']}")
        print(f"   - Successful connections: {analysis['successful_connections']}")
        print(f"   - Failed connections: {analysis['failed_connections']}")
        print(f"   - Success rate: {analysis['success_rate']:.1f}%")
        print(f"   - Total main pipe length: {analysis['total_main_pipe_length']:.2f}m")
        print(f"   - Total service pipe length: {analysis['total_service_pipe_length']:.2f}m")
        print(f"   - Total network length: {analysis['total_network_length']:.2f}m")
        print(f"   - Average main pipe length: {analysis['avg_main_pipe_length']:.2f}m")
        print(f"   - Average service pipe length: {analysis['avg_service_pipe_length']:.2f}m")

        return analysis
    else:
        print("❌ No successful paths found")
        return {}


def create_path_geometries(G, paths, connections_df, plant_connection):
    """
    Create GeoDataFrame with path geometries for visualization.

    Args:
        G: NetworkX graph
        paths: Dictionary with shortest paths
        connections_df: Building connections DataFrame
        plant_connection: Plant connection dictionary

    Returns:
        GeoDataFrame with path geometries
    """
    print(f"\nCreating path geometries...")

    path_features = []

    for building_id, path_info in paths.items():
        if path_info["path"] is None:
            continue

        path = path_info["path"]

        # Create path geometry
        path_coords = []
        for node in path:
            node_pos = G.nodes[node]["pos"]
            path_coords.append(node_pos)

        path_geometry = LineString(path_coords)

        # Get building connection info
        building_conn = connections_df[connections_df["building_id"] == building_id].iloc[0]

        path_feature = {
            "building_id": building_id,
            "path_length": path_info["path_length"],
            "total_pipe_length": path_info["total_pipe_length"],
            "num_nodes": path_info["num_nodes"],
            "num_edges": path_info["num_edges"],
            "building_x": building_conn["building_x"],
            "building_y": building_conn["building_y"],
            "connection_point_x": building_conn["connection_point_x"],
            "connection_point_y": building_conn["connection_point_y"],
            "distance_to_street": building_conn["distance_to_street"],
            "geometry": path_geometry,
        }

        path_features.append(path_feature)

    if path_features:
        paths_gdf = gpd.GeoDataFrame(path_features, crs="EPSG:32633")
        print(f"✅ Created {len(paths_gdf)} path geometries")
        return paths_gdf
    else:
        print("❌ No path geometries created")
        return None


def plot_routing_results(
    G, paths, connections_df, plant_connection, paths_gdf=None, figsize=(16, 12), save_path=None
):
    """Plot routing results with paths from plant to buildings."""
    fig, ax = plt.subplots(figsize=figsize)

    # Plot street network edges
    street_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("edge_type") == "street"]
    street_coords = []
    for u, v in street_edges:
        u_pos = G.nodes[u]["pos"]
        v_pos = G.nodes[v]["pos"]
        street_coords.append([u_pos, v_pos])

    for coords in street_coords:
        ax.plot(
            [coords[0][0], coords[1][0]],
            [coords[0][1], coords[1][1]],
            "gray",
            linewidth=1,
            alpha=0.7,
        )

    # Plot street nodes
    street_nodes = [node for node in G.nodes() if G.nodes[node]["node_type"] == "street"]
    street_node_coords = np.array([G.nodes[node]["pos"] for node in street_nodes])
    ax.scatter(
        street_node_coords[:, 0],
        street_node_coords[:, 1],
        color="lightgray",
        s=20,
        alpha=0.6,
        label="Street Nodes",
    )

    # Plot plant
    plant_pos = G.nodes["PLANT"]["pos"]
    ax.scatter(
        plant_pos[0], plant_pos[1], color="green", s=200, marker="s", label="Plant", zorder=5
    )

    # Plot virtual nodes (building connections)
    virtual_nodes = [node for node in G.nodes() if G.nodes[node]["node_type"] == "virtual"]
    virtual_node_coords = np.array([G.nodes[node]["pos"] for node in virtual_nodes])
    ax.scatter(
        virtual_node_coords[:, 0],
        virtual_node_coords[:, 1],
        color="red",
        s=50,
        alpha=0.8,
        label="Service Connections",
        zorder=4,
    )

    # Plot building locations
    building_coords = np.array(
        [[row["building_x"], row["building_y"]] for _, row in connections_df.iterrows()]
    )
    ax.scatter(
        building_coords[:, 0],
        building_coords[:, 1],
        color="blue",
        s=100,
        alpha=0.6,
        label="Buildings",
        zorder=3,
    )

    # Plot service connections (building to virtual node)
    for _, connection in connections_df.iterrows():
        building_point = (connection["building_x"], connection["building_y"])
        connection_point = (connection["connection_point_x"], connection["connection_point_y"])
        ax.plot(
            [building_point[0], connection_point[0]],
            [building_point[1], connection_point[1]],
            "blue",
            linewidth=1,
            alpha=0.6,
            linestyle="--",
        )

    # Plot routing paths
    if paths_gdf is not None:
        paths_gdf.plot(ax=ax, color="red", linewidth=2, alpha=0.8, label="Main Network Paths")

    # Plot individual paths with different colors
    colors = plt.cm.Set3(np.linspace(0, 1, len(paths)))
    for i, (building_id, path_info) in enumerate(paths.items()):
        if path_info["path"] is None:
            continue

        path = path_info["path"]
        path_coords = [G.nodes[node]["pos"] for node in path]

        if len(path_coords) > 1:
            path_x = [coord[0] for coord in path_coords]
            path_y = [coord[1] for coord in path_coords]
            ax.plot(path_x, path_y, color=colors[i], linewidth=1.5, alpha=0.7)

    ax.set_title(
        f"District Heating Network Routing\n" f"Plant to {len(paths)} Buildings via Street Network"
    )
    ax.set_aspect("equal")
    ax.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✅ Plot saved to {save_path}")

    return fig, ax


def save_routing_results(paths, analysis, paths_gdf, output_dir="results_test"):
    """Save routing results to files."""
    os.makedirs(output_dir, exist_ok=True)

    # Save path data
    path_data = []
    for building_id, path_info in paths.items():
        if path_info["path"] is not None:
            path_data.append(
                {
                    "building_id": building_id,
                    "path_length": path_info["path_length"],
                    "total_pipe_length": path_info["total_pipe_length"],
                    "num_nodes": path_info["num_nodes"],
                    "num_edges": path_info["num_edges"],
                    "path_nodes": " -> ".join(path_info["path"]),
                }
            )

    if path_data:
        paths_df = pd.DataFrame(path_data)
        paths_df.to_csv(os.path.join(output_dir, "routing_paths.csv"), index=False)
        print(f"✅ Routing paths saved to {output_dir}/routing_paths.csv")

    # Save analysis
    if analysis:
        analysis_df = pd.DataFrame([analysis])
        analysis_df.to_csv(os.path.join(output_dir, "routing_analysis.csv"), index=False)
        print(f"✅ Routing analysis saved to {output_dir}/routing_analysis.csv")

    # Save path geometries
    if paths_gdf is not None:
        paths_gdf.to_file(os.path.join(output_dir, "routing_paths.geojson"), driver="GeoJSON")
        print(f"✅ Path geometries saved to {output_dir}/routing_paths.geojson")


def main():
    """Run the shortest path routing example."""
    print("🔗 Shortest Path Routing for District Heating Network")
    print("=" * 60)

    # Transform plant coordinates
    plant_x, plant_y = transform_plant_coordinates()

    # Load data
    buildings_file = "results_test/buildings_prepared.geojson"
    streets_file = "results_test/streets.geojson"
    connections_file = "results_test/building_network_connections.csv"

    if not all(os.path.exists(f) for f in [buildings_file, streets_file, connections_file]):
        print(f"❌ Required files not found.")
        print("Run the plant_building_snapping.py first:")
        print("python plant_building_snapping.py")
        return

    buildings_gdf = gpd.read_file(buildings_file)
    streets_gdf = gpd.read_file(streets_file)
    connections_df = pd.read_csv(connections_file)

    print(
        f"Loaded {len(buildings_gdf)} buildings, {len(streets_gdf)} street segments, and {len(connections_df)} connections"
    )

    # Create plant connection
    plant_connection = {"plant_x": plant_x, "plant_y": plant_y, "nearest_node_id": "PLANT"}

    # Create street network with virtual nodes
    G, virtual_nodes = create_street_network_with_virtual_nodes(
        streets_gdf, connections_df, plant_connection
    )

    # Find shortest paths from plant to all buildings
    paths = find_shortest_paths_from_plant(G)

    # Analyze routing results
    analysis = analyze_routing_results(paths, connections_df)

    # Create path geometries
    paths_gdf = create_path_geometries(G, paths, connections_df, plant_connection)

    # Plot results
    fig, ax = plot_routing_results(
        G,
        paths,
        connections_df,
        plant_connection,
        paths_gdf,
        save_path="results_test/shortest_path_routing.png",
    )

    # Save results
    save_routing_results(paths, analysis, paths_gdf)

    print("\n" + "=" * 60)
    print("✅ Routing example completed!")
    print("=" * 60)
    print("\nKey outputs:")
    print("- routing_paths.csv - Path data for each building")
    print("- routing_analysis.csv - Network statistics")
    print("- routing_paths.geojson - Path geometries")
    print("- shortest_path_routing.png - Visualization")
    print("\nNetwork features:")
    print("- Virtual nodes at service connection points")
    print("- Routing only along street network")
    print("- Complete path from plant to each building")
    print("- Pipe length calculations for cost estimation")


if __name__ == "__main__":
    main()
