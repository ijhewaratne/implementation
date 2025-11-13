#!/usr/bin/env python3
"""
Demo script for testing custom temperature parameters and temperature/pressure plots.
"""

import os
import json
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
from pyproj import Transformer
from shapely.geometry import Point
from scipy.spatial import distance_matrix
import networkx as nx


def create_realistic_network_from_buildings(buildings_gdf, results, custom_params=None):
    """
    Create a realistic DH network from building data and simulation results.

    Args:
        buildings_gdf: GeoDataFrame of buildings
        results: Simulation results dictionary
        custom_params: Custom parameters including supply temperature

    Returns:
        dict: Network data for visualization
    """
    # Get custom parameters or use defaults
    supply_temp = custom_params.get("supply_temp", 70.0) if custom_params else 70.0
    return_temp = custom_params.get("return_temp", 40.0) if custom_params else 40.0

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

    # Use actual CHP plant coordinates instead of central building
    # Plant coordinates in WGS84
    PLANT_LAT, PLANT_LON = 51.76274, 14.3453979

    # Transform plant coordinates to the same CRS as buildings
    transformer = Transformer.from_crs("EPSG:4326", buildings_gdf.crs, always_xy=True)
    plant_x, plant_y = transformer.transform(PLANT_LON, PLANT_LAT)

    # Find closest building to plant for connection
    plant_point = Point(plant_x, plant_y)
    distances_to_plant = centroids.distance(plant_point)
    closest_to_plant_idx = distances_to_plant.idxmin()

    # Create network data structure
    network_data = {"junctions": [], "pipes": [], "consumers": [], "plant": None}

    # Add CHP plant as first junction
    plant_junction = {
        "id": 0,
        "name": "CHP_Plant",
        "x": plant_x,
        "y": plant_y,
        "type": "plant",
        "temperature": supply_temp,  # Use custom supply temperature
        "return_temp": return_temp,  # Store return temperature for plots
    }
    network_data["junctions"].append(plant_junction)
    network_data["plant"] = plant_junction

    # Add consumer junctions
    for i, (idx, row) in enumerate(buildings_gdf.iterrows(), 1):
        centroid = centroids.iloc[idx]
        consumer_junction = {
            "id": i,
            "name": f"Building_{i}",
            "x": centroid.x,
            "y": centroid.y,
            "type": "consumer",
        }
        network_data["junctions"].append(consumer_junction)

        # Add consumer data
        consumer = {
            "id": i,
            "junction_id": i,
            "building_id": idx,
            "heat_demand": results.get("total_heat_demand", 1000)
            / len(buildings_gdf),  # Distribute demand
        }
        network_data["consumers"].append(consumer)

    # Add pipes based on MST
    pipe_id = 1
    for edge in mst.edges():
        # Supply pipe
        supply_pipe = {
            "id": pipe_id,
            "from_junction": edge[0] + 1,  # +1 because plant is junction 0
            "to_junction": edge[1] + 1,
            "type": "supply",
            "diameter": 0.4,
        }
        network_data["pipes"].append(supply_pipe)
        pipe_id += 1

        # Return pipe
        return_pipe = {
            "id": pipe_id,
            "from_junction": edge[1] + 1,
            "to_junction": edge[0] + 1,
            "type": "return",
            "diameter": 0.4,
        }
        network_data["pipes"].append(return_pipe)
        pipe_id += 1

    # Add connection from plant to closest building
    plant_supply_pipe = {
        "id": pipe_id,
        "from_junction": 0,  # Plant
        "to_junction": closest_to_plant_idx + 1,
        "type": "supply",
        "diameter": 0.6,
    }
    network_data["pipes"].append(plant_supply_pipe)
    pipe_id += 1

    plant_return_pipe = {
        "id": pipe_id,
        "from_junction": closest_to_plant_idx + 1,
        "to_junction": 0,  # Plant
        "type": "return",
        "diameter": 0.6,
    }
    network_data["pipes"].append(plant_return_pipe)

    # Calculate temperatures and pressures based on distance from plant
    # Simple temperature drop model: 1°C per 100m
    # Simple pressure drop model: 0.1 bar per 100m
    for junction in network_data["junctions"]:
        if junction["type"] == "consumer":
            # Calculate distance from plant
            distance = np.sqrt((junction["x"] - plant_x) ** 2 + (junction["y"] - plant_y) ** 2)

            # Temperature drop: 1°C per 100m, minimum return temperature
            max_temp_drop = supply_temp - return_temp
            temp_drop = min(distance / 100.0, max_temp_drop)  # Max drop to return temperature
            junction["temperature"] = max(supply_temp - temp_drop, return_temp)

            # Pressure drop: 0.1 bar per 100m, starting from 6 bar at plant
            pressure_drop = min(distance / 100.0 * 0.1, 5.0)  # Max 5 bar drop
            junction["pressure"] = max(6.0 - pressure_drop, 1.0)  # Minimum 1 bar
        else:
            # Plant has supply temperature and pressure
            junction["temperature"] = supply_temp
            junction["pressure"] = 6.0

    return network_data


