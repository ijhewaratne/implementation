"""
NPV-based District Heating Integration

This module integrates the NPV-based pipe diameter optimizer with the existing
dual-pipe district heating system, providing optimized pipe selection for
the pandapipes network builder.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import logging
import geopandas as gpd
import pandapipes as pp

# Import local modules
from npv_pipe_optimizer import NPVPipeOptimizer, PipeSegment, PipeConstraints, EconomicParameters
from pipe_catalog_extractor import PipeCatalogExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptimizedPipeSegment:
    """Represents an optimized pipe segment with NPV analysis results."""

    segment_id: str
    from_junction: int
    to_junction: int
    length_m: float
    heat_demand_kw: float
    flow_rate_m3_h: float
    optimal_diameter_mm: float
    npv_eur: float
    initial_cost_eur: float
    annual_operating_cost_eur: float
    pressure_drop_bar: float
    velocity_m_s: float
    heat_loss_kw: float
    pumping_power_kw: float
    constraints_satisfied: bool


class NPVDHIntegration:
    """
    Integration class for NPV-based district heating optimization.

    This class integrates the NPV pipe optimizer with the existing dual-pipe
    district heating system, providing optimized pipe selection and analysis.
    """

    def __init__(
        self,
        pipe_catalog_path: str,
        constraints: Optional[PipeConstraints] = None,
        economic_params: Optional[EconomicParameters] = None,
    ):
        """
        Initialize the NPV DH integration.

        Args:
            pipe_catalog_path: Path to pipe catalog CSV file
            constraints: EN 13941 constraints (optional)
            economic_params: Economic parameters for NPV calculation (optional)
        """
        self.pipe_catalog_path = Path(pipe_catalog_path)
        self.constraints = constraints or PipeConstraints()
        self.economic_params = economic_params or EconomicParameters()

        # Initialize optimizer
        self.optimizer = NPVPipeOptimizer(pipe_catalog_path, self.constraints, self.economic_params)

        # Results storage
        self.optimization_results: Dict[str, Any] = {}
        self.optimized_segments: List[OptimizedPipeSegment] = []

    def extract_pipe_catalog_from_excel(self, excel_file_path: str, output_csv_path: str) -> None:
        """
        Extract pipe catalog from Excel file and save to CSV.

        Args:
            excel_file_path: Path to Technikkatalog Excel file
            output_csv_path: Path for output CSV file
        """
        logger.info(f"Extracting pipe catalog from: {excel_file_path}")

        extractor = PipeCatalogExtractor(excel_file_path)
        pipe_data = extractor.extract_pipe_catalog()
        extractor.save_to_csv(output_csv_path)

        logger.info(f"Pipe catalog extracted and saved to: {output_csv_path}")
        logger.info(f"Available diameters: {extractor.get_available_diameters()}")

    def create_pipe_segments_from_buildings(
        self,
        buildings_gdf: gpd.GeoDataFrame,
        street_network_gdf: gpd.GeoDataFrame,
        supply_temp_c: float = 80.0,
        return_temp_c: float = 50.0,
    ) -> List[PipeSegment]:
        """
        Create pipe segments from building data and street network.

        Args:
            buildings_gdf: GeoDataFrame with building data
            street_network_gdf: GeoDataFrame with street network
            supply_temp_c: Supply temperature in °C
            return_temp_c: Return temperature in °C

        Returns:
            List of pipe segments
        """
        logger.info("Creating pipe segments from building data")

        segments = []

        # Calculate total heat demand
        total_heat_demand_kw = buildings_gdf["heating_load_kw"].sum()

        # Calculate total street length
        total_street_length_m = street_network_gdf["length"].sum()

        # Create segments based on street network
        for idx, street in street_network_gdf.iterrows():
            # Calculate heat demand for this street segment
            # This is a simplified approach - in practice, you'd map buildings to streets
            street_length_m = street["length"]
            heat_demand_ratio = street_length_m / total_street_length_m
            heat_demand_kw = total_heat_demand_kw * heat_demand_ratio

            # Calculate flow rate based on heat demand
            # Q = P / (c_p * ρ * ΔT)
            # where: Q = flow rate (m³/h), P = power (kW), c_p = specific heat (kJ/kgK),
            # ρ = density (kg/m³), ΔT = temperature difference (K)
            c_p = 4.2  # kJ/kgK for water
            rho = 971.8  # kg/m³ for water at 80°C
            delta_t_k = supply_temp_c - return_temp_c

            flow_rate_m3_h = (heat_demand_kw * 3600) / (c_p * rho * delta_t_k)

            # Create pipe segment
            segment = PipeSegment(
                length_m=street_length_m,
                heat_demand_kw=heat_demand_kw,
                supply_temperature_c=supply_temp_c,
                return_temperature_c=return_temp_c,
                flow_rate_m3_h=flow_rate_m3_h,
                diameter_mm=50.0,  # Will be optimized
                cost_per_meter_eur=100.0,  # Will be updated from catalog
            )

            segments.append(segment)

        logger.info(f"Created {len(segments)} pipe segments")
        return segments

    def optimize_pipe_diameters(self, segments: List[PipeSegment]) -> Dict[str, Any]:
        """
        Optimize pipe diameters for all segments.

        Args:
            segments: List of pipe segments to optimize

        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Optimizing pipe diameters for {len(segments)} segments")

        # Run optimization
        results = self.optimizer.optimize_network(segments)

        # Store results
        self.optimization_results = results

        # Create optimized segments
        self.optimized_segments = []
        for i, segment in enumerate(segments):
            segment_key = f"segment_{i}"
            if segment_key in results and "error" not in results[segment_key]:
                segment_result = results[segment_key]

                optimized_segment = OptimizedPipeSegment(
                    segment_id=f"segment_{i}",
                    from_junction=i,
                    to_junction=i + 1,
                    length_m=segment.length_m,
                    heat_demand_kw=segment.heat_demand_kw,
                    flow_rate_m3_h=segment.flow_rate_m3_h,
                    optimal_diameter_mm=segment_result["diameter_mm"],
                    npv_eur=segment_result["npv_eur"],
                    initial_cost_eur=segment_result["initial_cost_eur"],
                    annual_operating_cost_eur=segment_result["annual_operating_cost_eur"],
                    pressure_drop_bar=segment_result["pressure_drop_bar"],
                    velocity_m_s=segment_result["velocity_m_s"],
                    heat_loss_kw=segment_result["heat_loss_kw"],
                    pumping_power_kw=segment_result["pumping_power_kw"],
                    constraints_satisfied=segment_result["constraints_satisfied"],
                )

                self.optimized_segments.append(optimized_segment)

        logger.info(
            f"Optimization complete. Network NPV: {results['network_summary']['network_npv_eur']:.2f} EUR"
        )
        return results

    def create_optimized_pandapipes_network(self, supply_temp_c: float = 80.0):
        """
        Create pandapipes network with optimized diameters.

        Args:
            supply_temp_c: Supply temperature in °C

        Returns:
            pandapipes network object
        """
        if not self.optimized_segments:
            raise ValueError(
                "No optimized segments available. Run optimize_pipe_diameters() first."
            )

        logger.info("Creating optimized pandapipes network")

        # Create pandapipes network
        net = pp.create_empty_network("optimized_dh_network")

        # Add fluid (water)
        pp.create_fluid_from_lib(net, "water")

        # Add junctions
        num_junctions = len(self.optimized_segments) + 1
        for i in range(num_junctions):
            pp.create_junction(
                net, pn_bar=1.0, tfluid_k=273.15 + supply_temp_c, name=f"junction_{i}"
            )

        # Add external grid (source) at first junction
        pp.create_ext_grid(
            net, junction=0, p_bar=1.0, t_k=273.15 + supply_temp_c, name="heat_source"
        )

        # Add pipes with optimized diameters
        for segment in self.optimized_segments:
            diameter_m = segment.optimal_diameter_mm / 1000.0

            pp.create_pipe_from_parameters(
                net,
                from_junction=segment.from_junction,
                to_junction=segment.to_junction,
                length_km=segment.length_m / 1000.0,
                diameter_m=diameter_m,
                k_mm=0.1,  # Roughness
                loss_coefficient=0.0,
                sections=1,
                alpha_w_per_m2k=0.0,  # No heat transfer for now
                name=segment.segment_id,
            )

        logger.info(f"Created pandapipes network with {len(net.pipe)} pipes")
        return net

    def run_hydraulic_simulation(self, net) -> Dict[str, Any]:
        """
        Run hydraulic simulation on the optimized network.

        Args:
            net: pandapipes network object

        Returns:
            Dictionary with simulation results
        """
        logger.info("Running hydraulic simulation")

        try:
            # Run simulation
            pp.pipeflow(net)

            # Extract results
            simulation_results = {
                "converged": net.res_pipe is not None,
                "pipe_results": {},
                "junction_results": {},
            }

            if net.res_pipe is not None:
                for pipe_idx in net.res_pipe.index:
                    pipe_name = net.pipe.at[pipe_idx, "name"]
                    simulation_results["pipe_results"][pipe_name] = {
                        "v_mean_m_per_s": net.res_pipe.at[pipe_idx, "v_mean_m_per_s"],
                        "p_from_bar": net.res_pipe.at[pipe_idx, "p_from_bar"],
                        "p_to_bar": net.res_pipe.at[pipe_idx, "p_to_bar"],
                        "mdot_from_kg_per_s": net.res_pipe.at[pipe_idx, "mdot_from_kg_per_s"],
                        "mdot_to_kg_per_s": net.res_pipe.at[pipe_idx, "mdot_to_kg_per_s"],
                    }

            if net.res_junction is not None:
                for junction_idx in net.res_junction.index:
                    junction_name = net.junction.at[junction_idx, "name"]
                    simulation_results["junction_results"][junction_name] = {
                        "p_bar": net.res_junction.at[junction_idx, "p_bar"],
                        "t_k": net.res_junction.at[junction_idx, "t_k"],
                    }

            logger.info("Hydraulic simulation completed successfully")
            return simulation_results

        except Exception as e:
            logger.error(f"Error in hydraulic simulation: {e}")
            raise

    def generate_optimization_report(self, output_path: str) -> None:
        """
        Generate comprehensive optimization report.

        Args:
            output_path: Path for output report file
        """
        if not self.optimized_segments:
            raise ValueError("No optimization results available")

        logger.info(f"Generating optimization report: {output_path}")

        # Create report content
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("NPV-BASED DISTRICT HEATING PIPE OPTIMIZATION REPORT")
        report_lines.append("=" * 80)
        report_lines.append("")

        # Network summary
        network_summary = self.optimization_results["network_summary"]
        report_lines.append("NETWORK SUMMARY:")
        report_lines.append(f"  Total Segments: {network_summary['total_segments']}")
        report_lines.append(f"  Network NPV: {network_summary['network_npv_eur']:.2f} EUR")
        report_lines.append(
            f"  Total Initial Cost: {network_summary['total_initial_cost_eur']:.2f} EUR"
        )
        report_lines.append(
            f"  Total Annual Operating Cost: {network_summary['total_annual_operating_cost_eur']:.2f} EUR"
        )
        report_lines.append("")

        # Economic parameters
        report_lines.append("ECONOMIC PARAMETERS:")
        report_lines.append(f"  Discount Rate: {self.economic_params.discount_rate:.1%}")
        report_lines.append(f"  Lifetime: {self.economic_params.lifetime_years} years")
        report_lines.append(
            f"  Electricity Cost: {self.economic_params.electricity_cost_eur_mwh:.1f} EUR/MWh"
        )
        report_lines.append(f"  Heat Cost: {self.economic_params.heat_cost_eur_mwh:.1f} EUR/MWh")
        report_lines.append(f"  Pump Efficiency: {self.economic_params.pump_efficiency:.1%}")
        report_lines.append("")

        # Constraints
        report_lines.append("EN 13941 CONSTRAINTS:")
        report_lines.append(f"  Max Velocity: {self.constraints.max_velocity_m_s:.1f} m/s")
        report_lines.append(
            f"  Min Temperature Difference: {self.constraints.min_temperature_difference_k:.1f} K"
        )
        report_lines.append(
            f"  Max Pressure Drop: {self.constraints.max_pressure_drop_bar_per_km:.1f} bar/km"
        )
        report_lines.append("")

        # Segment details
        report_lines.append("SEGMENT DETAILS:")
        report_lines.append("-" * 80)

        for segment in self.optimized_segments:
            report_lines.append(f"Segment: {segment.segment_id}")
            report_lines.append(f"  Length: {segment.length_m:.1f} m")
            report_lines.append(f"  Heat Demand: {segment.heat_demand_kw:.1f} kW")
            report_lines.append(f"  Flow Rate: {segment.flow_rate_m3_h:.2f} m³/h")
            report_lines.append(f"  Optimal Diameter: {segment.optimal_diameter_mm:.0f} mm")
            report_lines.append(f"  NPV: {segment.npv_eur:.2f} EUR")
            report_lines.append(f"  Initial Cost: {segment.initial_cost_eur:.2f} EUR")
            report_lines.append(
                f"  Annual Operating Cost: {segment.annual_operating_cost_eur:.2f} EUR"
            )
            report_lines.append(f"  Pressure Drop: {segment.pressure_drop_bar:.3f} bar")
            report_lines.append(f"  Velocity: {segment.velocity_m_s:.2f} m/s")
            report_lines.append(f"  Heat Loss: {segment.heat_loss_kw:.2f} kW")
            report_lines.append(f"  Pumping Power: {segment.pumping_power_kw:.2f} kW")
            report_lines.append(f"  Constraints Satisfied: {segment.constraints_satisfied}")
            report_lines.append("")

        # Write report
        with open(output_path, "w") as f:
            f.write("\n".join(report_lines))

        logger.info(f"Optimization report saved to: {output_path}")

    def save_optimization_results_csv(self, output_path: str) -> None:
        """
        Save optimization results to CSV file.

        Args:
            output_path: Path for output CSV file
        """
        if not self.optimized_segments:
            raise ValueError("No optimization results available")

        logger.info(f"Saving optimization results to CSV: {output_path}")

        # Convert to DataFrame
        results_data = []
        for segment in self.optimized_segments:
            results_data.append(
                {
                    "segment_id": segment.segment_id,
                    "from_junction": segment.from_junction,
                    "to_junction": segment.to_junction,
                    "length_m": segment.length_m,
                    "heat_demand_kw": segment.heat_demand_kw,
                    "flow_rate_m3_h": segment.flow_rate_m3_h,
                    "optimal_diameter_mm": segment.optimal_diameter_mm,
                    "npv_eur": segment.npv_eur,
                    "initial_cost_eur": segment.initial_cost_eur,
                    "annual_operating_cost_eur": segment.annual_operating_cost_eur,
                    "pressure_drop_bar": segment.pressure_drop_bar,
                    "velocity_m_s": segment.velocity_m_s,
                    "heat_loss_kw": segment.heat_loss_kw,
                    "pumping_power_kw": segment.pumping_power_kw,
                    "constraints_satisfied": segment.constraints_satisfied,
                }
            )

        df = pd.DataFrame(results_data)
        df.to_csv(output_path, index=False)

        logger.info(f"Optimization results saved to: {output_path}")


