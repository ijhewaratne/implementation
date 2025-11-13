# interactive_run_enhanced.py

import json
import os
import subprocess
import sys
import yaml
import questionary
import geopandas as gpd
from pathlib import Path
import shutil
from datetime import datetime

# Add imports for interactive map generation
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
    print("Warning: folium not available. Interactive maps will be skipped.")

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Temperature/pressure plots will be skipped.")


def get_all_street_names(geojson_path):
    """Scans the entire GeoJSON file and returns a sorted list of unique street names."""
    print(f"Reading all street names from {geojson_path}...")
    street_names = set()
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feature in data["features"]:
        for adr in feature.get("adressen", []):
            street_val = adr.get("str")
            if street_val:
                street_names.add(street_val.strip())

    print(f"Found {len(street_names)} unique streets.")
    return sorted(list(street_names))


def get_buildings_for_streets(geojson_path, selected_streets):
    """Gets all building features for a given list of street names."""
    print(f"Fetching buildings for selected streets...")
    street_set = {s.lower() for s in selected_streets}
    selected_features = []

    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feature in data["features"]:
        for adr in feature.get("adressen", []):
            street_val = adr.get("str")
            if street_val and street_val.strip().lower() in street_set:
                selected_features.append(feature)
                break  # Found a matching street, move to the next building feature

    print(f"Found {len(selected_features)} buildings.")
    return selected_features


def create_street_buildings_geojson(buildings_features, street_name, output_dir):
    """Create a GeoJSON file for the selected street buildings."""
    # Clean street name for filename
    clean_street_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")

    # Create GeoJSON structure
    street_geojson = {"type": "FeatureCollection", "features": buildings_features}

    # Save to file
    output_file = os.path.join(output_dir, f"buildings_{clean_street_name}.geojson")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(street_geojson, f, indent=2)

    print(f"Created building file: {output_file}")
    return output_file


def create_street_scenario(street_name, building_file, output_dir, custom_params=None):
    """Create a scenario configuration for the selected street."""
    clean_street_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")

    # Default parameters
    default_params = {"supply_temp": 70, "return_temp": 40, "tech": "biomass", "main_diameter": 0.4}

    # Override with custom parameters if provided
    if custom_params:
        default_params.update(custom_params)

    scenario = {
        "name": f"street_{clean_street_name}",
        "description": f"District Heating simulation for {street_name}",
        "type": "DH",
        "params": default_params,
        "building_file": building_file,
    }

    scenario_file = os.path.join(output_dir, f"scenario_{clean_street_name}.json")
    with open(scenario_file, "w", encoding="utf-8") as f:
        json.dump(scenario, f, indent=2)

    print(f"Created scenario file: {scenario_file}")
    return scenario_file


