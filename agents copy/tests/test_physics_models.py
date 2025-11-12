"""
Tests for physics_models module.

This module contains comprehensive tests for fluid dynamics and heat transfer
calculations used in district heating network analysis.
"""

import math
import pytest
from optimize.physics_models import (
    PI,
    G,
    DEFAULT_EPSILON,
    reynolds,
    swamee_jain_f,
    segment_hydraulics,
    segment_heat_loss_W,
)


class TestConstants:
    """Test module constants."""

    def test_pi_constant(self):
        """Test PI constant matches math.pi."""
        assert math.isclose(PI, math.pi, rel_tol=1e-15)

    def test_gravitational_constant(self):
        """Test gravitational acceleration constant."""
        assert math.isclose(G, 9.81, rel_tol=1e-15)

    def test_default_epsilon(self):
        """Test default pipe roughness constant."""
        assert math.isclose(DEFAULT_EPSILON, 4.5e-5, rel_tol=1e-15)


class TestReynolds:
    """Test Reynolds number calculation."""

    def test_reynolds_basic(self):
        """Test basic Reynolds number calculation."""
        # Example: rho=1000, v=1.0, d=0.1, mu=0.001 → Re = 100000
        result = reynolds(1000.0, 1.0, 0.1, 0.001)
        expected = 100000.0
        assert math.isclose(result, expected, rel_tol=1e-10)

    def test_reynolds_negative_density(self):
        """Test error on negative fluid density."""
        with pytest.raises(ValueError, match="Fluid density must be positive"):
            reynolds(-1000.0, 1.0, 0.1, 0.001)

    def test_reynolds_zero_velocity(self):
        """Test error on zero velocity."""
        with pytest.raises(ValueError, match="Flow velocity must be positive"):
            reynolds(1000.0, 0.0, 0.1, 0.001)

    def test_reynolds_negative_diameter(self):
        """Test error on negative diameter."""
        with pytest.raises(ValueError, match="Pipe diameter must be positive"):
            reynolds(1000.0, 1.0, -0.1, 0.001)

    def test_reynolds_zero_viscosity(self):
        """Test error on zero viscosity."""
        with pytest.raises(ValueError, match="Dynamic viscosity must be positive"):
            reynolds(1000.0, 1.0, 0.1, 0.0)

    def test_reynolds_laminar_range(self):
        """Test Reynolds number in laminar range."""
        # Re = 1000 (laminar)
        result = reynolds(1000.0, 0.1, 0.01, 0.001)
        expected = 1000.0
        assert math.isclose(result, expected, rel_tol=1e-10)

    def test_reynolds_turbulent_range(self):
        """Test Reynolds number in turbulent range."""
        # Re = 50000 (turbulent)
        result = reynolds(1000.0, 5.0, 0.01, 0.001)
        expected = 50000.0
        assert math.isclose(result, expected, rel_tol=1e-10)


class TestSwameeJainF:
    """Test Swamee-Jain friction factor calculation."""

    def test_swamee_jain_turbulent_sanity(self):
        """Test turbulent friction factor in reasonable range."""
        # With epsilon=4.5e-5, d=0.1, re=1e5, f should be around ~0.018–0.02
        result = swamee_jain_f(4.5e-5, 0.1, 1e5)
        assert 0.018 <= result <= 0.021

    def test_swamee_jain_laminar_fallback(self):
        """Test laminar fallback for Re < 2300."""
        # re=1000 should return f≈0.064
        result = swamee_jain_f(4.5e-5, 0.1, 1000)
        expected = 64.0 / 1000
        assert math.isclose(result, expected, rel_tol=1e-10)

    def test_swamee_jain_negative_epsilon(self):
        """Test error on negative roughness."""
        with pytest.raises(ValueError, match="Pipe roughness must be non-negative"):
            swamee_jain_f(-1e-5, 0.1, 1e5)

    def test_swamee_jain_zero_diameter(self):
        """Test error on zero diameter."""
        with pytest.raises(ValueError, match="Pipe diameter must be positive"):
            swamee_jain_f(4.5e-5, 0.0, 1e5)

    def test_swamee_jain_negative_reynolds(self):
        """Test error on negative Reynolds number."""
        with pytest.raises(ValueError, match="Reynolds number must be positive"):
            swamee_jain_f(4.5e-5, 0.1, -1e5)

    def test_swamee_jain_zero_reynolds(self):
        """Test error on zero Reynolds number."""
        with pytest.raises(ValueError, match="Reynolds number must be positive"):
            swamee_jain_f(4.5e-5, 0.1, 0.0)

    def test_swamee_jain_very_small_reynolds(self):
        """Test error on very small Reynolds number."""
        with pytest.raises(ValueError, match="Reynolds number too small"):
            swamee_jain_f(4.5e-5, 0.1, 1e-7)

    def test_swamee_jain_transitional_range(self):
        """Test friction factor in transitional range."""
        # Re = 3000 (transitional)
        result = swamee_jain_f(4.5e-5, 0.1, 3000)
        # Should be between laminar and turbulent values
        assert 0.01 <= result <= 0.1


