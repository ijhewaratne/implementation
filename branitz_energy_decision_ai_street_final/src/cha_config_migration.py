#!/usr/bin/env python3
"""
CHA Configuration Migration Tool

This tool provides comprehensive configuration migration capabilities for the CHA
Intelligent Pipe Sizing System, including:
- Migration from legacy configurations
- Configuration validation
- Backward compatibility
- Configuration templates
- Migration reporting
"""

import os
import sys
import yaml
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from cha_enhanced_config_loader import CHAEnhancedConfigLoader

@dataclass
class MigrationResult:
    """Result of configuration migration."""
    success: bool
    source_config: str
    target_config: str
    migration_type: str
    warnings: List[str]
    errors: List[str]
    changes: List[Dict[str, Any]]
    backup_created: bool
    backup_path: Optional[str]
    timestamp: str

@dataclass
class ValidationResult:
    """Result of configuration validation."""
    valid: bool
    config_path: str
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]
    timestamp: str

class CHAConfigMigrationTool:
    """Configuration migration tool for CHA system."""
    
    def __init__(self, config_dir: str = "configs"):
        """Initialize the migration tool.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.backup_dir = self.config_dir / "backups"
        self.templates_dir = self.config_dir / "templates"
        self.migration_log = []
        
        # Create directories if they don't exist
        self.backup_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # Configuration schemas
        self.schemas = self._load_schemas()
        
        # Migration mappings
        self.migration_mappings = self._load_migration_mappings()
    
    def _setup_logging(self):
        """Setup logging for the migration tool."""
        log_file = self.config_dir / "migration.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def _load_schemas(self) -> Dict[str, Dict]:
        """Load configuration schemas for validation."""
        return {
            'cha_v1': {
                'required_fields': ['streets_path', 'buildings_path', 'plant_lon', 'plant_lat'],
                'optional_fields': ['max_building_distance_m', 'connectivity_fix_distance_m'],
                'version': '1.0'
            },
            'cha_v2': {
                'required_fields': ['streets_path', 'buildings_path', 'plant_lon', 'plant_lat', 'pipe_sizing'],
                'optional_fields': ['max_building_distance_m', 'connectivity_fix_distance_m', 'pandapipes'],
                'version': '2.0'
            },
            'cha_intelligent_sizing': {
                'required_fields': ['flow_calculation', 'pipe_sizing', 'network_hierarchy'],
                'optional_fields': ['standards_compliance', 'output', 'validation', 'performance'],
                'version': '2.1'
            }
        }
    
    def _load_migration_mappings(self) -> Dict[str, Dict]:
        """Load migration mappings between configuration versions."""
        return {
            'cha_v1_to_cha_v2': {
                'mappings': {
                    'default_pipe_diameter_m': 'pipe_sizing.default_diameter_m',
                    'default_pipe_roughness_mm': 'pipe_sizing.pipe_roughness_mm',
                    'default_mass_flow_kg_s': 'pipe_sizing.default_mass_flow_kg_s',
                    'enable_pandapipes_simulation': 'pandapipes.enabled'
                },
                'new_sections': {
                    'pipe_sizing': {
                        'enable_intelligent_sizing': True,
                        'standard_diameters': [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400],
                        'max_velocity_ms': 2.0,
                        'min_velocity_ms': 0.1,
                        'max_pressure_drop_pa_per_m': 5000
                    }
                }
            },
            'cha_v2_to_cha_intelligent_sizing': {
                'mappings': {
                    'pipe_sizing.standard_diameters': 'pipe_sizing.standard_diameters_mm',
                    'pipe_sizing.max_velocity_ms': 'pipe_sizing.max_velocity_ms',
                    'pipe_sizing.min_velocity_ms': 'pipe_sizing.min_velocity_ms',
                    'pipe_sizing.max_pressure_drop_pa_per_m': 'pipe_sizing.max_pressure_drop_pa_per_m'
                },
                'new_sections': {
                    'flow_calculation': {
                        'supply_temperature_c': 70,
                        'return_temperature_c': 40,
                        'safety_factor': 1.1,
                        'diversity_factor': 0.8,
                        'water_density_kg_m3': 977.8,
                        'water_specific_heat_j_per_kgk': 4180
                    },
                    'network_hierarchy': {
                        'network_analysis': True,
                        'connectivity_check': True,
                        'critical_path_analysis': True
                    },
                    'standards_compliance': {
                        'standards_enabled': ['EN_13941', 'DIN_1988', 'VDI_2067', 'Local_Codes']
                    }
                }
            }
        }
    
    def detect_config_version(self, config_path: str) -> str:
        """Detect the version of a configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Detected version string
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Check for intelligent sizing configuration
            if 'flow_calculation' in config and 'pipe_sizing' in config and 'network_hierarchy' in config:
                return 'cha_intelligent_sizing'
            
            # Check for v2 configuration
            if 'pipe_sizing' in config:
                return 'cha_v2'
            
            # Check for v1 configuration
            if 'streets_path' in config and 'buildings_path' in config:
                return 'cha_v1'
            
            return 'unknown'
            
        except Exception as e:
            self.logger.error(f"Error detecting config version for {config_path}: {e}")
            return 'unknown'
    
    def validate_config(self, config_path: str) -> ValidationResult:
        """Validate a configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Load configuration
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Detect version
            version = self.detect_config_version(config_path)
            
            if version == 'unknown':
                errors.append("Unknown configuration version")
                return ValidationResult(
                    valid=False,
                    config_path=config_path,
                    errors=errors,
                    warnings=warnings,
                    suggestions=suggestions,
                    timestamp=datetime.now().isoformat()
                )
            
            # Get schema for validation
            schema = self.schemas.get(version, {})
            
            # Check required fields
            required_fields = schema.get('required_fields', [])
            for field in required_fields:
                if not self._check_nested_field(config, field):
                    errors.append(f"Missing required field: {field}")
            
            # Check optional fields and provide suggestions
            optional_fields = schema.get('optional_fields', [])
            for field in optional_fields:
                if not self._check_nested_field(config, field):
                    suggestions.append(f"Consider adding optional field: {field}")
            
            # Validate specific sections
            if version == 'cha_intelligent_sizing':
                self._validate_intelligent_sizing_config(config, errors, warnings, suggestions)
            
            valid = len(errors) == 0
            
        except Exception as e:
            errors.append(f"Error loading configuration: {e}")
            valid = False
        
        return ValidationResult(
            valid=valid,
            config_path=config_path,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions,
            timestamp=datetime.now().isoformat()
        )
    
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
    
    def _validate_intelligent_sizing_config(self, config: Dict, errors: List[str], 
                                          warnings: List[str], suggestions: List[str]):
        """Validate intelligent sizing configuration.
        
        Args:
            config: Configuration dictionary
            errors: List to append errors to
            warnings: List to append warnings to
            suggestions: List to append suggestions to
        """
        # Validate pipe sizing section
        if 'pipe_sizing' in config:
            pipe_sizing = config['pipe_sizing']
            
            # Check velocity constraints
            if pipe_sizing.get('max_velocity_ms', 0) <= pipe_sizing.get('min_velocity_ms', 0):
                errors.append("max_velocity_ms must be greater than min_velocity_ms")
            
            # Check standard diameters
            if 'standard_diameters_mm' in pipe_sizing:
                diameters = pipe_sizing['standard_diameters_mm']
                if not isinstance(diameters, list) or len(diameters) == 0:
                    errors.append("standard_diameters_mm must be a non-empty list")
                elif not all(isinstance(d, (int, float)) and d > 0 for d in diameters):
                    errors.append("All standard diameters must be positive numbers")
        
        # Validate flow calculation section
        if 'flow_calculation' in config:
            flow_calc = config['flow_calculation']
            
            # Check temperature settings
            if flow_calc.get('supply_temperature_c', 0) <= flow_calc.get('return_temperature_c', 0):
                errors.append("supply_temperature_c must be greater than return_temperature_c")
            
            # Check safety factors
            if flow_calc.get('safety_factor', 1.0) < 1.0:
                warnings.append("safety_factor should be >= 1.0")
            
            if flow_calc.get('diversity_factor', 1.0) > 1.0:
                warnings.append("diversity_factor should be <= 1.0")
    
    def migrate_config(self, source_path: str, target_path: str, 
                      migration_type: str = "auto") -> MigrationResult:
        """Migrate a configuration file.
        
        Args:
            source_path: Path to source configuration file
            target_path: Path to target configuration file
            migration_type: Type of migration to perform
            
        Returns:
            Migration result
        """
        warnings = []
        errors = []
        changes = []
        
        try:
            # Load source configuration
            with open(source_path, 'r') as f:
                source_config = yaml.safe_load(f)
            
            # Detect source version
            source_version = self.detect_config_version(source_path)
            
            if source_version == 'unknown':
                errors.append(f"Unknown source configuration version: {source_path}")
                return MigrationResult(
                    success=False,
                    source_config=source_path,
                    target_config=target_path,
                    migration_type=migration_type,
                    warnings=warnings,
                    errors=errors,
                    changes=changes,
                    backup_created=False,
                    backup_path=None,
                    timestamp=datetime.now().isoformat()
                )
            
            # Create backup
            backup_path = self._create_backup(source_path)
            
            # Determine target version
            if migration_type == "auto":
                if source_version == 'cha_v1':
                    target_version = 'cha_v2'
                elif source_version == 'cha_v2':
                    target_version = 'cha_intelligent_sizing'
                else:
                    target_version = 'cha_intelligent_sizing'
            else:
                target_version = migration_type
            
            # Perform migration
            migrated_config = self._perform_migration(source_config, source_version, target_version)
            
            # Save migrated configuration
            with open(target_path, 'w') as f:
                yaml.dump(migrated_config, f, default_flow_style=False, indent=2)
            
            # Log migration
            self.migration_log.append({
                'source': source_path,
                'target': target_path,
                'source_version': source_version,
                'target_version': target_version,
                'timestamp': datetime.now().isoformat(),
                'success': True
            })
            
            self.logger.info(f"Successfully migrated {source_path} to {target_path}")
            
        except Exception as e:
            errors.append(f"Migration failed: {e}")
            self.logger.error(f"Migration failed for {source_path}: {e}")
        
        return MigrationResult(
            success=len(errors) == 0,
            source_config=source_path,
            target_config=target_path,
            migration_type=migration_type,
            warnings=warnings,
            errors=errors,
            changes=changes,
            backup_created=backup_path is not None,
            backup_path=backup_path,
            timestamp=datetime.now().isoformat()
        )
    
    def _create_backup(self, config_path: str) -> Optional[str]:
        """Create a backup of the configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{Path(config_path).stem}_backup_{timestamp}.yml"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(config_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {config_path}: {e}")
            return None
    
    def _perform_migration(self, source_config: Dict, source_version: str, 
                          target_version: str) -> Dict:
        """Perform the actual migration between versions.
        
        Args:
            source_config: Source configuration dictionary
            source_version: Source version string
            target_version: Target version string
            
        Returns:
            Migrated configuration dictionary
        """
        migration_key = f"{source_version}_to_{target_version}"
        migration_mapping = self.migration_mappings.get(migration_key, {})
        
        # Start with source configuration
        migrated_config = source_config.copy()
        
        # Apply field mappings
        mappings = migration_mapping.get('mappings', {})
        for source_field, target_field in mappings.items():
            if self._check_nested_field(migrated_config, source_field):
                value = self._get_nested_field(migrated_config, source_field)
                self._set_nested_field(migrated_config, target_field, value)
                # Remove from old location
                self._remove_nested_field(migrated_config, source_field)
        
        # Add new sections
        new_sections = migration_mapping.get('new_sections', {})
        for section_name, section_config in new_sections.items():
            if section_name not in migrated_config:
                migrated_config[section_name] = section_config
        
        # Add version information
        migrated_config['_migration_info'] = {
            'migrated_from': source_version,
            'migrated_to': target_version,
            'migration_timestamp': datetime.now().isoformat(),
            'migration_tool': 'CHAConfigMigrationTool'
        }
        
        return migrated_config
    
    def _get_nested_field(self, config: Dict, field_path: str) -> Any:
        """Get a nested field value from configuration.
        
        Args:
            config: Configuration dictionary
            field_path: Dot-separated field path
            
        Returns:
            Field value
        """
        keys = field_path.split('.')
        current = config
        
        for key in keys:
            current = current[key]
        
        return current
    
    def _set_nested_field(self, config: Dict, field_path: str, value: Any):
        """Set a nested field value in configuration.
        
        Args:
            config: Configuration dictionary
            field_path: Dot-separated field path
            value: Value to set
        """
        keys = field_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _remove_nested_field(self, config: Dict, field_path: str):
        """Remove a nested field from configuration.
        
        Args:
            config: Configuration dictionary
            field_path: Dot-separated field path
        """
        keys = field_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key in current:
                current = current[key]
            else:
                return  # Field doesn't exist
        
        if keys[-1] in current:
            del current[keys[-1]]
    
    def create_config_template(self, template_name: str, config_type: str = "cha_intelligent_sizing") -> str:
        """Create a configuration template.
        
        Args:
            template_name: Name of the template
            config_type: Type of configuration template
            
        Returns:
            Path to created template file
        """
        template_path = self.templates_dir / f"{template_name}.yml"
        
        if config_type == "cha_intelligent_sizing":
            template_config = self._get_intelligent_sizing_template()
        elif config_type == "cha_v2":
            template_config = self._get_cha_v2_template()
        else:
            template_config = self._get_cha_v1_template()
        
        with open(template_path, 'w') as f:
            yaml.dump(template_config, f, default_flow_style=False, indent=2)
        
        self.logger.info(f"Created template: {template_path}")
        return str(template_path)
    
    def _get_intelligent_sizing_template(self) -> Dict:
        """Get intelligent sizing configuration template."""
        return {
            'flow_calculation': {
                'supply_temperature_c': 70,
                'return_temperature_c': 40,
                'design_hour_method': 'peak_hour',
                'top_n_hours': 10,
                'design_full_load_hours': 2000,
                'safety_factor': 1.1,
                'diversity_factor': 0.8,
                'water_density_kg_m3': 977.8,
                'water_specific_heat_j_per_kgk': 4180
            },
            'pipe_sizing': {
                'max_velocity_ms': 2.0,
                'min_velocity_ms': 0.1,
                'max_pressure_drop_pa_per_m': 5000,
                'min_pressure_drop_pa_per_m': 100,
                'pipe_roughness_mm': 0.1,
                'cost_factors': {
                    'base_cost_per_mm_diameter': 0.5,
                    'installation_factor': 1.5,
                    'insulation_cost_per_m': 15.0,
                    'material_factor': 1.0
                },
                'standard_diameters_mm': [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400],
                'pipe_categories': {
                    'service_connection': {
                        'diameter_range_m': [0.025, 0.050],
                        'velocity_limit_ms': 1.5,
                        'pressure_drop_limit_pa_per_m': 5000,
                        'typical_flow_range_kg_s': [0.1, 2.0],
                        'material': 'steel_or_plastic',
                        'insulation_required': True
                    },
                    'distribution_pipe': {
                        'diameter_range_m': [0.063, 0.150],
                        'velocity_limit_ms': 2.0,
                        'pressure_drop_limit_pa_per_m': 4000,
                        'typical_flow_range_kg_s': [2.0, 20.0],
                        'material': 'steel',
                        'insulation_required': True
                    },
                    'main_pipe': {
                        'diameter_range_m': [0.200, 0.400],
                        'velocity_limit_ms': 2.0,
                        'pressure_drop_limit_pa_per_m': 3000,
                        'typical_flow_range_kg_s': [10.0, 100.0],
                        'material': 'steel',
                        'insulation_required': True
                    }
                }
            },
            'network_hierarchy': {
                'network_analysis': True,
                'connectivity_check': True,
                'critical_path_analysis': True,
                'hierarchy_levels': {
                    1: {'name': 'Service Connections', 'min_flow_kg_s': 0, 'max_flow_kg_s': 2},
                    2: {'name': 'Street Distribution', 'min_flow_kg_s': 2, 'max_flow_kg_s': 10},
                    3: {'name': 'Area Distribution', 'min_flow_kg_s': 10, 'max_flow_kg_s': 30},
                    4: {'name': 'Main Distribution', 'min_flow_kg_s': 30, 'max_flow_kg_s': 80},
                    5: {'name': 'Primary Main', 'min_flow_kg_s': 80, 'max_flow_kg_s': 200}
                }
            },
            'standards_compliance': {
                'standards_enabled': ['EN_13941', 'DIN_1988', 'VDI_2067', 'Local_Codes'],
                'severity_thresholds': {
                    'critical': 0.5,
                    'high': 0.3,
                    'medium': 0.2,
                    'low': 0.1
                }
            },
            'output': {
                'output_dir': 'processed/cha_intelligent_sizing',
                'export_flow_results': True,
                'export_pipe_sizing_results': True,
                'export_compliance_results': True,
                'export_network_hierarchy': True,
                'export_summary': True
            },
            'validation': {
                'validate_inputs': True,
                'validate_outputs': True,
                'check_connectivity': True,
                'check_standards_compliance': True
            },
            'performance': {
                'enable_optimization': True,
                'parallel_processing': True,
                'max_workers': 4,
                'enable_caching': True,
                'cache_size_mb': 100
            },
            'logging': {
                'log_level': 'INFO',
                'log_file': 'logs/cha_intelligent_sizing.log',
                'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
    
    def _get_cha_v2_template(self) -> Dict:
        """Get CHA v2 configuration template."""
        return {
            'streets_path': 'data/geojson/streets.geojson',
            'buildings_path': 'data/geojson/buildings.geojson',
            'plant_lon': 14.3453979,
            'plant_lat': 51.76274,
            'max_building_distance_m': 50,
            'connectivity_fix_distance_m': 100,
            'output_dir': 'processed/cha',
            'supply_temperature_c': 70,
            'return_temperature_c': 40,
            'supply_pressure_bar': 6.0,
            'return_pressure_bar': 2.0,
            'pipe_sizing': {
                'enable_intelligent_sizing': True,
                'standard_diameters': [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400],
                'max_velocity_ms': 2.0,
                'min_velocity_ms': 0.1,
                'max_pressure_drop_pa_per_m': 5000
            },
            'pandapipes': {
                'enabled': True,
                'default_diameter_m': 0.1,
                'default_roughness_mm': 0.1,
                'default_mass_flow_kg_s': 0.1
            }
        }
    
    def _get_cha_v1_template(self) -> Dict:
        """Get CHA v1 configuration template."""
        return {
            'streets_path': 'data/geojson/streets.geojson',
            'buildings_path': 'data/geojson/buildings.geojson',
            'plant_lon': 14.3453979,
            'plant_lat': 51.76274,
            'max_building_distance_m': 50,
            'connectivity_fix_distance_m': 100,
            'output_dir': 'processed/cha',
            'supply_temperature_c': 70,
            'return_temperature_c': 40,
            'supply_pressure_bar': 6.0,
            'return_pressure_bar': 2.0,
            'default_heating_load_kw': 10.0,
            'default_annual_heat_demand_kwh': 24000,
            'enable_pandapipes_simulation': True,
            'default_pipe_diameter_m': 0.1,
            'default_pipe_roughness_mm': 0.1,
            'default_mass_flow_kg_s': 0.1
        }
    
    def generate_migration_report(self, output_path: str = None) -> str:
        """Generate a migration report.
        
        Args:
            output_path: Path to save the report
            
        Returns:
            Path to the generated report
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config_dir / f"migration_report_{timestamp}.json"
        
        report = {
            'migration_tool_version': '1.0.0',
            'generated_at': datetime.now().isoformat(),
            'migration_log': self.migration_log,
            'available_templates': list(self.templates_dir.glob("*.yml")),
            'available_backups': list(self.backup_dir.glob("*.yml")),
            'configuration_schemas': self.schemas,
            'migration_mappings': self.migration_mappings
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Generated migration report: {output_path}")
        return str(output_path)
    
    def list_configs(self) -> List[Dict[str, Any]]:
        """List all configuration files in the config directory.
        
        Returns:
            List of configuration file information
        """
        configs = []
        
        for config_file in self.config_dir.glob("*.yml"):
            if config_file.name.startswith('.'):
                continue
                
            version = self.detect_config_version(str(config_file))
            validation = self.validate_config(str(config_file))
            
            configs.append({
                'path': str(config_file),
                'name': config_file.name,
                'version': version,
                'valid': validation.valid,
                'errors': validation.errors,
                'warnings': validation.warnings,
                'size_bytes': config_file.stat().st_size,
                'modified': datetime.fromtimestamp(config_file.stat().st_mtime).isoformat()
            })
        
        return configs

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CHA Configuration Migration Tool')
    parser.add_argument('--config-dir', default='configs', help='Configuration directory')
    parser.add_argument('--action', choices=['migrate', 'validate', 'template', 'list', 'report'], 
                       required=True, help='Action to perform')
    parser.add_argument('--source', help='Source configuration file')
    parser.add_argument('--target', help='Target configuration file')
    parser.add_argument('--template-name', help='Template name')
    parser.add_argument('--template-type', default='cha_intelligent_sizing', 
                       choices=['cha_v1', 'cha_v2', 'cha_intelligent_sizing'],
                       help='Template type')
    parser.add_argument('--migration-type', default='auto', 
                       choices=['auto', 'cha_v1_to_cha_v2', 'cha_v2_to_cha_intelligent_sizing'],
                       help='Migration type')
    
    args = parser.parse_args()
    
    # Initialize migration tool
    migration_tool = CHAConfigMigrationTool(args.config_dir)
    
    if args.action == 'migrate':
        if not args.source or not args.target:
            print("Error: --source and --target are required for migration")
            return 1
        
        result = migration_tool.migrate_config(args.source, args.target, args.migration_type)
        
        if result.success:
            print(f"✅ Migration successful: {args.source} -> {args.target}")
            if result.warnings:
                print("⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"   - {warning}")
        else:
            print(f"❌ Migration failed: {args.source} -> {args.target}")
            for error in result.errors:
                print(f"   - {error}")
            return 1
    
    elif args.action == 'validate':
        if not args.source:
            print("Error: --source is required for validation")
            return 1
        
        result = migration_tool.validate_config(args.source)
        
        if result.valid:
            print(f"✅ Configuration is valid: {args.source}")
        else:
            print(f"❌ Configuration is invalid: {args.source}")
            for error in result.errors:
                print(f"   - {error}")
            return 1
        
        if result.warnings:
            print("⚠️  Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")
        
        if result.suggestions:
            print("💡 Suggestions:")
            for suggestion in result.suggestions:
                print(f"   - {suggestion}")
    
    elif args.action == 'template':
        if not args.template_name:
            print("Error: --template-name is required for template creation")
            return 1
        
        template_path = migration_tool.create_config_template(args.template_name, args.template_type)
        print(f"✅ Created template: {template_path}")
    
    elif args.action == 'list':
        configs = migration_tool.list_configs()
        
        print("📋 Configuration Files:")
        for config in configs:
            status = "✅" if config['valid'] else "❌"
            print(f"{status} {config['name']} (v{config['version']}) - {config['path']}")
            if not config['valid'] and config['errors']:
                for error in config['errors']:
                    print(f"   - {error}")
    
    elif args.action == 'report':
        report_path = migration_tool.generate_migration_report()
        print(f"✅ Generated migration report: {report_path}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
