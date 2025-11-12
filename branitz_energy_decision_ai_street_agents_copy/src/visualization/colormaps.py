"""
Color palette definitions and gradient functions for network visualizations.

This module provides:
- Standard color palettes for network components
- Gradient color functions for temperature, pressure, voltage
- Matplotlib colormap presets for different visualization types
"""

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib import cm
import numpy as np

# ============================================================================
# Network Component Color Definitions
# ============================================================================

NETWORK_COLORS = {
    # District Heating Network (Temperature-based)
    'supply_pipe': '#DC143C',        # Crimson (hot)
    'return_pipe': '#4682B4',        # SteelBlue (cold)
    'supply_junction': '#DC143C',    # Crimson
    'return_junction': '#4682B4',    # SteelBlue
    'heat_consumer': '#FF8C00',      # DarkOrange
    'chp_plant': '#228B22',          # ForestGreen
    'service_connection': '#FFA500', # Orange
    
    # Heat Pump Network (Voltage-based)
    'lv_bus': '#4169E1',             # RoyalBlue
    'mv_bus': '#8B008B',             # DarkMagenta
    'transformer': '#FFD700',        # Gold
    'hp_load': '#FF4500',            # OrangeRed
    'substation': '#32CD32',         # LimeGreen
    'power_line': '#696969',         # DimGray
    
    # Infrastructure
    'street': '#696969',             # DimGray
    'building': '#D3D3D3',           # LightGray
    'building_outline': '#000000',   # Black
    
    # Status Colors (Traffic Light System)
    'normal': '#2ECC71',             # Green
    'warning': '#F39C12',            # Orange
    'critical': '#E74C3C',           # Red
    'excellent': '#27AE60',          # DarkGreen
    'info': '#3498DB',               # Blue
}


# ============================================================================
# Colormap Presets for Different Visualizations
# ============================================================================

COLORMAPS = {
    # Temperature gradients (DH networks)
    'temperature': 'hot',          # Black -> Red -> Yellow -> White
    'temperature_alt': 'inferno',  # Black -> Purple -> Red -> Yellow
    
    # Pressure gradients (DH networks)  
    'pressure': 'RdYlGn',          # Red (low) -> Yellow -> Green (high)
    'pressure_alt': 'viridis',     # Purple -> Blue -> Green -> Yellow
    
    # Voltage gradients (HP networks)
    'voltage': 'RdYlGn',           # Red (violation) -> Yellow -> Green (normal)
    'voltage_alt': 'coolwarm',     # Blue -> White -> Red
    
    # Heat demand intensity
    'heat_demand': 'YlOrRd',       # Yellow -> Orange -> Red
    'heat_demand_alt': 'Reds',     # Light Red -> Dark Red
    
    # Service connection length
    'service_length': 'RdYlGn_r',  # Red (long) -> Yellow -> Green (short)
    
    # Line loading (HP networks)
    'loading': 'RdYlGn_r',         # Red (overload) -> Yellow -> Green (light)
    
    # General performance
    'performance': 'RdYlGn',       # Red (poor) -> Yellow -> Green (good)
}


# ============================================================================
# Gradient Color Functions
# ============================================================================

def get_temperature_color(temp_c, t_min=40, t_max=90, colormap='hot'):
    """
    Get color for temperature value using specified colormap.
    
    Args:
        temp_c: Temperature in Celsius
        t_min: Minimum temperature for normalization
        t_max: Maximum temperature for normalization
        colormap: Matplotlib colormap name (default: 'hot')
    
    Returns:
        Hex color string
    
    Example:
        >>> get_temperature_color(85)  # High temperature
        '#FF0000'  # Red
        >>> get_temperature_color(45)  # Low temperature
        '#800000'  # Dark red
    """
    cmap = cm.get_cmap(colormap)
    norm = mcolors.Normalize(vmin=t_min, vmax=t_max)
    rgba = cmap(norm(temp_c))
    return mcolors.to_hex(rgba)


def get_pressure_color(pressure_bar, p_min=0, p_max=5, colormap='RdYlGn'):
    """
    Get color for pressure value.
    
    Higher pressure = green (good)
    Lower pressure = red (poor)
    
    Args:
        pressure_bar: Pressure in bar
        p_min: Minimum pressure for normalization
        p_max: Maximum pressure for normalization
        colormap: Matplotlib colormap name (default: 'RdYlGn')
    
    Returns:
        Hex color string
    """
    cmap = cm.get_cmap(colormap)
    norm = mcolors.Normalize(vmin=p_min, vmax=p_max)
    rgba = cmap(norm(pressure_bar))
    return mcolors.to_hex(rgba)


