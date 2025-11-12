#!/usr/bin/env python3
"""
CHA Configuration Validation Script

This script provides comprehensive validation of CHA configuration files,
including:
- Schema validation
- Value range validation
- Dependency validation
- Best practices validation
- Migration recommendations
"""

import os
import sys
import yaml
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from cha_config_migration import CHAConfigMigrationTool, ValidationResult

class CHAConfigValidator:
    """Enhanced configuration validator for CHA system."""
    
    def __init__(self):
        """Initialize the validator."""
        self.migration_tool = CHAConfigMigrationTool()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # Validation rules
        self.validation_rules = self._load_validation_rules()
    
    def _setup_logging(self):
        """Setup logging for the validator."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def _load_validation_rules(self) -> Dict[str, Dict]:
        """Load validation rules for different configuration types."""
        return {
            'cha_intelligent_sizing': {
                'pipe_sizing': {
                    'max_velocity_ms': {'min': 0.1, 'max': 5.0, 'type': 'float'},
                    'min_velocity_ms': {'min': 0.01, 'max': 2.0, 'type': 'float'},
                    'max_pressure_drop_pa_per_m': {'min': 100, 'max': 10000, 'type': 'float'},
                    'standard_diameters_mm': {'min_items': 3, 'max_items': 20, 'type': 'list'},
                    'pipe_roughness_mm': {'min': 0.01, 'max': 2.0, 'type': 'float'}
                },
                'flow_calculation': {
                    'supply_temperature_c': {'min': 40, 'max': 120, 'type': 'float'},
                    'return_temperature_c': {'min': 20, 'max': 80, 'type': 'float'},
                    'safety_factor': {'min': 1.0, 'max': 2.0, 'type': 'float'},
                    'diversity_factor': {'min': 0.1, 'max': 1.0, 'type': 'float'},
                    'water_density_kg_m3': {'min': 800, 'max': 1200, 'type': 'float'},
                    'water_specific_heat_j_per_kgk': {'min': 4000, 'max': 4500, 'type': 'float'}
                },
                'network_hierarchy': {
                    'hierarchy_levels': {'min_items': 3, 'max_items': 10, 'type': 'dict'}
                },
                'standards_compliance': {
                    'standards_enabled': {'min_items': 1, 'type': 'list'},
                    'severity_thresholds': {'required_keys': ['critical', 'high', 'medium', 'low'], 'type': 'dict'}
                },
                'performance': {
                    'max_workers': {'min': 1, 'max': 16, 'type': 'int'},
                    'cache_size_mb': {'min': 10, 'max': 1000, 'type': 'int'}
                }
            },
            'cha_v2': {
                'pipe_sizing': {
                    'max_velocity_ms': {'min': 0.1, 'max': 5.0, 'type': 'float'},
                    'min_velocity_ms': {'min': 0.01, 'max': 2.0, 'type': 'float'},
                    'standard_diameters': {'min_items': 3, 'max_items': 20, 'type': 'list'}
                },
                'pandapipes': {
                    'default_diameter_m': {'min': 0.025, 'max': 0.5, 'type': 'float'},
                    'default_roughness_mm': {'min': 0.01, 'max': 2.0, 'type': 'float'}
                }
            },
            'cha_v1': {
                'max_building_distance_m': {'min': 10, 'max': 200, 'type': 'float'},
                'connectivity_fix_distance_m': {'min': 50, 'max': 500, 'type': 'float'},
                'supply_temperature_c': {'min': 40, 'max': 120, 'type': 'float'},
                'return_temperature_c': {'min': 20, 'max': 80, 'type': 'float'},
                'default_pipe_diameter_m': {'min': 0.025, 'max': 0.5, 'type': 'float'}
            }
        }
    
    def validate_config_comprehensive(self, config_path: str) -> Dict[str, Any]:
        """Perform comprehensive validation of a configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Comprehensive validation results
        """
        results = {
            'config_path': config_path,
            'timestamp': datetime.now().isoformat(),
            'basic_validation': None,
            'schema_validation': None,
            'value_validation': None,
            'dependency_validation': None,
            'best_practices_validation': None,
            'migration_recommendations': None,
            'overall_valid': False,
            'summary': {}
        }
        
        try:
            # Basic validation using migration tool
            basic_result = self.migration_tool.validate_config(config_path)
            results['basic_validation'] = {
                'valid': basic_result.valid,
                'errors': basic_result.errors,
                'warnings': basic_result.warnings,
                'suggestions': basic_result.suggestions
            }
            
            # Load configuration for detailed validation
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Detect version
            version = self.migration_tool.detect_config_version(config_path)
            results['detected_version'] = version
            
            # Schema validation
            schema_result = self._validate_schema(config, version)
            results['schema_validation'] = schema_result
            
            # Value validation
            value_result = self._validate_values(config, version)
            results['value_validation'] = value_result
            
            # Dependency validation
            dependency_result = self._validate_dependencies(config, version)
            results['dependency_validation'] = dependency_result
            
            # Best practices validation
            best_practices_result = self._validate_best_practices(config, version)
            results['best_practices_validation'] = best_practices_result
            
            # Migration recommendations
            migration_recommendations = self._get_migration_recommendations(version, config)
            results['migration_recommendations'] = migration_recommendations
            
            # Overall validation
            results['overall_valid'] = (
                basic_result.valid and
                schema_result['valid'] and
                value_result['valid'] and
                dependency_result['valid']
            )
            
            # Generate summary
            results['summary'] = self._generate_validation_summary(results)
            
        except Exception as e:
            results['error'] = str(e)
            results['overall_valid'] = False
        
        return results
    
    def _validate_schema(self, config: Dict, version: str) -> Dict[str, Any]:
        """Validate configuration schema.
        
        Args:
            config: Configuration dictionary
            version: Configuration version
            
        Returns:
            Schema validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'missing_required': [],
            'unexpected_fields': []
        }
        
        # Get schema for version
        schema = self.migration_tool.schemas.get(version, {})
        
        # Check required fields
        required_fields = schema.get('required_fields', [])
        for field in required_fields:
            if not self._check_nested_field(config, field):
                result['missing_required'].append(field)
                result['valid'] = False
        
        # Check for unexpected fields (basic check)
        if version == 'cha_v1':
            expected_fields = ['streets_path', 'buildings_path', 'plant_lon', 'plant_lat']
        elif version == 'cha_v2':
            expected_fields = ['streets_path', 'buildings_path', 'plant_lon', 'plant_lat', 'pipe_sizing']
        elif version == 'cha_intelligent_sizing':
            expected_fields = ['flow_calculation', 'pipe_sizing', 'network_hierarchy']
        else:
            expected_fields = []
        
        for field in config.keys():
            if field not in expected_fields and not field.startswith('_'):
                result['unexpected_fields'].append(field)
                result['warnings'].append(f"Unexpected field: {field}")
        
        return result
    
    def _validate_values(self, config: Dict, version: str) -> Dict[str, Any]:
        """Validate configuration values against rules.
        
        Args:
            config: Configuration dictionary
            version: Configuration version
            
        Returns:
            Value validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'validated_fields': []
        }
        
        # Get validation rules for version
        rules = self.validation_rules.get(version, {})
        
        for section, section_rules in rules.items():
            if section in config:
                section_config = config[section]
                
                for field, field_rules in section_rules.items():
                    if field in section_config:
                        field_value = section_config[field]
                        field_result = self._validate_field_value(field_value, field_rules, f"{section}.{field}")
                        
                        result['validated_fields'].append(f"{section}.{field}")
                        
                        if not field_result['valid']:
                            result['valid'] = False
                            result['errors'].extend(field_result['errors'])
                        
                        result['warnings'].extend(field_result['warnings'])
        
        return result
    
    def _validate_field_value(self, value: Any, rules: Dict, field_path: str) -> Dict[str, Any]:
        """Validate a single field value against rules.
        
        Args:
            value: Field value
            rules: Validation rules
            field_path: Field path for error messages
            
        Returns:
            Field validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Type validation
        expected_type = rules.get('type')
        if expected_type:
            if expected_type == 'float' and not isinstance(value, (int, float)):
                result['errors'].append(f"{field_path}: Expected float, got {type(value).__name__}")
                result['valid'] = False
            elif expected_type == 'int' and not isinstance(value, int):
                result['errors'].append(f"{field_path}: Expected int, got {type(value).__name__}")
                result['valid'] = False
            elif expected_type == 'list' and not isinstance(value, list):
                result['errors'].append(f"{field_path}: Expected list, got {type(value).__name__}")
                result['valid'] = False
            elif expected_type == 'dict' and not isinstance(value, dict):
                result['errors'].append(f"{field_path}: Expected dict, got {type(value).__name__}")
                result['valid'] = False
        
        # Range validation for numeric values
        if isinstance(value, (int, float)):
            if 'min' in rules and value < rules['min']:
                result['errors'].append(f"{field_path}: Value {value} is below minimum {rules['min']}")
                result['valid'] = False
            if 'max' in rules and value > rules['max']:
                result['errors'].append(f"{field_path}: Value {value} is above maximum {rules['max']}")
                result['valid'] = False
        
        # List validation
        if isinstance(value, list):
            if 'min_items' in rules and len(value) < rules['min_items']:
                result['errors'].append(f"{field_path}: List has {len(value)} items, minimum is {rules['min_items']}")
                result['valid'] = False
            if 'max_items' in rules and len(value) > rules['max_items']:
                result['warnings'].append(f"{field_path}: List has {len(value)} items, maximum recommended is {rules['max_items']}")
        
        # Dict validation
        if isinstance(value, dict):
            if 'required_keys' in rules:
                missing_keys = set(rules['required_keys']) - set(value.keys())
                if missing_keys:
                    result['errors'].append(f"{field_path}: Missing required keys: {list(missing_keys)}")
                    result['valid'] = False
        
        return result
    
    def _validate_dependencies(self, config: Dict, version: str) -> Dict[str, Any]:
        """Validate configuration dependencies.
        
        Args:
            config: Configuration dictionary
            version: Configuration version
            
        Returns:
            Dependency validation results
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Temperature dependency validation
        if 'flow_calculation' in config:
            flow_calc = config['flow_calculation']
            supply_temp = flow_calc.get('supply_temperature_c')
            return_temp = flow_calc.get('return_temperature_c')
            
            if supply_temp and return_temp:
                if supply_temp <= return_temp:
                    result['errors'].append("supply_temperature_c must be greater than return_temperature_c")
                    result['valid'] = False
                
                delta_t = supply_temp - return_temp
                if delta_t < 10:
                    result['warnings'].append(f"Temperature difference ({delta_t}°C) is quite low, consider increasing")
                elif delta_t > 50:
                    result['warnings'].append(f"Temperature difference ({delta_t}°C) is quite high, consider reducing")
        
        # Velocity dependency validation
        if 'pipe_sizing' in config:
            pipe_sizing = config['pipe_sizing']
            max_velocity = pipe_sizing.get('max_velocity_ms')
            min_velocity = pipe_sizing.get('min_velocity_ms')
            
            if max_velocity and min_velocity:
                if max_velocity <= min_velocity:
                    result['errors'].append("max_velocity_ms must be greater than min_velocity_ms")
                    result['valid'] = False
        
        # File path validation
        if 'streets_path' in config:
            streets_path = config['streets_path']
            if not os.path.exists(streets_path):
                result['warnings'].append(f"Streets file not found: {streets_path}")
        
        if 'buildings_path' in config:
            buildings_path = config['buildings_path']
            if not os.path.exists(buildings_path):
                result['warnings'].append(f"Buildings file not found: {buildings_path}")
        
        return result
    
    def _validate_best_practices(self, config: Dict, version: str) -> Dict[str, Any]:
        """Validate configuration against best practices.
        
        Args:
            config: Configuration dictionary
            version: Configuration version
            
        Returns:
            Best practices validation results
        """
        result = {
            'valid': True,
            'recommendations': [],
            'warnings': []
        }
        
        # Performance recommendations
        if 'performance' in config:
            performance = config['performance']
            
            max_workers = performance.get('max_workers', 1)
            if max_workers == 1:
                result['recommendations'].append("Consider increasing max_workers for better performance")
            
            if not performance.get('enable_caching', False):
                result['recommendations'].append("Consider enabling caching for better performance")
        
        # Standards compliance recommendations
        if 'standards_compliance' in config:
            standards = config['standards_compliance']
            enabled_standards = standards.get('standards_enabled', [])
            
            if 'EN_13941' not in enabled_standards:
                result['recommendations'].append("Consider enabling EN_13941 standard for district heating")
            
            if 'DIN_1988' not in enabled_standards:
                result['recommendations'].append("Consider enabling DIN_1988 standard for drinking water")
        
        # Pipe sizing recommendations
        if 'pipe_sizing' in config:
            pipe_sizing = config['pipe_sizing']
            
            standard_diameters = pipe_sizing.get('standard_diameters_mm', [])
            if len(standard_diameters) < 5:
                result['recommendations'].append("Consider adding more standard diameters for better sizing flexibility")
            
            # Check for reasonable velocity limits
            max_velocity = pipe_sizing.get('max_velocity_ms', 2.0)
            if max_velocity > 3.0:
                result['warnings'].append("High velocity limit may cause noise and pressure issues")
            elif max_velocity < 1.0:
                result['warnings'].append("Low velocity limit may result in oversized pipes")
        
        # Logging recommendations
        if 'logging' in config:
            logging_config = config['logging']
            log_level = logging_config.get('log_level', 'INFO')
            
            if log_level == 'DEBUG':
                result['recommendations'].append("DEBUG log level may impact performance in production")
        
        return result
    
    def _get_migration_recommendations(self, version: str, config: Dict) -> Dict[str, Any]:
        """Get migration recommendations for the configuration.
        
        Args:
            version: Current configuration version
            config: Configuration dictionary
            
        Returns:
            Migration recommendations
        """
        recommendations = {
            'current_version': version,
            'recommended_version': None,
            'migration_available': False,
            'migration_steps': [],
            'benefits': []
        }
        
        if version == 'cha_v1':
            recommendations['recommended_version'] = 'cha_v2'
            recommendations['migration_available'] = True
            recommendations['migration_steps'] = [
                "Add pipe_sizing section with intelligent sizing parameters",
                "Migrate pandapipes settings to dedicated section",
                "Add enhanced configuration options"
            ]
            recommendations['benefits'] = [
                "Intelligent pipe sizing capabilities",
                "Enhanced pandapipes integration",
                "Better configuration organization"
            ]
        
        elif version == 'cha_v2':
            recommendations['recommended_version'] = 'cha_intelligent_sizing'
            recommendations['migration_available'] = True
            recommendations['migration_steps'] = [
                "Add flow_calculation section with safety and diversity factors",
                "Add network_hierarchy section for advanced analysis",
                "Add standards_compliance section for engineering standards",
                "Add performance and validation sections"
            ]
            recommendations['benefits'] = [
                "Advanced flow calculation with safety factors",
                "Network hierarchy analysis",
                "Engineering standards compliance",
                "Performance optimization features",
                "Comprehensive validation"
            ]
        
        elif version == 'cha_intelligent_sizing':
            recommendations['recommended_version'] = version
            recommendations['migration_available'] = False
            recommendations['benefits'] = [
                "Already using the latest configuration version",
                "All advanced features available"
            ]
        
        return recommendations
    
    def _generate_validation_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of validation results.
        
        Args:
            results: Complete validation results
            
        Returns:
            Validation summary
        """
        summary = {
            'overall_status': 'VALID' if results['overall_valid'] else 'INVALID',
            'total_errors': 0,
            'total_warnings': 0,
            'total_recommendations': 0,
            'validation_categories': {}
        }
        
        # Count errors and warnings
        for category in ['basic_validation', 'schema_validation', 'value_validation', 'dependency_validation']:
            if results.get(category):
                category_result = results[category]
                summary['total_errors'] += len(category_result.get('errors', []))
                summary['total_warnings'] += len(category_result.get('warnings', []))
                
                summary['validation_categories'][category] = {
                    'valid': category_result.get('valid', False),
                    'errors': len(category_result.get('errors', [])),
                    'warnings': len(category_result.get('warnings', []))
                }
        
        # Count recommendations
        if results.get('best_practices_validation'):
            summary['total_recommendations'] += len(results['best_practices_validation'].get('recommendations', []))
        
        return summary
    
    def _check_nested_field(self, config: Dict, field_path: str) -> bool:
        """Check if a nested field exists in configuration.
        
        Args:
            config: Configuration dictionary
            field_path: Dot-separated field path
            
        Returns:
            True if field exists, False otherwise
        """
        keys = field_path.split('.')
        current = config
        
        for key in keys:
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        
        return True
    
    def export_validation_report(self, results: Dict[str, Any], output_path: str):
        """Export validation results to a file.
        
        Args:
            results: Validation results
            output_path: Path to save the report
        """
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Validation report exported to: {output_path}")

