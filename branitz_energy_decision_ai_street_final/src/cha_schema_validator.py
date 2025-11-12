"""
CHA Output Schema Validator

This module provides utilities for validating CHA simulation outputs against
the defined JSON schema, ensuring data contracts are maintained.
"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")


class CHASchemaValidator:
    """
    Validator for CHA output data against the defined JSON schema.
    
    Ensures that all CHA simulation results conform to the established
    data contract for physics-based results with thermal analysis.
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the CHA schema validator.
        
        Args:
            schema_path: Path to the CHA output schema file. If None, uses default path.
        """
        if schema_path is None:
            schema_path = Path(__file__).parent.parent / "schemas" / "cha_output.schema.json"
        
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        self.validator = jsonschema.Draft202012Validator(self.schema)
    
    def _load_schema(self) -> Dict[str, Any]:
        """Load the CHA output schema from file."""
        try:
            with open(self.schema_path, 'r') as f:
                schema = json.load(f)
            print(f"✅ Loaded CHA output schema from {self.schema_path}")
            return schema
        except FileNotFoundError:
            raise FileNotFoundError(f"Schema file not found: {self.schema_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")
    
    def validate_cha_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate CHA output data against the schema.
        
        Args:
            data: CHA output data to validate
            
        Returns:
            Dict with validation results:
            - valid: bool - Whether data is valid
            - errors: List[str] - List of validation errors
            - warnings: List[str] - List of validation warnings
        """
        try:
            # Validate against schema
            self.validator.validate(data)
            
            # Additional custom validations
            warnings_list = self._perform_custom_validations(data)
            
            return {
                "valid": True,
                "errors": [],
                "warnings": warnings_list,
                "message": "CHA output data is valid"
            }
            
        except jsonschema.ValidationError as e:
            return {
                "valid": False,
                "errors": [str(e.message)],
                "warnings": [],
                "message": f"CHA output data validation failed: {e.message}"
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "warnings": [],
                "message": f"Unexpected validation error: {e}"
            }
    
    def _perform_custom_validations(self, data: Dict[str, Any]) -> List[str]:
        """
        Perform additional custom validations beyond JSON schema.
        
        Args:
            data: CHA output data to validate
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        # Check for reasonable value ranges
        if "kpis" in data:
            kpis = data["kpis"]
            
            # Check velocity limits
            if "v_max_ms" in kpis and kpis["v_max_ms"] > 2.5:
                warnings.append(f"High maximum velocity: {kpis['v_max_ms']:.2f} m/s (consider pipe sizing)")
            
            # Check pressure drop limits
            if "dp100m_max_pa" in kpis and kpis["dp100m_max_pa"] > 500:
                warnings.append(f"High pressure drop: {kpis['dp100m_max_pa']:.0f} Pa/100m (consider pipe sizing)")
            
            # Check temperature drop
            if "dt_k" in kpis:
                if kpis["dt_k"] < 25:
                    warnings.append(f"Low temperature drop: {kpis['dt_k']:.1f} K (may indicate insufficient thermal losses)")
                elif kpis["dt_k"] > 60:
                    warnings.append(f"High temperature drop: {kpis['dt_k']:.1f} K (may indicate excessive thermal losses)")
            
            # Check thermal efficiency
            if "thermal_efficiency" in kpis and kpis["thermal_efficiency"] < 0.7:
                warnings.append(f"Low thermal efficiency: {kpis['thermal_efficiency']:.2%} (consider insulation improvements)")
        
        # Check compliance status
        if "compliance" in data:
            compliance = data["compliance"]
            
            if compliance.get("overall_status") == "FAIL":
                violations = compliance.get("violations", [])
                critical_violations = [v for v in violations if v.get("severity") == "critical"]
                if critical_violations:
                    warnings.append(f"Critical violations found: {len(critical_violations)} (immediate action required)")
        
        # Check network size
        if "metadata" in data and "network_size" in data["metadata"]:
            network_size = data["metadata"]["network_size"]
            total_pipes = network_size.get("pipes", 0)
            total_junctions = network_size.get("junctions", 0)
            
            if total_pipes > 10000:
                warnings.append(f"Large network: {total_pipes} pipes (consider performance optimization)")
            
            if total_junctions > 5000:
                warnings.append(f"Large network: {total_junctions} junctions (consider performance optimization)")
        
        return warnings
    
    def validate_and_save(self, data: Dict[str, Any], output_path: str) -> Dict[str, Any]:
        """
        Validate CHA output data and save to file if valid.
        
        Args:
            data: CHA output data to validate and save
            output_path: Path to save the validated data
            
        Returns:
            Dict with validation and save results
        """
        # Validate data
        validation_result = self.validate_cha_output(data)
        
        if validation_result["valid"]:
            try:
                # Add validation metadata
                if "metadata" not in data:
                    data["metadata"] = {}
                
                data["metadata"]["schema_validation"] = {
                    "validated_at": datetime.now().isoformat(),
                    "schema_version": self.schema.get("$schema", "unknown"),
                    "validator_version": "1.0.0",
                    "validation_status": "PASS"
                }
                
                # Save to file
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)
                
                validation_result["saved"] = True
                validation_result["output_path"] = str(output_path)
                validation_result["message"] += f" and saved to {output_path}"
                
                print(f"✅ Validated and saved CHA output to {output_path}")
                
            except Exception as e:
                validation_result["saved"] = False
                validation_result["save_error"] = str(e)
                validation_result["message"] += f" but failed to save: {e}"
                
                print(f"❌ Validation passed but save failed: {e}")
        else:
            validation_result["saved"] = False
            print(f"❌ Validation failed: {validation_result['message']}")
        
        return validation_result
    
    def create_example_output(self) -> Dict[str, Any]:
        """
        Create an example CHA output that conforms to the schema.
        
        Returns:
            Example CHA output data
        """
        return {
            "metadata": {
                "simulation_timestamp": datetime.now().isoformat(),
                "pandapipes_version": "0.8.0",
                "convergence_status": "converged",
                "total_iterations": 12,
                "simulation_duration_s": 35.5,
                "thermal_simulation_enabled": True,
                "auto_resize_enabled": True,
                "network_size": {
                    "junctions": 50,
                    "pipes": 75,
                    "sources": 1,
                    "sinks": 25
                }
            },
            "nodes": [
                {
                    "id": "source_1",
                    "x": 456259.85,
                    "y": 5734163.40,
                    "p_bar": 6.0,
                    "t_c": 80.0,
                    "node_type": "source",
                    "mdot_kg_s": 15.5,
                    "elevation_m": 120.0
                },
                {
                    "id": "junction_1",
                    "x": 456300.0,
                    "y": 5734200.0,
                    "p_bar": 5.8,
                    "t_c": 78.5,
                    "node_type": "junction",
                    "elevation_m": 118.5
                },
                {
                    "id": "sink_1",
                    "x": 456350.0,
                    "y": 5734250.0,
                    "p_bar": 5.5,
                    "t_c": 50.0,
                    "node_type": "sink",
                    "mdot_kg_s": 0.5,
                    "elevation_m": 117.0
                }
            ],
            "pipes": [
                {
                    "id": "pipe_1",
                    "from_node": "source_1",
                    "to_node": "junction_1",
                    "length_m": 150.0,
                    "dn_mm": 200,
                    "v_ms": 1.2,
                    "dp100m_pa": 280.0,
                    "mdot_kg_s": 15.5,
                    "t_seg_c": 79.2,
                    "pipe_category": "mains",
                    "q_loss_Wm": 45.2,
                    "reynolds_number": 125000,
                    "friction_factor": 0.018,
                    "heat_transfer_coeff": 0.6
                },
                {
                    "id": "pipe_2",
                    "from_node": "junction_1",
                    "to_node": "sink_1",
                    "length_m": 75.0,
                    "dn_mm": 50,
                    "v_ms": 0.8,
                    "dp100m_pa": 320.0,
                    "mdot_kg_s": 0.5,
                    "t_seg_c": 65.0,
                    "pipe_category": "services",
                    "q_loss_Wm": 12.5,
                    "reynolds_number": 25000,
                    "friction_factor": 0.022,
                    "heat_transfer_coeff": 0.6
                }
            ],
            "kpis": {
                "v_max_ms": 1.8,
                "dp100m_max_pa": 350.0,
                "pump_kw": 8.5,
                "losses_mwh_a": 32.1,
                "dt_k": 30.0,
                "thermal_efficiency": 0.85,
                "total_flow_kg_s": 15.5,
                "network_length_km": 1.8,
                "supply_temp_c": 80.0,
                "return_temp_c": 50.0
            },
            "compliance": {
                "overall_status": "PASS",
                "standards_results": {
                    "EN_13941": "PASS",
                    "DIN_1988": "PASS",
                    "VDI_2067": "PASS"
                },
                "violations": [],
                "auto_resize_results": {
                    "iterations_completed": 1,
                    "pipes_resized": 2,
                    "final_compliance": True,
                    "resize_history": [
                        {
                            "iteration": 1,
                            "violations_found": 3,
                            "pipes_resized": 2
                        }
                    ]
                }
            },
            "crs": {
                "epsg": 25832,
                "name": "ETRS89 / UTM zone 32N",
                "units": "m"
            },
            "units": {
                "pressure": "bar",
                "temperature": "C",
                "flow_rate": "kg_s",
                "power": "kW",
                "energy": "MWh",
                "length": "m",
                "velocity": "m_s",
                "diameter": "mm"
            },
            "thermal_analysis": {
                "pump_power_analysis": {
                    "total_pump_power_w": 8500.0,
                    "total_pump_power_kw": 8.5,
                    "pump_efficiency": 0.75,
                    "pipe_details": [
                        {
                            "pipe_id": "pipe_1",
                            "pressure_drop_pa": 420.0,
                            "volumetric_flow_m3_s": 0.016,
                            "pump_power_w": 7000.0
                        },
                        {
                            "pipe_id": "pipe_2",
                            "pressure_drop_pa": 240.0,
                            "volumetric_flow_m3_s": 0.0005,
                            "pump_power_w": 1500.0
                        }
                    ]
                },
                "thermal_loss_analysis": {
                    "total_thermal_loss_w": 32100.0,
                    "total_thermal_loss_kw": 32.1,
                    "pipe_details": [
                        {
                            "pipe_id": "pipe_1",
                            "surface_area_m2": 94.2,
                            "heat_transfer_coeff": 0.6,
                            "delta_t_k": 69.2,
                            "thermal_loss_w": 28000.0
                        },
                        {
                            "pipe_id": "pipe_2",
                            "surface_area_m2": 11.8,
                            "heat_transfer_coeff": 0.6,
                            "delta_t_k": 55.0,
                            "thermal_loss_w": 4100.0
                        }
                    ]
                },
                "temperature_profiles": {
                    "network_temp_drop_c": 30.0,
                    "max_inlet_temp_c": 80.0,
                    "min_outlet_temp_c": 50.0,
                    "pipe_profiles": [
                        {
                            "pipe_id": "pipe_1",
                            "inlet_temp_c": 80.0,
                            "outlet_temp_c": 78.5,
                            "temp_drop_c": 1.5,
                            "thermal_loss_w": 28000.0
                        },
                        {
                            "pipe_id": "pipe_2",
                            "inlet_temp_c": 78.5,
                            "outlet_temp_c": 50.0,
                            "temp_drop_c": 28.5,
                            "thermal_loss_w": 4100.0
                        }
                    ]
                }
            }
        }
    
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded schema.
        
        Returns:
            Dict with schema information
        """
        return {
            "schema_path": str(self.schema_path),
            "schema_title": self.schema.get("title", "Unknown"),
            "schema_description": self.schema.get("description", "No description"),
            "required_fields": self.schema.get("required", []),
            "properties_count": len(self.schema.get("properties", {})),
            "schema_version": self.schema.get("$schema", "Unknown")
        }


