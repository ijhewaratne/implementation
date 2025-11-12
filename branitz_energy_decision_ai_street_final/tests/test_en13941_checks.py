"""
Tests for en13941_checks module.

This module contains comprehensive tests for EN 13941 validation functions
used in district heating network design and operation.
"""

import pytest
from optimize.en13941_checks import check_velocity, check_deltaT


class TestCheckVelocity:
    """Test velocity limit checks."""
    
    def test_check_velocity_pass_fail(self):
        """Test velocity check pass/fail scenarios."""
        # v_max=1.45, default limit → True
        assert check_velocity(1.45) is True
        
        # v_max=1.51, default → False
        assert check_velocity(1.51) is False
        
        # custom limit=1.6 with v_max=1.55 → True
        assert check_velocity(1.55, limit=1.6) is True
        
        # v_max exactly at limit → True (inclusive)
        assert check_velocity(1.5, limit=1.5) is True
    
    def test_check_velocity_guards(self):
        """Test input validation guards."""
        # Test negative velocity
        with pytest.raises(ValueError, match="Maximum velocity must be non-negative"):
            check_velocity(-0.5)
        
        # Test zero velocity (should pass)
        assert check_velocity(0.0) is True
        
        # Test zero limit
        with pytest.raises(ValueError, match="Velocity limit must be positive"):
            check_velocity(1.0, limit=0)
        
        # Test negative limit
        with pytest.raises(ValueError, match="Velocity limit must be positive"):
            check_velocity(1.0, limit=-1.0)
    
    def test_check_velocity_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with very small velocity
        assert check_velocity(0.001) is True
        
        # Test with very large velocity
        assert check_velocity(10.0) is False
        
        # Test with very small limit
        assert check_velocity(0.1, limit=0.05) is False
        
        # Test with very large limit
        assert check_velocity(5.0, limit=10.0) is True
        
        # Test with equal values
        assert check_velocity(2.0, limit=2.0) is True


class TestCheckDeltaT:
    """Test temperature difference checks."""
    
    def test_check_deltaT_pass_fail(self):
        """Test temperature difference check pass/fail scenarios."""
        # deltaT=30.0, default → True
        assert check_deltaT(30.0) is True
        
        # deltaT=29.9 → False
        assert check_deltaT(29.9) is False
        
        # custom min_deltaT=25 with deltaT=27 → True
        assert check_deltaT(27.0, min_deltaT=25.0) is True
        
        # deltaT exactly at minimum → True (inclusive)
        assert check_deltaT(30.0, min_deltaT=30.0) is True
    
    def test_check_deltaT_guards(self):
        """Test input validation guards."""
        # Test negative deltaT
        with pytest.raises(ValueError, match="Delivered temperature difference must be non-negative"):
            check_deltaT(-5.0)
        
        # Test zero deltaT (should fail with default min_deltaT=30.0)
        assert check_deltaT(0.0) is False
        
        # Test zero min_deltaT
        with pytest.raises(ValueError, match="Minimum temperature difference must be positive"):
            check_deltaT(25.0, min_deltaT=0)
        
        # Test negative min_deltaT
        with pytest.raises(ValueError, match="Minimum temperature difference must be positive"):
            check_deltaT(25.0, min_deltaT=-10.0)
    
    def test_check_deltaT_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with very small deltaT
        assert check_deltaT(0.1, min_deltaT=0.05) is True
        
        # Test with very large deltaT
        assert check_deltaT(100.0) is True
        
        # Test with very small min_deltaT
        assert check_deltaT(1.0, min_deltaT=0.5) is True
        
        # Test with very large min_deltaT
        assert check_deltaT(50.0, min_deltaT=60.0) is False
        
        # Test with equal values
        assert check_deltaT(25.0, min_deltaT=25.0) is True
        
        # Test with zero deltaT and zero min_deltaT (should raise error)
        with pytest.raises(ValueError, match="Minimum temperature difference must be positive"):
            check_deltaT(0.0, min_deltaT=0.0)
    
    def test_check_deltaT_typical_scenarios(self):
        """Test typical district heating scenarios."""
        # Typical 80/50°C design (ΔT=30K)
        assert check_deltaT(30.0) is True
        
        # Good design with higher ΔT
        assert check_deltaT(35.0) is True
        
        # Poor design with lower ΔT
        assert check_deltaT(25.0) is False
        
        # Modern low-temperature design (70/40°C, ΔT=30K)
        assert check_deltaT(30.0, min_deltaT=30.0) is True
        
        # Ultra-low temperature design (55/25°C, ΔT=30K)
        assert check_deltaT(30.0, min_deltaT=25.0) is True


class TestIntegration:
    """Test integration between functions."""
    
    def test_velocity_and_deltaT_combined(self):
        """Test that both checks can be used together."""
        # Good design: acceptable velocity and temperature difference
        velocity_ok = check_velocity(1.3)
        deltaT_ok = check_deltaT(32.0)
        assert velocity_ok is True
        assert deltaT_ok is True
        
        # Poor design: high velocity and low temperature difference
        velocity_ok = check_velocity(1.8)
        deltaT_ok = check_deltaT(25.0)
        assert velocity_ok is False
        assert deltaT_ok is False
        
        # Mixed design: good velocity but poor temperature difference
        velocity_ok = check_velocity(1.2)
        deltaT_ok = check_deltaT(28.0)
        assert velocity_ok is True
        assert deltaT_ok is False
    
    def test_consistent_behavior(self):
        """Test consistent behavior across different input types."""
        # Test with float inputs
        assert check_velocity(1.5) is True
        assert check_deltaT(30.0) is True
        
        # Test with integer inputs (should work the same)
        assert check_velocity(1) is True
        assert check_deltaT(30) is True
        
        # Test with very small float differences
        assert check_velocity(1.5000001) is False  # Slightly above limit
        assert check_deltaT(29.9999999) is False   # Slightly below minimum


if __name__ == "__main__":
    pytest.main([__file__]) 