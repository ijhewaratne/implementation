"""Utilities for constructing dual-pipe district heating topologies."""

from __future__ import annotations

from typing import Dict, Any, Optional, Tuple, List

import math
import networkx as nx
from shapely.geometry import LineString, Point

TARGET_CRS = "EPSG:32633"
TOLERANCE = 1e-6


def _round_coord(coord: Tuple[float, float]) -> Tuple[float, float]:
    return (round(float(coord[0]), 6), round(float(coord[1]), 6))


def _ensure_graph_connectivity(G: nx.Graph) -> None:
    if nx.is_connected(G):
        return

    components = [set(comp) for comp in nx.connected_components(G)]
    if not components:
        return

    main_component = components[0]

    for comp in components[1:]:
        min_distance = float("inf")
        best_pair = None

        for node1 in main_component:
            for node2 in comp:
                dist = Point(node1).distance(Point(node2))
                if dist < min_distance:
                    min_distance = dist
                    best_pair = (node1, node2)

        if best_pair is None:
            continue

        u, v = best_pair
        line = LineString([u, v])
        attrs = {
            "weight": float(line.length),
            "geometry": line,
            "street_id": "connectivity_fix",
            "street_name": "Connectivity Fix",
            "highway_type": "service",
        }
        G.add_edge(u, v, **attrs)
        main_component.update(comp)


def _insert_point_on_graph(
    G: nx.Graph,
    point: Point,
    node_attrs: Optional[Dict[str, Any]] = None,
) -> Tuple[Tuple[float, float], Dict[str, Any]]:
    point_coords = _round_coord((point.x, point.y))

    if point_coords in G:
        if node_attrs:
            G.nodes[point_coords].update(node_attrs)
        return point_coords, {}

    min_distance = float("inf")
    best_edge = None
    best_data = None

    for u, v, data in G.edges(data=True):
        line: LineString = data["geometry"]
        distance = line.distance(point)
        if distance < min_distance:
            min_distance = distance
            best_edge = (u, v)
            best_data = data

    if best_edge is None or best_data is None:
        raise ValueError("Unable to locate edge for inserting point on graph.")

    u, v = best_edge

    # Handle points that already coincide with an existing node
    if min_distance < TOLERANCE:
        if Point(u).distance(point) < TOLERANCE:
            if node_attrs:
                G.nodes[u].update(node_attrs)
            return u, best_data
        if Point(v).distance(point) < TOLERANCE:
            if node_attrs:
                G.nodes[v].update(node_attrs)
            return v, best_data

    line: LineString = best_data["geometry"]
    if line.length < TOLERANCE:
        # Degenerate edge, attach to u
        if node_attrs:
            G.nodes[u].update(node_attrs)
        return u, best_data

    G.remove_edge(u, v)

    point_coords = _round_coord((point.x, point.y))
    attrs_u = best_data.copy()
    attrs_v = best_data.copy()

    line_u = LineString([u, point_coords])
    line_v = LineString([point_coords, v])

    attrs_u["geometry"] = line_u
    attrs_u["weight"] = float(line_u.length)

    attrs_v["geometry"] = line_v
    attrs_v["weight"] = float(line_v.length)

    if point_coords not in G:
        G.add_node(point_coords, **(node_attrs or {}))
    else:
        if node_attrs:
            G.nodes[point_coords].update(node_attrs)

    G.add_edge(u, point_coords, **attrs_u)
    G.add_edge(point_coords, v, **attrs_v)

    return point_coords, best_data


def _build_street_graph(streets_gdf) -> nx.Graph:
    G = nx.Graph()

    for idx, row in streets_gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue

        coords: List[Tuple[float, float]] = list(geom.coords)
        if len(coords) < 2:
            continue

        for i in range(len(coords) - 1):
            u = _round_coord(coords[i])
            v = _round_coord(coords[i + 1])
            if u == v:
                continue

            line = LineString([u, v])
            weight = float(line.length)
            edge_attrs = {
                "weight": weight,
                "geometry": line,
                "street_id": row.get("osmid", idx),
                "street_name": row.get("name") or f"Street_{idx}",
                "highway_type": row.get("highway", "residential"),
            }
            if G.has_edge(u, v):
                existing_weight = G[u][v]["weight"]
                if weight < existing_weight:
                    G[u][v] = edge_attrs
            else:
                G.add_edge(u, v, **edge_attrs)

    _ensure_graph_connectivity(G)
    return G


def _prepare_connections_df(connections_df) -> List[Dict[str, Any]]:
    if connections_df is None:
        return []
    return connections_df.to_dict(orient="records")