def run_simulation_for_street(scenario_file, output_dir):
    """Run the simulation for the selected street."""
    print(f"\n{'='*60}")
    print(f"RUNNING SIMULATION FOR STREET")
    print(f"{'='*60}")

    try:
        # Run the simulation
        result = subprocess.run(
            [sys.executable, "src/simulation_runner.py", "--scenarios", scenario_file],
            check=True,
            capture_output=True,
            text=True,
        )

        print("Simulation completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Simulation failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def generate_llm_report_for_street(street_name, output_dir):
    """Generate LLM report for the street simulation results."""
    print(f"\n{'='*60}")
    print(f"GENERATING LLM REPORT FOR {street_name}")
    print(f"{'='*60}")

    clean_street_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    scenario_name = f"street_{clean_street_name}"

    # Find the simulation results
    results_file = os.path.join("simulation_outputs", f"{scenario_name}_results.json")

    if not os.path.exists(results_file):
        print(f"Results file not found: {results_file}")
        return False

    # Read the simulation results
    with open(results_file, "r") as f:
        results = json.load(f)

    if not results.get("success", False):
        print("Simulation was not successful, skipping LLM report")
        return False

    # Create a simple KPI summary for the LLM
    kpi_data = results.get("kpi", {})

    # Create a basic scenario metadata
    scenario_metadata = {
        "street_name": street_name,
        "scenario_type": "District Heating",
        "description": f"DH network simulation for {street_name}",
        "parameters": {"supply_temperature": 70, "return_temperature": 40, "pipe_diameter": 0.4},
    }

    # Create LLM report content
    report_content = f"""# District Heating Network Analysis for {street_name}

## Executive Summary

This report analyzes the feasibility and performance of a district heating (DH) network for {street_name}.

## Simulation Results

### Key Performance Indicators

- **Total Heat Demand**: {kpi_data.get('heat_mwh', 'N/A')} MWh
- **Total Pipe Length**: {kpi_data.get('total_pipe_length_km', 'N/A')} km
- **Number of Buildings**: {kpi_data.get('num_buildings', 'N/A')}
- **Network Density**: {kpi_data.get('network_density_km_per_building', 'N/A')} km per building
- **Hydraulic Success**: {'Yes' if kpi_data.get('hydraulic_success', False) else 'No'}
- **Maximum Pressure Drop**: {kpi_data.get('max_dp_bar', 'N/A')} bar

## Technical Analysis

### Network Characteristics
- The network serves {kpi_data.get('num_buildings', 0)} buildings
- Total network length is {kpi_data.get('total_pipe_length_km', 0)} km
- Average pipe length per building is {kpi_data.get('network_density_km_per_building', 0)} km

### Performance Assessment
- The hydraulic simulation {'converged successfully' if kpi_data.get('hydraulic_success', False) else 'failed to converge'}
- Total heat demand is {kpi_data.get('heat_mwh', 0)} MWh
- {'Pressure drops are within acceptable limits' if kpi_data.get('max_dp_bar', 0) < 1.0 else 'Pressure drops may be high'}

## Recommendations

Based on the simulation results:

1. **Feasibility**: {'The DH network appears technically feasible' if kpi_data.get('hydraulic_success', False) else 'The DH network may face technical challenges'}
2. **Efficiency**: Network density of {kpi_data.get('network_density_km_per_building', 0)} km per building {'is reasonable' if kpi_data.get('network_density_km_per_building', 0) < 0.5 else 'may be high'}
3. **Scale**: With {kpi_data.get('num_buildings', 0)} buildings, this represents a {'small' if kpi_data.get('num_buildings', 0) < 10 else 'medium' if kpi_data.get('num_buildings', 0) < 50 else 'large'} scale DH network

## Next Steps

1. Review the network plot for spatial layout optimization
2. Consider economic feasibility analysis
3. Evaluate environmental impact compared to individual heating systems
4. Assess grid connection requirements and costs

---
*Report generated automatically based on simulation results*
"""

    # Save the report
    report_file = os.path.join(output_dir, f"llm_report_{clean_street_name}.md")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"LLM report saved to: {report_file}")
    return True


def generate_consumer_reports_for_street(street_name, output_dir, custom_params=None):
    """Generate detailed consumer reports for each building in the street."""
    print(f"\n{'='*60}")
    print(f"GENERATING CONSUMER REPORTS FOR {street_name}")
    print(f"{'='*60}")

    clean_street_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")

    # Load building data
    buildings_file = os.path.join(output_dir, f"buildings_{clean_street_name}.geojson")
    if not os.path.exists(buildings_file):
        print(f"Buildings file not found: {buildings_file}")
        return False

    try:
        buildings_gdf = gpd.read_file(buildings_file)
        print(f"Loaded {len(buildings_gdf)} buildings for {street_name}")
    except Exception as e:
        print(f"Error loading buildings: {e}")
        return False

    # Load simulation results
    results_file = os.path.join("simulation_outputs", f"street_{clean_street_name}_results.json")
    if not os.path.exists(results_file):
        print(f"Results file not found: {results_file}")
        return False

    try:
        with open(results_file, "r") as f:
            results = json.load(f)

        if not results.get("success", False):
            print(f"Simulation was not successful for {street_name}")
            return False

        print(f"Loaded simulation results for {street_name}")
    except Exception as e:
        print(f"Error loading results: {e}")
        return False

    # Create realistic network from buildings
    network_data = create_realistic_network_from_buildings(buildings_gdf, results, custom_params)

    # Generate consumer reports
    reports_file = os.path.join(output_dir, f"consumer_reports_{clean_street_name}.html")
    success = create_consumer_reports_html(network_data, buildings_gdf, street_name, reports_file)

    if success:
        print(f"Consumer reports saved to: {reports_file}")
        return True
    else:
        print("Failed to create consumer reports")
        return False


