"""Hourly load profile generation for Branitz AI.

TODO: Bring in 8760 h profile synthesis from
`Branitz_energy_decision_ai_street_final/src/profile_generation.py` and
adjacent utilities.
"""

from __future__ import annotations

from typing import Sequence


def generate_hourly_profile(annual_demand_mwh: float) -> Sequence[float]:
    """Return a placeholder hourly load profile normalized to the annual demand."""

    # TODO: Replace with the actual profile generation logic.
    return [annual_demand_mwh / 8760.0] * 8760
