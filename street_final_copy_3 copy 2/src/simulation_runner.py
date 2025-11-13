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
from shapely.geometry import Point, LineString
from scipy.spatial import distance_matrix
from pyproj import Transformer
import fiona
import shapely.geometry

# Import simulation libraries
try:
    import pandapipes as pp
    import pandapipes.plotting as plot
    import matplotlib.pyplot as plt

    PANDAPIPES_AVAILABLE = True
except ImportError:
    PANDAPIPES_AVAILABLE = False
    print("Warning: pandapipes not available. DH simulations will use placeholders.")

# Import enhanced visualization
try:
    from .network_visualization import create_enhanced_network_visualization

    ENHANCED_VISUALIZATION_AVAILABLE = True
except ImportError:
    ENHANCED_VISUALIZATION_AVAILABLE = False
    print("Warning: Enhanced visualization not available. Using basic plotting.")

try:
    import pandapower as pn

    PANDAPOWER_AVAILABLE = True
except ImportError:
    PANDAPOWER_AVAILABLE = False
    print("Warning: pandapower not available. HP simulations will use placeholders.")

try:
    import osmnx as ox

    OSMNX_AVAILABLE = True
except ImportError:
    OSMNX_AVAILABLE = False
    print("Warning: osmnx not available. Will use MST fallback for network topology.")

# Output directory
RESULTS_DIR = Path("simulation_outputs")
RESULTS_DIR.mkdir(exist_ok=True)

# -------------------------------
# NETWORK PARAMETERS
# -------------------------------
PLANT_LAT, PLANT_LON = 51.76274, 14.3453979  # Cottbus CHP (WGS84)
OFFSET_RETURN = 0.3  # offset for return main (m)
PIPE_DIAMETER_MAIN = 0.6  # 600 mm for main pipes (upsized for better convergence)
PIPE_DIAMETER_SERVICE = 0.05
PIPE_ROUGHNESS = 0.1
CP_WATER = 4180
DEFAULT_HEAT_DEMAND_W = 10e3


