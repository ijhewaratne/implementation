#!/usr/bin/env python3
"""
Building to Street Network Snapping

This script demonstrates how to snap buildings and plants to the street network
to find the closest points along street segments for service connections.

Features:
- Snap buildings to nearest street segments (not just nodes)
- Find closest point along street geometry
- Record street segment and node information
- Generate service connection data
- Visualize connections
"""

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from scipy.spatial import distance_matrix
from src import crs_utils
import os


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
        self.buildings_gdf = crs_utils.ensure_projected_crs(
            self.buildings_gdf, self.target_crs, "Buildings"
        )

        # Load streets
        self.streets_gdf = gpd.read_file(streets_file)
        self.streets_gdf = crs_utils.ensure_projected_crs(
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
                    "service_line_length": min_distance,  # Distance from building to street
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
            Node ID or coordinates
        """
        # For simplicity, return the point coordinates as node ID
        # In a real implementation, you might want to snap to actual network nodes
        return f"node_{point.x:.0f}_{point.y:.0f}"

    def snap_plant_to_streets(self, max_distance=100):
        """
        Snap plant to nearest street segment.

        Args:
            max_distance: Maximum distance to consider for snapping (meters)

        Returns:
            Dictionary with plant connection information
        """
        print(f"Snapping plant to streets (max distance: {max_distance}m)...")

        min_distance = float("inf")
        nearest_street = None
        nearest_point = None
        street_segment_id = None

        for street_idx, street in self.streets_gdf.iterrows():
            street_geom = street.geometry

            # Find nearest points between plant and street
            plant_point, street_point = nearest_points(self.plant_location, street_geom)
            distance = plant_point.distance(street_point)

            if distance < min_distance and distance <= max_distance:
                min_distance = distance
                nearest_street = street_geom
                nearest_point = street_point
                street_segment_id = street_idx

        if nearest_street is not None:
            nearest_node = self._find_nearest_node_on_street(nearest_point, nearest_street)

            plant_connection = {
                "building_id": "PLANT",
                "building_centroid_x": self.plant_location.x,
                "building_centroid_y": self.plant_location.y,
                "street_segment_id": street_segment_id,
                "connection_point_x": nearest_point.x,
                "connection_point_y": nearest_point.y,
                "nearest_node_id": nearest_node,
                "distance_to_street": min_distance,
                "service_line_length": min_distance,
                "geometry": LineString([self.plant_location, nearest_point]),
            }

            print(f"✅ Plant snapped to street segment {street_segment_id}")
            print(f"   Connection point: {nearest_point.x:.2f}, {nearest_point.y:.2f}")
            print(f"   Distance: {min_distance:.2f}m")

            return plant_connection
        else:
            print("⚠️  Plant not snapped (too far from streets)")
            return None

    def create_service_connections_gdf(self):
        """Create GeoDataFrame with all service connections."""
        if not self.connections:
            print("❌ No connections available. Run snap_buildings_to_streets first.")
            return None

        # Convert connections to GeoDataFrame
        connections_gdf = gpd.GeoDataFrame(
            self.connections, geometry="geometry", crs=self.target_crs
        )

        return connections_gdf

    def analyze_connections(self):
        """Analyze service connection statistics."""
        if not self.connections:
            print("❌ No connections to analyze.")
            return None

        df = pd.DataFrame(self.connections)

        analysis = {
            "total_connections": len(df),
            "average_distance": df["distance_to_street"].mean(),
            "max_distance": df["distance_to_street"].max(),
            "min_distance": df["distance_to_street"].min(),
            "total_service_length": df["service_line_length"].sum(),
            "buildings_within_50m": len(df[df["distance_to_street"] <= 50]),
            "buildings_within_100m": len(df[df["distance_to_street"] <= 100]),
        }

        print("\n=== Service Connection Analysis ===")
        for key, value in analysis.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")

        return analysis

    def plot_connections(self, figsize=(15, 10), save_path=None):
        """Plot buildings, streets, and service connections."""
        fig, ax = plt.subplots(figsize=figsize)

        # Plot streets
        self.streets_gdf.plot(ax=ax, color="gray", linewidth=2, alpha=0.7, label="Streets")

        # Plot buildings
        self.buildings_gdf.plot(
            ax=ax, color="lightblue", edgecolor="blue", alpha=0.6, label="Buildings"
        )

        # Plot plant
        ax.scatter(
            self.plant_location.x,
            self.plant_location.y,
            color="green",
            s=200,
            marker="s",
            label="Plant",
            zorder=5,
        )

        # Plot service connections
        if self.connections:
            connections_gdf = self.create_service_connections_gdf()
            connections_gdf.plot(
                ax=ax, color="red", linewidth=1.5, alpha=0.8, label="Service Connections"
            )

            # Plot connection points
            connection_points = gpd.GeoDataFrame(
                self.connections,
                geometry=[
                    Point(conn["connection_point_x"], conn["connection_point_y"])
                    for conn in self.connections
                ],
                crs=self.target_crs,
            )
            connection_points.plot(ax=ax, color="red", markersize=30, alpha=0.8, zorder=4)

        ax.set_title(f"Building-Street Service Connections\n{len(self.connections)} connections")
        ax.set_aspect("equal")
        ax.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"✅ Plot saved to {save_path}")

        return fig, ax

    def save_connections(self, output_dir="results_test"):
        """Save connection data to files."""
        os.makedirs(output_dir, exist_ok=True)

        if not self.connections:
            print("❌ No connections to save.")
            return

        # Save as CSV
        df = pd.DataFrame(self.connections)
        # Remove geometry column for CSV
        df_csv = df.drop("geometry", axis=1, errors="ignore")
        df_csv.to_csv(os.path.join(output_dir, "service_connections.csv"), index=False)

        # Save as GeoJSON
        connections_gdf = self.create_service_connections_gdf()
        connections_gdf.to_file(
            os.path.join(output_dir, "service_connections.geojson"), driver="GeoJSON"
        )

        # Save connection points
        connection_points = gpd.GeoDataFrame(
            self.connections,
            geometry=[
                Point(conn["connection_point_x"], conn["connection_point_y"])
                for conn in self.connections
            ],
            crs=self.target_crs,
        )
        connection_points.to_file(
            os.path.join(output_dir, "connection_points.geojson"), driver="GeoJSON"
        )

        print(f"✅ Connection data saved to {output_dir}")
        print(f"   - service_connections.csv - Tabular data")
        print(f"   - service_connections.geojson - Connection lines")
        print(f"   - connection_points.geojson - Connection points")


def example_basic_snapping():
    """Basic example of building to street snapping."""
    print("=" * 60)
    print("Example: Basic Building to Street Snapping")
    print("=" * 60)

    # Initialize snapper
    snapper = BuildingStreetSnapper()

    # Load data
    buildings_file = "results_test/buildings_prepared.geojson"
    streets_file = "results_test/streets.geojson"

    if not os.path.exists(buildings_file) or not os.path.exists(streets_file):
        print("❌ Required files not found. Run the data preparation pipeline first.")
        return

    snapper.load_data(buildings_file, streets_file)

    # Snap buildings to streets
    connections_df = snapper.snap_buildings_to_streets(max_distance=100)

    # Snap plant to streets
    plant_connection = snapper.snap_plant_to_streets(max_distance=100)

    # Analyze connections
    analysis = snapper.analyze_connections()

    # Plot results
    fig, ax = snapper.plot_connections(save_path="results_test/building_street_connections.png")

    # Save data
    snapper.save_connections()

    return snapper


def example_granularity_comparison():
    """Compare different street network granularities for snapping."""
    print("\n" + "=" * 60)
    print("Example: Granularity Comparison for Snapping")
    print("=" * 60)

    # Load data
    buildings_file = "results_test/buildings_prepared.geojson"
    streets_file = "results_test/streets.geojson"

    if not os.path.exists(buildings_file) or not os.path.exists(streets_file):
        print("❌ Required files not found.")
        return

    buildings_gdf = gpd.read_file(buildings_file)
    streets_gdf = gpd.read_file(streets_file)

    # Test different street network granularities
    granularities = [
        ("Original", streets_gdf),
        ("High Granularity", streets_gdf),  # In practice, you'd use different networks
    ]

    results = []

    for name, streets in granularities:
        print(f"\nTesting {name}...")

        snapper = BuildingStreetSnapper()
        snapper.buildings_gdf = buildings_gdf
        snapper.streets_gdf = streets
        snapper.plant_location = buildings_gdf.geometry.unary_union.centroid

        connections_df = snapper.snap_buildings_to_streets(max_distance=100)
        analysis = snapper.analyze_connections()

        results.append(
            {
                "granularity": name,
                "num_connections": analysis["total_connections"],
                "avg_distance": analysis["average_distance"],
                "total_service_length": analysis["total_service_length"],
            }
        )

    # Print comparison
    print("\n=== Granularity Comparison ===")
    print(f"{'Granularity':<20} {'Connections':<12} {'Avg Distance':<15} {'Total Length':<15}")
    print("-" * 65)
    for result in results:
        print(
            f"{result['granularity']:<20} "
            f"{result['num_connections']:<12} "
            f"{result['avg_distance']:<15.2f} "
            f"{result['total_service_length']:<15.2f}"
        )


def main():
    """Run all examples."""
    print("🔗 Building to Street Network Snapping Examples")
    print("=" * 60)

    # Check dependencies
    try:
        import geopandas as gpd
        import networkx as nx

        print("✅ Required packages available")
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        return

    # Run examples
    snapper = example_basic_snapping()
    example_granularity_comparison()

    print("\n" + "=" * 60)
    print("🎉 Examples completed!")
    print("=" * 60)
    print("\nKey outputs:")
    print("- service_connections.csv - Connection data for each building")
    print("- service_connections.geojson - Service line geometries")
    print("- connection_points.geojson - Connection points on streets")
    print("- building_street_connections.png - Visualization")
    print("\nNext steps:")
    print("1. Use connection points as service pipe endpoints")
    print("2. Connect to street network nodes for routing")
    print("3. Calculate pipe lengths and costs")


if __name__ == "__main__":
    main()
