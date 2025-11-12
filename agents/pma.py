"""
Physics Modeling Agent (PMA)

Vectorized physics functions for district heating network analysis.
All functions are pure NumPy, vectorized, and accept scalars/arrays with broadcasting.
"""

from __future__ import annotations
from typing import Union
import numpy as np

ArrayLike = Union[float, int, np.ndarray]

def _as_float(x: ArrayLike) -> np.ndarray:
    """Cast input to float64 ndarray (no copy if already ndarray)."""
    return np.asarray(x, dtype=np.float64)

def calc_reynolds(v_ms: ArrayLike, d_m: ArrayLike, rho: ArrayLike, mu: ArrayLike) -> np.ndarray:
    """
    Reynolds number (dimensionless), vectorized.
    Re = rho * v * d / mu
    
    Parameters
    ----------
    v_ms : m/s
    d_m : m
    rho : kg/m^3
    mu : Pa·s  (kg/(m·s))
    
    Returns
    -------
    np.ndarray float64 : Reynolds number
    """
    v = _as_float(v_ms)
    d = _as_float(d_m)
    r = _as_float(rho)
    m = _as_float(mu)
    # prevent divide-by-zero; mu should be >0
    m = np.maximum(m, 1e-18)
    return (r * v * d) / m

def friction_factor_swamee_jain(Re: ArrayLike, eps_rel: ArrayLike) -> np.ndarray:
    """
    Darcy friction factor (dimensionless), vectorized.
    Laminar (Re < 2300): f = 64/Re
    Turbulent: f = 0.25 / [log10(eps_rel/3.7 + 5.74/Re^0.9)]^2
    
    Parameters
    ----------
    Re : Reynolds number (dimensionless)
    eps_rel : relative roughness (epsilon / d), dimensionless (>= 0)
    
    Returns
    -------
    np.ndarray float64 : Darcy friction factor
    
    Notes
    -----
    - eps_rel is relative roughness (epsilon / d), dimensionless (>= 0).
    - Transitional regime is handled by the threshold at Re=2300.
    """
    Re_arr = _as_float(Re)
    rr = _as_float(eps_rel)
    Re_safe = np.maximum(Re_arr, 1e-12)
    f_lam = 64.0 / Re_safe
    # Avoid invalid log10 arguments
    core = rr / 3.7 + 5.74 / (Re_safe ** 0.9)
    core = np.maximum(core, 1e-12)
    f_turb = 0.25 / (np.log10(core) ** 2)
    return np.where(Re_arr < 2300.0, f_lam, f_turb)

def darcy_dp(L_m: ArrayLike, f: ArrayLike, rho: ArrayLike, v_ms: ArrayLike, d_m: ArrayLike) -> np.ndarray:
    """
    Darcy–Weisbach pressure drop (Pa) along a straight pipe, vectorized.
    Δp = f * (L/d) * (rho * v^2 / 2)
    
    Parameters
    ----------
    L_m : m  (pipe length)
    f :  Darcy friction factor (dimensionless)
    rho : kg/m^3
    v_ms : m/s
    d_m : m
    
    Returns
    -------
    np.ndarray float64 : pressure drop in Pascal
    """
    L = _as_float(L_m)
    ff = _as_float(f)
    r = _as_float(rho)
    v = _as_float(v_ms)
    d = _as_float(d_m)
    d = np.maximum(d, 1e-12)
    dyn = r * (v ** 2) / 2.0
    return ff * (L / d) * dyn

def heat_loss_w_per_m(d_outer_m: ArrayLike, U: ArrayLike, deltaT_K: ArrayLike) -> np.ndarray:
    """
    Linear heat loss (W/m) for a cylindrical pipe with overall heat transfer coefficient U.
    q' = U * (π * d_outer) * ΔT
    
    Parameters
    ----------
    d_outer_m : m
    U : W/(m^2·K)
    deltaT_K : K
    
    Returns
    -------
    np.ndarray float64 : W/m
    """
    do = _as_float(d_outer_m)
    uu = _as_float(U)
    dt = _as_float(deltaT_K)
    return np.pi * do * uu * dt
