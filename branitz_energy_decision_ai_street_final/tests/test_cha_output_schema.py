"""
Test suite for CHA Output Schema validation.

This module tests the CHA output schema to ensure it properly validates
physics-based simulation results with thermal analysis and standards compliance.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
import jsonschema
from jsonschema import validate, ValidationError

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

class TestCHAOutputSchema:
    """Test class for CHA output schema validation."""
    
    @pytest.fixture
    def schema(self):
        """Load the CHA output schema."""
        schema_path = Path(__file__).parent.parent / "schemas" / "cha_output.schema.json"
        with open(schema_path, 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def valid_cha_output(self):
        """Create a valid CHA output example."""
        return {
            "metadata": {
                "simulation_timestamp": "2024-01-15T10:30:00Z",
                "pandapipes_version": "0.8.0",
                "convergence_status": "converged",
                "total_iterations": 15,
                "simulation_duration_s": 45.2,
                "thermal_simulation_enabled": True,
                "auto_resize_enabled": True,
                "network_size": {
                    "junctions": 100,
                    "pipes": 150,
                    "sources": 1,
                    "sinks": 50
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
                    "mdot_kg_s": 25.5,
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
                    "mdot_kg_s": 25.5,
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
                "pump_kw": 12.5,
                "losses_mwh_a": 45.2,
                "dt_k": 30.0,
                "thermal_efficiency": 0.85,
                "total_flow_kg_s": 25.5,
                "network_length_km": 2.5,
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
                    "iterations_completed": 2,
                    "pipes_resized": 3,
                    "final_compliance": True,
                    "resize_history": [
                        {
                            "iteration": 1,
                            "violations_found": 5,
                            "pipes_resized": 3
                        },
                        {
                            "iteration": 2,
                            "violations_found": 0,
                            "pipes_resized": 0
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
                    "total_pump_power_w": 12500.0,
                    "total_pump_power_kw": 12.5,
                    "pump_efficiency": 0.75,
                    "pipe_details": [
                        {
                            "pipe_id": "pipe_1",
                            "pressure_drop_pa": 420.0,
                            "volumetric_flow_m3_s": 0.026,
                            "pump_power_w": 11000.0
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
                    "total_thermal_loss_w": 45200.0,
                    "total_thermal_loss_kw": 45.2,
                    "pipe_details": [
                        {
                            "pipe_id": "pipe_1",
                            "surface_area_m2": 94.2,
                            "heat_transfer_coeff": 0.6,
                            "delta_t_k": 69.2,
                            "thermal_loss_w": 39000.0
                        },
                        {
                            "pipe_id": "pipe_2",
                            "surface_area_m2": 11.8,
                            "heat_transfer_coeff": 0.6,
                            "delta_t_k": 55.0,
                            "thermal_loss_w": 6200.0
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
                            "thermal_loss_w": 39000.0
                        },
                        {
                            "pipe_id": "pipe_2",
                            "inlet_temp_c": 78.5,
                            "outlet_temp_c": 50.0,
                            "temp_drop_c": 28.5,
                            "thermal_loss_w": 6200.0
                        }
                    ]
                }
            }
        }
    
    def test_schema_validation_valid_data(self, schema, valid_cha_output):
        """Test that valid CHA output data passes schema validation."""
        try:
            validate(instance=valid_cha_output, schema=schema)
            assert True, "Valid data should pass schema validation"
        except ValidationError as e:
            pytest.fail(f"Valid data failed validation: {e.message}")
    
    def test_schema_validation_missing_required_fields(self, schema):
        """Test that missing required fields fail validation."""
        invalid_data = {
            "metadata": {
                "simulation_timestamp": "2024-01-15T10:30:00Z",
                "pandapipes_version": "0.8.0",
                "convergence_status": "converged"
            }
            # Missing nodes, pipes, kpis, compliance, crs, units
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        assert "required" in str(exc_info.value)
    
    def test_schema_validation_invalid_enum_values(self, schema, valid_cha_output):
        """Test that invalid enum values fail validation."""
        # Test invalid convergence status
        invalid_data = valid_cha_output.copy()
        invalid_data["metadata"]["convergence_status"] = "invalid_status"
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        assert "convergence_status" in str(exc_info.value)
    
    def test_schema_validation_invalid_node_type(self, schema, valid_cha_output):
        """Test that invalid node types fail validation."""
        invalid_data = valid_cha_output.copy()
        invalid_data["nodes"][0]["node_type"] = "invalid_type"
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        assert "node_type" in str(exc_info.value)
    
    def test_schema_validation_invalid_pipe_category(self, schema, valid_cha_output):
        """Test that invalid pipe categories fail validation."""
        invalid_data = valid_cha_output.copy()
        invalid_data["pipes"][0]["pipe_category"] = "invalid_category"
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        assert "pipe_category" in str(exc_info.value)
    
    def test_schema_validation_invalid_temperature_range(self, schema, valid_cha_output):
        """Test that temperatures outside valid range fail validation."""
        invalid_data = valid_cha_output.copy()
        invalid_data["nodes"][0]["t_c"] = 150.0  # Too high
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        assert "t_c" in str(exc_info.value)
    
    def test_schema_validation_invalid_diameter_range(self, schema, valid_cha_output):
        """Test that diameters outside valid range fail validation."""
        invalid_data = valid_cha_output.copy()
        invalid_data["pipes"][0]["dn_mm"] = 10.0  # Too small
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        assert "dn_mm" in str(exc_info.value)
    
    def test_schema_validation_invalid_velocity_range(self, schema, valid_cha_output):
        """Test that velocities outside valid range fail validation."""
        invalid_data = valid_cha_output.copy()
        invalid_data["pipes"][0]["v_ms"] = 5.0  # Too high
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        assert "v_ms" in str(exc_info.value)
    
    def test_schema_validation_invalid_pressure_drop_range(self, schema, valid_cha_output):
        """Test that pressure drops outside valid range fail validation."""
        invalid_data = valid_cha_output.copy()
        invalid_data["pipes"][0]["dp100m_pa"] = 2000.0  # Too high
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        assert "dp100m_pa" in str(exc_info.value)
    
    def test_schema_validation_invalid_thermal_efficiency_range(self, schema, valid_cha_output):
        """Test that thermal efficiency outside valid range fails validation."""
        invalid_data = valid_cha_output.copy()
        invalid_data["kpis"]["thermal_efficiency"] = 1.5  # Too high
        
        with pytest.raises(ValidationError) as exc_info:
            validate(instance=invalid_data, schema=schema)
        
        assert "thermal_efficiency" in str(exc_info.value)
    
    def test_schema_validation_compliance_violations(self, schema, valid_cha_output):
        """Test validation of compliance violations structure."""
        # Add a violation
        invalid_data = valid_cha_output.copy()
        invalid_data["compliance"]["violations"] = [
            {
                "type": "velocity",
                "severity": "warning",
                "pipe_id": "pipe_1",
                "value": 2.5,
                "limit": 2.0,
                "standard": "DIN_1988",
                "recommendation": "Increase pipe diameter"
            }
        ]
        
        try:
            validate(instance=invalid_data, schema=schema)
            assert True, "Valid violation data should pass validation"
        except ValidationError as e:
            pytest.fail(f"Valid violation data failed validation: {e.message}")
    
    def test_schema_validation_thermal_analysis(self, schema, valid_cha_output):
        """Test validation of thermal analysis structure."""
        try:
            validate(instance=valid_cha_output, schema=schema)
            assert True, "Valid thermal analysis data should pass validation"
        except ValidationError as e:
            pytest.fail(f"Valid thermal analysis data failed validation: {e.message}")
    
    def test_schema_validation_auto_resize_results(self, schema, valid_cha_output):
        """Test validation of auto-resize results structure."""
        try:
            validate(instance=valid_cha_output, schema=schema)
            assert True, "Valid auto-resize results should pass validation"
        except ValidationError as e:
            pytest.fail(f"Valid auto-resize results failed validation: {e.message}")
    
    def test_schema_validation_units_structure(self, schema, valid_cha_output):
        """Test validation of units structure."""
        try:
            validate(instance=valid_cha_output, schema=schema)
            assert True, "Valid units structure should pass validation"
        except ValidationError as e:
            pytest.fail(f"Valid units structure failed validation: {e.message}")
    
    def test_schema_validation_crs_structure(self, schema, valid_cha_output):
        """Test validation of CRS structure."""
        try:
            validate(instance=valid_cha_output, schema=schema)
            assert True, "Valid CRS structure should pass validation"
        except ValidationError as e:
            pytest.fail(f"Valid CRS structure failed validation: {e.message}")


def test_schema_file_exists():
    """Test that the schema file exists and is valid JSON."""
    schema_path = Path(__file__).parent.parent / "schemas" / "cha_output.schema.json"
    assert schema_path.exists(), "CHA output schema file should exist"
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    assert isinstance(schema, dict), "Schema should be a valid JSON object"
    assert "$schema" in schema, "Schema should have $schema property"
    assert "properties" in schema, "Schema should have properties"


def test_schema_required_fields():
    """Test that all required fields are defined in the schema."""
    schema_path = Path(__file__).parent.parent / "schemas" / "cha_output.schema.json"
    
    with open(schema_path, 'r') as f:
        schema = json.load(f)
    
    required_fields = schema.get("required", [])
    expected_required = ["metadata", "nodes", "pipes", "kpis", "compliance", "crs", "units"]
    
    for field in expected_required:
        assert field in required_fields, f"Required field '{field}' should be in schema"


if __name__ == "__main__":
    # Run basic tests if executed directly
    test_schema_file_exists()
    test_schema_required_fields()
    print("✅ Basic schema tests passed!")