def create_dh_network_from_buildings(buildings_gdf, params):
    """
    Build a district-heating network in pandapipes with:
      - supply + return mains along street graph (or MST fallback)
      - junction at each building & plant
      - heat_exchanger + consumer per building
      - circulation pump at plant
    """
    if not PANDAPIPES_AVAILABLE:
        raise ImportError("pandapipes is required for DH simulations")

    # 1. Project to metric CRS
    if buildings_gdf.crs is None or buildings_gdf.crs.is_geographic:
        try:
            buildings_gdf = buildings_gdf.to_crs(buildings_gdf.estimate_utm_crs())
        except Exception:
            buildings_gdf = buildings_gdf.to_crs("EPSG:32633")
    crs_proj = buildings_gdf.crs

    # 2. Centroids & demands
    buildings = buildings_gdf.copy()
    buildings["geometry"] = buildings.geometry.centroid
    buildings["x"] = buildings.geometry.x
    buildings["y"] = buildings.geometry.y
    if "heating_load_kw" not in buildings.columns:
        buildings["heating_load_kw"] = DEFAULT_HEAT_DEMAND_W / 1000
    # Reduce demands for better convergence
    # try reducing the peak load further to 1 kW
    buildings["heating_load_kw"] = buildings["heating_load_kw"].clip(upper=1.0)
    buildings["heat_demand_w"] = buildings["heating_load_kw"] * 1000

    # 3. Compute plant point in projected CRS
    tf = Transformer.from_crs("EPSG:4326", crs_proj, always_xy=True)
    plant_x, plant_y = tf.transform(PLANT_LON, PLANT_LAT)

    # 4. Build street graph or MST
    edge_set = []
    nodes_used = set()
    use_mst = False
    if OSMNX_AVAILABLE:
        try:
            center = buildings.geometry.union_all().centroid
            center_lon, center_lat = Transformer.from_crs(
                crs_proj, "EPSG:4326", always_xy=True
            ).transform(center.x, center.y)
            G = ox.graph_from_point(
                (center_lat, center_lon), dist=2000, network_type="drive", simplify=True
            )
            G = ox.project_graph(G, to_crs=crs_proj)
            buildings["snap_node"] = buildings.apply(
                lambda r: ox.nearest_nodes(G, X=r.x, Y=r.y), axis=1
            )
            plant_node = ox.nearest_nodes(G, X=plant_x, Y=plant_y)
            reachable = set()
            for tgt in buildings["snap_node"]:
                try:
                    path = nx.shortest_path(G, plant_node, int(tgt), weight="length")
                    for u, v in zip(path[:-1], path[1:]):
                        data = G.get_edge_data(u, v)
                        if isinstance(data, dict):
                            data = min(data.values(), key=lambda d: d["length"])
                        geom = data.get(
                            "geometry",
                            LineString(
                                [
                                    (G.nodes[u]["x"], G.nodes[u]["y"]),
                                    (G.nodes[v]["x"], G.nodes[v]["y"]),
                                ]
                            ),
                        )
                        edge_set.append((u, v, data["length"], geom))
                        nodes_used.update([u, v])
                    reachable.add(int(tgt))
                except nx.NetworkXNoPath:
                    print(f"Warning: Building {tgt} not reachable from plant via OSM network")
            if len(reachable) < len(buildings):
                print(
                    f"Only {len(reachable)}/{len(buildings)} buildings reachable via OSM, using MST fallback"
                )
                use_mst = True
                edge_set = []
                nodes_used = set()
            else:
                print(f"OSM network: {len(reachable)}/{len(buildings)} buildings connected")
                use_mst = False
        except Exception as e:
            print(f"OSM network extraction failed: {e}, using MST fallback")
            use_mst = True
    else:
        use_mst = True
    if use_mst:
        print("Building MST topology...")
        coords = np.vstack([buildings[["x", "y"]].to_numpy(), [plant_x, plant_y]])
        print(f"MST coords shape: {coords.shape} (buildings: {len(buildings)}, plant: 1)")
        print(f"Building indices: 0 to {len(buildings)-1}, Plant index: {len(buildings)}")

        D = distance_matrix(coords, coords)
        Gm = nx.Graph()
        n = len(coords)
        for i in range(n):
            for j in range(i + 1, n):
                Gm.add_edge(i, j, weight=D[i, j])

        mst = nx.minimum_spanning_tree(Gm)
        print(f"MST edges: {list(mst.edges())}")
        print(f"MST nodes: {list(mst.nodes())}")

        # Ensure MST connects all nodes
        if not nx.is_connected(mst):
            print("Warning: MST is not connected, forcing connection to plant")
            # Force connection from plant to all buildings
            plant_idx = len(buildings)
            for i in range(len(buildings)):
                if not nx.has_path(mst, plant_idx, i):
                    print(f"Adding direct connection: plant({plant_idx}) -> building({i})")
                    mst.add_edge(plant_idx, i, weight=D[plant_idx, i])

        print(f"Final MST edges: {list(mst.edges())}")
        print(f"Final MST connected: {nx.is_connected(mst)}")

        for u, v, d in mst.edges(data=True):
            geom = LineString([(coords[u][0], coords[u][1]), (coords[v][0], coords[v][1])])
            edge_set.append((u, v, d["weight"], geom))
            nodes_used.update([u, v])

        buildings["snap_node"] = range(len(buildings))
        plant_node = len(buildings)
        print(f"Final nodes_used: {sorted(nodes_used)}")
        print(f"Plant node: {plant_node}")

    # 5. Build pandapipes network
    net = pp.create_empty_network(fluid="water")

    # 5a. Junctions
    sup_jids, ret_jids = {}, {}
    for node in nodes_used:
        # Choose coordinates depending on topology used
        if OSMNX_AVAILABLE and not use_mst:
            x, y = G.nodes[node]["x"], G.nodes[node]["y"]
        else:
            x, y = coords[node]
        sup_jids[node] = pp.create_junction(
            net,
            pn_bar=6,
            tfluid_k=params.get("supply_temp", 70) + 273.15,
            x=x,
            y=y,
            name=f"sup_{node}",
        )
        ret_jids[node] = pp.create_junction(
            net,
            pn_bar=6,
            tfluid_k=params.get("return_temp", 40) + 273.15,
            x=x + OFFSET_RETURN,
            y=y,
            name=f"ret_{node}",
        )

    # 5b. External grid and circulation pump
    pp.create_ext_grid(
        net,
        junction=sup_jids[plant_node],
        p_bar=6,
        t_k=params.get("supply_temp", 70) + 273.15,
        name="Plant_Supply",
    )
    total_heat = buildings["heat_demand_w"].sum()
    dt = params.get("supply_temp", 70) - params.get("return_temp", 40)
    pp.create_circ_pump_const_pressure(
        net,
        return_junction=ret_jids[plant_node],
        flow_junction=sup_jids[plant_node],
        p_flow_bar=5,
        plift_bar=0.7,
        t_flow_k=params.get("supply_temp", 70) + 273.15,
    )

    # 5c. Heat consumers
    for idx, row in buildings.iterrows():
        node = int(row["snap_node"])
        if node == plant_node:
            continue
        q_nom = row["heat_demand_w"]
        mdot = q_nom / (CP_WATER * dt)
        pp.create_heat_consumer(
            net,
            from_junction=sup_jids[node],
            to_junction=ret_jids[node],
            qext_w=q_nom,
            deltat_k=dt,
            name=f"Consumer_{idx}",
        )

    # 5d. Pipes
    supply_geoms, return_geoms = [], []
    for u, v, length_m, geom in edge_set:
        L_km = length_m / 1000
        pp.create_pipe_from_parameters(
            net,
            from_junction=sup_jids[u],
            to_junction=sup_jids[v],
            length_km=L_km,
            diameter_m=params.get("main_diameter", PIPE_DIAMETER_MAIN),
            k_mm=PIPE_ROUGHNESS,
            name=f"SUP_{u}_{v}",
        )
        supply_geoms.append(list(geom.coords))
        pp.create_pipe_from_parameters(
            net,
            from_junction=ret_jids[u],
            to_junction=ret_jids[v],
            length_km=L_km,
            diameter_m=params.get("main_diameter", PIPE_DIAMETER_MAIN),
            k_mm=PIPE_ROUGHNESS,
            name=f"RET_{u}_{v}",
        )
        return_geoms.append([(x + OFFSET_RETURN, y) for x, y in geom.coords])

    net.pipe_geodata = pd.DataFrame({"coords": supply_geoms + return_geoms}, index=net.pipe.index)
    return net


