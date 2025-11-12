"""
NPV-based Pipe Diameter Optimizer

This module implements an NPV-based optimization algorithm for district heating
pipe diameter selection that satisfies EN 13941 constraints (v ≤ 1.5 m/s, ΔT ≥ 30 K)
and integrates with the existing pandapipes dual-pipe system.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass
import logging
from scipy.optimize import minimize_scalar
import pandapipes as pp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PipeConstraints:
    """EN 13941 constraints for district heating pipes."""

    max_velocity_m_s: float = 1.5
    min_temperature_difference_k: float = 30.0
    max_pressure_drop_bar_per_km: float = 50.0


@dataclass
class EconomicParameters:
    """Economic parameters for NPV calculation."""

    discount_rate: float = 0.05  # 5% annual discount rate
    lifetime_years: int = 30
    electricity_cost_eur_mwh: float = 80.0
    heat_cost_eur_mwh: float = 60.0
    pump_efficiency: float = 0.75
    operation_hours_per_year: float = 8760.0


@dataclass
class PipeSegment:
    """Represents a pipe segment with its properties."""

    length_m: float
    heat_demand_kw: float
    supply_temperature_c: float
    return_temperature_c: float
    flow_rate_m3_h: float
    diameter_mm: float
    cost_per_meter_eur: float


class NPVPipeOptimizer:
    """
    NPV-based pipe diameter optimizer for district heating networks.

    This class implements optimization algorithms to select optimal pipe diameters
    based on Net Present Value (NPV) analysis while satisfying EN 13941 constraints.
    """

    def __init__(
        self,
        pipe_catalog_path: str,
        constraints: Optional[PipeConstraints] = None,
        economic_params: Optional[EconomicParameters] = None,
    ):
        """
        Initialize the NPV pipe optimizer.

        Args:
            pipe_catalog_path: Path to pipe catalog CSV file
            constraints: EN 13941 constraints (optional)
            economic_params: Economic parameters for NPV calculation (optional)
        """
        self.pipe_catalog_path = Path(pipe_catalog_path)
        self.constraints = constraints or PipeConstraints()
        self.economic_params = economic_params or EconomicParameters()
        self.pipe_catalog: Optional[pd.DataFrame] = None
        self._load_pipe_catalog()

    def _load_pipe_catalog(self) -> None:
        """Load pipe catalog from CSV file."""
        if not self.pipe_catalog_path.exists():
            raise FileNotFoundError(f"Pipe catalog not found: {self.pipe_catalog_path}")

        self.pipe_catalog = pd.read_csv(self.pipe_catalog_path)
        logger.info(f"Loaded pipe catalog with {len(self.pipe_catalog)} specifications")

    def get_available_diameters(self) -> List[float]:
        """
        Get list of available pipe diameters.

        Returns:
            List of available diameters in mm
        """
        if self.pipe_catalog is None:
            raise ValueError("Pipe catalog not loaded")

        return sorted(self.pipe_catalog["diameter_mm"].unique().tolist())

    def calculate_flow_velocity(self, flow_rate_m3_h: float, diameter_mm: float) -> float:
        """
        Calculate flow velocity in pipe.

        Args:
            flow_rate_m3_h: Flow rate in m³/h
            diameter_mm: Pipe diameter in mm

        Returns:
            Flow velocity in m/s
        """
        # Convert flow rate to m³/s
        flow_rate_m3_s = flow_rate_m3_h / 3600.0

        # Calculate cross-sectional area
        diameter_m = diameter_mm / 1000.0
        area_m2 = np.pi * (diameter_m / 2.0) ** 2

        # Calculate velocity
        velocity_m_s = flow_rate_m3_s / area_m2

        return velocity_m_s

    def calculate_pressure_drop(
        self, flow_rate_m3_h: float, diameter_mm: float, length_m: float, roughness_mm: float = 0.1
    ) -> float:
        """
        Calculate pressure drop in pipe using Darcy-Weisbach equation.

        Args:
            flow_rate_m3_h: Flow rate in m³/h
            diameter_mm: Pipe diameter in mm
            length_m: Pipe length in m
            roughness_mm: Pipe roughness in mm

        Returns:
            Pressure drop in bar
        """
        # Convert units
        diameter_m = diameter_mm / 1000.0
        roughness_m = roughness_mm / 1000.0
        flow_rate_m3_s = flow_rate_m3_h / 3600.0

        # Calculate velocity
        velocity_m_s = self.calculate_flow_velocity(flow_rate_m3_h, diameter_mm)

        # Water properties at 80°C
        density_kg_m3 = 971.8
        dynamic_viscosity_pa_s = 0.000355

        # Calculate Reynolds number
        reynolds = (density_kg_m3 * velocity_m_s * diameter_m) / dynamic_viscosity_pa_s

        # Calculate friction factor using Colebrook-White equation
        # For simplicity, using Swamee-Jain approximation
        friction_factor = (
            0.25 / (np.log10(roughness_m / (3.7 * diameter_m) + 5.74 / reynolds**0.9)) ** 2
        )

        # Calculate pressure drop using Darcy-Weisbach equation
        pressure_drop_pa = (
            friction_factor * (length_m / diameter_m) * (density_kg_m3 * velocity_m_s**2) / 2
        )

        # Convert to bar
        pressure_drop_bar = pressure_drop_pa / 100000.0

        return pressure_drop_bar

    def calculate_heat_loss(
        self,
        diameter_mm: float,
        length_m: float,
        supply_temp_c: float,
        return_temp_c: float,
        thermal_conductivity_w_mk: float = 0.035,
        insulation_thickness_mm: float = 50.0,
    ) -> float:
        """
        Calculate heat loss through pipe insulation.

        Args:
            diameter_mm: Pipe diameter in mm
            length_m: Pipe length in m
            supply_temp_c: Supply temperature in °C
            return_temp_c: Return temperature in °C
            thermal_conductivity_w_mk: Thermal conductivity of insulation
            insulation_thickness_mm: Insulation thickness in mm

        Returns:
            Heat loss in kW
        """
        # Convert units
        diameter_m = diameter_mm / 1000.0
        insulation_thickness_m = insulation_thickness_mm / 1000.0

        # Calculate average temperature
        avg_temp_c = (supply_temp_c + return_temp_c) / 2.0
        ambient_temp_c = 10.0  # Ground temperature

        # Calculate outer diameter with insulation
        outer_diameter_m = diameter_m + 2 * insulation_thickness_m

        # Calculate thermal resistance
        thermal_resistance = np.log(outer_diameter_m / diameter_m) / (
            2 * np.pi * thermal_conductivity_w_mk
        )

        # Calculate heat loss per unit length
        heat_loss_per_m_w = (avg_temp_c - ambient_temp_c) / thermal_resistance

        # Calculate total heat loss
        heat_loss_w = heat_loss_per_m_w * length_m

        # Convert to kW
        heat_loss_kw = heat_loss_w / 1000.0

        return heat_loss_kw

    def calculate_pumping_power(self, flow_rate_m3_h: float, pressure_drop_bar: float) -> float:
        """
        Calculate pumping power required.

        Args:
            flow_rate_m3_h: Flow rate in m³/h
            pressure_drop_bar: Pressure drop in bar

        Returns:
            Pumping power in kW
        """
        # Convert units
        flow_rate_m3_s = flow_rate_m3_h / 3600.0
        pressure_drop_pa = pressure_drop_bar * 100000.0

        # Calculate pumping power
        pumping_power_w = flow_rate_m3_s * pressure_drop_pa / self.economic_params.pump_efficiency

        # Convert to kW
        pumping_power_kw = pumping_power_w / 1000.0

        return pumping_power_kw

    def calculate_npv(self, initial_cost_eur: float, annual_operating_cost_eur: float) -> float:
        """
        Calculate Net Present Value.

        Args:
            initial_cost_eur: Initial investment cost in EUR
            annual_operating_cost_eur: Annual operating cost in EUR

        Returns:
            NPV in EUR
        """
        # Calculate present value of operating costs
        pv_factor = (
            1 - (1 + self.economic_params.discount_rate) ** (-self.economic_params.lifetime_years)
        ) / self.economic_params.discount_rate
        pv_operating_costs = annual_operating_cost_eur * pv_factor

        # Calculate NPV (negative because costs are negative cash flows)
        npv = -(initial_cost_eur + pv_operating_costs)

        return npv

    def check_constraints(
        self,
        flow_rate_m3_h: float,
        diameter_mm: float,
        pressure_drop_bar_per_km: float,
        temp_difference_k: float,
    ) -> bool:
        """
        Check if pipe design satisfies EN 13941 constraints.

        Args:
            flow_rate_m3_h: Flow rate in m³/h
            diameter_mm: Pipe diameter in mm
            pressure_drop_bar_per_km: Pressure drop per km in bar/km
            temp_difference_k: Temperature difference in K

        Returns:
            True if all constraints are satisfied
        """
        # Check velocity constraint
        velocity_m_s = self.calculate_flow_velocity(flow_rate_m3_h, diameter_mm)
        if velocity_m_s > self.constraints.max_velocity_m_s:
            return False

        # Check temperature difference constraint
        if temp_difference_k < self.constraints.min_temperature_difference_k:
            return False

        # Check pressure drop constraint
        if pressure_drop_bar_per_km > self.constraints.max_pressure_drop_bar_per_km:
            return False

        return True

    def optimize_diameter_for_segment(self, segment: PipeSegment) -> Tuple[float, Dict]:
        """
        Optimize pipe diameter for a single segment.

        Args:
            segment: Pipe segment to optimize

        Returns:
            Tuple of (optimal_diameter_mm, optimization_results)
        """
        logger.info(f"Optimizing diameter for segment with {segment.heat_demand_kw:.1f} kW demand")

        available_diameters = self.get_available_diameters()
        best_npv = float("-inf")
        best_diameter = None
        best_results = {}

        for diameter_mm in available_diameters:
            try:
                # Get pipe specifications
                pipe_spec = self.pipe_catalog[self.pipe_catalog["diameter_mm"] == diameter_mm].iloc[
                    0
                ]

                # Calculate pressure drop
                pressure_drop_bar = self.calculate_pressure_drop(
                    segment.flow_rate_m3_h, diameter_mm, segment.length_m
                )
                pressure_drop_bar_per_km = pressure_drop_bar / (segment.length_m / 1000.0)

                # Calculate temperature difference
                temp_difference_k = segment.supply_temperature_c - segment.return_temperature_c

                # Check constraints
                if not self.check_constraints(
                    segment.flow_rate_m3_h, diameter_mm, pressure_drop_bar_per_km, temp_difference_k
                ):
                    continue

                # Calculate heat loss
                heat_loss_kw = self.calculate_heat_loss(
                    diameter_mm,
                    segment.length_m,
                    segment.supply_temperature_c,
                    segment.return_temperature_c,
                    pipe_spec["thermal_conductivity_w_mk"],
                )

                # Calculate pumping power
                pumping_power_kw = self.calculate_pumping_power(
                    segment.flow_rate_m3_h, pressure_drop_bar
                )

                # Calculate costs
                initial_cost_eur = pipe_spec["cost_per_meter_eur"] * segment.length_m

                # Annual operating costs
                pumping_cost_eur_per_year = (
                    pumping_power_kw
                    * self.economic_params.electricity_cost_eur_mwh
                    / 1000.0
                    * self.economic_params.operation_hours_per_year
                )
                heat_loss_cost_eur_per_year = (
                    heat_loss_kw
                    * self.economic_params.heat_cost_eur_mwh
                    / 1000.0
                    * self.economic_params.operation_hours_per_year
                )
                annual_operating_cost_eur = pumping_cost_eur_per_year + heat_loss_cost_eur_per_year

                # Calculate NPV
                npv = self.calculate_npv(initial_cost_eur, annual_operating_cost_eur)

                # Update best solution
                if npv > best_npv:
                    best_npv = npv
                    best_diameter = diameter_mm
                    best_results = {
                        "diameter_mm": diameter_mm,
                        "npv_eur": npv,
                        "initial_cost_eur": initial_cost_eur,
                        "annual_operating_cost_eur": annual_operating_cost_eur,
                        "pressure_drop_bar": pressure_drop_bar,
                        "pressure_drop_bar_per_km": pressure_drop_bar_per_km,
                        "velocity_m_s": self.calculate_flow_velocity(
                            segment.flow_rate_m3_h, diameter_mm
                        ),
                        "heat_loss_kw": heat_loss_kw,
                        "pumping_power_kw": pumping_power_kw,
                        "temp_difference_k": temp_difference_k,
                        "constraints_satisfied": True,
                    }

            except Exception as e:
                logger.debug(f"Error evaluating diameter {diameter_mm}: {e}")
                continue

        if best_diameter is None:
            raise ValueError("No feasible diameter found that satisfies constraints")

        logger.info(f"Optimal diameter: {best_diameter} mm, NPV: {best_npv:.2f} EUR")
        return best_diameter, best_results

    def optimize_network(self, segments: List[PipeSegment]) -> Dict:
        """
        Optimize pipe diameters for entire network.

        Args:
            segments: List of pipe segments to optimize

        Returns:
            Dictionary with optimization results for each segment
        """
        logger.info(f"Optimizing network with {len(segments)} segments")

        results = {}
        total_initial_cost = 0.0
        total_annual_operating_cost = 0.0

        for i, segment in enumerate(segments):
            try:
                optimal_diameter, segment_results = self.optimize_diameter_for_segment(segment)
                results[f"segment_{i}"] = segment_results

                total_initial_cost += segment_results["initial_cost_eur"]
                total_annual_operating_cost += segment_results["annual_operating_cost_eur"]

            except Exception as e:
                logger.error(f"Error optimizing segment {i}: {e}")
                results[f"segment_{i}"] = {"error": str(e)}

        # Calculate network-wide NPV
        network_npv = self.calculate_npv(total_initial_cost, total_annual_operating_cost)

        results["network_summary"] = {
            "total_initial_cost_eur": total_initial_cost,
            "total_annual_operating_cost_eur": total_annual_operating_cost,
            "network_npv_eur": network_npv,
            "total_segments": len(segments),
        }

        logger.info(f"Network optimization complete. Total NPV: {network_npv:.2f} EUR")
        return results

    def create_pandapipes_network(self, segments: List[PipeSegment], optimization_results: Dict):
        """
        Create pandapipes network with optimized diameters.

        Args:
            segments: List of pipe segments
            optimization_results: Results from diameter optimization

        Returns:
            pandapipes network object
        """
        # Create pandapipes network
        net = pp.create_empty_network("optimized_dh_network")

        # Add junctions
        for i in range(len(segments) + 1):
            pp.create_junction(net, pn_bar=1.0, tfluid_k=273.15 + 80.0, name=f"junction_{i}")

        # Add pipes with optimized diameters
        for i, segment in enumerate(segments):
            segment_key = f"segment_{i}"
            if (
                segment_key in optimization_results
                and "error" not in optimization_results[segment_key]
            ):
                diameter_mm = optimization_results[segment_key]["diameter_mm"]
                diameter_m = diameter_mm / 1000.0

                pp.create_pipe_from_parameters(
                    net,
                    from_junction=i,
                    to_junction=i + 1,
                    length_km=segment.length_m / 1000.0,
                    diameter_m=diameter_m,
                    k_mm=0.1,  # Roughness
                    loss_coefficient=0.0,
                    sections=1,
                    alpha_w_per_m2k=0.0,  # No heat transfer for now
                    name=f"pipe_{i}",
                )

        return net


def create_sample_segments() -> List[PipeSegment]:
    """Create sample pipe segments for testing."""
    segments = [
        PipeSegment(
            length_m=100.0,
            heat_demand_kw=50.0,
            supply_temperature_c=80.0,
            return_temperature_c=50.0,
            flow_rate_m3_h=2.5,
            diameter_mm=50.0,  # Will be optimized
            cost_per_meter_eur=100.0,
        ),
        PipeSegment(
            length_m=150.0,
            heat_demand_kw=75.0,
            supply_temperature_c=80.0,
            return_temperature_c=50.0,
            flow_rate_m3_h=3.8,
            diameter_mm=65.0,  # Will be optimized
            cost_per_meter_eur=120.0,
        ),
    ]
    return segments


def main():
    """Main function to demonstrate NPV pipe optimization."""
    try:
        # Create sample pipe catalog if it doesn't exist
        pipe_catalog_path = "data/csv/pipe_catalog.csv"
        if not Path(pipe_catalog_path).exists():
            logger.info("Creating sample pipe catalog...")
            sample_catalog = pd.DataFrame(
                {
                    "diameter_mm": [25, 32, 40, 50, 65, 80, 100, 125, 150, 200],
                    "inner_diameter_mm": [23, 30, 38, 48, 63, 78, 98, 123, 148, 198],
                    "outer_diameter_mm": [27, 34, 42, 52, 67, 82, 102, 127, 152, 202],
                    "wall_thickness_mm": [2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                    "material": ["Stahl"] * 10,
                    "insulation_type": ["Standard"] * 10,
                    "thermal_conductivity_w_mk": [0.035] * 10,
                    "max_pressure_bar": [16.0] * 10,
                    "max_temperature_c": [120.0] * 10,
                    "cost_per_meter_eur": [50, 60, 75, 100, 130, 170, 220, 280, 350, 450],
                }
            )
            sample_catalog.to_csv(pipe_catalog_path, index=False)
            logger.info(f"Created sample pipe catalog: {pipe_catalog_path}")

        # Initialize optimizer
        optimizer = NPVPipeOptimizer(pipe_catalog_path)

        # Create sample segments
        segments = create_sample_segments()

        # Optimize network
        results = optimizer.optimize_network(segments)

        # Print results
        print("\n=== NPV Pipe Optimization Results ===")
        print(f"Network NPV: {results['network_summary']['network_npv_eur']:.2f} EUR")
        print(f"Total Initial Cost: {results['network_summary']['total_initial_cost_eur']:.2f} EUR")
        print(
            f"Total Annual Operating Cost: {results['network_summary']['total_annual_operating_cost_eur']:.2f} EUR"
        )

        print("\n=== Segment Results ===")
        for segment_key, segment_result in results.items():
            if segment_key != "network_summary" and "error" not in segment_result:
                print(f"{segment_key}:")
                print(f"  Diameter: {segment_result['diameter_mm']} mm")
                print(f"  NPV: {segment_result['npv_eur']:.2f} EUR")
                print(f"  Velocity: {segment_result['velocity_m_s']:.2f} m/s")
                print(f"  Pressure Drop: {segment_result['pressure_drop_bar_per_km']:.2f} bar/km")

        # Create pandapipes network
        net = optimizer.create_pandapipes_network(segments, results)
        print(f"\nCreated pandapipes network with {len(net.pipe)} pipes")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
