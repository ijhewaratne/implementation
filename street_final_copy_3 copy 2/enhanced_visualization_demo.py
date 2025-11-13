#!/usr/bin/env python3
"""
Enhanced Network Visualization Demo

This script demonstrates the enhanced network visualization capabilities
with street map overlays for the Branitz Energy Decision AI system.

Features:
- Static maps with OSM street overlay using GeoPandas + Contextily
- Interactive maps using Folium
- Automatic coordinate transformation
- Building context integration

Usage:
    python enhanced_visualization_demo.py [--street STREET_NAME] [--interactive] [--static]
"""

import argparse
import json
import os
import sys
from pathlib import Path
import geopandas as gpd

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from network_visualization import (
        create_static_network_map,
        create_interactive_network_map,
        create_enhanced_network_visualization,
    )

    ENHANCED_VISUALIZATION_AVAILABLE = True
except ImportError as e:
    print(f"Error importing enhanced visualization: {e}")
    print("Make sure you have installed the required dependencies:")
    print("pip install contextily folium")
    ENHANCED_VISUALIZATION_AVAILABLE = False


def load_existing_simulation_results(street_name):
    """
    Load existing simulation results for a given street.

    Args:
        street_name: Name of the street to load results for

    Returns:
        tuple: (net, buildings_gdf) or (None, None) if not found
    """
    # Clean street name for file matching
    clean_name = street_name.replace(" ", "_").replace("/", "_").replace("\\", "_")

    # Look for existing simulation results
    simulation_dir = Path("simulation_outputs")
    results_file = simulation_dir / f"street_{clean_name}_results.json"

    if not results_file.exists():
        print(f"No simulation results found for {street_name}")
        print(f"Expected file: {results_file}")
        return None, None

    # Load simulation results
    with open(results_file, "r") as f:
        results = json.load(f)

    if not results.get("success", False):
        print(f"Simulation for {street_name} was not successful")
        return None, None

    # Load buildings data
    buildings_file = Path("street_analysis_outputs") / f"buildings_{clean_name}.geojson"
    if buildings_file.exists():
        buildings_gdf = gpd.read_file(buildings_file)
    else:
        print(f"Warning: Buildings file not found: {buildings_file}")
        buildings_gdf = None

    # For this demo, we'll create a mock network since we can't easily reconstruct
    # the pandapipes network from the results file
    print(f"Found simulation results for {street_name}")
    print(f"Buildings loaded: {len(buildings_gdf) if buildings_gdf is not None else 0}")

    return None, buildings_gdf  # Return None for net since we can't reconstruct it easily