def generate_interactive_map_for_street(street_name, output_dir, custom_params=None):
    """Generate interactive Folium map for the street simulation results."""
    if not FOLIUM_AVAILABLE:
        print("Skipping interactive map generation (folium not available)")
        return False

    print(f"\n{'='*60}")
    print(f"GENERATING INTERACTIVE MAP FOR {street_name}")
    print(f"{'='*60}")

    clean_street_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")

    # Load building data
    buildings_file = os.path.join(output_dir, f"buildings_{clean_street_name}.geojson")
    if not os.path.exists(buildings_file):
        print(f"Buildings file not found: {buildings_file}")
        return False

    try:
        buildings_gdf = gpd.read_file(buildings_file)
        print(f"Loaded {len(buildings_gdf)} buildings for {street_name}")
    except Exception as e:
        print(f"Error loading buildings: {e}")
        return False

    # Load simulation results
    results_file = os.path.join("simulation_outputs", f"street_{clean_street_name}_results.json")
    if not os.path.exists(results_file):
        print(f"Results file not found: {results_file}")
        return False

    try:
        with open(results_file, "r") as f:
            results = json.load(f)

        if not results.get("success", False):
            print(f"Simulation was not successful for {street_name}")
            return False

        print(f"Loaded simulation results for {street_name}")
    except Exception as e:
        print(f"Error loading results: {e}")
        return False

    # Create realistic network from buildings
    network_data = create_realistic_network_from_buildings(buildings_gdf, results, custom_params)

    # Generate interactive map
    map_file = os.path.join(output_dir, f"interactive_map_{clean_street_name}.html")
    success = create_folium_map_from_real_network(network_data, street_name, map_file)

    if success:
        print(f"Interactive map saved to: {map_file}")
        return True
    else:
        print("Failed to create interactive map")
        return False


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

    # Add building junctions (consumers)
    for i, (idx, building) in enumerate(buildings_gdf.iterrows()):
        centroid = building.geometry.centroid
        junction = {
            "id": i + 1,  # Start from 1 since plant is 0
            "name": f"building_{i}",
            "x": centroid.x,
            "y": centroid.y,
            "type": "consumer",
            "temperature": 40.0,  # Return temperature (will be calculated based on distance)
        }
        network_data["junctions"].append(junction)

    # Connect plant to closest building
    closest_building = network_data["junctions"][
        closest_to_plant_idx + 1
    ]  # +1 because plant is at index 0

    # Add pipe from plant to closest building
    plant_pipe = {
        "id": "PLANT_CONNECTION",
        "from_junction": 0,
        "to_junction": closest_to_plant_idx + 1,
        "coords": [(plant_x, plant_y), (closest_building["x"], closest_building["y"])],
    }
    network_data["pipes"].append(plant_pipe)

    # Add MST pipes (connecting buildings)
    pipe_id = 1
    for edge in mst.edges():
        u, v = edge
        u_junc = network_data["junctions"][u + 1]  # +1 because plant is at index 0
        v_junc = network_data["junctions"][v + 1]

        # Supply pipe
        supply_pipe = {
            "id": f"SUP_{pipe_id}",
            "from_junction": u + 1,
            "to_junction": v + 1,
            "coords": [(u_junc["x"], u_junc["y"]), (v_junc["x"], v_junc["y"])],
        }
        network_data["pipes"].append(supply_pipe)

        # Return pipe (parallel to supply)
        return_pipe = {
            "id": f"RET_{pipe_id}",
            "from_junction": v + 1,
            "to_junction": u + 1,
            "coords": [(v_junc["x"] + 2, v_junc["y"]), (u_junc["x"] + 2, u_junc["y"])],
        }
        network_data["pipes"].append(return_pipe)

        pipe_id += 1

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

    # Add consumers (all buildings)
    for i, junction in enumerate(network_data["junctions"]):
        if junction["type"] == "consumer":
            consumer = {
                "id": i,
                "name": f"consumer_{i}",
                "junction_id": i,
                "heat_demand": results.get("kpi", {}).get("heat_mwh", 0.1)
                / len(network_data["junctions"])
                * 1000,  # kW
                "temperature": junction["temperature"],
                "pressure": junction["pressure"],
            }
            network_data["consumers"].append(consumer)

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
        bool: True if successful, False otherwise
    """
    try:
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

                # Get pressure drop for this pipe
                from_junc = network_data["junctions"][pipe["from_junction"]]
                to_junc = network_data["junctions"][pipe["to_junction"]]
                pressure_drop = from_junc.get("pressure", 6.0) - to_junc.get("pressure", 1.0)

                folium.GeoJson(
                    mapping(LineString(transformed_coords)),
                    style_function=lambda feat: {"color": "red", "weight": 4, "opacity": 0.8},
                    tooltip=f"Supply Pipe: {pipe['id']}<br>Pressure Drop: {pressure_drop:.2f} bar",
                ).add_to(m)

        # Add return pipes
        for pipe in network_data["pipes"]:
            if pipe["id"].startswith("RET_"):
                coords = pipe["coords"]
                # Convert coordinates to lat/lon
                transformed_coords = [transformer.transform(x, y) for x, y in coords]

                # Get pressure drop for this pipe
                from_junc = network_data["junctions"][pipe["from_junction"]]
                to_junc = network_data["junctions"][pipe["to_junction"]]
                pressure_drop = from_junc.get("pressure", 1.0) - to_junc.get("pressure", 0.5)

                folium.GeoJson(
                    mapping(LineString(transformed_coords)),
                    style_function=lambda feat: {"color": "blue", "weight": 3, "opacity": 0.6},
                    tooltip=f"Return Pipe: {pipe['id']}<br>Pressure Drop: {pressure_drop:.2f} bar",
                ).add_to(m)

        # Add junctions
        for junction in network_data["junctions"]:
            x, y = junction["x"], junction["y"]
            # Convert to lat/lon
            lon, lat = transformer.transform(x, y)

            if junction["type"] == "plant":
                # CHP Plant (green square)
                temp = junction.get("temperature", 70.0)
                pressure = junction.get("pressure", 6.0)
                folium.RegularPolygonMarker(
                    location=[lat, lon],
                    number_of_sides=4,
                    radius=8,
                    color="green",
                    rotation=45,
                    fill=True,
                    fillColor="green",
                    fillOpacity=0.8,
                    tooltip=f"CHP Plant: {junction['name']}<br>Temperature: {temp:.1f}°C<br>Pressure: {pressure:.1f} bar",
                ).add_to(m)
            else:
                # Consumer buildings (orange circles)
                temp = junction.get("temperature", 40.0)
                pressure = junction.get("pressure", 1.0)
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=6,
                    color="orange",
                    fill=True,
                    fillColor="orange",
                    fillOpacity=0.6,
                    tooltip=f"Consumer: {junction['name']}<br>Temperature: {temp:.1f}°C<br>Pressure: {pressure:.1f} bar",
                ).add_to(m)

        # Add legend
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 250px; height: 160px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p><b>DH Network Legend</b></p>
        <p><i class="fa fa-square" style="color:green"></i> CHP Plant (70°C, 6 bar)</p>
        <p><i class="fa fa-circle" style="color:orange"></i> Consumers (40-70°C, 1-6 bar)</p>
        <p><i class="fa fa-minus" style="color:red"></i> Supply Pipes</p>
        <p><i class="fa fa-minus" style="color:blue"></i> Return Pipes</p>
        <p><i class="fa fa-info-circle"></i> Hover for temp & pressure</p>
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend_html))

        # Add title
        title_html = f"""
        <h3 align="center" style="font-size:16px">
            <b>District Heating Network: {street_name}</b>
        </h3>
        """
        m.get_root().html.add_child(folium.Element(title_html))

        # Save the map
        if output_file is None:
            clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
            output_file = f"interactive_map_{clean_name}.html"

        m.save(output_file)
        return True

    except Exception as e:
        print(f"Error creating interactive map: {e}")
        return False


def create_consumer_reports_html(network_data, buildings_gdf, street_name, output_file=None):
    """
    Create detailed HTML consumer reports for each building.

    Args:
        network_data: Network data dictionary
        buildings_gdf: GeoDataFrame of buildings
        street_name: Name of the street
        output_file: Output HTML file path (optional)

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create HTML content
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Consumer Reports - {street_name}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .summary {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .consumer-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }}
        .consumer-card {{
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #3498db;
        }}
        .consumer-header {{
            background-color: #3498db;
            color: white;
            padding: 10px;
            margin: -20px -20px 15px -20px;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
        }}
        .parameter-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .parameter {{
            background-color: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
            border-left: 3px solid #3498db;
        }}
        .parameter-label {{
            font-weight: bold;
            color: #2c3e50;
            font-size: 0.9em;
        }}
        .parameter-value {{
            color: #34495e;
            font-size: 1.1em;
        }}
        .address-section {{
            background-color: #ecf0f1;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }}
        .address-label {{
            font-weight: bold;
            color: #2c3e50;
        }}
        .address-value {{
            color: #34495e;
        }}
        .thermal-section {{
            background-color: #e8f5e8;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }}
        .hydraulic-section {{
            background-color: #e8f4fd;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }}
        .section-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        .plant-info {{
            background-color: #e8f8f5;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #27ae60;
        }}
        .plant-header {{
            background-color: #27ae60;
            color: white;
            padding: 10px;
            margin: -15px -15px 15px -15px;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>District Heating Network - Consumer Reports</h1>
        <h2>{street_name}</h2>
        <p>Detailed analysis for each consumer building</p>
    </div>
    
    <div class="summary">
        <h3>Network Summary</h3>
        <div class="parameter-grid">
            <div class="parameter">
                <div class="parameter-label">Total Buildings</div>
                <div class="parameter-value">{len(network_data['consumers'])}</div>
            </div>
            <div class="parameter">
                <div class="parameter-label">CHP Plant Location</div>
                <div class="parameter-value">51.76274°N, 14.3453979°E</div>
            </div>
            <div class="parameter">
                <div class="parameter-label">Supply Temperature</div>
                <div class="parameter-value">70°C</div>
            </div>
            <div class="parameter">
                <div class="parameter-label">Supply Pressure</div>
                <div class="parameter-value">6 bar</div>
            </div>
        </div>
    </div>
    
    <div class="plant-info">
        <div class="plant-header">CHP Plant Information</div>
        <div class="parameter-grid">
            <div class="parameter">
                <div class="parameter-label">Plant Name</div>
                <div class="parameter-value">CHP_Plant</div>
            </div>
            <div class="parameter">
                <div class="parameter-label">Supply Temperature</div>
                <div class="parameter-value">70.0°C</div>
            </div>
            <div class="parameter">
                <div class="parameter-label">Supply Pressure</div>
                <div class="parameter-value">6.0 bar</div>
            </div>
            <div class="parameter">
                <div class="parameter-label">Return Temperature</div>
                <div class="parameter-value">40.0°C</div>
            </div>
        </div>
    </div>
    
    <div class="consumer-grid">
"""

        # Add consumer reports
        for i, consumer in enumerate(network_data["consumers"]):
            junction = network_data["junctions"][consumer["junction_id"]]

            # Get building address information
            building_idx = consumer["junction_id"] - 1  # -1 because plant is at index 0
            building_data = buildings_gdf.iloc[building_idx]

            # Extract address information
            address_info = "No address data"
            try:
                # Check if building_data is a Series and has the adressen column
                if hasattr(building_data, "adressen") and building_data.adressen:
                    # Parse JSON string to get address data
                    adr_data = json.loads(building_data.adressen)
                    if isinstance(adr_data, list) and len(adr_data) > 0:
                        adr = adr_data[0]
                        if isinstance(adr, dict):
                            street = adr.get("str", "Unknown Street")
                            house_num = adr.get("hnr", "")
                            postcode = adr.get("postplz", "")
                            city = adr.get("postonm", "")
                            address_info = f"{street} {house_num}, {postcode} {city}"
            except Exception as e:
                address_info = f"Address extraction error: {str(e)}"

            # Extract building profile information
            building_profile = "Residential"
            try:
                if hasattr(building_data, "gebaeude") and building_data.gebaeude:
                    # Parse JSON string to get building data
                    geb_data = json.loads(building_data.gebaeude)
                    if isinstance(geb_data, dict) and "oi" in geb_data:
                        building_profile = f"Building ID: {geb_data['oi']}"
            except Exception as e:
                building_profile = f"Profile extraction error: {str(e)}"

            # Calculate return pressure (simplified model)
            return_pressure = max(junction["pressure"] - 0.5, 0.5)  # 0.5 bar drop for return

            html_content += f"""
        <div class="consumer-card">
            <div class="consumer-header">Consumer {consumer['id']} - Building {building_idx + 1}</div>
            
            <div class="address-section">
                <div class="section-title">📍 Building Address</div>
                <div class="address-value">{address_info}</div>
            </div>
            
            <div class="parameter-grid">
                <div class="parameter">
                    <div class="parameter-label">Building Profile</div>
                    <div class="parameter-value">{building_profile}</div>
                </div>
                <div class="parameter">
                    <div class="parameter-label">Heat Demand</div>
                    <div class="parameter-value">{consumer['heat_demand']:.2f} kW</div>
                </div>
            </div>
            
            <div class="thermal-section">
                <div class="section-title">🌡️ Thermal Parameters</div>
                <div class="parameter-grid">
                    <div class="parameter">
                        <div class="parameter-label">Supply Temperature</div>
                        <div class="parameter-value">{junction['temperature']:.1f}°C</div>
                    </div>
                    <div class="parameter">
                        <div class="parameter-label">Return Temperature</div>
                        <div class="parameter-value">40.0°C</div>
                    </div>
                </div>
            </div>
            
            <div class="hydraulic-section">
                <div class="section-title">⚡ Hydraulic Parameters</div>
                <div class="parameter-grid">
                    <div class="parameter">
                        <div class="parameter-label">Supply Pressure</div>
                        <div class="parameter-value">{junction['pressure']:.1f} bar</div>
                    </div>
                    <div class="parameter">
                        <div class="parameter-label">Return Pressure</div>
                        <div class="parameter-value">{return_pressure:.1f} bar</div>
                    </div>
                </div>
            </div>
        </div>
"""

        html_content += (
            """
    </div>
    
    <div style="text-align: center; margin-top: 30px; color: #7f8c8d;">
        <p>Report generated automatically by Branitz Energy Decision AI System</p>
        <p>Date: """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</p>
    </div>
</body>
</html>
"""
        )

        # Save the HTML file
        if output_file is None:
            clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
            output_file = f"consumer_reports_{clean_name}.html"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return True

    except Exception as e:
        print(f"Error creating consumer reports: {e}")
        return False


def create_temperature_pressure_plots(network_data, street_name, output_dir):
    """Create temperature and pressure distribution plots."""
    if not MATPLOTLIB_AVAILABLE:
        print("Skipping temperature/pressure plots (matplotlib not available)")
        return False

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
    """Enhanced main function with automatic simulation, LLM report, and interactive map generation."""

    # --- Configuration ---
    full_data_geojson = "data/geojson/hausumringe_mit_adressenV3.geojson"
    base_config_path = "run_all_test.yaml"
    dynamic_config_path = "config_interactive_run.yaml"

    # Create output directory for this run
    output_dir = "street_analysis_outputs"
    os.makedirs(output_dir, exist_ok=True)

    # Validate required files exist
    required_files = [
        (full_data_geojson, "Main data file"),
        (base_config_path, "Base configuration file"),
    ]

    for file_path, description in required_files:
        if not os.path.exists(file_path):
            print(f"Error: {description} not found at '{file_path}'")
            print("Please ensure all required files are present in the correct locations.")
            return

    # --- 1. User Street Selection ---
    try:
        all_streets = get_all_street_names(full_data_geojson)
        if not all_streets:
            print("Error: No street names found in the GeoJSON file.")
            return

        selected_streets = questionary.checkbox(
            "Select the streets you want to analyze (use space to select, enter to confirm):",
            choices=all_streets,
        ).ask()

        if not selected_streets:
            print("No streets selected. Exiting.")
            return

    except FileNotFoundError:
        print(f"Error: The main data file was not found at '{full_data_geojson}'")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    # --- 2. Custom Parameters ---
    print(f"\n{'='*60}")
    print("CUSTOM PARAMETERS")
    print(f"{'='*60}")
    print("You can set custom plant temperatures and other parameters.")
    print("Press Enter to use defaults, or enter custom values:")

    custom_params = {}

    # Supply temperature
    try:
        supply_temp_input = input("Supply temperature (°C) [default: 70]: ").strip()
        if supply_temp_input:
            custom_params["supply_temp"] = float(supply_temp_input)
            print(f"Using custom supply temperature: {custom_params['supply_temp']}°C")
        else:
            print("Using default supply temperature: 70°C")
    except ValueError:
        print("Invalid input. Using default supply temperature: 70°C")

    # Return temperature
    try:
        return_temp_input = input("Return temperature (°C) [default: 40]: ").strip()
        if return_temp_input:
            custom_params["return_temp"] = float(return_temp_input)
            print(f"Using custom return temperature: {custom_params['return_temp']}°C")
        else:
            print("Using default return temperature: 40°C")
    except ValueError:
        print("Invalid input. Using default return temperature: 40°C")

    # --- 3. Process Each Selected Street ---
    for street_name in selected_streets:
        print(f"\n{'='*80}")
        print(f"PROCESSING STREET: {street_name}")
        print(f"{'='*80}")

        # Get buildings for this street
        buildings_features = get_buildings_for_streets(full_data_geojson, [street_name])
        if not buildings_features:
            print(f"No buildings found for {street_name}. Skipping...")
            continue

        # Create building GeoJSON for this street
        building_file = create_street_buildings_geojson(buildings_features, street_name, output_dir)

        # Create scenario for this street
        scenario_file = create_street_scenario(
            street_name, building_file, output_dir, custom_params
        )

        # Run simulation for this street
        simulation_success = run_simulation_for_street(scenario_file, output_dir)

        if simulation_success:
            # Generate LLM report for this street
            report_success = generate_llm_report_for_street(street_name, output_dir)

            # Generate interactive map for this street
            map_success = generate_interactive_map_for_street(
                street_name, output_dir, custom_params
            )

            # Generate consumer reports for this street
            reports_success = generate_consumer_reports_for_street(
                street_name, output_dir, custom_params
            )

            # Generate temperature and pressure plots
            plots_success = False
            if custom_params:  # Only generate plots if custom parameters were used
                try:
                    buildings_gdf = gpd.read_file(building_file)
                    clean_street_name = (
                        street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
                    )
                    results_file = os.path.join(
                        "simulation_outputs", f"street_{clean_street_name}_results.json"
                    )
                    if os.path.exists(results_file):
                        with open(results_file, "r") as f:
                            results = json.load(f)
                        network_data = create_realistic_network_from_buildings(
                            buildings_gdf, results, custom_params
                        )
                        plots_success = create_temperature_pressure_plots(
                            network_data, street_name, output_dir
                        )
                except Exception as e:
                    print(f"Error generating temperature/pressure plots: {e}")

            if report_success and map_success and reports_success:
                print(f"✅ Successfully completed analysis for {street_name}")
            elif report_success and map_success:
                print(
                    f"⚠️  Analysis completed but consumer reports generation failed for {street_name}"
                )
            elif report_success and reports_success:
                print(
                    f"⚠️  Analysis completed but interactive map generation failed for {street_name}"
                )
            elif map_success and reports_success:
                print(f"⚠️  Analysis completed but LLM report generation failed for {street_name}")
            else:
                print(f"⚠️  Analysis completed but some report generation failed for {street_name}")
        else:
            print(f"❌ Simulation failed for {street_name}")

    # --- 4. Summary ---
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"Results saved in: {output_dir}")
    print(f"Network plots saved in: simulation_outputs/")
    print(f"LLM reports saved in: {output_dir}/")
    print(f"Interactive maps saved in: {output_dir}/")
    print(f"Consumer reports saved in: {output_dir}/")
    if custom_params:
        print(f"Temperature & pressure plots saved in: {output_dir}/")

    # List generated files
    print(f"\nGenerated files:")
    for street_name in selected_streets:
        clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        print(f"  - {street_name}:")
        print(f"    • Buildings: {output_dir}/buildings_{clean_name}.geojson")
        print(f"    • Scenario: {output_dir}/scenario_{clean_name}.json")
        print(f"    • Results: simulation_outputs/street_{clean_name}_results.json")
        print(f"    • Network Plot: simulation_outputs/dh_street_{clean_name}.png")
        print(f"    • LLM Report: {output_dir}/llm_report_{clean_name}.md")
        print(f"    • Interactive Map: {output_dir}/interactive_map_{clean_name}.html")
        print(f"    • Consumer Reports: {output_dir}/consumer_reports_{clean_name}.html")
        if custom_params:
            print(
                f"    • Temperature & Pressure Plot: {output_dir}/temp_pressure_plot_{clean_name}.png"
            )


if __name__ == "__main__":
    main()
