"""
Standards-compliance checks for sized pipes.

This module evaluates the hydraulic metrics produced by the sizing engine
against a small set of configurable thresholds (derived from EN 13941 /
DIN 1988 limits).  The goal is to surface potential violations without
replicating the entire CHA reporting layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class StandardsViolation:
    """Single violation record."""

    standard: str
    violation_type: str
    message: str
    severity: str
    current_value: float
    limit_value: float


@dataclass
class ComplianceResult:
    """Compliance result for a pipe."""

    pipe_id: str
    overall_compliant: bool
    standards_compliance: Dict[str, bool]
    violations: List[StandardsViolation]


class CHAStandardsComplianceEngine:
    """
    Minimal compliance engine used by the agent workflow.

    Checks velocity and pressure-drop limits for each pipe category using
    configurable thresholds.  Additional standards can be layered later.
    """

    def __init__(
        self,
        velocity_limits: Dict[str, float] | None = None,
        pressure_drop_limits_pa_per_m: Dict[str, float] | None = None,
    ) -> None:
        self.velocity_limits = velocity_limits or {
            "service_connection": 1.5,
            "distribution_pipe": 2.0,
            "main_pipe": 2.0,
        }
        self.pressure_drop_limits = pressure_drop_limits_pa_per_m or {
            "service_connection": 5000.0,
            "distribution_pipe": 4000.0,
            "main_pipe": 3000.0,
        }

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def validate_pipe(
        self,
        pipe_id: str,
        pipe_category: str,
        velocity_ms: float,
        pressure_drop_pa_per_m: float,
    ) -> ComplianceResult:
        """
        Validate a single pipe.

        Returns:
            ComplianceResult with any violations discovered.
        """
        violations: List[StandardsViolation] = []
        standards_flags: Dict[str, bool] = {}

        # DIN-inspired limits
        din_ok = self._check_limits(
            violations,
            standard="DIN_1988",
            pipe_category=pipe_category,
            velocity_ms=velocity_ms,
            pressure_drop_pa_per_m=pressure_drop_pa_per_m,
        )
        standards_flags["DIN_1988"] = din_ok

        # EN 13941 generic envelope
        en_ok = self._check_en13941(
            violations,
            velocity_ms=velocity_ms,
            pressure_drop_pa_per_m=pressure_drop_pa_per_m,
        )
        standards_flags["EN_13941"] = en_ok

        overall = all(standards_flags.values())

        return ComplianceResult(
            pipe_id=pipe_id,
            overall_compliant=overall,
            standards_compliance=standards_flags,
            violations=violations,
        )

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _check_limits(
        self,
        violations: List[StandardsViolation],
        standard: str,
        pipe_category: str,
        velocity_ms: float,
        pressure_drop_pa_per_m: float,
    ) -> bool:
        vel_limit = self.velocity_limits.get(pipe_category, 2.0)
        pd_limit = self.pressure_drop_limits.get(pipe_category, 4000.0)
        ok = True

        if velocity_ms > vel_limit:
            violations.append(
                StandardsViolation(
                    standard=standard,
                    violation_type="velocity_exceeded",
                    message=(
                        f"Velocity {velocity_ms:.2f} m/s exceeds limit "
                        f"{vel_limit:.2f} m/s for {pipe_category}"
                    ),
                    severity="high",
                    current_value=velocity_ms,
                    limit_value=vel_limit,
                )
            )
            ok = False

        if pressure_drop_pa_per_m > pd_limit:
            violations.append(
                StandardsViolation(
                    standard=standard,
                    violation_type="pressure_drop_exceeded",
                    message=(
                        f"Pressure drop {pressure_drop_pa_per_m:.0f} Pa/m exceeds "
                        f"limit {pd_limit:.0f} Pa/m for {pipe_category}"
                    ),
                    severity="medium",
                    current_value=pressure_drop_pa_per_m,
                    limit_value=pd_limit,
                )
            )
            ok = False

        return ok

    @staticmethod
    def _check_en13941(
        violations: List[StandardsViolation],
        velocity_ms: float,
        pressure_drop_pa_per_m: float,
    ) -> bool:
        ok = True
        if velocity_ms > 2.0:
            violations.append(
                StandardsViolation(
                    standard="EN_13941",
                    violation_type="velocity_exceeded",
                    message=f"Velocity {velocity_ms:.2f} m/s exceeds EN 13941 envelope (2.0 m/s)",
                    severity="high",
                    current_value=velocity_ms,
                    limit_value=2.0,
                )
            )
            ok = False
        if pressure_drop_pa_per_m > 5000.0:
            violations.append(
                StandardsViolation(
                    standard="EN_13941",
                    violation_type="pressure_drop_exceeded",
                    message=(
                        f"Pressure drop {pressure_drop_pa_per_m:.0f} Pa/m exceeds "
                        "EN 13941 envelope (5000 Pa/m)"
                    ),
                    severity="medium",
                    current_value=pressure_drop_pa_per_m,
                    limit_value=5000.0,
                )
            )
            ok = False
        return ok

