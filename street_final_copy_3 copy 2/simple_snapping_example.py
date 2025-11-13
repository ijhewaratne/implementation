#!/usr/bin/env python3
"""
Simple Building to Street Snapping Example

This script shows the essential steps for snapping buildings to street segments
to create service connection points for district heating networks.
"""

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString
from shapely.ops import nearest_points
from src import crs_utils
import os


def snap_buildings_to_streets_simple(buildings_gdf, streets_gdf, max_distance=100):
    """
    Simple function to snap buildings to nearest street segments.

    Args:
        buildings_gdf: GeoDataFrame with building geometries
        streets_gdf: GeoDataFrame with street geometries
        max_distance: Maximum distance to consider for snapping (meters)

    Returns:
        DataFrame with connection information
    """
    print(f"Snapping {len(buildings_gdf)} buildings to {len(streets_gdf)} street segments...")

    # Ensure both are in projected CRS for accurate distance calculations
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
            # Create connection record
            connection = {
                "building_id": building_id,
                "building_x": building_geom.centroid.x,
                "building_y": building_geom.centroid.y,
                "street_segment_id": nearest_street_idx,
                "connection_x": nearest_point.x,
                "connection_y": nearest_point.y,
                "distance_meters": min_distance,
                "service_line": LineString([building_geom.centroid, nearest_point]),
            }
            connections.append(connection)
            print(f"  ✅ {building_id}: {min_distance:.1f}m to street {nearest_street_idx}")
        else:
            print(f"  ❌ {building_id}: No street within {max_distance}m")

    print(f"✅ Successfully snapped {len(connections)} buildings")
    return pd.DataFrame(connections)


def snap_plant_to_streets(plant_location, streets_gdf, max_distance=100):
    """
    Snap plant to nearest street segment.

    Args:
        plant_location: Plant location as Point or (x, y) coordinates
        streets_gdf: GeoDataFrame with street geometries
        max_distance: Maximum distance to consider for snapping (meters)

    Returns:
        Dictionary with plant connection information
    """
    print(f"Snapping plant to streets (max distance: {max_distance}m)...")

    # Convert to Point if needed
    if isinstance(plant_location, (tuple, list)):
        plant_point = Point(plant_location[0], plant_location[1])
    else:
        plant_point = plant_location

    # Ensure projected CRS
    streets_proj = crs_utils.ensure_projected_crs(streets_gdf, "EPSG:32633", "Streets")

    min_distance = float("inf")
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
        plant_connection = {
            "building_id": "PLANT",
            "building_x": plant_point.x,
            "building_y": plant_point.y,
            "street_segment_id": nearest_street_idx,
            "connection_x": nearest_point.x,
            "connection_y": nearest_point.y,
            "distance_meters": min_distance,
            "service_line": LineString([plant_point, nearest_point]),
        }

        print(f"✅ Plant snapped to street {nearest_street_idx}: {min_distance:.1f}m")
        return plant_connection
    else:
        print(f"❌ Plant not snapped (no street within {max_distance}m)")
        return None


def plot_snapping_results(
    buildings_gdf,
    streets_gdf,
    connections_df,
    plant_connection=None,
    figsize=(12, 10),
    save_path=None,
):
    """Plot buildings, streets, and service connections."""
    fig, ax = plt.subplots(figsize=figsize)

    # Plot streets
    streets_gdf.plot(ax=ax, color="gray", linewidth=2, alpha=0.7, label="Streets")

    # Plot buildings
    buildings_gdf.plot(ax=ax, color="lightblue", edgecolor="blue", alpha=0.6, label="Buildings")

    # Plot plant if available
    if plant_connection:
        ax.scatter(
            plant_connection["building_x"],
            plant_connection["building_y"],
            color="green",
            s=200,
            marker="s",
            label="Plant",
            zorder=5,
        )

    # Plot service connections
    if not connections_df.empty:
        # Create GeoDataFrame for connections
        connections_gdf = gpd.GeoDataFrame(
            connections_df, geometry="service_line", crs=buildings_gdf.crs
        )
        connections_gdf.plot(
            ax=ax, color="red", linewidth=1.5, alpha=0.8, label="Service Connections"
        )

        # Plot connection points
        connection_points = gpd.GeoDataFrame(
            connections_df,
            geometry=[
                Point(row["connection_x"], row["connection_y"])
                for _, row in connections_df.iterrows()
            ],
            crs=buildings_gdf.crs,
        )
        connection_points.plot(ax=ax, color="red", markersize=50, alpha=0.8, zorder=4)

    ax.set_title(f"Building-Street Service Connections\n{len(connections_df)} connections")
    ax.set_aspect("equal")
    ax.legend()
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"✅ Plot saved to {save_path}")

    return fig, ax


