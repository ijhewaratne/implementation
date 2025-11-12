#!/usr/bin/env python3
"""
Unit Tests for ADK Tools
Tests ADK tool functionality and integration
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile

class TestADKToolsImport:
    """Test ADK tools import and availability."""
    
    def test_enhanced_tools_import(self):
        """Test that enhanced tools can be imported."""
        try:
            from src.enhanced_tools import (
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios,
                analyze_kpi_report,
                list_available_results,
                generate_comprehensive_kpi_report
            )
            assert get_all_street_names is not None
            assert get_building_ids_for_street is not None
            assert run_comprehensive_hp_analysis is not None
            assert run_comprehensive_dh_analysis is not None
            assert compare_comprehensive_scenarios is not None
            assert analyze_kpi_report is not None
            assert list_available_results is not None
            assert generate_comprehensive_kpi_report is not None
        except ImportError as e:
            pytest.skip(f"Enhanced tools not available: {e}")
    
    def test_tool_functions_are_callable(self):
        """Test that tool functions are callable."""
        try:
            from src.enhanced_tools import (
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios,
                analyze_kpi_report,
                list_available_results,
                generate_comprehensive_kpi_report
            )
            
            tools = [
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios,
                analyze_kpi_report,
                list_available_results,
                generate_comprehensive_kpi_report
            ]
            
            for tool in tools:
                assert callable(tool), f"Tool {tool.__name__} is not callable"
                
        except ImportError:
            pytest.skip("Enhanced tools not available")

class TestGetAllStreetNames:
    """Test get_all_street_names tool."""
    
    @pytest.fixture
    def get_all_street_names_tool(self):
        """Get the get_all_street_names tool."""
        try:
            from src.enhanced_tools import get_all_street_names
            return get_all_street_names
        except ImportError:
            pytest.skip("get_all_street_names tool not available")
    
    def test_get_all_street_names_basic(self, get_all_street_names_tool):
        """Test basic functionality of get_all_street_names."""
        result = get_all_street_names_tool()
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_get_all_street_names_returns_street_list(self, get_all_street_names_tool):
        """Test that get_all_street_names returns a list of streets."""
        result = get_all_street_names_tool()
        # The result should contain street names
        assert isinstance(result, list)
        # Should contain actual street names
        assert len(result) > 0
        # Check that we have actual street names
        assert all(isinstance(street, str) for street in result)

class TestGetBuildingIdsForStreet:
    """Test get_building_ids_for_street tool."""
    
    @pytest.fixture
    def get_building_ids_tool(self):
        """Get the get_building_ids_for_street tool."""
        try:
            from src.enhanced_tools import get_building_ids_for_street
            return get_building_ids_for_street
        except ImportError:
            pytest.skip("get_building_ids_for_street tool not available")
    
    def test_get_building_ids_for_street_basic(self, get_building_ids_tool):
        """Test basic functionality of get_building_ids_for_street."""
        result = get_building_ids_tool("Test Street")
        assert isinstance(result, list)
        # Should return a list (even if empty)
        assert result is not None
    
    def test_get_building_ids_for_street_with_valid_street(self, get_building_ids_tool):
        """Test get_building_ids_for_street with a valid street name."""
        # Test with a common street name that might exist
        result = get_building_ids_tool("Parkstraße")
        assert isinstance(result, list)
        # Should return a list of building IDs
        assert result is not None

class TestAnalyzeKpiReport:
    """Test analyze_kpi_report tool."""
    
    @pytest.fixture
    def analyze_kpi_report_tool(self):
        """Get the analyze_kpi_report tool."""
        try:
            from src.enhanced_tools import analyze_kpi_report
            return analyze_kpi_report
        except ImportError:
            pytest.skip("analyze_kpi_report tool not available")
    
    def test_analyze_kpi_report_with_valid_file(self, analyze_kpi_report_tool):
        """Test analyze_kpi_report with a valid KPI file."""
        # Create a temporary KPI file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            kpi_data = {
                "economic_metrics": {
                    "lcoh_eur_per_mwh": 95.2,
                    "capex_eur": 1500000,
                    "opex_eur_per_year": 75000
                },
                "technical_metrics": {
                    "feeder_max_utilization_pct": 72.5,
                    "network_efficiency": 0.85
                },
                "recommendation": {
                    "preferred_scenario": "Hybrid",
                    "confidence": 0.8
                }
            }
            json.dump(kpi_data, f)
            temp_file = f.name
        
        try:
            result = analyze_kpi_report_tool(temp_file)
            assert isinstance(result, str)
            assert len(result) > 0
            # Should contain some analysis of the KPI data
            assert any(keyword in result.lower() for keyword in ['analysis', 'kpi', 'metrics', 'recommendation'])
        finally:
            os.unlink(temp_file)
    
    def test_analyze_kpi_report_with_nonexistent_file(self, analyze_kpi_report_tool):
        """Test analyze_kpi_report with a nonexistent file."""
        result = analyze_kpi_report_tool("nonexistent_file.json")
        assert isinstance(result, str)
        # Should handle the error gracefully
        assert len(result) > 0

class TestListAvailableResults:
    """Test list_available_results tool."""
    
    @pytest.fixture
    def list_available_results_tool(self):
        """Get the list_available_results tool."""
        try:
            from src.enhanced_tools import list_available_results
            return list_available_results
        except ImportError:
            pytest.skip("list_available_results tool not available")
    
    def test_list_available_results_basic(self, list_available_results_tool):
        """Test basic functionality of list_available_results."""
        result = list_available_results_tool()
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_list_available_results_returns_file_list(self, list_available_results_tool):
        """Test that list_available_results returns a list of files."""
        result = list_available_results_tool()
        assert isinstance(result, str)
        # Should contain some indication of files or results
        assert any(keyword in result.lower() for keyword in ['file', 'result', 'list', 'available'])

class TestRunComprehensiveHPAnalysis:
    """Test run_comprehensive_hp_analysis tool."""
    
    @pytest.fixture
    def run_comprehensive_hp_analysis_tool(self):
        """Get the run_comprehensive_hp_analysis tool."""
        try:
            from src.enhanced_tools import run_comprehensive_hp_analysis
            return run_comprehensive_hp_analysis
        except ImportError:
            pytest.skip("run_comprehensive_hp_analysis tool not available")
    
    def test_run_comprehensive_hp_analysis_basic(self, run_comprehensive_hp_analysis_tool):
        """Test basic functionality of run_comprehensive_hp_analysis."""
        result = run_comprehensive_hp_analysis_tool("Test Street")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_run_comprehensive_hp_analysis_with_scenario(self, run_comprehensive_hp_analysis_tool):
        """Test run_comprehensive_hp_analysis with a specific scenario."""
        result = run_comprehensive_hp_analysis_tool("Test Street", "winter_werktag_abendspitze")
        assert isinstance(result, str)
        assert len(result) > 0

class TestRunComprehensiveDHAnalysis:
    """Test run_comprehensive_dh_analysis tool."""
    
    @pytest.fixture
    def run_comprehensive_dh_analysis_tool(self):
        """Get the run_comprehensive_dh_analysis tool."""
        try:
            from src.enhanced_tools import run_comprehensive_dh_analysis
            return run_comprehensive_dh_analysis
        except ImportError:
            pytest.skip("run_comprehensive_dh_analysis tool not available")
    
    def test_run_comprehensive_dh_analysis_basic(self, run_comprehensive_dh_analysis_tool):
        """Test basic functionality of run_comprehensive_dh_analysis."""
        result = run_comprehensive_dh_analysis_tool("Test Street")
        assert isinstance(result, str)
        assert len(result) > 0

class TestCompareComprehensiveScenarios:
    """Test compare_comprehensive_scenarios tool."""
    
    @pytest.fixture
    def compare_comprehensive_scenarios_tool(self):
        """Get the compare_comprehensive_scenarios tool."""
        try:
            from src.enhanced_tools import compare_comprehensive_scenarios
            return compare_comprehensive_scenarios
        except ImportError:
            pytest.skip("compare_comprehensive_scenarios tool not available")
    
    def test_compare_comprehensive_scenarios_basic(self, compare_comprehensive_scenarios_tool):
        """Test basic functionality of compare_comprehensive_scenarios."""
        result = compare_comprehensive_scenarios_tool("Test Street")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_compare_comprehensive_scenarios_with_hp_scenario(self, compare_comprehensive_scenarios_tool):
        """Test compare_comprehensive_scenarios with a specific HP scenario."""
        result = compare_comprehensive_scenarios_tool("Test Street", "winter_werktag_abendspitze")
        assert isinstance(result, str)
        assert len(result) > 0

class TestGenerateComprehensiveKpiReport:
    """Test generate_comprehensive_kpi_report tool."""
    
    @pytest.fixture
    def generate_comprehensive_kpi_report_tool(self):
        """Get the generate_comprehensive_kpi_report tool."""
        try:
            from src.enhanced_tools import generate_comprehensive_kpi_report
            return generate_comprehensive_kpi_report
        except ImportError:
            pytest.skip("generate_comprehensive_kpi_report tool not available")
    
    def test_generate_comprehensive_kpi_report_basic(self, generate_comprehensive_kpi_report_tool):
        """Test basic functionality of generate_comprehensive_kpi_report."""
        result = generate_comprehensive_kpi_report_tool("Test Street")
        assert isinstance(result, str)
        assert len(result) > 0

class TestToolIntegration:
    """Test tool integration with ADK agents."""
    
    def test_tools_are_assignable_to_agents(self):
        """Test that tools can be assigned to agents."""
        try:
            from src.enhanced_agents import (
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            from src.enhanced_tools import (
                run_comprehensive_dh_analysis,
                run_comprehensive_hp_analysis,
                compare_comprehensive_scenarios,
                get_all_street_names,
                list_available_results,
                analyze_kpi_report,
                generate_comprehensive_kpi_report
            )
            
            # Check if agents are ADK agents (have config) or SimpleAgent fallback
            agents = [
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            ]
            
            # If any agent has config, test ADK tool assignments
            if any(hasattr(agent, 'config') for agent in agents):
                # Test that tools are properly assigned to agents
                assert run_comprehensive_dh_analysis in CentralHeatingAgent.config['tools']
                assert run_comprehensive_hp_analysis in DecentralizedHeatingAgent.config['tools']
                assert compare_comprehensive_scenarios in ComparisonAgent.config['tools']
                
                # AnalysisAgent should have multiple tools
                aa_tools = AnalysisAgent.config['tools']
                assert run_comprehensive_hp_analysis in aa_tools
                assert run_comprehensive_dh_analysis in aa_tools
                assert compare_comprehensive_scenarios in aa_tools
                assert generate_comprehensive_kpi_report in aa_tools
                
                # DataExplorerAgent should have data exploration tools
                dea_tools = DataExplorerAgent.config['tools']
                assert get_all_street_names in dea_tools
                assert list_available_results in dea_tools
                assert analyze_kpi_report in dea_tools
                
                # EnergyGPT should have analysis tools
                assert analyze_kpi_report in EnergyGPT.config['tools']
            else:
                # SimpleAgent fallback - just verify tools are importable
                assert run_comprehensive_dh_analysis is not None
                assert run_comprehensive_hp_analysis is not None
                assert compare_comprehensive_scenarios is not None
                assert get_all_street_names is not None
                assert list_available_results is not None
                assert analyze_kpi_report is not None
                assert generate_comprehensive_kpi_report is not None
            
        except ImportError:
            pytest.skip("Enhanced agents or tools not available")
    
    def test_tool_function_signatures(self):
        """Test that tool functions have expected signatures."""
        try:
            from src.enhanced_tools import (
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios,
                analyze_kpi_report,
                list_available_results,
                generate_comprehensive_kpi_report
            )
            
            import inspect
            
            # Test function signatures
            sig = inspect.signature(get_all_street_names)
            assert len(sig.parameters) == 0  # No parameters
            
            sig = inspect.signature(get_building_ids_for_street)
            assert len(sig.parameters) == 1  # One parameter (street_name)
            
            sig = inspect.signature(run_comprehensive_hp_analysis)
            assert len(sig.parameters) >= 1  # At least one parameter (street_name)
            
            sig = inspect.signature(run_comprehensive_dh_analysis)
            assert len(sig.parameters) >= 1  # At least one parameter (street_name)
            
            sig = inspect.signature(compare_comprehensive_scenarios)
            assert len(sig.parameters) >= 1  # At least one parameter (street_name)
            
            sig = inspect.signature(analyze_kpi_report)
            assert len(sig.parameters) == 1  # One parameter (kpi_report_path)
            
            sig = inspect.signature(list_available_results)
            assert len(sig.parameters) == 0  # No parameters
            
            sig = inspect.signature(generate_comprehensive_kpi_report)
            assert len(sig.parameters) >= 1  # At least one parameter (street_name)
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

class TestToolErrorHandling:
    """Test tool error handling."""
    
    def test_tools_handle_invalid_inputs_gracefully(self):
        """Test that tools handle invalid inputs gracefully."""
        try:
            from src.enhanced_tools import (
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios,
                analyze_kpi_report,
                generate_comprehensive_kpi_report
            )
            
            # Test with empty string (safer than None)
            result = get_building_ids_for_street("")
            assert isinstance(result, list)  # get_building_ids_for_street returns list
            
            result = run_comprehensive_hp_analysis("")
            assert isinstance(result, str)
            
            result = run_comprehensive_dh_analysis("")
            assert isinstance(result, str)
            
            result = compare_comprehensive_scenarios("")
            assert isinstance(result, str)
            
            result = analyze_kpi_report("")
            assert isinstance(result, str)
            
            result = generate_comprehensive_kpi_report("")
            assert isinstance(result, str)
            
            # Test with invalid file path
            result = analyze_kpi_report("nonexistent_file.json")
            assert isinstance(result, str)
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
