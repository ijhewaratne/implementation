"""Configuration helpers for the Branitz AI package.

TODO: Consolidate scenario and path configuration from legacy modules such as
`Branitz_energy_decision_ai_street_final/src/config.py` and related YAML
loaders in `branitz_energy_decision_ai_street_agents_copy/src/configuration/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScenarioConfig:
    """Placeholder dataclass for scenario-level configuration options."""

    name: str
    description: Optional[str] = None


def load_default_config() -> ScenarioConfig:
    """Return a placeholder default configuration until legacy logic is migrated."""

    # TODO: Implement using existing defaults from the legacy configuration stack.
    return ScenarioConfig(name="default")
