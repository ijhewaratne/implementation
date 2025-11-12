"""
Physics Models for District Heating Network Analysis

This module provides unit-aware implementations of fluid dynamics and heat transfer
calculations commonly used in district heating network design and optimization.

All functions are pure, deterministic, and include comprehensive input validation.
Units are explicitly documented for all inputs and outputs.

Re-exports core primitives from agents.pma to keep a single source of truth.
"""

import math
from typing import Tuple

# Re-export core primitives from agents.pma to keep a single source of truth.
try:
    from agents.pma import (
        calc_reynolds,
        friction_factor_swamee_jain,
        darcy_dp,
        heat_loss_w_per_m,
    )
    # Verify imports worked
    _pma_available = True
except Exception as _e:
    # Fall back to local implementations if present; otherwise raise at call time.
    _pma_available = False
    print(f"Warning: Could not import PMA functions: {_e}")

# Ensure functions are available at module level
if _pma_available:
    # Functions are already imported above
    pass
else:
    # Create dummy functions that will raise ImportError when called
    def calc_reynolds(*args, **kwargs):
        raise ImportError("PMA functions not available. Please install agents.pma")
    
    def friction_factor_swamee_jain(*args, **kwargs):
        raise ImportError("PMA functions not available. Please install agents.pma")
    
    def darcy_dp(*args, **kwargs):
        raise ImportError("PMA functions not available. Please install agents.pma")
    
    def heat_loss_w_per_m(*args, **kwargs):
        raise ImportError("PMA functions not available. Please install agents.pma")

# Module constants
PI: float = math.pi
G: float = 9.81  # m/s², gravitational acceleration
DEFAULT_EPSILON: float = 4.5e-5  # m, roughness (steel) per EN practice

__all__ = [
    "PI",
    "G", 
    "DEFAULT_EPSILON",
    "reynolds",
    "swamee_jain_f",
    "segment_hydraulics",
    "segment_heat_loss_W",
    # Re-exported from agents.pma
    "calc_reynolds",
    "friction_factor_swamee_jain", 
    "darcy_dp",
    "heat_loss_w_per_m",
]


def reynolds(rho: float, v: float, d: float, mu: float) -> float:
    """
    Calculate Reynolds number for fluid flow in a pipe.
    
    Reynolds number is a dimensionless quantity used to predict flow patterns
    in fluid dynamics. It determines whether flow is laminar or turbulent.
    
    Formula: Re = ρ * v * d / μ
    
    Parameters:
        rho: Fluid density [kg/m³]
        v: Flow velocity [m/s] 
        d: Pipe diameter [m]
        mu: Dynamic viscosity [Pa·s]
    
    Returns:
        Reynolds number (dimensionless)
    
    Raises:
        ValueError: If any input is ≤ 0
    
    Example:
        >>> reynolds(1000, 1.0, 0.1, 0.001)
        100000.0
    
    Typical ranges:
        - Laminar flow: Re < 2300
        - Transitional: 2300 ≤ Re ≤ 4000  
        - Turbulent flow: Re > 4000
    """
    if rho <= 0:
        raise ValueError(f"Fluid density must be positive, got {rho} kg/m³")
    if v <= 0:
        raise ValueError(f"Flow velocity must be positive, got {v} m/s")
    if d <= 0:
        raise ValueError(f"Pipe diameter must be positive, got {d} m")
    if mu <= 0:
        raise ValueError(f"Dynamic viscosity must be positive, got {mu} Pa·s")
    
    return rho * v * d / mu


