"""
Advanced color gradient functions for cascading visualizations.

This module provides functions for creating smooth color gradients along
network elements (pipes, lines) to visualize cascading effects like:
- Temperature drop along district heating pipes
- Pressure drop along network paths
- Voltage drop along electrical lines
"""

import numpy as np
import matplotlib.colors as mcolors
from matplotlib import cm
from typing import List, Tuple, Optional

from .colormaps import NETWORK_COLORS, COLORMAPS


def create_pipe_temperature_gradient(
    coords: List[Tuple[float, float]],
    temp_start: float,
    temp_end: float,
    colormap: str = 'hot'
) -> List[Tuple[Tuple[float, float], Tuple[float, float], str]]:
    """
    Create temperature gradient segments along a pipe.
    
    Creates segments with cascading colors showing temperature drop
    from start to end of pipe (e.g., 85°C → 75°C).
    
    Args:
        coords: List of (lat, lon) coordinates defining pipe path
        temp_start: Starting temperature (°C)
        temp_end: Ending temperature (°C)
        colormap: Matplotlib colormap name
    
    Returns:
        List of (start_coord, end_coord, color_hex) tuples for each segment
    
    Example:
        >>> coords = [(51.76, 14.34), (51.76, 14.35), (51.76, 14.36)]
        >>> segments = create_pipe_temperature_gradient(coords, 85, 75)
        >>> # Returns colored segments: red → darker red
    """
    if len(coords) < 2:
        return []
    
    cmap = cm.get_cmap(colormap)
    segments = []
    
    # Create temperature values for each segment
    num_segments = len(coords) - 1
    temps = np.linspace(temp_start, temp_end, num_segments + 1)
    
    # Normalize temperatures for colormap
    norm = mcolors.Normalize(vmin=min(temp_start, temp_end), vmax=max(temp_start, temp_end))
    
    # Create colored segments
    for i in range(num_segments):
        start_coord = coords[i]
        end_coord = coords[i + 1]
        segment_temp = temps[i]
        
        # Get color for this temperature
        rgba = cmap(norm(segment_temp))
        color_hex = mcolors.to_hex(rgba)
        
        segments.append((start_coord, end_coord, color_hex))
    
    return segments


def create_pressure_gradient_path(
    network_path: List[dict],
    pressure_start: float,
    pressure_end: float,
    colormap: str = 'RdYlGn'
) -> List[Tuple[dict, str]]:
    """
    Create pressure gradient along a network path.
    
    Shows pressure drop cascade from source to consumers.
    High pressure = green, low pressure = red.
    
    Args:
        network_path: List of path dictionaries with 'coords' and 'id'
        pressure_start: Starting pressure (bar)
        pressure_end: Ending pressure (bar)
        colormap: Matplotlib colormap name
    
    Returns:
        List of (path_dict, color_hex) tuples
    """
    if not network_path:
        return []
    
    cmap = cm.get_cmap(colormap)
    num_segments = len(network_path)
    
    # Calculate pressure at each point
    pressures = np.linspace(pressure_start, pressure_end, num_segments)
    
    # Normalize (higher pressure = higher value in colormap)
    norm = mcolors.Normalize(vmin=pressure_end, vmax=pressure_start)
    
    colored_path = []
    for i, path_segment in enumerate(network_path):
        pressure = pressures[i]
        rgba = cmap(norm(pressure))
        color_hex = mcolors.to_hex(rgba)
        colored_path.append((path_segment, color_hex))
    
    return colored_path


def create_voltage_gradient(
    bus_voltages: List[float],
    colormap: str = 'RdYlGn'
) -> List[str]:
    """
    Create voltage-based color gradient for electrical network buses.
    
    Uses traffic light colors based on voltage level:
    - Green: Normal (0.95-1.05 pu)
    - Yellow/Orange: Warning
    - Red: Violation
    
    Args:
        bus_voltages: List of bus voltages in per-unit
        colormap: Matplotlib colormap name (default: 'RdYlGn')
    
    Returns:
        List of hex color strings, one per bus
    """
    from .colormaps import get_voltage_color
    
    colors = [get_voltage_color(v) for v in bus_voltages]
    return colors


def interpolate_gradient(
    values: np.ndarray,
    coords: np.ndarray,
    colormap: str,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None
) -> Tuple[List[str], List[float]]:
    """
    Create interpolated color gradient for visualization.
    
    Args:
        values: Array of values to visualize
        coords: Array of coordinates (N x 2)
        colormap: Matplotlib colormap name
        vmin: Minimum value for normalization
        vmax: Maximum value for normalization
    
    Returns:
        Tuple of (colors, normalized_values)
    """
    if vmin is None:
        vmin = values.min()
    if vmax is None:
        vmax = values.max()
    
    cmap = cm.get_cmap(colormap)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    
    colors = [mcolors.to_hex(cmap(norm(v))) for v in values]
    normalized = (values - vmin) / (vmax - vmin) if (vmax - vmin) > 0 else np.zeros_like(values)
    
    return colors, normalized.tolist()


