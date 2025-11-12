"""
EN 13941 Checks for District Heating Network Validation

This module provides validation functions based on EN 13941 standards for
district heating network design and operation.

All functions are pure, deterministic, and include comprehensive input validation.
Standards compliance checks are implemented according to EN 13941 requirements.
"""

__all__ = ["check_velocity", "check_deltaT"]


def check_velocity(v_max: float, limit: float = 1.5) -> bool:
    """
    EN 13941 velocity limit check for DH pipes.
    
    This function validates that the maximum flow velocity in a district heating
    network does not exceed the specified limit according to EN 13941 standards.
    
    Semantics: Return True if v_max <= limit, else False.
    
    Parameters:
        v_max: Maximum flow velocity [m/s]
        limit: Velocity limit according to EN 13941 [m/s], defaults to 1.5
    
    Returns:
        True if velocity is within limit, False otherwise
    
    Raises:
        ValueError: If v_max < 0 or limit <= 0
    
    Example:
        >>> check_velocity(1.3)  # Within typical design target
        True
        >>> check_velocity(1.6, limit=1.5)  # Exceeds limit
        False
    
    Notes:
        Typical design targets are 1.3–1.5 m/s for optimal network performance
        and to minimize pressure losses while maintaining good heat transfer.
    """
    if v_max < 0:
        raise ValueError(f"Maximum velocity must be non-negative, got {v_max} m/s")
    if limit <= 0:
        raise ValueError(f"Velocity limit must be positive, got {limit} m/s")
    
    return v_max <= limit


def check_deltaT(deltaT_delivered: float, min_deltaT: float = 30.0) -> bool:
    """
    Check delivered temperature spread meets design target.
    
    This function validates that the delivered temperature difference (ΔT) in a
    district heating network meets the minimum design target according to EN 13941.
    
    Semantics: Return True if deltaT_delivered >= min_deltaT, else False.
    
    Parameters:
        deltaT_delivered: Delivered temperature difference [K]
        min_deltaT: Minimum required temperature difference [K], defaults to 30.0
    
    Returns:
        True if temperature difference meets minimum requirement, False otherwise
    
    Raises:
        ValueError: If deltaT_delivered < 0 or min_deltaT <= 0
    
    Example:
        >>> check_deltaT(32.0)  # Meets typical 80/50°C design (ΔT=30K)
        True
        >>> check_deltaT(28.0, min_deltaT=30.0)  # Below minimum
        False
    
    Notes:
        Typical design uses 80/50°C supply/return temperatures (ΔT=30K).
        Checks are performed at the farthest consumer in network validation.
        Higher ΔT values improve network efficiency and reduce flow rates.
    """
    if deltaT_delivered < 0:
        raise ValueError(f"Delivered temperature difference must be non-negative, got {deltaT_delivered} K")
    if min_deltaT <= 0:
        raise ValueError(f"Minimum temperature difference must be positive, got {min_deltaT} K")
    
    return deltaT_delivered >= min_deltaT 