def create_temperature_pressure_plots(network_data, street_name, output_dir):
    """Create temperature and pressure distribution plots."""
    print(f"\n{'='*60}")
    print(f"GENERATING TEMPERATURE & PRESSURE PLOTS FOR {street_name}")
    print(f"{'='*60}")

    try:
        # Extract data for plotting
        consumers = network_data["consumers"]
        plant = network_data["plant"]

        # Prepare data
        distances = []
        temperatures = []
        pressures = []

        for consumer in consumers:
            junction = network_data["junctions"][consumer["junction_id"]]
            # Calculate distance from plant
            distance = np.sqrt(
                (junction["x"] - plant["x"]) ** 2 + (junction["y"] - plant["y"]) ** 2
            )
            distances.append(distance)
            temperatures.append(junction["temperature"])
            pressures.append(junction["pressure"])

        # Create figure with subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Temperature plot
        ax1.scatter(distances, temperatures, c="red", s=50, alpha=0.7, label="Consumer Buildings")
        ax1.axhline(
            y=plant["temperature"],
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"Plant Supply ({plant['temperature']}°C)",
        )
        # Use return temperature from plant data or default to 40°C
        return_temp = plant.get("return_temp", 40.0)
        ax1.axhline(
            y=return_temp,
            color="blue",
            linestyle="--",
            linewidth=2,
            label=f"Return Temperature ({return_temp}°C)",
        )
        ax1.set_xlabel("Distance from Plant (m)")
        ax1.set_ylabel("Temperature (°C)")
        ax1.set_title(f"Temperature Distribution - {street_name}")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Pressure plot
        ax2.scatter(distances, pressures, c="orange", s=50, alpha=0.7, label="Consumer Buildings")
        ax2.axhline(
            y=plant["pressure"],
            color="green",
            linestyle="--",
            linewidth=2,
            label=f"Plant Supply ({plant['pressure']} bar)",
        )
        ax2.axhline(
            y=1.0, color="red", linestyle="--", linewidth=2, label="Minimum Pressure (1 bar)"
        )
        ax2.set_xlabel("Distance from Plant (m)")
        ax2.set_ylabel("Pressure (bar)")
        ax2.set_title(f"Pressure Distribution - {street_name}")
        ax2.legend()
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        plot_file = os.path.join(output_dir, f"temp_pressure_plot_{clean_name}.png")
        plt.savefig(plot_file, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"Temperature & pressure plot saved to: {plot_file}")
        return True

    except Exception as e:
        print(f"Error creating temperature/pressure plots: {e}")
        return False


def main():
    """Demo function to test custom temperature parameters."""
    print("=" * 80)
    print("CUSTOM TEMPERATURE DEMO")
    print("=" * 80)

    # Test different temperature scenarios
    scenarios = [
        {"name": "Standard DH", "supply_temp": 70, "return_temp": 40},
        {"name": "Low Temperature DH", "supply_temp": 55, "return_temp": 25},
        {"name": "High Temperature DH", "supply_temp": 90, "return_temp": 50},
        {"name": "Ultra Low Temperature", "supply_temp": 45, "return_temp": 20},
    ]

    # Load sample building data
    buildings_file = "street_analysis_outputs/buildings_Bleyerstraße.geojson"
    if not os.path.exists(buildings_file):
        print(f"Buildings file not found: {buildings_file}")
        print("Please run the interactive script first to generate building data.")
        return

    try:
        buildings_gdf = gpd.read_file(buildings_file)
        print(f"Loaded {len(buildings_gdf)} buildings for testing")
    except Exception as e:
        print(f"Error loading buildings: {e}")
        return

    # Create sample results
    results = {"success": True, "total_heat_demand": 5000, "total_power_demand": 2000}

    # Create output directory
    output_dir = "demo_outputs"
    os.makedirs(output_dir, exist_ok=True)

    # Test each scenario
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"TESTING SCENARIO: {scenario['name']}")
        print(f"Supply Temperature: {scenario['supply_temp']}°C")
        print(f"Return Temperature: {scenario['return_temp']}°C")
        print(f"{'='*60}")

        # Create network with custom parameters
        network_data = create_realistic_network_from_buildings(
            buildings_gdf, results, custom_params=scenario
        )

        # Generate temperature and pressure plots
        plot_success = create_temperature_pressure_plots(
            network_data, f"Bleyerstraße_{scenario['name'].replace(' ', '_')}", output_dir
        )

        if plot_success:
            print(f"✅ Successfully generated plots for {scenario['name']}")
        else:
            print(f"❌ Failed to generate plots for {scenario['name']}")

        # Print some statistics
        temperatures = [
            j["temperature"] for j in network_data["junctions"] if j["type"] == "consumer"
        ]
        pressures = [j["pressure"] for j in network_data["junctions"] if j["type"] == "consumer"]

        print(f"Temperature range: {min(temperatures):.1f}°C - {max(temperatures):.1f}°C")
        print(f"Pressure range: {min(pressures):.1f} bar - {max(pressures):.1f} bar")

    print(f"\n{'='*80}")
    print("DEMO COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved in: {output_dir}")
    print("Generated temperature and pressure plots for different scenarios:")
    for scenario in scenarios:
        clean_name = (
            f"Bleyerstraße_{scenario['name'].replace(' ', '_')}".replace(" ", "_")
            .replace("/", "_")
            .replace("\\", "_")
        )
        print(f"  • {scenario['name']}: {output_dir}/temp_pressure_plot_{clean_name}.png")


if __name__ == "__main__":
    main()
