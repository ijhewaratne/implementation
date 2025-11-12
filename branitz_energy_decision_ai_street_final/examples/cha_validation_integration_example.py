"""
CHA Validation Integration Example

This example demonstrates how the CHA validation system integrates with the
complete CHA workflow, providing comprehensive validation of simulation outputs
against engineering standards and data contracts.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from cha_validation import CHAValidationSystem
from cha_schema_validator import CHASchemaValidator


def create_realistic_cha_output():
    """Create a realistic CHA output with some intentional violations for demonstration."""
    return {
        "metadata": {
            "simulation_timestamp": datetime.now().isoformat(),
            "pandapipes_version": "0.8.0",
            "convergence_status": "converged",
            "total_iterations": 18,
            "simulation_duration_s": 67.3,
            "thermal_simulation_enabled": True,
            "auto_resize_enabled": True,
            "network_size": {
                "junctions": 150,
                "pipes": 225,
                "sources": 2,
                "sinks": 75
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
                "mdot_kg_s": 45.5,
                "elevation_m": 120.0
            },
            {
                "id": "source_2",
                "x": 456500.0,
                "y": 5734500.0,
                "p_bar": 6.0,
                "t_c": 80.0,
                "node_type": "source",
                "mdot_kg_s": 35.2,
                "elevation_m": 118.5
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
                "id": "junction_2",
                "x": 456400.0,
                "y": 5734300.0,
                "p_bar": 5.6,
                "t_c": 76.8,
                "node_type": "junction",
                "elevation_m": 117.8
            }
        ],
        "pipes": [
            # Main pipes - some with violations
            {
                "id": "main_1",
                "from_node": "source_1",
                "to_node": "junction_1",
                "length_m": 200.0,
                "dn_mm": 300,
                "v_ms": 1.8,  # Good velocity
                "dp100m_pa": 280.0,  # Good pressure drop
                "mdot_kg_s": 45.5,
                "t_seg_c": 79.2,
                "pipe_category": "mains",
                "q_loss_Wm": 65.2,
                "reynolds_number": 185000,
                "friction_factor": 0.016,
                "heat_transfer_coeff": 0.6
            },
            {
                "id": "main_2",
                "from_node": "source_2",
                "to_node": "junction_2",
                "length_m": 180.0,
                "dn_mm": 250,
                "v_ms": 2.8,  # VIOLATION: Too high velocity
                "dp100m_pa": 450.0,  # VIOLATION: Too high pressure drop
                "mdot_kg_s": 35.2,
                "t_seg_c": 78.8,
                "pipe_category": "mains",
                "q_loss_Wm": 58.7,
                "reynolds_number": 165000,
                "friction_factor": 0.018,
                "heat_transfer_coeff": 0.6
            },
            # Distribution pipes
            {
                "id": "dist_1",
                "from_node": "junction_1",
                "to_node": "junction_2",
                "length_m": 120.0,
                "dn_mm": 150,
                "v_ms": 1.5,  # Good velocity
                "dp100m_pa": 320.0,  # Good pressure drop
                "mdot_kg_s": 25.0,
                "t_seg_c": 77.5,
                "pipe_category": "distribution",
                "q_loss_Wm": 42.3,
                "reynolds_number": 125000,
                "friction_factor": 0.017,
                "heat_transfer_coeff": 0.6
            },
            # Service connections - some with violations
            {
                "id": "service_1",
                "from_node": "junction_2",
                "to_node": "sink_1",
                "length_m": 50.0,
                "dn_mm": 40,
                "v_ms": 0.8,  # Good velocity
                "dp100m_pa": 380.0,  # Good pressure drop
                "mdot_kg_s": 0.8,
                "t_seg_c": 65.0,
                "pipe_category": "services",
                "q_loss_Wm": 15.2,
                "reynolds_number": 32000,
                "friction_factor": 0.022,
                "heat_transfer_coeff": 0.6
            },
            {
                "id": "service_2",
                "from_node": "junction_2",
                "to_node": "sink_2",
                "length_m": 60.0,
                "dn_mm": 32,
                "v_ms": 2.2,  # VIOLATION: Too high velocity for service
                "dp100m_pa": 650.0,  # VIOLATION: Too high pressure drop
                "mdot_kg_s": 1.2,
                "t_seg_c": 62.5,
                "pipe_category": "services",
                "q_loss_Wm": 18.7,
                "reynolds_number": 45000,
                "friction_factor": 0.024,
                "heat_transfer_coeff": 0.6
            }
        ],
        "kpis": {
            "v_max_ms": 2.8,  # VIOLATION: Too high
            "dp100m_max_pa": 650.0,  # VIOLATION: Too high
            "pump_kw": 35.5,  # High pump power
            "losses_mwh_a": 125.8,  # High thermal losses
            "dt_k": 18.0,  # Low temperature drop
            "thermal_efficiency": 0.65,  # Low efficiency
            "total_flow_kg_s": 80.7,
            "network_length_km": 3.2,
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
                    "pipe_id": "main_2",
                    "value": 2.8,
                    "limit": 2.0,
                    "standard": "DIN_1988",
                    "recommendation": "Increase pipe diameter or reduce flow rate"
                },
                {
                    "type": "pressure_drop",
                    "severity": "critical",
                    "pipe_id": "main_2",
                    "value": 450.0,
                    "limit": 300.0,
                    "standard": "DIN_1988",
                    "recommendation": "Increase pipe diameter"
                },
                {
                    "type": "velocity",
                    "severity": "critical",
                    "pipe_id": "service_2",
                    "value": 2.2,
                    "limit": 1.5,
                    "standard": "DIN_1988",
                    "recommendation": "Increase pipe diameter or reduce flow rate"
                },
                {
                    "type": "pressure_drop",
                    "severity": "critical",
                    "pipe_id": "service_2",
                    "value": 650.0,
                    "limit": 500.0,
                    "standard": "DIN_1988",
                    "recommendation": "Increase pipe diameter"
                }
            ],
            "auto_resize_results": {
                "iterations_completed": 3,
                "pipes_resized": 4,
                "final_compliance": False,
                "resize_history": [
                    {
                        "iteration": 1,
                        "violations_found": 8,
                        "pipes_resized": 2
                    },
                    {
                        "iteration": 2,
                        "violations_found": 4,
                        "pipes_resized": 2
                    },
                    {
                        "iteration": 3,
                        "violations_found": 4,
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
                "total_pump_power_w": 35500.0,
                "total_pump_power_kw": 35.5,
                "pump_efficiency": 0.75,
                "pipe_details": [
                    {
                        "pipe_id": "main_1",
                        "pressure_drop_pa": 560.0,
                        "volumetric_flow_m3_s": 0.047,
                        "pump_power_w": 15000.0
                    },
                    {
                        "pipe_id": "main_2",
                        "pressure_drop_pa": 810.0,
                        "volumetric_flow_m3_s": 0.036,
                        "pump_power_w": 18000.0
                    },
                    {
                        "pipe_id": "dist_1",
                        "pressure_drop_pa": 384.0,
                        "volumetric_flow_m3_s": 0.026,
                        "pump_power_w": 8000.0
                    },
                    {
                        "pipe_id": "service_1",
                        "pressure_drop_pa": 190.0,
                        "volumetric_flow_m3_s": 0.0008,
                        "pump_power_w": 1200.0
                    },
                    {
                        "pipe_id": "service_2",
                        "pressure_drop_pa": 390.0,
                        "volumetric_flow_m3_s": 0.0012,
                        "pump_power_w": 3300.0
                    }
                ]
            },
            "thermal_loss_analysis": {
                "total_thermal_loss_w": 125800.0,
                "total_thermal_loss_kw": 125.8,
                "pipe_details": [
                    {
                        "pipe_id": "main_1",
                        "surface_area_m2": 188.5,
                        "heat_transfer_coeff": 0.6,
                        "delta_t_k": 69.2,
                        "thermal_loss_w": 45000.0
                    },
                    {
                        "pipe_id": "main_2",
                        "surface_area_m2": 141.4,
                        "heat_transfer_coeff": 0.6,
                        "delta_t_k": 68.8,
                        "thermal_loss_w": 35000.0
                    },
                    {
                        "pipe_id": "dist_1",
                        "surface_area_m2": 56.5,
                        "heat_transfer_coeff": 0.6,
                        "delta_t_k": 67.5,
                        "thermal_loss_w": 18000.0
                    },
                    {
                        "pipe_id": "service_1",
                        "surface_area_m2": 6.3,
                        "heat_transfer_coeff": 0.6,
                        "delta_t_k": 55.0,
                        "thermal_loss_w": 15000.0
                    },
                    {
                        "pipe_id": "service_2",
                        "surface_area_m2": 6.0,
                        "heat_transfer_coeff": 0.6,
                        "delta_t_k": 52.5,
                        "thermal_loss_w": 12800.0
                    }
                ]
            },
            "temperature_profiles": {
                "network_temp_drop_c": 18.0,
                "max_inlet_temp_c": 80.0,
                "min_outlet_temp_c": 50.0,
                "pipe_profiles": [
                    {
                        "pipe_id": "main_1",
                        "inlet_temp_c": 80.0,
                        "outlet_temp_c": 78.5,
                        "temp_drop_c": 1.5,
                        "thermal_loss_w": 45000.0
                    },
                    {
                        "pipe_id": "main_2",
                        "inlet_temp_c": 80.0,
                        "outlet_temp_c": 76.8,
                        "temp_drop_c": 3.2,
                        "thermal_loss_w": 35000.0
                    },
                    {
                        "pipe_id": "dist_1",
                        "inlet_temp_c": 78.5,
                        "outlet_temp_c": 77.5,
                        "temp_drop_c": 1.0,
                        "thermal_loss_w": 18000.0
                    },
                    {
                        "pipe_id": "service_1",
                        "inlet_temp_c": 77.5,
                        "outlet_temp_c": 65.0,
                        "temp_drop_c": 12.5,
                        "thermal_loss_w": 15000.0
                    },
                    {
                        "pipe_id": "service_2",
                        "inlet_temp_c": 77.5,
                        "outlet_temp_c": 62.5,
                        "temp_drop_c": 15.0,
                        "thermal_loss_w": 12800.0
                    }
                ]
            }
        }
    }


def demonstrate_validation_workflow():
    """Demonstrate the complete CHA validation workflow."""
    print("🚀 CHA Validation Integration Example")
    print("=" * 60)
    
    # Step 1: Initialize validation system
    print("Step 1: Initializing CHA Validation System...")
    validator = CHAValidationSystem()
    print("✅ Validation system initialized")
    
    # Step 2: Create realistic CHA output with violations
    print("\nStep 2: Creating realistic CHA output with intentional violations...")
    cha_output = create_realistic_cha_output()
    print("✅ CHA output created with intentional violations for demonstration")
    
    # Step 3: Create test directory and save output
    print("\nStep 3: Setting up test environment...")
    test_dir = Path("examples/test_cha_outputs")
    test_dir.mkdir(exist_ok=True)
    
    output_file = test_dir / "realistic_cha_output.json"
    with open(output_file, 'w') as f:
        json.dump(cha_output, f, indent=2, default=str)
    
    print(f"✅ Test output saved to {output_file}")
    
    # Step 4: Run comprehensive validation
    print("\nStep 4: Running comprehensive validation...")
    results = validator.run_complete_validation(
        str(test_dir), 
        "examples/validation_results.json"
    )
    
    # Step 5: Display validation results
    print("\nStep 5: Validation Results Summary")
    print("-" * 40)
    print(f"Files validated: {results['validated_files']}")
    print(f"Total violations: {results['total_violations']}")
    print(f"Success rate: {results['summary']['success_rate']:.1%}")
    
    # Step 6: Display standards compliance
    print("\nStep 6: Standards Compliance Results")
    print("-" * 40)
    standards_compliance = results['summary']['standards_compliance']
    for standard, compliance in standards_compliance.items():
        total = sum(compliance.values())
        pass_rate = compliance.get('PASS', 0) / total if total > 0 else 0
        print(f"{standard}:")
        print(f"  Pass: {compliance.get('PASS', 0)} ({pass_rate:.1%})")
        print(f"  Fail: {compliance.get('FAIL', 0)}")
        print(f"  Warning: {compliance.get('WARNING', 0)}")
    
    # Step 7: Display specific violations
    print("\nStep 7: Specific Violations Found")
    print("-" * 40)
    file_results = results['file_results']
    for file_name, file_result in file_results.items():
        if file_result.get('total_violations', 0) > 0:
            print(f"\n{file_name}:")
            compliance = file_result.get('standards_compliance', {})
            violations = compliance.get('violations', [])
            
            for violation in violations[:5]:  # Show first 5 violations
                print(f"  - {violation.get('type', 'unknown')}: {violation.get('value', 'N/A')} > {violation.get('limit', 'N/A')} ({violation.get('standard', 'unknown')})")
                print(f"    Recommendation: {violation.get('recommendation', 'N/A')}")
            
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more violations")
    
    # Step 8: Display compliance report
    print("\nStep 8: Compliance Report")
    print("-" * 40)
    compliance_report = results['compliance_report']
    print(compliance_report)
    
    # Step 9: Demonstrate schema validation
    print("\nStep 9: Schema Validation Demonstration")
    print("-" * 40)
    schema_validator = CHASchemaValidator()
    schema_result = schema_validator.validate_cha_output(cha_output)
    
    print(f"Schema validation: {'PASS' if schema_result['valid'] else 'FAIL'}")
    if schema_result['warnings']:
        print("Schema warnings:")
        for warning in schema_result['warnings']:
            print(f"  - {warning}")
    
    # Step 10: Demonstrate individual validation methods
    print("\nStep 10: Individual Validation Methods")
    print("-" * 40)
    
    # Standards compliance
    compliance_result = validator.check_standards_compliance(cha_output)
    print(f"Standards compliance: {compliance_result['overall_status']}")
    print(f"Total violations: {len(compliance_result['violations'])}")
    
    # Performance validation
    performance_result = validator._validate_performance_criteria(cha_output)
    print(f"Performance validation: {performance_result['status']}")
    print(f"Performance violations: {len(performance_result['violations'])}")
    
    # Data quality validation
    quality_result = validator._validate_data_quality(cha_output)
    print(f"Data quality: {quality_result['status']}")
    print(f"Quality issues: {len(quality_result['issues'])}")
    
    print("\n🎉 CHA Validation Integration Example completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Schema validation against JSON schema contract")
    print("✅ Engineering standards compliance (EN 13941, DIN 1988, VDI 2067)")
    print("✅ Performance criteria validation")
    print("✅ Data quality validation")
    print("✅ Comprehensive compliance reporting")
    print("✅ Violation detection and recommendations")
    print("✅ Export functionality for results and reports")
    print("✅ Integration with CHA workflow")


if __name__ == "__main__":
    demonstrate_validation_workflow()