def get_voltage_color(voltage_pu, v_min=0.95, v_max=1.05):
    """
    Get color for voltage value using traffic light system.
    
    Green: Within acceptable range (0.95-1.05 pu)
    Orange: Warning zone (0.92-0.95 or 1.05-1.08 pu)
    Red: Violation (<0.92 or >1.08 pu)
    
    Args:
        voltage_pu: Voltage in per-unit
        v_min: Lower acceptable limit (default: 0.95)
        v_max: Upper acceptable limit (default: 1.05)
    
    Returns:
        Hex color string
    """
    if voltage_pu < 0.92 or voltage_pu > 1.08:
        return NETWORK_COLORS['critical']  # Red - violation
    elif voltage_pu < v_min or voltage_pu > v_max:
        return NETWORK_COLORS['warning']   # Orange - warning
    else:
        return NETWORK_COLORS['normal']    # Green - normal


def get_loading_color(loading_pct, threshold_warning=80, threshold_critical=100):
    """
    Get color for line loading percentage using traffic light system.
    
    Green: Light loading (<80%)
    Orange: High loading (80-100%)
    Red: Overload (>100%)
    
    Args:
        loading_pct: Loading percentage (0-100+)
        threshold_warning: Warning threshold (default: 80%)
        threshold_critical: Critical threshold (default: 100%)
    
    Returns:
        Hex color string
    """
    if loading_pct > threshold_critical:
        return NETWORK_COLORS['critical']  # Red - overload
    elif loading_pct > threshold_warning:
        return NETWORK_COLORS['warning']   # Orange - high
    else:
        return NETWORK_COLORS['normal']    # Green - light


def get_heat_demand_color(demand_kw, min_demand=0, max_demand=100, colormap='YlOrRd'):
    """
    Get color for heat demand intensity.
    
    Yellow: Low demand
    Orange: Medium demand  
    Red: High demand
    
    Args:
        demand_kw: Heat demand in kW
        min_demand: Minimum demand for normalization
        max_demand: Maximum demand for normalization
        colormap: Matplotlib colormap name (default: 'YlOrRd')
    
    Returns:
        Hex color string
    """
    cmap = cm.get_cmap(colormap)
    norm = mcolors.Normalize(vmin=min_demand, vmax=max_demand)
    rgba = cmap(norm(demand_kw))
    return mcolors.to_hex(rgba)


def get_service_length_color(length_m, max_length=100, colormap='RdYlGn_r'):
    """
    Get color for service connection length.
    
    Green: Short connections (<30m) - efficient
    Yellow: Medium connections (30-60m)
    Red: Long connections (>60m) - less efficient
    
    Args:
        length_m: Service connection length in meters
        max_length: Maximum length for normalization (default: 100m)
        colormap: Matplotlib colormap name (default: 'RdYlGn_r' - reversed)
    
    Returns:
        Hex color string
    """
    cmap = cm.get_cmap(colormap)
    norm = mcolors.Normalize(vmin=0, vmax=max_length)
    rgba = cmap(norm(length_m))
    return mcolors.to_hex(rgba)


# ============================================================================
# Helper Functions
# ============================================================================

def create_colorbar(cmap_name, vmin, vmax, label='', orientation='horizontal', figsize=(8, 1)):
    """
    Create a standalone colorbar for documentation or legends.
    
    Args:
        cmap_name: Matplotlib colormap name
        vmin: Minimum value
        vmax: Maximum value
        label: Colorbar label
        orientation: 'horizontal' or 'vertical'
        figsize: Figure size (width, height)
    
    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)
    
    cmap = cm.get_cmap(cmap_name)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    
    cb = plt.colorbar(
        cm.ScalarMappable(norm=norm, cmap=cmap),
        cax=ax,
        orientation=orientation,
        label=label
    )
    
    return fig


def get_gradient_colors(values, cmap_name, vmin=None, vmax=None):
    """
    Get list of colors for array of values using a colormap.
    
    Args:
        values: Array-like of values
        cmap_name: Matplotlib colormap name
        vmin: Minimum value for normalization (default: min of values)
        vmax: Maximum value for normalization (default: max of values)
    
    Returns:
        List of hex color strings
    """
    values = np.asarray(values)
    
    if vmin is None:
        vmin = values.min()
    if vmax is None:
        vmax = values.max()
    
    cmap = cm.get_cmap(cmap_name)
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    
    colors = [mcolors.to_hex(cmap(norm(v))) for v in values]
    return colors