def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='CHA Configuration Validator')
    parser.add_argument('config_path', help='Path to configuration file')
    parser.add_argument('--output', help='Output file for validation report')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='Output format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize validator
    validator = CHAConfigValidator()
    
    # Perform validation
    results = validator.validate_config_comprehensive(args.config_path)
    
    # Output results
    if args.format == 'json':
        if args.output:
            validator.export_validation_report(results, args.output)
        else:
            print(json.dumps(results, indent=2, default=str))
    else:
        # Text output
        print(f"🔍 Configuration Validation Report")
        print(f"📁 File: {results['config_path']}")
        print(f"📅 Timestamp: {results['timestamp']}")
        print(f"🔧 Version: {results.get('detected_version', 'unknown')}")
        print()
        
        # Overall status
        status_icon = "✅" if results['overall_valid'] else "❌"
        print(f"{status_icon} Overall Status: {results['summary']['overall_status']}")
        print()
        
        # Summary
        summary = results['summary']
        print(f"📊 Summary:")
        print(f"   Errors: {summary['total_errors']}")
        print(f"   Warnings: {summary['total_warnings']}")
        print(f"   Recommendations: {summary['total_recommendations']}")
        print()
        
        # Detailed results
        if results.get('basic_validation'):
            basic = results['basic_validation']
            if basic['errors']:
                print("❌ Basic Validation Errors:")
                for error in basic['errors']:
                    print(f"   - {error}")
                print()
            
            if basic['warnings']:
                print("⚠️  Basic Validation Warnings:")
                for warning in basic['warnings']:
                    print(f"   - {warning}")
                print()
        
        # Migration recommendations
        if results.get('migration_recommendations'):
            migration = results['migration_recommendations']
            if migration['migration_available']:
                print("🔄 Migration Recommendations:")
                print(f"   Current Version: {migration['current_version']}")
                print(f"   Recommended Version: {migration['recommended_version']}")
                print("   Migration Steps:")
                for step in migration['migration_steps']:
                    print(f"     - {step}")
                print("   Benefits:")
                for benefit in migration['benefits']:
                    print(f"     - {benefit}")
                print()
        
        # Best practices
        if results.get('best_practices_validation'):
            best_practices = results['best_practices_validation']
            if best_practices['recommendations']:
                print("💡 Best Practice Recommendations:")
                for rec in best_practices['recommendations']:
                    print(f"   - {rec}")
                print()
    
    return 0 if results['overall_valid'] else 1

if __name__ == '__main__':
    sys.exit(main())
