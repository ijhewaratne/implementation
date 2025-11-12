"""
CHA Validation System

This module provides comprehensive validation of CHA simulation outputs against
engineering standards, data contracts, and performance criteria. It integrates
with the schema validation system and provides detailed compliance reporting.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import warnings

# Import the schema validator
try:
    from .cha_schema_validator import CHASchemaValidator
except ImportError:
    from cha_schema_validator import CHASchemaValidator

warnings.filterwarnings("ignore")


class CHAValidationSystem:
    """
    Comprehensive validation system for CHA simulation outputs.
    
    Provides validation against:
    - JSON schema contracts
    - Engineering standards (EN 13941, DIN 1988, VDI 2067)
    - Performance criteria
    - Data quality checks
    """
    
    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the CHA validation system.
        
        Args:
            schema_path: Path to the CHA output schema file
        """
        self.schema_validator = CHASchemaValidator(schema_path)
        self.validation_results = {}
        self.compliance_reports = {}
        
        # Engineering standards limits
        self.standards_limits = {
            'EN_13941': {
                'max_velocity_ms': 2.0,
                'max_pressure_drop_pa_per_m': 500,
                'min_velocity_ms': 0.1,
                'temperature_range_c': (40, 90),
                'pressure_range_bar': (2, 16)
            },
            'DIN_1988': {
                'main_pipes_velocity_ms': 2.0,
                'distribution_velocity_ms': 2.0,
                'service_velocity_ms': 1.5,
                'main_pipes_pressure_drop_pa_per_m': 300,
                'distribution_pressure_drop_pa_per_m': 400,
                'service_pressure_drop_pa_per_m': 500
            },
            'VDI_2067': {
                'max_thermal_loss_kw_per_km': 50,
                'min_thermal_efficiency': 0.7,
                'max_temperature_drop_k': 50,
                'min_temperature_drop_k': 25
            }
        }
        
        print("✅ CHA Validation System initialized")
    
    def validate_cha_outputs(self, output_dir: str) -> Dict[str, Any]:
        """
        Validate all CHA outputs in the specified directory.
        
        Args:
            output_dir: Directory containing CHA output files
            
        Returns:
            Dict with comprehensive validation results
        """
        output_path = Path(output_dir)
        if not output_path.exists():
            return {
                "status": "error",
                "message": f"Output directory not found: {output_dir}",
                "validated_files": 0,
                "validation_results": {}
            }
        
        print(f"🔍 Validating CHA outputs in {output_dir}")
        
        validation_results = {
            "validation_timestamp": datetime.now().isoformat(),
            "output_directory": str(output_path),
            "validated_files": 0,
            "total_violations": 0,
            "standards_compliance": {},
            "file_results": {},
            "summary": {}
        }
        
        # Find CHA output files
        cha_files = self._find_cha_output_files(output_path)
        
        if not cha_files:
            print("⚠️ No CHA output files found")
            return validation_results
        
        print(f"📁 Found {len(cha_files)} CHA output files")
        
        # Validate each file
        for file_path in cha_files:
            print(f"🔍 Validating {file_path.name}...")
            
            try:
                file_result = self._validate_single_file(file_path)
                validation_results["file_results"][file_path.name] = file_result
                validation_results["validated_files"] += 1
                validation_results["total_violations"] += file_result.get("total_violations", 0)
                
                if file_result["status"] == "valid":
                    print(f"✅ {file_path.name}: Valid")
                else:
                    print(f"❌ {file_path.name}: {file_result['message']}")
                    
            except Exception as e:
                print(f"❌ {file_path.name}: Validation error - {e}")
                validation_results["file_results"][file_path.name] = {
                    "status": "error",
                    "message": str(e),
                    "validated_at": datetime.now().isoformat()
                }
        
        # Generate summary
        validation_results["summary"] = self._generate_validation_summary(validation_results)
        
        # Store results
        self.validation_results = validation_results
        
        print(f"✅ Validation completed: {validation_results['validated_files']} files, {validation_results['total_violations']} violations")
        
        return validation_results
    
    def _find_cha_output_files(self, output_path: Path) -> List[Path]:
        """Find CHA output files in the directory."""
        cha_files = []
        
        # Look for JSON files that might contain CHA outputs
        for pattern in ["*.json", "cha_*.json", "*_cha_*.json"]:
            cha_files.extend(output_path.glob(pattern))
        
        # Look for specific CHA output files
        specific_files = [
            "cha_output.json",
            "cha_results.json",
            "cha_simulation_results.json",
            "cha_kpis.json"
        ]
        
        for filename in specific_files:
            file_path = output_path / filename
            if file_path.exists():
                cha_files.append(file_path)
        
        # Remove duplicates and return
        return list(set(cha_files))
    
    def _validate_single_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Validate a single CHA output file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dict with validation results for the file
        """
        try:
            # Load the file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Schema validation
            schema_result = self.schema_validator.validate_cha_output(data)
            
            # Standards compliance validation
            standards_result = self.check_standards_compliance(data)
            
            # Performance validation
            performance_result = self._validate_performance_criteria(data)
            
            # Data quality validation
            quality_result = self._validate_data_quality(data)
            
            # Combine results
            file_result = {
                "status": "valid" if schema_result["valid"] else "invalid",
                "validated_at": datetime.now().isoformat(),
                "file_path": str(file_path),
                "file_size_bytes": file_path.stat().st_size,
                "schema_validation": schema_result,
                "standards_compliance": standards_result,
                "performance_validation": performance_result,
                "data_quality": quality_result,
                "total_violations": (
                    len(schema_result.get("errors", [])) +
                    len(standards_result.get("violations", [])) +
                    len(performance_result.get("violations", [])) +
                    len(quality_result.get("issues", []))
                )
            }
            
            return file_result
            
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON: {e}",
                "validated_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Validation error: {e}",
                "validated_at": datetime.now().isoformat()
            }
    
    def check_standards_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check compliance with engineering standards.
        
        Args:
            data: CHA output data to validate
            
        Returns:
            Dict with standards compliance results
        """
        compliance_result = {
            "overall_status": "PASS",
            "standards_results": {},
            "violations": [],
            "summary": {}
        }
        
        # Check each standard
        for standard_name, limits in self.standards_limits.items():
            standard_result = self._check_single_standard(data, standard_name, limits)
            compliance_result["standards_results"][standard_name] = standard_result["status"]
            compliance_result["violations"].extend(standard_result["violations"])
        
        # Determine overall status
        if any(result == "FAIL" for result in compliance_result["standards_results"].values()):
            compliance_result["overall_status"] = "FAIL"
        elif any(result == "WARNING" for result in compliance_result["standards_results"].values()):
            compliance_result["overall_status"] = "WARNING"
        
        # Generate summary
        compliance_result["summary"] = {
            "total_violations": len(compliance_result["violations"]),
            "critical_violations": len([v for v in compliance_result["violations"] if v.get("severity") == "critical"]),
            "warning_violations": len([v for v in compliance_result["violations"] if v.get("severity") == "warning"]),
            "standards_passed": sum(1 for status in compliance_result["standards_results"].values() if status == "PASS")
        }
        
        return compliance_result
    
    def _check_single_standard(self, data: Dict[str, Any], standard_name: str, limits: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with a single engineering standard."""
        violations = []
        status = "PASS"
        
        if "pipes" not in data:
            return {"status": "ERROR", "violations": [], "message": "No pipe data found"}
        
        pipes = data["pipes"]
        
        for pipe in pipes:
            pipe_id = pipe.get("id", "unknown")
            pipe_category = pipe.get("pipe_category", "unknown")
            
            # Check velocity limits
            if "v_ms" in pipe:
                velocity = pipe["v_ms"]
                
                if standard_name == "DIN_1988":
                    if pipe_category == "mains" and velocity > limits["main_pipes_velocity_ms"]:
                        violations.append({
                            "type": "velocity",
                            "severity": "critical",
                            "pipe_id": pipe_id,
                            "value": velocity,
                            "limit": limits["main_pipes_velocity_ms"],
                            "standard": standard_name,
                            "recommendation": "Increase pipe diameter or reduce flow rate"
                        })
                        status = "FAIL"
                    elif pipe_category == "distribution" and velocity > limits["distribution_velocity_ms"]:
                        violations.append({
                            "type": "velocity",
                            "severity": "critical",
                            "pipe_id": pipe_id,
                            "value": velocity,
                            "limit": limits["distribution_velocity_ms"],
                            "standard": standard_name,
                            "recommendation": "Increase pipe diameter or reduce flow rate"
                        })
                        status = "FAIL"
                    elif pipe_category == "services" and velocity > limits["service_velocity_ms"]:
                        violations.append({
                            "type": "velocity",
                            "severity": "critical",
                            "pipe_id": pipe_id,
                            "value": velocity,
                            "limit": limits["service_velocity_ms"],
                            "standard": standard_name,
                            "recommendation": "Increase pipe diameter or reduce flow rate"
                        })
                        status = "FAIL"
                
                elif standard_name == "EN_13941":
                    if velocity > limits["max_velocity_ms"]:
                        violations.append({
                            "type": "velocity",
                            "severity": "critical",
                            "pipe_id": pipe_id,
                            "value": velocity,
                            "limit": limits["max_velocity_ms"],
                            "standard": standard_name,
                            "recommendation": "Increase pipe diameter or reduce flow rate"
                        })
                        status = "FAIL"
                    elif velocity < limits["min_velocity_ms"]:
                        violations.append({
                            "type": "velocity",
                            "severity": "warning",
                            "pipe_id": pipe_id,
                            "value": velocity,
                            "limit": limits["min_velocity_ms"],
                            "standard": standard_name,
                            "recommendation": "Consider reducing pipe diameter"
                        })
                        if status == "PASS":
                            status = "WARNING"
            
            # Check pressure drop limits
            if "dp100m_pa" in pipe:
                pressure_drop = pipe["dp100m_pa"]
                
                if standard_name == "DIN_1988":
                    if pipe_category == "mains" and pressure_drop > limits["main_pipes_pressure_drop_pa_per_m"]:
                        violations.append({
                            "type": "pressure_drop",
                            "severity": "critical",
                            "pipe_id": pipe_id,
                            "value": pressure_drop,
                            "limit": limits["main_pipes_pressure_drop_pa_per_m"],
                            "standard": standard_name,
                            "recommendation": "Increase pipe diameter"
                        })
                        status = "FAIL"
                    elif pipe_category == "distribution" and pressure_drop > limits["distribution_pressure_drop_pa_per_m"]:
                        violations.append({
                            "type": "pressure_drop",
                            "severity": "critical",
                            "pipe_id": pipe_id,
                            "value": pressure_drop,
                            "limit": limits["distribution_pressure_drop_pa_per_m"],
                            "standard": standard_name,
                            "recommendation": "Increase pipe diameter"
                        })
                        status = "FAIL"
                    elif pipe_category == "services" and pressure_drop > limits["service_pressure_drop_pa_per_m"]:
                        violations.append({
                            "type": "pressure_drop",
                            "severity": "critical",
                            "pipe_id": pipe_id,
                            "value": pressure_drop,
                            "limit": limits["service_pressure_drop_pa_per_m"],
                            "standard": standard_name,
                            "recommendation": "Increase pipe diameter"
                        })
                        status = "FAIL"
                
                elif standard_name == "EN_13941":
                    if pressure_drop > limits["max_pressure_drop_pa_per_m"]:
                        violations.append({
                            "type": "pressure_drop",
                            "severity": "critical",
                            "pipe_id": pipe_id,
                            "value": pressure_drop,
                            "limit": limits["max_pressure_drop_pa_per_m"],
                            "standard": standard_name,
                            "recommendation": "Increase pipe diameter"
                        })
                        status = "FAIL"
        
        # Check VDI 2067 thermal criteria
        if standard_name == "VDI_2067" and "kpis" in data:
            kpis = data["kpis"]
            
            # Check thermal efficiency
            if "thermal_efficiency" in kpis:
                efficiency = kpis["thermal_efficiency"]
                if efficiency < limits["min_thermal_efficiency"]:
                    violations.append({
                        "type": "thermal_efficiency",
                        "severity": "warning",
                        "pipe_id": "network",
                        "value": efficiency,
                        "limit": limits["min_thermal_efficiency"],
                        "standard": standard_name,
                        "recommendation": "Improve insulation or reduce thermal losses"
                    })
                    if status == "PASS":
                        status = "WARNING"
            
            # Check temperature drop
            if "dt_k" in kpis:
                temp_drop = kpis["dt_k"]
                if temp_drop > limits["max_temperature_drop_k"]:
                    violations.append({
                        "type": "temperature_drop",
                        "severity": "warning",
                        "pipe_id": "network",
                        "value": temp_drop,
                        "limit": limits["max_temperature_drop_k"],
                        "standard": standard_name,
                        "recommendation": "Improve insulation or reduce network length"
                    })
                    if status == "PASS":
                        status = "WARNING"
                elif temp_drop < limits["min_temperature_drop_k"]:
                    violations.append({
                        "type": "temperature_drop",
                        "severity": "info",
                        "pipe_id": "network",
                        "value": temp_drop,
                        "limit": limits["min_temperature_drop_k"],
                        "standard": standard_name,
                        "recommendation": "Consider reducing insulation or increasing flow rates"
                    })
        
        return {"status": status, "violations": violations}
    
    def _validate_performance_criteria(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate performance criteria and efficiency metrics."""
        performance_result = {
            "status": "PASS",
            "violations": [],
            "metrics": {}
        }
        
        if "kpis" not in data:
            return performance_result
        
        kpis = data["kpis"]
        
        # Check pump power efficiency
        if "pump_kw" in kpis and "total_flow_kg_s" in kpis:
            pump_power = kpis["pump_kw"]
            total_flow = kpis["total_flow_kg_s"]
            
            if total_flow > 0:
                specific_pump_power = pump_power / total_flow  # kW per kg/s
                performance_result["metrics"]["specific_pump_power"] = specific_pump_power
                
                if specific_pump_power > 2.0:  # kW per kg/s
                    performance_result["violations"].append({
                        "type": "pump_efficiency",
                        "severity": "warning",
                        "pipe_id": "network",
                        "value": specific_pump_power,
                        "limit": 2.0,
                        "standard": "Performance",
                        "recommendation": "Optimize pipe sizing or reduce network complexity"
                    })
                    performance_result["status"] = "WARNING"
        
        # Check thermal loss efficiency
        if "losses_mwh_a" in kpis and "network_length_km" in kpis:
            thermal_losses = kpis["losses_mwh_a"]
            network_length = kpis["network_length_km"]
            
            if network_length > 0:
                specific_thermal_loss = thermal_losses / network_length  # MWh/a per km
                performance_result["metrics"]["specific_thermal_loss"] = specific_thermal_loss
                
                if specific_thermal_loss > 100:  # MWh/a per km
                    performance_result["violations"].append({
                        "type": "thermal_efficiency",
                        "severity": "warning",
                        "pipe_id": "network",
                        "value": specific_thermal_loss,
                        "limit": 100,
                        "standard": "Performance",
                        "recommendation": "Improve insulation or optimize network layout"
                    })
                    if performance_result["status"] == "PASS":
                        performance_result["status"] = "WARNING"
        
        return performance_result
    
    def _validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data quality and completeness."""
        quality_result = {
            "status": "PASS",
            "issues": [],
            "completeness": {}
        }
        
        # Check required sections
        required_sections = ["metadata", "nodes", "pipes", "kpis", "compliance", "crs", "units"]
        for section in required_sections:
            if section not in data:
                quality_result["issues"].append({
                    "type": "missing_section",
                    "severity": "critical",
                    "section": section,
                    "recommendation": f"Add missing {section} section"
                })
                quality_result["status"] = "FAIL"
        
        # Check data completeness
        if "nodes" in data:
            nodes = data["nodes"]
            quality_result["completeness"]["nodes"] = len(nodes)
            
            # Check for required node fields
            for i, node in enumerate(nodes):
                required_fields = ["id", "x", "y", "p_bar", "t_c", "node_type"]
                for field in required_fields:
                    if field not in node:
                        quality_result["issues"].append({
                            "type": "missing_field",
                            "severity": "critical",
                            "section": "nodes",
                            "index": i,
                            "field": field,
                            "recommendation": f"Add missing {field} field to node {i}"
                        })
                        quality_result["status"] = "FAIL"
        
        if "pipes" in data:
            pipes = data["pipes"]
            quality_result["completeness"]["pipes"] = len(pipes)
            
            # Check for required pipe fields
            for i, pipe in enumerate(pipes):
                required_fields = ["id", "dn_mm", "v_ms", "dp100m_pa", "mdot_kg_s", "t_seg_c", "pipe_category"]
                for field in required_fields:
                    if field not in pipe:
                        quality_result["issues"].append({
                            "type": "missing_field",
                            "severity": "critical",
                            "section": "pipes",
                            "index": i,
                            "field": field,
                            "recommendation": f"Add missing {field} field to pipe {i}"
                        })
                        quality_result["status"] = "FAIL"
        
        return quality_result
    
    def _generate_validation_summary(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of validation results."""
        file_results = validation_results.get("file_results", {})
        
        total_files = len(file_results)
        valid_files = sum(1 for result in file_results.values() if result.get("status") == "valid")
        invalid_files = sum(1 for result in file_results.values() if result.get("status") == "invalid")
        error_files = sum(1 for result in file_results.values() if result.get("status") == "error")
        
        # Standards compliance summary
        standards_summary = {}
        for file_name, file_result in file_results.items():
            if "standards_compliance" in file_result:
                compliance = file_result["standards_compliance"]
                for standard, status in compliance.get("standards_results", {}).items():
                    if standard not in standards_summary:
                        standards_summary[standard] = {"PASS": 0, "FAIL": 0, "WARNING": 0}
                    standards_summary[standard][status] += 1
        
        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "invalid_files": invalid_files,
            "error_files": error_files,
            "success_rate": valid_files / total_files if total_files > 0 else 0,
            "total_violations": validation_results.get("total_violations", 0),
            "standards_compliance": standards_summary
        }
    
    def generate_compliance_report(self, validation_results: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a comprehensive compliance report.
        
        Args:
            validation_results: Validation results to report on. If None, uses stored results.
            
        Returns:
            String containing the compliance report
        """
        if validation_results is None:
            validation_results = self.validation_results
        
        if not validation_results:
            return "No validation results available. Run validation first."
        
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("CHA SIMULATION COMPLIANCE REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Output Directory: {validation_results.get('output_directory', 'Unknown')}")
        report_lines.append("")
        
        # Summary section
        summary = validation_results.get("summary", {})
        report_lines.append("EXECUTIVE SUMMARY")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Files Validated: {summary.get('total_files', 0)}")
        report_lines.append(f"Valid Files: {summary.get('valid_files', 0)}")
        report_lines.append(f"Invalid Files: {summary.get('invalid_files', 0)}")
        report_lines.append(f"Error Files: {summary.get('error_files', 0)}")
        report_lines.append(f"Success Rate: {summary.get('success_rate', 0):.1%}")
        report_lines.append(f"Total Violations: {summary.get('total_violations', 0)}")
        report_lines.append("")
        
        # Standards compliance section
        standards_compliance = summary.get("standards_compliance", {})
        if standards_compliance:
            report_lines.append("STANDARDS COMPLIANCE")
            report_lines.append("-" * 40)
            for standard, results in standards_compliance.items():
                total = sum(results.values())
                pass_rate = results.get("PASS", 0) / total if total > 0 else 0
                report_lines.append(f"{standard}:")
                report_lines.append(f"  Pass: {results.get('PASS', 0)} ({pass_rate:.1%})")
                report_lines.append(f"  Fail: {results.get('FAIL', 0)}")
                report_lines.append(f"  Warning: {results.get('WARNING', 0)}")
            report_lines.append("")
        
        # File-by-file results
        file_results = validation_results.get("file_results", {})
        if file_results:
            report_lines.append("FILE-BY-FILE RESULTS")
            report_lines.append("-" * 40)
            
            for file_name, file_result in file_results.items():
                status = file_result.get("status", "unknown")
                violations = file_result.get("total_violations", 0)
                
                report_lines.append(f"{file_name}:")
                report_lines.append(f"  Status: {status.upper()}")
                report_lines.append(f"  Violations: {violations}")
                
                # Add specific violation details
                if "standards_compliance" in file_result:
                    compliance = file_result["standards_compliance"]
                    violations_list = compliance.get("violations", [])
                    if violations_list:
                        report_lines.append("  Standards Violations:")
                        for violation in violations_list[:5]:  # Show first 5 violations
                            report_lines.append(f"    - {violation.get('type', 'unknown')}: {violation.get('value', 'N/A')} > {violation.get('limit', 'N/A')} ({violation.get('standard', 'unknown')})")
                        if len(violations_list) > 5:
                            report_lines.append(f"    ... and {len(violations_list) - 5} more violations")
                
                report_lines.append("")
        
        # Recommendations section
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 40)
        
        if summary.get("invalid_files", 0) > 0:
            report_lines.append("• Address invalid files to ensure data quality")
        
        if summary.get("total_violations", 0) > 0:
            report_lines.append("• Review and resolve standards violations")
        
        if summary.get("success_rate", 0) < 0.8:
            report_lines.append("• Improve overall validation success rate")
        
        # Standards-specific recommendations
        for standard, results in standards_compliance.items():
            fail_count = results.get("FAIL", 0)
            if fail_count > 0:
                report_lines.append(f"• Address {fail_count} {standard} compliance failures")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def export_validation_results(self, results: Optional[Dict[str, Any]] = None, output_path: str = "validation_results.json") -> bool:
        """
        Export validation results to a file.
        
        Args:
            results: Validation results to export. If None, uses stored results.
            output_path: Path to save the results
            
        Returns:
            True if successful, False otherwise
        """
        if results is None:
            results = self.validation_results
        
        if not results:
            print("❌ No validation results to export")
            return False
        
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Add export metadata
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "export_version": "1.0.0",
                "validation_results": results
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"✅ Validation results exported to {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to export validation results: {e}")
            return False
    
    def run_complete_validation(self, output_dir: str, export_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Run complete validation workflow.
        
        Args:
            output_dir: Directory containing CHA outputs
            export_path: Optional path to export results
            
        Returns:
            Complete validation results
        """
        print("🚀 Starting complete CHA validation workflow")
        print("=" * 60)
        
        # Step 1: Validate outputs
        print("Step 1: Validating CHA outputs...")
        validation_results = self.validate_cha_outputs(output_dir)
        
        # Step 2: Generate compliance report
        print("Step 2: Generating compliance report...")
        compliance_report = self.generate_compliance_report(validation_results)
        
        # Step 3: Export results if requested
        if export_path:
            print("Step 3: Exporting validation results...")
            self.export_validation_results(validation_results, export_path)
        
        # Step 4: Save compliance report
        if export_path:
            report_path = Path(export_path).parent / "compliance_report.txt"
            with open(report_path, 'w') as f:
                f.write(compliance_report)
            print(f"✅ Compliance report saved to {report_path}")
        
        # Add compliance report to results
        validation_results["compliance_report"] = compliance_report
        
        print("✅ Complete validation workflow finished")
        return validation_results


# Example usage and testing
if __name__ == "__main__":
    print("🔍 CHA Validation System Test")
    print("=" * 50)
    
    # Initialize validation system
    validator = CHAValidationSystem()
    
    # Create test data directory
    test_dir = Path("test_cha_outputs")
    test_dir.mkdir(exist_ok=True)
    
    # Create example CHA output file
    example_data = validator.schema_validator.create_example_output()
    test_file = test_dir / "cha_output_example.json"
    
    with open(test_file, 'w') as f:
        json.dump(example_data, f, indent=2, default=str)
    
    print(f"📁 Created test file: {test_file}")
    
    # Run validation
    print(f"\n🔍 Running validation on {test_dir}...")
    results = validator.run_complete_validation(str(test_dir), "test_validation_results.json")
    
    # Display results
    print(f"\n📊 Validation Results:")
    print(f"   Files validated: {results['validated_files']}")
    print(f"   Total violations: {results['total_violations']}")
    print(f"   Success rate: {results['summary']['success_rate']:.1%}")
    
    # Display compliance report
    print(f"\n📋 Compliance Report:")
    print(results['compliance_report'])
    
    print(f"\n🎉 CHA Validation System test completed!")


def validate_cha_outputs(output_dir: str) -> Dict[str, Any]:
    """
    Standalone function to validate CHA outputs from command line.
    
    Args:
        output_dir: Directory containing CHA output files
        
    Returns:
        Dict with comprehensive validation results
    """
    validator = CHAValidationSystem()
    return validator.validate_cha_outputs(output_dir)