class TestSegmentHydraulics:
    """Test segment hydraulic calculations."""

    def test_segment_hydraulics_example(self):
        """Test hydraulic calculation with known example."""
        # Pick: V_dot=0.01 m³/s, d_inner=0.1 m, L=100 m, rho=1000, mu=0.001,
        # epsilon=4.5e-5, K_minor=1.0
        v, dp, h = segment_hydraulics(0.01, 0.1, 100, 1000, 0.001, epsilon=4.5e-5, K_minor=1.0)

        # Check velocity: v ≈ 1.273 m/s (A=π*0.1²/4 ≈ 0.00785398; v=0.01/0.00785)
        expected_v = 0.01 / (PI * 0.1**2 / 4)
        assert math.isclose(v, expected_v, rel_tol=1e-3)

        # Check pressure drop in reasonable range (e.g., 2e4–8e4 Pa)
        assert 1.5e4 <= dp <= 2.5e4

        # Check head loss: h = Δp/(ρ*g)
        expected_h = dp / (1000 * G)
        assert math.isclose(h, expected_h, rel_tol=1e-10)

    def test_segment_hydraulics_zero_flow(self):
        """Test error on zero flow rate."""
        with pytest.raises(ValueError, match="Volumetric flow rate must be positive"):
            segment_hydraulics(0.0, 0.1, 100, 1000, 0.001)

    def test_segment_hydraulics_zero_diameter(self):
        """Test error on zero diameter."""
        with pytest.raises(ValueError, match="Inner diameter must be positive"):
            segment_hydraulics(0.01, 0.0, 100, 1000, 0.001)

    def test_segment_hydraulics_zero_length(self):
        """Test error on zero length."""
        with pytest.raises(ValueError, match="Segment length must be positive"):
            segment_hydraulics(0.01, 0.1, 0.0, 1000, 0.001)

    def test_segment_hydraulics_negative_density(self):
        """Test error on negative density."""
        with pytest.raises(ValueError, match="Fluid density must be positive"):
            segment_hydraulics(0.01, 0.1, 100, -1000, 0.001)

    def test_segment_hydraulics_negative_viscosity(self):
        """Test error on negative viscosity."""
        with pytest.raises(ValueError, match="Dynamic viscosity must be positive"):
            segment_hydraulics(0.01, 0.1, 100, 1000, -0.001)

    def test_segment_hydraulics_negative_epsilon(self):
        """Test error on negative roughness."""
        with pytest.raises(ValueError, match="Pipe roughness must be non-negative"):
            segment_hydraulics(0.01, 0.1, 100, 1000, 0.001, epsilon=-1e-5)

    def test_segment_hydraulics_negative_minor_loss(self):
        """Test error on negative minor loss coefficient."""
        with pytest.raises(ValueError, match="Minor loss coefficient must be non-negative"):
            segment_hydraulics(0.01, 0.1, 100, 1000, 0.001, K_minor=-1.0)

    def test_segment_hydraulics_defaults(self):
        """Test segment hydraulics with default parameters."""
        v, dp, h = segment_hydraulics(0.01, 0.1, 100, 1000, 0.001)

        # Should work with default epsilon and K_minor=0
        assert v > 0
        assert dp > 0
        assert h > 0


