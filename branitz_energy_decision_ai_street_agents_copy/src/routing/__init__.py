"""
Advanced Network Routing Module

This module provides sophisticated routing algorithms for district heating networks.

Migrated from street_final_copy_3:
- Shortest path routing with virtual nodes
- Street network construction
- Graph algorithms and utilities
- Network optimization

Classes:
- StreetNetworkBuilder: Build NetworkX graphs from street data

Functions:
- Shortest path algorithms
- Virtual node insertion
- Network validation
- Route optimization
- MST construction
- Service connection calculation
"""

from .network_builder import StreetNetworkBuilder
from .shortest_path import (
    transform_plant_coordinates,
    create_street_network_with_virtual_nodes,
    find_shortest_paths_from_plant,
    analyze_routing_results,
    create_path_geometries,
    plot_routing_results,
    save_routing_results,
)
from .graph_utils import (
    create_mst_network_from_buildings,
    calculate_service_connections,
    plot_mst_network,
    plot_service_connections,
    save_service_connections,
)
from .snapping import (
    BuildingStreetSnapper,
    snap_buildings_to_street_segments,
    snap_plant_to_network_node,
    save_snapping_results,
    visualize_snapping_results,
)
from .dual_pipe import build_dual_pipe_topology

__all__ = [
    'StreetNetworkBuilder',
    'transform_plant_coordinates',
    'create_street_network_with_virtual_nodes',
    'find_shortest_paths_from_plant',
    'analyze_routing_results',
    'create_path_geometries',
    'plot_routing_results',
    'save_routing_results',
    'create_mst_network_from_buildings',
    'calculate_service_connections',
    'plot_mst_network',
    'plot_service_connections',
    'save_service_connections',
    'BuildingStreetSnapper',
    'snap_buildings_to_street_segments',
    'snap_plant_to_network_node',
    'save_snapping_results',
    'visualize_snapping_results',
    'build_dual_pipe_topology',
]