def build_dual_pipe_topology(
    buildings_gdf,
    streets_gdf,
    plant_connection: Dict[str, float],
    supply_temp: float,
    return_temp: float,
    supply_pressure: float,
    analysis: Optional[Dict[str, Any]] = None,
    connections_df=None,
) -> Dict[str, Any]:
    """Construct a dual supply/return pipe topology following street geometry."""

    if buildings_gdf is None or buildings_gdf.empty:
        raise ValueError("No buildings provided for dual-pipe topology")
    if streets_gdf is None or streets_gdf.empty:
        raise ValueError("No streets provided for dual-pipe topology")

    network_data: Dict[str, Any] = {
        "junctions": [],
        "pipes": [],
        "consumers": [],
        "stats": {},
    }

    plant_x = float(plant_connection["plant_x"])
    plant_y = float(plant_connection["plant_y"])

    street_graph = _build_street_graph(streets_gdf)

    plant_point = Point(plant_x, plant_y)
    plant_node, _ = _insert_point_on_graph(
        street_graph,
        plant_point,
        {"node_type": "plant", "name": "CHP_Plant"},
    )

    service_records = _prepare_connections_df(connections_df)
    service_nodes = []

    for record in service_records:
        point = Point(record["connection_point_x"], record["connection_point_y"])
        node_attrs = {
            "node_type": "service",
            "building_id": record.get("building_id"),
        }
        inserted_node, edge_meta = _insert_point_on_graph(street_graph, point, node_attrs)
        service_nodes.append(
            {
                "building_id": record.get("building_id"),
                "graph_node": inserted_node,
                "edge_meta": edge_meta or {},
                "record": record,
            }
        )

    supply_segments: List[Dict[str, Any]] = []
    return_segments: List[Dict[str, Any]] = []
    unreachable_buildings: List[Any] = []

    for service in service_nodes:
        building_id = service["building_id"]
        node = service["graph_node"]

        try:
            path = nx.shortest_path(street_graph, plant_node, node, weight="weight")
        except nx.NetworkXNoPath:
            unreachable_buildings.append(building_id)
            continue

        if len(path) < 2:
            continue

        # Supply segments
        for start, end in zip(path[:-1], path[1:]):
            data = street_graph.get_edge_data(start, end)
            geometry: LineString = data["geometry"]
            coords = [(float(x), float(y)) for x, y in geometry.coords]
            supply_segments.append(
                {
                    "id": f"SUP_{building_id}_{len(supply_segments)}",
                    "coords": coords,
                    "type": "supply",
                    "length_m": float(data["weight"]),
                    "street_id": data.get("street_id"),
                    "street_name": data.get("street_name"),
                    "highway_type": data.get("highway_type"),
                    "building_id": building_id,
                    "from_node": start,
                    "to_node": end,
                    "temperature_c": supply_temp,
                    "pressure_bar": supply_pressure,
                    "flow_direction": "plant_to_building",
                }
            )

        # Return segments (reverse path)
        reversed_path = list(reversed(path))
        for start, end in zip(reversed_path[:-1], reversed_path[1:]):
            data = street_graph.get_edge_data(start, end)
            geometry: LineString = data["geometry"]
            coords = [(float(x), float(y)) for x, y in geometry.coords][::-1]
            return_segments.append(
                {
                    "id": f"RET_{building_id}_{len(return_segments)}",
                    "coords": coords,
                    "type": "return",
                    "length_m": float(data["weight"]),
                    "street_id": data.get("street_id"),
                    "street_name": data.get("street_name"),
                    "highway_type": data.get("highway_type"),
                    "building_id": building_id,
                    "from_node": start,
                    "to_node": end,
                    "temperature_c": return_temp,
                    "pressure_bar": max(supply_pressure - 0.3, 1.0),
                    "flow_direction": "building_to_plant",
                }
            )

    supply_length = sum(seg["length_m"] for seg in supply_segments)
    return_length = sum(seg["length_m"] for seg in return_segments)

    # Prepare service export with legacy-compatible columns
    service_export = []
    for service in service_nodes:
        record = service["record"]
        edge_meta = service["edge_meta"]
        base_entry = {
            "building_id": record.get("building_id"),
            "building_x": record.get("building_x"),
            "building_y": record.get("building_y"),
            "connection_x": record.get("connection_point_x"),
            "connection_y": record.get("connection_point_y"),
            "distance_to_street": record.get("distance_to_street"),
            "street_segment_id": edge_meta.get("street_id", record.get("street_segment_id")),
            "street_name": edge_meta.get("street_name", record.get("street_name")),
            "highway_type": edge_meta.get("highway_type", record.get("highway_type")),
            "heating_load_kw": record.get("heating_load_kw", 0.0),
            "follows_street": True,
            "connected_to_supply_pipe": True,
            "connected_to_return_pipe": True,
        }
        supply_entry = base_entry.copy()
        supply_entry.update(
            {
                "pipe_type": "supply_service",
                "temperature_c": supply_temp,
                "flow_direction": "main_to_building",
            }
        )
        return_entry = base_entry.copy()
        return_entry.update(
            {
                "pipe_type": "return_service",
                "temperature_c": return_temp,
                "flow_direction": "building_to_main",
            }
        )
        service_export.extend([supply_entry, return_entry])

    # Junction & consumer metadata (plant + building centroids)
    building_id_col = "GebaeudeID" if "GebaeudeID" in buildings_gdf.columns else "building_id"
    junctions = []
    consumers = []
    junction_lookup: Dict[int, Dict[str, Any]] = {}

    plant_junction = {
        "id": 0,
        "name": "CHP_Plant",
        "type": "plant",
        "x": plant_x,
        "y": plant_y,
        "temperature": supply_temp,
        "pressure": supply_pressure,
    }
    junctions.append(plant_junction)
    junction_lookup[0] = plant_junction

    for idx_enum, (idx, building) in enumerate(buildings_gdf.iterrows(), start=1):
        centroid = building.geometry.centroid
        building_id = building.get(building_id_col, idx)
        heating_kw = float(building.get("heating_load_kw", 0.0) or 0.0)
        junction = {
            "id": idx_enum,
            "name": f"building_{building_id}",
            "type": "consumer",
            "x": float(centroid.x),
            "y": float(centroid.y),
            "building_id": building_id,
            "heating_load_kw": heating_kw,
            "temperature": supply_temp,
            "pressure": supply_pressure,
        }
        junctions.append(junction)
        junction_lookup[idx_enum] = junction
        consumers.append(
            {
                "id": building_id,
                "name": f"consumer_{building_id}",
                "junction_id": idx_enum,
                "heat_demand_kw": heating_kw,
                "temperature": supply_temp,
                "pressure_bar": supply_pressure,
            }
        )

    network_data["junctions"] = junctions
    network_data["consumers"] = consumers
    network_data["plant"] = plant_junction
    network_data["pipes"] = supply_segments + return_segments
    network_data["service_connections"] = service_export

    service_lengths = [
        entry.get("distance_to_street", 0.0) or 0.0 for entry in service_export if entry["pipe_type"] == "supply_service"
    ]
    total_service_length = float(sum(service_lengths) * 2.0)
    supply_service_length = float(sum(service_lengths))
    return_service_length = float(sum(service_lengths))
    avg_service_length = float(sum(service_lengths) / len(service_lengths)) if service_lengths else 0.0
    max_service_length = float(max(service_lengths)) if service_lengths else 0.0

    total_heat_kw = sum(consumer.get("heat_demand_kw", 0.0) or 0.0 for consumer in consumers)
    total_heat_mwh = (total_heat_kw * 8760) / 1000 if total_heat_kw else 0.0
    total_main_length = supply_length + return_length
    total_pipe_length = total_main_length + total_service_length
    num_buildings = len(consumers)

    unique_supply_segments = len({tuple(sorted((seg["from_node"], seg["to_node"]))) for seg in supply_segments})
    unique_return_segments = len({tuple(sorted((seg["from_node"], seg["to_node"]))) for seg in return_segments})

    network_stats = {
        "total_supply_length_m": float(supply_length),
        "total_return_length_m": float(return_length),
        "total_supply_length_km": float(supply_length / 1000),
        "total_return_length_km": float(return_length / 1000),
        "total_main_length_km": float(total_main_length / 1000),
        "total_service_length_m": total_service_length,
        "supply_service_length_m": supply_service_length,
        "return_service_length_m": return_service_length,
        "avg_service_length_m": avg_service_length,
        "max_service_length_m": max_service_length,
        "unique_supply_segments": unique_supply_segments,
        "unique_return_segments": unique_return_segments,
        "num_junctions": len(junctions),
        "num_pipes": len(supply_segments) + len(return_segments),
        "success_rate": float(analysis.get("success_rate", 0.0) if analysis else 0.0),
        "num_buildings": num_buildings,
        "total_heat_demand_kw": float(total_heat_kw),
        "total_heat_demand_mwh": float(total_heat_mwh),
        "network_density_km_per_building": float((total_main_length / 1000) / num_buildings) if num_buildings else 0.0,
        "total_pipe_length_km": float(total_pipe_length / 1000),
        "service_connections": num_buildings * 2,
        "dual_pipe_system": True,
        "street_based_routing": True,
        "all_connections_follow_streets": True,
        "no_direct_connections": True,
        "supply_temperature_c": supply_temp,
        "return_temperature_c": return_temp,
    }

    network_data["stats"] = network_stats

    if analysis is not None:
        analysis.update(
            {
                "total_main_pipe_length": total_main_length,
                "total_service_pipe_length": total_service_length,
                "total_network_length": total_main_length + total_service_length,
                "avg_main_pipe_length": total_main_length / max(num_buildings, 1),
            }
        )

    if unreachable_buildings:
        network_data["unreachable_buildings"] = unreachable_buildings

    return network_data

