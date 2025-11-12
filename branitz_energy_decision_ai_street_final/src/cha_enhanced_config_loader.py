"""
CHA Enhanced Configuration Loader - Enhanced Configuration Integration

This module loads and integrates the enhanced CHA configuration with the existing
system, providing seamless access to pipe sizing parameters and standards.

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

# Import our configuration validator
from cha_config_validation import CHAConfigValidator, ValidationResult

warnings.filterwarnings("ignore")


@dataclass
class PipeSizingConfig:
    """Pipe sizing configuration data class."""
    enable_intelligent_sizing: bool
    standard_diameters: List[int]
    max_velocity_ms: float
    min_velocity_ms: float
    max_pressure_drop_pa_per_m: float
    water_density_kg_m3: float
    water_specific_heat_j_per_kgk: float
    water_dynamic_viscosity_pa_s: float
    pipe_roughness_mm: float
    pipe_material: str
    insulation_material: str
    insulation_thickness_mm: int
    safety_factor: float
    diversity_factor: float
    design_full_load_hours: int
    cost_per_meter: Dict[int, float]
    installation_factor: float
    material_factor: float
    insulation_cost_per_m: float


@dataclass
class PipeTypeConfig:
    """Pipe type configuration data class."""
    min_diameter_mm: int
    max_diameter_mm: int
    flow_threshold_kg_s: float
    velocity_limit_ms: float
    pressure_drop_limit_pa_per_m: float
    material: str
    insulation_required: bool


@dataclass
class StandardsConfig:
    """Engineering standards configuration data class."""
    EN_13941: Dict[str, Any]
    DIN_1988: Dict[str, Any]
    VDI_2067: Dict[str, Any]
    Local_Codes: Dict[str, Any]


@dataclass
class HierarchyLevelConfig:
    """Hierarchy level configuration data class."""
    name: str
    min_flow_kg_s: float
    max_flow_kg_s: float
    typical_diameter_mm: List[int]


@dataclass
class ValidationConfig:
    """Validation configuration data class."""
    enable_validation: bool
    compliance_threshold: float
    critical_violation_threshold: float
    warning_violation_threshold: float


@dataclass
class OutputConfig:
    """Output configuration data class."""
    export_enhanced_data: bool
    export_validation_results: bool
    export_cost_analysis: bool
    export_performance_metrics: bool


@dataclass
class EnhancedCHAConfig:
    """Complete enhanced CHA configuration data class."""
    pipe_sizing: PipeSizingConfig
    main_pipes: PipeTypeConfig
    distribution_pipes: PipeTypeConfig
    service_connections: PipeTypeConfig
    standards: StandardsConfig
    hierarchy_levels: Dict[int, HierarchyLevelConfig]
    validation: ValidationConfig
    output: OutputConfig


class CHAEnhancedConfigLoader:
    """
    Enhanced configuration loader for CHA system.
    
    Loads, validates, and provides access to enhanced pipe sizing configuration
    with seamless integration to existing CHA components.
    """
    
    def __init__(self, config_path: str = "configs/cha.yml"):
        """
        Initialize the enhanced configuration loader.
        
        Args:
            config_path: Path to CHA configuration file
        """
        self.config_path = config_path
        self.raw_config: Dict[str, Any] = {}
        self.enhanced_config: Optional[EnhancedCHAConfig] = None
        self.validator: Optional[CHAConfigValidator] = None
        self.validation_result: Optional[ValidationResult] = None
        
        print(f"✅ CHA Enhanced Configuration Loader initialized")
        print(f"   Configuration file: {config_path}")
    
    def load_configuration(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            success: True if loading successful
        """
        try:
            with open(self.config_path, 'r') as f:
                self.raw_config = yaml.safe_load(f)
            
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
    
    def validate_configuration(self) -> bool:
        """
        Validate configuration using the validator.
        
        Returns:
            success: True if validation successful
        """
        try:
            self.validator = CHAConfigValidator(self.config_path)
            
            if not self.validator.load_configuration():
                print("❌ Failed to load configuration for validation")
                return False
            
            self.validation_result = self.validator.validate_pipe_sizing_configuration()
            
            if self.validation_result.is_valid:
                print(f"✅ Configuration validation passed")
            else:
                print(f"⚠️ Configuration validation failed with {len(self.validation_result.errors)} errors")
                print(f"   Warnings: {len(self.validation_result.warnings)}")
                print(f"   Recommendations: {len(self.validation_result.recommendations)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error validating configuration: {e}")
            return False
    
    def parse_enhanced_configuration(self) -> bool:
        """
        Parse enhanced configuration into structured data classes.
        
        Returns:
            success: True if parsing successful
        """
        try:
            pipe_sizing_config = self.raw_config.get('pipe_sizing', {})
            
            if not pipe_sizing_config:
                print("❌ Pipe sizing configuration section is missing")
                return False
            
            # Parse pipe sizing configuration
            pipe_sizing = PipeSizingConfig(
                enable_intelligent_sizing=pipe_sizing_config.get('enable_intelligent_sizing', True),
                standard_diameters=pipe_sizing_config.get('standard_diameters', [25, 32, 40, 50, 63, 80, 100, 125, 150, 200, 250, 300, 400]),
                max_velocity_ms=pipe_sizing_config.get('max_velocity_ms', 3.0),
                min_velocity_ms=pipe_sizing_config.get('min_velocity_ms', 0.5),
                max_pressure_drop_pa_per_m=pipe_sizing_config.get('max_pressure_drop_pa_per_m', 50),
                water_density_kg_m3=pipe_sizing_config.get('water_density_kg_m3', 977.8),
                water_specific_heat_j_per_kgk=pipe_sizing_config.get('water_specific_heat_j_per_kgk', 4180),
                water_dynamic_viscosity_pa_s=pipe_sizing_config.get('water_dynamic_viscosity_pa_s', 0.000404),
                pipe_roughness_mm=pipe_sizing_config.get('pipe_roughness_mm', 0.1),
                pipe_material=pipe_sizing_config.get('pipe_material', 'steel'),
                insulation_material=pipe_sizing_config.get('insulation_material', 'polyurethane'),
                insulation_thickness_mm=pipe_sizing_config.get('insulation_thickness_mm', 30),
                safety_factor=pipe_sizing_config.get('safety_factor', 1.1),
                diversity_factor=pipe_sizing_config.get('diversity_factor', 0.8),
                design_full_load_hours=pipe_sizing_config.get('design_full_load_hours', 2000),
                cost_per_meter=pipe_sizing_config.get('cost_per_meter', {}),
                installation_factor=pipe_sizing_config.get('installation_factor', 1.5),
                material_factor=pipe_sizing_config.get('material_factor', 1.0),
                insulation_cost_per_m=pipe_sizing_config.get('insulation_cost_per_m', 15.0)
            )
            
            # Parse pipe type configurations
            main_pipes_config = pipe_sizing_config.get('main_pipes', {})
            main_pipes = PipeTypeConfig(
                min_diameter_mm=main_pipes_config.get('min_diameter_mm', 200),
                max_diameter_mm=main_pipes_config.get('max_diameter_mm', 400),
                flow_threshold_kg_s=main_pipes_config.get('flow_threshold_kg_s', 2.0),
                velocity_limit_ms=main_pipes_config.get('velocity_limit_ms', 2.0),
                pressure_drop_limit_pa_per_m=main_pipes_config.get('pressure_drop_limit_pa_per_m', 3000),
                material=main_pipes_config.get('material', 'steel'),
                insulation_required=main_pipes_config.get('insulation_required', True)
            )
            
            distribution_pipes_config = pipe_sizing_config.get('distribution_pipes', {})
            distribution_pipes = PipeTypeConfig(
                min_diameter_mm=distribution_pipes_config.get('min_diameter_mm', 100),
                max_diameter_mm=distribution_pipes_config.get('max_diameter_mm', 200),
                flow_threshold_kg_s=distribution_pipes_config.get('flow_threshold_kg_s', 0.5),
                velocity_limit_ms=distribution_pipes_config.get('velocity_limit_ms', 2.0),
                pressure_drop_limit_pa_per_m=distribution_pipes_config.get('pressure_drop_limit_pa_per_m', 4000),
                material=distribution_pipes_config.get('material', 'steel'),
                insulation_required=distribution_pipes_config.get('insulation_required', True)
            )
            
            service_connections_config = pipe_sizing_config.get('service_connections', {})
            service_connections = PipeTypeConfig(
                min_diameter_mm=service_connections_config.get('min_diameter_mm', 50),
                max_diameter_mm=service_connections_config.get('max_diameter_mm', 100),
                flow_threshold_kg_s=service_connections_config.get('flow_threshold_kg_s', 0.1),
                velocity_limit_ms=service_connections_config.get('velocity_limit_ms', 1.5),
                pressure_drop_limit_pa_per_m=service_connections_config.get('pressure_drop_limit_pa_per_m', 5000),
                material=service_connections_config.get('material', 'steel_or_plastic'),
                insulation_required=service_connections_config.get('insulation_required', True)
            )
            
            # Parse standards configuration
            standards_config = pipe_sizing_config.get('standards', {})
            standards = StandardsConfig(
                EN_13941=standards_config.get('EN_13941', {}),
                DIN_1988=standards_config.get('DIN_1988', {}),
                VDI_2067=standards_config.get('VDI_2067', {}),
                Local_Codes=standards_config.get('Local_Codes', {})
            )
            
            # Parse hierarchy levels
            hierarchy_levels_config = pipe_sizing_config.get('hierarchy_levels', {})
            hierarchy_levels = {}
            for level, config in hierarchy_levels_config.items():
                hierarchy_levels[int(level)] = HierarchyLevelConfig(
                    name=config.get('name', f'Level {level}'),
                    min_flow_kg_s=config.get('min_flow_kg_s', 0),
                    max_flow_kg_s=config.get('max_flow_kg_s', 100),
                    typical_diameter_mm=config.get('typical_diameter_mm', [50, 80, 100])
                )
            
            # Parse validation configuration
            validation_config = pipe_sizing_config.get('validation', {})
            validation = ValidationConfig(
                enable_validation=validation_config.get('enable_validation', True),
                compliance_threshold=validation_config.get('compliance_threshold', 0.95),
                critical_violation_threshold=validation_config.get('critical_violation_threshold', 0.0),
                warning_violation_threshold=validation_config.get('warning_violation_threshold', 0.1)
            )
            
            # Parse output configuration
            output_config = pipe_sizing_config.get('output', {})
            output = OutputConfig(
                export_enhanced_data=output_config.get('export_enhanced_data', True),
                export_validation_results=output_config.get('export_validation_results', True),
                export_cost_analysis=output_config.get('export_cost_analysis', True),
                export_performance_metrics=output_config.get('export_performance_metrics', True)
            )
            
            # Create enhanced configuration
            self.enhanced_config = EnhancedCHAConfig(
                pipe_sizing=pipe_sizing,
                main_pipes=main_pipes,
                distribution_pipes=distribution_pipes,
                service_connections=service_connections,
                standards=standards,
                hierarchy_levels=hierarchy_levels,
                validation=validation,
                output=output
            )
            
            print(f"✅ Enhanced configuration parsed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error parsing enhanced configuration: {e}")
            return False
    
    def get_pipe_sizing_config(self) -> Optional[PipeSizingConfig]:
        """Get pipe sizing configuration."""
        return self.enhanced_config.pipe_sizing if self.enhanced_config else None
    
    def get_pipe_type_config(self, pipe_type: str) -> Optional[PipeTypeConfig]:
        """Get pipe type configuration."""
        if not self.enhanced_config:
            return None
        
        if pipe_type == 'main_pipes':
            return self.enhanced_config.main_pipes
        elif pipe_type == 'distribution_pipes':
            return self.enhanced_config.distribution_pipes
        elif pipe_type == 'service_connections':
            return self.enhanced_config.service_connections
        else:
            return None
    
    def get_standards_config(self) -> Optional[StandardsConfig]:
        """Get standards configuration."""
        return self.enhanced_config.standards if self.enhanced_config else None
    
    def get_hierarchy_levels(self) -> Optional[Dict[int, HierarchyLevelConfig]]:
        """Get hierarchy levels configuration."""
        return self.enhanced_config.hierarchy_levels if self.enhanced_config else None
    
    def get_validation_config(self) -> Optional[ValidationConfig]:
        """Get validation configuration."""
        return self.enhanced_config.validation if self.enhanced_config else None
    
    def get_output_config(self) -> Optional[OutputConfig]:
        """Get output configuration."""
        return self.enhanced_config.output if self.enhanced_config else None
    
    def is_intelligent_sizing_enabled(self) -> bool:
        """Check if intelligent sizing is enabled."""
        return self.enhanced_config.pipe_sizing.enable_intelligent_sizing if self.enhanced_config else False
    
    def get_standard_diameters(self) -> List[int]:
        """Get standard pipe diameters."""
        return self.enhanced_config.pipe_sizing.standard_diameters if self.enhanced_config else []
    
    def get_cost_for_diameter(self, diameter_mm: int) -> float:
        """Get cost for specific diameter."""
        if not self.enhanced_config:
            return 0.0
        
        return self.enhanced_config.pipe_sizing.cost_per_meter.get(diameter_mm, 0.0)
    
    def get_water_properties(self) -> Dict[str, float]:
        """Get water properties."""
        if not self.enhanced_config:
            return {}
        
        return {
            'density_kg_m3': self.enhanced_config.pipe_sizing.water_density_kg_m3,
            'specific_heat_j_per_kgk': self.enhanced_config.pipe_sizing.water_specific_heat_j_per_kgk,
            'dynamic_viscosity_pa_s': self.enhanced_config.pipe_sizing.water_dynamic_viscosity_pa_s
        }
    
    def get_hydraulic_constraints(self) -> Dict[str, float]:
        """Get hydraulic constraints."""
        if not self.enhanced_config:
            return {}
        
        return {
            'max_velocity_ms': self.enhanced_config.pipe_sizing.max_velocity_ms,
            'min_velocity_ms': self.enhanced_config.pipe_sizing.min_velocity_ms,
            'max_pressure_drop_pa_per_m': self.enhanced_config.pipe_sizing.max_pressure_drop_pa_per_m
        }
    
    def export_enhanced_config(self, output_path: str) -> None:
        """
        Export enhanced configuration to JSON file.
        
        Args:
            output_path: Output file path
        """
        if not self.enhanced_config:
            print("❌ No enhanced configuration to export")
            return
        
        # Convert dataclasses to dictionaries
        config_dict = {
            'pipe_sizing': self.enhanced_config.pipe_sizing.__dict__,
            'main_pipes': self.enhanced_config.main_pipes.__dict__,
            'distribution_pipes': self.enhanced_config.distribution_pipes.__dict__,
            'service_connections': self.enhanced_config.service_connections.__dict__,
            'standards': {
                'EN_13941': self.enhanced_config.standards.EN_13941,
                'DIN_1988': self.enhanced_config.standards.DIN_1988,
                'VDI_2067': self.enhanced_config.standards.VDI_2067,
                'Local_Codes': self.enhanced_config.standards.Local_Codes
            },
            'hierarchy_levels': {
                str(level): level_config.__dict__ 
                for level, level_config in self.enhanced_config.hierarchy_levels.items()
            },
            'validation': self.enhanced_config.validation.__dict__,
            'output': self.enhanced_config.output.__dict__
        }
        
        with open(output_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        print(f"✅ Enhanced configuration exported to {output_path}")
    
    def print_configuration_summary(self) -> None:
        """Print configuration summary."""
        if not self.enhanced_config:
            print("❌ No enhanced configuration available")
            return
        
        print(f"\n📊 ENHANCED CONFIGURATION SUMMARY")
        print(f"=" * 50)
        print(f"📁 Configuration File: {self.config_path}")
        print(f"🔧 Intelligent Sizing: {self.enhanced_config.pipe_sizing.enable_intelligent_sizing}")
        print(f"📏 Standard Diameters: {len(self.enhanced_config.pipe_sizing.standard_diameters)}")
        print(f"💧 Water Properties:")
        print(f"   Density: {self.enhanced_config.pipe_sizing.water_density_kg_m3} kg/m³")
        print(f"   Specific Heat: {self.enhanced_config.pipe_sizing.water_specific_heat_j_per_kgk} J/kg·K")
        print(f"   Dynamic Viscosity: {self.enhanced_config.pipe_sizing.water_dynamic_viscosity_pa_s} Pa·s")
        print(f"")
        print(f"⚡ Hydraulic Constraints:")
        print(f"   Max Velocity: {self.enhanced_config.pipe_sizing.max_velocity_ms} m/s")
        print(f"   Min Velocity: {self.enhanced_config.pipe_sizing.min_velocity_ms} m/s")
        print(f"   Max Pressure Drop: {self.enhanced_config.pipe_sizing.max_pressure_drop_pa_per_m} Pa/m")
        print(f"")
        print(f"🏗️ Pipe Types Configured:")
        print(f"   Main Pipes: {self.enhanced_config.main_pipes.min_diameter_mm}-{self.enhanced_config.main_pipes.max_diameter_mm}mm")
        print(f"   Distribution Pipes: {self.enhanced_config.distribution_pipes.min_diameter_mm}-{self.enhanced_config.distribution_pipes.max_diameter_mm}mm")
        print(f"   Service Connections: {self.enhanced_config.service_connections.min_diameter_mm}-{self.enhanced_config.service_connections.max_diameter_mm}mm")
        print(f"")
        print(f"📊 Hierarchy Levels: {len(self.enhanced_config.hierarchy_levels)}")
        print(f"💰 Cost Model Diameters: {len(self.enhanced_config.pipe_sizing.cost_per_meter)}")
        print(f"✅ Validation Enabled: {self.enhanced_config.validation.enable_validation}")
        
        if self.validation_result:
            print(f"")
            print(f"🔍 VALIDATION STATUS:")
            print(f"   Valid: {self.validation_result.is_valid}")
            print(f"   Errors: {len(self.validation_result.errors)}")
            print(f"   Warnings: {len(self.validation_result.warnings)}")
            print(f"   Recommendations: {len(self.validation_result.recommendations)}")


# Example usage and testing
if __name__ == "__main__":
    # Create enhanced configuration loader
    config_loader = CHAEnhancedConfigLoader("configs/cha.yml")
    
    try:
        # Load configuration
        if not config_loader.load_configuration():
            print("❌ Failed to load configuration")
            exit(1)
        
        # Validate configuration
        if not config_loader.validate_configuration():
            print("❌ Failed to validate configuration")
            exit(1)
        
        # Parse enhanced configuration
        if not config_loader.parse_enhanced_configuration():
            print("❌ Failed to parse enhanced configuration")
            exit(1)
        
        # Print configuration summary
        config_loader.print_configuration_summary()
        
        # Test configuration access
        print(f"\n🧪 Testing configuration access...")
        print(f"   Intelligent sizing enabled: {config_loader.is_intelligent_sizing_enabled()}")
        print(f"   Standard diameters: {len(config_loader.get_standard_diameters())}")
        print(f"   Water properties: {config_loader.get_water_properties()}")
        print(f"   Hydraulic constraints: {config_loader.get_hydraulic_constraints()}")
        
        # Export enhanced configuration
        config_loader.export_enhanced_config("enhanced_config.json")
        
        print(f"\n🎉 Enhanced configuration loading completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in enhanced configuration loading: {e}")
        import traceback
        traceback.print_exc()
