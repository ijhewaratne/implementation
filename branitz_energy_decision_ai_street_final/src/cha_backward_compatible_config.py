#!/usr/bin/env python3
"""
CHA Backward Compatible Configuration Loader

This module provides backward compatibility for CHA configuration files,
automatically detecting and adapting to different configuration versions.
"""

import os
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging

class CHABackwardCompatibleConfigLoader:
    """Backward compatible configuration loader for CHA system."""
    
    def __init__(self, config_path: str):
        """Initialize the configuration loader.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = Path(config_path)
        self.original_config = None
        self.compatible_config = None
        self.config_version = None
        self.logger = logging.getLogger(__name__)
        
        # Load and process configuration
        self._load_config()
        self._detect_version()
        self._make_compatible()
    
    def _load_config(self):
        """Load the configuration file."""
        try:
            with open(self.config_path, 'r') as f:
                self.original_config = yaml.safe_load(f)
            self.logger.info(f"Loaded configuration from {self.config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            raise
    
    def _detect_version(self):
        """Detect the configuration version."""
        if not self.original_config:
            self.config_version = 'unknown'
            return
        
        # Check for intelligent sizing configuration
        if ('flow_calculation' in self.original_config and 
            'pipe_sizing' in self.original_config and 
            'network_hierarchy' in self.original_config):
            self.config_version = 'cha_intelligent_sizing'
        
        # Check for v2 configuration
        elif 'pipe_sizing' in self.original_config:
            self.config_version = 'cha_v2'
        
        # Check for v1 configuration
        elif ('streets_path' in self.original_config and 
              'buildings_path' in self.original_config):
            self.config_version = 'cha_v1'
        
        else:
            self.config_version = 'unknown'
        
        self.logger.info(f"Detected configuration version: {self.config_version}")
    
    def _make_compatible(self):
        """Make the configuration compatible with the latest system."""
        if not self.original_config:
            return
        
        # Start with a copy of the original configuration
        self.compatible_config = self.original_config.copy()
        
        # Apply compatibility transformations based on version
        if self.config_version == 'cha_v1':
            self._upgrade_v1_to_compatible()
        elif self.config_version == 'cha_v2':
            self._upgrade_v2_to_compatible()
        elif self.config_version == 'cha_intelligent_sizing':
            self._ensure_intelligent_sizing_compatibility()
        else:
            self.logger.warning(f"Unknown configuration version: {self.config_version}")
            self._apply_default_compatibility()
        
        # Add compatibility metadata
        self.compatible_config['_compatibility_info'] = {
            'original_version': self.config_version,
            'compatibility_timestamp': self._get_timestamp(),
            'compatibility_loader': 'CHABackwardCompatibleConfigLoader'
        }
    
    def _upgrade_v1_to_compatible(self):
        """Upgrade CHA v1 configuration to be compatible."""
        self.logger.info("Upgrading CHA v1 configuration to compatible format")
        
        # Add pipe sizing section
        if 'pipe_sizing' not in self.compatible_config:
            self.compatible_config['pipe_sizing'] = {
                'enable_intelligent_sizing': True,
                'standard_diameters': [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400],
                'standard_diameters_mm': [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400],
                'max_velocity_ms': 2.0,
                'min_velocity_ms': 0.1,
                'max_pressure_drop_pa_per_m': 5000,
                'pipe_roughness_mm': self.compatible_config.get('default_pipe_roughness_mm', 0.1),
                'water_density_kg_m3': 977.8,
                'water_specific_heat_j_per_kgk': 4180,
                'pipe_material': 'steel',
                'insulation_material': 'polyurethane',
                'insulation_thickness_mm': 30
            }
        
        # Add pandapipes section
        if 'pandapipes' not in self.compatible_config:
            self.compatible_config['pandapipes'] = {
                'enabled': self.compatible_config.get('enable_pandapipes_simulation', True),
                'default_diameter_m': self.compatible_config.get('default_pipe_diameter_m', 0.1),
                'default_roughness_mm': self.compatible_config.get('default_pipe_roughness_mm', 0.1),
                'default_mass_flow_kg_s': self.compatible_config.get('default_mass_flow_kg_s', 0.1)
            }
        
        # Add flow calculation section
        if 'flow_calculation' not in self.compatible_config:
            self.compatible_config['flow_calculation'] = {
                'supply_temperature_c': self.compatible_config.get('supply_temperature_c', 70),
                'return_temperature_c': self.compatible_config.get('return_temperature_c', 40),
                'design_hour_method': 'peak_hour',
                'top_n_hours': 10,
                'design_full_load_hours': 2000,
                'safety_factor': 1.1,
                'diversity_factor': 0.8,
                'water_density_kg_m3': 977.8,
                'water_specific_heat_j_per_kgk': 4180
            }
        
        # Add network hierarchy section
        if 'network_hierarchy' not in self.compatible_config:
            self.compatible_config['network_hierarchy'] = {
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
            }
        
        # Add standards compliance section
        if 'standards_compliance' not in self.compatible_config:
            self.compatible_config['standards_compliance'] = {
                'standards_enabled': ['EN_13941', 'DIN_1988', 'VDI_2067', 'Local_Codes'],
                'severity_thresholds': {
                    'critical': 0.5,
                    'high': 0.3,
                    'medium': 0.2,
                    'low': 0.1
                }
            }
        
        # Add output section
        if 'output' not in self.compatible_config:
            self.compatible_config['output'] = {
                'output_dir': self.compatible_config.get('output_dir', 'processed/cha'),
                'export_flow_results': True,
                'export_pipe_sizing_results': True,
                'export_compliance_results': True,
                'export_network_hierarchy': True,
                'export_summary': True
            }
        
        # Add validation section
        if 'validation' not in self.compatible_config:
            self.compatible_config['validation'] = {
                'validate_inputs': True,
                'validate_outputs': True,
                'check_connectivity': True,
                'check_standards_compliance': True
            }
        
        # Add performance section
        if 'performance' not in self.compatible_config:
            self.compatible_config['performance'] = {
                'enable_optimization': True,
                'parallel_processing': True,
                'max_workers': 4,
                'enable_caching': True,
                'cache_size_mb': 100
            }
        
        # Add logging section
        if 'logging' not in self.compatible_config:
            self.compatible_config['logging'] = {
                'log_level': 'INFO',
                'log_file': 'logs/cha.log',
                'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
    
    def _upgrade_v2_to_compatible(self):
        """Upgrade CHA v2 configuration to be compatible."""
        self.logger.info("Upgrading CHA v2 configuration to compatible format")
        
        # Ensure pipe_sizing has both standard_diameters and standard_diameters_mm
        if 'pipe_sizing' in self.compatible_config:
            pipe_sizing = self.compatible_config['pipe_sizing']
            
            # Add standard_diameters_mm if not present
            if 'standard_diameters' in pipe_sizing and 'standard_diameters_mm' not in pipe_sizing:
                pipe_sizing['standard_diameters_mm'] = pipe_sizing['standard_diameters']
            
            # Add standard_diameters if not present
            if 'standard_diameters_mm' in pipe_sizing and 'standard_diameters' not in pipe_sizing:
                pipe_sizing['standard_diameters'] = pipe_sizing['standard_diameters_mm']
        
        # Add missing sections
        self._add_missing_sections()
    
    def _ensure_intelligent_sizing_compatibility(self):
        """Ensure intelligent sizing configuration is fully compatible."""
        self.logger.info("Ensuring intelligent sizing configuration compatibility")
        
        # Ensure pipe_sizing has both standard_diameters and standard_diameters_mm
        if 'pipe_sizing' in self.compatible_config:
            pipe_sizing = self.compatible_config['pipe_sizing']
            
            # Add standard_diameters if not present
            if 'standard_diameters_mm' in pipe_sizing and 'standard_diameters' not in pipe_sizing:
                pipe_sizing['standard_diameters'] = pipe_sizing['standard_diameters_mm']
            
            # Add standard_diameters_mm if not present
            if 'standard_diameters' in pipe_sizing and 'standard_diameters_mm' not in pipe_sizing:
                pipe_sizing['standard_diameters_mm'] = pipe_sizing['standard_diameters']
        
        # Ensure all required sections exist
        self._add_missing_sections()
    
    def _add_missing_sections(self):
        """Add any missing sections with default values."""
        default_sections = {
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
                'output_dir': 'processed/cha',
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
                'log_file': 'logs/cha.log',
                'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        }
        
        for section_name, section_config in default_sections.items():
            if section_name not in self.compatible_config:
                self.compatible_config[section_name] = section_config
                self.logger.info(f"Added missing section: {section_name}")
    
    def _apply_default_compatibility(self):
        """Apply default compatibility for unknown configuration versions."""
        self.logger.warning("Applying default compatibility for unknown configuration version")
        
        # Add all required sections with default values
        self._add_missing_sections()
        
        # Ensure basic pipe sizing configuration
        if 'pipe_sizing' not in self.compatible_config:
            self.compatible_config['pipe_sizing'] = {
                'enable_intelligent_sizing': True,
                'standard_diameters': [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400],
                'standard_diameters_mm': [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400],
                'max_velocity_ms': 2.0,
                'min_velocity_ms': 0.1,
                'max_pressure_drop_pa_per_m': 5000,
                'pipe_roughness_mm': 0.1,
                'water_density_kg_m3': 977.8,
                'water_specific_heat_j_per_kgk': 4180
            }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_config(self) -> Dict[str, Any]:
        """Get the compatible configuration.
        
        Returns:
            Compatible configuration dictionary
        """
        return self.compatible_config
    
    def get_original_config(self) -> Dict[str, Any]:
        """Get the original configuration.
        
        Returns:
            Original configuration dictionary
        """
        return self.original_config
    
    def get_version(self) -> str:
        """Get the detected configuration version.
        
        Returns:
            Configuration version string
        """
        return self.config_version
    
    def get_compatibility_info(self) -> Dict[str, Any]:
        """Get compatibility information.
        
        Returns:
            Compatibility information dictionary
        """
        return self.compatible_config.get('_compatibility_info', {})
    
    def save_compatible_config(self, output_path: str):
        """Save the compatible configuration to a file.
        
        Args:
            output_path: Path to save the compatible configuration
        """
        try:
            with open(output_path, 'w') as f:
                yaml.dump(self.compatible_config, f, default_flow_style=False, indent=2)
            self.logger.info(f"Saved compatible configuration to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save compatible configuration to {output_path}: {e}")
            raise
    
    def is_compatible(self) -> bool:
        """Check if the configuration is compatible with the current system.
        
        Returns:
            True if compatible, False otherwise
        """
        return self.config_version != 'unknown' and self.compatible_config is not None
    
    def get_missing_sections(self) -> list:
        """Get list of missing sections in the original configuration.
        
        Returns:
            List of missing section names
        """
        required_sections = [
            'pipe_sizing', 'flow_calculation', 'network_hierarchy',
            'standards_compliance', 'output', 'validation', 'performance', 'logging'
        ]
        
        missing = []
        for section in required_sections:
            if section not in self.original_config:
                missing.append(section)
        
        return missing
    
    def get_upgrade_recommendations(self) -> list:
        """Get upgrade recommendations for the configuration.
        
        Returns:
            List of upgrade recommendations
        """
        recommendations = []
        
        if self.config_version == 'cha_v1':
            recommendations.extend([
                "Upgrade to CHA v2.0 for intelligent pipe sizing capabilities",
                "Add flow calculation section for advanced flow analysis",
                "Add network hierarchy section for network analysis",
                "Add standards compliance section for engineering standards"
            ])
        elif self.config_version == 'cha_v2':
            recommendations.extend([
                "Upgrade to CHA v2.1 (Intelligent Sizing) for advanced features",
                "Add flow calculation section with safety and diversity factors",
                "Add network hierarchy section for advanced analysis",
                "Add standards compliance section for engineering standards",
                "Add performance optimization section"
            ])
        elif self.config_version == 'cha_intelligent_sizing':
            recommendations.append("Configuration is already at the latest version")
        
        return recommendations

def load_cha_config(config_path: str) -> Dict[str, Any]:
    """Load CHA configuration with backward compatibility.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Compatible configuration dictionary
    """
    loader = CHABackwardCompatibleConfigLoader(config_path)
    return loader.get_config()

def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='CHA Backward Compatible Configuration Loader')
    parser.add_argument('config_path', help='Path to configuration file')
    parser.add_argument('--output', help='Output path for compatible configuration')
    parser.add_argument('--info', action='store_true', help='Show configuration information')
    parser.add_argument('--recommendations', action='store_true', help='Show upgrade recommendations')
    
    args = parser.parse_args()
    
    # Load configuration
    loader = CHABackwardCompatibleConfigLoader(args.config_path)
    
    if args.info:
        print(f"📁 Configuration: {args.config_path}")
        print(f"🔧 Version: {loader.get_version()}")
        print(f"✅ Compatible: {loader.is_compatible()}")
        print(f"📅 Compatibility Timestamp: {loader.get_compatibility_info().get('compatibility_timestamp', 'N/A')}")
        
        missing_sections = loader.get_missing_sections()
        if missing_sections:
            print(f"⚠️  Missing Sections: {', '.join(missing_sections)}")
        else:
            print("✅ All required sections present")
    
    if args.recommendations:
        recommendations = loader.get_upgrade_recommendations()
        print("💡 Upgrade Recommendations:")
        for rec in recommendations:
            print(f"   - {rec}")
    
    if args.output:
        loader.save_compatible_config(args.output)
        print(f"✅ Saved compatible configuration to {args.output}")
    
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