def create_demo_network():
    """
    Create a demo pandapipes network for visualization testing.

    Returns:
        pandapipes network object
    """
    try:
        import pandapipes as pp
        import numpy as np
        from shapely.geometry import Point, LineString

        # Create a simple demo network
        net = pp.create_empty_network(fluid="water")

        # Create junctions in a simple grid pattern
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

        # Create external grid at center
        center_sup, center_ret = junctions[4]  # Center junction
        pp.create_ext_grid(net, junction=center_sup, p_bar=6.0, t_k=343.15, name="Plant_Supply")

        # Create pipes connecting junctions
        for i in range(3):
            for j in range(3):
                if i < 2:  # Horizontal connections
                    sup_from, ret_from = junctions[i * 3 + j]
                    sup_to, ret_to = junctions[(i + 1) * 3 + j]

                    # Supply pipe
                    pp.create_pipe_from_parameters(
                        net,
                        from_junction=sup_from,
                        to_junction=sup_to,
                        length_km=0.1,
                        diameter_m=0.2,
                        name=f"SUP_H_{i}_{j}",
                    )

                    # Return pipe
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

                    # Supply pipe
                    pp.create_pipe_from_parameters(
                        net,
                        from_junction=sup_from,
                        to_junction=sup_to,
                        length_km=0.1,
                        diameter_m=0.2,
                        name=f"SUP_V_{i}_{j}",
                    )

                    # Return pipe
                    pp.create_pipe_from_parameters(
                        net,
                        from_junction=ret_from,
                        to_junction=ret_to,
                        length_km=0.1,
                        diameter_m=0.2,
                        name=f"RET_V_{i}_{j}",
                    )

        # Add heat consumers at each junction (except center)
        for i, (sup_j, ret_j) in enumerate(junctions):
            if i != 4:  # Skip center (plant)
                pp.create_heat_exchanger(
                    net, from_junction=sup_j, to_junction=ret_j, qext_w=10000, name=f"consumer_{i}"
                )

        print("Created demo network with 9 junctions and heat consumers")
        return net

    except ImportError:
        print("pandapipes not available, cannot create demo network")
        return None
    except Exception as e:
        print(f"Error creating demo network: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Enhanced Network Visualization Demo")
    parser.add_argument(
        "--street", type=str, help="Street name to visualize (if simulation results exist)"
    )
    parser.add_argument("--interactive", action="store_true", help="Create interactive map")
    parser.add_argument(
        "--static", action="store_true", help="Create static map with street overlay"
    )
    parser.add_argument("--demo", action="store_true", help="Use demo network instead of real data")

    args = parser.parse_args()

    if not ENHANCED_VISUALIZATION_AVAILABLE:
        print("Enhanced visualization not available. Please install dependencies:")
        print("pip install contextily folium")
        return

    # Determine what to visualize
    if args.demo:
        print("Creating demo network visualization...")
        net = create_demo_network()
        buildings_gdf = None
        scenario_name = "demo_network"

        if net is None:
            print("Could not create demo network")
            return

    elif args.street:
        print(f"Loading simulation results for {args.street}...")
        net, buildings_gdf = load_existing_simulation_results(args.street)
        scenario_name = f"street_{args.street.replace(' ', '_')}"

        if net is None:
            print("Could not load simulation results. Use --demo for a demo network.")
            return
    else:
        print("No street specified and --demo not used.")
        print("Usage examples:")
        print("  python enhanced_visualization_demo.py --demo --static --interactive")
        print("  python enhanced_visualization_demo.py --street 'Bleyerstraße' --static")
        return

    # Create visualizations
    output_dir = "simulation_outputs"

    if args.static or not (args.static or args.interactive):
        print("\n" + "=" * 60)
        print("CREATING STATIC MAP WITH STREET OVERLAY")
        print("=" * 60)

        try:
            static_file = create_static_network_map(
                net=net,
                scenario_name=scenario_name,
                output_dir=output_dir,
                include_street_map=True,
                buildings_gdf=buildings_gdf,
            )
            print(f"✅ Static map created: {static_file}")
        except Exception as e:
            print(f"❌ Error creating static map: {e}")

    if args.interactive:
        print("\n" + "=" * 60)
        print("CREATING INTERACTIVE MAP")
        print("=" * 60)

        try:
            interactive_file = create_interactive_network_map(
                net=net,
                scenario_name=scenario_name,
                output_dir=output_dir,
                buildings_gdf=buildings_gdf,
            )
            if interactive_file:
                print(f"✅ Interactive map created: {interactive_file}")
                print("   Open this file in your web browser to view the interactive map")
            else:
                print("❌ Failed to create interactive map")
        except Exception as e:
            print(f"❌ Error creating interactive map: {e}")

    print("\n" + "=" * 60)
    print("VISUALIZATION COMPLETE")
    print("=" * 60)

    if args.static or not (args.static or args.interactive):
        print("📊 Static maps show the DH network overlaid on OpenStreetMap")
        print("   - Red lines: Supply pipes")
        print("   - Blue lines: Return pipes")
        print("   - Red dots: Supply junctions")
        print("   - Blue dots: Return junctions")
        print("   - Orange triangles: Heat consumers")
        print("   - Green square: CHP Plant")

    if args.interactive:
        print("🌐 Interactive maps allow you to:")
        print("   - Pan and zoom around the network")
        print("   - Click on elements for detailed information")
        print("   - Toggle different map layers")
        print("   - Export the view")


if __name__ == "__main__":
    main()
