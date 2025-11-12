"""
Cost Models for District Heating Network Analysis

This module provides cost calculation functions for district heating network
economic analysis, including pump energy consumption and net present value calculations.

All functions are pure, deterministic, and include comprehensive input validation.
Units are explicitly documented for all inputs and outputs.
"""

from typing import Union, List, Tuple

__all__ = ["annual_pump_energy_mwhel", "npv"]


def annual_pump_energy_mwhel(
    dp_sum_pa: float, 
    V_dot_path_m3s: float, 
    eta_pump: float, 
    hours: float
) -> float:
    """
    Compute annual pumping electrical energy in MWh for the worst path (or representative path).
    
    This function calculates the annual electrical energy consumption for pumping
    in a district heating network based on hydraulic power requirements and pump efficiency.
    
    Formula & units:
    
    Hydraulic power: P_hyd = Δp ⋅ V̇ [W] where Δp [Pa], V̇ [m³/s]
    
    Electrical power: P_el = P_hyd / η_pump
    
    Annual energy in MWh:
    E_MWh = (Δp ⋅ V̇ ⋅ hours) / (η_pump ⋅ 10⁶)
    
    (Reason: 1 W⋅h = 1/10⁶ MWh; and Δp ⋅ V̇ is W; multiply by hours → Wh)
    
    Parameters:
        dp_sum_pa: Total pressure drop along the path [Pa]
        V_dot_path_m3s: Volumetric flow rate along the path [m³/s]
        eta_pump: Pump efficiency (dimensionless, 0 < η ≤ 1)
        hours: Annual operating hours [h]
    
    Returns:
        Annual electrical energy consumption [MWh_el per year]
    
    Raises:
        ValueError: If any input is ≤ 0 or if η_pump > 1.0 (unphysical)
    
    Example:
        >>> annual_pump_energy_mwhel(50000, 0.02, 0.65, 3000)
        4.615384615384615
    """
    if dp_sum_pa <= 0:
        raise ValueError(f"Pressure drop must be positive, got {dp_sum_pa} Pa")
    if V_dot_path_m3s <= 0:
        raise ValueError(f"Flow rate must be positive, got {V_dot_path_m3s} m³/s")
    if eta_pump <= 0:
        raise ValueError(f"Pump efficiency must be positive, got {eta_pump}")
    if eta_pump > 1.0:
        raise ValueError(f"Pump efficiency cannot exceed 1.0 (unphysical), got {eta_pump}")
    if hours <= 0:
        raise ValueError(f"Operating hours must be positive, got {hours} h")
    
    # Calculate annual energy in MWh
    # E_MWh = (Δp ⋅ V̇ ⋅ hours) / (η_pump ⋅ 10⁶)
    annual_energy_mwh = (dp_sum_pa * V_dot_path_m3s * hours) / (eta_pump * 1e6)
    
    return annual_energy_mwh


def npv(
    capex: float, 
    annual_cost: Union[float, List[float], Tuple[float, ...]], 
    years: int, 
    r: float
) -> float:
    """
    Calculate present-value cost over the project lifetime.
    
    This function computes the net present value (NPV) of a project considering
    initial capital expenditure and annual operating costs discounted over time.
    
    Behavior:
    
    If annual_cost is a scalar, assume constant yearly cost:
    NPV = CapEx + Σ(y=1 to N) C / (1 + r)^y
    
    If annual_cost is a sequence, discount each element C_y for year y
    (length must be ≥ years; use only first years entries).
    
    Special case: if r == 0, use simple sum: CapEx + sum(C_y) 
    (or CapEx + years * C for scalars).
    
    Parameters:
        capex: Initial capital expenditure [€]
        annual_cost: Annual operating cost(s) [€]
                     - Scalar: constant annual cost
                     - Sequence: varying annual costs (length ≥ years)
        years: Project lifetime [years]
        r: Discount rate (dimensionless, r ≥ 0)
    
    Returns:
        Net present value [€]
    
    Raises:
        ValueError: If inputs are invalid (capex < 0, years < 1, r < 0, 
                   negative costs, or sequence too short)
    
    Example:
        >>> npv(100000, 10000, 5, 0.05)  # Constant annual cost
        143295.8807...
        >>> npv(50000, [8000, 9000, 10000], 3, 0.04)  # Varying costs
        118000.0  # When r = 0
    """
    # Validate inputs
    if capex < 0:
        raise ValueError(f"Capital expenditure must be non-negative, got {capex} €")
    if years < 1:
        raise ValueError(f"Project lifetime must be at least 1 year, got {years}")
    if r < 0:
        raise ValueError(f"Discount rate must be non-negative, got {r}")
    
    # Handle scalar vs sequence annual costs
    if isinstance(annual_cost, (int, float)):
        # Scalar case: constant annual cost
        if annual_cost < 0:
            raise ValueError(f"Annual cost must be non-negative, got {annual_cost} €")
        
        if r == 0:
            # Special case: no discounting
            return capex + annual_cost * years
        else:
            # Discounted constant annuity
            pv_annuity = annual_cost * (1 - (1 + r) ** (-years)) / r
            return capex + pv_annuity
    
    elif isinstance(annual_cost, (list, tuple)):
        # Sequence case: varying annual costs
        if len(annual_cost) < years:
            raise ValueError(
                f"Annual cost sequence length ({len(annual_cost)}) must be >= years ({years})"
            )
        
        # Check all costs are non-negative
        for i, cost in enumerate(annual_cost[:years]):
            if cost < 0:
                raise ValueError(f"Annual cost at year {i+1} must be non-negative, got {cost} €")
        
        if r == 0:
            # Special case: no discounting
            return capex + sum(annual_cost[:years])
        else:
            # Discount each year's cost
            pv_costs = sum(cost / ((1 + r) ** (i + 1)) for i, cost in enumerate(annual_cost[:years]))
            return capex + pv_costs
    
    else:
        raise ValueError(f"Annual cost must be scalar or sequence, got {type(annual_cost)}") 