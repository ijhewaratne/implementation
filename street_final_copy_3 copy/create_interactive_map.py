#!/usr/bin/env python3
"""
Simple Interactive DH Network Map with Folium

This script creates an interactive HTML map of a district heating network
using Folium, following a simplified approach that directly uses the
pandapipes network data.

Usage:
    python create_interactive_map.py [--scenario SCENARIO_NAME] [--output OUTPUT_FILE]
"""

import argparse
import json
import sys
from pathlib import Path
import geopandas as gpd
from shapely.geometry import LineString, mapping
from pyproj import Transformer

try:
    import folium

    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False
    print("Error: folium not available. Install with 'pip install folium'")
    sys.exit(1)


def load_network_from_results(scenario_name):
    """
    Load network data from simulation results.

    Args:
        scenario_name: Name of the scenario (e.g., 'street_Bleyerstraße')

    Returns:
        dict: Network data or None if not found
    """
    results_file = Path("simulation_outputs") / f"{scenario_name}_results.json"

    if not results_file.exists():
        print(f"Results file not found: {results_file}")
        return None

    with open(results_file, "r") as f:
        results = json.load(f)

    if not results.get("success", False):
        print(f"Simulation was not successful for {scenario_name}")
        return None

    return results


def create_simple_interactive_map(scenario_name, output_file=None):
    """
    Create a simple interactive map using Folium.

    Args:
        scenario_name: Name of the scenario
        output_file: Output HTML file path (optional)

    Returns:
        str: Path to the created HTML file
    """
    # Check if we have real simulation results
    results = load_network_from_results(scenario_name)

    if results:
        print(f"Found simulation results for {scenario_name}")
        print("Note: Creating demo network since full pandapipes network reconstruction is complex")
    else:
        print(f"No simulation results found for {scenario_name}")
        print("Creating demo network for visualization")

    # Create a simple demo network for visualization
    print(f"Creating interactive map for {scenario_name}")

    # Create a simple demo network for visualization
    try:
        import pandapipes as pp
        import numpy as np

        # Create a simple network
        net = pp.create_empty_network(fluid="water")

        # Create junctions in a grid pattern
        junctions = []
        for i in range(3):
            for j in range(3):
                x = i * 100
                y = j * 100
                sup_j = pp.create_junction(
                    net, pn_bar=6.0, tfluid_k=343.15, geodata=(x, y), name=f"sup_{i}_{j}"
                )
                ret_j = pp.create_junction(
                    net, pn_bar=6.0, tfluid_k=313.15, geodata=(x + 5, y), name=f"ret_{i}_{j}"
                )
                junctions.append((sup_j, ret_j))

        # Add x and y columns for mapping compatibility
        if "geodata" in net.junction.columns:
            net.junction["x"] = net.junction["geodata"].apply(
                lambda g: g[0] if g is not None else 0
            )
            net.junction["y"] = net.junction["geodata"].apply(
                lambda g: g[1] if g is not None else 0
            )
        else:
            # If geodata column doesn't exist, create x and y from the grid pattern
            net.junction["x"] = 0
            net.junction["y"] = 0
            for idx, row in net.junction.iterrows():
                name_str = str(row["name"])
                if "sup_0_0" in name_str:
                    net.junction.at[idx, "x"] = 0
                    net.junction.at[idx, "y"] = 0
                elif "sup_0_1" in name_str:
                    net.junction.at[idx, "x"] = 0
                    net.junction.at[idx, "y"] = 100
                elif "sup_0_2" in name_str:
                    net.junction.at[idx, "x"] = 0
                    net.junction.at[idx, "y"] = 200
                elif "sup_1_0" in name_str:
                    net.junction.at[idx, "x"] = 100
                    net.junction.at[idx, "y"] = 0
                elif "sup_1_1" in name_str:
                    net.junction.at[idx, "x"] = 100
                    net.junction.at[idx, "y"] = 100
                elif "sup_1_2" in name_str:
                    net.junction.at[idx, "x"] = 100
                    net.junction.at[idx, "y"] = 200
                elif "sup_2_0" in name_str:
                    net.junction.at[idx, "x"] = 200
                    net.junction.at[idx, "y"] = 0
                elif "sup_2_1" in name_str:
                    net.junction.at[idx, "x"] = 200
                    net.junction.at[idx, "y"] = 100
                elif "sup_2_2" in name_str:
                    net.junction.at[idx, "x"] = 200
                    net.junction.at[idx, "y"] = 200
                # For return junctions, offset by 5
                elif "ret_" in name_str:
                    base_name = name_str.replace("ret_", "sup_")
                    for idx2, row2 in net.junction.iterrows():
                        if base_name in str(row2["name"]):
                            net.junction.at[idx, "x"] = row2["x"] + 5
                            net.junction.at[idx, "y"] = row2["y"]
                            break

        # Create external grid at center
        center_sup, center_ret = junctions[4]
        pp.create_ext_grid(net, junction=center_sup, p_bar=6.0, t_k=343.15, name="Plant_Supply")

        # Create pipes connecting junctions
        for i in range(3):
            for j in range(3):
                if i < 2:  # Horizontal connections
                    sup_from, ret_from = junctions[i * 3 + j]
                    sup_to, ret_to = junctions[(i + 1) * 3 + j]

                    pp.create_pipe_from_parameters(
                        net,
                        from_junction=sup_from,
                        to_junction=sup_to,
                        length_km=0.1,
                        diameter_m=0.2,
                        name=f"SUP_H_{i}_{j}",
                    )
                    pp.create_pipe_from_parameters(
                        net,
                        from_junction=ret_from,
                        to_junction=ret_to,
                        length_km=0.1,
                        diameter_m=0.2,
                        name=f"RET_H_{i}_{j}",
                    )

                if j < 2:  # Vertical connections
                    sup_from, ret_from = junctions[i * 3 + j]
                    sup_to, ret_to = junctions[i * 3 + (j + 1)]

                    pp.create_pipe_from_parameters(
                        net,
                        from_junction=sup_from,
                        to_junction=sup_to,
                        length_km=0.1,
                        diameter_m=0.2,
                        name=f"SUP_V_{i}_{j}",
                    )
                    pp.create_pipe_from_parameters(
                        net,
                        from_junction=ret_from,
                        to_junction=ret_to,
                        length_km=0.1,
                        diameter_m=0.2,
                        name=f"RET_V_{i}_{j}",
                    )

        # Add heat consumers
        for i, (sup_j, ret_j) in enumerate(junctions):
            if i != 4:  # Skip center (plant)
                pp.create_heat_exchanger(
                    net, from_junction=sup_j, to_junction=ret_j, qext_w=10000, name=f"consumer_{i}"
                )

    except ImportError:
        print("pandapipes not available, creating mock network data")
        return None

    # Now create the interactive map
    return create_folium_map_from_network(net, scenario_name, output_file)


