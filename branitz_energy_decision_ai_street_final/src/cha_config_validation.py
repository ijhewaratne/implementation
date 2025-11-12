"""
CHA Configuration Validation - Enhanced Configuration Validation

This module validates the enhanced CHA configuration to ensure all pipe sizing
parameters are properly configured and within acceptable ranges.

Author: Branitz Energy Decision AI
Version: 1.0.0
"""

from __future__ import annotations
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass
import warnings

warnings.filterwarnings("ignore")


@dataclass
class ValidationResult:
    """Configuration validation result."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]


@dataclass
class ConfigurationSummary:
    """Configuration summary."""
    pipe_sizing_enabled: bool
    standard_diameters_count: int
    pipe_types_configured: List[str]
    standards_enabled: List[str]
    hierarchy_levels: int
    cost_model_diameters: int
    validation_enabled: bool


class CHAConfigValidator:
    """
    Configuration validator for enhanced CHA configuration.
    
    Validates pipe sizing parameters, engineering standards, and configuration
    consistency to ensure proper system operation.
    """
    
    def __init__(self, config_path: str = "configs/cha.yml"):
        """
        Initialize the configuration validator.
        
        Args:
            config_path: Path to CHA configuration file
        """
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.pipe_sizing_config: Dict[str, Any] = {}
        
        print(f"✅ CHA Configuration Validator initialized")
        print(f"   Configuration file: {config_path}")
    
    def load_configuration(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            success: True if loading successful
        """
        try:
            with open(self.config_path, 'r') as f:
                self.config = yaml.safe_load(f)
            
            self.pipe_sizing_config = self.config.get('pipe_sizing', {})
            
            print(f"✅ Configuration loaded successfully")
            return True
            
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_path}")
            return False
        except yaml.YAMLError as e:
            print(f"❌ YAML parsing error: {e}")
            return False
        except Exception as e:
            print(f"❌ Error loading configuration: {e}")
            return False
    
    def validate_pipe_sizing_configuration(self) -> ValidationResult:
        """
        Validate pipe sizing configuration.
        
        Returns:
            ValidationResult: Validation result with errors and warnings
        """
        errors = []
        warnings = []
        recommendations = []
        
        if not self.pipe_sizing_config:
            errors.append("Pipe sizing configuration section is missing")
            return ValidationResult(False, errors, warnings, recommendations)
        
        # Validate basic parameters
        self._validate_basic_parameters(errors, warnings, recommendations)
        
        # Validate standard diameters
        self._validate_standard_diameters(errors, warnings, recommendations)
        
        # Validate hydraulic constraints
        self._validate_hydraulic_constraints(errors, warnings, recommendations)
        
        # Validate pipe type configurations
        self._validate_pipe_type_configurations(errors, warnings, recommendations)
        
        # Validate cost model
        self._validate_cost_model(errors, warnings, recommendations)
        
        # Validate engineering standards
        self._validate_engineering_standards(errors, warnings, recommendations)
        
        # Validate hierarchy levels
        self._validate_hierarchy_levels(errors, warnings, recommendations)
        
        # Validate validation settings
        self._validate_validation_settings(errors, warnings, recommendations)
        
        is_valid = len(errors) == 0
        
        return ValidationResult(is_valid, errors, warnings, recommendations)
    
    def _validate_basic_parameters(self, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate basic pipe sizing parameters."""
        # Check if intelligent sizing is enabled
        if not self.pipe_sizing_config.get('enable_intelligent_sizing', False):
            warnings.append("Intelligent pipe sizing is disabled - using default diameters")
        
        # Validate water properties
        water_density = self.pipe_sizing_config.get('water_density_kg_m3', 977.8)
        if not (900 <= water_density <= 1000):
            errors.append(f"Water density {water_density} kg/m³ is outside acceptable range (900-1000)")
        
        water_specific_heat = self.pipe_sizing_config.get('water_specific_heat_j_per_kgk', 4180)
        if not (4000 <= water_specific_heat <= 4200):
            warnings.append(f"Water specific heat {water_specific_heat} J/kg·K is outside typical range (4000-4200)")
        
        # Validate safety factors
        safety_factor = self.pipe_sizing_config.get('safety_factor', 1.1)
        if not (1.0 <= safety_factor <= 2.0):
            errors.append(f"Safety factor {safety_factor} is outside acceptable range (1.0-2.0)")
        
        diversity_factor = self.pipe_sizing_config.get('diversity_factor', 0.8)
        if not (0.5 <= diversity_factor <= 1.0):
            errors.append(f"Diversity factor {diversity_factor} is outside acceptable range (0.5-1.0)")
    
    def _validate_standard_diameters(self, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate standard pipe diameters."""
        standard_diameters = self.pipe_sizing_config.get('standard_diameters', [])
        
        if not standard_diameters:
            errors.append("Standard diameters list is empty")
            return
        
        if len(standard_diameters) < 5:
            warnings.append(f"Only {len(standard_diameters)} standard diameters defined - consider adding more")
        
        # Check diameter range
        min_diameter = min(standard_diameters)
        max_diameter = max(standard_diameters)
        
        if min_diameter < 25:
            warnings.append(f"Minimum diameter {min_diameter} mm is very small - consider minimum 25mm")
        
        if max_diameter > 500:
            warnings.append(f"Maximum diameter {max_diameter} mm is very large - consider maximum 500mm")
        
        # Check for gaps in diameter series
        sorted_diameters = sorted(standard_diameters)
        gaps = []
        for i in range(len(sorted_diameters) - 1):
            ratio = sorted_diameters[i + 1] / sorted_diameters[i]
            if ratio > 1.6:  # More than 60% increase
                gaps.append(f"Large gap between {sorted_diameters[i]}mm and {sorted_diameters[i + 1]}mm")
        
        if gaps:
            recommendations.extend(gaps)
    
    def _validate_hydraulic_constraints(self, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate hydraulic constraints."""
        max_velocity = self.pipe_sizing_config.get('max_velocity_ms', 3.0)
        min_velocity = self.pipe_sizing_config.get('min_velocity_ms', 0.5)
        max_pressure_drop = self.pipe_sizing_config.get('max_pressure_drop_pa_per_m', 50)
        
        # Validate velocity constraints
        if max_velocity < 1.0:
            warnings.append(f"Maximum velocity {max_velocity} m/s is very low - consider minimum 1.0 m/s")
        elif max_velocity > 5.0:
            warnings.append(f"Maximum velocity {max_velocity} m/s is very high - consider maximum 5.0 m/s")
        
        if min_velocity < 0.1:
            warnings.append(f"Minimum velocity {min_velocity} m/s is very low - consider minimum 0.1 m/s")
        
        if max_velocity <= min_velocity:
            errors.append(f"Maximum velocity {max_velocity} m/s must be greater than minimum velocity {min_velocity} m/s")
        
        # Validate pressure drop constraints
        if max_pressure_drop < 100:
            warnings.append(f"Maximum pressure drop {max_pressure_drop} Pa/m is very low - consider minimum 100 Pa/m")
        elif max_pressure_drop > 10000:
            warnings.append(f"Maximum pressure drop {max_pressure_drop} Pa/m is very high - consider maximum 10000 Pa/m")
    
    def _validate_pipe_type_configurations(self, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate pipe type configurations."""
        pipe_types = ['main_pipes', 'distribution_pipes', 'service_connections']
        
        for pipe_type in pipe_types:
            config = self.pipe_sizing_config.get(pipe_type, {})
            
            if not config:
                errors.append(f"Configuration for {pipe_type} is missing")
                continue
            
            # Validate diameter ranges
            min_diameter = config.get('min_diameter_mm', 0)
            max_diameter = config.get('max_diameter_mm', 0)
            
            if min_diameter <= 0:
                errors.append(f"Minimum diameter for {pipe_type} must be positive")
            
            if max_diameter <= 0:
                errors.append(f"Maximum diameter for {pipe_type} must be positive")
            
            if min_diameter >= max_diameter:
                errors.append(f"Minimum diameter {min_diameter}mm must be less than maximum diameter {max_diameter}mm for {pipe_type}")
            
            # Validate flow thresholds
            flow_threshold = config.get('flow_threshold_kg_s', 0)
            if flow_threshold < 0:
                errors.append(f"Flow threshold for {pipe_type} must be non-negative")
            
            # Validate velocity limits
            velocity_limit = config.get('velocity_limit_ms', 0)
            if velocity_limit <= 0:
                errors.append(f"Velocity limit for {pipe_type} must be positive")
            elif velocity_limit > 5.0:
                warnings.append(f"Velocity limit {velocity_limit} m/s for {pipe_type} is very high")
            
            # Validate pressure drop limits
            pressure_drop_limit = config.get('pressure_drop_limit_pa_per_m', 0)
            if pressure_drop_limit <= 0:
                errors.append(f"Pressure drop limit for {pipe_type} must be positive")
            elif pressure_drop_limit > 10000:
                warnings.append(f"Pressure drop limit {pressure_drop_limit} Pa/m for {pipe_type} is very high")
    
    def _validate_cost_model(self, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate cost model configuration."""
        cost_per_meter = self.pipe_sizing_config.get('cost_per_meter', {})
        
        if not cost_per_meter:
            errors.append("Cost model is missing")
            return
        
        if len(cost_per_meter) < 3:
            warnings.append(f"Only {len(cost_per_meter)} cost entries defined - consider adding more")
        
        # Validate cost values
        for diameter, cost in cost_per_meter.items():
            if cost <= 0:
                errors.append(f"Cost for diameter {diameter}mm must be positive")
            elif cost > 1000:
                warnings.append(f"Cost {cost} EUR/m for diameter {diameter}mm seems very high")
        
        # Check cost progression
        sorted_costs = sorted(cost_per_meter.items())
        for i in range(len(sorted_costs) - 1):
            diameter1, cost1 = sorted_costs[i]
            diameter2, cost2 = sorted_costs[i + 1]
            
            if cost2 < cost1:
                warnings.append(f"Cost decreases from {diameter1}mm ({cost1} EUR/m) to {diameter2}mm ({cost2} EUR/m)")
    
    def _validate_engineering_standards(self, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate engineering standards configuration."""
        standards = self.pipe_sizing_config.get('standards', {})
        
        if not standards:
            warnings.append("No engineering standards configured")
            return
        
        enabled_standards = []
        for standard_name, standard_config in standards.items():
            if standard_config.get('enabled', False):
                enabled_standards.append(standard_name)
        
        if not enabled_standards:
            warnings.append("No engineering standards are enabled")
        
        # Validate specific standards
        if 'EN_13941' in standards and standards['EN_13941'].get('enabled', False):
            self._validate_en_13941_standard(standards['EN_13941'], errors, warnings, recommendations)
        
        if 'DIN_1988' in standards and standards['DIN_1988'].get('enabled', False):
            self._validate_din_1988_standard(standards['DIN_1988'], errors, warnings, recommendations)
    
    def _validate_en_13941_standard(self, config: Dict, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate EN 13941 standard configuration."""
        max_velocity = config.get('max_velocity_ms', 2.0)
        if max_velocity > 3.0:
            warnings.append(f"EN 13941 maximum velocity {max_velocity} m/s exceeds typical limit of 3.0 m/s")
        
        max_pressure_drop = config.get('max_pressure_drop_pa_per_m', 5000)
        if max_pressure_drop > 10000:
            warnings.append(f"EN 13941 maximum pressure drop {max_pressure_drop} Pa/m exceeds typical limit of 10000 Pa/m")
    
    def _validate_din_1988_standard(self, config: Dict, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate DIN 1988 standard configuration."""
        # Validate velocity limits for different pipe types
        for pipe_type in ['main_pipes', 'distribution_pipes', 'service_connections']:
            velocity_key = f"{pipe_type}_velocity_ms"
            velocity = config.get(velocity_key, 0)
            
            if velocity <= 0:
                errors.append(f"DIN 1988 {velocity_key} must be positive")
            elif velocity > 3.0:
                warnings.append(f"DIN 1988 {velocity_key} {velocity} m/s exceeds typical limit of 3.0 m/s")
    
    def _validate_hierarchy_levels(self, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate hierarchy levels configuration."""
        hierarchy_levels = self.pipe_sizing_config.get('hierarchy_levels', {})
        
        if not hierarchy_levels:
            warnings.append("No hierarchy levels configured")
            return
        
        if len(hierarchy_levels) < 3:
            warnings.append(f"Only {len(hierarchy_levels)} hierarchy levels defined - consider minimum 3")
        
        # Validate hierarchy level configurations
        for level, config in hierarchy_levels.items():
            min_flow = config.get('min_flow_kg_s', 0)
            max_flow = config.get('max_flow_kg_s', 0)
            
            if min_flow < 0:
                errors.append(f"Hierarchy level {level} minimum flow must be non-negative")
            
            if max_flow <= min_flow:
                errors.append(f"Hierarchy level {level} maximum flow must be greater than minimum flow")
    
    def _validate_validation_settings(self, errors: List[str], warnings: List[str], recommendations: List[str]) -> None:
        """Validate validation settings."""
        validation = self.pipe_sizing_config.get('validation', {})
        
        if not validation.get('enable_validation', True):
            warnings.append("Validation is disabled - consider enabling for quality assurance")
        
        compliance_threshold = validation.get('compliance_threshold', 0.95)
        if not (0.0 <= compliance_threshold <= 1.0):
            errors.append(f"Compliance threshold {compliance_threshold} must be between 0.0 and 1.0")
        
        if compliance_threshold < 0.8:
            warnings.append(f"Compliance threshold {compliance_threshold} is very low - consider minimum 0.8")
    
    def generate_configuration_summary(self) -> ConfigurationSummary:
        """Generate configuration summary."""
        pipe_sizing_enabled = self.pipe_sizing_config.get('enable_intelligent_sizing', False)
        standard_diameters_count = len(self.pipe_sizing_config.get('standard_diameters', []))
        
        pipe_types_configured = []
        for pipe_type in ['main_pipes', 'distribution_pipes', 'service_connections']:
            if pipe_type in self.pipe_sizing_config:
                pipe_types_configured.append(pipe_type)
        
        standards_enabled = []
        standards = self.pipe_sizing_config.get('standards', {})
        for standard_name, standard_config in standards.items():
            if standard_config.get('enabled', False):
                standards_enabled.append(standard_name)
        
        hierarchy_levels = len(self.pipe_sizing_config.get('hierarchy_levels', {}))
        cost_model_diameters = len(self.pipe_sizing_config.get('cost_per_meter', {}))
        validation_enabled = self.pipe_sizing_config.get('validation', {}).get('enable_validation', True)
        
        return ConfigurationSummary(
            pipe_sizing_enabled=pipe_sizing_enabled,
            standard_diameters_count=standard_diameters_count,
            pipe_types_configured=pipe_types_configured,
            standards_enabled=standards_enabled,
            hierarchy_levels=hierarchy_levels,
            cost_model_diameters=cost_model_diameters,
            validation_enabled=validation_enabled
        )
    
    def export_validation_report(self, validation_result: ValidationResult, output_path: str) -> None:
        """
        Export validation report to JSON file.
        
        Args:
            validation_result: Validation result
            output_path: Output file path
        """
        report = {
            'configuration_file': self.config_path,
            'validation_timestamp': str(Path().cwd()),
            'is_valid': validation_result.is_valid,
            'errors': validation_result.errors,
            'warnings': validation_result.warnings,
            'recommendations': validation_result.recommendations,
            'summary': self.generate_configuration_summary().__dict__
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"✅ Validation report exported to {output_path}")
    
    def print_validation_summary(self, validation_result: ValidationResult) -> None:
        """Print validation summary."""
        summary = self.generate_configuration_summary()
        
        print(f"\n📊 CONFIGURATION VALIDATION SUMMARY")
        print(f"=" * 50)
        print(f"📁 Configuration File: {self.config_path}")
        print(f"✅ Valid: {validation_result.is_valid}")
        print(f"❌ Errors: {len(validation_result.errors)}")
        print(f"⚠️ Warnings: {len(validation_result.warnings)}")
        print(f"💡 Recommendations: {len(validation_result.recommendations)}")
        print(f"")
        print(f"🔧 CONFIGURATION SUMMARY:")
        print(f"   Pipe Sizing Enabled: {summary.pipe_sizing_enabled}")
        print(f"   Standard Diameters: {summary.standard_diameters_count}")
        print(f"   Pipe Types Configured: {len(summary.pipe_types_configured)}")
        print(f"   Standards Enabled: {len(summary.standards_enabled)}")
        print(f"   Hierarchy Levels: {summary.hierarchy_levels}")
        print(f"   Cost Model Diameters: {summary.cost_model_diameters}")
        print(f"   Validation Enabled: {summary.validation_enabled}")
        
        if validation_result.errors:
            print(f"")
            print(f"❌ ERRORS:")
            for i, error in enumerate(validation_result.errors, 1):
                print(f"   {i}. {error}")
        
        if validation_result.warnings:
            print(f"")
            print(f"⚠️ WARNINGS:")
            for i, warning in enumerate(validation_result.warnings, 1):
                print(f"   {i}. {warning}")
        
        if validation_result.recommendations:
            print(f"")
            print(f"💡 RECOMMENDATIONS:")
            for i, recommendation in enumerate(validation_result.recommendations, 1):
                print(f"   {i}. {recommendation}")


# Example usage and testing
if __name__ == "__main__":
    # Create configuration validator
    validator = CHAConfigValidator("configs/cha.yml")
    
    try:
        # Load configuration
        if not validator.load_configuration():
            print("❌ Failed to load configuration")
            exit(1)
        
        # Validate configuration
        validation_result = validator.validate_pipe_sizing_configuration()
        
        # Print validation summary
        validator.print_validation_summary(validation_result)
        
        # Export validation report
        validator.export_validation_report(validation_result, "config_validation_report.json")
        
        if validation_result.is_valid:
            print(f"\n🎉 Configuration validation completed successfully!")
        else:
            print(f"\n❌ Configuration validation failed with {len(validation_result.errors)} errors")
        
    except Exception as e:
        print(f"❌ Error in configuration validation: {e}")
        import traceback
        traceback.print_exc()