# Example usage and testing
if __name__ == "__main__":
    print("🔍 CHA Schema Validator Test")
    print("=" * 50)
    
    # Initialize validator
    validator = CHASchemaValidator()
    
    # Get schema info
    schema_info = validator.get_schema_info()
    print(f"📋 Schema: {schema_info['schema_title']}")
    print(f"📝 Description: {schema_info['schema_description']}")
    print(f"📊 Properties: {schema_info['properties_count']}")
    print(f"✅ Required fields: {len(schema_info['required_fields'])}")
    
    # Create and validate example data
    print(f"\n🧪 Testing with example data...")
    example_data = validator.create_example_output()
    
    validation_result = validator.validate_cha_output(example_data)
    
    if validation_result["valid"]:
        print(f"✅ Validation: {validation_result['message']}")
        if validation_result["warnings"]:
            print(f"⚠️ Warnings ({len(validation_result['warnings'])}):")
            for warning in validation_result["warnings"]:
                print(f"   - {warning}")
    else:
        print(f"❌ Validation: {validation_result['message']}")
        for error in validation_result["errors"]:
            print(f"   - {error}")
    
    # Test save functionality
    print(f"\n💾 Testing save functionality...")
    save_result = validator.validate_and_save(example_data, "test_cha_output.json")
    
    if save_result["saved"]:
        print(f"✅ Save: {save_result['message']}")
    else:
        print(f"❌ Save: {save_result['message']}")
    
    print(f"\n🎉 CHA Schema Validator test completed!")