def create_heatmap_colors(
    grid_values: np.ndarray,
    colormap: str = 'hot',
    vmin: Optional[float] = None,
    vmax: Optional[float] = None
) -> np.ndarray:
    """
    Create 2D heatmap colors from grid values.
    
    Args:
        grid_values: 2D array of values
        colormap: Matplotlib colormap name
        vmin: Minimum value for normalization
        vmax: Maximum value for normalization
    
    Returns:
        2D array of RGBA colors
    """
    if vmin is None:
        vmin = grid_values.min()
    if vmax is None:
        vmax = grid_values.max()
    
    cmap = cm.get_cmap(colormap)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    
    colors = cmap(norm(grid_values))
    return colors


def blend_colors(color1: str, color2: str, ratio: float = 0.5) -> str:
    """
    Blend two colors together.
    
    Args:
        color1: First hex color
        color2: Second hex color
        ratio: Blend ratio (0=color1, 1=color2)
    
    Returns:
        Blended hex color
    """
    rgb1 = mcolors.hex2color(color1)
    rgb2 = mcolors.hex2color(color2)
    
    blended = tuple(
        rgb1[i] * (1 - ratio) + rgb2[i] * ratio
        for i in range(3)
    )
    
    return mcolors.to_hex(blended)


def get_cascading_opacity(
    position: int,
    total_positions: int,
    opacity_start: float = 1.0,
    opacity_end: float = 0.5
) -> float:
    """
    Calculate cascading opacity for visual depth effect.
    
    Creates opacity gradient from start to end (e.g., 1.0 → 0.5).
    
    Args:
        position: Current position in sequence (0-based)
        total_positions: Total number of positions
        opacity_start: Starting opacity
        opacity_end: Ending opacity
    
    Returns:
        Opacity value (0.0-1.0)
    """
    if total_positions <= 1:
        return opacity_start
    
    ratio = position / (total_positions - 1)
    opacity = opacity_start * (1 - ratio) + opacity_end * ratio
    
    return max(0.0, min(1.0, opacity))


def create_diverging_gradient(
    values: np.ndarray,
    center_value: float,
    colormap: str = 'RdBu_r'
) -> List[str]:
    """
    Create diverging color gradient centered on a value.
    
    Useful for showing deviations from normal (e.g., voltage from 1.0 pu).
    
    Args:
        values: Array of values
        center_value: Center point for divergence
        colormap: Matplotlib diverging colormap name
    
    Returns:
        List of hex color strings
    """
    # Calculate symmetric range around center
    max_deviation = max(abs(values.max() - center_value), abs(values.min() - center_value))
    vmin = center_value - max_deviation
    vmax = center_value + max_deviation
    
    cmap = cm.get_cmap(colormap)
    norm = mcolors.TwoSlopeNorm(vmin=vmin, vcenter=center_value, vmax=vmax)
    
    colors = [mcolors.to_hex(cmap(norm(v))) for v in values]
    return colors


# ============================================================================
# Specialized Gradient Functions
# ============================================================================

def create_dh_supply_gradient(
    pipe_coords: List[Tuple[float, float]],
    supply_temp_start: float = 85,
    supply_temp_end: float = 80
) -> List[Tuple[Tuple[float, float], Tuple[float, float], str]]:
    """
    Create temperature gradient for DH supply pipe (hot -> cooler).
    
    Uses 'hot' colormap: bright red -> darker red.
    """
    return create_pipe_temperature_gradient(
        pipe_coords,
        supply_temp_start,
        supply_temp_end,
        colormap='hot'
    )


def create_dh_return_gradient(
    pipe_coords: List[Tuple[float, float]],
    return_temp_start: float = 55,
    return_temp_end: float = 50
) -> List[Tuple[Tuple[float, float], Tuple[float, float], str]]:
    """
    Create temperature gradient for DH return pipe (cool -> cooler).
    
    Uses 'cool' colors: blue shades.
    """
    return create_pipe_temperature_gradient(
        pipe_coords,
        return_temp_start,
        return_temp_end,
        colormap='Blues_r'
    )


def create_hp_voltage_cascade(
    bus_ids: List[str],
    voltages_pu: List[float]
) -> dict:
    """
    Create voltage cascade for HP network buses.
    
    Returns dictionary mapping bus_id to color based on voltage level.
    """
    from .colormaps import get_voltage_color
    
    cascade = {}
    for bus_id, voltage in zip(bus_ids, voltages_pu):
        cascade[bus_id] = get_voltage_color(voltage)
    
    return cascade