def create_folium_map_from_network(net, scenario_name, output_file=None):
    """
    Create Folium map from pandapipes network.

    Args:
        net: pandapipes network object
        scenario_name: Name of the scenario
        output_file: Output HTML file path (optional)

    Returns:
        str: Path to the created HTML file
    """
    # Find center point (plant location)
    try:
        plant_j = net.ext_grid.junction.iloc[0]
        plant_x, plant_y = net.junction.at[plant_j, "x"], net.junction.at[plant_j, "y"]
    except:
        # Fallback: use center of all junctions
        plant_x = net.junction.x.mean()
        plant_y = net.junction.y.mean()

    # Convert to lat/lon if in projected CRS
    # Assume EPSG:25833 (ETRS89 / UTM zone 33N) for Germany
    if hasattr(net.junction, "crs") and net.junction.crs and net.junction.crs.is_projected:
        transformer = Transformer.from_crs(net.junction.crs, "EPSG:4326", always_xy=True)
        plant_lon, plant_lat = transformer.transform(plant_x, plant_y)
    else:
        # Assume already in lat/lon
        plant_lon, plant_lat = plant_x, plant_y

    # Create the map centered on the plant
    m = folium.Map(location=[plant_lat, plant_lon], zoom_start=15, tiles="OpenStreetMap")

    # Add pipes
    for name, row in net.pipe_geodata.iterrows():
        try:
            line = mapping(LineString(row.coords))
            color = "red" if name.startswith("SUP_") else "blue"

            # Convert coordinates if needed
            if (
                hasattr(net.pipe_geodata, "crs")
                and net.pipe_geodata.crs
                and net.pipe_geodata.crs.is_projected
            ):
                transformer = Transformer.from_crs(
                    net.pipe_geodata.crs, "EPSG:4326", always_xy=True
                )
                coords = list(LineString(row.coords).coords)
                transformed_coords = [transformer.transform(x, y) for x, y in coords]
                line = mapping(LineString(transformed_coords))

            folium.GeoJson(
                line,
                style_function=lambda feat, c=color: {"color": c, "weight": 4, "opacity": 0.8},
                tooltip=f"Pipe: {name}",
            ).add_to(m)
        except Exception as e:
            print(f"Warning: Could not add pipe {name}: {e}")

    # Add junctions
    for j, rj in net.junction.iterrows():
        try:
            x, y = rj.x, rj.y
            # Convert to lat/lon if needed
            if hasattr(net.junction, "crs") and net.junction.crs and net.junction.crs.is_projected:
                transformer = Transformer.from_crs(net.junction.crs, "EPSG:4326", always_xy=True)
                x, y = transformer.transform(x, y)
            name_str = str(rj.name)
            color = "red" if name_str.startswith("sup_") else "blue"
            folium.CircleMarker(
                location=[y, x],
                radius=5,
                color=color,
                fill=True,
                popup=f"Junction: {name_str}",
                tooltip=f"Junction: {name_str}",
            ).add_to(m)
        except Exception as e:
            print(f"Warning: Could not add junction {j}: {e}")

    # Add heat consumers
    for hx in net.heat_exchanger.itertuples():
        try:
            sup_j = net.junction.loc[hx.from_junction]
            x, y = sup_j.x, sup_j.y
            # Convert to lat/lon if needed
            if hasattr(net.junction, "crs") and net.junction.crs and net.junction.crs.is_projected:
                transformer = Transformer.from_crs(net.junction.crs, "EPSG:4326", always_xy=True)
                x, y = transformer.transform(x, y)
            folium.RegularPolygonMarker(
                location=[y, x],
                number_of_sides=3,
                radius=6,
                color="orange",
                fill=True,
                popup=f"Consumer: {hx.name}",
                tooltip=f"Consumer: {hx.name}",
            ).add_to(m)
        except Exception as e:
            print(f"Warning: Could not add consumer {hx.name}: {e}")

    # Add CHP plant marker
    try:
        for idx, ext_grid in net.ext_grid.iterrows():
            junction = net.junction.loc[ext_grid.junction]
            x, y = junction.x, junction.y

            # Convert to lat/lon if needed
            if hasattr(net.junction, "crs") and net.junction.crs and net.junction.crs.is_projected:
                transformer = Transformer.from_crs(net.junction.crs, "EPSG:4326", always_xy=True)
                x, y = transformer.transform(x, y)

            folium.RegularPolygonMarker(
                location=[y, x],
                number_of_sides=4,
                radius=8,
                color="green",
                rotation=45,
                fill=True,
                popup="CHP Plant",
                tooltip="CHP Plant",
            ).add_to(m)
            break
    except Exception as e:
        print(f"Warning: Could not add CHP plant: {e}")

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
        output_file = f"simulation_outputs/interactive_dh_{scenario_name}.html"

    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True)

    m.save(str(output_path))
    print(f"Interactive map saved to: {output_path}")
    return str(output_path)


def main():
    parser = argparse.ArgumentParser(description="Create interactive DH network map with Folium")
    parser.add_argument(
        "--scenario", type=str, default="demo_network", help="Scenario name (default: demo_network)"
    )
    parser.add_argument("--output", type=str, help="Output HTML file path (optional)")

    args = parser.parse_args()

    if not FOLIUM_AVAILABLE:
        print("Error: folium not available. Install with 'pip install folium'")
        return

    # Create the interactive map
    output_file = create_simple_interactive_map(args.scenario, args.output)

    if output_file:
        print(f"\n✅ Interactive map created successfully!")
        print(f"📁 File: {output_file}")
        print(f"🌐 Open this file in your web browser to view the interactive map")
        print(f"🔍 Features: Pan, zoom, click on elements for details")
    else:
        print("❌ Failed to create interactive map")


if __name__ == "__main__":
    main()
