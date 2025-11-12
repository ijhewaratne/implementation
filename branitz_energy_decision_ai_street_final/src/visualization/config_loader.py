"""
Configuration loader utilities for visualization settings.

Provides a lightweight accessor around the YAML configuration file used by the
visualization tooling. The implementation mirrors the behaviour documented in
`untitled folder/branitz_energy_decision_ai_street_agents`, but lives in the
canonical `src/visualization` package so that production code and tests can
import it directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, cast

import yaml


class VisualizationConfig:
    """
    Load and manage visualization configuration.

    Loads settings from `config/visualization_config.yaml` and provides easy
    access to configuration values with sensible defaults.
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialise the configuration loader.

        Args:
            config_path: Optional override path to the visualization config file.
        """

        if config_path is None:
            config_path = Path("config/visualization_config.yaml")
        else:
            config_path = Path(config_path)

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML, falling back to defaults on error."""

        if not self.config_path.exists():
            print(  # noqa: T201 - aligned with existing CLI messaging style
                f"⚠️  Visualization config not found at {self.config_path}, using defaults"
            )
            return self._get_defaults()

        try:
            with self.config_path.open("r", encoding="utf-8") as handle:
                config = yaml.safe_load(handle) or {}

            # Merge with defaults to ensure all expected keys exist.
            defaults = self._get_defaults()
            merged = self._merge_configs(defaults, config)

            return merged

        except Exception as exc:  # pragma: no cover - defensive logging path
            print(
                f"⚠️  Error loading visualization config: {exc}, using defaults"
            )  # noqa: T201 - see above
            return self._get_defaults()

    def _get_defaults(self) -> Dict[str, Any]:
        """Return default configuration values."""

        return {
            "visualization": {
                "enabled": True,
                "auto_generate_on_simulation": False,
                "static_maps_enabled": True,
                "interactive_maps_enabled": True,
                "dashboards_enabled": True,
                "output": {
                    "base_dir": "results_test/visualizations",
                    "static_dir": "results_test/visualizations/static",
                    "interactive_dir": "results_test/visualizations/interactive",
                    "dashboard_dir": "results_test/visualizations/dashboards",
                },
                "static": {
                    "enabled": True,
                    "dpi": 300,
                    "format": "png",
                    "figsize": [15, 12],
                    "include_street_map": True,
                },
                "interactive": {
                    "enabled": True,
                    "zoom_start": 16,
                    "tiles": "OpenStreetMap",
                    "include_statistics_panel": True,
                    "include_performance_dashboard": True,
                    "include_legend": True,
                },
                "colors": {
                    "dh_supply": "#DC143C",
                    "dh_return": "#4682B4",
                    "normal": "#2ECC71",
                    "warning": "#F39C12",
                    "critical": "#E74C3C",
                },
                "temperature": {
                    "colormap": "hot",
                    "min_temp_c": 40,
                    "max_temp_c": 90,
                },
                "voltage": {
                    "colormap": "RdYlGn",
                    "acceptable_min": 0.95,
                    "acceptable_max": 1.05,
                },
            }
        }

    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge configuration dictionaries."""

        merged: Dict[str, Any] = default.copy()

        for key, value in override.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value

        return merged

    def get(self, path: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation path.

        Args:
            path: Dot-separated path (e.g. `visualization.static.dpi`).
            default: Optional default value if the path is missing.
        """

        keys = path.split(".")
        value: Any = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def is_enabled(self) -> bool:
        """Return whether visualizations are enabled."""

        return bool(self.get("visualization.enabled", True))

    def get_output_dir(self, viz_type: str = "static") -> str:
        """
        Get the output directory for a visualization type.

        Args:
            viz_type: One of `static`, `interactive`, or `dashboard`.
        """

        return str(
            self.get(
                f"visualization.output.{viz_type}_dir",
                f"results_test/visualizations/{viz_type}",
            )
        )

    def get_color(self, color_name: str) -> str:
        """Return a colour value by name."""

        return str(self.get(f"visualization.colors.{color_name}", "#000000"))

    def get_static_settings(self) -> Dict[str, Any]:
        """Return the static-map configuration block."""

        settings = self.get("visualization.static", {})
        return cast(Dict[str, Any], settings) if isinstance(settings, dict) else {}

    def get_interactive_settings(self) -> Dict[str, Any]:
        """Return the interactive-map configuration block."""

        settings = self.get("visualization.interactive", {})
        return cast(Dict[str, Any], settings) if isinstance(settings, dict) else {}

    def get_dashboard_settings(self) -> Dict[str, Any]:
        """Return the dashboard configuration block."""

        settings = self.get("visualization.dashboard", {})
        return cast(Dict[str, Any], settings) if isinstance(settings, dict) else {}


# Singleton instance cache.
_config_instance: Optional[VisualizationConfig] = None


def get_visualization_config() -> VisualizationConfig:
    """
    Return a singleton `VisualizationConfig` instance.

    Re-uses the same loader across the application to avoid repeated disk IO.
    """

    global _config_instance

    if _config_instance is None:
        _config_instance = VisualizationConfig()

    return _config_instance