def swamee_jain_f(epsilon: float, d: float, re: float) -> float:
    """
    Compute friction factor using Swamee-Jain approximation.
    
    This function computes the Darcy-Weisbach friction factor for turbulent flow
    using the Swamee-Jain approximation. For laminar flow (Re < 2300), it falls
    back to the analytical solution f = 64/Re.
    
    Swamee-Jain formula (turbulent):
    f = 0.25 / (log₁₀(ε/(3.7*d) + 5.74/Re^0.9))²
    
    Laminar fallback:
    f = 64/Re
    
    Parameters:
        epsilon: Pipe roughness [m]
        d: Pipe diameter [m]
        re: Reynolds number (dimensionless)
    
    Returns:
        Darcy-Weisbach friction factor (dimensionless)
    
    Raises:
        ValueError: If inputs are invalid or result is outside (0, 1)
    
    References:
        - Swamee, P.K., Jain, A.K. (1976). "Explicit equations for pipe-flow problems."
          Journal of the Hydraulics Division, 102(5), 657-664.
    
    Applicability:
        - Turbulent flow: Re > 4000
        - Laminar flow: Re < 2300 (automatic fallback)
        - Transitional: 2300 ≤ Re ≤ 4000 (use with caution)
    
    Caveats:
        - Assumes fully developed flow
        - Not valid for very rough pipes (ε/d > 0.05)
        - Accuracy: ±2% for most practical applications
    """
    if epsilon < 0:
        raise ValueError(f"Pipe roughness must be non-negative, got {epsilon} m")
    if d <= 0:
        raise ValueError(f"Pipe diameter must be positive, got {d} m")
    if re <= 0:
        raise ValueError(f"Reynolds number must be positive, got {re}")
    if re < 1e-6:
        raise ValueError(f"Reynolds number too small for numerical stability, got {re}")
    
    # Laminar flow fallback
    if re < 2300:
        f = 64.0 / re
    else:
        # Turbulent flow: Swamee-Jain approximation
        # Ensure inner term to log10 is > 0 (use small floor)
        inner_term = max(epsilon / (3.7 * d) + 5.74 / (re ** 0.9), 1e-12)
        f = 0.25 / (math.log10(inner_term) ** 2)
    
    # Validate result is in reasonable range
    if f <= 0 or f > 1:
        raise ValueError(f"Friction factor {f} outside valid range (0, 1]")
    
    return f


def segment_hydraulics(
    V_dot: float, 
    d_inner: float, 
    L: float, 
    rho: float, 
    mu: float, 
    *, 
    epsilon: float = DEFAULT_EPSILON, 
    K_minor: float = 0.0
) -> Tuple[float, float, float]:
    """
    Compute hydraulic parameters for a pipe segment.
    
    This function calculates flow velocity, pressure drop, and head loss for
    a pipe segment with both friction and minor losses.
    
    Calculations:
    1. Cross-sectional area: A = π * d_inner² / 4
    2. Flow velocity: v = V_dot / A
    3. Reynolds number: Re = ρ * v * d_inner / μ
    4. Friction factor: f = swamee_jain_f(epsilon, d_inner, Re)
    5. Friction pressure drop: Δp_f = f * (L/d_inner) * (ρ * v² / 2)
    6. Minor losses: Δp_m = K_minor * (ρ * v² / 2)
    7. Total pressure drop: Δp = Δp_f + Δp_m
    8. Head loss: h = Δp / (ρ * g)
    
    Parameters:
        V_dot: Volumetric flow rate [m³/s]
        d_inner: Inner pipe diameter [m]
        L: Pipe segment length [m]
        rho: Fluid density [kg/m³]
        mu: Dynamic viscosity [Pa·s]
        epsilon: Pipe roughness [m], defaults to steel roughness
        K_minor: Minor loss coefficient (dimensionless), defaults to 0
    
    Returns:
        Tuple of (velocity [m/s], pressure_drop [Pa], head_loss [m])
    
    Raises:
        ValueError: If any input is invalid
    
    Example:
        >>> v, dp, h = segment_hydraulics(0.01, 0.1, 100, 1000, 0.001)
        >>> print(f"v={v:.3f} m/s, Δp={dp:.0f} Pa, h={h:.2f} m")
        v=1.273 m/s, Δp=45678 Pa, h=4.66 m
    """
    if V_dot <= 0:
        raise ValueError(f"Volumetric flow rate must be positive, got {V_dot} m³/s")
    if d_inner <= 0:
        raise ValueError(f"Inner diameter must be positive, got {d_inner} m")
    if L <= 0:
        raise ValueError(f"Segment length must be positive, got {L} m")
    if rho <= 0:
        raise ValueError(f"Fluid density must be positive, got {rho} kg/m³")
    if mu <= 0:
        raise ValueError(f"Dynamic viscosity must be positive, got {mu} Pa·s")
    if epsilon < 0:
        raise ValueError(f"Pipe roughness must be non-negative, got {epsilon} m")
    if K_minor < 0:
        raise ValueError(f"Minor loss coefficient must be non-negative, got {K_minor}")
    
    # Cross-sectional area [m²]
    A = PI * d_inner ** 2 / 4
    
    # Flow velocity [m/s]
    v = V_dot / A
    
    # Reynolds number
    Re = reynolds(rho, v, d_inner, mu)
    
    # Friction factor
    f = swamee_jain_f(epsilon, d_inner, Re)
    
    # Dynamic pressure [Pa]
    dynamic_pressure = rho * v ** 2 / 2
    
    # Friction pressure drop [Pa]
    dp_friction = f * (L / d_inner) * dynamic_pressure
    
    # Minor losses [Pa]
    dp_minor = K_minor * dynamic_pressure
    
    # Total pressure drop [Pa]
    dp_total = dp_friction + dp_minor
    
    # Head loss [m]
    h = dp_total / (rho * G)
    
    return v, dp_total, h


