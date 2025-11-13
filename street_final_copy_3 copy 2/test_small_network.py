#!/usr/bin/env python3
"""
Test script for debugging pandapipes DH network convergence
Creates a minimal network with 3 buildings to isolate issues
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import pandapipes as pp
import pandapipes.plotting as plot
import matplotlib.pyplot as plt

# Test parameters
SUPPLY_TEMP = 70  # °C
RETURN_TEMP = 40  # °C
CP_WATER = 4180  # J/(kg·K)


def create_simple_test_network():
    """Create a simple test network with 3 buildings using correct pandapipes elements"""

    # Create simple building data
    buildings_data = [
        {"id": "plant", "x": 0, "y": 0, "heat_demand_w": 0, "is_plant": True},
        {"id": "building1", "x": 100, "y": 0, "heat_demand_w": 100000, "is_plant": False},  # 100 kW
        {"id": "building2", "x": 50, "y": 86.6, "heat_demand_w": 80000, "is_plant": False},  # 80 kW
    ]

    print("Creating simple test network with 3 buildings...")

    # Create pandapipe network
    net = pp.create_empty_network(fluid="water")

    # Create junctions for supply flow
    supply_jids = []
    for i, bldg in enumerate(buildings_data):
        jid = pp.create_junction(
            net, pn_bar=5.0, tfluid_k=70 + 273.15, name=f"sup_{bldg['id']}"  # 70°C supply
        )
        supply_jids.append(jid)

    # Create junctions for return flow
    return_jids = []
    for i, bldg in enumerate(buildings_data):
        jid = pp.create_junction(
            net, pn_bar=5.0, tfluid_k=40 + 273.15, name=f"ret_{bldg['id']}"  # 40°C return
        )
        return_jids.append(jid)

    # Find plant index
    plant_idx = next(i for i, b in enumerate(buildings_data) if b["is_plant"])

    # Create pipes for supply flow (star topology from plant)
    for i, bldg in enumerate(buildings_data):
        if not bldg["is_plant"]:
            # Calculate distance from plant
            dx = bldg["x"] - buildings_data[plant_idx]["x"]
            dy = bldg["y"] - buildings_data[plant_idx]["y"]
            distance = np.sqrt(dx * dx + dy * dy) / 1000  # km

            pp.create_pipe_from_parameters(
                net,
                from_junction=supply_jids[plant_idx],
                to_junction=supply_jids[i],
                length_km=distance,
                diameter_m=200e-3,  # 200mm
                alpha_w_per_m2k=5,
            )

    # Create pipes for return flow (star topology to plant)
    for i, bldg in enumerate(buildings_data):
        if not bldg["is_plant"]:
            # Calculate distance from plant
            dx = bldg["x"] - buildings_data[plant_idx]["x"]
            dy = bldg["y"] - buildings_data[plant_idx]["y"]
            distance = np.sqrt(dx * dx + dy * dy) / 1000  # km

            pp.create_pipe_from_parameters(
                net,
                from_junction=return_jids[i],
                to_junction=return_jids[plant_idx],
                length_km=distance,
                diameter_m=200e-3,  # 200mm
                alpha_w_per_m2k=5,
            )

    # Create circulation pump at plant
    total_heat_demand = sum(b["heat_demand_w"] for b in buildings_data if not b["is_plant"])
    delta_t = 70 - 40  # 30K temperature difference
    nominal_flow = total_heat_demand / (4180 * delta_t)  # kg/s

    pp.create_circ_pump_const_pressure(
        net,
        return_junction=return_jids[plant_idx],
        flow_junction=supply_jids[plant_idx],
        p_flow_bar=5.0,
        plift_bar=0.7,
        t_flow_k=70 + 273.15,  # 70°C
    )

    print(f"Total heat demand: {total_heat_demand/1000:.1f} kW")
    print(f"Nominal flow: {nominal_flow:.3f} kg/s")

    # Create heat consumers for each building (except plant)
    for i, bldg in enumerate(buildings_data):
        if not bldg["is_plant"]:
            heat_demand = bldg["heat_demand_w"]
            mdot = heat_demand / (4180 * delta_t)

            pp.create_heat_consumer(
                net,
                from_junction=supply_jids[i],
                to_junction=return_jids[i],
                diameter_m=200e-3,
                controlled_mdot_kg_per_s=mdot,
                qext_w=heat_demand,
            )

    print(f"Created network with {len(net.junction)} junctions and {len(net.pipe)} pipes")
    print("Network components:")
    print(f"- Junctions: {len(net.junction)}")
    print(f"- Pipes: {len(net.pipe)}")
    print(f"- Heat consumers: {len(net.heat_consumer)}")
    print(f"- Circulation pumps: {len(net.circ_pump_pressure)}")

    return net


def test_network_convergence():
    """Test the simple network for convergence"""

    try:
        # Create network
        net = create_simple_test_network()

        # Try to run simulation
        print("\nRunning pandapipe simulation...")
        pp.pipeflow(net)

        print("✅ Simulation converged successfully!")

        # Print results
        print("\n--- SIMULATION RESULTS ---")
        print("Pipe results:")
        for idx, row in net.res_pipe.iterrows():
            print(
                f"  Pipe {idx}: v_mean={row['v_mean_m_per_s']:.2f} m/s, "
                f"p_from={row['p_from_bar']:.2f} bar, p_to={row['p_to_bar']:.2f} bar"
            )

        print("\nHeat consumer results:")
        for idx, row in net.res_heat_consumer.iterrows():
            print(f"  Heat Consumer {idx}: qext_w={row['qext_w']:.0f} W")

        print("\nJunction pressures:")
        for idx, row in net.res_junction.iterrows():
            print(f"  Junction {idx}: p={row['p_bar']:.2f} bar, t={row['t_k']-273.15:.1f}°C")

        # Try to plot
        try:
            fig, ax = plot.simple_plot(
                net, plot_sinks=False, plot_sources=True, title="Simple Test DH Network"
            )
            plt.savefig("test_network.png", dpi=300, bbox_inches="tight")
            print("\n✅ Network plot saved as 'test_network.png'")
            plt.close(fig)
        except Exception as e:
            print(f"⚠️  Could not create plot: {e}")

        return True

    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        print(f"Error type: {type(e).__name__}")

        # Print network diagnostics
        try:
            print("\n--- NETWORK DIAGNOSTICS ---")
            print(f"Junctions: {len(net.junction)}")
            print(f"Pipes: {len(net.pipe)}")
            print(f"Heat consumers: {len(net.heat_consumer)}")
            print(f"Circulation pumps: {len(net.circ_pump_pressure)}")

            # Check for isolated nodes
            connected_junctions = set()
            for _, pipe in net.pipe.iterrows():
                connected_junctions.add(pipe["from_junction"])
                connected_junctions.add(pipe["to_junction"])

            all_junctions = set(net.junction.index)
            isolated = all_junctions - connected_junctions
            if isolated:
                print(f"⚠️  Isolated junctions: {isolated}")
            else:
                print("✅ All junctions are connected")

        except Exception as diag_e:
            print(f"⚠️  Could not run diagnostics: {diag_e}")

        return False


if __name__ == "__main__":
    print("=== PANDAPIPES DH NETWORK DEBUG TEST ===")
    success = test_network_convergence()

    if success:
        print("\n🎉 Test passed! The basic network topology works.")
        print("The issue in the main simulation is likely due to:")
        print("- Complex network topology")
        print("- Parameter tuning needed")
        print("- Boundary condition setup")
    else:
        print("\n🔧 Test failed. Need to fix basic network setup first.")
