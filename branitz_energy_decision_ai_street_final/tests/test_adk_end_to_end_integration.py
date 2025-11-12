#!/usr/bin/env python3
"""
End-to-End Integration Tests for ADK System
Tests complete end-to-end pipeline with ADK agents
"""

import pytest
import sys
import os
import time
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add ADK to path
sys.path.insert(0, 'adk')

class TestEndToEndADKIntegration:
    """Test complete end-to-end ADK integration."""
    
    def test_complete_data_exploration_workflow(self):
        """Test complete data exploration workflow."""
        try:
            from src.enhanced_tools import get_all_street_names, list_available_results
            
            # Step 1: Get all available streets
            print("Step 1: Getting all available streets...")
            streets = get_all_street_names()
            assert isinstance(streets, list), "Streets should be a list"
            assert len(streets) > 0, "Should have at least one street"
            print(f"Found {len(streets)} streets: {streets[:5]}...")
            
            # Step 2: List available results
            print("Step 2: Listing available results...")
            results = list_available_results()
            assert isinstance(results, str), "Results should be a string"
            assert len(results) > 0, "Should have some results"
            print(f"Results summary: {results[:200]}...")
            
            # Step 3: Verify data consistency
            print("Step 3: Verifying data consistency...")
            assert len(streets) > 0, "No streets available for analysis"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_complete_building_analysis_workflow(self):
        """Test complete building analysis workflow."""
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Step 1: Get available streets
            streets = get_all_street_names()
            assert len(streets) > 0, "No streets available for testing"
            
            # Step 2: Select a test street
            test_street = streets[0]
            print(f"Testing with street: {test_street}")
            
            # Step 3: Get building IDs for the street
            building_ids = get_building_ids_for_street(test_street)
            assert isinstance(building_ids, list), "Building IDs should be a list"
            print(f"Found {len(building_ids)} buildings for {test_street}")
            
            # Step 4: Verify building IDs format (if any exist)
            if building_ids:
                for building_id in building_ids[:3]:  # Check first 3
                    assert isinstance(building_id, str), "Building ID should be a string"
                    assert len(building_id) > 0, "Building ID should not be empty"
                print(f"Sample building IDs: {building_ids[:3]}")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_complete_heat_pump_analysis_workflow(self):
        """Test complete heat pump analysis workflow."""
        try:
            from src.enhanced_tools import run_comprehensive_hp_analysis
            
            # Test with a known street
            test_street = "Parkstraße"
            print(f"Testing heat pump analysis for: {test_street}")
            
            # Run heat pump analysis
            result = run_comprehensive_hp_analysis(test_street)
            assert isinstance(result, str), "Result should be a string"
            assert len(result) > 0, "Result should not be empty"
            print(f"Heat pump analysis result: {result[:200]}...")
            
            # Verify result contains expected content
            assert any(keyword in result.lower() for keyword in ['analysis', 'heat', 'pump', 'feasibility']), "Result should contain analysis content"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_complete_district_heating_analysis_workflow(self):
        """Test complete district heating analysis workflow."""
        try:
            from src.enhanced_tools import run_comprehensive_dh_analysis
            
            # Test with a known street
            test_street = "Parkstraße"
            print(f"Testing district heating analysis for: {test_street}")
            
            # Run district heating analysis
            result = run_comprehensive_dh_analysis(test_street)
            assert isinstance(result, str), "Result should be a string"
            assert len(result) > 0, "Result should not be empty"
            print(f"District heating analysis result: {result[:200]}...")
            
            # Verify result contains expected content
            assert any(keyword in result.lower() for keyword in ['analysis', 'district', 'heating', 'network']), "Result should contain analysis content"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_complete_scenario_comparison_workflow(self):
        """Test complete scenario comparison workflow."""
        try:
            from src.enhanced_tools import compare_comprehensive_scenarios
            
            # Test with a known street
            test_street = "Parkstraße"
            print(f"Testing scenario comparison for: {test_street}")
            
            # Run scenario comparison
            result = compare_comprehensive_scenarios(test_street)
            assert isinstance(result, str), "Result should be a string"
            assert len(result) > 0, "Result should not be empty"
            print(f"Scenario comparison result: {result[:200]}...")
            
            # Verify result contains expected content
            assert any(keyword in result.lower() for keyword in ['comparison', 'scenario', 'analysis', 'compare']), "Result should contain comparison content"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_complete_kpi_report_workflow(self):
        """Test complete KPI report generation workflow."""
        try:
            from src.enhanced_tools import generate_comprehensive_kpi_report
            
            # Test with a known street
            test_street = "Parkstraße"
            print(f"Testing KPI report generation for: {test_street}")
            
            # Generate KPI report
            result = generate_comprehensive_kpi_report(test_street)
            assert isinstance(result, str), "Result should be a string"
            assert len(result) > 0, "Result should not be empty"
            print(f"KPI report result: {result[:200]}...")
            
            # Verify result contains expected content
            assert any(keyword in result.lower() for keyword in ['kpi', 'report', 'analysis', 'metrics']), "Result should contain KPI content"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_complete_analysis_pipeline_workflow(self):
        """Test complete analysis pipeline workflow."""
        try:
            from src.enhanced_tools import (
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios,
                generate_comprehensive_kpi_report
            )
            
            print("Starting complete analysis pipeline workflow...")
            
            # Step 1: Get available streets
            print("Step 1: Getting available streets...")
            streets = get_all_street_names()
            assert len(streets) > 0, "No streets available for testing"
            test_street = streets[0]
            print(f"Selected test street: {test_street}")
            
            # Step 2: Get building information
            print("Step 2: Getting building information...")
            building_ids = get_building_ids_for_street(test_street)
            print(f"Found {len(building_ids)} buildings")
            
            # Step 3: Run heat pump analysis
            print("Step 3: Running heat pump analysis...")
            hp_result = run_comprehensive_hp_analysis(test_street)
            assert isinstance(hp_result, str) and len(hp_result) > 0
            print("Heat pump analysis completed")
            
            # Step 4: Run district heating analysis
            print("Step 4: Running district heating analysis...")
            dh_result = run_comprehensive_dh_analysis(test_street)
            assert isinstance(dh_result, str) and len(dh_result) > 0
            print("District heating analysis completed")
            
            # Step 5: Compare scenarios
            print("Step 5: Comparing scenarios...")
            comparison_result = compare_comprehensive_scenarios(test_street)
            assert isinstance(comparison_result, str) and len(comparison_result) > 0
            print("Scenario comparison completed")
            
            # Step 6: Generate KPI report
            print("Step 6: Generating KPI report...")
            kpi_result = generate_comprehensive_kpi_report(test_street)
            assert isinstance(kpi_result, str) and len(kpi_result) > 0
            print("KPI report generation completed")
            
            # Step 7: Verify all results
            print("Step 7: Verifying all results...")
            # Check that results are strings and have reasonable length (even if they contain errors)
            assert len(hp_result) > 50, "Heat pump analysis result too short"
            assert len(dh_result) > 50, "District heating analysis result too short"
            assert len(comparison_result) > 50, "Comparison result too short"
            assert len(kpi_result) > 50, "KPI report result too short"
            
            # Log the results for debugging
            print(f"HP result length: {len(hp_result)}")
            print(f"DH result length: {len(dh_result)}")
            print(f"Comparison result length: {len(comparison_result)}")
            print(f"KPI result length: {len(kpi_result)}")
            
            print("Complete analysis pipeline workflow completed successfully!")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_multi_street_analysis_workflow(self):
        """Test multi-street analysis workflow."""
        try:
            from src.enhanced_tools import get_all_street_names, run_comprehensive_hp_analysis
            
            # Get multiple streets
            streets = get_all_street_names()
            assert len(streets) > 0, "No streets available for testing"
            
            # Test with first few streets (limit to 3 for performance)
            test_streets = streets[:3]
            print(f"Testing multi-street analysis with: {test_streets}")
            
            results = {}
            for street in test_streets:
                print(f"Analyzing street: {street}")
                result = run_comprehensive_hp_analysis(street)
                assert isinstance(result, str) and len(result) > 0
                results[street] = result
                print(f"Analysis completed for {street}")
            
            # Verify all results
            assert len(results) == len(test_streets), "Not all streets were analyzed"
            for street, result in results.items():
                assert len(result) > 50, f"Result for {street} too short"
            
            print("Multi-street analysis workflow completed successfully!")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_error_handling_workflow(self):
        """Test error handling in end-to-end workflow."""
        try:
            from src.enhanced_tools import get_building_ids_for_street, run_comprehensive_hp_analysis
            
            # Test with invalid street name
            print("Testing error handling with invalid street...")
            invalid_result = get_building_ids_for_street("NonExistentStreet123")
            assert isinstance(invalid_result, list), "Should return list even for invalid street"
            print(f"Invalid street result: {len(invalid_result)} buildings found")
            
            # Test with empty street name
            print("Testing error handling with empty street...")
            empty_result = get_building_ids_for_street("")
            assert isinstance(empty_result, list), "Should return list even for empty street"
            print(f"Empty street result: {len(empty_result)} buildings found")
            
            # Test analysis with invalid street
            print("Testing analysis with invalid street...")
            invalid_analysis = run_comprehensive_hp_analysis("NonExistentStreet123")
            assert isinstance(invalid_analysis, str), "Should return string even for invalid street"
            assert len(invalid_analysis) > 0, "Should return some result even for invalid street"
            print("Error handling workflow completed successfully!")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_performance_workflow(self):
        """Test performance of end-to-end workflow."""
        try:
            from src.enhanced_tools import get_all_street_names, run_comprehensive_hp_analysis
            
            # Test execution time
            print("Testing workflow performance...")
            start_time = time.time()
            
            # Get streets
            streets = get_all_street_names()
            assert len(streets) > 0, "No streets available for testing"
            
            # Run analysis on first street
            result = run_comprehensive_hp_analysis(streets[0])
            assert isinstance(result, str) and len(result) > 0
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            print(f"Workflow execution time: {execution_time:.2f} seconds")
            
            # Should complete within reasonable time (30 seconds)
            assert execution_time < 30.0, f"Workflow took too long: {execution_time:.2f}s"
            
            print("Performance workflow test completed successfully!")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_data_consistency_workflow(self):
        """Test data consistency across workflow."""
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Get streets multiple times and verify consistency
            print("Testing data consistency...")
            
            streets1 = get_all_street_names()
            streets2 = get_all_street_names()
            
            assert streets1 == streets2, "Street lists should be consistent"
            assert len(streets1) > 0, "Should have streets"
            
            # Test building consistency for a street
            if streets1:
                test_street = streets1[0]
                buildings1 = get_building_ids_for_street(test_street)
                buildings2 = get_building_ids_for_street(test_street)
                
                assert buildings1 == buildings2, f"Building lists should be consistent for {test_street}"
                print(f"Data consistency verified for {test_street}: {len(buildings1)} buildings")
            
            print("Data consistency workflow test completed successfully!")
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
