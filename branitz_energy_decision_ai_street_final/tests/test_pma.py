"""
Tests for Physics Modeling Agent (PMA) functions.

Tests vectorized physics functions with reference values, broadcasting,
and edge case handling.
"""

import numpy as np
import pytest
from agents import pma


def test_reynolds_scalar_and_array():
    """Test Reynolds number calculation with scalars and arrays."""
    # Scalar test
    Re = pma.calc_reynolds(v_ms=1.0, d_m=0.1, rho=1000.0, mu=1e-3)
    assert np.isfinite(Re) and abs(Re - 100000.0) < 1e-6
    
    # Array test
    Re_arr = pma.calc_reynolds(v_ms=[0.5, 1.0], d_m=0.1, rho=1000.0, mu=1e-3)
    assert np.allclose(Re_arr, np.array([50000.0, 100000.0]))
    
    # Broadcasting test
    Re_broad = pma.calc_reynolds(v_ms=np.array([0.5, 1.0, 1.5]), d_m=0.1, rho=1000.0, mu=1e-3)
    assert Re_broad.shape == (3,)
    assert np.allclose(Re_broad, np.array([50000.0, 100000.0, 150000.0]))


def test_friction_laminar_and_turbulent():
    """Test friction factor calculation for laminar and turbulent flow."""
    # Laminar reference (Re = 1000)
    f_lam = pma.friction_factor_swamee_jain(Re=1000.0, eps_rel=1e-5)
    assert np.allclose(f_lam, 0.064, rtol=1e-3)
    
    # Turbulent reference (Re = 1e5, eps_rel = 2e-4)
    f_turb = pma.friction_factor_swamee_jain(Re=1e5, eps_rel=2e-4)
    assert np.allclose(float(f_turb), 0.0190, atol=1e-3)
    
    # Array test with mixed laminar/turbulent
    Re_mixed = np.array([1000, 1e5, 5000])
    eps_rel = 2e-4
    f_mixed = pma.friction_factor_swamee_jain(Re=Re_mixed, eps_rel=eps_rel)
    assert f_mixed.shape == (3,)
    assert f_mixed[0] > f_mixed[1]  # Laminar > turbulent friction factor


def test_darcy_dp_example_and_zero_flow_stability():
    """Test Darcy pressure drop calculation with example and zero flow stability."""
    # Example: L=100 m, d=0.1 m, rho=1000, v=1 m/s, Re=1e5 -> f ~ 0.019 (turbulent)
    f = float(pma.friction_factor_swamee_jain(1e5, 2e-4))
    dp = float(pma.darcy_dp(L_m=100.0, f=f, rho=1000.0, v_ms=1.0, d_m=0.1))
    # Expected around: f * (L/d) * (rho v^2 / 2) = f * 1000 * 500 ≈ 0.019 * 500000 = 9500 Pa
    assert 8000.0 <= dp <= 11000.0
    
    # Zero flow shouldn't produce NaNs (dp=0)
    dp0 = pma.darcy_dp(L_m=100.0, f=f, rho=1000.0, v_ms=0.0, d_m=0.1)
    assert np.all(np.isfinite(dp0)) and np.allclose(dp0, 0.0)
    
    # Array test
    v_array = np.array([0.5, 1.0, 1.5])
    dp_array = pma.darcy_dp(L_m=100.0, f=f, rho=1000.0, v_ms=v_array, d_m=0.1)
    assert dp_array.shape == (3,)
    assert np.all(dp_array > 0)  # All positive pressure drops


def test_heat_loss_linear_model():
    """Test heat loss calculation with exact mathematical verification."""
    # d_o=0.1 m, U=0.4 W/m^2K, ΔT=50 K => q' = π*0.1*0.4*50 ≈ 6.283...
    q = float(pma.heat_loss_w_per_m(0.1, 0.4, 50.0))
    expected = np.pi * 0.1 * 0.4 * 50.0
    assert abs(q - expected) < 1e-9
    
    # Array test
    d_outer_array = np.array([0.1, 0.2, 0.3])
    q_array = pma.heat_loss_w_per_m(d_outer_array, 0.4, 50.0)
    assert q_array.shape == (3,)
    assert np.allclose(q_array, np.pi * d_outer_array * 0.4 * 50.0)


def test_broadcasting_shapes():
    """Test broadcasting behavior across different input shapes."""
    # v shape (3,), others scalar -> (3,)
    Re = pma.calc_reynolds(v_ms=np.array([0.5, 1.0, 1.5]), d_m=0.1, rho=1000.0, mu=1e-3)
    assert Re.shape == (3,)
    
    # 2D broadcasting
    v_2d = np.array([[0.5, 1.0], [1.5, 2.0]])
    Re_2d = pma.calc_reynolds(v_ms=v_2d, d_m=0.1, rho=1000.0, mu=1e-3)
    assert Re_2d.shape == (2, 2)
    
    # Mixed broadcasting
    v_mixed = np.array([0.5, 1.0, 1.5])
    d_mixed = np.array([0.1, 0.2])
    Re_mixed = pma.calc_reynolds(v_ms=v_mixed[:, None], d_m=d_mixed[None, :], rho=1000.0, mu=1e-3)
    assert Re_mixed.shape == (3, 2)


def test_edge_cases_and_stability():
    """Test edge cases and numerical stability."""
    # Very small Reynolds numbers
    f_small = pma.friction_factor_swamee_jain(Re=1e-10, eps_rel=1e-5)
    assert np.isfinite(f_small)
    
    # Very large Reynolds numbers
    f_large = pma.friction_factor_swamee_jain(Re=1e8, eps_rel=1e-5)
    assert np.isfinite(f_large) and f_large > 0
    
    # Zero velocity in Darcy calculation
    dp_zero = pma.darcy_dp(L_m=100.0, f=0.02, rho=1000.0, v_ms=0.0, d_m=0.1)
    assert np.allclose(dp_zero, 0.0)
    
    # Negative temperature difference in heat loss
    q_neg = pma.heat_loss_w_per_m(0.1, 0.4, -50.0)
    assert np.allclose(q_neg, -np.pi * 0.1 * 0.4 * 50.0)


def test_formula_verification():
    """Verify that formulas match the specified mathematical expressions."""
    # Reynolds: Re = rho * v * d / mu
    v, d, rho, mu = 2.0, 0.05, 998.0, 1e-3
    Re = pma.calc_reynolds(v, d, rho, mu)
    expected_Re = rho * v * d / mu
    assert np.allclose(Re, expected_Re)
    
    # Darcy: Δp = f * (L/d) * (rho * v^2 / 2)
    L, f, v, d = 50.0, 0.02, 1.5, 0.1
    dp = pma.darcy_dp(L, f, rho, v, d)
    expected_dp = f * (L / d) * (rho * v**2 / 2)
    assert np.allclose(dp, expected_dp)
    
    # Heat loss: q' = U * (π * d_outer) * ΔT
    d_outer, U, deltaT = 0.15, 0.3, 40.0
    q = pma.heat_loss_w_per_m(d_outer, U, deltaT)
    expected_q = U * (np.pi * d_outer) * deltaT
    assert np.allclose(q, expected_q)


if __name__ == "__main__":
    # Run all tests
    test_reynolds_scalar_and_array()
    test_friction_laminar_and_turbulent()
    test_darcy_dp_example_and_zero_flow_stability()
    test_heat_loss_linear_model()
    test_broadcasting_shapes()
    test_edge_cases_and_stability()
    test_formula_verification()
    print("✅ All PMA tests passed!")

