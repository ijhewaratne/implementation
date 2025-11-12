"""
Test suite for CHA Validation System.

This module tests the comprehensive validation system for CHA simulation outputs,
including schema validation, standards compliance, and performance criteria.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent / "src"))

from cha_validation import CHAValidationSystem


class TestCHAValidationSystem:
    """Test class for CHA validation system."""
    
    @pytest.fixture
    def validation_system(self):
        """Create a CHA validation system instance."""
        return CHAValidationSystem()
    
    @pytest.fixture
    def valid_cha_data(self, validation_system):
        """Create valid CHA data for testing."""
        return validation_system.schema_validator.create_example_output()
    
    @pytest.fixture
    def invalid_cha_data(self):
        """Create invalid CHA data with violations for testing."""
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
                }
            ],
            "pipes": [
                {
                    "id": "pipe_1",
                    "from_node": "source_1",
                    "to_node": "junction_1",
                    "length_m": 150.0,
                    "dn_mm": 200,
                    "v_ms": 3.5,  # Violation: too high velocity
                    "dp100m_pa": 800.0,  # Violation: too high pressure drop
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
                    "v_ms": 0.05,  # Violation: too low velocity
                    "dp100m_pa": 50.0,  # Very low pressure drop
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
                "v_max_ms": 3.5,  # Violation: too high
                "dp100m_max_pa": 800.0,  # Violation: too high
                "pump_kw": 25.0,  # High pump power
                "losses_mwh_a": 150.0,  # High thermal losses
                "dt_k": 15.0,  # Low temperature drop
                "thermal_efficiency": 0.5,  # Low efficiency
                "total_flow_kg_s": 25.5,
                "network_length_km": 2.5,
                "supply_temp_c": 80.0,
                "return_temp_c": 50.0
            },
            "compliance": {
                "overall_status": "FAIL",
                "standards_results": {
                    "EN_13941": "FAIL",
                    "DIN_1988": "FAIL",
                    "VDI_2067": "WARNING"
                },
                "violations": [
                    {
                        "type": "velocity",
                        "severity": "critical",
                        "pipe_id": "pipe_1",
                        "value": 3.5,
                        "limit": 2.0,
                        "standard": "DIN_1988",
                        "recommendation": "Increase pipe diameter or reduce flow rate"
                    }
                ],
                "auto_resize_results": {
                    "iterations_completed": 3,
                    "pipes_resized": 5,
                    "final_compliance": False,
                    "resize_history": []
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
                    "total_pump_power_w": 25000.0,
                    "total_pump_power_kw": 25.0,
                    "pump_efficiency": 0.75,
                    "pipe_details": []
                },
                "thermal_loss_analysis": {
                    "total_thermal_loss_w": 150000.0,
                    "total_thermal_loss_kw": 150.0,
                    "pipe_details": []
                },
                "temperature_profiles": {
                    "network_temp_drop_c": 15.0,
                    "max_inlet_temp_c": 80.0,
                    "min_outlet_temp_c": 50.0,
                    "pipe_profiles": []
                }
            }
        }
    
    def test_validation_system_initialization(self, validation_system):
        """Test that the validation system initializes correctly."""
        assert validation_system is not None
        assert validation_system.schema_validator is not None
        assert validation_system.standards_limits is not None
        assert "EN_13941" in validation_system.standards_limits
        assert "DIN_1988" in validation_system.standards_limits
        assert "VDI_2067" in validation_system.standards_limits
    
    def test_validate_cha_outputs_valid_data(self, validation_system, valid_cha_data):
        """Test validation with valid CHA data."""
        # Create temporary directory with valid data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write valid data to file
            valid_file = temp_path / "valid_cha_output.json"
            with open(valid_file, 'w') as f:
                json.dump(valid_cha_data, f, indent=2, default=str)
            
            # Run validation
            results = validation_system.validate_cha_outputs(str(temp_path))
            
            # Check results
            assert results["status"] != "error"
            assert results["validated_files"] == 1
            assert results["total_violations"] == 0
            assert "valid_cha_output.json" in results["file_results"]
            
            file_result = results["file_results"]["valid_cha_output.json"]
            assert file_result["status"] == "valid"
    
    def test_validate_cha_outputs_invalid_data(self, validation_system, invalid_cha_data):
        """Test validation with invalid CHA data containing violations."""
        # Create temporary directory with invalid data
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write invalid data to file
            invalid_file = temp_path / "invalid_cha_output.json"
            with open(invalid_file, 'w') as f:
                json.dump(invalid_cha_data, f, indent=2, default=str)
            
            # Run validation
            results = validation_system.validate_cha_outputs(str(temp_path))
            
            # Check results
            assert results["status"] != "error"
            assert results["validated_files"] == 1
            assert results["total_violations"] > 0
            assert "invalid_cha_output.json" in results["file_results"]
            
            file_result = results["file_results"]["invalid_cha_output.json"]
            assert file_result["status"] == "valid"  # Schema validation passes
            assert file_result["total_violations"] > 0  # But has standards violations
    
    def test_check_standards_compliance(self, validation_system, invalid_cha_data):
        """Test standards compliance checking."""
        compliance_result = validation_system.check_standards_compliance(invalid_cha_data)
        
        assert compliance_result["overall_status"] in ["PASS", "FAIL", "WARNING"]
        assert "standards_results" in compliance_result
        assert "violations" in compliance_result
        assert "summary" in compliance_result
        
        # Check that violations were found
        assert len(compliance_result["violations"]) > 0
        
        # Check standards results
        standards_results = compliance_result["standards_results"]
        assert "EN_13941" in standards_results
        assert "DIN_1988" in standards_results
        assert "VDI_2067" in standards_results
    
    def test_generate_compliance_report(self, validation_system, invalid_cha_data):
        """Test compliance report generation."""
        # Create validation results
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write invalid data to file
            invalid_file = temp_path / "test_cha_output.json"
            with open(invalid_file, 'w') as f:
                json.dump(invalid_cha_data, f, indent=2, default=str)
            
            # Run validation
            results = validation_system.validate_cha_outputs(str(temp_path))
            
            # Generate compliance report
            report = validation_system.generate_compliance_report(results)
            
            # Check report content
            assert isinstance(report, str)
            assert "CHA SIMULATION COMPLIANCE REPORT" in report
            assert "EXECUTIVE SUMMARY" in report
            assert "STANDARDS COMPLIANCE" in report
            assert "FILE-BY-FILE RESULTS" in report
            assert "RECOMMENDATIONS" in report
    
    def test_export_validation_results(self, validation_system, invalid_cha_data):
        """Test validation results export."""
        # Create validation results
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write invalid data to file
            invalid_file = temp_path / "test_cha_output.json"
            with open(invalid_file, 'w') as f:
                json.dump(invalid_cha_data, f, indent=2, default=str)
            
            # Run validation
            results = validation_system.validate_cha_outputs(str(temp_path))
            
            # Export results
            export_path = temp_path / "exported_results.json"
            success = validation_system.export_validation_results(results, str(export_path))
            
            # Check export
            assert success is True
            assert export_path.exists()
            
            # Check exported content
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            
            assert "export_timestamp" in exported_data
            assert "validation_results" in exported_data
    
    def test_run_complete_validation(self, validation_system, invalid_cha_data):
        """Test complete validation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Write invalid data to file
            invalid_file = temp_path / "test_cha_output.json"
            with open(invalid_file, 'w') as f:
                json.dump(invalid_cha_data, f, indent=2, default=str)
            
            # Run complete validation
            export_path = temp_path / "complete_results.json"
            results = validation_system.run_complete_validation(str(temp_path), str(export_path))
            
            # Check results
            assert "validation_timestamp" in results
            assert "validated_files" in results
            assert "compliance_report" in results
            
            # Check that files were created
            assert export_path.exists()
            report_path = temp_path / "compliance_report.txt"
            assert report_path.exists()
    
    def test_standards_limits_configuration(self, validation_system):
        """Test that standards limits are properly configured."""
        standards = validation_system.standards_limits
        
        # Check EN 13941
        en_13941 = standards["EN_13941"]
        assert "max_velocity_ms" in en_13941
        assert "max_pressure_drop_pa_per_m" in en_13941
        assert en_13941["max_velocity_ms"] == 2.0
        assert en_13941["max_pressure_drop_pa_per_m"] == 500
        
        # Check DIN 1988
        din_1988 = standards["DIN_1988"]
        assert "main_pipes_velocity_ms" in din_1988
        assert "distribution_velocity_ms" in din_1988
        assert "service_velocity_ms" in din_1988
        assert din_1988["main_pipes_velocity_ms"] == 2.0
        assert din_1988["service_velocity_ms"] == 1.5
        
        # Check VDI 2067
        vdi_2067 = standards["VDI_2067"]
        assert "max_thermal_loss_kw_per_km" in vdi_2067
        assert "min_thermal_efficiency" in vdi_2067
        assert vdi_2067["min_thermal_efficiency"] == 0.7
    
    def test_performance_validation(self, validation_system, invalid_cha_data):
        """Test performance criteria validation."""
        performance_result = validation_system._validate_performance_criteria(invalid_cha_data)
        
        assert "status" in performance_result
        assert "violations" in performance_result
        assert "metrics" in performance_result
        
        # Check that performance violations were detected
        assert len(performance_result["violations"]) > 0
        
        # Check metrics
        metrics = performance_result["metrics"]
        assert "specific_pump_power" in metrics or "specific_thermal_loss" in metrics
    
    def test_data_quality_validation(self, validation_system, valid_cha_data):
        """Test data quality validation."""
        quality_result = validation_system._validate_data_quality(valid_cha_data)
        
        assert "status" in quality_result
        assert "issues" in quality_result
        assert "completeness" in quality_result
        
        # For valid data, should have no issues
        assert quality_result["status"] == "PASS"
        assert len(quality_result["issues"]) == 0
        
        # Check completeness
        completeness = quality_result["completeness"]
        assert "nodes" in completeness
        assert "pipes" in completeness


def test_validation_system_integration():
    """Test integration between validation system components."""
    # Initialize system
    validator = CHAValidationSystem()
    
    # Create test data
    test_data = validator.schema_validator.create_example_output()
    
    # Test schema validation
    schema_result = validator.schema_validator.validate_cha_output(test_data)
    assert schema_result["valid"] is True
    
    # Test standards compliance
    compliance_result = validator.check_standards_compliance(test_data)
    assert compliance_result["overall_status"] in ["PASS", "FAIL", "WARNING"]
    
    # Test performance validation
    performance_result = validator._validate_performance_criteria(test_data)
    assert "status" in performance_result
    
    # Test data quality validation
    quality_result = validator._validate_data_quality(test_data)
    assert "status" in quality_result


if __name__ == "__main__":
    # Run basic tests if executed directly
    test_validation_system_integration()
    print("✅ Basic validation system tests passed!")
