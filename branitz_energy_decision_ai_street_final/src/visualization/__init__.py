"""
Visualization configuration entry points.

Exposes the `VisualizationConfig` class and its singleton accessor so that
other modules (and the test suite) can import them from `src.visualization`.
"""

from .config_loader import VisualizationConfig, get_visualization_config

__all__ = [
    "VisualizationConfig",
    "get_visualization_config",
]