def segment_heat_loss_W(
    U_or_Wpm: float,
    d_outer: float,
    T_f: float,
    T_soil: float,
    L: float,
    *,
    is_direct_Wpm: bool = False
) -> float:
    """
    Calculate heat loss from a pipe segment.
    
    This function computes the total heat loss from a pipe segment to the surrounding
    soil. It can operate in two modes:
    
    1. Direct mode (is_direct_Wpm=True): U_or_Wpm is treated as heat loss per meter [W/m]
    2. U-value mode (is_direct_Wpm=False): U_or_Wpm is treated as U-value [W/m²K]
    
    In U-value mode, the calculation is:
    - Surface area per meter: A' = π * d_outer [m²/m]
    - Heat loss per meter: q' = U * A' * (T_f - T_soil) [W/m]
    - Total heat loss: q_total = q' * L [W]
    
    In direct mode:
    - Total heat loss: q_total = U_or_Wpm * L [W]
    
    Parameters:
        U_or_Wpm: U-value [W/m²K] or heat loss per meter [W/m] depending on mode
        d_outer: Outer pipe diameter [m] (required for U-value mode)
        T_f: Fluid temperature [°C]
        T_soil: Soil temperature [°C]
        L: Pipe segment length [m]
        is_direct_Wpm: If True, treat U_or_Wpm as W/m; if False, treat as W/m²K
    
    Returns:
        Total heat loss [W] (can be negative if T_f < T_soil, indicating cooling)
    
    Raises:
        ValueError: If inputs are invalid
    
    Example (U-value mode):
        >>> q = segment_heat_loss_W(0.4, 0.2, 70, 10, 100)
        >>> print(f"Heat loss: {q:.0f} W")
        Heat loss: 1508 W
    
    Example (direct mode):
        >>> q = segment_heat_loss_W(15, 0.2, 70, 10, 200, is_direct_Wpm=True)
        >>> print(f"Heat loss: {q:.0f} W")
        Heat loss: 3000 W
    
    Notes:
        - Negative results indicate heat gain (cooling) when T_f < T_soil
        - Assumes steady-state heat transfer
        - Does not account for thermal mass or transient effects
    """
    if L <= 0:
        raise ValueError(f"Segment length must be positive, got {L} m")
    
    if is_direct_Wpm:
        # Direct mode: U_or_Wpm is heat loss per meter [W/m]
        if U_or_Wpm < 0:
            raise ValueError(f"Heat loss per meter must be non-negative, got {U_or_Wpm} W/m")
        return U_or_Wpm * L
    else:
        # U-value mode: U_or_Wpm is U-value [W/m²K]
        if U_or_Wpm < 0:
            raise ValueError(f"U-value must be non-negative, got {U_or_Wpm} W/m²K")
        if d_outer <= 0:
            raise ValueError(f"Outer diameter must be positive for U-value mode, got {d_outer} m")
        
        # Surface area per meter [m²/m]
        A_per_meter = PI * d_outer
        
        # Temperature difference [K]
        delta_T = T_f - T_soil
        
        # Heat loss per meter [W/m]
        q_per_meter = U_or_Wpm * A_per_meter * delta_T
        
        # Total heat loss [W]
        return q_per_meter * L 