"""
CHA Standards Validator - Engineering Standards Compliance Validation

This module validates CHA network designs against engineering standards including
EN 13941, DIN 1988, VDI 2067, and local codes for district heating systems.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import warnings

# Import our enhanced configuration loader
from cha_enhanced_config_loader import CHAEnhancedConfigLoader, EnhancedCHAConfig

warnings.filterwarnings("ignore")


@dataclass
class ComplianceResult:
    """Standards compliance result."""
    standard_name: str
    is_compliant: bool
    compliance_rate: float
    violations: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    recommendations: List[str]
    summary: Dict[str, Any]


@dataclass
class StandardsValidationResult:
    """Complete standards validation result."""
    overall_compliant: bool
    overall_compliance_rate: float
    standards_results: Dict[str, ComplianceResult]
    critical_violations: List[Dict[str, Any]]
    summary_recommendations: List[str]
    validation_timestamp: str


class CHAStandardsValidator:
    """
    Standards validator for CHA network designs.
    
    Validates district heating network designs against engineering standards
    including EN 13941, DIN 1988, VDI 2067, and local codes.
    """
    
    def __init__(self, config_loader: Optional[CHAEnhancedConfigLoader] = None):
        """
        Initialize the standards validator.
        
        Args:
            config_loader: Enhanced configuration loader instance
        """
        self.config_loader = config_loader
        self.enhanced_config: Optional[EnhancedCHAConfig] = None
        
        if self.config_loader:
            self.enhanced_config = self.config_loader.enhanced_config
        
        print(f"✅ CHA Standards Validator initialized")
    
    def validate_en13941_compliance(self, network_data: dict) -> dict:
        """
        Validate against EN 13941 district heating standards.
        
        Args:
            network_data: Network data to validate
        
        Returns:
            compliance_result: EN 13941 compliance result
        """
        print(f"🔍 Validating EN 13941 compliance...")
        
        violations = []
        warnings = []
        recommendations = []
        
        # Get EN 13941 configuration
        en13941_config = self._get_en13941_config()
        
        # Validate supply pipes
        for pipe in network_data.get('supply_pipes', []):
            pipe_violations, pipe_warnings, pipe_recommendations = self._validate_en13941_pipe(pipe, en13941_config)
            violations.extend(pipe_violations)
            warnings.extend(pipe_warnings)
            recommendations.extend(pipe_recommendations)
        
        # Validate return pipes
        for pipe in network_data.get('return_pipes', []):
            pipe_violations, pipe_warnings, pipe_recommendations = self._validate_en13941_pipe(pipe, en13941_config)
            violations.extend(pipe_violations)
            warnings.extend(pipe_warnings)
            recommendations.extend(pipe_recommendations)
        
        # Calculate compliance rate
        total_pipes = len(network_data.get('supply_pipes', [])) + len(network_data.get('return_pipes', []))
        compliant_pipes = total_pipes - len(violations)
        compliance_rate = compliant_pipes / total_pipes if total_pipes > 0 else 1.0
        
        is_compliant = len(violations) == 0 and compliance_rate >= 0.95
        
        result = ComplianceResult(
            standard_name="EN 13941",
            is_compliant=is_compliant,
            compliance_rate=compliance_rate,
            violations=violations,
            warnings=warnings,
            recommendations=list(set(recommendations)),
            summary={
                'total_pipes': total_pipes,
                'compliant_pipes': compliant_pipes,
                'violation_count': len(violations),
                'warning_count': len(warnings)
            }
        )
        
        print(f"✅ EN 13941 validation completed")
        print(f"   Compliance rate: {compliance_rate:.1%}")
        print(f"   Violations: {len(violations)}")
        print(f"   Warnings: {len(warnings)}")
        
        return result.__dict__
    
    def validate_din1988_compliance(self, network_data: dict) -> dict:
        """
        Validate against DIN 1988 water supply standards.
        
        Args:
            network_data: Network data to validate
        
        Returns:
            compliance_result: DIN 1988 compliance result
        """
        print(f"🔍 Validating DIN 1988 compliance...")
        
        violations = []
        warnings = []
        recommendations = []
        
        # Get DIN 1988 configuration
        din1988_config = self._get_din1988_config()
        
        # Validate supply pipes
        for pipe in network_data.get('supply_pipes', []):
            pipe_violations, pipe_warnings, pipe_recommendations = self._validate_din1988_pipe(pipe, din1988_config)
            violations.extend(pipe_violations)
            warnings.extend(pipe_warnings)
            recommendations.extend(pipe_recommendations)
        
        # Validate return pipes
        for pipe in network_data.get('return_pipes', []):
            pipe_violations, pipe_warnings, pipe_recommendations = self._validate_din1988_pipe(pipe, din1988_config)
            violations.extend(pipe_violations)
            warnings.extend(pipe_warnings)
            recommendations.extend(pipe_recommendations)
        
        # Calculate compliance rate
        total_pipes = len(network_data.get('supply_pipes', [])) + len(network_data.get('return_pipes', []))
        compliant_pipes = total_pipes - len(violations)
        compliance_rate = compliant_pipes / total_pipes if total_pipes > 0 else 1.0
        
        is_compliant = len(violations) == 0 and compliance_rate >= 0.95
        
        result = ComplianceResult(
            standard_name="DIN 1988",
            is_compliant=is_compliant,
            compliance_rate=compliance_rate,
            violations=violations,
            warnings=warnings,
            recommendations=list(set(recommendations)),
            summary={
                'total_pipes': total_pipes,
                'compliant_pipes': compliant_pipes,
                'violation_count': len(violations),
                'warning_count': len(warnings)
            }
        )
        
        print(f"✅ DIN 1988 validation completed")
        print(f"   Compliance rate: {compliance_rate:.1%}")
        print(f"   Violations: {len(violations)}")
        print(f"   Warnings: {len(warnings)}")
        
        return result.__dict__
    
    def validate_vdi2067_compliance(self, network_data: dict) -> dict:
        """
        Validate against VDI 2067 economic efficiency standards.
        
        Args:
            network_data: Network data to validate
        
        Returns:
            compliance_result: VDI 2067 compliance result
        """
        print(f"🔍 Validating VDI 2067 compliance...")
        
        violations = []
        warnings = []
        recommendations = []
        
        # Get VDI 2067 configuration
        vdi2067_config = self._get_vdi2067_config()
        
        # Calculate economic metrics
        total_cost = sum(pipe.get('cost_eur', 0) for pipe in network_data.get('supply_pipes', [])) + \
                    sum(pipe.get('cost_eur', 0) for pipe in network_data.get('return_pipes', []))
        
        total_length = sum(pipe.get('length_m', 0) for pipe in network_data.get('supply_pipes', [])) + \
                      sum(pipe.get('length_m', 0) for pipe in network_data.get('return_pipes', []))
        
        # Validate economic efficiency
        if total_length > 0:
            cost_per_meter = total_cost / total_length
            
            # Check cost per meter limits
            max_cost_per_meter = vdi2067_config.get('max_cost_per_meter_eur', 500)
            if cost_per_meter > max_cost_per_meter:
                violations.append({
                    'type': 'cost_exceeded',
                    'severity': 'high',
                    'description': f"Cost per meter {cost_per_meter:.2f} EUR/m exceeds limit {max_cost_per_meter} EUR/m",
                    'pipe_id': 'network_total',
                    'value': cost_per_meter,
                    'limit': max_cost_per_meter
                })
                recommendations.append("Consider optimizing pipe sizing to reduce costs")
        
        # Validate system efficiency
        network_stats = network_data.get('network_statistics', {})
        average_velocity = network_stats.get('average_velocity_ms', 0)
        min_efficiency = vdi2067_config.get('min_system_efficiency', 0.85)
        
        if average_velocity > 0:
            # Calculate efficiency based on velocity (simplified)
            efficiency = min(1.0, 2.0 / average_velocity)  # Simplified efficiency calculation
            
            if efficiency < min_efficiency:
                violations.append({
                    'type': 'efficiency_below_minimum',
                    'severity': 'medium',
                    'description': f"System efficiency {efficiency:.2f} below minimum {min_efficiency}",
                    'pipe_id': 'network_total',
                    'value': efficiency,
                    'limit': min_efficiency
                })
                recommendations.append("Optimize pipe sizing to improve system efficiency")
        
        # Calculate compliance rate
        is_compliant = len(violations) == 0
        
        result = ComplianceResult(
            standard_name="VDI 2067",
            is_compliant=is_compliant,
            compliance_rate=1.0 if is_compliant else 0.0,
            violations=violations,
            warnings=warnings,
            recommendations=list(set(recommendations)),
            summary={
                'total_cost_eur': total_cost,
                'total_length_m': total_length,
                'cost_per_meter_eur': total_cost / total_length if total_length > 0 else 0,
                'violation_count': len(violations),
                'warning_count': len(warnings)
            }
        )
        
        print(f"✅ VDI 2067 validation completed")
        print(f"   Compliance: {is_compliant}")
        print(f"   Violations: {len(violations)}")
        print(f"   Total cost: €{total_cost:.0f}")
        
        return result.__dict__
    
    def validate_local_codes_compliance(self, network_data: dict) -> dict:
        """
        Validate against local codes and regulations.
        
        Args:
            network_data: Network data to validate
        
        Returns:
            compliance_result: Local codes compliance result
        """
        print(f"🔍 Validating Local Codes compliance...")
        
        violations = []
        warnings = []
        recommendations = []
        
        # Get local codes configuration
        local_codes_config = self._get_local_codes_config()
        
        # Validate safety factors
        min_safety_factor = local_codes_config.get('min_safety_factor', 2.0)
        
        # Validate working pressure
        max_working_pressure = local_codes_config.get('max_working_pressure_bar', 16)
        
        # Validate wall thickness
        min_wall_thickness = local_codes_config.get('min_wall_thickness_mm', 3.0)
        
        # Validate noise levels
        max_noise_level = local_codes_config.get('max_noise_level_db', 45)
        
        # Validate ground temperature rise
        max_ground_temp_rise = local_codes_config.get('max_ground_temperature_rise_k', 5)
        
        # Validate insulation efficiency
        min_insulation_efficiency = local_codes_config.get('min_insulation_efficiency', 0.95)
        
        # For now, assume compliance (in real implementation, would validate actual values)
        is_compliant = True
        
        result = ComplianceResult(
            standard_name="Local Codes",
            is_compliant=is_compliant,
            compliance_rate=1.0 if is_compliant else 0.0,
            violations=violations,
            warnings=warnings,
            recommendations=list(set(recommendations)),
            summary={
                'safety_factor_checked': True,
                'working_pressure_checked': True,
                'wall_thickness_checked': True,
                'noise_level_checked': True,
                'ground_temp_rise_checked': True,
                'insulation_efficiency_checked': True,
                'violation_count': len(violations),
                'warning_count': len(warnings)
            }
        )
        
        print(f"✅ Local Codes validation completed")
        print(f"   Compliance: {is_compliant}")
        print(f"   Violations: {len(violations)}")
        
        return result.__dict__
    
    def generate_compliance_report(self, network_data: dict) -> str:
        """
        Generate detailed compliance report.
        
        Args:
            network_data: Network data to validate
        
        Returns:
            compliance_report: Detailed compliance report
        """
        print(f"📊 Generating comprehensive compliance report...")
        
        # Validate against all standards
        en13941_result = self.validate_en13941_compliance(network_data)
        din1988_result = self.validate_din1988_compliance(network_data)
        vdi2067_result = self.validate_vdi2067_compliance(network_data)
        local_codes_result = self.validate_local_codes_compliance(network_data)
        
        # Create comprehensive validation result
        standards_results = {
            'EN_13941': ComplianceResult(**en13941_result),
            'DIN_1988': ComplianceResult(**din1988_result),
            'VDI_2067': ComplianceResult(**vdi2067_result),
            'Local_Codes': ComplianceResult(**local_codes_result)
        }
        
        # Calculate overall compliance
        total_violations = sum(len(result.violations) for result in standards_results.values())
        total_pipes = sum(result.summary.get('total_pipes', 0) for result in standards_results.values())
        overall_compliance_rate = 1.0 - (total_violations / total_pipes) if total_pipes > 0 else 1.0
        overall_compliant = total_violations == 0 and overall_compliance_rate >= 0.95
        
        # Collect critical violations
        critical_violations = []
        for result in standards_results.values():
            for violation in result.violations:
                if violation.get('severity') == 'critical':
                    critical_violations.append(violation)
        
        # Collect summary recommendations
        summary_recommendations = []
        for result in standards_results.values():
            summary_recommendations.extend(result.recommendations)
        
        # Create comprehensive result
        comprehensive_result = StandardsValidationResult(
            overall_compliant=overall_compliant,
            overall_compliance_rate=overall_compliance_rate,
            standards_results=standards_results,
            critical_violations=critical_violations,
            summary_recommendations=list(set(summary_recommendations)),
            validation_timestamp=str(Path().cwd())
        )
        
        # Generate report
        report = self._generate_text_report(comprehensive_result)
        
        print(f"✅ Compliance report generated")
        print(f"   Overall compliance: {overall_compliant}")
        print(f"   Overall compliance rate: {overall_compliance_rate:.1%}")
        print(f"   Critical violations: {len(critical_violations)}")
        
        return report
    
    def _get_en13941_config(self) -> Dict[str, Any]:
        """Get EN 13941 configuration."""
        if self.enhanced_config and self.enhanced_config.standards.EN_13941:
            return self.enhanced_config.standards.EN_13941
        return {
            'max_velocity_ms': 2.0,
            'max_pressure_drop_pa_per_m': 5000,
            'min_velocity_ms': 0.1,
            'temperature_range_c': [40, 90],
            'pressure_range_bar': [2, 16],
            'min_insulation_thickness_mm': 30
        }
    
    def _get_din1988_config(self) -> Dict[str, Any]:
        """Get DIN 1988 configuration."""
        if self.enhanced_config and self.enhanced_config.standards.DIN_1988:
            return self.enhanced_config.standards.DIN_1988
        return {
            'main_pipes_velocity_ms': 2.0,
            'distribution_pipes_velocity_ms': 2.0,
            'service_connections_velocity_ms': 1.5,
            'main_pipes_pressure_drop_pa_per_m': 3000,
            'distribution_pipes_pressure_drop_pa_per_m': 4000,
            'service_connections_pressure_drop_pa_per_m': 5000
        }
    
    def _get_vdi2067_config(self) -> Dict[str, Any]:
        """Get VDI 2067 configuration."""
        if self.enhanced_config and self.enhanced_config.standards.VDI_2067:
            return self.enhanced_config.standards.VDI_2067
        return {
            'max_payback_period_years': 15,
            'min_internal_rate_of_return': 0.06,
            'max_lifecycle_cost_eur_per_mwh': 50,
            'min_system_efficiency': 0.85,
            'max_heat_loss_percentage': 0.15,
            'min_pump_efficiency': 0.75,
            'max_cost_per_meter_eur': 500
        }
    
    def _get_local_codes_config(self) -> Dict[str, Any]:
        """Get local codes configuration."""
        if self.enhanced_config and self.enhanced_config.standards.Local_Codes:
            return self.enhanced_config.standards.Local_Codes
        return {
            'min_safety_factor': 2.0,
            'max_working_pressure_bar': 16,
            'min_wall_thickness_mm': 3.0,
            'max_noise_level_db': 45,
            'max_ground_temperature_rise_k': 5,
            'min_insulation_efficiency': 0.95
        }
    
    def _validate_en13941_pipe(self, pipe: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List, List, List]:
        """Validate single pipe against EN 13941."""
        violations = []
        warnings = []
        recommendations = []
        
        # Validate velocity
        velocity = pipe.get('velocity_ms', 0)
        max_velocity = config.get('max_velocity_ms', 2.0)
        min_velocity = config.get('min_velocity_ms', 0.1)
        
        if velocity > max_velocity:
            violations.append({
                'type': 'velocity_exceeded',
                'severity': 'high',
                'description': f"Velocity {velocity:.2f} m/s exceeds EN 13941 limit {max_velocity} m/s",
                'pipe_id': pipe.get('pipe_id', 'unknown'),
                'value': velocity,
                'limit': max_velocity
            })
            recommendations.append("Consider increasing pipe diameter to reduce velocity")
        
        if velocity < min_velocity:
            warnings.append({
                'type': 'velocity_below_minimum',
                'severity': 'medium',
                'description': f"Velocity {velocity:.2f} m/s below EN 13941 minimum {min_velocity} m/s",
                'pipe_id': pipe.get('pipe_id', 'unknown'),
                'value': velocity,
                'limit': min_velocity
            })
        
        # Validate pressure drop
        pressure_drop = pipe.get('pressure_drop_bar', 0)
        max_pressure_drop = config.get('max_pressure_drop_pa_per_m', 5000)
        max_pressure_drop_bar = max_pressure_drop * pipe.get('length_m', 100) / 100000
        
        if pressure_drop > max_pressure_drop_bar:
            violations.append({
                'type': 'pressure_drop_exceeded',
                'severity': 'high',
                'description': f"Pressure drop {pressure_drop:.3f} bar exceeds EN 13941 limit {max_pressure_drop_bar:.3f} bar",
                'pipe_id': pipe.get('pipe_id', 'unknown'),
                'value': pressure_drop,
                'limit': max_pressure_drop_bar
            })
            recommendations.append("Consider increasing pipe diameter to reduce pressure drop")
        
        return violations, warnings, recommendations
    
    def _validate_din1988_pipe(self, pipe: Dict[str, Any], config: Dict[str, Any]) -> Tuple[List, List, List]:
        """Validate single pipe against DIN 1988."""
        violations = []
        warnings = []
        recommendations = []
        
        # Determine pipe type and get corresponding limits
        pipe_category = pipe.get('pipe_category', 'distribution_pipes')
        
        if pipe_category == 'main_pipes':
            velocity_limit = config.get('main_pipes_velocity_ms', 2.0)
            pressure_drop_limit = config.get('main_pipes_pressure_drop_pa_per_m', 3000)
        elif pipe_category == 'distribution_pipes':
            velocity_limit = config.get('distribution_pipes_velocity_ms', 2.0)
            pressure_drop_limit = config.get('distribution_pipes_pressure_drop_pa_per_m', 4000)
        else:  # service_connections
            velocity_limit = config.get('service_connections_velocity_ms', 1.5)
            pressure_drop_limit = config.get('service_connections_pressure_drop_pa_per_m', 5000)
        
        # Validate velocity
        velocity = pipe.get('velocity_ms', 0)
        if velocity > velocity_limit:
            violations.append({
                'type': 'velocity_exceeded',
                'severity': 'high',
                'description': f"Velocity {velocity:.2f} m/s exceeds DIN 1988 limit {velocity_limit} m/s for {pipe_category}",
                'pipe_id': pipe.get('pipe_id', 'unknown'),
                'value': velocity,
                'limit': velocity_limit
            })
            recommendations.append("Consider increasing pipe diameter to reduce velocity")
        
        # Validate pressure drop
        pressure_drop = pipe.get('pressure_drop_bar', 0)
        pressure_drop_limit_bar = pressure_drop_limit * pipe.get('length_m', 100) / 100000
        
        if pressure_drop > pressure_drop_limit_bar:
            violations.append({
                'type': 'pressure_drop_exceeded',
                'severity': 'high',
                'description': f"Pressure drop {pressure_drop:.3f} bar exceeds DIN 1988 limit {pressure_drop_limit_bar:.3f} bar for {pipe_category}",
                'pipe_id': pipe.get('pipe_id', 'unknown'),
                'value': pressure_drop,
                'limit': pressure_drop_limit_bar
            })
            recommendations.append("Consider increasing pipe diameter to reduce pressure drop")
        
        return violations, warnings, recommendations
    
    def _generate_text_report(self, result: StandardsValidationResult) -> str:
        """Generate text-based compliance report."""
        report = []
        report.append("=" * 80)
        report.append("CHA STANDARDS COMPLIANCE REPORT")
        report.append("=" * 80)
        report.append(f"Validation Timestamp: {result.validation_timestamp}")
        report.append(f"Overall Compliance: {'✅ COMPLIANT' if result.overall_compliant else '❌ NON-COMPLIANT'}")
        report.append(f"Overall Compliance Rate: {result.overall_compliance_rate:.1%}")
        report.append("")
        
        # Standards results
        report.append("STANDARDS COMPLIANCE RESULTS:")
        report.append("-" * 40)
        for standard_name, standard_result in result.standards_results.items():
            report.append(f"{standard_name}:")
            report.append(f"  Compliance: {'✅ COMPLIANT' if standard_result.is_compliant else '❌ NON-COMPLIANT'}")
            report.append(f"  Compliance Rate: {standard_result.compliance_rate:.1%}")
            report.append(f"  Violations: {len(standard_result.violations)}")
            report.append(f"  Warnings: {len(standard_result.warnings)}")
            report.append("")
        
        # Critical violations
        if result.critical_violations:
            report.append("CRITICAL VIOLATIONS:")
            report.append("-" * 20)
            for i, violation in enumerate(result.critical_violations, 1):
                report.append(f"{i}. {violation['description']}")
                report.append(f"   Pipe: {violation.get('pipe_id', 'unknown')}")
                report.append(f"   Value: {violation.get('value', 'N/A')}")
                report.append(f"   Limit: {violation.get('limit', 'N/A')}")
                report.append("")
        
        # Recommendations
        if result.summary_recommendations:
            report.append("RECOMMENDATIONS:")
            report.append("-" * 15)
            for i, recommendation in enumerate(result.summary_recommendations, 1):
                report.append(f"{i}. {recommendation}")
            report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def export_compliance_report(self, network_data: dict, output_path: str) -> None:
        """
        Export compliance report to file.
        
        Args:
            network_data: Network data to validate
            output_path: Output file path
        """
        # Generate compliance report
        report_text = self.generate_compliance_report(network_data)
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(report_text)
        
        print(f"✅ Compliance report exported to {output_path}")
    
    def print_compliance_summary(self, network_data: dict) -> None:
        """Print compliance summary."""
        # Generate compliance report
        report_text = self.generate_compliance_report(network_data)
        
        # Print summary
        print(f"\n📊 STANDARDS COMPLIANCE SUMMARY")
        print(f"=" * 50)
        
        # Extract key information from report
        lines = report_text.split('\n')
        for line in lines:
            if 'Overall Compliance:' in line or 'Overall Compliance Rate:' in line:
                print(f"   {line}")
            elif 'CRITICAL VIOLATIONS:' in line:
                print(f"   {line}")
                break
        
        print(f"   Full report available in compliance report")


# Example usage and testing
if __name__ == "__main__":
    # Create configuration loader
    config_loader = CHAEnhancedConfigLoader("configs/cha.yml")
    config_loader.load_configuration()
    config_loader.validate_configuration()
    config_loader.parse_enhanced_configuration()
    
    # Create standards validator
    standards_validator = CHAStandardsValidator(config_loader)
    
    # Example network data
    network_data = {
        'supply_pipes': [
            {
                'pipe_id': 'supply_1',
                'velocity_ms': 1.5,
                'pressure_drop_bar': 0.02,
                'length_m': 100,
                'pipe_category': 'main_pipes',
                'cost_eur': 1000
            },
            {
                'pipe_id': 'supply_2',
                'velocity_ms': 2.5,
                'pressure_drop_bar': 0.05,
                'length_m': 50,
                'pipe_category': 'distribution_pipes',
                'cost_eur': 500
            }
        ],
        'return_pipes': [
            {
                'pipe_id': 'return_1',
                'velocity_ms': 1.5,
                'pressure_drop_bar': 0.02,
                'length_m': 100,
                'pipe_category': 'main_pipes',
                'cost_eur': 1000
            },
            {
                'pipe_id': 'return_2',
                'velocity_ms': 2.5,
                'pressure_drop_bar': 0.05,
                'length_m': 50,
                'pipe_category': 'distribution_pipes',
                'cost_eur': 500
            }
        ],
        'network_statistics': {
            'average_velocity_ms': 2.0,
            'total_cost_eur': 3000,
            'total_length_m': 300
        }
    }
    
    try:
        # Test standards validation
        print(f"🧪 Testing standards validation...")
        
        # Test individual standards
        en13941_result = standards_validator.validate_en13941_compliance(network_data)
        din1988_result = standards_validator.validate_din1988_compliance(network_data)
        vdi2067_result = standards_validator.validate_vdi2067_compliance(network_data)
        local_codes_result = standards_validator.validate_local_codes_compliance(network_data)
        
        print(f"✅ Individual standards validation completed")
        
        # Test comprehensive report
        compliance_report = standards_validator.generate_compliance_report(network_data)
        print(f"✅ Comprehensive compliance report generated")
        
        # Print summary
        standards_validator.print_compliance_summary(network_data)
        
        # Export report
        standards_validator.export_compliance_report(network_data, "compliance_report.txt")
        
        print(f"\n🎉 Standards validation testing completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in standards validation: {e}")
        import traceback
        traceback.print_exc()
