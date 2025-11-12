"""
Tests for cost_models module.

This module contains comprehensive tests for cost calculation functions
used in district heating network economic analysis.
"""

import math
import pytest
from optimize.cost_models import annual_pump_energy_mwhel, npv


class TestAnnualPumpEnergy:
    """Test annual pump energy calculation."""

    def test_annual_pump_energy_mwhel_basic(self):
        """Test basic annual pump energy calculation."""
        # Use: dp=50_000 Pa, V=0.02 m^3/s, eta=0.65, hours=3000
        # Expected: E = dp * V * hours / (eta * 1e6)
        # → 50_000 * 0.02 * 3000 / (0.65 * 1e6) ≈ 4.61538 MWh
        result = annual_pump_energy_mwhel(50000, 0.02, 0.65, 3000)
        expected = (50000 * 0.02 * 3000) / (0.65 * 1e6)
        assert math.isclose(result, expected, rel_tol=1e-6)

    def test_annual_pump_energy_mwhel_guards(self):
        """Test input validation guards."""
        # Test zero/negative pressure drop
        with pytest.raises(ValueError, match="Pressure drop must be positive"):
            annual_pump_energy_mwhel(0, 0.02, 0.65, 3000)

        with pytest.raises(ValueError, match="Pressure drop must be positive"):
            annual_pump_energy_mwhel(-1000, 0.02, 0.65, 3000)

        # Test zero/negative flow rate
        with pytest.raises(ValueError, match="Flow rate must be positive"):
            annual_pump_energy_mwhel(50000, 0, 0.65, 3000)

        with pytest.raises(ValueError, match="Flow rate must be positive"):
            annual_pump_energy_mwhel(50000, -0.01, 0.65, 3000)

        # Test zero/negative pump efficiency
        with pytest.raises(ValueError, match="Pump efficiency must be positive"):
            annual_pump_energy_mwhel(50000, 0.02, 0, 3000)

        with pytest.raises(ValueError, match="Pump efficiency must be positive"):
            annual_pump_energy_mwhel(50000, 0.02, -0.1, 3000)

        # Test pump efficiency > 1.0 (unphysical)
        with pytest.raises(ValueError, match="Pump efficiency cannot exceed 1.0"):
            annual_pump_energy_mwhel(50000, 0.02, 1.1, 3000)

        # Test zero/negative operating hours
        with pytest.raises(ValueError, match="Operating hours must be positive"):
            annual_pump_energy_mwhel(50000, 0.02, 0.65, 0)

        with pytest.raises(ValueError, match="Operating hours must be positive"):
            annual_pump_energy_mwhel(50000, 0.02, 0.65, -100)

    def test_annual_pump_energy_mwhel_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with very small values
        result = annual_pump_energy_mwhel(1, 0.001, 0.5, 1)
        expected = (1 * 0.001 * 1) / (0.5 * 1e6)
        assert math.isclose(result, expected, rel_tol=1e-10)

        # Test with maximum pump efficiency
        result = annual_pump_energy_mwhel(10000, 0.01, 1.0, 1000)
        expected = (10000 * 0.01 * 1000) / (1.0 * 1e6)
        assert math.isclose(result, expected, rel_tol=1e-10)

        # Test with high pressure and flow
        result = annual_pump_energy_mwhel(1000000, 1.0, 0.8, 8760)
        expected = (1000000 * 1.0 * 8760) / (0.8 * 1e6)
        assert math.isclose(result, expected, rel_tol=1e-10)