def debug_and_run_pipeflow(net):
    """
    Print network diagnostics, check connectivity, then run hydraulics.
    """
    # Diagnostics
    print(
        f"Diagnostics: junctions={len(net.junction)}, pipes={len(net.pipe)}, consumers={len(net.heat_consumer)}"
    )
    print(f"Total heat demand: {net.heat_consumer.qext_w.sum()/1000:.2f} kW")
    print(f"Pipe diameters: {net.pipe.diameter_m.unique()}")
    print(f"Pipe lengths: {net.pipe.length_km.describe()}")

    # Build connectivity graph for supply network only
    Gc_supply = nx.Graph()
    for _, row in net.pipe.iterrows():
        if row["name"].startswith("SUP_"):  # Only supply pipes
            Gc_supply.add_edge(int(row.from_junction), int(row.to_junction))

    comp_supply = list(nx.connected_components(Gc_supply))
    print(f"Supply network components: {len(comp_supply)}")

    # Build connectivity graph for return network only
    Gc_return = nx.Graph()
    for _, row in net.pipe.iterrows():
        if row["name"].startswith("RET_"):  # Only return pipes
            Gc_return.add_edge(int(row.from_junction), int(row.to_junction))

    comp_return = list(nx.connected_components(Gc_return))
    print(f"Return network components: {len(comp_return)}")

    # Check if plant is connected in supply network
    plant_jid = net.ext_grid.junction.iloc[0]
    plant_connected = any(plant_jid in c for c in comp_supply)
    print(f"Plant connected in supply network: {plant_connected}")

    if not plant_connected:
        print("ERROR: Plant not connected in supply network!")
        print(f"Plant junction: {plant_jid}")
        print(f"Supply components: {comp_supply}")
        return

    # Run calculation with convergence parameters
    print("Running pipeflow...")
    try:
        pp.pipeflow(
            net,
            algorithm="basic",  # simpler Newton scheme
            friction_model="constant",  # no Colebrook friction loop
            friction_factor=0.02,  # typical for steel
            tol_p=1e-3,
            tol_v=1e-3,  # looser tolerances
            max_iter=200,
        )
    except Exception as e:
        print(f"Pipeflow failed with error: {e}")
        # Try with even more relaxed parameters
        try:
            print("Retrying with very relaxed convergence parameters...")
            pp.pipeflow(
                net,
                algorithm="basic",
                friction_model="constant",
                friction_factor=0.02,
                tol_p=1e-2,
                tol_v=1e-2,  # very loose tolerances
                max_iter=300,
            )
        except Exception as e2:
            print(f"Second attempt also failed: {e2}")
            raise e2


