#!/usr/bin/env python3
"""
Real Interactive DH Network Map with Folium

This script creates an interactive HTML map of a district heating network
using real building data and simulation results.

Usage:
    python create_real_interactive_map.py --street "Bleyerstraße" [--output OUTPUT_FILE]
"""

import argparse
import json
import sys
from pathlib import Path
import geopandas as gpd
import numpy as np
from shapely.geometry import LineString, Point, mapping
from pyproj import Transformer
import networkx as nx
from scipy.spatial import distance_matrix

try:
    import folium

    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Error: folium not available. Install with 'pip install folium'")
    sys.exit(1)


def load_building_data(street_name):
    """
    Load building data for a given street.

    Args:
        street_name: Name of the street

    Returns:
        GeoDataFrame: Building data or None if not found
    """
    clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    buildings_file = Path("street_analysis_outputs") / f"buildings_{clean_name}.geojson"

    if not buildings_file.exists():
        print(f"Buildings file not found: {buildings_file}")
        return None

    try:
        buildings_gdf = gpd.read_file(buildings_file)
        print(f"Loaded {len(buildings_gdf)} buildings for {street_name}")
        return buildings_gdf
    except Exception as e:
        print(f"Error loading buildings: {e}")
        return None


def load_simulation_results(street_name):
    """
    Load simulation results for a given street.

    Args:
        street_name: Name of the street

    Returns:
        dict: Simulation results or None if not found
    """
    clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    results_file = Path("simulation_outputs") / f"street_{clean_name}_results.json"

    if not results_file.exists():
        print(f"Results file not found: {results_file}")
        return None

    try:
        with open(results_file, "r") as f:
            results = json.load(f)

        if not results.get("success", False):
            print(f"Simulation was not successful for {street_name}")
            return None

        print(f"Loaded simulation results for {street_name}")
        return results
    except Exception as e:
        print(f"Error loading results: {e}")
        return None


def create_realistic_network_from_buildings(buildings_gdf, results):
    """
    Create a realistic DH network from building data and simulation results.

    Args:
        buildings_gdf: GeoDataFrame of buildings
        results: Simulation results dictionary

    Returns:
        dict: Network data for visualization
    """
    # Ensure buildings are in a projected CRS
    if buildings_gdf.crs.is_geographic:
        buildings_gdf = buildings_gdf.to_crs(buildings_gdf.estimate_utm_crs())

    # Get building centroids
    centroids = buildings_gdf.geometry.centroid
    coords = np.array([[p.x, p.y] for p in centroids])

    # Create minimum spanning tree for network topology
    n_buildings = len(buildings_gdf)
    D = distance_matrix(coords, coords)

    # Create complete graph
    G = nx.Graph()
    for i in range(n_buildings):
        for j in range(i + 1, n_buildings):
            G.add_edge(i, j, weight=D[i, j])

    # Create minimum spanning tree
    mst = nx.minimum_spanning_tree(G)

    # Find central building (closest to centroid of all buildings)
    centroid = buildings_gdf.geometry.unary_union.centroid
    distances = centroids.distance(centroid)
    central_idx = distances.idxmin()

    # Create network data structure
    network_data = {"junctions": [], "pipes": [], "consumers": [], "plant": None}

    # Add junctions (buildings)
    for i, (idx, building) in enumerate(buildings_gdf.iterrows()):
        centroid = building.geometry.centroid
        junction = {
            "id": i,
            "name": f"building_{i}",
            "x": centroid.x,
            "y": centroid.y,
            "type": "consumer" if i != central_idx else "plant",
        }
        network_data["junctions"].append(junction)

        if i == central_idx:
            network_data["plant"] = junction

    # Add pipes (MST edges)
    pipe_id = 0
    for edge in mst.edges():
        u, v = edge
        u_junc = network_data["junctions"][u]
        v_junc = network_data["junctions"][v]

        # Supply pipe
        supply_pipe = {
            "id": f"SUP_{pipe_id}",
            "from_junction": u,
            "to_junction": v,
            "coords": [(u_junc["x"], u_junc["y"]), (v_junc["x"], v_junc["y"])],
        }
        network_data["pipes"].append(supply_pipe)

        # Return pipe (parallel to supply)
        return_pipe = {
            "id": f"RET_{pipe_id}",
            "from_junction": v,
            "to_junction": u,
            "coords": [(v_junc["x"] + 2, v_junc["y"]), (u_junc["x"] + 2, u_junc["y"])],
        }
        network_data["pipes"].append(return_pipe)

        pipe_id += 1

    # Add consumers (all buildings except plant)
    for i, junction in enumerate(network_data["junctions"]):
        if junction["type"] == "consumer":
            consumer = {
                "id": i,
                "name": f"consumer_{i}",
                "junction_id": i,
                "heat_demand": results.get("kpi", {}).get("heat_mwh", 0.1)
                / len(network_data["junctions"])
                * 1000,  # kW
            }
            network_data["consumers"].append(consumer)

    return network_data


