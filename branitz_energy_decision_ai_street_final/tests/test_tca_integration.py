"""
Comprehensive integration tests for the enhanced TCA system.
"""

import pytest
import pandas as pd
import numpy as np
import json
import yaml
from pathlib import Path
import sys
from datetime import datetime
import tempfile
import shutil

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from tca import (
    run, 
    _calculate_cha_metrics_from_hydraulics, 
    _calculate_pump_efficiency_metrics, 
    _integrate_thermal_performance, 
    _update_decision_logic_with_hydraulics,
    _validate_json,
    _read_summary_csv
)

class TestTCAIntegration:
    """Comprehensive integration tests for the enhanced TCA system."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def enhanced_cha_data(self):
        """Create enhanced CHA data with hydraulic simulation results."""
        return pd.DataFrame({
            "length_m": [150.0, 200.0, 100.0, 75.0, 120.0, 180.0, 90.0, 110.0],
            "d_inner_m": [0.2, 0.25, 0.15, 0.1, 0.18, 0.22, 0.12, 0.16],
            "v_ms": [1.2, 1.5, 1.8, 0.8, 1.1, 1.3, 2.1, 1.4],
            "dp_bar": [0.003, 0.004, 0.002, 0.001, 0.003, 0.0035, 0.0025, 0.0028],
            "q_loss_Wm": [45.2, 58.7, 32.1, 18.5, 42.3, 52.1, 28.9, 38.7],
            "mdot_kg_s": [25.5, 35.2, 18.8, 8.5, 22.1, 28.9, 12.3, 19.7],
            "t_seg_c": [78.5, 79.2, 77.8, 65.0, 76.5, 78.8, 66.2, 75.9],
            "pipe_category": ["mains", "mains", "distribution", "services", "distribution", "mains", "services", "distribution"]
        })
    
    @pytest.fixture
    def dha_data(self):
        """Create DHA feeder data."""
        return pd.DataFrame({
            "utilization_pct": [85.5, 92.3, 78.1, 88.7, 91.2, 83.4, 89.6, 87.3]
        })
    
    @pytest.fixture
    def eaa_summary_data(self):
        """Create EAA summary data."""
        return pd.DataFrame({
            "metric": ["lcoh_eur_per_mwh", "co2_kg_per_mwh"],
            "mean": [485.2, 0.312],
            "median": [482.1, 0.308],
            "p2_5": [420.5, 0.285],
            "p97_5": [550.8, 0.340]
        })
    
    @pytest.fixture
    def tca_config(self, temp_dir):
        """Create TCA configuration for testing."""
        return {
            "scenario_name": "integration_test",
            "paths": {
                "eaa_summary": str(Path(temp_dir) / "summary.csv"),
                "cha_segments": str(Path(temp_dir) / "segments.csv"),
                "dha_feeders": str(Path(temp_dir) / "feeder_loads.csv"),
                "kpi_out": str(Path(temp_dir) / "kpi_summary.json")
            },
            "thresholds": {
                "feeder_utilization_warn_pct": 80,
                "lcoh_hp_advantage_eur_per_mwh": 10,
                "max_velocity_ms": 2.5,
                "max_pressure_drop_pa_per_m": 500,
                "min_thermal_efficiency": 0.6,
                "max_thermal_losses_kw": 100,
                "max_specific_pump_power_kw_per_kg_s": 2.0,
                "max_lcoh_eur_per_mwh": 500
            },
            "forecast_rmse": 0.12,
            "forecast_picp_90": 0.90,
            "kpi_schema": "schemas/kpi_summary.schema.json",
            "kpi_schema_version": "2.0.0"
        }
    
    def test_cha_metrics_calculation(self, enhanced_cha_data):
        """Test CHA metrics calculation from hydraulic simulation data."""
        metrics = _calculate_cha_metrics_from_hydraulics(enhanced_cha_data)
        
        # Verify all required metrics are present
        required_metrics = [
            "dh_losses_pct", "pump_kw", "max_velocity_ms", 
            "max_pressure_drop_pa_per_m", "thermal_efficiency",
            "network_length_km", "total_flow_kg_s"
        ]
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
        
        # Verify metric values are reasonable
        assert metrics["dh_losses_pct"] >= 0, "DH losses should be non-negative"
        assert metrics["pump_kw"] >= 0, "Pump power should be non-negative"
        assert metrics["max_velocity_ms"] >= 0, "Max velocity should be non-negative"
        assert metrics["max_pressure_drop_pa_per_m"] >= 0, "Max pressure drop should be non-negative"
        assert 0 <= metrics["thermal_efficiency"] <= 1, "Thermal efficiency should be 0-1"
        assert metrics["network_length_km"] > 0, "Network length should be positive"
        assert metrics["total_flow_kg_s"] >= 0, "Total flow should be non-negative"
        
        # Verify specific values from test data
        assert metrics["max_velocity_ms"] == 2.1, "Max velocity should match test data"
        assert metrics["total_flow_kg_s"] == 171.0, "Total flow should match test data"
    
    def test_pump_efficiency_metrics(self, enhanced_cha_data):
        """Test pump efficiency metrics calculation."""
        metrics = _calculate_pump_efficiency_metrics(enhanced_cha_data)
        
        # Verify required metrics
        assert "pump_efficiency" in metrics, "Missing pump efficiency"
        assert "specific_pump_power" in metrics, "Missing specific pump power"
        
        # Verify metric values
        assert 0 <= metrics["pump_efficiency"] <= 1, "Pump efficiency should be 0-1"
        assert metrics["specific_pump_power"] >= 0, "Specific pump power should be non-negative"
        
        # Verify specific values
        assert metrics["pump_efficiency"] == 0.75, "Pump efficiency should be 75%"
    
    def test_thermal_performance_metrics(self, enhanced_cha_data):
        """Test thermal performance metrics calculation."""
        metrics = _integrate_thermal_performance(enhanced_cha_data)
        
        # Verify required metrics
        required_metrics = ["thermal_losses_kw", "temperature_drop_k", "thermal_loss_factor"]
        for metric in required_metrics:
            assert metric in metrics, f"Missing metric: {metric}"
        
        # Verify metric values
        assert metrics["thermal_losses_kw"] >= 0, "Thermal losses should be non-negative"
        assert metrics["temperature_drop_k"] >= 0, "Temperature drop should be non-negative"
        assert metrics["thermal_loss_factor"] >= 0, "Thermal loss factor should be non-negative"
        
        # Verify specific values from test data (with floating point tolerance)
        assert abs(metrics["temperature_drop_k"] - 14.2) < 0.1, "Temperature drop should match test data"
    
    def test_decision_logic_good_performance(self):
        """Test decision logic with good hydraulic performance."""
        metrics = {
            "feeder_max_utilization_pct": 75.0,
            "max_velocity_ms": 1.8,
            "max_pressure_drop_pa_per_m": 350,
            "thermal_efficiency": 0.75,
            "pump_efficiency": 0.75,
            "specific_pump_power": 1.2,
            "thermal_losses_kw": 45.0,
            "temperature_drop_k": 12.5,
            "lcoh_mean": 420.0,
            "thresholds": {
                "feeder_utilization_warn_pct": 80,
                "max_velocity_ms": 2.5,
                "max_pressure_drop_pa_per_m": 500,
                "min_thermal_efficiency": 0.6,
                "max_thermal_losses_kw": 100,
                "max_specific_pump_power_kw_per_kg_s": 2.0,
                "max_lcoh_eur_per_mwh": 500
            }
        }
        
        rec, rationale = _update_decision_logic_with_hydraulics(metrics)
        
        assert rec == "Hybrid", "Good performance should recommend Hybrid"
        assert len(rationale) > 0, "Should have rationale"
        assert "Both feasible" in rationale[0], "Should indicate both feasible"
    
    def test_decision_logic_poor_performance(self):
        """Test decision logic with poor hydraulic performance."""
        metrics = {
            "feeder_max_utilization_pct": 70.0,
            "max_velocity_ms": 3.2,
            "max_pressure_drop_pa_per_m": 650,
            "thermal_efficiency": 0.45,
            "pump_efficiency": 0.70,
            "specific_pump_power": 2.8,
            "thermal_losses_kw": 150.0,
            "temperature_drop_k": 18.0,
            "lcoh_mean": 580.0,
            "thresholds": {
                "feeder_utilization_warn_pct": 80,
                "max_velocity_ms": 2.5,
                "max_pressure_drop_pa_per_m": 500,
                "min_thermal_efficiency": 0.6,
                "max_thermal_losses_kw": 100,
                "max_specific_pump_power_kw_per_kg_s": 2.0,
                "max_lcoh_eur_per_mwh": 500
            }
        }
        
        rec, rationale = _update_decision_logic_with_hydraulics(metrics)
        
        assert rec == "HP", "Poor performance should recommend HP"
        assert len(rationale) > 1, "Should have multiple issues"
        assert any("velocity" in r for r in rationale), "Should mention velocity issue"
        assert any("pressure drop" in r for r in rationale), "Should mention pressure drop issue"
        assert any("thermal efficiency" in r for r in rationale), "Should mention thermal efficiency issue"
    
    def test_decision_logic_high_utilization(self):
        """Test decision logic with high feeder utilization."""
        metrics = {
            "feeder_max_utilization_pct": 95.0,
            "max_velocity_ms": 1.5,
            "max_pressure_drop_pa_per_m": 300,
            "thermal_efficiency": 0.80,
            "pump_efficiency": 0.78,
            "specific_pump_power": 0.8,
            "thermal_losses_kw": 35.0,
            "temperature_drop_k": 10.0,
            "lcoh_mean": 380.0,
            "thresholds": {
                "feeder_utilization_warn_pct": 80,
                "max_velocity_ms": 2.5,
                "max_pressure_drop_pa_per_m": 500,
                "min_thermal_efficiency": 0.6,
                "max_thermal_losses_kw": 100,
                "max_specific_pump_power_kw_per_kg_s": 2.0,
                "max_lcoh_eur_per_mwh": 500
            }
        }
        
        rec, rationale = _update_decision_logic_with_hydraulics(metrics)
        
        assert rec == "DH", "High utilization should recommend DH"
        assert len(rationale) > 0, "Should have rationale"
        assert "Feeder utilization" in rationale[0], "Should mention feeder utilization"
    
    def test_eaa_summary_reading(self, temp_dir, eaa_summary_data):
        """Test EAA summary CSV reading."""
        # Save test data
        eaa_summary_data.to_csv(Path(temp_dir) / "summary.csv", index=False)
        
        # Read and verify
        summary = _read_summary_csv(str(Path(temp_dir) / "summary.csv"))
        
        assert "lcoh_mean" in summary, "Missing LCOH mean"
        assert "co2_mean" in summary, "Missing CO2 mean"
        assert summary["lcoh_mean"] == 485.2, "LCOH mean should match test data"
        assert summary["co2_mean"] == 0.312, "CO2 mean should match test data"
    
    def test_full_tca_integration(self, temp_dir, enhanced_cha_data, dha_data, eaa_summary_data, tca_config):
        """Test full TCA integration with all components."""
        # Save test data
        enhanced_cha_data.to_csv(Path(temp_dir) / "segments.csv", index=False)
        dha_data.to_csv(Path(temp_dir) / "feeder_loads.csv", index=False)
        eaa_summary_data.to_csv(Path(temp_dir) / "summary.csv", index=False)
        
        # Save configuration
        config_file = Path(temp_dir) / "tca_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(tca_config, f)
        
        # Run TCA
        results = run(str(config_file))
        
        # Verify results
        assert "kpi" in results, "Results should contain KPI path"
        assert Path(results["kpi"]).exists(), "KPI file should exist"
        
        # Read and validate KPI data
        with open(results["kpi"], 'r') as f:
            kpi_data = json.load(f)
        
        # Verify structure
        assert "project_info" in kpi_data, "Missing project info"
        assert "economic_metrics" in kpi_data, "Missing economic metrics"
        assert "technical_metrics" in kpi_data, "Missing technical metrics"
        assert "recommendation" in kpi_data, "Missing recommendation"
        
        # Verify technical metrics
        tech_metrics = kpi_data["technical_metrics"]
        required_tech_metrics = [
            "dh_losses_pct", "pump_kw", "feeder_max_utilization_pct",
            "max_velocity_ms", "max_pressure_drop_pa_per_m", "thermal_efficiency",
            "network_length_km", "total_flow_kg_s", "pump_efficiency",
            "specific_pump_power_kw_per_kg_s", "thermal_losses_kw",
            "temperature_drop_k", "thermal_loss_factor"
        ]
        for metric in required_tech_metrics:
            assert metric in tech_metrics, f"Missing technical metric: {metric}"
        
        # Verify recommendation
        recommendation = kpi_data["recommendation"]
        assert "preferred_scenario" in recommendation, "Missing preferred scenario"
        assert "confidence_level" in recommendation, "Missing confidence level"
        assert "rationale" in recommendation, "Missing rationale"
        assert recommendation["preferred_scenario"] in ["DH", "HP", "Hybrid", "Inconclusive"], "Invalid scenario"
        assert recommendation["confidence_level"] in ["high", "medium", "low"], "Invalid confidence level"
    
    def test_schema_validation(self, temp_dir, enhanced_cha_data, dha_data, eaa_summary_data, tca_config):
        """Test schema validation of TCA output."""
        # Save test data
        enhanced_cha_data.to_csv(Path(temp_dir) / "segments.csv", index=False)
        dha_data.to_csv(Path(temp_dir) / "feeder_loads.csv", index=False)
        eaa_summary_data.to_csv(Path(temp_dir) / "summary.csv", index=False)
        
        # Save configuration
        config_file = Path(temp_dir) / "tca_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(tca_config, f)
        
        # Run TCA
        results = run(str(config_file))
        
        # Read KPI data
        with open(results["kpi"], 'r') as f:
            kpi_data = json.load(f)
        
        # Validate against schema
        _validate_json(kpi_data, "schemas/kpi_summary.schema.json")
        
        # If we get here, validation passed
        assert True, "Schema validation should pass"
    
    def test_threshold_sensitivity(self):
        """Test sensitivity to different threshold values."""
        base_metrics = {
            "feeder_max_utilization_pct": 70.0,
            "max_velocity_ms": 2.0,
            "max_pressure_drop_pa_per_m": 400,
            "thermal_efficiency": 0.7,
            "pump_efficiency": 0.75,
            "specific_pump_power": 1.5,
            "thermal_losses_kw": 80.0,
            "temperature_drop_k": 15.0,
            "lcoh_mean": 450.0,
            "thresholds": {
                "feeder_utilization_warn_pct": 80,
                "max_velocity_ms": 2.5,
                "max_pressure_drop_pa_per_m": 500,
                "min_thermal_efficiency": 0.6,
                "max_thermal_losses_kw": 100,
                "max_specific_pump_power_kw_per_kg_s": 2.0,
                "max_lcoh_eur_per_mwh": 500
            }
        }
        
        # Test with different velocity thresholds
        for threshold in [1.5, 2.0, 2.5, 3.0]:
            metrics = base_metrics.copy()
            metrics["thresholds"]["max_velocity_ms"] = threshold
            metrics["max_velocity_ms"] = threshold + 0.1  # Just above threshold
            
            rec, rationale = _update_decision_logic_with_hydraulics(metrics)
            
            # When velocity is above threshold, should recommend HP
            assert rec == "HP", f"Should recommend HP for velocity threshold {threshold} (velocity {metrics['max_velocity_ms']:.1f} above threshold {threshold})"
        
        # Test with velocity below threshold (should recommend Hybrid)
        metrics = base_metrics.copy()
        metrics["thresholds"]["max_velocity_ms"] = 2.5
        metrics["max_velocity_ms"] = 2.0  # Below threshold
        
        rec, rationale = _update_decision_logic_with_hydraulics(metrics)
        assert rec == "Hybrid", f"Should recommend Hybrid when velocity {metrics['max_velocity_ms']:.1f} is below threshold {metrics['thresholds']['max_velocity_ms']}"
    
    def test_fallback_behavior(self, temp_dir, dha_data, eaa_summary_data, tca_config):
        """Test fallback behavior with missing hydraulic data."""
        # Create CHA data without hydraulic simulation columns
        cha_data_fallback = pd.DataFrame({
            "length_m": [150.0, 200.0, 100.0],
            "d_inner_m": [0.2, 0.25, 0.15],
            "v_ms": [1.2, 1.5, 1.8],
            "dp_bar": [0.003, 0.004, 0.002]
            # Missing: q_loss_Wm, mdot_kg_s, t_seg_c, pipe_category
        })
        
        # Save test data
        cha_data_fallback.to_csv(Path(temp_dir) / "segments.csv", index=False)
        dha_data.to_csv(Path(temp_dir) / "feeder_loads.csv", index=False)
        eaa_summary_data.to_csv(Path(temp_dir) / "summary.csv", index=False)
        
        # Save configuration
        config_file = Path(temp_dir) / "tca_config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(tca_config, f)
        
        # Run TCA (should not fail)
        results = run(str(config_file))
        
        # Verify results still valid
        assert "kpi" in results, "Results should contain KPI path"
        assert Path(results["kpi"]).exists(), "KPI file should exist"
        
        # Read and verify KPI data
        with open(results["kpi"], 'r') as f:
            kpi_data = json.load(f)
        
        # Verify technical metrics exist (with fallback values)
        tech_metrics = kpi_data["technical_metrics"]
        assert "max_velocity_ms" in tech_metrics, "Should have max velocity"
        assert "thermal_efficiency" in tech_metrics, "Should have thermal efficiency"
        assert tech_metrics["thermal_efficiency"] == 0.0, "Should have fallback thermal efficiency"

if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
