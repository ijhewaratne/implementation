"""
CHA Enhanced Pandapipes Simulator - Intelligent Pipe Sizing Integration

This module provides an enhanced pandapipes simulator that integrates with the
intelligent pipe sizing system to create properly sized district heating networks.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import warnings

# Import our enhanced components
from cha_pipe_sizing import CHAPipeSizingEngine
from cha_enhanced_config_loader import CHAEnhancedConfigLoader
from cha_standards import CHAStandardsValidator

warnings.filterwarnings("ignore")

try:
    import pandapipes as pp
    PANDAPIPES_AVAILABLE = True
except ImportError:
    PANDAPIPES_AVAILABLE = False
    print("⚠️ Pandapipes not available - hydraulic simulation disabled")


@dataclass
class HydraulicResult:
    """Hydraulic simulation result."""
    pipe_id: str
    flow_rate_kg_s: float
    velocity_ms: float
    pressure_drop_bar: float
    pressure_start_bar: float
    pressure_end_bar: float
    temperature_start_c: float
    temperature_end_c: float
    head_loss_m: float
    reynolds_number: float
    friction_factor: float


@dataclass
class SimulationValidationResult:
    """Simulation validation result."""
    is_valid: bool
    convergence_achieved: bool
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    recommendations: List[str]
    summary: Dict[str, Any]


@dataclass
class HydraulicReport:
    """Hydraulic analysis report."""
    network_summary: Dict[str, Any]
    pipe_results: List[HydraulicResult]
    validation_result: SimulationValidationResult
    standards_compliance: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]


class CHAEnhancedPandapipesSimulator:
    """
    Enhanced pandapipes simulator with intelligent pipe sizing integration.
    
    Creates properly sized district heating networks using calculated diameters
    from the intelligent pipe sizing system and validates results against
    engineering standards.
    """
    
    def __init__(self, sizing_engine: CHAPipeSizingEngine, 
                 config_loader: Optional[CHAEnhancedConfigLoader] = None):
        """
        Initialize the enhanced pandapipes simulator.
        
        Args:
            sizing_engine: CHA pipe sizing engine instance
            config_loader: Enhanced configuration loader instance
        """
        self.sizing_engine = sizing_engine
        self.config_loader = config_loader
        self.standards_validator: Optional[CHAStandardsValidator] = None
        
        # Initialize standards validator if config loader is available
        if self.config_loader:
            self.standards_validator = CHAStandardsValidator(self.config_loader)
        
        # Pandapipes network
        self.net = None
        self.simulation_results = None
        self.hydraulic_results: List[HydraulicResult] = []
        
        print(f"✅ CHA Enhanced Pandapipes Simulator initialized")
        print(f"   Pandapipes available: {PANDAPIPES_AVAILABLE}")
        print(f"   Standards validator: {'Available' if self.standards_validator else 'Not available'}")
    
    def create_sized_pandapipes_network(self, network_data: dict) -> bool:
        """
        Create pandapipes network with calculated diameters.
        
        Args:
            network_data: Network data with intelligent sizing information
        
        Returns:
            success: True if network creation successful
        """
        if not PANDAPIPES_AVAILABLE:
            print("❌ Pandapipes not available")
            return False
        
        print(f"🏗️ Creating sized pandapipes network...")
        
        try:
            # Create new pandapipes network
            self.net = pp.create_empty_network("CHA_Enhanced_Network")
            
            # Define fluid properties (water)
            pp.create_fluid_from_lib(self.net, "water", overwrite=True)
            
            # Add junctions for supply and return networks
            self._create_network_junctions(network_data)
            
            # Add supply pipes with calculated diameters
            self._add_supply_pipes(network_data)
            
            # Add return pipes with calculated diameters
            self._add_return_pipes(network_data)
            
            # Add service connections
            self._add_service_connections(network_data)
            
            # Add external grid (heat source)
            self._add_external_grid(network_data)
            
            # Add sinks (heat consumers)
            self._add_heat_sinks(network_data)
            
            print(f"✅ Sized pandapipes network created successfully")
            print(f"   Junctions: {len(self.net.junction)}")
            print(f"   Pipes: {len(self.net.pipe)}")
            print(f"   External grids: {len(self.net.ext_grid)}")
            print(f"   Sinks: {len(self.net.sink)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create sized pandapipes network: {e}")
            return False
    
    def run_hydraulic_simulation(self) -> bool:
        """
        Run hydraulic simulation on the created network.
        
        Returns:
            success: True if simulation successful
        """
        if not PANDAPIPES_AVAILABLE or self.net is None:
            print("❌ Pandapipes not available or network not created")
            return False
        
        print(f"🔄 Running hydraulic simulation...")
        
        try:
            # Run pipeflow simulation
            pp.pipeflow(self.net, mode="all", max_iter=100, tol_p=1e-5, tol_v=1e-5)
            
            # Check convergence
            if self.net.res_pipe is not None and not self.net.res_pipe.empty:
                print(f"✅ Hydraulic simulation completed successfully")
                
                # Extract simulation results
                self._extract_simulation_results()
                
                return True
            else:
                print(f"❌ Simulation failed to converge")
                return False
                
        except Exception as e:
            print(f"❌ Hydraulic simulation failed: {e}")
            return False
    
    def validate_simulation_results(self, results: dict) -> dict:
        """
        Validate simulation results against sizing constraints.
        
        Args:
            results: Simulation results to validate
        
        Returns:
            validation_result: Validation result with violations and recommendations
        """
        print(f"✅ Validating simulation results...")
        
        violations = []
        warnings = []
        recommendations = []
        
        # Validate against pipe sizing constraints
        self._validate_pipe_sizing_constraints(results, violations, warnings, recommendations)
        
        # Validate against engineering standards if available
        if self.standards_validator:
            standards_results = self.standards_validator.validate_en13941_compliance(results)
            standards_results_din = self.standards_validator.validate_din1988_compliance(results)
            
            # Add standards violations
            violations.extend(standards_results.get('violations', []))
            violations.extend(standards_results_din.get('violations', []))
            
            # Add standards recommendations
            recommendations.extend(standards_results.get('recommendations', []))
            recommendations.extend(standards_results_din.get('recommendations', []))
        
        # Validate convergence
        convergence_achieved = self._validate_convergence(results)
        
        # Calculate validation summary
        total_pipes = len(results.get('supply_pipes', [])) + len(results.get('return_pipes', []))
        compliant_pipes = total_pipes - len(violations)
        compliance_rate = compliant_pipes / total_pipes if total_pipes > 0 else 1.0
        
        is_valid = len(violations) == 0 and convergence_achieved and compliance_rate >= 0.95
        
        validation_result = SimulationValidationResult(
            is_valid=is_valid,
            convergence_achieved=convergence_achieved,
            violations=violations,
            warnings=warnings,
            recommendations=list(set(recommendations)),
            summary={
                'total_pipes': total_pipes,
                'compliant_pipes': compliant_pipes,
                'compliance_rate': compliance_rate,
                'violation_count': len(violations),
                'warning_count': len(warnings)
            }
        )
        
        print(f"✅ Simulation validation completed")
        print(f"   Valid: {is_valid}")
        print(f"   Convergence: {convergence_achieved}")
        print(f"   Compliance rate: {compliance_rate:.1%}")
        print(f"   Violations: {len(violations)}")
        
        return validation_result.__dict__
    
    def validate_pandapipes_sizing(self, simulation_results: dict) -> dict:
        """
        Validate that pandapipes results match sizing expectations.
        
        Args:
            simulation_results: Pandapipes simulation results
        
        Returns:
            validation_results: Comprehensive validation results
        """
        print(f"🔍 Validating pandapipes sizing against expectations...")
        
        validation_results = {
            'velocity_compliance': {},
            'pressure_compliance': {},
            'flow_distribution': {},
            'sizing_accuracy': {},
            'overall_compliance': True,
            'compliance_rate': 0.0,
            'violations': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Get sizing constraints from configuration
        max_velocity = self._get_max_velocity()
        min_velocity = self._get_min_velocity()
        max_pressure_drop = self._get_max_pressure_drop()
        
        # Validate velocity constraints
        self._validate_velocity_compliance(simulation_results, validation_results, max_velocity, min_velocity)
        
        # Validate pressure constraints
        self._validate_pressure_compliance(simulation_results, validation_results, max_pressure_drop)
        
        # Validate flow distribution
        self._validate_flow_distribution(simulation_results, validation_results)
        
        # Validate sizing accuracy
        self._validate_sizing_accuracy(simulation_results, validation_results)
        
        # Calculate overall compliance
        self._calculate_overall_compliance(validation_results)
        
        print(f"✅ Pandapipes sizing validation completed")
        print(f"   Overall compliance: {validation_results['overall_compliance']}")
        print(f"   Compliance rate: {validation_results['compliance_rate']:.1%}")
        print(f"   Violations: {len(validation_results['violations'])}")
        print(f"   Warnings: {len(validation_results['warnings'])}")
        
        return validation_results
    
    def generate_hydraulic_report(self, results: dict) -> dict:
        """
        Generate detailed hydraulic analysis report.
        
        Args:
            results: Simulation results
        
        Returns:
            hydraulic_report: Detailed hydraulic analysis report
        """
        print(f"📊 Generating hydraulic analysis report...")
        
        # Calculate network summary
        network_summary = self._calculate_network_summary(results)
        
        # Extract pipe results
        pipe_results = self._extract_pipe_results(results)
        
        # Validate simulation results
        validation_result = self.validate_simulation_results(results)
        
        # Get standards compliance if available
        standards_compliance = {}
        if self.standards_validator:
            standards_compliance = {
                'EN_13941': self.standards_validator.validate_en13941_compliance(results),
                'DIN_1988': self.standards_validator.validate_din1988_compliance(results)
            }
        
        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(validation_result, standards_compliance)
        
        hydraulic_report = HydraulicReport(
            network_summary=network_summary,
            pipe_results=pipe_results,
            validation_result=SimulationValidationResult(**validation_result),
            standards_compliance=standards_compliance,
            performance_metrics=performance_metrics,
            recommendations=recommendations
        )
        
        print(f"✅ Hydraulic analysis report generated")
        print(f"   Network summary: {len(network_summary)} metrics")
        print(f"   Pipe results: {len(pipe_results)} pipes")
        print(f"   Performance metrics: {len(performance_metrics)} metrics")
        print(f"   Recommendations: {len(recommendations)} recommendations")
        
        return hydraulic_report.__dict__
    
    def _create_network_junctions(self, network_data: dict) -> None:
        """Create network junctions."""
        # Create plant junction
        pp.create_junction(self.net, pn_bar=6.0, tfluid_k=343.15, name="plant_junction")
        
        # Create building junctions
        for i, service in enumerate(network_data.get('service_connections', [])):
            pp.create_junction(self.net, pn_bar=2.0, tfluid_k=313.15, 
                             name=f"building_junction_{i}")
    
    def _add_supply_pipes(self, network_data: dict) -> None:
        """Add supply pipes with calculated diameters."""
        for i, pipe in enumerate(network_data.get('supply_pipes', [])):
            # Get calculated diameter
            diameter_m = pipe.get('diameter_m', 0.1)  # Use calculated diameter
            
            # Create pipe
            pp.create_pipe_from_parameters(
                self.net,
                from_junction=0,  # Plant junction
                to_junction=i + 1,  # Building junction
                length_km=pipe.get('length_m', 100) / 1000.0,
                diameter_m=diameter_m,
                k_mm=0.1,  # Roughness
                name=f"supply_{pipe.get('pipe_id', i)}",
                sections=1,
                alpha_w_per_m2k=0.0,
                text_k=313.15
            )
    
    def _add_return_pipes(self, network_data: dict) -> None:
        """Add return pipes with calculated diameters."""
        for i, pipe in enumerate(network_data.get('return_pipes', [])):
            # Get calculated diameter
            diameter_m = pipe.get('diameter_m', 0.1)  # Use calculated diameter
            
            # Create pipe
            pp.create_pipe_from_parameters(
                self.net,
                from_junction=i + 1,  # Building junction
                to_junction=0,  # Plant junction
                length_km=pipe.get('length_m', 100) / 1000.0,
                diameter_m=diameter_m,
                k_mm=0.1,  # Roughness
                name=f"return_{pipe.get('pipe_id', i)}",
                sections=1,
                alpha_w_per_m2k=0.0,
                text_k=313.15
            )
    
    def _add_service_connections(self, network_data: dict) -> None:
        """Add service connections."""
        # Service connections are handled as part of supply/return pipes
        pass
    
    def _add_external_grid(self, network_data: dict) -> None:
        """Add external grid (heat source)."""
        pp.create_ext_grid(self.net, junction=0, p_bar=6.0, t_k=343.15, 
                          name="CHP_Plant", type="pt")
    
    def _add_heat_sinks(self, network_data: dict) -> None:
        """Add heat sinks (heat consumers)."""
        for i, service in enumerate(network_data.get('service_connections', [])):
            # Calculate mass flow rate from heat demand
            heat_demand_kw = service.get('heating_load_kw', 10.0)
            delta_t_k = 30.0  # 70°C - 40°C
            cp_water = 4180  # J/kg·K
            
            mass_flow_kg_s = (heat_demand_kw * 1000) / (cp_water * delta_t_k)
            
            pp.create_sink(self.net, junction=i + 1, mdot_kg_per_s=mass_flow_kg_s,
                          name=f"heat_sink_{i}")
    
    def _extract_simulation_results(self) -> None:
        """Extract simulation results from pandapipes network."""
        if self.net.res_pipe is None or self.net.res_pipe.empty:
            return
        
        self.hydraulic_results = []
        
        for idx, row in self.net.res_pipe.iterrows():
            pipe_name = self.net.pipe.loc[idx, 'name']
            
            result = HydraulicResult(
                pipe_id=pipe_name,
                flow_rate_kg_s=row.get('mdot_kg_per_s', 0.0),
                velocity_ms=row.get('v_mean_m_per_s', 0.0),
                pressure_drop_bar=row.get('p_from_bar', 0.0) - row.get('p_to_bar', 0.0),
                pressure_start_bar=row.get('p_from_bar', 0.0),
                pressure_end_bar=row.get('p_to_bar', 0.0),
                temperature_start_c=row.get('t_from_k', 313.15) - 273.15,
                temperature_end_c=row.get('t_to_k', 313.15) - 273.15,
                head_loss_m=row.get('head_loss_m', 0.0),
                reynolds_number=row.get('reynolds', 0.0),
                friction_factor=row.get('lambda', 0.0)
            )
            
            self.hydraulic_results.append(result)
    
    def _validate_pipe_sizing_constraints(self, results: dict, violations: List, 
                                        warnings: List, recommendations: List) -> None:
        """Validate pipe sizing constraints."""
        # Get hydraulic constraints from configuration
        if self.config_loader and self.config_loader.enhanced_config:
            max_velocity = self.config_loader.enhanced_config.pipe_sizing.max_velocity_ms
            min_velocity = self.config_loader.enhanced_config.pipe_sizing.min_velocity_ms
            max_pressure_drop = self.config_loader.enhanced_config.pipe_sizing.max_pressure_drop_pa_per_m
        else:
            max_velocity = 3.0
            min_velocity = 0.5
            max_pressure_drop = 5000
        
        # Validate each pipe
        for result in self.hydraulic_results:
            # Validate velocity
            if result.velocity_ms > max_velocity:
                violations.append({
                    'type': 'velocity_exceeded',
                    'severity': 'high',
                    'description': f"Velocity {result.velocity_ms:.2f} m/s exceeds limit {max_velocity} m/s",
                    'pipe_id': result.pipe_id,
                    'value': result.velocity_ms,
                    'limit': max_velocity
                })
                recommendations.append("Consider increasing pipe diameter to reduce velocity")
            
            if result.velocity_ms < min_velocity:
                warnings.append({
                    'type': 'velocity_below_minimum',
                    'severity': 'medium',
                    'description': f"Velocity {result.velocity_ms:.2f} m/s below minimum {min_velocity} m/s",
                    'pipe_id': result.pipe_id,
                    'value': result.velocity_ms,
                    'limit': min_velocity
                })
            
            # Validate pressure drop
            pressure_drop_pa_per_m = (result.pressure_drop_bar * 100000) / 100  # Convert to Pa/m
            if pressure_drop_pa_per_m > max_pressure_drop:
                violations.append({
                    'type': 'pressure_drop_exceeded',
                    'severity': 'high',
                    'description': f"Pressure drop {pressure_drop_pa_per_m:.0f} Pa/m exceeds limit {max_pressure_drop} Pa/m",
                    'pipe_id': result.pipe_id,
                    'value': pressure_drop_pa_per_m,
                    'limit': max_pressure_drop
                })
                recommendations.append("Consider increasing pipe diameter to reduce pressure drop")
    
    def _validate_convergence(self, results: dict) -> bool:
        """Validate simulation convergence."""
        if self.net is None:
            return False
        
        # Check if simulation converged
        return hasattr(self.net, 'res_pipe') and self.net.res_pipe is not None and not self.net.res_pipe.empty
    
    def _calculate_network_summary(self, results: dict) -> Dict[str, Any]:
        """Calculate network summary statistics."""
        if not self.hydraulic_results:
            return {}
        
        total_flow = sum(result.flow_rate_kg_s for result in self.hydraulic_results)
        total_pressure_drop = sum(result.pressure_drop_bar for result in self.hydraulic_results)
        average_velocity = np.mean([result.velocity_ms for result in self.hydraulic_results])
        max_velocity = max(result.velocity_ms for result in self.hydraulic_results)
        min_velocity = min(result.velocity_ms for result in self.hydraulic_results)
        
        return {
            'total_pipes': len(self.hydraulic_results),
            'total_flow_kg_s': total_flow,
            'total_pressure_drop_bar': total_pressure_drop,
            'average_velocity_ms': average_velocity,
            'max_velocity_ms': max_velocity,
            'min_velocity_ms': min_velocity,
            'average_pressure_drop_bar': total_pressure_drop / len(self.hydraulic_results) if self.hydraulic_results else 0
        }
    
    def _extract_pipe_results(self, results: dict) -> List[HydraulicResult]:
        """Extract pipe results."""
        return self.hydraulic_results
    
    def _calculate_performance_metrics(self, results: dict) -> Dict[str, Any]:
        """Calculate performance metrics."""
        if not self.hydraulic_results:
            return {}
        
        # Calculate efficiency metrics
        total_flow = sum(result.flow_rate_kg_s for result in self.hydraulic_results)
        total_pressure_drop = sum(result.pressure_drop_bar for result in self.hydraulic_results)
        
        # Calculate pump power (simplified)
        pump_power_kw = (total_flow * total_pressure_drop * 100000) / (1000 * 0.75)  # Assuming 75% efficiency
        
        return {
            'total_flow_kg_s': total_flow,
            'total_pressure_drop_bar': total_pressure_drop,
            'pump_power_kw': pump_power_kw,
            'average_velocity_ms': np.mean([result.velocity_ms for result in self.hydraulic_results]),
            'max_velocity_ms': max(result.velocity_ms for result in self.hydraulic_results),
            'min_velocity_ms': min(result.velocity_ms for result in self.hydraulic_results),
            'average_reynolds_number': np.mean([result.reynolds_number for result in self.hydraulic_results]),
            'average_friction_factor': np.mean([result.friction_factor for result in self.hydraulic_results])
        }
    
    def _generate_recommendations(self, validation_result: dict, standards_compliance: dict) -> List[str]:
        """Generate recommendations based on validation and standards compliance."""
        recommendations = []
        
        # Add validation recommendations
        recommendations.extend(validation_result.get('recommendations', []))
        
        # Add standards compliance recommendations
        for standard, compliance in standards_compliance.items():
            recommendations.extend(compliance.get('recommendations', []))
        
        # Remove duplicates
        return list(set(recommendations))
    
    def _get_max_velocity(self) -> float:
        """Get maximum velocity constraint."""
        if self.config_loader and self.config_loader.enhanced_config:
            return self.config_loader.enhanced_config.pipe_sizing.max_velocity_ms
        return 3.0
    
    def _get_min_velocity(self) -> float:
        """Get minimum velocity constraint."""
        if self.config_loader and self.config_loader.enhanced_config:
            return self.config_loader.enhanced_config.pipe_sizing.min_velocity_ms
        return 0.5
    
    def _get_max_pressure_drop(self) -> float:
        """Get maximum pressure drop constraint."""
        if self.config_loader and self.config_loader.enhanced_config:
            return self.config_loader.enhanced_config.pipe_sizing.max_pressure_drop_pa_per_m
        return 5000
    
    def _validate_velocity_compliance(self, simulation_results: dict, validation_results: dict, 
                                    max_velocity: float, min_velocity: float) -> None:
        """Validate velocity compliance against sizing expectations."""
        for result in self.hydraulic_results:
            pipe_id = result.pipe_id
            velocity = result.velocity_ms
            
            compliance = {
                'compliant': True,
                'velocity': velocity,
                'constraint_violation': None,
                'expected_range': f"{min_velocity}-{max_velocity} m/s"
            }
            
            if velocity > max_velocity:
                compliance['compliant'] = False
                compliance['constraint_violation'] = 'high'
                validation_results['violations'].append({
                    'type': 'velocity_exceeded',
                    'severity': 'high',
                    'description': f"Velocity {velocity:.2f} m/s exceeds maximum {max_velocity} m/s",
                    'pipe_id': pipe_id,
                    'value': velocity,
                    'limit': max_velocity
                })
                validation_results['recommendations'].append(f"Consider increasing diameter for pipe {pipe_id} to reduce velocity")
                validation_results['overall_compliance'] = False
            elif velocity < min_velocity:
                compliance['compliant'] = False
                compliance['constraint_violation'] = 'low'
                validation_results['warnings'].append({
                    'type': 'velocity_below_minimum',
                    'severity': 'medium',
                    'description': f"Velocity {velocity:.2f} m/s below minimum {min_velocity} m/s",
                    'pipe_id': pipe_id,
                    'value': velocity,
                    'limit': min_velocity
                })
                validation_results['recommendations'].append(f"Consider decreasing diameter for pipe {pipe_id} to increase velocity")
            
            validation_results['velocity_compliance'][pipe_id] = compliance
    
    def _validate_pressure_compliance(self, simulation_results: dict, validation_results: dict, 
                                    max_pressure_drop: float) -> None:
        """Validate pressure compliance against sizing expectations."""
        for result in self.hydraulic_results:
            pipe_id = result.pipe_id
            pressure_drop_bar = result.pressure_drop_bar
            pressure_drop_pa_per_m = (pressure_drop_bar * 100000) / 100  # Convert to Pa/m
            
            compliance = {
                'compliant': True,
                'pressure_drop_bar': pressure_drop_bar,
                'pressure_drop_pa_per_m': pressure_drop_pa_per_m,
                'constraint_violation': None,
                'max_allowed_pa_per_m': max_pressure_drop
            }
            
            if pressure_drop_pa_per_m > max_pressure_drop:
                compliance['compliant'] = False
                compliance['constraint_violation'] = 'exceeded'
                validation_results['violations'].append({
                    'type': 'pressure_drop_exceeded',
                    'severity': 'high',
                    'description': f"Pressure drop {pressure_drop_pa_per_m:.0f} Pa/m exceeds maximum {max_pressure_drop} Pa/m",
                    'pipe_id': pipe_id,
                    'value': pressure_drop_pa_per_m,
                    'limit': max_pressure_drop
                })
                validation_results['recommendations'].append(f"Consider increasing diameter for pipe {pipe_id} to reduce pressure drop")
                validation_results['overall_compliance'] = False
            
            validation_results['pressure_compliance'][pipe_id] = compliance
    
    def _validate_flow_distribution(self, simulation_results: dict, validation_results: dict) -> None:
        """Validate flow distribution against sizing expectations."""
        total_flow = sum(result.flow_rate_kg_s for result in self.hydraulic_results)
        supply_flow = sum(result.flow_rate_kg_s for result in self.hydraulic_results if 'supply' in result.pipe_id)
        return_flow = sum(result.flow_rate_kg_s for result in self.hydraulic_results if 'return' in result.pipe_id)
        
        flow_distribution = {
            'total_flow_kg_s': total_flow,
            'supply_flow_kg_s': supply_flow,
            'return_flow_kg_s': return_flow,
            'flow_balance': abs(supply_flow - return_flow),
            'flow_balance_percentage': abs(supply_flow - return_flow) / max(supply_flow, return_flow) * 100 if max(supply_flow, return_flow) > 0 else 0
        }
        
        # Check flow balance
        if flow_distribution['flow_balance_percentage'] > 5.0:  # 5% tolerance
            validation_results['warnings'].append({
                'type': 'flow_imbalance',
                'severity': 'medium',
                'description': f"Flow imbalance: {flow_distribution['flow_balance_percentage']:.1f}% difference between supply and return",
                'supply_flow': supply_flow,
                'return_flow': return_flow
            })
            validation_results['recommendations'].append("Check network topology for flow balance issues")
        
        validation_results['flow_distribution'] = flow_distribution
    
    def _validate_sizing_accuracy(self, simulation_results: dict, validation_results: dict) -> None:
        """Validate sizing accuracy against expected values."""
        sizing_accuracy = {
            'total_pipes': len(self.hydraulic_results),
            'properly_sized_pipes': 0,
            'undersized_pipes': 0,
            'oversized_pipes': 0,
            'sizing_accuracy_rate': 0.0
        }
        
        for result in self.hydraulic_results:
            pipe_id = result.pipe_id
            velocity = result.velocity_ms
            max_velocity = self._get_max_velocity()
            min_velocity = self._get_min_velocity()
            
            # Determine if pipe is properly sized
            if min_velocity <= velocity <= max_velocity:
                sizing_accuracy['properly_sized_pipes'] += 1
            elif velocity > max_velocity:
                sizing_accuracy['oversized_pipes'] += 1
            else:
                sizing_accuracy['undersized_pipes'] += 1
        
        # Calculate sizing accuracy rate
        if sizing_accuracy['total_pipes'] > 0:
            sizing_accuracy['sizing_accuracy_rate'] = sizing_accuracy['properly_sized_pipes'] / sizing_accuracy['total_pipes']
        
        validation_results['sizing_accuracy'] = sizing_accuracy
    
    def _calculate_overall_compliance(self, validation_results: dict) -> None:
        """Calculate overall compliance metrics."""
        total_checks = 0
        compliant_checks = 0
        
        # Count velocity compliance checks
        for pipe_id, compliance in validation_results['velocity_compliance'].items():
            total_checks += 1
            if compliance['compliant']:
                compliant_checks += 1
        
        # Count pressure compliance checks
        for pipe_id, compliance in validation_results['pressure_compliance'].items():
            total_checks += 1
            if compliance['compliant']:
                compliant_checks += 1
        
        # Calculate compliance rate
        if total_checks > 0:
            validation_results['compliance_rate'] = compliant_checks / total_checks
        
        # Update overall compliance
        validation_results['overall_compliance'] = (
            validation_results['compliance_rate'] >= 0.95 and 
            len(validation_results['violations']) == 0
        )
    
    def export_hydraulic_report(self, results: dict, output_path: str) -> None:
        """
        Export hydraulic report to JSON file.
        
        Args:
            results: Simulation results
            output_path: Output file path
        """
        hydraulic_report = self.generate_hydraulic_report(results)
        
        with open(output_path, 'w') as f:
            json.dump(hydraulic_report, f, indent=2, default=str)
        
        print(f"✅ Hydraulic report exported to {output_path}")
    
    def print_hydraulic_summary(self, results: dict) -> None:
        """Print hydraulic analysis summary."""
        hydraulic_report = self.generate_hydraulic_report(results)
        
        print(f"\n📊 HYDRAULIC ANALYSIS SUMMARY")
        print(f"=" * 50)
        
        network_summary = hydraulic_report.get('network_summary', {})
        print(f"🏗️ NETWORK OVERVIEW:")
        print(f"   Total Pipes: {network_summary.get('total_pipes', 0)}")
        print(f"   Total Flow: {network_summary.get('total_flow_kg_s', 0):.2f} kg/s")
        print(f"   Total Pressure Drop: {network_summary.get('total_pressure_drop_bar', 0):.3f} bar")
        print(f"   Average Velocity: {network_summary.get('average_velocity_ms', 0):.2f} m/s")
        print(f"   Max Velocity: {network_summary.get('max_velocity_ms', 0):.2f} m/s")
        print(f"   Min Velocity: {network_summary.get('min_velocity_ms', 0):.2f} m/s")
        
        validation_result = hydraulic_report.get('validation_result', {})
        print(f"")
        print(f"✅ VALIDATION:")
        if isinstance(validation_result, dict):
            print(f"   Valid: {validation_result.get('is_valid', False)}")
            print(f"   Convergence: {validation_result.get('convergence_achieved', False)}")
            print(f"   Compliance Rate: {validation_result.get('summary', {}).get('compliance_rate', 0):.1%}")
            print(f"   Violations: {validation_result.get('summary', {}).get('violation_count', 0)}")
        else:
            print(f"   Valid: {validation_result.is_valid}")
            print(f"   Convergence: {validation_result.convergence_achieved}")
            print(f"   Compliance Rate: {validation_result.summary.get('compliance_rate', 0):.1%}")
            print(f"   Violations: {validation_result.summary.get('violation_count', 0)}")
        
        performance_metrics = hydraulic_report.get('performance_metrics', {})
        print(f"")
        print(f"⚡ PERFORMANCE:")
        print(f"   Pump Power: {performance_metrics.get('pump_power_kw', 0):.1f} kW")
        print(f"   Average Reynolds: {performance_metrics.get('average_reynolds_number', 0):.0f}")
        print(f"   Average Friction Factor: {performance_metrics.get('average_friction_factor', 0):.4f}")
    
    def print_validation_summary(self, validation_results: dict) -> None:
        """Print comprehensive validation summary."""
        print(f"\n🔍 PANDAPIPES SIZING VALIDATION SUMMARY")
        print(f"=" * 50)
        
        print(f"✅ OVERALL COMPLIANCE:")
        print(f"   Overall Compliant: {validation_results['overall_compliance']}")
        print(f"   Compliance Rate: {validation_results['compliance_rate']:.1%}")
        print(f"   Violations: {len(validation_results['violations'])}")
        print(f"   Warnings: {len(validation_results['warnings'])}")
        
        print(f"")
        print(f"🌊 VELOCITY COMPLIANCE:")
        velocity_compliant = sum(1 for v in validation_results['velocity_compliance'].values() if v['compliant'])
        total_velocity_checks = len(validation_results['velocity_compliance'])
        print(f"   Compliant Pipes: {velocity_compliant}/{total_velocity_checks}")
        print(f"   Compliance Rate: {velocity_compliant/total_velocity_checks*100:.1f}%" if total_velocity_checks > 0 else "   Compliance Rate: N/A")
        
        print(f"")
        print(f"💧 PRESSURE COMPLIANCE:")
        pressure_compliant = sum(1 for p in validation_results['pressure_compliance'].values() if p['compliant'])
        total_pressure_checks = len(validation_results['pressure_compliance'])
        print(f"   Compliant Pipes: {pressure_compliant}/{total_pressure_checks}")
        print(f"   Compliance Rate: {pressure_compliant/total_pressure_checks*100:.1f}%" if total_pressure_checks > 0 else "   Compliance Rate: N/A")
        
        print(f"")
        print(f"📊 FLOW DISTRIBUTION:")
        flow_dist = validation_results['flow_distribution']
        print(f"   Total Flow: {flow_dist['total_flow_kg_s']:.2f} kg/s")
        print(f"   Supply Flow: {flow_dist['supply_flow_kg_s']:.2f} kg/s")
        print(f"   Return Flow: {flow_dist['return_flow_kg_s']:.2f} kg/s")
        print(f"   Flow Balance: {flow_dist['flow_balance_percentage']:.1f}%")
        
        print(f"")
        print(f"📏 SIZING ACCURACY:")
        sizing_acc = validation_results['sizing_accuracy']
        print(f"   Total Pipes: {sizing_acc['total_pipes']}")
        print(f"   Properly Sized: {sizing_acc['properly_sized_pipes']}")
        print(f"   Undersized: {sizing_acc['undersized_pipes']}")
        print(f"   Oversized: {sizing_acc['oversized_pipes']}")
        print(f"   Accuracy Rate: {sizing_acc['sizing_accuracy_rate']:.1%}")
        
        if validation_results['violations']:
            print(f"")
            print(f"❌ VIOLATIONS:")
            for i, violation in enumerate(validation_results['violations'][:5], 1):  # Show first 5
                print(f"   {i}. {violation['description']}")
            if len(validation_results['violations']) > 5:
                print(f"   ... and {len(validation_results['violations']) - 5} more violations")
        
        if validation_results['warnings']:
            print(f"")
            print(f"⚠️ WARNINGS:")
            for i, warning in enumerate(validation_results['warnings'][:3], 1):  # Show first 3
                print(f"   {i}. {warning['description']}")
            if len(validation_results['warnings']) > 3:
                print(f"   ... and {len(validation_results['warnings']) - 3} more warnings")
        
        if validation_results['recommendations']:
            print(f"")
            print(f"💡 RECOMMENDATIONS:")
            for i, recommendation in enumerate(validation_results['recommendations'][:3], 1):  # Show first 3
                print(f"   {i}. {recommendation}")
            if len(validation_results['recommendations']) > 3:
                print(f"   ... and {len(validation_results['recommendations']) - 3} more recommendations")


# Example usage and testing
if __name__ == "__main__":
    # Create pipe sizing engine
    from cha_pipe_sizing import CHAPipeSizingEngine
    
    config = {
        'max_velocity_ms': 2.0,
        'min_velocity_ms': 0.1,
        'max_pressure_drop_pa_per_m': 5000,
        'pipe_roughness_mm': 0.1
    }
    
    sizing_engine = CHAPipeSizingEngine(config)
    
    # Create configuration loader
    config_loader = CHAEnhancedConfigLoader("configs/cha.yml")
    config_loader.load_configuration()
    config_loader.validate_configuration()
    config_loader.parse_enhanced_configuration()
    
    # Create enhanced pandapipes simulator
    enhanced_simulator = CHAEnhancedPandapipesSimulator(sizing_engine, config_loader)
    
    # Example network data
    network_data = {
        'supply_pipes': [
            {
                'pipe_id': 'supply_1',
                'diameter_m': 0.1,
                'length_m': 100,
                'flow_rate_kg_s': 0.5
            }
        ],
        'return_pipes': [
            {
                'pipe_id': 'return_1',
                'diameter_m': 0.1,
                'length_m': 100,
                'flow_rate_kg_s': 0.5
            }
        ],
        'service_connections': [
            {
                'heating_load_kw': 10.0,
                'building_id': 'building_1'
            }
        ]
    }
    
    try:
        # Test enhanced pandapipes simulator
        print(f"🧪 Testing enhanced pandapipes simulator...")
        
        # Create sized network
        success = enhanced_simulator.create_sized_pandapipes_network(network_data)
        print(f"✅ Network creation: {'Success' if success else 'Failed'}")
        
        if success and PANDAPIPES_AVAILABLE:
            # Run simulation
            success = enhanced_simulator.run_hydraulic_simulation()
            print(f"✅ Simulation: {'Success' if success else 'Failed'}")
            
            if success:
                # Generate hydraulic report
                hydraulic_report = enhanced_simulator.generate_hydraulic_report(network_data)
                print(f"✅ Hydraulic report: Generated")
                
                # Print summary
                enhanced_simulator.print_hydraulic_summary(network_data)
        
        print(f"\n🎉 Enhanced pandapipes simulator testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in enhanced pandapipes simulator: {e}")
        import traceback
        traceback.print_exc()