class TestNPV:
    """Test net present value calculation."""

    def test_npv_scalar_costs(self):
        """Test NPV with constant annual costs."""
        # capex=100_000, annual_cost=10_000, years=5, r=0.05
        # Expected scalar annuity PV: sum(10000/(1.05**y) for y in range(1,6)) + 100000
        result = npv(100000, 10000, 5, 0.05)

        # Calculate expected value manually
        expected_pv_annuity = sum(10000 / (1.05 ** (i + 1)) for i in range(5))
        expected = 100000 + expected_pv_annuity

        assert math.isclose(result, expected, rel_tol=1e-6)

    def test_npv_zero_discount_scalar(self):
        """Test NPV with zero discount rate and scalar costs."""
        # r=0, capex=50_000, annual_cost=5_000, years=4 → 50_000 + 20_000 = 70_000
        result = npv(50000, 5000, 4, 0)
        expected = 50000 + 5000 * 4
        assert math.isclose(result, expected, rel_tol=1e-10)

    def test_npv_series_costs(self):
        """Test NPV with varying annual costs."""
        # annual_cost=[8000,9000,10000,11000,12000], years=5, r=0.04
        annual_costs = [8000, 9000, 10000, 11000, 12000]
        result = npv(50000, annual_costs, 5, 0.04)

        # Calculate expected value manually
        expected_pv_costs = sum(cost / (1.04 ** (i + 1)) for i, cost in enumerate(annual_costs))
        expected = 50000 + expected_pv_costs

        assert math.isclose(result, expected, rel_tol=1e-6)

    def test_npv_zero_discount_series(self):
        """Test NPV with zero discount rate and series costs."""
        annual_costs = [8000, 9000, 10000]
        result = npv(50000, annual_costs, 3, 0)
        expected = 50000 + sum(annual_costs)
        assert math.isclose(result, expected, rel_tol=1e-10)

    def test_npv_series_shorter_than_years(self):
        """Test NPV with sequence shorter than years."""
        annual_costs = [8000, 9000]  # Only 2 years
        with pytest.raises(ValueError, match="Annual cost sequence length"):
            npv(50000, annual_costs, 3, 0.05)

    def test_npv_guards(self):
        """Test input validation guards."""
        # Test negative capex
        with pytest.raises(ValueError, match="Capital expenditure must be non-negative"):
            npv(-1000, 10000, 5, 0.05)

        # Test zero years
        with pytest.raises(ValueError, match="Project lifetime must be at least 1 year"):
            npv(100000, 10000, 0, 0.05)

        # Test negative years
        with pytest.raises(ValueError, match="Project lifetime must be at least 1 year"):
            npv(100000, 10000, -1, 0.05)

        # Test negative discount rate
        with pytest.raises(ValueError, match="Discount rate must be non-negative"):
            npv(100000, 10000, 5, -0.05)

        # Test negative scalar annual cost
        with pytest.raises(ValueError, match="Annual cost must be non-negative"):
            npv(100000, -1000, 5, 0.05)

        # Test negative values in sequence
        with pytest.raises(ValueError, match="Annual cost at year 1 must be non-negative"):
            npv(100000, [-1000, 2000, 3000], 3, 0.05)

        # Test invalid annual cost type
        with pytest.raises(ValueError, match="Annual cost must be scalar or sequence"):
            npv(100000, "invalid", 5, 0.05)

    def test_npv_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with zero capex
        result = npv(0, 1000, 3, 0.05)
        expected_pv = 1000 * (1 - (1.05 ** (-3))) / 0.05
        assert math.isclose(result, expected_pv, rel_tol=1e-6)

        # Test with zero annual cost
        result = npv(100000, 0, 5, 0.05)
        assert math.isclose(result, 100000, rel_tol=1e-10)

        # Test with zero discount rate and zero annual cost
        result = npv(100000, 0, 5, 0)
        assert math.isclose(result, 100000, rel_tol=1e-10)

        # Test with very high discount rate
        result = npv(100000, 10000, 3, 0.5)  # 50% discount rate
        expected_pv = 10000 * (1 - (1.5 ** (-3))) / 0.5
        expected = 100000 + expected_pv
        assert math.isclose(result, expected, rel_tol=1e-6)

    def test_npv_tuple_input(self):
        """Test NPV with tuple input for annual costs."""
        annual_costs = (8000, 9000, 10000)
        result = npv(50000, annual_costs, 3, 0.04)

        expected_pv_costs = sum(cost / (1.04 ** (i + 1)) for i, cost in enumerate(annual_costs))
        expected = 50000 + expected_pv_costs

        assert math.isclose(result, expected, rel_tol=1e-6)

    def test_npv_int_inputs(self):
        """Test NPV with integer inputs."""
        result = npv(100000, 10000, 5, 0)
        expected = 100000 + 10000 * 5
        assert math.isclose(result, expected, rel_tol=1e-10)

        # Test with integer sequence
        result = npv(50000, [8000, 9000, 10000], 3, 0)
        expected = 50000 + 8000 + 9000 + 10000
        assert math.isclose(result, expected, rel_tol=1e-10)


if __name__ == "__main__":
    pytest.main([__file__])
