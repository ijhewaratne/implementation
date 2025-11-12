"""
Branitz DH Core Module

Digital Humanities pipeline framework with data processing, visualization, and cost tracking.
"""

from .config import Config, DHDesign, Paths
from .data_adapters import DataAdapter, project_to_meters, load_network_from_json, load_addresses_geojson, load_gebaeudeanalyse, load_uwerte
from .ppipe_builder import build_and_run, _unique_endpoints, _add_junctions
from .viz import Visualizer, gradient_layer, repaint_with_results, paint_supply_return
from .costs import CostCalculator, CostEntry
from .load_binding import load_design_loads_csv, match_loads_to_addresses_by_roundrobin
from .routing_osm import build_street_graph_around, snap_points_to_graph, _steiner_tree, _tree_to_gdf, route_pipes_from_osm

__version__ = "1.0.0"
__author__ = "Branitz DH Team"

__all__ = [
    "Config",
    "DHDesign",
    "Paths",
    "DataAdapter", 
    "project_to_meters",
    "load_network_from_json",
    "load_addresses_geojson",
    "load_gebaeudeanalyse",
    "load_uwerte",
    "build_and_run",
    "_unique_endpoints",
    "_add_junctions",
    "Visualizer",
    "gradient_layer",
    "repaint_with_results",
    "paint_supply_return",
    "CostCalculator",
    "CostEntry",
    "load_design_loads_csv",
    "match_loads_to_addresses_by_roundrobin",
    "build_street_graph_around",
    "snap_points_to_graph",
    "_steiner_tree",
    "_tree_to_gdf",
    "route_pipes_from_osm"
]
