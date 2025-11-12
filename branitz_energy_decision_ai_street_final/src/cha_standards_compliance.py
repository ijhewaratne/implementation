"""
CHA Standards Compliance Engine - Engineering Standards Validation

This module implements compliance checking for engineering standards
including EN 13941, DIN 1988, and local codes for district heating networks.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import math
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")


@dataclass
class StandardsViolation:
    """Standards violation information."""
    standard: str
    violation_type: str
    description: str
    current_value: float
    limit_value: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    recommendation: str


@dataclass
class ComplianceResult:
    """Standards compliance result."""
    pipe_id: str
    overall_compliant: bool
    standards_compliance: Dict[str, bool]
    violations: List[StandardsViolation]
    recommendations: List[str]
    compliance_score: float  # 0.0 to 1.0


@dataclass
class StandardsSummary:
    """Overall standards compliance summary."""
    total_pipes: int
    compliant_pipes: int
    non_compliant_pipes: int
    compliance_rate: float
    total_violations: int
    violations_by_standard: Dict[str, int]
    violations_by_severity: Dict[str, int]
    critical_violations: List[StandardsViolation]


class CHAStandardsComplianceEngine:
    """
    Standards Compliance Engine for District Heating Networks.
    
    Validates pipe sizing and network design against engineering standards
    including EN 13941, DIN 1988, and local codes.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the standards compliance engine.
        
        Args:
            config: Configuration dictionary with standards parameters
        """
        self.config = config
        
        # Define engineering standards
        self.standards = self._define_engineering_standards()
        
        # Define violation severity levels
        self.severity_levels = {
            'critical': {'threshold': 0.5, 'weight': 4},
            'high': {'threshold': 0.3, 'weight': 3},
            'medium': {'threshold': 0.2, 'weight': 2},
            'low': {'threshold': 0.1, 'weight': 1}
        }
        
        print(f"✅ Standards Compliance Engine initialized")
        print(f"   Standards: {list(self.standards.keys())}")
        print(f"   Severity Levels: {len(self.severity_levels)}")
    
    def _define_engineering_standards(self) -> Dict[str, Dict]:
        """Define engineering standards and their requirements."""
        return {
            'EN_13941': {
                'name': 'EN 13941 - District heating pipes',
                'description': 'Preinsulated bonded pipe systems for directly buried hot water networks',
                'requirements': {
                    'velocity_limits': {
                        'maximum_velocity_ms': 2.0,
                        'minimum_velocity_ms': 0.1,
                        'recommended_velocity_ms': 1.0
                    },
                    'pressure_drop_limits': {
                        'maximum_pressure_drop_pa_per_m': 5000,  # 0.5 bar/100m
                        'recommended_pressure_drop_pa_per_m': 2000  # 0.2 bar/100m
                    },
                    'temperature_requirements': {
                        'supply_temperature_range_c': (40, 90),
                        'return_temperature_range_c': (30, 60),
                        'temperature_difference_minimum_k': 20
                    },
                    'pressure_requirements': {
                        'working_pressure_range_bar': (2, 16),
                        'test_pressure_multiplier': 1.5
                    },
                    'material_requirements': {
                        'pipe_material': 'steel',
                        'insulation_material': 'polyurethane',
                        'outer_jacket': 'HDPE',
                        'minimum_insulation_thickness_mm': 30
                    }
                }
            },
            'DIN_1988': {
                'name': 'DIN 1988 - Technical rules for drinking water installations',
                'description': 'Water supply systems and district heating',
                'requirements': {
                    'velocity_limits': {
                        'main_pipes_velocity_ms': 2.0,
                        'distribution_velocity_ms': 2.0,
                        'service_velocity_ms': 1.5,
                        'minimum_velocity_ms': 0.1
                    },
                    'pressure_drop_limits': {
                        'main_pipes_pressure_drop_pa_per_m': 3000,  # 0.3 bar/100m
                        'distribution_pressure_drop_pa_per_m': 4000,  # 0.4 bar/100m
                        'service_pressure_drop_pa_per_m': 5000  # 0.5 bar/100m
                    },
                    'pipe_sizing_method': {
                        'method': 'velocity_based',
                        'calculation_basis': 'peak_demand',
                        'safety_factors': {
                            'peak_factor': 1.2,
                            'future_growth': 1.1,
                            'safety_margin': 1.1
                        }
                    }
                }
            },
            'VDI_2067': {
                'name': 'VDI 2067 - Economic efficiency of building installations',
                'description': 'Economic optimization of district heating systems',
                'requirements': {
                    'economic_criteria': {
                        'maximum_payback_period_years': 15,
                        'minimum_internal_rate_of_return': 0.06,
                        'maximum_lifecycle_cost_eur_per_mwh': 50
                    },
                    'efficiency_requirements': {
                        'minimum_system_efficiency': 0.85,
                        'maximum_heat_loss_percentage': 0.15,
                        'minimum_pump_efficiency': 0.75
                    }
                }
            },
            'Local_Codes': {
                'name': 'Local Building Codes',
                'description': 'Local building and utility codes',
                'requirements': {
                    'safety_requirements': {
                        'minimum_safety_factor': 2.0,
                        'maximum_working_pressure_bar': 16,
                        'minimum_wall_thickness_mm': 3.0
                    },
                    'environmental_requirements': {
                        'maximum_noise_level_db': 45,
                        'maximum_ground_temperature_rise_k': 5,
                        'minimum_insulation_efficiency': 0.95
                    }
                }
            }
        }
    
    def validate_pipe_compliance(self, pipe_data: dict) -> ComplianceResult:
        """
        Validate pipe compliance against all applicable standards.
        
        Args:
            pipe_data: Dictionary with pipe information
        
        Returns:
            ComplianceResult: Compliance validation result
        """
        pipe_id = pipe_data.get('pipe_id', 'unknown')
        violations = []
        recommendations = []
        standards_compliance = {}
        
        # Validate against each standard
        for standard_name, standard_info in self.standards.items():
            standard_violations = self._validate_against_standard(pipe_data, standard_name, standard_info)
            violations.extend(standard_violations)
            
            # Check if standard is compliant
            standard_compliant = len(standard_violations) == 0
            standards_compliance[standard_name] = standard_compliant
        
        # Generate recommendations
        recommendations = self._generate_recommendations(violations)
        
        # Calculate compliance score
        compliance_score = self._calculate_compliance_score(violations)
        
        # Determine overall compliance
        overall_compliant = len(violations) == 0
        
        return ComplianceResult(
            pipe_id=pipe_id,
            overall_compliant=overall_compliant,
            standards_compliance=standards_compliance,
            violations=violations,
            recommendations=recommendations,
            compliance_score=compliance_score
        )
    
    def _validate_against_standard(self, pipe_data: dict, standard_name: str, 
                                 standard_info: dict) -> List[StandardsViolation]:
        """Validate pipe against a specific standard."""
        violations = []
        requirements = standard_info['requirements']
        
        # Extract pipe parameters
        velocity_ms = pipe_data.get('velocity_ms', 0)
        pressure_drop_pa_per_m = pipe_data.get('pressure_drop_pa_per_m', 0)
        diameter_m = pipe_data.get('diameter_m', 0)
        pipe_category = pipe_data.get('pipe_category', 'unknown')
        temperature_supply_c = pipe_data.get('temperature_supply_c', 70)
        temperature_return_c = pipe_data.get('temperature_return_c', 40)
        pressure_bar = pipe_data.get('pressure_bar', 2)
        
        # EN 13941 validation
        if standard_name == 'EN_13941':
            violations.extend(self._validate_en_13941(
                velocity_ms, pressure_drop_pa_per_m, temperature_supply_c, 
                temperature_return_c, pressure_bar, requirements
            ))
        
        # DIN 1988 validation
        elif standard_name == 'DIN_1988':
            violations.extend(self._validate_din_1988(
                velocity_ms, pressure_drop_pa_per_m, pipe_category, requirements
            ))
        
        # VDI 2067 validation
        elif standard_name == 'VDI_2067':
            violations.extend(self._validate_vdi_2067(
                pipe_data, requirements
            ))
        
        # Local codes validation
        elif standard_name == 'Local_Codes':
            violations.extend(self._validate_local_codes(
                pipe_data, requirements
            ))
        
        return violations
    
    def _validate_en_13941(self, velocity_ms: float, pressure_drop_pa_per_m: float,
                          temperature_supply_c: float, temperature_return_c: float,
                          pressure_bar: float, requirements: dict) -> List[StandardsViolation]:
        """Validate against EN 13941 standard."""
        violations = []
        
        # Velocity validation
        velocity_limits = requirements['velocity_limits']
        if velocity_ms > velocity_limits['maximum_velocity_ms']:
            violations.append(StandardsViolation(
                standard='EN_13941',
                violation_type='velocity_exceeded',
                description=f"Velocity {velocity_ms:.2f} m/s exceeds maximum limit {velocity_limits['maximum_velocity_ms']} m/s",
                current_value=velocity_ms,
                limit_value=velocity_limits['maximum_velocity_ms'],
                severity=self._determine_severity(velocity_ms, velocity_limits['maximum_velocity_ms']),
                recommendation="Increase pipe diameter to reduce velocity"
            ))
        
        if velocity_ms < velocity_limits['minimum_velocity_ms']:
            violations.append(StandardsViolation(
                standard='EN_13941',
                violation_type='velocity_below_minimum',
                description=f"Velocity {velocity_ms:.2f} m/s below minimum limit {velocity_limits['minimum_velocity_ms']} m/s",
                current_value=velocity_ms,
                limit_value=velocity_limits['minimum_velocity_ms'],
                severity='medium',
                recommendation="Decrease pipe diameter to increase velocity"
            ))
        
        # Pressure drop validation
        pressure_drop_limits = requirements['pressure_drop_limits']
        if pressure_drop_pa_per_m > pressure_drop_limits['maximum_pressure_drop_pa_per_m']:
            violations.append(StandardsViolation(
                standard='EN_13941',
                violation_type='pressure_drop_exceeded',
                description=f"Pressure drop {pressure_drop_pa_per_m:.0f} Pa/m exceeds maximum limit {pressure_drop_limits['maximum_pressure_drop_pa_per_m']} Pa/m",
                current_value=pressure_drop_pa_per_m,
                limit_value=pressure_drop_limits['maximum_pressure_drop_pa_per_m'],
                severity=self._determine_severity(pressure_drop_pa_per_m, pressure_drop_limits['maximum_pressure_drop_pa_per_m']),
                recommendation="Increase pipe diameter to reduce pressure drop"
            ))
        
        # Temperature validation
        temperature_requirements = requirements['temperature_requirements']
        if temperature_supply_c < temperature_requirements['supply_temperature_range_c'][0] or \
           temperature_supply_c > temperature_requirements['supply_temperature_range_c'][1]:
            violations.append(StandardsViolation(
                standard='EN_13941',
                violation_type='supply_temperature_out_of_range',
                description=f"Supply temperature {temperature_supply_c}°C outside range {temperature_requirements['supply_temperature_range_c']}°C",
                current_value=temperature_supply_c,
                limit_value=temperature_requirements['supply_temperature_range_c'][1],
                severity='high',
                recommendation="Adjust supply temperature to within acceptable range"
            ))
        
        # Pressure validation
        pressure_requirements = requirements['pressure_requirements']
        if pressure_bar < pressure_requirements['working_pressure_range_bar'][0] or \
           pressure_bar > pressure_requirements['working_pressure_range_bar'][1]:
            violations.append(StandardsViolation(
                standard='EN_13941',
                violation_type='pressure_out_of_range',
                description=f"Working pressure {pressure_bar} bar outside range {pressure_requirements['working_pressure_range_bar']} bar",
                current_value=pressure_bar,
                limit_value=pressure_requirements['working_pressure_range_bar'][1],
                severity='critical',
                recommendation="Adjust working pressure to within acceptable range"
            ))
        
        return violations
    
    def _validate_din_1988(self, velocity_ms: float, pressure_drop_pa_per_m: float,
                          pipe_category: str, requirements: dict) -> List[StandardsViolation]:
        """Validate against DIN 1988 standard."""
        violations = []
        
        # Get category-specific limits
        velocity_limits = requirements['velocity_limits']
        pressure_drop_limits = requirements['pressure_drop_limits']
        
        # Determine velocity limit based on pipe category
        if pipe_category == 'main_pipe':
            velocity_limit = velocity_limits['main_pipes_velocity_ms']
            pressure_drop_limit = pressure_drop_limits['main_pipes_pressure_drop_pa_per_m']
        elif pipe_category == 'distribution_pipe':
            velocity_limit = velocity_limits['distribution_velocity_ms']
            pressure_drop_limit = pressure_drop_limits['distribution_pressure_drop_pa_per_m']
        elif pipe_category == 'service_connection':
            velocity_limit = velocity_limits['service_velocity_ms']
            pressure_drop_limit = pressure_drop_limits['service_pressure_drop_pa_per_m']
        else:
            velocity_limit = velocity_limits['main_pipes_velocity_ms']
            pressure_drop_limit = pressure_drop_limits['main_pipes_pressure_drop_pa_per_m']
        
        # Velocity validation
        if velocity_ms > velocity_limit:
            violations.append(StandardsViolation(
                standard='DIN_1988',
                violation_type='velocity_exceeded',
                description=f"Velocity {velocity_ms:.2f} m/s exceeds limit {velocity_limit} m/s for {pipe_category}",
                current_value=velocity_ms,
                limit_value=velocity_limit,
                severity=self._determine_severity(velocity_ms, velocity_limit),
                recommendation=f"Increase pipe diameter to reduce velocity for {pipe_category}"
            ))
        
        # Pressure drop validation
        if pressure_drop_pa_per_m > pressure_drop_limit:
            violations.append(StandardsViolation(
                standard='DIN_1988',
                violation_type='pressure_drop_exceeded',
                description=f"Pressure drop {pressure_drop_pa_per_m:.0f} Pa/m exceeds limit {pressure_drop_limit} Pa/m for {pipe_category}",
                current_value=pressure_drop_pa_per_m,
                limit_value=pressure_drop_limit,
                severity=self._determine_severity(pressure_drop_pa_per_m, pressure_drop_limit),
                recommendation=f"Increase pipe diameter to reduce pressure drop for {pipe_category}"
            ))
        
        return violations
    
    def _validate_vdi_2067(self, pipe_data: dict, requirements: dict) -> List[StandardsViolation]:
        """Validate against VDI 2067 standard."""
        violations = []
        
        # Economic criteria validation
        economic_criteria = requirements['economic_criteria']
        payback_period = pipe_data.get('payback_period_years', 0)
        lifecycle_cost = pipe_data.get('lifecycle_cost_eur_per_mwh', 0)
        
        if payback_period > economic_criteria['maximum_payback_period_years']:
            violations.append(StandardsViolation(
                standard='VDI_2067',
                violation_type='payback_period_exceeded',
                description=f"Payback period {payback_period:.1f} years exceeds maximum {economic_criteria['maximum_payback_period_years']} years",
                current_value=payback_period,
                limit_value=economic_criteria['maximum_payback_period_years'],
                severity='medium',
                recommendation="Optimize pipe sizing to improve economic performance"
            ))
        
        if lifecycle_cost > economic_criteria['maximum_lifecycle_cost_eur_per_mwh']:
            violations.append(StandardsViolation(
                standard='VDI_2067',
                violation_type='lifecycle_cost_exceeded',
                description=f"Lifecycle cost {lifecycle_cost:.1f} EUR/MWh exceeds maximum {economic_criteria['maximum_lifecycle_cost_eur_per_mwh']} EUR/MWh",
                current_value=lifecycle_cost,
                limit_value=economic_criteria['maximum_lifecycle_cost_eur_per_mwh'],
                severity='medium',
                recommendation="Optimize pipe sizing and material selection to reduce lifecycle costs"
            ))
        
        return violations
    
    def _validate_local_codes(self, pipe_data: dict, requirements: dict) -> List[StandardsViolation]:
        """Validate against local building codes."""
        violations = []
        
        # Safety requirements validation
        safety_requirements = requirements['safety_requirements']
        safety_factor = pipe_data.get('safety_factor', 1.0)
        working_pressure = pipe_data.get('pressure_bar', 2)
        
        if safety_factor < safety_requirements['minimum_safety_factor']:
            violations.append(StandardsViolation(
                standard='Local_Codes',
                violation_type='safety_factor_insufficient',
                description=f"Safety factor {safety_factor:.1f} below minimum {safety_requirements['minimum_safety_factor']}",
                current_value=safety_factor,
                limit_value=safety_requirements['minimum_safety_factor'],
                severity='critical',
                recommendation="Increase pipe wall thickness or use higher grade material"
            ))
        
        if working_pressure > safety_requirements['maximum_working_pressure_bar']:
            violations.append(StandardsViolation(
                standard='Local_Codes',
                violation_type='pressure_exceeds_maximum',
                description=f"Working pressure {working_pressure} bar exceeds maximum {safety_requirements['maximum_working_pressure_bar']} bar",
                current_value=working_pressure,
                limit_value=safety_requirements['maximum_working_pressure_bar'],
                severity='critical',
                recommendation="Reduce working pressure or use higher pressure rated pipes"
            ))
        
        return violations
    
    def _determine_severity(self, current_value: float, limit_value: float) -> str:
        """Determine violation severity based on exceedance ratio."""
        if limit_value == 0:
            return 'medium'
        
        exceedance_ratio = current_value / limit_value
        
        if exceedance_ratio >= 2.0:
            return 'critical'
        elif exceedance_ratio >= 1.5:
            return 'high'
        elif exceedance_ratio >= 1.2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendations(self, violations: List[StandardsViolation]) -> List[str]:
        """Generate recommendations based on violations."""
        recommendations = []
        
        # Group violations by type
        violation_types = {}
        for violation in violations:
            if violation.violation_type not in violation_types:
                violation_types[violation.violation_type] = []
            violation_types[violation.violation_type].append(violation)
        
        # Generate recommendations for each violation type
        for violation_type, type_violations in violation_types.items():
            if violation_type == 'velocity_exceeded':
                recommendations.append("Consider increasing pipe diameter to reduce velocity")
            elif violation_type == 'pressure_drop_exceeded':
                recommendations.append("Consider increasing pipe diameter to reduce pressure drop")
            elif violation_type == 'velocity_below_minimum':
                recommendations.append("Consider decreasing pipe diameter to increase velocity")
            elif violation_type == 'safety_factor_insufficient':
                recommendations.append("Consider using higher grade material or increasing wall thickness")
            elif violation_type == 'payback_period_exceeded':
                recommendations.append("Consider optimizing pipe sizing for better economic performance")
            else:
                recommendations.append("Review pipe design parameters")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _calculate_compliance_score(self, violations: List[StandardsViolation]) -> float:
        """Calculate compliance score (0.0 to 1.0)."""
        if not violations:
            return 1.0
        
        # Calculate weighted score based on severity
        total_weight = 0
        violation_weight = 0
        
        for violation in violations:
            severity_info = self.severity_levels.get(violation.severity, {'weight': 1})
            weight = severity_info['weight']
            total_weight += weight
            violation_weight += weight
        
        if total_weight == 0:
            return 1.0
        
        compliance_score = 1.0 - (violation_weight / total_weight)
        return max(0.0, compliance_score)
    
    def validate_network_compliance(self, pipe_results: List[ComplianceResult]) -> StandardsSummary:
        """
        Validate overall network compliance.
        
        Args:
            pipe_results: List of pipe compliance results
        
        Returns:
            StandardsSummary: Overall compliance summary
        """
        total_pipes = len(pipe_results)
        compliant_pipes = sum(1 for result in pipe_results if result.overall_compliant)
        non_compliant_pipes = total_pipes - compliant_pipes
        compliance_rate = compliant_pipes / total_pipes if total_pipes > 0 else 0.0
        
        # Count violations by standard
        violations_by_standard = {}
        violations_by_severity = {}
        critical_violations = []
        
        for result in pipe_results:
            for violation in result.violations:
                # Count by standard
                if violation.standard not in violations_by_standard:
                    violations_by_standard[violation.standard] = 0
                violations_by_standard[violation.standard] += 1
                
                # Count by severity
                if violation.severity not in violations_by_severity:
                    violations_by_severity[violation.severity] = 0
                violations_by_severity[violation.severity] += 1
                
                # Collect critical violations
                if violation.severity == 'critical':
                    critical_violations.append(violation)
        
        total_violations = sum(violations_by_standard.values())
        
        return StandardsSummary(
            total_pipes=total_pipes,
            compliant_pipes=compliant_pipes,
            non_compliant_pipes=non_compliant_pipes,
            compliance_rate=compliance_rate,
            total_violations=total_violations,
            violations_by_standard=violations_by_standard,
            violations_by_severity=violations_by_severity,
            critical_violations=critical_violations
        )
    
    def export_compliance_results(self, pipe_results: List[ComplianceResult], 
                                network_summary: StandardsSummary,
                                output_path: str) -> None:
        """
        Export compliance results to JSON file.
        
        Args:
            pipe_results: List of pipe compliance results
            network_summary: Overall compliance summary
            output_path: Output file path
        """
        export_data = {
            'network_summary': {
                'total_pipes': network_summary.total_pipes,
                'compliant_pipes': network_summary.compliant_pipes,
                'non_compliant_pipes': network_summary.non_compliant_pipes,
                'compliance_rate': network_summary.compliance_rate,
                'total_violations': network_summary.total_violations,
                'violations_by_standard': network_summary.violations_by_standard,
                'violations_by_severity': network_summary.violations_by_severity,
                'critical_violations_count': len(network_summary.critical_violations)
            },
            'pipe_results': []
        }
        
        # Export pipe results
        for result in pipe_results:
            pipe_data = {
                'pipe_id': result.pipe_id,
                'overall_compliant': result.overall_compliant,
                'compliance_score': result.compliance_score,
                'standards_compliance': result.standards_compliance,
                'violations': [
                    {
                        'standard': v.standard,
                        'violation_type': v.violation_type,
                        'description': v.description,
                        'current_value': v.current_value,
                        'limit_value': v.limit_value,
                        'severity': v.severity,
                        'recommendation': v.recommendation
                    }
                    for v in result.violations
                ],
                'recommendations': result.recommendations
            }
            export_data['pipe_results'].append(pipe_data)
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Compliance results exported to {output_path}")


# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = {
        'standards_enabled': ['EN_13941', 'DIN_1988', 'VDI_2067', 'Local_Codes'],
        'severity_thresholds': {
            'critical': 0.5,
            'high': 0.3,
            'medium': 0.2,
            'low': 0.1
        }
    }
    
    # Create standards compliance engine
    compliance_engine = CHAStandardsComplianceEngine(config)
    
    # Example pipe data
    test_pipes = [
        {
            'pipe_id': 'pipe_1',
            'velocity_ms': 2.5,  # Exceeds limit
            'pressure_drop_pa_per_m': 3000,
            'diameter_m': 0.1,
            'pipe_category': 'distribution_pipe',
            'temperature_supply_c': 70,
            'temperature_return_c': 40,
            'pressure_bar': 6,
            'safety_factor': 2.5,
            'payback_period_years': 12,
            'lifecycle_cost_eur_per_mwh': 45
        },
        {
            'pipe_id': 'pipe_2',
            'velocity_ms': 1.2,  # Within limits
            'pressure_drop_pa_per_m': 2500,
            'diameter_m': 0.125,
            'pipe_category': 'distribution_pipe',
            'temperature_supply_c': 70,
            'temperature_return_c': 40,
            'pressure_bar': 6,
            'safety_factor': 2.5,
            'payback_period_years': 8,
            'lifecycle_cost_eur_per_mwh': 35
        }
    ]
    
    # Validate compliance for each pipe
    pipe_results = []
    for pipe_data in test_pipes:
        result = compliance_engine.validate_pipe_compliance(pipe_data)
        pipe_results.append(result)
        
        print(f"\n📊 Compliance Result for {pipe_data['pipe_id']}:")
        print(f"   Overall Compliant: {result.overall_compliant}")
        print(f"   Compliance Score: {result.compliance_score:.2f}")
        print(f"   Standards Compliance: {result.standards_compliance}")
        if result.violations:
            print(f"   Violations: {len(result.violations)}")
            for violation in result.violations:
                print(f"     - {violation.standard}: {violation.description} ({violation.severity})")
        if result.recommendations:
            print(f"   Recommendations: {result.recommendations}")
    
    # Validate overall network compliance
    network_summary = compliance_engine.validate_network_compliance(pipe_results)
    
    # Export results
    compliance_engine.export_compliance_results(pipe_results, network_summary, "test_compliance_results.json")
    
    # Print summary
    print(f"\n📊 Network Compliance Summary:")
    print(f"   Total Pipes: {network_summary.total_pipes}")
    print(f"   Compliant Pipes: {network_summary.compliant_pipes}")
    print(f"   Compliance Rate: {network_summary.compliance_rate:.1%}")
    print(f"   Total Violations: {network_summary.total_violations}")
    print(f"   Critical Violations: {len(network_summary.critical_violations)}")
    print(f"   Violations by Standard: {network_summary.violations_by_standard}")
    print(f"   Violations by Severity: {network_summary.violations_by_severity}")
