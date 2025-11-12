"""
Pipe sizing utilities derived from the CHA toolkit.

The implementation keeps the core hydraulics used in the legacy project
while removing file I/O and UI code.  It can size a single pipe based on
mass flow, pressure-drop limits, and velocity limits, then snap the result
to a catalogue of standard diameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import math


@dataclass
class PipeSizingResult:
    """Outcome of sizing a single pipe."""

    pipe_id: str
    diameter_m: float
    diameter_nominal: str
    velocity_ms: float
    pressure_drop_pa_per_m: float
    pressure_drop_bar: float
    reynolds_number: float
    friction_factor: float
    pipe_category: str


class CHAPipeSizingEngine:
    """
    Hydraulics-based pipe sizing engine.

    The engine:
      1. Calculates a diameter that satisfies both velocity and
         pressure-drop limits.
      2. Snaps the required diameter to the next larger standard size.
      3. Returns core hydraulic metrics for reporting.
    """

    def __init__(
        self,
        max_velocity_ms: Dict[str, float] | None = None,
        max_pressure_drop_pa_per_m: Dict[str, float] | None = None,
        standard_diameters_mm: Iterable[int] | None = None,
        pipe_roughness_mm: float = 0.1,
    ) -> None:
        self.max_velocity_ms = max_velocity_ms or {
            "service_connection": 1.5,
            "distribution_pipe": 2.0,
            "main_pipe": 2.0,
        }
        self.max_pressure_drop_pa_per_m = max_pressure_drop_pa_per_m or {
            "service_connection": 5000.0,
            "distribution_pipe": 4000.0,
            "main_pipe": 3000.0,
        }

        self.standard_diameters_m = [
            (d if isinstance(d, (int, float)) else float(d)) / 1000.0
            for d in (standard_diameters_mm or [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400])
        ]
        self.standard_diameters_m.sort()

        self.pipe_roughness_m = pipe_roughness_mm / 1000.0
        self._water_density_kg_m3 = 977.8
        self._water_dynamic_viscosity_pa_s = 0.000404

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def size_pipe(
        self,
        pipe_id: str,
        flow_rate_kg_s: float,
        length_m: float,
        pipe_category: str,
    ) -> PipeSizingResult:
        """
        Size a single pipe.

        Args:
            pipe_id: identifier used in results.
            flow_rate_kg_s: mass flow through the pipe.
            length_m: physical length of the pipe.
            pipe_category: one of service_connection/distribution_pipe/main_pipe.
        """
        flow_rate_kg_s = max(0.0, flow_rate_kg_s)
        length_m = max(1.0, length_m)
        category = pipe_category or "distribution_pipe"

        required_diameter = self._calculate_required_diameter(flow_rate_kg_s, category)
        selected_diameter = self._select_standard_diameter(required_diameter, category)

        velocity = self._calculate_velocity(flow_rate_kg_s, selected_diameter)
        reynolds = self._calculate_reynolds_number(velocity, selected_diameter)
        friction_factor = self._calculate_friction_factor(reynolds, selected_diameter)
        pressure_drop_pa_per_m = self._calculate_pressure_drop_per_meter(
            flow_rate_kg_s,
            selected_diameter,
            friction_factor,
        )
        pressure_drop_bar = (pressure_drop_pa_per_m * length_m) / 100000.0

        return PipeSizingResult(
            pipe_id=pipe_id,
            diameter_m=selected_diameter,
            diameter_nominal=self._format_nominal(selected_diameter),
            velocity_ms=velocity,
            pressure_drop_pa_per_m=pressure_drop_pa_per_m,
            pressure_drop_bar=pressure_drop_bar,
            reynolds_number=reynolds,
            friction_factor=friction_factor,
            pipe_category=category,
        )

    # ------------------------------------------------------------------ #
    # Core calculations
    # ------------------------------------------------------------------ #

    def _calculate_required_diameter(self, flow_rate_kg_s: float, pipe_category: str) -> float:
        """Diameter needed to satisfy both velocity and pressure constraints."""
        if flow_rate_kg_s <= 0.0:
            return self.standard_diameters_m[0]

        max_velocity = self.max_velocity_ms.get(pipe_category, 2.0)
        velocity_limited = math.sqrt(
            4.0 * flow_rate_kg_s / (self._water_density_kg_m3 * math.pi * max_velocity)
        )

        pressure_limit = self.max_pressure_drop_pa_per_m.get(pipe_category, 4000.0)
        pressure_limited = self._diameter_for_pressure_drop(flow_rate_kg_s, pressure_limit)

        return max(velocity_limited, pressure_limited)

    def _diameter_for_pressure_drop(self, flow_rate_kg_s: float, max_pressure_drop_pa_per_m: float) -> float:
        """Iteratively solve for diameter that satisfies the pressure drop limit."""
        diameter = max(self.standard_diameters_m[0], 0.02)
        for _ in range(20):
            velocity = self._calculate_velocity(flow_rate_kg_s, diameter)
            if velocity <= 0.0:
                break
            reynolds = self._calculate_reynolds_number(velocity, diameter)
            friction = self._calculate_friction_factor(reynolds, diameter)
            pressure_drop = self._calculate_pressure_drop_per_meter(flow_rate_kg_s, diameter, friction)
            if abs(pressure_drop - max_pressure_drop_pa_per_m) < 10.0:
                break
            if pressure_drop > max_pressure_drop_pa_per_m:
                diameter *= 1.1
            else:
                diameter *= 0.95
        return diameter

    def _select_standard_diameter(self, required_diameter: float, pipe_category: str) -> float:
        """Snap to the next larger diameter in the catalogue."""
        min_d, max_d = self._category_range(pipe_category)
        for diameter in self.standard_diameters_m:
            if diameter < min_d:
                continue
            if diameter >= required_diameter and diameter <= max_d:
                return diameter
        # If requirement exceeds catalogue, clamp to largest allowed
        return min(max_d, max(self.standard_diameters_m))

    def _category_range(self, pipe_category: str) -> Tuple[float, float]:
        if pipe_category == "service_connection":
            return 0.025, 0.050
        if pipe_category == "main_pipe":
            return 0.200, 0.400
        return 0.063, 0.200  # distribution default

    def _calculate_velocity(self, flow_rate_kg_s: float, diameter_m: float) -> float:
        area = math.pi * (diameter_m ** 2) / 4.0
        mass_flux = flow_rate_kg_s / self._water_density_kg_m3
        return mass_flux / max(area, 1e-6)

    def _calculate_reynolds_number(self, velocity_ms: float, diameter_m: float) -> float:
        return (
            self._water_density_kg_m3
            * velocity_ms
            * diameter_m
            / self._water_dynamic_viscosity_pa_s
        )

    def _calculate_friction_factor(self, reynolds_number: float, diameter_m: float) -> float:
        # Use the Swamee-Jain approximation for turbulent flow, fallback to laminar
        if reynolds_number <= 0:
            return 0.0
        if reynolds_number < 2300:
            return 64.0 / max(reynolds_number, 1e-6)
        relative_roughness = self.pipe_roughness_m / diameter_m
        return 0.25 / (
            math.log10(relative_roughness / 3.7 + 5.74 / (reynolds_number ** 0.9))
            ** 2
        )

    def _calculate_pressure_drop_per_meter(
        self,
        flow_rate_kg_s: float,
        diameter_m: float,
        friction_factor: float,
    ) -> float:
        if diameter_m <= 0 or friction_factor <= 0:
            return 0.0
        velocity = self._calculate_velocity(flow_rate_kg_s, diameter_m)
        return (
            friction_factor
            * (self._water_density_kg_m3 * velocity ** 2)
            / (2.0 * diameter_m)
        )

    @staticmethod
    def _format_nominal(diameter_m: float) -> str:
        return f"DN{int(round(diameter_m * 1000.0))}"

