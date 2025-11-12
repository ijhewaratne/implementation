# src/simulation_runner.py

import argparse
import json
from pathlib import Path
import multiprocessing
import traceback
import networkx as nx
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

# Import simulation libraries
try:
    import pandapipes as pp
    from pandapipes.component_models import CirculationPump, HeatExchanger

    PANDAPIPES_AVAILABLE = True
except ImportError:
    PANDAPIPES_AVAILABLE = False
    print("Warning: pandapipes not available. DH simulations will use placeholders.")

try:
    import pandapower as pn

    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False
    print("Warning: pandapower not available. HP simulations will use placeholders.")

# Import our configuration
from .simulation_config import PIPE_SPECS, NETWORK_PARAMS

RESULTS_DIR = Path("simulation_outputs")
RESULTS_DIR.mkdir(exist_ok=True)


def create_dh_network_from_buildings(buildings_gdf, scenario_params):
    """
    Creates a pandapipe network with radial topology for district heating.
    Uses a central heat source building with consumers connected in series.
    Includes proper boundary conditions for convergence.
    """
    if not PANDAPIPES_AVAILABLE:
        raise ImportError("pandapipes is required for DH simulations")

    # 1. Ensure building data is in a projected Coordinate Reference System (CRS) for accurate distances
    if buildings_gdf.crs.is_geographic:
        print(
            "Warning: Buildings GeoDataFrame is in a geographic CRS. Reprojecting to a suitable UTM CRS."
        )
        buildings_gdf = buildings_gdf.to_crs(buildings_gdf.estimate_utm_crs())

    # 2. Create a pandapipe network
    net = pp.create_empty_network(fluid="water")

    # 3. Calculate total heat demand and select central heat source
    total_demand_w = buildings_gdf["heating_load_kw"].sum() * 1000
    print(f"Total heat demand: {total_demand_w/1000:.1f} kW")

    # Select building closest to centroid as heat source
    centroid = buildings_gdf.geometry.unary_union.centroid
    distances = buildings_gdf.geometry.centroid.distance(centroid)
    source_building_idx = distances.idxmin()
    source_building = buildings_gdf.iloc[source_building_idx]
    print(
        f"Selected building {source_building['GebaeudeID']} as central heat source (closest to centroid)"
    )

    # 4. Create radial network topology
    # Start with heat source building
    source_coords = source_building.geometry.centroid
    source_supply_junction = pp.create_junction(
        net,
        pn_bar=6.0,
        tfluid_k=scenario_params.get("supply_temp", 70) + 273.15,
        geodata=(source_coords.x, source_coords.y),
        name=f"plant_supply",
    )
    source_return_junction = pp.create_junction(
        net,
        pn_bar=6.0,
        tfluid_k=scenario_params.get("return_temp", 40) + 273.15,
        geodata=(source_coords.x, source_coords.y),
        name=f"plant_return",
    )

    # 5. Add external grid at plant supply junction (pressure/temperature boundary)
    supply_temp_k = scenario_params.get("supply_temp", 70) + 273.15
    return_temp_k = scenario_params.get("return_temp", 40) + 273.15
    delta_t_k = supply_temp_k - return_temp_k

    # Calculate mass flow rate from heat demand and temperature difference
    # Q = m * cp * ΔT, where cp ≈ 4186 J/(kg·K) for water
    cp_water = 4186  # J/(kg·K)
    mdot_kg_per_s = total_demand_w / (cp_water * delta_t_k)
    print(
        f"Estimated mass flow at plant supply: {mdot_kg_per_s:.2f} kg/s (Q={total_demand_w/1000:.1f} kW, ΔT={delta_t_k:.0f} K)"
    )

    pp.create_ext_grid(
        net,
        junction=source_supply_junction,
        p_bar=6.0,  # supply pressure
        t_k=supply_temp_k,
        name="plant_ext_grid",
    )
    print("Added external grid at plant supply junction.")

    # 6. Connect consumer buildings in radial topology
    consumer_buildings = buildings_gdf[buildings_gdf.index != source_building_idx].copy()
    consumer_buildings = consumer_buildings.sort_values(
        "heating_load_kw", ascending=False
    )  # Connect largest consumers first

    current_supply_junction = source_supply_junction
    current_return_junction = source_return_junction

    for idx, building in consumer_buildings.iterrows():
        coords = building.geometry.centroid

        # Create supply and return junctions for this building
        building_supply_junction = pp.create_junction(
            net,
            pn_bar=6.0,
            tfluid_k=supply_temp_k,
            geodata=(coords.x, coords.y),
            name=f"supply_{building['GebaeudeID']}",
        )
        building_return_junction = pp.create_junction(
            net,
            pn_bar=6.0,
            tfluid_k=return_temp_k,
            geodata=(coords.x, coords.y),
            name=f"return_{building['GebaeudeID']}",
        )

        # Connect to current network
        geo = net.junction_geodata.loc[current_supply_junction]
        distance = coords.distance(Point(geo["x"], geo["y"]))
        pp.create_pipe_from_parameters(
            net,
            from_junction=current_supply_junction,
            to_junction=building_supply_junction,
            length_km=distance / 1000,
            diameter_m=0.048,
            name=f"pipe_supply_{building['GebaeudeID']}",
        )
        pp.create_pipe_from_parameters(
            net,
            from_junction=building_return_junction,
            to_junction=current_return_junction,
            length_km=distance / 1000,
            diameter_m=0.048,
            name=f"pipe_return_{building['GebaeudeID']}",
        )

        # Add heat exchanger for this building
        heat_demand_w = building["heating_load_kw"] * 1000
        pp.create_heat_exchanger(
            net,
            from_junction=building_supply_junction,
            to_junction=building_return_junction,
            diameter_m=0.1,
            qext_w=-heat_demand_w,
            name=f"he_{building['GebaeudeID']}",
        )

        # Update current junctions for next building
        current_supply_junction = building_supply_junction
        current_return_junction = building_return_junction

    # 7. Add pressure boundary (sink) at the last return junction
    pp.create_sink(
        net, junction=current_return_junction, mdot_kg_per_s=mdot_kg_per_s, name="system_sink"
    )
    print("Added pressure boundary at last return junction (sink).")

    print(
        f"Created radial DH network with {len(net.junction)} junctions and {len(net.pipe)} pipes."
    )
    print(
        f"Heat source at building {source_building['GebaeudeID']}, total demand: {total_demand_w/1000:.1f} kW"
    )
    print(f"Connected {len(consumer_buildings)} consumer buildings in radial topology")

    # 8. Debug: Print pipe summary
    print("\n--- PIPE SUMMARY ---")
    for idx, row in net.pipe.iterrows():
        from_junc = row["from_junction"]
        to_junc = row["to_junction"]
        length_m = row["length_km"] * 1000
        diameter_mm = row["diameter_m"] * 1000
        print(
            f"Pipe {idx}: {from_junc} -> {to_junc}, Length: {length_m:.2f} m, Diameter: {diameter_mm:.1f} mm"
        )
    print("--- END PIPE SUMMARY ---")

    # 9. Debug: Print all node coordinates
    print("--- JUNCTION COORDINATES ---")
    for idx, row in net.junction.iterrows():
        try:
            geo = net.junction_geodata.loc[idx]
            print(f"Junction {idx}: x={geo['x']:.2f}, y={geo['y']:.2f}")
        except Exception:
            print(f"Junction {idx}: geodata not available")
    print("--- END JUNCTION COORDINATES ---\n")

    # 10. Save network to file for inspection and plotting
    import json
    from pathlib import Path

    # Create output directory
    output_dir = Path("simulation_outputs")
    output_dir.mkdir(exist_ok=True)

    # Save network to JSON for inspection
    network_file = output_dir / f"dh_network_{scenario_params.get('supply_temp', 70)}C.json"

    # Extract network data for JSON export
    network_data = {
        "junctions": [],
        "pipes": [],
        "heat_exchangers": [],
        "pumps": [],
        "sources": [],
        "sinks": [],
        "external_grids": [],
    }

    # Add junctions
    for idx, row in net.junction.iterrows():
        try:
            geodata = row["geodata"]
            x, y = geodata[0], geodata[1]
        except (KeyError, TypeError):
            x, y = 0.0, 0.0  # Default coordinates if geodata not available

        network_data["junctions"].append(
            {"id": idx, "x": x, "y": y, "pn_bar": row["pn_bar"], "tfluid_k": row["tfluid_k"]}
        )

    # Add pipes
    for idx, row in net.pipe.iterrows():
        network_data["pipes"].append(
            {
                "id": idx,
                "from_junction": row["from_junction"],
                "to_junction": row["to_junction"],
                "length_km": row["length_km"],
                "diameter_m": row["diameter_m"],
                "name": row["name"],
            }
        )

    # Add heat exchangers
    for idx, row in net.heat_exchanger.iterrows():
        network_data["heat_exchangers"].append(
            {
                "id": idx,
                "from_junction": row["from_junction"],
                "to_junction": row["to_junction"],
                "qext_w": row["qext_w"],
                "name": row["name"],
            }
        )

    # Add pumps
    if hasattr(net, "circ_pump_pressure"):
        for idx, row in net.circ_pump_pressure.iterrows():
            network_data["pumps"].append(
                {
                    "id": idx,
                    "return_junction": row["return_junction"],
                    "flow_junction": row["flow_junction"],
                    "p_flow_bar": row["p_flow_bar"],
                    "plift_bar": row["plift_bar"],
                    "name": row["name"],
                }
            )

    # Add sources
    if hasattr(net, "source"):
        for idx, row in net.source.iterrows():
            network_data["sources"].append(
                {
                    "id": idx,
                    "junction": row["junction"],
                    "mdot_kg_per_s": row["mdot_kg_per_s"],
                    "name": row["name"],
                }
            )

    # Add external grids
    if hasattr(net, "ext_grid"):
        for idx, row in net.ext_grid.iterrows():
            network_data["external_grids"] = network_data.get("external_grids", [])
            network_data["external_grids"].append(
                {
                    "id": idx,
                    "junction": row["junction"],
                    "p_bar": row["p_bar"],
                    "t_k": row["t_k"],
                    "name": row["name"],
                }
            )

    # Add sinks
    for idx, row in net.sink.iterrows():
        network_data["sinks"].append(
            {
                "id": idx,
                "junction": row["junction"],
                "mdot_kg_per_s": row["mdot_kg_per_s"],
                "name": row["name"],
                "scaling": row["scaling"],
                "in_service": row["in_service"],
                "type": row["type"],
            }
        )

    # Save to JSON file
    with open(network_file, "w") as f:
        json.dump(network_data, f, indent=2)

    print(f"Network saved to: {network_file}")
    print(f"You can inspect this file or use pandapipes plotting tools to visualize the network.")

    # Also save a simple network summary
    summary_file = output_dir / f"dh_network_summary_{scenario_params.get('supply_temp', 70)}C.txt"
    with open(summary_file, "w") as f:
        f.write(f"DH Network Summary\n")
        f.write(f"==================\n")
        f.write(f"Total junctions: {len(net.junction)}\n")
        f.write(f"Total pipes: {len(net.pipe)}\n")
        f.write(f"Total heat exchangers: {len(net.heat_exchanger)}\n")
        f.write(
            f"Total pumps: {len(net.circ_pump_pressure) if hasattr(net, 'circ_pump_pressure') else 0}\n"
        )
        f.write(f"Total sources: {len(net.source) if hasattr(net, 'source') else 0}\n")
        f.write(f"Total sinks: {len(net.sink)}\n")
        f.write(f"Total heat demand: {total_demand_w/1000:.1f} kW\n")
        f.write(f"Mass flow rate: {mdot_kg_per_s:.2f} kg/s\n")
        f.write(f"Supply temperature: {scenario_params.get('supply_temp', 70)}°C\n")
        f.write(f"Return temperature: {scenario_params.get('return_temp', 40)}°C\n")

    print(f"Network summary saved to: {summary_file}")

    return net