def create_folium_map_from_real_network(network_data, street_name, output_file=None):
    """
    Create Folium map from real network data.

    Args:
        network_data: Network data dictionary
        street_name: Name of the street
        output_file: Output HTML file path (optional)

    Returns:
        str: Path to the created HTML file
    """
    # Find center point (plant location)
    plant = network_data["plant"]
    center_x, center_y = plant["x"], plant["y"]

    # Convert to lat/lon if in projected CRS
    # Assume EPSG:25833 (ETRS89 / UTM zone 33N) for Germany
    transformer = Transformer.from_crs("EPSG:25833", "EPSG:4326", always_xy=True)
    center_lon, center_lat = transformer.transform(center_x, center_y)

    # Create the map centered on the plant
    m = folium.Map(location=[center_lat, center_lon], zoom_start=16, tiles="OpenStreetMap")

    # Add supply pipes
    for pipe in network_data["pipes"]:
        if pipe["id"].startswith("SUP_"):
            coords = pipe["coords"]
            # Convert coordinates to lat/lon
            transformed_coords = [transformer.transform(x, y) for x, y in coords]

            folium.GeoJson(
                mapping(LineString(transformed_coords)),
                style_function=lambda feat: {"color": "red", "weight": 4, "opacity": 0.8},
                tooltip=f"Supply Pipe: {pipe['id']}",
            ).add_to(m)

    # Add return pipes
    for pipe in network_data["pipes"]:
        if pipe["id"].startswith("RET_"):
            coords = pipe["coords"]
            # Convert coordinates to lat/lon
            transformed_coords = [transformer.transform(x, y) for x, y in coords]

            folium.GeoJson(
                mapping(LineString(transformed_coords)),
                style_function=lambda feat: {"color": "blue", "weight": 3, "opacity": 0.6},
                tooltip=f"Return Pipe: {pipe['id']}",
            ).add_to(m)

    # Add junctions
    for junction in network_data["junctions"]:
        x, y = junction["x"], junction["y"]
        # Convert to lat/lon
        lon, lat = transformer.transform(x, y)

        if junction["type"] == "plant":
            # CHP Plant (green square)
            folium.RegularPolygonMarker(
                location=[lat, lon],
                number_of_sides=4,
                radius=8,
                color="green",
                rotation=45,
                fill=True,
                popup="CHP Plant",
                tooltip="CHP Plant",
            ).add_to(m)
        else:
            # Consumer junctions (blue circles)
            folium.CircleMarker(
                location=[lat, lon],
                radius=4,
                color="blue",
                fill=True,
                popup=f"Building: {junction['name']}",
                tooltip=f"Building: {junction['name']}",
            ).add_to(m)

    # Add heat consumers (orange triangles)
    for consumer in network_data["consumers"]:
        junction = network_data["junctions"][consumer["junction_id"]]
        x, y = junction["x"], junction["y"]
        # Convert to lat/lon
        lon, lat = transformer.transform(x, y)

        folium.RegularPolygonMarker(
            location=[lat, lon],
            number_of_sides=3,
            radius=6,
            color="orange",
            fill=True,
            popup=f"Consumer: {consumer['name']}<br>Demand: {consumer['heat_demand']:.1f} kW",
            tooltip=f"Consumer: {consumer['name']}",
        ).add_to(m)

    # Add statistics box
    stats = network_data.get("stats", {})
    stats_html = f"""
    <div style="position: fixed; 
                top: 50px; right: 50px; width: 250px; height: 200px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>DH Network Statistics</b></p>
    <p>Street: {street_name}</p>
    <p>Buildings: {len(network_data['junctions'])}</p>
    <p>Pipes: {len(network_data['pipes'])}</p>
    <p>Total Length: {stats.get('total_length_km', 0):.2f} km</p>
    <p>Network Density: {stats.get('density_km_per_building', 0):.3f} km/building</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(stats_html))

    # Add legend
    legend_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 140px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>DH Network Legend</b></p>
    <p><i class="fa fa-circle" style="color:red"></i> Supply Pipes</p>
    <p><i class="fa fa-circle" style="color:blue"></i> Return Pipes</p>
    <p><i class="fa fa-circle" style="color:orange"></i> Heat Consumers</p>
    <p><i class="fa fa-circle" style="color:green"></i> CHP Plant</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save the map
    if output_file is None:
        clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        output_file = f"simulation_outputs/interactive_real_dh_{clean_name}.html"

    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True)

    m.save(str(output_path))
    print(f"Real interactive map saved to: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Create real interactive DH network map with Folium"
    )
    parser.add_argument(
        "--street", type=str, required=True, help="Street name (e.g., 'Bleyerstraße')"
    )
    parser.add_argument("--output", type=str, help="Output HTML file path (optional)")

    args = parser.parse_args()

    if not FOLIUM_AVAILABLE:
        print("Error: folium not available. Install with 'pip install folium'")
        return

    print(f"Creating real interactive map for {args.street}...")

    # Load building data
    buildings_gdf = load_building_data(args.street)
    if buildings_gdf is None:
        print(f"❌ Could not load building data for {args.street}")
        return

    # Load simulation results
    results = load_simulation_results(args.street)
    if results is None:
        print(f"❌ Could not load simulation results for {args.street}")
        return

    # Create realistic network
    print("Creating realistic network from building data...")
    network_data = create_realistic_network_from_buildings(buildings_gdf, results)

    # Calculate network statistics
    total_length = (
        sum(
            LineString(pipe["coords"]).length
            for pipe in network_data["pipes"]
            if pipe["id"].startswith("SUP_")
        )
        / 1000
    )  # Convert to km

    network_data["stats"] = {
        "total_length_km": total_length,
        "density_km_per_building": total_length / len(network_data["junctions"]),
    }

    # Create interactive map
    output_file = create_folium_map_from_real_network(network_data, args.street, args.output)

    if output_file:
        print(f"\n✅ Real interactive map created successfully!")
        print(f"📁 File: {output_file}")
        print(f"🌐 Open this file in your web browser to view the interactive map")
        print(f"🔍 Features: Pan, zoom, click on elements for details")
        print(
            f"📊 Network: {len(network_data['junctions'])} buildings, {len(network_data['pipes'])} pipes"
        )
    else:
        print("❌ Failed to create real interactive map")


if __name__ == "__main__":
    main()
