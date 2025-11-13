#!/usr/bin/env python3
"""
Plant and Building Snapping to Street Network

This script demonstrates:
1. Snapping the specific plant location to the nearest street network node
2. Finding the closest point along street segments for each building
3. Identifying the corresponding street segment and nearest network node
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

# Plant coordinates in WGS84
PLANT_LAT, PLANT_LON = 51.76274, 14.3453979


def transform_plant_coordinates():
    """Transform plant coordinates from WGS84 to UTM."""
    # Create transformer from WGS84 to UTM Zone 33N (EPSG:32633)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:32633", always_xy=True)

    # Transform coordinates
    plant_x, plant_y = transformer.transform(PLANT_LON, PLANT_LAT)

    print(f"Plant coordinates:")
    print(f"  WGS84: {PLANT_LAT:.6f}, {PLANT_LON:.6f}")
    print(f"  UTM: {plant_x:.2f}, {plant_y:.2f}")

    return plant_x, plant_y


def snap_plant_to_network_node(plant_x, plant_y, street_network, streets_gdf):
    """
    Snap plant to the nearest node in the street network.

    Args:
        plant_x, plant_y: Plant coordinates in UTM
        street_network: NetworkX graph of street network
        streets_gdf: GeoDataFrame of street segments

    Returns:
        Dictionary with plant connection information
    """
    print(f"\nSnapping plant to nearest network node...")

    plant_point = Point(plant_x, plant_y)

    # Find nearest network node
    nearest_node = None
    min_distance = float("inf")
    nearest_node_coords = None

    for node in street_network.nodes():
        node_coords = street_network.nodes[node]["pos"]
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
        "building_id": "PLANT",
        "plant_x": plant_x,
        "plant_y": plant_y,
        "nearest_node_id": nearest_node,
        "nearest_node_x": nearest_node_coords[0],
        "nearest_node_y": nearest_node_coords[1],
        "street_segment_id": street_segment_id,
        "distance_to_node": min_distance,
        "connection_line": LineString([plant_point, Point(nearest_node_coords)]),
    }

    print(f"✅ Plant snapped to node {nearest_node}")
    print(f"   Node coordinates: {nearest_node_coords[0]:.2f}, {nearest_node_coords[1]:.2f}")
    print(f"   Distance: {min_distance:.2f}m")
    print(f"   Street segment: {street_segment_id}")

    return plant_connection


def snap_buildings_to_street_segments(buildings_gdf, streets_gdf, street_network, max_distance=100):
    """
    Snap buildings to nearest street segments and find corresponding network nodes.

    Args:
        buildings_gdf: GeoDataFrame with building geometries
        streets_gdf: GeoDataFrame with street geometries
        street_network: NetworkX graph of street network
        max_distance: Maximum distance to consider for snapping (meters)

    Returns:
        DataFrame with connection information
    """
    print(f"\nSnapping {len(buildings_gdf)} buildings to street segments...")

    # Ensure projected CRS for accurate distances
    buildings_proj = crs_utils.ensure_projected_crs(buildings_gdf, "EPSG:32633", "Buildings")
    streets_proj = crs_utils.ensure_projected_crs(streets_gdf, "EPSG:32633", "Streets")

    connections = []

    for idx, building in buildings_proj.iterrows():
        building_geom = building.geometry
        building_id = building.get("GebaeudeID", f"building_{idx}")

        # Find nearest street segment
        min_distance = float("inf")
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
            # Find nearest network node to the connection point
            nearest_node = None
            nearest_node_coords = None
            min_node_distance = float("inf")

            for node in street_network.nodes():
                node_coords = street_network.nodes[node]["pos"]
                node_point = Point(node_coords)
                node_distance = nearest_point.distance(node_point)

                if node_distance < min_node_distance:
                    min_node_distance = node_distance
                    nearest_node = node
                    nearest_node_coords = node_coords

            connection = {
                "building_id": building_id,
                "building_x": building_geom.centroid.x,
                "building_y": building_geom.centroid.y,
                "street_segment_id": nearest_street_idx,
                "connection_point_x": nearest_point.x,
                "connection_point_y": nearest_point.y,
                "nearest_node_id": nearest_node,
                "nearest_node_x": nearest_node_coords[0],
                "nearest_node_y": nearest_node_coords[1],
                "distance_to_street": min_distance,
                "distance_to_node": min_node_distance,
                "service_line": LineString([building_geom.centroid, nearest_point]),
                "connection_to_node": LineString([nearest_point, Point(nearest_node_coords)]),
            }
            connections.append(connection)

            print(f"  ✅ {building_id}:")
            print(f"     Street segment: {nearest_street_idx}")
            print(f"     Connection point: {nearest_point.x:.2f}, {nearest_point.y:.2f}")
            print(
                f"     Nearest node: {nearest_node} ({nearest_node_coords[0]:.2f}, {nearest_node_coords[1]:.2f})"
            )
            print(f"     Distance to street: {min_distance:.2f}m")
            print(f"     Distance to node: {min_node_distance:.2f}m")
        else:
            print(f"  ❌ {building_id}: No street within {max_distance}m")

    print(f"✅ Successfully snapped {len(connections)} buildings")
    return pd.DataFrame(connections)


def create_network_with_service_connections(street_network, connections_df, plant_connection):
    """
    Create a new network that includes service connections.

    Args:
        street_network: Original street network
        connections_df: Building connections DataFrame
        plant_connection: Plant connection dictionary

    Returns:
        NetworkX graph with service connections
    """
    print(f"\nCreating network with service connections...")

    # Create a copy of the original network
    network_with_services = street_network.copy()

    # Add plant connection
    if plant_connection:
        network_with_services.add_edge(
            "PLANT",
            plant_connection["nearest_node_id"],
            weight=plant_connection["distance_to_node"],
            edge_type="plant_connection",
            length=plant_connection["distance_to_node"],
        )
        print(f"✅ Added plant connection to node {plant_connection['nearest_node_id']}")

    # Add building service connections
    for _, connection in connections_df.iterrows():
        network_with_services.add_edge(
            connection["building_id"],
            connection["nearest_node_id"],
            weight=connection["distance_to_node"],
            edge_type="service_connection",
            length=connection["distance_to_node"],
        )

    print(f"✅ Added {len(connections_df)} building service connections")
    print(f"✅ Total nodes: {network_with_services.number_of_nodes()}")
    print(f"✅ Total edges: {network_with_services.number_of_edges()}")

    return network_with_services


def plot_connections_with_network(
    buildings_gdf,
    streets_gdf,
    connections_df,
    plant_connection,
    street_network,
    figsize=(15, 12),
    save_path=None,
):
    """Plot buildings, streets, network nodes, and service connections."""
    fig, ax = plt.subplots(figsize=figsize)

    # Plot streets
    streets_gdf.plot(ax=ax, color="gray", linewidth=2, alpha=0.7, label="Streets")

    # Plot network nodes
    node_coords = np.array([street_network.nodes[node]["pos"] for node in street_network.nodes()])
    ax.scatter(
        node_coords[:, 0],
        node_coords[:, 1],
        color="orange",
        s=30,
        alpha=0.8,
        label="Network Nodes",
        zorder=3,
    )

    # Plot buildings
    buildings_gdf.plot(ax=ax, color="lightblue", edgecolor="blue", alpha=0.6, label="Buildings")

    # Plot plant
    if plant_connection:
        ax.scatter(
            plant_connection["plant_x"],
            plant_connection["plant_y"],
            color="green",
            s=200,
            marker="s",
            label="Plant",
            zorder=5,
        )

        # Plot plant connection
        plant_line = plant_connection["connection_line"]
        ax.plot(
            [plant_line.coords[0][0], plant_line.coords[1][0]],
            [plant_line.coords[0][1], plant_line.coords[1][1]],
            "g-",
            linewidth=2,
            alpha=0.8,
            label="Plant Connection",
        )

    # Plot building service connections
    if not connections_df.empty:
        # Plot service lines (building to street)
        for _, connection in connections_df.iterrows():
            service_line = connection["service_line"]
            ax.plot(
                [service_line.coords[0][0], service_line.coords[1][0]],
                [service_line.coords[0][1], service_line.coords[1][1]],
                "r-",
                linewidth=1.5,
                alpha=0.8,
            )

        # Plot connection points on streets
        connection_points = gpd.GeoDataFrame(
            connections_df,
            geometry=[
                Point(row["connection_point_x"], row["connection_point_y"])
                for _, row in connections_df.iterrows()
            ],
            crs=buildings_gdf.crs,
        )
        connection_points.plot(ax=ax, color="red", markersize=50, alpha=0.8, zorder=4)

        # Plot connections to nodes
        for _, connection in connections_df.iterrows():
            node_line = connection["connection_to_node"]
            ax.plot(
                [node_line.coords[0][0], node_line.coords[1][0]],
                [node_line.coords[0][1], node_line.coords[1][1]],
                "b--",
                linewidth=1,
                alpha=0.6,
            )

    ax.set_title(
        f"Plant and Building Connections to Street Network\n"
        f"{len(connections_df)} buildings + 1 plant"
    )
    ax.set_aspect("equal")
    ax.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✅ Plot saved to {save_path}")

    return fig, ax


def save_connection_data(connections_df, plant_connection, output_dir="results_test"):
    """Save connection data to files."""
    os.makedirs(output_dir, exist_ok=True)

    # Save building connections
    if not connections_df.empty:
        # Save as CSV (without geometry columns)
        connections_csv = connections_df.drop(
            ["service_line", "connection_to_node"], axis=1, errors="ignore"
        )
        connections_csv.to_csv(
            os.path.join(output_dir, "building_network_connections.csv"), index=False
        )

        # Save as GeoJSON (with service lines)
        service_lines_gdf = gpd.GeoDataFrame(
            connections_df, geometry="service_line", crs="EPSG:32633"
        )
        service_lines_gdf.to_file(
            os.path.join(output_dir, "building_service_lines.geojson"), driver="GeoJSON"
        )

        print(f"✅ Building connections saved to {output_dir}")

    # Save plant connection
    if plant_connection:
        plant_df = pd.DataFrame([plant_connection])
        plant_df.to_csv(os.path.join(output_dir, "plant_network_connection.csv"), index=False)

        plant_gdf = gpd.GeoDataFrame(plant_df, geometry="connection_line", crs="EPSG:32633")
        plant_gdf.to_file(
            os.path.join(output_dir, "plant_connection_line.geojson"), driver="GeoJSON"
        )

        print(f"✅ Plant connection saved to {output_dir}")


def main():
    """Run the plant and building snapping example."""
    print("🔗 Plant and Building Snapping to Street Network")
    print("=" * 60)

    # Transform plant coordinates
    plant_x, plant_y = transform_plant_coordinates()

    # Load data
    buildings_file = "results_test/buildings_prepared.geojson"
    streets_file = "results_test/streets.geojson"

    if not os.path.exists(buildings_file) or not os.path.exists(streets_file):
        print(f"❌ Required files not found.")
        print("Run the data preparation pipeline first:")
        print("python main.py --config config_interactive_run.yaml")
        return

    buildings_gdf = gpd.read_file(buildings_file)
    streets_gdf = gpd.read_file(streets_file)

    print(f"Loaded {len(buildings_gdf)} buildings and {len(streets_gdf)} street segments")

    # Create street network (using the network builder we created earlier)
    try:
        from street_network_builder import create_network_from_geodataframe

        street_network = create_network_from_geodataframe(streets_gdf, max_edge_length=50)
        print(
            f"✅ Created street network with {street_network.number_of_nodes()} nodes and {street_network.number_of_edges()} edges"
        )
    except ImportError:
        print("❌ Could not import street_network_builder. Using simple network creation...")
        # Simple fallback network creation
        street_network = nx.Graph()
        for idx, street in streets_gdf.iterrows():
            coords = list(street.geometry.coords)
            for i in range(len(coords) - 1):
                node1 = f"node_{idx}_{i}"
                node2 = f"node_{idx}_{i+1}"
                street_network.add_node(node1, pos=coords[i])
                street_network.add_node(node2, pos=coords[i + 1])
                street_network.add_edge(
                    node1, node2, weight=Point(coords[i]).distance(Point(coords[i + 1]))
                )

    # Snap plant to nearest network node
    plant_connection = snap_plant_to_network_node(plant_x, plant_y, street_network, streets_gdf)

    # Snap buildings to street segments and find nearest nodes
    connections_df = snap_buildings_to_street_segments(
        buildings_gdf, streets_gdf, street_network, max_distance=100
    )

    # Create network with service connections
    network_with_services = create_network_with_service_connections(
        street_network, connections_df, plant_connection
    )

    # Plot results
    fig, ax = plot_connections_with_network(
        buildings_gdf,
        streets_gdf,
        connections_df,
        plant_connection,
        street_network,
        save_path="results_test/plant_building_network_connections.png",
    )

    # Save data
    save_connection_data(connections_df, plant_connection)

    print("\n" + "=" * 60)
    print("✅ Example completed!")
    print("=" * 60)
    print("\nKey outputs:")
    print("- building_network_connections.csv - Building connection data with nodes")
    print("- building_service_lines.geojson - Service line geometries")
    print("- plant_network_connection.csv - Plant connection data")
    print("- plant_connection_line.geojson - Plant connection geometry")
    print("- plant_building_network_connections.png - Visualization")
    print("\nConnection data includes:")
    print("- connection_point_x/y: Exact point on street for service connection")
    print("- nearest_node_id: Network node for routing")
    print("- distance_to_street: Distance from building to street")
    print("- distance_to_node: Distance from connection point to network node")


if __name__ == "__main__":
    main()