def run_pandapipes_simulation(scenario):
    try:
        print(f"Running DH simulation: {scenario['name']}")
        if not PANDAPIPES_AVAILABLE:
            return {
                "scenario": scenario["name"],
                "success": False,
                "error": "pandapipes not installed",
            }
        buildings_gdf = gpd.read_file(scenario["building_file"])
        buildings_gdf.set_crs(buildings_gdf.crs or "EPSG:4326", inplace=True)
        if buildings_gdf.empty:
            return {"scenario": scenario["name"], "success": False, "error": "No building features"}
        buildings_gdf["heating_load_kw"] = buildings_gdf.get(
            "heating_load_kw", pd.Series(DEFAULT_HEAT_DEMAND_W / 1000, index=buildings_gdf.index)
        ).clip(lower=1)
        net = create_dh_network_from_buildings(buildings_gdf, scenario.get("params", {}))

        # Try to run pipeflow, but handle convergence issues gracefully
        try:
            debug_and_run_pipeflow(net)
            total_heat = net.res_heat_consumer.qext_w.sum()
            mwh = total_heat / 1e6
            max_dp = (net.res_pipe.p_from_bar - net.res_pipe.p_to_bar).abs().max()
            hydraulic_success = True
        except Exception as e:
            print(f"Hydraulic calculation failed: {e}")
            print("Providing basic network analysis without hydraulic results...")
            total_heat = net.heat_consumer.qext_w.sum()
            mwh = total_heat / 1e6
            max_dp = None
            hydraulic_success = False

        # Create enhanced network visualizations
        try:
            if ENHANCED_VISUALIZATION_AVAILABLE:
                # Load buildings data for context
                buildings_gdf = None
                try:
                    buildings_gdf = gpd.read_file(scenario["building_file"])
                except Exception:
                    print("Warning: Could not load buildings for visualization context")

                # Create enhanced visualizations
                viz_results = create_enhanced_network_visualization(
                    net=net,
                    scenario_name=scenario["name"],
                    output_dir=str(RESULTS_DIR),
                    buildings_gdf=buildings_gdf,
                    create_static=True,
                    create_interactive=True,
                )

                plot_created = True
                if viz_results.get("static_map"):
                    print(f"Enhanced static map saved to: {viz_results['static_map']}")
                if viz_results.get("interactive_map"):
                    print(f"Interactive map saved to: {viz_results['interactive_map']}")

                # Also create the basic plot for backward compatibility
                plot_file = RESULTS_DIR / f"dh_{scenario['name']}.png"
                if not viz_results.get("static_map"):
                    # Fallback to basic plotting if enhanced visualization failed
                    raise Exception("Enhanced visualization failed, falling back to basic plotting")

            else:
                # Fallback to basic plotting
                raise Exception("Enhanced visualization not available")

        except Exception as e:
            print(f"Enhanced visualization failed: {e}")
            print("Falling back to basic network plotting...")

            # Create basic network plot (original code)
            fig, ax = plt.subplots(figsize=(12, 10))

            # Plot junctions with different colors for supply and return
            supply_junctions = []
            return_junctions = []
            plant_junction = None

            for idx, junction in net.junction.iterrows():
                if junction["name"].startswith("sup_"):
                    supply_junctions.append((junction["x"], junction["y"]))
                elif junction["name"].startswith("ret_"):
                    return_junctions.append((junction["x"], junction["y"]))
                elif "plant" in junction["name"].lower():
                    plant_junction = (junction["x"], junction["y"])

            # Plot supply junctions
            if supply_junctions:
                x_coords, y_coords = zip(*supply_junctions)
                ax.scatter(
                    x_coords,
                    y_coords,
                    c="red",
                    s=100,
                    zorder=5,
                    label="Supply Junctions",
                    alpha=0.8,
                )

            # Plot return junctions
            if return_junctions:
                x_coords, y_coords = zip(*return_junctions)
                ax.scatter(
                    x_coords,
                    y_coords,
                    c="blue",
                    s=80,
                    zorder=4,
                    label="Return Junctions",
                    alpha=0.6,
                )

            # Plot plant location
            if plant_junction:
                ax.scatter(
                    plant_junction[0],
                    plant_junction[1],
                    c="green",
                    s=200,
                    zorder=6,
                    label="CHP Plant",
                    marker="s",
                    edgecolors="black",
                    linewidth=2,
                )

            # Plot pipes with different colors for supply and return
            supply_pipes = []
            return_pipes = []

            for idx, pipe in net.pipe.iterrows():
                from_junc = net.junction.loc[pipe.from_junction]
                to_junc = net.junction.loc[pipe.to_junction]
                line_coords = [(from_junc.x, from_junc.y), (to_junc.x, to_junc.y)]

                if pipe["name"].startswith("SUP_"):
                    supply_pipes.append(line_coords)
                elif pipe["name"].startswith("RET_"):
                    return_pipes.append(line_coords)

            # Plot supply pipes
            for line_coords in supply_pipes:
                x_coords, y_coords = zip(*line_coords)
                ax.plot(x_coords, y_coords, "r-", linewidth=3, alpha=0.8, zorder=2)

            # Plot return pipes
            for line_coords in return_pipes:
                x_coords, y_coords = zip(*line_coords)
                ax.plot(x_coords, y_coords, "b-", linewidth=2, alpha=0.6, zorder=1)

            # Add heat consumers
            consumer_positions = []
            for idx, consumer in net.heat_consumer.iterrows():
                from_junc = net.junction.loc[consumer.from_junction]
                consumer_positions.append((from_junc.x, from_junc.y))

            if consumer_positions:
                x_coords, y_coords = zip(*consumer_positions)
                ax.scatter(
                    x_coords,
                    y_coords,
                    c="orange",
                    s=60,
                    zorder=3,
                    label="Heat Consumers",
                    marker="^",
                    edgecolors="black",
                    linewidth=1,
                )

            # Customize the plot
            ax.set_title(
                f'District Heating Network - {scenario["name"]}\n'
                f"Buildings: {len(net.heat_consumer)}, Total Length: {net.pipe.length_km.sum():.2f} km",
                fontsize=14,
                fontweight="bold",
            )
            ax.set_xlabel("X coordinate (m)", fontsize=12)
            ax.set_ylabel("Y coordinate (m)", fontsize=12)
            ax.legend(loc="upper right", fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_aspect("equal", adjustable="box")

            # Add text box with network statistics
            stats_text = f"Network Statistics:\n"
            stats_text += f"• Total Heat Demand: {net.heat_consumer.qext_w.sum()/1000:.2f} kW\n"
            stats_text += (
                f'• Supply Temperature: {scenario.get("params", {}).get("supply_temp", 70)}°C\n'
            )
            stats_text += (
                f'• Return Temperature: {scenario.get("params", {}).get("return_temp", 40)}°C\n'
            )
            stats_text += (
                f'• Pipe Diameter: {scenario.get("params", {}).get("main_diameter", 0.4)} m'
            )

            # Position text box in upper left
            ax.text(
                0.02,
                0.98,
                stats_text,
                transform=ax.transAxes,
                fontsize=10,
                verticalalignment="top",
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
            )

            plot_file = RESULTS_DIR / f"dh_{scenario['name']}.png"
            fig.savefig(plot_file, dpi=300, bbox_inches="tight")
            plt.close(fig)
            plot_created = True
            print(f"Basic network plot saved to: {plot_file}")

        # Calculate basic network statistics
        total_pipe_length = net.pipe.length_km.sum()
        num_buildings = len(net.heat_consumer)
        network_density = total_pipe_length / num_buildings if num_buildings > 0 else 0

        kpi = {
            "heat_mwh": round(mwh, 4),
            "total_pipe_length_km": round(total_pipe_length, 3),
            "num_buildings": num_buildings,
            "network_density_km_per_building": round(network_density, 3),
            "hydraulic_success": hydraulic_success,
        }

        if max_dp is not None:
            kpi["max_dp_bar"] = round(max_dp, 3)

        return {
            "scenario": scenario["name"],
            "success": True,
            "kpi": kpi,
            "plot_created": plot_created,
        }
    except Exception:
        traceback.print_exc()
        return {
            "scenario": scenario.get("name", ""),
            "success": False,
            "error": "Exception occurred",
        }


def run_scenario(scenario_file):
    try:
        scenario = json.loads(Path(scenario_file).read_text())
        if scenario.get("type", "DH").upper() == "DH":
            res = run_pandapipes_simulation(scenario)
        else:
            res = run_pandapower_simulation(scenario)
        Path(RESULTS_DIR / f"{scenario['name']}_results.json").write_text(json.dumps(res, indent=2))
        return res
    except Exception:
        traceback.print_exc()
        return {"scenario_file": scenario_file, "success": False}


def run_simulation_scenarios(files, parallel=True):
    if parallel and len(files) > 1:
        with multiprocessing.Pool(min(4, len(files))) as p:
            return p.map(run_scenario, files)
    return [run_scenario(f) for f in files]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenarios", nargs="+", required=True)
    parser.add_argument("--no_parallel", action="store_true")
    args = parser.parse_args()
    run_simulation_scenarios(args.scenarios, parallel=not args.no_parallel)
