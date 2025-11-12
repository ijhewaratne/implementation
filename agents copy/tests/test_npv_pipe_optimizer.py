"""
Unit tests for NPV pipe optimizer.
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
import sys

sys.path.append(str(Path(__file__).parent.parent / "src"))

from npv_pipe_optimizer import (
    NPVPipeOptimizer,
    PipeConstraints,
    EconomicParameters,
    PipeSegment,
    create_sample_segments,
)


class TestNPVPipeOptimizer(unittest.TestCase):
    """Test cases for NPVPipeOptimizer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = os.path.join(self.temp_dir, "test_pipe_catalog.csv")

        # Create test pipe catalog
        self.test_catalog = pd.DataFrame(
            {
                "diameter_mm": [25, 32, 40, 50, 65, 80, 100],
                "inner_diameter_mm": [23, 30, 38, 48, 63, 78, 98],
                "outer_diameter_mm": [27, 34, 42, 52, 67, 82, 102],
                "wall_thickness_mm": [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                "material": ["Stahl"] * 7,
                "insulation_type": ["Standard"] * 7,
                "thermal_conductivity_w_mk": [0.035] * 7,
                "max_pressure_bar": [16.0] * 7,
                "max_temperature_c": [120.0] * 7,
                "cost_per_meter_eur": [50, 60, 75, 100, 130, 170, 220],
            }
        )

        # Save test catalog
        self.test_catalog.to_csv(self.test_csv_path, index=False)

        # Create test constraints and economic parameters
        self.constraints = PipeConstraints(
            max_velocity_m_s=1.5,
            min_temperature_difference_k=30.0,
            max_pressure_drop_bar_per_km=50.0,
        )

        self.economic_params = EconomicParameters(
            discount_rate=0.05,
            lifetime_years=30,
            electricity_cost_eur_mwh=80.0,
            heat_cost_eur_mwh=60.0,
            pump_efficiency=0.75,
            operation_hours_per_year=8760.0,
        )

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_csv_path):
            os.remove(self.test_csv_path)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

    def test_init(self):
        """Test initialization."""
        optimizer = NPVPipeOptimizer(self.test_csv_path, self.constraints, self.economic_params)

        self.assertEqual(optimizer.pipe_catalog_path, Path(self.test_csv_path))
        self.assertEqual(optimizer.constraints, self.constraints)
        self.assertEqual(optimizer.economic_params, self.economic_params)
        self.assertIsNotNone(optimizer.pipe_catalog)

    def test_load_pipe_catalog(self):
        """Test pipe catalog loading."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        self.assertIsNotNone(optimizer.pipe_catalog)
        self.assertEqual(len(optimizer.pipe_catalog), 7)
        self.assertIn("diameter_mm", optimizer.pipe_catalog.columns)
        self.assertIn("cost_per_meter_eur", optimizer.pipe_catalog.columns)

    def test_get_available_diameters(self):
        """Test getting available diameters."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        diameters = optimizer.get_available_diameters()
        expected_diameters = [25.0, 32.0, 40.0, 50.0, 65.0, 80.0, 100.0]

        self.assertEqual(diameters, expected_diameters)

    def test_calculate_flow_velocity(self):
        """Test flow velocity calculation."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Test with known values
        flow_rate_m3_h = 10.0  # 10 m³/h
        diameter_mm = 50.0  # 50 mm

        velocity = optimizer.calculate_flow_velocity(flow_rate_m3_h, diameter_mm)

        # Expected velocity: (10/3600) / (π * (0.025)²) ≈ 1.41 m/s
        expected_velocity = (10.0 / 3600.0) / (np.pi * (0.025**2))

        self.assertAlmostEqual(velocity, expected_velocity, places=2)

        # Test that velocity increases with flow rate
        velocity_high_flow = optimizer.calculate_flow_velocity(20.0, diameter_mm)
        self.assertGreater(velocity_high_flow, velocity)

        # Test that velocity decreases with diameter
        velocity_large_diameter = optimizer.calculate_flow_velocity(flow_rate_m3_h, 100.0)
        self.assertLess(velocity_large_diameter, velocity)

    def test_calculate_pressure_drop(self):
        """Test pressure drop calculation."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Test with reasonable values
        flow_rate_m3_h = 10.0
        diameter_mm = 50.0
        length_m = 100.0

        pressure_drop = optimizer.calculate_pressure_drop(flow_rate_m3_h, diameter_mm, length_m)

        # Pressure drop should be positive
        self.assertGreater(pressure_drop, 0)

        # Pressure drop should increase with flow rate
        pressure_drop_high_flow = optimizer.calculate_pressure_drop(20.0, diameter_mm, length_m)
        self.assertGreater(pressure_drop_high_flow, pressure_drop)

        # Pressure drop should increase with length
        pressure_drop_long = optimizer.calculate_pressure_drop(flow_rate_m3_h, diameter_mm, 200.0)
        self.assertGreater(pressure_drop_long, pressure_drop)

        # Pressure drop should decrease with diameter
        pressure_drop_large_diameter = optimizer.calculate_pressure_drop(
            flow_rate_m3_h, 100.0, length_m
        )
        self.assertLess(pressure_drop_large_diameter, pressure_drop)

    def test_calculate_heat_loss(self):
        """Test heat loss calculation."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Test with reasonable values
        diameter_mm = 50.0
        length_m = 100.0
        supply_temp_c = 80.0
        return_temp_c = 50.0

        heat_loss = optimizer.calculate_heat_loss(
            diameter_mm, length_m, supply_temp_c, return_temp_c
        )

        # Heat loss should be positive
        self.assertGreater(heat_loss, 0)

        # Heat loss should increase with length
        heat_loss_long = optimizer.calculate_heat_loss(
            diameter_mm, 200.0, supply_temp_c, return_temp_c
        )
        self.assertGreater(heat_loss_long, heat_loss)

        # Heat loss should increase with temperature difference
        heat_loss_high_temp = optimizer.calculate_heat_loss(diameter_mm, length_m, 90.0, 40.0)
        self.assertGreater(heat_loss_high_temp, heat_loss)

    def test_calculate_pumping_power(self):
        """Test pumping power calculation."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Test with reasonable values
        flow_rate_m3_h = 10.0
        pressure_drop_bar = 0.5

        pumping_power = optimizer.calculate_pumping_power(flow_rate_m3_h, pressure_drop_bar)

        # Pumping power should be positive
        self.assertGreater(pumping_power, 0)

        # Pumping power should increase with flow rate
        pumping_power_high_flow = optimizer.calculate_pumping_power(20.0, pressure_drop_bar)
        self.assertGreater(pumping_power_high_flow, pumping_power)

        # Pumping power should increase with pressure drop
        pumping_power_high_pressure = optimizer.calculate_pumping_power(flow_rate_m3_h, 1.0)
        self.assertGreater(pumping_power_high_pressure, pumping_power)

    def test_calculate_npv(self):
        """Test NPV calculation."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Test with reasonable values
        initial_cost_eur = 10000.0
        annual_operating_cost_eur = 1000.0

        npv = optimizer.calculate_npv(initial_cost_eur, annual_operating_cost_eur)

        # NPV should be negative (costs are negative cash flows)
        self.assertLess(npv, 0)

        # NPV should be more negative with higher costs
        npv_high_cost = optimizer.calculate_npv(20000.0, annual_operating_cost_eur)
        self.assertLess(npv_high_cost, npv)

        npv_high_operating = optimizer.calculate_npv(initial_cost_eur, 2000.0)
        self.assertLess(npv_high_operating, npv)

    def test_check_constraints(self):
        """Test constraint checking."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Test valid case
        flow_rate_m3_h = 10.0
        diameter_mm = 50.0
        pressure_drop_bar_per_km = 20.0
        temp_difference_k = 35.0

        is_valid = optimizer.check_constraints(
            flow_rate_m3_h, diameter_mm, pressure_drop_bar_per_km, temp_difference_k
        )
        self.assertTrue(is_valid)

        # Test velocity constraint violation
        velocity = optimizer.calculate_flow_velocity(flow_rate_m3_h, diameter_mm)
        if velocity > optimizer.constraints.max_velocity_m_s:
            is_valid = optimizer.check_constraints(
                flow_rate_m3_h, diameter_mm, pressure_drop_bar_per_km, temp_difference_k
            )
            self.assertFalse(is_valid)

        # Test temperature difference constraint violation
        is_valid = optimizer.check_constraints(
            flow_rate_m3_h, diameter_mm, pressure_drop_bar_per_km, 25.0
        )
        self.assertFalse(is_valid)

        # Test pressure drop constraint violation
        is_valid = optimizer.check_constraints(flow_rate_m3_h, diameter_mm, 60.0, temp_difference_k)
        self.assertFalse(is_valid)

    def test_optimize_diameter_for_segment(self):
        """Test diameter optimization for a single segment."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Create test segment
        segment = PipeSegment(
            length_m=100.0,
            heat_demand_kw=50.0,
            supply_temperature_c=80.0,
            return_temperature_c=50.0,
            flow_rate_m3_h=2.5,
            diameter_mm=50.0,
            cost_per_meter_eur=100.0,
        )

        # Optimize diameter
        optimal_diameter, results = optimizer.optimize_diameter_for_segment(segment)

        # Check results
        self.assertIsInstance(optimal_diameter, float)
        self.assertIn(optimal_diameter, optimizer.get_available_diameters())
        self.assertIsInstance(results, dict)
        self.assertIn("npv_eur", results)
        self.assertIn("diameter_mm", results)
        self.assertIn("constraints_satisfied", results)
        self.assertTrue(results["constraints_satisfied"])

    def test_optimize_network(self):
        """Test network optimization."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Create test segments
        segments = create_sample_segments()

        # Optimize network
        results = optimizer.optimize_network(segments)

        # Check results
        self.assertIsInstance(results, dict)
        self.assertIn("network_summary", results)
        self.assertIn("segment_0", results)
        self.assertIn("segment_1", results)

        network_summary = results["network_summary"]
        self.assertIn("network_npv_eur", network_summary)
        self.assertIn("total_initial_cost_eur", network_summary)
        self.assertIn("total_annual_operating_cost_eur", network_summary)
        self.assertEqual(network_summary["total_segments"], 2)

    def test_create_pandapipes_network(self):
        """Test pandapipes network creation."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Create test segments
        segments = create_sample_segments()

        # Optimize network first
        results = optimizer.optimize_network(segments)

        # Create pandapipes network
        net = optimizer.create_pandapipes_network(segments, results)

        # Check network properties
        self.assertEqual(len(net.junction), 3)  # 2 segments + 1 = 3 junctions
        self.assertEqual(len(net.pipe), 2)  # 2 pipes

        # Check that pipes have reasonable diameters
        for pipe_idx in net.pipe.index:
            diameter_m = net.pipe.at[pipe_idx, "diameter_m"]
            self.assertGreater(diameter_m, 0)
            self.assertLess(diameter_m, 0.5)  # Should be less than 500mm

    def test_file_not_found(self):
        """Test handling of non-existent pipe catalog."""
        non_existent_path = "non_existent_catalog.csv"

        with self.assertRaises(FileNotFoundError):
            optimizer = NPVPipeOptimizer(non_existent_path)

    def test_no_feasible_diameter(self):
        """Test case where no feasible diameter is found."""
        optimizer = NPVPipeOptimizer(self.test_csv_path)

        # Create segment with very high flow rate that violates constraints
        segment = PipeSegment(
            length_m=100.0,
            heat_demand_kw=1000.0,
            supply_temperature_c=80.0,
            return_temperature_c=50.0,
            flow_rate_m3_h=100.0,  # Very high flow rate
            diameter_mm=25.0,
            cost_per_meter_eur=100.0,
        )

        # This should raise an error because no diameter satisfies constraints
        with self.assertRaises(ValueError):
            optimizer.optimize_diameter_for_segment(segment)


class TestPipeConstraints(unittest.TestCase):
    """Test cases for PipeConstraints dataclass."""

    def test_default_values(self):
        """Test default constraint values."""
        constraints = PipeConstraints()

        self.assertEqual(constraints.max_velocity_m_s, 1.5)
        self.assertEqual(constraints.min_temperature_difference_k, 30.0)
        self.assertEqual(constraints.max_pressure_drop_bar_per_km, 50.0)

    def test_custom_values(self):
        """Test custom constraint values."""
        constraints = PipeConstraints(
            max_velocity_m_s=2.0,
            min_temperature_difference_k=25.0,
            max_pressure_drop_bar_per_km=40.0,
        )

        self.assertEqual(constraints.max_velocity_m_s, 2.0)
        self.assertEqual(constraints.min_temperature_difference_k, 25.0)
        self.assertEqual(constraints.max_pressure_drop_bar_per_km, 40.0)


class TestEconomicParameters(unittest.TestCase):
    """Test cases for EconomicParameters dataclass."""

    def test_default_values(self):
        """Test default economic parameter values."""
        params = EconomicParameters()

        self.assertEqual(params.discount_rate, 0.05)
        self.assertEqual(params.lifetime_years, 30)
        self.assertEqual(params.electricity_cost_eur_mwh, 80.0)
        self.assertEqual(params.heat_cost_eur_mwh, 60.0)
        self.assertEqual(params.pump_efficiency, 0.75)
        self.assertEqual(params.operation_hours_per_year, 8760.0)

    def test_custom_values(self):
        """Test custom economic parameter values."""
        params = EconomicParameters(
            discount_rate=0.08,
            lifetime_years=25,
            electricity_cost_eur_mwh=100.0,
            heat_cost_eur_mwh=80.0,
            pump_efficiency=0.80,
            operation_hours_per_year=8000.0,
        )

        self.assertEqual(params.discount_rate, 0.08)
        self.assertEqual(params.lifetime_years, 25)
        self.assertEqual(params.electricity_cost_eur_mwh, 100.0)
        self.assertEqual(params.heat_cost_eur_mwh, 80.0)
        self.assertEqual(params.pump_efficiency, 0.80)
        self.assertEqual(params.operation_hours_per_year, 8000.0)


class TestPipeSegment(unittest.TestCase):
    """Test cases for PipeSegment dataclass."""

    def test_pipe_segment_creation(self):
        """Test pipe segment creation."""
        segment = PipeSegment(
            length_m=100.0,
            heat_demand_kw=50.0,
            supply_temperature_c=80.0,
            return_temperature_c=50.0,
            flow_rate_m3_h=2.5,
            diameter_mm=50.0,
            cost_per_meter_eur=100.0,
        )

        self.assertEqual(segment.length_m, 100.0)
        self.assertEqual(segment.heat_demand_kw, 50.0)
        self.assertEqual(segment.supply_temperature_c, 80.0)
        self.assertEqual(segment.return_temperature_c, 50.0)
        self.assertEqual(segment.flow_rate_m3_h, 2.5)
        self.assertEqual(segment.diameter_mm, 50.0)
        self.assertEqual(segment.cost_per_meter_eur, 100.0)


if __name__ == "__main__":
    unittest.main()
