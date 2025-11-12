"""
Pytest checks ensuring agents can access visualization tooling.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Iterable, Sequence, Tuple

import pytest

import src.visualization as visualization

AGENTS_REPO_ROOT = Path(__file__).resolve().parent / "agents copy"


@pytest.fixture(scope="module")
def agents_module():
    """Dynamically load the enriched agent definitions shipped alongside the repo."""

    module_path = AGENTS_REPO_ROOT / "agents.py"
    if not module_path.exists():
        pytest.skip("Enhanced agent module not available in the workspace")

    spec = importlib.util.spec_from_file_location("branitz_agents", module_path)
    if spec is None or spec.loader is None:
        pytest.skip("Unable to create module spec for enhanced agents")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError as exc:
        pytest.skip(f"Skipping enhanced agent checks because dependency is missing: {exc}")

    return module


def _tool_names(tools: Sequence[object]) -> Sequence[str]:
    """Extract consistent tool names from ADK tool objects or callables."""

    names = []
    for tool in tools:
        if hasattr(tool, "name"):
            names.append(str(getattr(tool, "name")))
        elif hasattr(tool, "func"):
            names.append(str(getattr(tool, "func").__name__))
        elif hasattr(tool, "__name__"):
            names.append(str(getattr(tool, "__name__")))
        else:
            names.append(repr(tool))
    return names


@pytest.mark.parametrize(
    ("agent_attr", "expected_tools"),
    [
        ("CentralHeatingAgent", {"get_building_ids_for_street", "run_simulation_pipeline"}),
        ("DecentralizedHeatingAgent", {"run_simulation_pipeline", "create_network_visualization"}),
        ("ComparisonAgent", {"compare_scenarios"}),
        ("DataExplorerAgent", {"get_all_street_names", "list_available_results"}),
    ],
)
def test_agent_definitions_expose_expected_tools(
    agents_module, agent_attr: str, expected_tools: Iterable[str]
) -> None:
    """The enhanced agents should expose the toolchain required for visualization output."""

    agent = getattr(agents_module, agent_attr)
    assert hasattr(agent, "config"), f"{agent_attr} should expose a config attribute"
    tool_names = set(_tool_names(getattr(agent.config, "tools", [])))
    missing = set(expected_tools) - tool_names
    assert not missing, f"{agent_attr} missing expected tools: {sorted(missing)}"


def test_visualization_module_exposes_configuration() -> None:
    """`src.visualization` should export the configuration helpers used by agents."""

    assert hasattr(visualization, "VisualizationConfig")
    assert hasattr(visualization, "get_visualization_config")


def test_visualization_module_has_optional_generators() -> None:
    """If advanced generators are present they should be importable."""

    optional_symbols: Tuple[str, ...] = (
        "NetworkMapGenerator",
        "InteractiveMapGenerator",
        "NETWORK_COLORS",
    )

    missing = [name for name in optional_symbols if not hasattr(visualization, name)]
    if missing:
        pytest.skip(f"Advanced visualization generators not yet ported: {', '.join(missing)}")


def test_energy_tools_module_available() -> None:
    """Ensure the shared energy_tools module can be imported for agent tooling."""

    energy_tools_path = AGENTS_REPO_ROOT / "energy_tools.py"
    if not energy_tools_path.exists():
        pytest.skip("Energy tools module not provided in workspace")

    spec = importlib.util.spec_from_file_location("branitz_energy_tools", energy_tools_path)
    if spec is None or spec.loader is None:
        pytest.skip("Unable to load energy_tools module spec")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except ModuleNotFoundError as exc:
        pytest.skip(f"Skipping energy tools validation because dependency is missing: {exc}")

    for func_name in ("create_network_visualization", "create_summary_dashboard"):
        assert hasattr(module, func_name), f"energy_tools missing expected function {func_name}"
