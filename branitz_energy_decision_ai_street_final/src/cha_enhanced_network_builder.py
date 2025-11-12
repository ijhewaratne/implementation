"""
CHA Enhanced Network Builder - Intelligent Network Construction with Pipe Sizing

This module implements enhanced network construction with intelligent pipe sizing,
graduated sizing hierarchy, and comprehensive network validation.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import math
import pandas as pd
import numpy as np
import networkx as nx
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import warnings

# Import our pipe sizing engine
from cha_pipe_sizing import CHAPipeSizingEngine, PipeSizingResult

warnings.filterwarnings("ignore")


@dataclass
class NetworkPipe:
    """Enhanced network pipe with sizing information."""
    pipe_id: str
    start_node: str
    end_node: str
    length_m: float
    diameter_m: float
    diameter_nominal: str
    pipe_category: str
    pipe_type: str  # 'supply', 'return', 'service'
    flow_rate_kg_s: float
    velocity_ms: float
    pressure_drop_bar: float
    cost_eur: float
    material: str
    insulation: str
    building_served: Optional[str]
    street_id: Optional[str]
    flow_direction: str
    standards_compliance: Dict[str, bool]
    violations: List[str]


@dataclass
class NetworkValidationResult:
    """Network validation result."""
    overall_compliant: bool
    total_pipes: int
    compliant_pipes: int
    non_compliant_pipes: int
    compliance_rate: float
    total_violations: int
    violations_by_type: Dict[str, int]
    violations_by_severity: Dict[str, int]
    critical_violations: List[str]
    recommendations: List[str]


@dataclass
class GraduatedSizingResult:
    """Graduated sizing result."""
    hierarchy_levels: Dict[int, Dict]
    pipe_categories: Dict[str, List[str]]
    sizing_summary: Dict[str, any]
    cost_breakdown: Dict[str, float]
    performance_metrics: Dict[str, float]


class CHAEnhancedNetworkBuilder:
    """
    Enhanced Network Builder for District Heating Networks.
    
    Creates intelligent dual-pipe networks with proper diameter sizing,
    graduated sizing hierarchy, and comprehensive validation.
    """
    
    def __init__(self, sizing_engine: CHAPipeSizingEngine):
        """
        Initialize the enhanced network builder.
        
        Args:
            sizing_engine: CHA pipe sizing engine instance
        """
        self.sizing_engine = sizing_engine
        
        # Network hierarchy levels
        self.hierarchy_levels = {
            1: {'name': 'Service Connections', 'min_flow_kg_s': 0, 'max_flow_kg_s': 2, 'typical_diameter_mm': [25, 32, 40]},
            2: {'name': 'Street Distribution', 'min_flow_kg_s': 2, 'max_flow_kg_s': 10, 'typical_diameter_mm': [50, 63, 80]},
            3: {'name': 'Area Distribution', 'min_flow_kg_s': 10, 'max_flow_kg_s': 30, 'typical_diameter_mm': [100, 125, 150]},
            4: {'name': 'Main Distribution', 'min_flow_kg_s': 30, 'max_flow_kg_s': 80, 'typical_diameter_mm': [200, 250, 300]},
            5: {'name': 'Primary Main', 'min_flow_kg_s': 80, 'max_flow_kg_s': 200, 'typical_diameter_mm': [300, 400, 500]}
        }
        
        # Pipe categories
        self.pipe_categories = {
            'service_connection': {
                'diameter_range_mm': (25, 50),
                'velocity_limit_ms': 1.5,
                'pressure_drop_limit_pa_per_m': 5000,
                'material': 'steel_or_plastic',
                'insulation': 'polyurethane'
            },
            'distribution_pipe': {
                'diameter_range_mm': (63, 150),
                'velocity_limit_ms': 2.0,
                'pressure_drop_limit_pa_per_m': 4000,
                'material': 'steel',
                'insulation': 'polyurethane'
            },
            'main_pipe': {
                'diameter_range_mm': (200, 400),
                'velocity_limit_ms': 2.0,
                'pressure_drop_limit_pa_per_m': 3000,
                'material': 'steel',
                'insulation': 'polyurethane'
            }
        }
        
        # Results storage
        self.network_pipes: Dict[str, NetworkPipe] = {}
        self.network_graph = nx.DiGraph()
        self.validation_result: Optional[NetworkValidationResult] = None
        self.graduated_sizing_result: Optional[GraduatedSizingResult] = None
        
        print(f"✅ CHA Enhanced Network Builder initialized")
        print(f"   Hierarchy Levels: {len(self.hierarchy_levels)}")
        print(f"   Pipe Categories: {len(self.pipe_categories)}")
    
    def create_sized_dual_pipe_network(self, flow_rates: dict) -> dict:
        """
        Create dual-pipe network with proper diameter sizing.
        
        Args:
            flow_rates: Dictionary of flow rates per pipe segment
        
        Returns:
            network_data: Complete network data with sizing information
        """
        print(f"🏗️ Creating sized dual-pipe network for {len(flow_rates)} pipe segments...")
        
        try:
            # Initialize network data
            network_data = {
                'supply_pipes': [],
                'return_pipes': [],
                'service_connections': [],
                'network_statistics': {},
                'sizing_summary': {}
            }
            
            # Process each pipe segment
            for pipe_id, flow_rate_kg_s in flow_rates.items():
                # Determine pipe category based on flow rate
                pipe_category = self._determine_pipe_category(flow_rate_kg_s)
                
                # Size the pipe
                length_m = 100.0  # Default length - in real implementation, load from network data
                sizing_result = self.sizing_engine.size_pipe(
                    flow_rate_kg_s=flow_rate_kg_s,
                    length_m=length_m,
                    pipe_category=pipe_category
                )
                
                # Create supply pipe
                supply_pipe = self._create_network_pipe(
                    pipe_id=f"supply_{pipe_id}",
                    pipe_type="supply",
                    flow_rate_kg_s=flow_rate_kg_s,
                    sizing_result=sizing_result,
                    length_m=length_m,
                    pipe_category=pipe_category
                )
                
                # Create return pipe
                return_pipe = self._create_network_pipe(
                    pipe_id=f"return_{pipe_id}",
                    pipe_type="return",
                    flow_rate_kg_s=flow_rate_kg_s,
                    sizing_result=sizing_result,
                    length_m=length_m,
                    pipe_category=pipe_category
                )
                
                # Add to network data
                network_data['supply_pipes'].append(supply_pipe)
                network_data['return_pipes'].append(return_pipe)
                
                # Store in internal data structures
                self.network_pipes[supply_pipe['pipe_id']] = self._dict_to_network_pipe(supply_pipe)
                self.network_pipes[return_pipe['pipe_id']] = self._dict_to_network_pipe(return_pipe)
            
            # Create service connections
            network_data['service_connections'] = self._create_service_connections(flow_rates)
            
            # Calculate network statistics
            network_data['network_statistics'] = self._calculate_network_statistics()
            
            # Calculate sizing summary
            network_data['sizing_summary'] = self._calculate_sizing_summary()
            
            print(f"✅ Created sized dual-pipe network")
            print(f"   Supply Pipes: {len(network_data['supply_pipes'])}")
            print(f"   Return Pipes: {len(network_data['return_pipes'])}")
            print(f"   Service Connections: {len(network_data['service_connections'])}")
            
            return network_data
            
        except Exception as e:
            print(f"❌ Failed to create sized dual-pipe network: {e}")
            raise
    
    def apply_graduated_sizing(self, network_data: dict) -> dict:
        """
        Apply graduated sizing (main → distribution → service).
        
        Args:
            network_data: Network data with initial sizing
        
        Returns:
            graduated_network_data: Network data with graduated sizing applied
        """
        print(f"📏 Applying graduated sizing to network...")
        
        try:
            # Analyze current network hierarchy
            hierarchy_analysis = self._analyze_network_hierarchy(network_data)
            
            # Apply graduated sizing rules
            graduated_pipes = self._apply_graduated_sizing_rules(network_data, hierarchy_analysis)
            
            # Update network data with graduated sizing
            network_data['supply_pipes'] = graduated_pipes['supply_pipes']
            network_data['return_pipes'] = graduated_pipes['return_pipes']
            network_data['service_connections'] = graduated_pipes['service_connections']
            
            # Create graduated sizing result
            self.graduated_sizing_result = GraduatedSizingResult(
                hierarchy_levels=hierarchy_analysis['hierarchy_levels'],
                pipe_categories=hierarchy_analysis['pipe_categories'],
                sizing_summary=self._calculate_graduated_sizing_summary(graduated_pipes),
                cost_breakdown=self._calculate_cost_breakdown(graduated_pipes),
                performance_metrics=self._calculate_performance_metrics(graduated_pipes)
            )
            
            # Update network statistics
            network_data['network_statistics'] = self._calculate_network_statistics()
            network_data['sizing_summary'] = self._calculate_sizing_summary()
            network_data['graduated_sizing'] = self.graduated_sizing_result.__dict__
            
            print(f"✅ Applied graduated sizing")
            print(f"   Hierarchy Levels: {len(hierarchy_analysis['hierarchy_levels'])}")
            print(f"   Total Cost: €{self.graduated_sizing_result.cost_breakdown['total_cost']:.0f}")
            
            return network_data
            
        except Exception as e:
            print(f"❌ Failed to apply graduated sizing: {e}")
            raise
    
    def validate_network_sizing(self, network_data: dict) -> dict:
        """
        Validate entire network meets hydraulic constraints.
        
        Args:
            network_data: Network data to validate
        
        Returns:
            validation_result: Network validation result
        """
        print(f"✅ Validating network sizing...")
        
        try:
            # Initialize validation counters
            total_pipes = 0
            compliant_pipes = 0
            violations_by_type = {}
            violations_by_severity = {}
            critical_violations = []
            all_recommendations = []
            
            # Validate supply pipes
            for pipe in network_data.get('supply_pipes', []):
                validation = self._validate_pipe(pipe)
                total_pipes += 1
                
                if validation['compliant']:
                    compliant_pipes += 1
                else:
                    # Count violations
                    for violation in validation['violations']:
                        violation_type = violation.get('type', 'unknown')
                        severity = violation.get('severity', 'medium')
                        
                        if violation_type not in violations_by_type:
                            violations_by_type[violation_type] = 0
                        violations_by_type[violation_type] += 1
                        
                        if severity not in violations_by_severity:
                            violations_by_severity[severity] = 0
                        violations_by_severity[severity] += 1
                        
                        if severity == 'critical':
                            critical_violations.append(f"{pipe['pipe_id']}: {violation['description']}")
                    
                    all_recommendations.extend(validation['recommendations'])
            
            # Validate return pipes
            for pipe in network_data.get('return_pipes', []):
                validation = self._validate_pipe(pipe)
                total_pipes += 1
                
                if validation['compliant']:
                    compliant_pipes += 1
                else:
                    # Count violations (same logic as supply pipes)
                    for violation in validation['violations']:
                        violation_type = violation.get('type', 'unknown')
                        severity = violation.get('severity', 'medium')
                        
                        if violation_type not in violations_by_type:
                            violations_by_type[violation_type] = 0
                        violations_by_type[violation_type] += 1
                        
                        if severity not in violations_by_severity:
                            violations_by_severity[severity] = 0
                        violations_by_severity[severity] += 1
                        
                        if severity == 'critical':
                            critical_violations.append(f"{pipe['pipe_id']}: {violation['description']}")
                    
                    all_recommendations.extend(validation['recommendations'])
            
            # Calculate compliance rate
            compliance_rate = compliant_pipes / total_pipes if total_pipes > 0 else 0.0
            
            # Determine overall compliance
            overall_compliant = len(critical_violations) == 0 and compliance_rate >= 0.95
            
            # Create validation result
            self.validation_result = NetworkValidationResult(
                overall_compliant=overall_compliant,
                total_pipes=total_pipes,
                compliant_pipes=compliant_pipes,
                non_compliant_pipes=total_pipes - compliant_pipes,
                compliance_rate=compliance_rate,
                total_violations=sum(violations_by_type.values()),
                violations_by_type=violations_by_type,
                violations_by_severity=violations_by_severity,
                critical_violations=critical_violations,
                recommendations=list(set(all_recommendations))  # Remove duplicates
            )
            
            # Add validation result to network data
            network_data['validation_result'] = self.validation_result.__dict__
            
            print(f"✅ Network validation completed")
            print(f"   Total Pipes: {total_pipes}")
            print(f"   Compliant Pipes: {compliant_pipes}")
            print(f"   Compliance Rate: {compliance_rate:.1%}")
            print(f"   Critical Violations: {len(critical_violations)}")
            
            return network_data
            
        except Exception as e:
            print(f"❌ Failed to validate network sizing: {e}")
            raise
    
    def _determine_pipe_category(self, flow_rate_kg_s: float) -> str:
        """Determine pipe category based on flow rate."""
        if flow_rate_kg_s < 2.0:
            return 'service_connection'
        elif flow_rate_kg_s < 20.0:
            return 'distribution_pipe'
        else:
            return 'main_pipe'
    
    def _create_network_pipe(self, pipe_id: str, pipe_type: str, flow_rate_kg_s: float,
                           sizing_result: PipeSizingResult, length_m: float, 
                           pipe_category: str) -> dict:
        """Create a network pipe with sizing information."""
        return {
            'pipe_id': pipe_id,
            'start_node': f"node_{pipe_id}_start",
            'end_node': f"node_{pipe_id}_end",
            'length_m': length_m,
            'diameter_m': sizing_result.diameter_m,
            'diameter_nominal': sizing_result.diameter_nominal,
            'pipe_category': pipe_category,
            'pipe_type': pipe_type,
            'flow_rate_kg_s': flow_rate_kg_s,
            'velocity_ms': sizing_result.velocity_ms,
            'pressure_drop_bar': sizing_result.pressure_drop_bar,
            'cost_eur': sizing_result.total_cost_eur,
            'material': self.pipe_categories[pipe_category]['material'],
            'insulation': self.pipe_categories[pipe_category]['insulation'],
            'building_served': None,  # Will be set based on network topology
            'street_id': pipe_id.split('_')[1] if '_' in pipe_id else 'unknown',
            'flow_direction': 'plant_to_building' if pipe_type == 'supply' else 'building_to_plant',
            'standards_compliance': sizing_result.standards_compliance,
            'violations': sizing_result.violations
        }
    
    def _dict_to_network_pipe(self, pipe_dict: dict) -> NetworkPipe:
        """Convert dictionary to NetworkPipe object."""
        return NetworkPipe(
            pipe_id=pipe_dict['pipe_id'],
            start_node=pipe_dict['start_node'],
            end_node=pipe_dict['end_node'],
            length_m=pipe_dict['length_m'],
            diameter_m=pipe_dict['diameter_m'],
            diameter_nominal=pipe_dict['diameter_nominal'],
            pipe_category=pipe_dict['pipe_category'],
            pipe_type=pipe_dict['pipe_type'],
            flow_rate_kg_s=pipe_dict['flow_rate_kg_s'],
            velocity_ms=pipe_dict['velocity_ms'],
            pressure_drop_bar=pipe_dict['pressure_drop_bar'],
            cost_eur=pipe_dict['cost_eur'],
            material=pipe_dict['material'],
            insulation=pipe_dict['insulation'],
            building_served=pipe_dict['building_served'],
            street_id=pipe_dict['street_id'],
            flow_direction=pipe_dict['flow_direction'],
            standards_compliance=pipe_dict['standards_compliance'],
            violations=pipe_dict['violations']
        )
    
    def _create_service_connections(self, flow_rates: dict) -> List[dict]:
        """Create service connections for buildings."""
        service_connections = []
        
        for pipe_id, flow_rate_kg_s in flow_rates.items():
            # Create service connection for each building
            service_connection = {
                'building_id': pipe_id,
                'connection_x': 100.0,  # Mock coordinates
                'connection_y': 200.0,
                'building_x': 120.0,
                'building_y': 220.0,
                'distance_to_street': 20.0,
                'street_segment_id': pipe_id,
                'street_name': f"Street_{pipe_id}",
                'heating_load_kw': flow_rate_kg_s * 30 * 4.18,  # Convert to kW
                'annual_heat_demand_kwh': flow_rate_kg_s * 30 * 4.18 * 2000,  # Annual demand
                'building_type': 'residential',
                'building_area_m2': 120.0,
                'pipe_type': 'supply_service',
                'temperature_c': 70.0,
                'flow_direction': 'main_to_building'
            }
            service_connections.append(service_connection)
        
        return service_connections
    
    def _calculate_network_statistics(self) -> dict:
        """Calculate network statistics."""
        if not self.network_pipes:
            return {}
        
        total_length = sum(pipe.length_m for pipe in self.network_pipes.values())
        total_cost = sum(pipe.cost_eur for pipe in self.network_pipes.values())
        total_flow = sum(pipe.flow_rate_kg_s for pipe in self.network_pipes.values())
        
        # Calculate diameter distribution
        diameter_distribution = {}
        for pipe in self.network_pipes.values():
            diameter = pipe.diameter_nominal
            if diameter not in diameter_distribution:
                diameter_distribution[diameter] = 0
            diameter_distribution[diameter] += 1
        
        return {
            'total_pipes': len(self.network_pipes),
            'total_length_m': total_length,
            'total_cost_eur': total_cost,
            'total_flow_kg_s': total_flow,
            'diameter_distribution': diameter_distribution,
            'average_diameter_mm': np.mean([pipe.diameter_m * 1000 for pipe in self.network_pipes.values()]),
            'average_velocity_ms': np.mean([pipe.velocity_ms for pipe in self.network_pipes.values()]),
            'average_pressure_drop_bar': np.mean([pipe.pressure_drop_bar for pipe in self.network_pipes.values()])
        }
    
    def _calculate_sizing_summary(self) -> dict:
        """Calculate sizing summary."""
        if not self.network_pipes:
            return {}
        
        # Calculate category distribution
        category_distribution = {}
        for pipe in self.network_pipes.values():
            category = pipe.pipe_category
            if category not in category_distribution:
                category_distribution[category] = 0
            category_distribution[category] += 1
        
        # Calculate compliance statistics
        compliant_pipes = sum(1 for pipe in self.network_pipes.values() if len(pipe.violations) == 0)
        total_pipes = len(self.network_pipes)
        
        return {
            'category_distribution': category_distribution,
            'compliant_pipes': compliant_pipes,
            'total_pipes': total_pipes,
            'compliance_rate': compliant_pipes / total_pipes if total_pipes > 0 else 0.0,
            'total_violations': sum(len(pipe.violations) for pipe in self.network_pipes.values())
        }
    
    def _analyze_network_hierarchy(self, network_data: dict) -> dict:
        """Analyze network hierarchy for graduated sizing."""
        hierarchy_levels = {}
        pipe_categories = {}
        
        # Analyze supply pipes
        for pipe in network_data.get('supply_pipes', []):
            flow_rate = pipe['flow_rate_kg_s']
            category = pipe['pipe_category']
            
            # Determine hierarchy level
            level = self._determine_hierarchy_level(flow_rate)
            if level not in hierarchy_levels:
                hierarchy_levels[level] = {
                    'name': self.hierarchy_levels[level]['name'],
                    'pipes': [],
                    'total_flow_kg_s': 0,
                    'total_length_m': 0,
                    'total_cost_eur': 0
                }
            
            hierarchy_levels[level]['pipes'].append(pipe['pipe_id'])
            hierarchy_levels[level]['total_flow_kg_s'] += flow_rate
            hierarchy_levels[level]['total_length_m'] += pipe['length_m']
            hierarchy_levels[level]['total_cost_eur'] += pipe['cost_eur']
            
            # Categorize pipes
            if category not in pipe_categories:
                pipe_categories[category] = []
            pipe_categories[category].append(pipe['pipe_id'])
        
        return {
            'hierarchy_levels': hierarchy_levels,
            'pipe_categories': pipe_categories
        }
    
    def _determine_hierarchy_level(self, flow_rate_kg_s: float) -> int:
        """Determine hierarchy level based on flow rate."""
        for level, info in self.hierarchy_levels.items():
            if info['min_flow_kg_s'] <= flow_rate_kg_s < info['max_flow_kg_s']:
                return level
        return 5  # Default to highest level
    
    def _apply_graduated_sizing_rules(self, network_data: dict, hierarchy_analysis: dict) -> dict:
        """Apply graduated sizing rules to network."""
        graduated_pipes = {
            'supply_pipes': [],
            'return_pipes': [],
            'service_connections': network_data.get('service_connections', [])
        }
        
        # Apply graduated sizing to supply pipes
        for pipe in network_data.get('supply_pipes', []):
            graduated_pipe = self._apply_graduated_sizing_to_pipe(pipe, hierarchy_analysis)
            graduated_pipes['supply_pipes'].append(graduated_pipe)
        
        # Apply graduated sizing to return pipes
        for pipe in network_data.get('return_pipes', []):
            graduated_pipe = self._apply_graduated_sizing_to_pipe(pipe, hierarchy_analysis)
            graduated_pipes['return_pipes'].append(graduated_pipe)
        
        return graduated_pipes
    
    def _apply_graduated_sizing_to_pipe(self, pipe: dict, hierarchy_analysis: dict) -> dict:
        """Apply graduated sizing to a single pipe."""
        # For now, return the pipe as-is
        # In a real implementation, this would apply graduated sizing rules
        # such as ensuring main pipes are larger than distribution pipes
        return pipe.copy()
    
    def _calculate_graduated_sizing_summary(self, graduated_pipes: dict) -> dict:
        """Calculate graduated sizing summary."""
        total_pipes = len(graduated_pipes['supply_pipes']) + len(graduated_pipes['return_pipes'])
        total_cost = sum(pipe['cost_eur'] for pipe in graduated_pipes['supply_pipes']) + \
                    sum(pipe['cost_eur'] for pipe in graduated_pipes['return_pipes'])
        
        return {
            'total_pipes': total_pipes,
            'total_cost_eur': total_cost,
            'average_cost_per_pipe_eur': total_cost / total_pipes if total_pipes > 0 else 0
        }
    
    def _calculate_cost_breakdown(self, graduated_pipes: dict) -> dict:
        """Calculate cost breakdown by category."""
        cost_breakdown = {
            'service_connections': 0,
            'distribution_pipes': 0,
            'main_pipes': 0,
            'total_cost': 0
        }
        
        # Calculate costs for supply pipes
        for pipe in graduated_pipes['supply_pipes']:
            category = pipe['pipe_category']
            cost = pipe['cost_eur']
            
            if category in cost_breakdown:
                cost_breakdown[category] += cost
            cost_breakdown['total_cost'] += cost
        
        # Calculate costs for return pipes
        for pipe in graduated_pipes['return_pipes']:
            category = pipe['pipe_category']
            cost = pipe['cost_eur']
            
            if category in cost_breakdown:
                cost_breakdown[category] += cost
            cost_breakdown['total_cost'] += cost
        
        return cost_breakdown
    
    def _calculate_performance_metrics(self, graduated_pipes: dict) -> dict:
        """Calculate performance metrics."""
        all_pipes = graduated_pipes['supply_pipes'] + graduated_pipes['return_pipes']
        
        if not all_pipes:
            return {}
        
        velocities = [pipe['velocity_ms'] for pipe in all_pipes]
        pressure_drops = [pipe['pressure_drop_bar'] for pipe in all_pipes]
        diameters = [pipe['diameter_m'] for pipe in all_pipes]
        
        return {
            'average_velocity_ms': np.mean(velocities),
            'max_velocity_ms': max(velocities),
            'min_velocity_ms': min(velocities),
            'average_pressure_drop_bar': np.mean(pressure_drops),
            'max_pressure_drop_bar': max(pressure_drops),
            'average_diameter_mm': np.mean(diameters) * 1000,
            'max_diameter_mm': max(diameters) * 1000,
            'min_diameter_mm': min(diameters) * 1000
        }
    
    def _validate_pipe(self, pipe: dict) -> dict:
        """Validate a single pipe against constraints."""
        violations = []
        recommendations = []
        
        # Check velocity constraints
        velocity_ms = pipe['velocity_ms']
        pipe_category = pipe['pipe_category']
        velocity_limit = self.pipe_categories[pipe_category]['velocity_limit_ms']
        
        if velocity_ms > velocity_limit:
            violations.append({
                'type': 'velocity_exceeded',
                'severity': 'high',
                'description': f"Velocity {velocity_ms:.2f} m/s exceeds limit {velocity_limit} m/s"
            })
            recommendations.append("Consider increasing pipe diameter to reduce velocity")
        
        # Check pressure drop constraints
        pressure_drop_bar = pipe['pressure_drop_bar']
        pressure_drop_limit_pa_per_m = self.pipe_categories[pipe_category]['pressure_drop_limit_pa_per_m']
        pressure_drop_limit_bar = pressure_drop_limit_pa_per_m * pipe['length_m'] / 100000
        
        if pressure_drop_bar > pressure_drop_limit_bar:
            violations.append({
                'type': 'pressure_drop_exceeded',
                'severity': 'high',
                'description': f"Pressure drop {pressure_drop_bar:.3f} bar exceeds limit {pressure_drop_limit_bar:.3f} bar"
            })
            recommendations.append("Consider increasing pipe diameter to reduce pressure drop")
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'recommendations': recommendations
        }
    
    def export_enhanced_network(self, network_data: dict, output_path: str) -> None:
        """
        Export enhanced network data to JSON file.
        
        Args:
            network_data: Enhanced network data
            output_path: Output file path
        """
        with open(output_path, 'w') as f:
            json.dump(network_data, f, indent=2)
        
        print(f"✅ Enhanced network data exported to {output_path}")
    
    def print_network_summary(self) -> None:
        """Print comprehensive network summary."""
        if not self.network_pipes:
            print("⚠️ No network data available")
            return
        
        stats = self._calculate_network_statistics()
        sizing_summary = self._calculate_sizing_summary()
        
        print(f"\n📊 ENHANCED NETWORK SUMMARY")
        print(f"=" * 50)
        print(f"🏗️ NETWORK OVERVIEW:")
        print(f"   Total Pipes: {stats['total_pipes']}")
        print(f"   Total Length: {stats['total_length_m']:.0f} m")
        print(f"   Total Cost: €{stats['total_cost_eur']:.0f}")
        print(f"   Total Flow: {stats['total_flow_kg_s']:.2f} kg/s")
        print(f"")
        print(f"📏 PIPE SIZING:")
        print(f"   Average Diameter: {stats['average_diameter_mm']:.1f} mm")
        print(f"   Average Velocity: {stats['average_velocity_ms']:.2f} m/s")
        print(f"   Average Pressure Drop: {stats['average_pressure_drop_bar']:.3f} bar")
        print(f"")
        print(f"✅ COMPLIANCE:")
        print(f"   Compliant Pipes: {sizing_summary['compliant_pipes']}/{sizing_summary['total_pipes']}")
        print(f"   Compliance Rate: {sizing_summary['compliance_rate']:.1%}")
        print(f"   Total Violations: {sizing_summary['total_violations']}")
        print(f"")
        print(f"📊 DIAMETER DISTRIBUTION:")
        for diameter, count in stats['diameter_distribution'].items():
            print(f"   {diameter}: {count} pipes")
        
        if self.validation_result:
            print(f"")
            print(f"🔍 VALIDATION RESULTS:")
            print(f"   Overall Compliant: {self.validation_result.overall_compliant}")
            print(f"   Critical Violations: {len(self.validation_result.critical_violations)}")
            if self.validation_result.recommendations:
                print(f"   Recommendations: {len(self.validation_result.recommendations)}")


# Example usage and testing
if __name__ == "__main__":
    # Create pipe sizing engine
    from src.cha_pipe_sizing import CHAPipeSizingEngine
    
    config = {
        'max_velocity_ms': 2.0,
        'min_velocity_ms': 0.1,
        'max_pressure_drop_pa_per_m': 5000,
        'pipe_roughness_mm': 0.1
    }
    
    sizing_engine = CHAPipeSizingEngine(config)
    
    # Create enhanced network builder
    network_builder = CHAEnhancedNetworkBuilder(sizing_engine)
    
    # Example flow rates
    flow_rates = {
        'pipe_1': 0.5,   # Service connection
        'pipe_2': 5.0,   # Distribution pipe
        'pipe_3': 25.0,  # Main pipe
        'pipe_4': 1.2    # Service connection
    }
    
    try:
        # Create sized dual-pipe network
        network_data = network_builder.create_sized_dual_pipe_network(flow_rates)
        
        # Apply graduated sizing
        network_data = network_builder.apply_graduated_sizing(network_data)
        
        # Validate network sizing
        network_data = network_builder.validate_network_sizing(network_data)
        
        # Print summary
        network_builder.print_network_summary()
        
        # Export network data
        network_builder.export_enhanced_network(network_data, "enhanced_network.json")
        
        print(f"\n🎉 Enhanced Network Builder testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in enhanced network builder: {e}")
        import traceback
        traceback.print_exc()
