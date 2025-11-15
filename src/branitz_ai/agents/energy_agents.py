"""Definitions of planner, CHA, and DHA agents.

TODO: Rehome agent orchestration from
`branitz_energy_decision_ai_street_final/src/enhanced_agents_adk_updated.py`
and related ADK setups in `branitz_energy_decision_ai_street_agents_copy/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


default_agent_registry: Dict[str, "EnergyAgent"] = {}


@dataclass
class EnergyAgent:
    """Placeholder dataclass describing an energy planning agent."""

    name: str
    role: str
    description: str

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent with the provided payload."""

        # TODO: Wire up to actual tool-calling and orchestration logic.
        raise NotImplementedError("Agent execution not yet implemented.")