def analyze_connections(connections_df):
    """Analyze service connection statistics."""
    if connections_df.empty:
        print("❌ No connections to analyze.")
        return None

    analysis = {
        "total_connections": len(connections_df),
        "average_distance": connections_df["distance_meters"].mean(),
        "max_distance": connections_df["distance_meters"].max(),
        "min_distance": connections_df["distance_meters"].min(),
        "total_service_length": connections_df["distance_meters"].sum(),
        "buildings_within_50m": len(connections_df[connections_df["distance_meters"] <= 50]),
        "buildings_within_100m": len(connections_df[connections_df["distance_meters"] <= 100]),
    }

    print("\n=== Service Connection Analysis ===")
    for key, value in analysis.items():
        if isinstance(value, float):
            print(f"{key}: {value:.2f}")
        else:
            print(f"{key}: {value}")

    return analysis


def save_connection_data(connections_df, plant_connection=None, output_dir="results_test"):
    """Save connection data to files."""
    import os

    os.makedirs(output_dir, exist_ok=True)

    # Save building connections
    if not connections_df.empty:
        # Save as CSV (without geometry)
        connections_csv = connections_df.drop("service_line", axis=1, errors="ignore")
        connections_csv.to_csv(os.path.join(output_dir, "building_connections.csv"), index=False)

        # Save as GeoJSON (with geometry)
        connections_gdf = gpd.GeoDataFrame(
            connections_df, geometry="service_line", crs="EPSG:32633"
        )
        connections_gdf.to_file(
            os.path.join(output_dir, "building_connections.geojson"), driver="GeoJSON"
        )

        print(f"✅ Building connections saved to {output_dir}")

    # Save plant connection
    if plant_connection:
        plant_df = pd.DataFrame([plant_connection])
        plant_df.to_csv(os.path.join(output_dir, "plant_connection.csv"), index=False)

        plant_gdf = gpd.GeoDataFrame(plant_df, geometry="service_line", crs="EPSG:32633")
        plant_gdf.to_file(os.path.join(output_dir, "plant_connection.geojson"), driver="GeoJSON")

        print(f"✅ Plant connection saved to {output_dir}")


def main():
    """Run the simple snapping example."""
    print("🔗 Simple Building to Street Snapping Example")
    print("=" * 50)

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

    # Snap buildings to streets
    connections_df = snap_buildings_to_streets_simple(buildings_gdf, streets_gdf, max_distance=100)

    # Snap plant to streets (use centroid of buildings as plant location)
    plant_location = buildings_gdf.geometry.unary_union.centroid
    plant_connection = snap_plant_to_streets(plant_location, streets_gdf, max_distance=100)

    # Analyze connections
    analysis = analyze_connections(connections_df)

    # Plot results
    fig, ax = plot_snapping_results(
        buildings_gdf,
        streets_gdf,
        connections_df,
        plant_connection,
        save_path="results_test/simple_snapping_results.png",
    )

    # Save data
    save_connection_data(connections_df, plant_connection)

    print("\n" + "=" * 50)
    print("✅ Example completed!")
    print("=" * 50)
    print("\nKey outputs:")
    print("- building_connections.csv - Connection data for each building")
    print("- building_connections.geojson - Service line geometries")
    print("- plant_connection.csv - Plant connection data")
    print("- simple_snapping_results.png - Visualization")
    print("\nConnection data includes:")
    print("- building_id: Building identifier")
    print("- street_segment_id: Street segment where building connects")
    print("- connection_x/y: Exact point on street for service connection")
    print("- distance_meters: Distance from building to street")
    print("- service_line: Geometry of service connection line")


if __name__ == "__main__":
    main()
