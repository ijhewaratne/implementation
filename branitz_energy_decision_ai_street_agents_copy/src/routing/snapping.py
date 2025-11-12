#!/usr/bin/env python3
"""
Building to Street Network Snapping

Migrated from street_final_copy_3/01_building_street_snapping.py and 03_plant_building_snapping.py

This module provides functionality to snap buildings and plants to the street network
to find the closest points along street segments for service connections.

Features:
- Snap buildings to nearest street segments (not just nodes)
- Find closest point along street geometry
- Record street segment and node information
- Generate service connection data
- Visualize connections
- Snap plant to network nodes
"""

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from scipy.spatial import distance_matrix
import os


def ensure_projected_crs(gdf, target_crs, layer_name="Layer"):
    """
    Ensure GeoDataFrame is in projected CRS.
    
    Helper function for CRS management.
    """
    if gdf.crs is None:
        print(f"Warning: {layer_name} has no CRS. Assuming {target_crs}")
        gdf = gdf.set_crs(target_crs)
    elif gdf.crs != target_crs:
        print(f"Reprojecting {layer_name} from {gdf.crs} to {target_crs}")
        gdf = gdf.to_crs(target_crs)
    return gdf


class BuildingStreetSnapper:
    """Snap buildings and plants to street network for service connections."""

    def __init__(self, target_crs="EPSG:32633"):
        """
        Initialize the snapper.

        Args:
            target_crs: Target coordinate reference system
        """
        self.target_crs = target_crs
        self.street_network = None
        self.streets_gdf = None
        self.buildings_gdf = None
        self.plant_location = None
        self.connections = []

    def load_data(self, buildings_file, streets_file, plant_location=None):
        """
        Load buildings and streets data.

        Args:
            buildings_file: Path to buildings GeoJSON
            streets_file: Path to streets GeoJSON
            plant_location: Optional plant location (x, y) coordinates
        """
        print("Loading data...")

        # Load buildings
        self.buildings_gdf = gpd.read_file(buildings_file)
        self.buildings_gdf = ensure_projected_crs(
            self.buildings_gdf, self.target_crs, "Buildings"
        )

        # Load streets
        self.streets_gdf = gpd.read_file(streets_file)
        self.streets_gdf = ensure_projected_crs(
            self.streets_gdf, self.target_crs, "Streets"
        )

        # Set plant location
        if plant_location:
            self.plant_location = Point(plant_location)
        else:
            # Use centroid of buildings as default plant location
            centroid = self.buildings_gdf.geometry.unary_union.centroid
            self.plant_location = centroid

        print(
            f"✅ Loaded {len(self.buildings_gdf)} buildings and {len(self.streets_gdf)} street segments"
        )
        print(f"Plant location: {self.plant_location.x:.2f}, {self.plant_location.y:.2f}")

    def snap_buildings_to_streets(self, max_distance=100):
        """
        Snap buildings to nearest street segments.

        Args:
            max_distance: Maximum distance to consider for snapping (meters)

        Returns:
            DataFrame with connection information
        """
        print(f"Snapping buildings to streets (max distance: {max_distance}m)...")

        connections = []

        for idx, building in self.buildings_gdf.iterrows():
            building_geom = building.geometry
            building_id = building.get("GebaeudeID", f"building_{idx}")

            # Find nearest street segment
            min_distance = float("inf")
            nearest_street = None
            nearest_point = None
            street_segment_id = None

            for street_idx, street in self.streets_gdf.iterrows():
                street_geom = street.geometry

                # Find nearest points between building and street
                building_point, street_point = nearest_points(building_geom, street_geom)
                distance = building_point.distance(street_point)

                if distance < min_distance and distance <= max_distance:
                    min_distance = distance
                    nearest_street = street_geom
                    nearest_point = street_point
                    street_segment_id = street_idx

            if nearest_street is not None:
                # Find the nearest node on the street network
                nearest_node = self._find_nearest_node_on_street(nearest_point, nearest_street)

                connection = {
                    "building_id": building_id,
                    "building_centroid_x": building_geom.centroid.x,
                    "building_centroid_y": building_geom.centroid.y,
                    "street_segment_id": street_segment_id,
                    "connection_point_x": nearest_point.x,
                    "connection_point_y": nearest_point.y,
                    "nearest_node_id": nearest_node,
                    "distance_to_street": min_distance,
                    "service_line_length": min_distance,
                    "geometry": LineString([building_geom.centroid, nearest_point]),
                }
                connections.append(connection)
            else:
                print(f"⚠️  Building {building_id} not snapped (too far from streets)")

        self.connections = connections
        print(f"✅ Snapped {len(connections)} buildings to streets")
        return pd.DataFrame(connections)

    def _find_nearest_node_on_street(self, point, street_geom):
        """
        Find the nearest node on a street segment.

        Args:
            point: Point on the street
            street_geom: Street geometry

        Returns:
            Node ID or None
        """
        if self.street_network is None:
            return None

        # Find nearest node to the point
        min_distance = float("inf")
        nearest_node = None

        for node in self.street_network.nodes():
            node_coords = self.street_network.nodes[node]["pos"]
            node_point = Point(node_coords)
            distance = point.distance(node_point)

            if distance < min_distance:
                min_distance = distance
                nearest_node = node

        return nearest_node

    def create_street_network(self):
        """Create NetworkX graph from street segments."""
        print("\nCreating street network graph...")

        G = nx.Graph()

        for idx, street in self.streets_gdf.iterrows():
            coords = list(street.geometry.coords)
            for i in range(len(coords) - 1):
                node1 = f"street_{idx}_{i}"
                node2 = f"street_{idx}_{i+1}"

                # Add nodes
                G.add_node(node1, pos=coords[i], node_type="street")
                G.add_node(node2, pos=coords[i + 1], node_type="street")

                # Add edge
                length = Point(coords[i]).distance(Point(coords[i + 1]))
                G.add_edge(node1, node2, weight=length, length=length)

        self.street_network = G
        print(f"✅ Created street network with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
        return G

    def snap_plant_to_network(self):
        """
        Snap plant to nearest network node.

        Returns:
            Dictionary with plant connection information
        """
        if self.street_network is None:
            self.create_street_network()

        print(f"\nSnapping plant to nearest network node...")

        plant_point = self.plant_location

        # Find nearest network node
        nearest_node = None
        min_distance = float("inf")
        nearest_node_coords = None

        for node in self.street_network.nodes():
            node_coords = self.street_network.nodes[node]["pos"]
            node_point = Point(node_coords)
            distance = plant_point.distance(node_point)

            if distance < min_distance:
                min_distance = distance
                nearest_node = node
                nearest_node_coords = node_coords

        # Find which street segment contains this node
        street_segment_id = None
        for idx, street in self.streets_gdf.iterrows():
            street_geom = street.geometry
            if street_geom.distance(Point(nearest_node_coords)) < 1.0:  # Within 1 meter
                street_segment_id = idx
                break

        plant_connection = {
            "building_id": "PLANT",
            "plant_x": plant_point.x,
            "plant_y": plant_point.y,
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

    def save_connections(self, output_dir="results_test"):
        """Save connection data to files."""
        os.makedirs(output_dir, exist_ok=True)

        if self.connections:
            # Save as DataFrame
            connections_df = pd.DataFrame(self.connections)
            
            # Save connection data
            connections_df.to_csv(
                os.path.join(output_dir, "building_network_connections.csv"), index=False
            )

            # Save as GeoDataFrame with geometries
            connections_gdf = gpd.GeoDataFrame(
                connections_df, 
                geometry="geometry", 
                crs=self.target_crs
            )
            connections_gdf.to_file(
                os.path.join(output_dir, "building_network_connections.geojson"), driver="GeoJSON"
            )

            print(f"✅ Connections saved to {output_dir}/building_network_connections.*")

    def plot_connections(self, figsize=(14, 14), save_path=None):
        """Plot building-to-street connections."""
        fig, ax = plt.subplots(figsize=figsize)

        # Plot streets
        self.streets_gdf.plot(ax=ax, color="black", linewidth=2, alpha=0.7, label="Streets")

        # Plot buildings
        self.buildings_gdf.plot(
            ax=ax, color="lightblue", edgecolor="black", alpha=0.6, label="Buildings"
        )

        # Plot connections
        if self.connections:
            connections_gdf = gpd.GeoDataFrame(
                self.connections, 
                geometry="geometry", 
                crs=self.target_crs
            )
            connections_gdf.plot(
                ax=ax, color="red", linewidth=1.5, alpha=0.8, label="Service Connections"
            )

            # Plot connection points
            connection_points = [Point(c["connection_point_x"], c["connection_point_y"]) for c in self.connections]
            connection_gdf = gpd.GeoDataFrame(
                geometry=connection_points, 
                crs=self.target_crs
            )
            connection_gdf.plot(ax=ax, color="red", markersize=30, alpha=0.8)

        # Plot plant
        if self.plant_location:
            ax.scatter(
                self.plant_location.x,
                self.plant_location.y,
                color="green",
                s=200,
                marker="s",
                label="Plant",
                zorder=5,
            )

        ax.set_title(f"Building to Street Snapping\n{len(self.connections)} Connections")
        ax.set_aspect("equal")
        ax.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Plot saved to {save_path}")

        return fig, ax


# Standalone functions for direct use

def snap_buildings_to_street_segments(buildings_gdf, streets_gdf, street_network, max_distance=100):
    """
    Snap buildings to nearest street segments and find corresponding network nodes.
    
    Standalone function migrated from 03_plant_building_snapping.py

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
    buildings_proj = ensure_projected_crs(buildings_gdf, "EPSG:32633", "Buildings")
    streets_proj = ensure_projected_crs(streets_gdf, "EPSG:32633", "Streets")

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
                "nearest_node_x": nearest_node_coords[0] if nearest_node_coords else None,
                "nearest_node_y": nearest_node_coords[1] if nearest_node_coords else None,
                "distance_to_street": min_distance,
                "distance_to_node": min_node_distance,
                "service_line_length": min_distance,
            }
            connections.append(connection)
        else:
            print(f"⚠️  Building {building_id} not snapped (too far from streets)")

    print(f"✅ Snapped {len(connections)} buildings to streets")
    return pd.DataFrame(connections)


def snap_plant_to_network_node(plant_x, plant_y, street_network, streets_gdf):
    """
    Snap plant to the nearest node in the street network.
    
    Migrated from 03_plant_building_snapping.py

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


def save_snapping_results(connections_df, plant_connection, output_dir="results_test"):
    """
    Save snapping results to files.
    
    Args:
        connections_df: DataFrame with building connections
        plant_connection: Dictionary with plant connection info
        output_dir: Output directory
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save building connections
    connections_df.to_csv(
        os.path.join(output_dir, "building_network_connections.csv"), index=False
    )
    print(f"✅ Building connections saved to {output_dir}/building_network_connections.csv")

    # Save plant connection
    plant_df = pd.DataFrame([plant_connection])
    plant_df.to_csv(os.path.join(output_dir, "plant_network_connection.csv"), index=False)
    print(f"✅ Plant connection saved to {output_dir}/plant_network_connection.csv")


def visualize_snapping_results(buildings_gdf, streets_gdf, connections_df, 
                               plant_connection=None, figsize=(14, 14), save_path=None):
    """
    Visualize snapping results.
    
    Args:
        buildings_gdf: Buildings GeoDataFrame
        streets_gdf: Streets GeoDataFrame
        connections_df: Connections DataFrame
        plant_connection: Optional plant connection dict
        figsize: Figure size
        save_path: Path to save plot
        
    Returns:
        fig, ax
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Plot streets
    streets_gdf.plot(ax=ax, color="black", linewidth=2, alpha=0.7, label="Streets")

    # Plot buildings
    buildings_gdf.plot(
        ax=ax, color="lightblue", edgecolor="black", alpha=0.6, label="Buildings"
    )

    # Plot connections
    for _, conn in connections_df.iterrows():
        building_point = Point(conn["building_x"], conn["building_y"])
        connection_point = Point(conn["connection_point_x"], conn["connection_point_y"])
        line = LineString([building_point, connection_point])
        
        ax.plot(*line.xy, color="red", linewidth=1.5, alpha=0.8)

    # Plot connection points
    connection_points = [Point(row["connection_point_x"], row["connection_point_y"]) for _, row in connections_df.iterrows()]
    if connection_points:
        for point in connection_points:
            ax.scatter(point.x, point.y, color="red", s=30, alpha=0.8, zorder=4)

    # Plot plant if provided
    if plant_connection:
        plant_x = plant_connection["plant_x"]
        plant_y = plant_connection["plant_y"]
        ax.scatter(plant_x, plant_y, color="green", s=200, marker="s", label="Plant", zorder=5)
        
        # Plot plant connection
        if "nearest_node_x" in plant_connection:
            node_point = Point(plant_connection["nearest_node_x"], plant_connection["nearest_node_y"])
            plant_point = Point(plant_x, plant_y)
            line = LineString([plant_point, node_point])
            ax.plot(*line.xy, color="green", linewidth=2, alpha=0.8, linestyle="--")

    ax.set_title(f"Building and Plant Snapping to Street Network\n{len(connections_df)} Connections")
    ax.set_aspect("equal")
    ax.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✅ Plot saved to {save_path}")

    return fig, ax

