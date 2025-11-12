"""
Pytest-compatible assertions for the visualization configuration loader.

The original script used print statements accompanied by `sys.exit`. Pytest
interpreted that as an internal error, so we convert those checks into proper
assertions.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Generator

import pytest
import yaml

from src.visualization import VisualizationConfig, get_visualization_config
from src.visualization import config_loader as _config_loader


@pytest.fixture(autouse=True)
def reset_singleton() -> Generator[None, None, None]:
    """Ensure each test starts with a clean singleton instance."""

    _config_loader._config_instance = None
    try:
        yield
    finally:
        _config_loader._config_instance = None


def test_get_visualization_config_returns_singleton() -> None:
    """Repeated calls should return the same object."""

    first = get_visualization_config()
    second = get_visualization_config()
    assert first is second


def test_defaults_are_loaded_when_file_missing(tmp_path: Path) -> None:
    """
    When the config file is missing we fall back to defaults.

    The default values include expected keys and option values.
    """

    missing_config = tmp_path / "does_not_exist.yaml"
    config = VisualizationConfig(config_path=missing_config)

    assert config.is_enabled() is True
    assert config.get("visualization.static.dpi") == 300
    assert config.get("visualization.interactive.zoom_start") == 16
    assert config.get_color("dh_supply") == "#DC143C"
    assert config.get_output_dir("static").endswith("visualizations/static")


def test_merging_overrides_respects_defaults(tmp_path: Path) -> None:
    """Only override the values present in the YAML file."""

    cfg_path = tmp_path / "visualization.yaml"
    cfg_path.write_text(
        yaml.safe_dump(
            {
                "visualization": {
                    "enabled": False,
                    "static": {"dpi": 150},
                    "colors": {"dh_supply": "#FFFFFF"},
                }
            }
        ),
        encoding="utf-8",
    )

    config = VisualizationConfig(config_path=cfg_path)

    assert config.is_enabled() is False
    assert config.get("visualization.static.dpi") == 150
    assert config.get_color("dh_supply") == "#FFFFFF"
    # Keys not overridden should still be populated from defaults.
    assert config.get("visualization.interactive.tiles") == "OpenStreetMap"


def test_settings_accessors_return_dicts(tmp_path: Path) -> None:
    """Accessors should return dictionaries even for partial configs."""

    cfg_path = tmp_path / "visualization.yaml"
    cfg_path.write_text(
        yaml.safe_dump({"visualization": {"static": {"dpi": 200}}}),
        encoding="utf-8",
    )

    config = VisualizationConfig(config_path=cfg_path)

    static_settings: Dict[str, object] = config.get_static_settings()
    interactive_settings: Dict[str, object] = config.get_interactive_settings()
    dashboard_settings: Dict[str, object] = config.get_dashboard_settings()

    assert isinstance(static_settings, dict)
    assert isinstance(interactive_settings, dict)
    assert isinstance(dashboard_settings, dict)
    assert static_settings["dpi"] == 200


def test_feature_flags_optional_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Feature flag file is optional; absence should not raise errors."""

    # Simulate absence of the feature-flag file by working in a temp directory.
    monkeypatch.chdir(tmp_path)
    config = VisualizationConfig()

    # The loader should still provide sane defaults in the absence of the file.
    assert config.is_enabled() is True

