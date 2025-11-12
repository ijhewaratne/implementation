"""
Helpers for working with Branitz LV network nodes and ways.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in meters."""
    R = 6371000.0
    t1, t2 = math.radians(lat1), math.radians(lat2)
    dlat = t2 - t1
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(t1) * math.cos(t2) * math.sin(dlon / 2.0) ** 2
    return 2.0 * R * math.asin(math.sqrt(a))


def load_nodes_ways(path: Path | str) -> Tuple[Dict[int, dict], List[dict]]:
    """
    Load LV nodes and ways from the Branitz JSON export.

    Returns:
        (id_to_node, ways) where id_to_node maps node id to dict with lat/lon.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    nodes = payload.get("nodes", [])
    ways = payload.get("ways", [])

    id_to_node: Dict[int, dict] = {}
    for node in nodes:
        try:
            node_id = int(node["id"])
            id_to_node[node_id] = {
                "id": node_id,
                "lat": float(node["lat"]),
                "lon": float(node["lon"]),
                "tags": node.get("tags", {}),
            }
        except (KeyError, TypeError, ValueError):
            continue

    # Normalize ways to ensure node references are ints
    normalized_ways: List[dict] = []
    for way in ways:
        try:
            nodes_seq = [int(nid) for nid in way.get("nodes", [])]
        except Exception:
            continue
        if len(nodes_seq) < 2:
            continue

        normalized_ways.append(
            {
                "id": way.get("id"),
                "nodes": nodes_seq,
                "tags": way.get("tags", {}),
            }
        )

    return id_to_node, normalized_ways


def nearest_node_id(
    id_to_node: Dict[int, dict],
    lat: float,
    lon: float,
    candidates: Iterable[int] | None = None,
) -> Tuple[int | None, float]:
    """
    Find the nearest node to the given latitude/longitude.

    Args:
        id_to_node: Mapping of node id -> data with lat/lon.
        lat: Latitude in degrees.
        lon: Longitude in degrees.
        candidates: Optional iterable of node ids to restrict the search.

    Returns:
        (node_id, distance_m). If no node found, returns (None, inf).
    """
    best_id = None
    best_dist = float("inf")

    iterable = candidates if candidates is not None else id_to_node.keys()

    for node_id in iterable:
        node = id_to_node.get(node_id)
        if not node:
            continue
        d = haversine_m(lat, lon, node.get("lat"), node.get("lon"))
        if d < best_dist:
            best_dist = d
            best_id = node_id

    return best_id, best_dist


__all__ = ["load_nodes_ways", "nearest_node_id", "haversine_m"]