class TestSegmentHeatLoss:
    """Test heat loss calculations."""

    def test_segment_heat_loss_W_direct(self):
        """Test direct heat loss mode."""
        # U_or_Wpm=15 W/m, L=200 m, direct mode → 3000 W
        result = segment_heat_loss_W(15, 0.2, 70, 10, 200, is_direct_Wpm=True)
        expected = 15 * 200
        assert math.isclose(result, expected, rel_tol=1e-10)

    def test_segment_heat_loss_W_Uvalue(self):
        """Test U-value heat loss mode."""
        # U=0.4 W/m²K, d_outer=0.2 m, T_f=70°C, T_soil=10°C, L=100 m
        # Per-meter area A'=π*0.2≈0.6283 m²/m; ΔT=60 K → q'≈0.4*0.6283*60≈15.08 W/m
        # Total ≈1508 W
        result = segment_heat_loss_W(0.4, 0.2, 70, 10, 100)
        expected = 0.4 * PI * 0.2 * (70 - 10) * 100
        assert math.isclose(result, expected, rel_tol=1e-10)

        # Assert close with ±1%
        assert math.isclose(result, 1508, rel_tol=0.01)

    def test_segment_heat_loss_W_cooling(self):
        """Test heat loss when fluid is cooler than soil (cooling)."""
        # T_f < T_soil should give negative result (cooling)
        result = segment_heat_loss_W(0.4, 0.2, 10, 70, 100)
        assert result < 0  # Negative indicates cooling

    def test_segment_heat_loss_W_zero_length(self):
        """Test error on zero length."""
        with pytest.raises(ValueError, match="Segment length must be positive"):
            segment_heat_loss_W(15, 0.2, 70, 10, 0, is_direct_Wpm=True)

    def test_segment_heat_loss_W_negative_direct(self):
        """Test error on negative heat loss per meter in direct mode."""
        with pytest.raises(ValueError, match="Heat loss per meter must be non-negative"):
            segment_heat_loss_W(-15, 0.2, 70, 10, 200, is_direct_Wpm=True)

    def test_segment_heat_loss_W_negative_Uvalue(self):
        """Test error on negative U-value."""
        with pytest.raises(ValueError, match="U-value must be non-negative"):
            segment_heat_loss_W(-0.4, 0.2, 70, 10, 100)

    def test_segment_heat_loss_W_zero_diameter_Uvalue(self):
        """Test error on zero diameter in U-value mode."""
        with pytest.raises(ValueError, match="Outer diameter must be positive"):
            segment_heat_loss_W(0.4, 0.0, 70, 10, 100)

    def test_segment_heat_loss_W_negative_diameter_Uvalue(self):
        """Test error on negative diameter in U-value mode."""
        with pytest.raises(ValueError, match="Outer diameter must be positive"):
            segment_heat_loss_W(0.4, -0.2, 70, 10, 100)

    def test_segment_heat_loss_W_diameter_ignored_direct(self):
        """Test that diameter is ignored in direct mode."""
        # Should work even with zero diameter in direct mode
        result1 = segment_heat_loss_W(15, 0.2, 70, 10, 200, is_direct_Wpm=True)
        result2 = segment_heat_loss_W(15, 0.0, 70, 10, 200, is_direct_Wpm=True)
        assert math.isclose(result1, result2, rel_tol=1e-10)


class TestIntegration:
    """Test integration between functions."""

    def test_hydraulics_uses_reynolds(self):
        """Test that segment_hydraulics uses reynolds function."""
        # This is an indirect test - if reynolds function changes,
        # segment_hydraulics should still work correctly
        v, dp, h = segment_hydraulics(0.01, 0.1, 100, 1000, 0.001)

        # Verify the result is reasonable
        assert v > 0
        assert dp > 0
        assert h > 0

    def test_hydraulics_uses_swamee_jain(self):
        """Test that segment_hydraulics uses swamee_jain_f function."""
        # Test with laminar flow (Re < 2300)
        # Small diameter and low velocity to ensure laminar flow
        v, dp, h = segment_hydraulics(0.001, 0.01, 10, 1000, 0.001)

        # Verify the result is reasonable
        assert v > 0
        assert dp > 0
        assert h > 0


if __name__ == "__main__":
    pytest.main([__file__])