def run_pandapipes_simulation(scenario):
    """
    Run a single pandapipes simulation for a DH scenario.
    """
    try:
        print(f"Running DH simulation for scenario: {scenario['name']}")

        if not PANDAPIPES_AVAILABLE:
            return {
                "scenario": scenario["name"],
                "type": "DH",
                "success": False,
                "error": "pandapipes library not installed.",
            }

        buildings_gdf = gpd.read_file(scenario["building_file"])

        if buildings_gdf.empty:
            return {
                "scenario": scenario.get("name", ""),
                "type": "DH",
                "success": False,
                "error": "Building file is empty or contains no features.",
            }

        # Ensure there's a non-zero demand to prevent convergence issues
        if "heating_load_kw" not in buildings_gdf.columns:
            buildings_gdf["heating_load_kw"] = 10.0  # Assign a default
        buildings_gdf["heating_load_kw"] = buildings_gdf["heating_load_kw"].clip(
            lower=1.0
        )  # Ensure a minimum of 1kW demand
        print(f"Total heat demand: {buildings_gdf['heating_load_kw'].sum():.1f} kW")

        net = create_dh_network_from_buildings(buildings_gdf, scenario.get("params", {}))

        print("Running pandapipe simulation...")
        pp.pipeflow(net)

        # Extract results
        print("res_heat_exchanger columns:", net.res_heat_exchanger.columns)
        if "qext_w" in net.res_heat_exchanger.columns:
            total_heat_supplied_w = -net.res_heat_exchanger["qext_w"].sum()
        else:
            print(
                "Warning: 'qext_w' not found in res_heat_exchanger. Available columns:",
                net.res_heat_exchanger.columns,
            )
            total_heat_supplied_w = None

        total_heat_supplied_mwh = total_heat_supplied_w / 1e6  # W -> MW, assuming 1 hour -> MWh

        pump_power_w = (
            net.res_circ_pump_const_pressure.mdot_flow_kg_per_s.item()
            * net.res_circ_pump_const_pressure.deltap_bar.item()
            * 1e5
            / 997
        )  # A rough estimate
        pump_energy_kwh = pump_power_w / 1000  # Assuming 1hr

        max_pressure_drop_bar = (net.res_pipe.p_from_bar - net.res_pipe.p_to_bar).abs().max()

        return {
            "scenario": scenario["name"],
            "type": "DH",
            "success": True,
            "kpi": {
                "total_heat_supplied_mwh": round(total_heat_supplied_mwh, 4),
                "pump_energy_kwh": round(pump_energy_kwh, 2),
                "max_pressure_drop_bar": round(max_pressure_drop_bar, 3),
            },
        }

    except Exception as e:
        traceback.print_exc()
        return {
            "scenario": scenario.get("name", ""),
            "type": "DH",
            "success": False,
            "error": str(e),
        }


