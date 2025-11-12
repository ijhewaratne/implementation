"""
Helpers for loading LV network nodes/ways data.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, Tuple, List, Any


@lru_cache(maxsize=4)
def load_nodes_ways(path: Path | str) -> Tuple[Dict[int, Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load LV network nodes and ways from JSON file.

    Returns:
        A tuple of (id_to_node, ways) where:
            id_to_node: dict mapping node id -> node dict with lat/lon
            ways: list of way dicts with nodes[] and tags
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Nodes/ways JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    ways = data.get("ways", [])

    id_to_node: Dict[int, Dict[str, Any]] = {}
    for node in nodes:
        try:
            node_id = int(node.get("id"))
        except (TypeError, ValueError):
            continue
        id_to_node[node_id] = node

    return id_to_node, ways