def main():
    """Main function to demonstrate NPV DH integration."""
    try:
        # Initialize integration
        pipe_catalog_path = "data/csv/pipe_catalog.csv"
        integration = NPVDHIntegration(pipe_catalog_path)

        # Extract pipe catalog from Excel if needed
        excel_file = "Technikkatalog_Wärmeplanung_Version_1.1_August24_CC-BY.xlsx"
        if Path(excel_file).exists() and not Path(pipe_catalog_path).exists():
            integration.extract_pipe_catalog_from_excel(excel_file, pipe_catalog_path)

        # Create sample segments
        segments = [
            PipeSegment(
                length_m=100.0,
                heat_demand_kw=50.0,
                supply_temperature_c=80.0,
                return_temperature_c=50.0,
                flow_rate_m3_h=2.5,
                diameter_mm=50.0,
                cost_per_meter_eur=100.0,
            ),
            PipeSegment(
                length_m=150.0,
                heat_demand_kw=75.0,
                supply_temperature_c=80.0,
                return_temperature_c=50.0,
                flow_rate_m3_h=3.8,
                diameter_mm=65.0,
                cost_per_meter_eur=120.0,
            ),
        ]

        # Optimize pipe diameters
        results = integration.optimize_pipe_diameters(segments)

        # Create optimized pandapipes network
        net = integration.create_optimized_pandapipes_network()

        # Run hydraulic simulation
        simulation_results = integration.run_hydraulic_simulation(net)

        # --- CHA: hourly time-series with LFA ----
        from cha_timeseries import run_timeseries
        from building_mapping import create_simple_mapping_for_test

        # 1) Create building_id -> junction index mapping
        # For now, use simple test mapping. In production, use real building data
        building_ids = ["B12"]  # Add actual building IDs from your LFA data
        num_junctions = len(net.junction)
        building_to_junction = create_simple_mapping_for_test(building_ids, num_junctions)
        
        if not building_to_junction:
            raise RuntimeError("CHA: building_to_junction map is empty. Provide a real mapping!")

        # 2) Run CHA simulations from LFA
        cha_res = run_timeseries(
            net,
            building_to_junction,
            lfa_glob="processed/lfa/*.json",
            t_supply_c=80, t_return_c=50,
            top_n=10,                 # configurable (design + top-N peak hours)
            out_dir="processed/cha",
            v_max_ms=1.5,
            save_hourly=True,
        )
        print("CHA:", cha_res)
        # -----------------------------------------

        # Generate reports
        integration.generate_optimization_report("results_test/npv_optimization_report.txt")
        integration.save_optimization_results_csv("results_test/npv_optimization_results.csv")

        print("NPV DH integration completed successfully!")
        print(f"Network NPV: {results['network_summary']['network_npv_eur']:.2f} EUR")
        print(f"Simulation converged: {simulation_results['converged']}")
        print(f"CHA time-series: {cha_res['status']}")

    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