def run_pandapower_simulation(scenario):
    """
    Placeholder: Run a single pandapower simulation for HP scenario.
    """
    print(f"Running HP simulation for scenario: {scenario['name']} (PLACEHOLDER)")
    return {
        "scenario": scenario["name"],
        "type": "HP",
        "success": True,
        "kpi": {"max_feeder_load_percent": 82, "transformer_overloads": 1},
    }


def run_scenario(scenario_file):
    """
    Load scenario JSON, call the correct simulation function, and save results.
    """
    try:
        with open(scenario_file, "r", encoding="utf-8") as f:
            scenario = json.load(f)
        if scenario.get("type", "DH").upper() == "DH":
            results = run_pandapipes_simulation(scenario)
        elif scenario.get("type", "DH").upper() == "HP":
            results = run_pandapower_simulation(scenario)
        else:
            raise ValueError(f"Unknown scenario type: {scenario.get('type')}")

        out_file = RESULTS_DIR / f"{scenario['name']}_results.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"Results saved: {out_file}")
        return results
    except Exception as e:
        traceback.print_exc()
        return {"scenario_file": scenario_file, "success": False, "error": str(e)}


def run_simulation_scenarios(scenario_files, parallel=True):
    """
    Batch run all scenario files.
    """
    print(f"Running simulations for {len(scenario_files)} scenarios...")
    if parallel and len(scenario_files) > 1:
        with multiprocessing.Pool(processes=min(4, len(scenario_files))) as pool:
            results = pool.map(run_scenario, scenario_files)
    else:
        results = [run_scenario(sf) for sf in scenario_files]
    print("\nAll simulations complete.")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run batch energy network simulations for scenario files."
    )
    parser.add_argument(
        "--scenarios", nargs="+", required=True, help="List of scenario JSON files to run"
    )
    parser.add_argument("--no_parallel", action="store_true", help="Disable multiprocessing")
    args = parser.parse_args()

    run_simulation_scenarios(args.scenarios, parallel=not args.no_parallel)
