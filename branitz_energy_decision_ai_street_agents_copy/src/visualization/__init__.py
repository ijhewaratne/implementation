"""
Visualization module for color-coded cascading network visualizations.

This module provides functions for creating static and interactive visualizations
of district heating (DH) and heat pump (HP) networks with color-coded gradients.
"""

from .colormaps import (
    NETWORK_COLORS,
    COLORMAPS,
    get_temperature_color,
    get_pressure_color,
    get_voltage_color,
    get_loading_color,
    get_heat_demand_color,
    get_service_length_color,
)

from .network_maps import NetworkMapGenerator
from .interactive_maps import InteractiveMapGenerator
from .config_loader import VisualizationConfig, get_visualization_config

__all__ = [
    'NETWORK_COLORS',
    'COLORMAPS',
    'get_temperature_color',
    'get_pressure_color',
    'get_voltage_color',
    'get_loading_color',
    'get_heat_demand_color',
    'get_service_length_color',
    'NetworkMapGenerator',
    'InteractiveMapGenerator',
    'VisualizationConfig',
    'get_visualization_config',
]

