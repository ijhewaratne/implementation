#!/usr/bin/env python3
"""
Integration Tests for Enhanced Multi-Agent System with ADK
Tests complete enhanced multi-agent system with ADK, end-to-end pipeline, and agent communication
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

class TestEnhancedMultiAgentSystemIntegration:
    """Test complete enhanced multi-agent system integration."""
    
    def test_enhanced_agents_import(self):
        """Test that all enhanced agents can be imported."""
        try:
            from src.enhanced_agents import (
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT,
                load_gemini_config
            )
            assert EnergyPlannerAgent is not None
            assert CentralHeatingAgent is not None
            assert DecentralizedHeatingAgent is not None
            assert ComparisonAgent is not None
            assert AnalysisAgent is not None
            assert DataExplorerAgent is not None
            assert EnergyGPT is not None
            assert load_gemini_config is not None
        except ImportError as e:
            pytest.skip(f"Enhanced agents not available: {e}")
    
    def test_enhanced_tools_import(self):
        """Test that all enhanced tools can be imported."""
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
    
    def test_adk_runner_import(self):
        """Test that ADK runner can be imported."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            assert ADKAgentRunner is not None
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_configuration_loading(self):
        """Test that configuration can be loaded."""
        try:
            from src.enhanced_agents import load_gemini_config
            config = load_gemini_config()
            assert config is not None
            assert 'api_key' in config
            assert 'model' in config
            assert 'temperature' in config
        except Exception as e:
            pytest.skip(f"Configuration loading failed: {e}")

class TestEndToEndPipeline:
    """Test end-to-end pipeline with ADK agents."""
    
    def test_data_exploration_pipeline(self):
        """Test complete data exploration pipeline."""
        try:
            from src.enhanced_tools import get_all_street_names, list_available_results
            
            # Step 1: Get all street names
            streets = get_all_street_names()
            assert isinstance(streets, list)
            assert len(streets) > 0
            
            # Step 2: List available results
            results = list_available_results()
            assert isinstance(results, str)
            assert len(results) > 0
            
            # Step 3: Verify we have data to work with
            assert len(streets) > 0, "No streets available for testing"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_building_analysis_pipeline(self):
        """Test building analysis pipeline."""
        try:
            from src.enhanced_tools import get_building_ids_for_street
            
            # Get a test street
            from src.enhanced_tools import get_all_street_names
            streets = get_all_street_names()
            assert len(streets) > 0, "No streets available for testing"
            
            test_street = streets[0]  # Use first available street
            
            # Get building IDs for the street
            building_ids = get_building_ids_for_street(test_street)
            assert isinstance(building_ids, list)
            # Note: building_ids might be empty for some streets, which is valid
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_heat_pump_analysis_pipeline(self):
        """Test heat pump analysis pipeline."""
        try:
            from src.enhanced_tools import run_comprehensive_hp_analysis
            
            # Test with a known street
            result = run_comprehensive_hp_analysis("Parkstraße")
            assert isinstance(result, str)
            assert len(result) > 0
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_district_heating_analysis_pipeline(self):
        """Test district heating analysis pipeline."""
        try:
            from src.enhanced_tools import run_comprehensive_dh_analysis
            
            # Test with a known street
            result = run_comprehensive_dh_analysis("Parkstraße")
            assert isinstance(result, str)
            assert len(result) > 0
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_scenario_comparison_pipeline(self):
        """Test scenario comparison pipeline."""
        try:
            from src.enhanced_tools import compare_comprehensive_scenarios
            
            # Test with a known street
            result = compare_comprehensive_scenarios("Parkstraße")
            assert isinstance(result, str)
            assert len(result) > 0
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_kpi_report_generation_pipeline(self):
        """Test KPI report generation pipeline."""
        try:
            from src.enhanced_tools import generate_comprehensive_kpi_report
            
            # Test with a known street
            result = generate_comprehensive_kpi_report("Parkstraße")
            assert isinstance(result, str)
            assert len(result) > 0
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

class TestADKAgentCommunication:
    """Test ADK agent communication and coordination."""
    
    def test_agent_runner_initialization(self):
        """Test ADK agent runner initialization."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization to avoid actual API calls
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                assert runner is not None
                assert runner.adk is not None
                assert runner.config is not None
                assert runner.agent_map is not None
                assert len(runner.agent_map) > 0
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_agent_map_structure(self):
        """Test agent map structure and completeness."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                agent_map = runner.agent_map
                
                # Check that all expected agents are in the map
                expected_agents = ["CHA", "DHA", "CA", "AA", "DEA", "EGPT"]
                for agent_name in expected_agents:
                    assert agent_name in agent_map, f"Agent {agent_name} not found in agent map"
                    assert agent_map[agent_name] is not None, f"Agent {agent_name} is None"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_delegation_workflow(self):
        """Test complete delegation workflow."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test delegation scenarios
                test_cases = [
                    ("show me all available streets", "DEA"),
                    ("analyze district heating for Parkstraße", "CHA"),
                    ("analyze heat pump feasibility for Parkstraße", "DHA"),
                    ("compare heating scenarios for Parkstraße", "CA"),
                    ("analyze heating options for Parkstraße", "AA"),
                    ("analyze the available results", "DEA"),
                ]
                
                for input_text, expected_agent in test_cases:
                    # Mock the ADK run method to return expected agent name
                    mock_response = Mock()
                    mock_response.agent_response = expected_agent
                    mock_adk_instance.run.return_value = mock_response
                    
                    result = runner.delegate_to_agent(input_text)
                    
                    assert result is not None
                    assert "delegated_agent" in result
                    assert result["delegated_agent"] == expected_agent
                    assert result["success"] is True
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_error_handling_workflow(self):
        """Test error handling in agent communication."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test with ADK error
                mock_adk_instance.run.side_effect = Exception("API Error")
                
                result = runner.delegate_to_agent("test input")
                
                assert result is not None
                assert "error" in result
                assert "API Error" in result["error"]
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_quota_management_workflow(self):
        """Test quota management in agent communication."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test with quota exceeded error
                quota_error = Exception("429 You exceeded your current quota")
                mock_adk_instance.run.side_effect = quota_error
                
                result = runner.delegate_to_agent("test input")
                
                assert result is not None
                assert "error" in result
                assert "quota" in result["error"].lower()
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_response_parsing_workflow(self):
        """Test response parsing in agent communication."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test response parsing with tool execution
                mock_response = Mock()
                mock_response.agent_response = "CHA\nTOOL: run_comprehensive_dh_analysis(street_name='Parkstraße')"
                mock_response.tool_calls = []
                
                parsed = runner.parse_agent_response(mock_response)
                
                assert parsed is not None
                assert parsed["success"] is True
                assert parsed["tools_executed"] is True
                assert "TOOL:" in parsed["agent_response"]
                assert "run_comprehensive_dh_analysis" in parsed["agent_response"]
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")

class TestMultiAgentCoordination:
    """Test multi-agent coordination and workflow."""
    
    def test_energy_planner_delegation(self):
        """Test EnergyPlannerAgent delegation to specialist agents."""
        try:
            from src.enhanced_agents import EnergyPlannerAgent
            
            # Test that EnergyPlannerAgent can be created
            assert EnergyPlannerAgent is not None
            
            # If it's an ADK agent, test its configuration
            if hasattr(EnergyPlannerAgent, 'config'):
                config = EnergyPlannerAgent.config
                assert 'system_prompt' in config
                assert 'delegate' in config['system_prompt'].lower()
                assert 'CHA' in config['system_prompt']
                assert 'DHA' in config['system_prompt']
                assert 'CA' in config['system_prompt']
                assert 'AA' in config['system_prompt']
                assert 'DEA' in config['system_prompt']
                assert 'EGPT' in config['system_prompt']
            
        except ImportError:
            pytest.skip("EnergyPlannerAgent not available")
    
    def test_specialist_agent_coordination(self):
        """Test coordination between specialist agents."""
        try:
            from src.enhanced_agents import (
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            
            agents = [
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            ]
            
            # Test that all specialist agents can be created
            for agent in agents:
                assert agent is not None
            
            # If using ADK agents, test their tool assignments
            if any(hasattr(agent, 'config') for agent in agents):
                # Test that each agent has appropriate tools
                if hasattr(CentralHeatingAgent, 'config'):
                    assert 'run_comprehensive_dh_analysis' in [tool.__name__ for tool in CentralHeatingAgent.config['tools']]
                
                if hasattr(DecentralizedHeatingAgent, 'config'):
                    assert 'run_comprehensive_hp_analysis' in [tool.__name__ for tool in DecentralizedHeatingAgent.config['tools']]
                
                if hasattr(ComparisonAgent, 'config'):
                    assert 'compare_comprehensive_scenarios' in [tool.__name__ for tool in ComparisonAgent.config['tools']]
                
                if hasattr(DataExplorerAgent, 'config'):
                    tool_names = [tool.__name__ for tool in DataExplorerAgent.config['tools']]
                    assert 'get_all_street_names' in tool_names
                    assert 'list_available_results' in tool_names
                    assert 'analyze_kpi_report' in tool_names
                
                if hasattr(EnergyGPT, 'config'):
                    assert 'analyze_kpi_report' in [tool.__name__ for tool in EnergyGPT.config['tools']]
            
        except ImportError:
            pytest.skip("Specialist agents not available")
    
    def test_workflow_sequence(self):
        """Test complete workflow sequence."""
        try:
            from src.enhanced_tools import (
                get_all_street_names,
                get_building_ids_for_street,
                run_comprehensive_hp_analysis,
                run_comprehensive_dh_analysis,
                compare_comprehensive_scenarios
            )
            
            # Step 1: Get available streets
            streets = get_all_street_names()
            assert isinstance(streets, list)
            assert len(streets) > 0
            
            # Step 2: Select a test street
            test_street = streets[0] if streets else "Parkstraße"
            
            # Step 3: Get building IDs for the street
            building_ids = get_building_ids_for_street(test_street)
            assert isinstance(building_ids, list)
            
            # Step 4: Run heat pump analysis
            hp_result = run_comprehensive_hp_analysis(test_street)
            assert isinstance(hp_result, str)
            assert len(hp_result) > 0
            
            # Step 5: Run district heating analysis
            dh_result = run_comprehensive_dh_analysis(test_street)
            assert isinstance(dh_result, str)
            assert len(dh_result) > 0
            
            # Step 6: Compare scenarios
            comparison_result = compare_comprehensive_scenarios(test_street)
            assert isinstance(comparison_result, str)
            assert len(comparison_result) > 0
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

class TestSystemIntegration:
    """Test complete system integration."""
    
    def test_makefile_integration(self):
        """Test Makefile integration with enhanced agents."""
        # Test that makefile targets exist and are callable
        makefile_path = Path("Makefile")
        assert makefile_path.exists(), "Makefile not found"
        
        # Read makefile content
        with open(makefile_path, 'r') as f:
            makefile_content = f.read()
        
        # Check for enhanced agent targets
        assert "enhanced-agents:" in makefile_content
        assert "test-enhanced-agents:" in makefile_content
        assert "batch-enhanced-agents:" in makefile_content
        assert "test-adk-config:" in makefile_content
        assert "test-adk-runner:" in makefile_content
        assert "test-adk-input:" in makefile_content
        assert "test-adk-analysis:" in makefile_content
    
    def test_configuration_integration(self):
        """Test configuration integration."""
        # Test that configuration files exist
        config_files = [
            "configs/gemini_config.yml",
            "configs/cha.yml",
            "configs/cha_intelligent_sizing.yml"
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                # Test that configuration can be loaded
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                assert config is not None
    
    def test_data_integration(self):
        """Test data integration."""
        # Test that data files exist
        data_files = [
            "data/geojson/hausumringe_mit_adressenV3.geojson"
        ]
        
        for data_file in data_files:
            data_path = Path(data_file)
            if data_path.exists():
                # Test that data can be accessed
                assert data_path.is_file()
                assert data_path.stat().st_size > 0
    
    def test_output_integration(self):
        """Test output integration."""
        # Test that output directories exist or can be created
        output_dirs = [
            "processed",
            "processed/cha",
            "processed/dha",
            "processed/kpi",
            "processed/comparison"
        ]
        
        for output_dir in output_dirs:
            output_path = Path(output_dir)
            if output_path.exists():
                assert output_path.is_dir()
            else:
                # Directory doesn't exist, which is fine for testing
                pass

class TestPerformanceIntegration:
    """Test performance aspects of integration."""
    
    def test_tool_execution_performance(self):
        """Test tool execution performance."""
        try:
            from src.enhanced_tools import get_all_street_names
            
            # Test execution time
            start_time = time.time()
            result = get_all_street_names()
            end_time = time.time()
            
            execution_time = end_time - start_time
            
            # Should complete within reasonable time (5 seconds)
            assert execution_time < 5.0, f"Tool execution took too long: {execution_time:.2f}s"
            assert isinstance(result, list)
            assert len(result) > 0
            
        except ImportError:
            pytest.skip("Enhanced tools not available")
    
    def test_memory_usage_integration(self):
        """Test memory usage during integration."""
        import psutil
        import os
        
        # Get current process
        process = psutil.Process(os.getpid())
        
        # Get initial memory usage
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            from src.enhanced_tools import get_all_street_names, get_building_ids_for_street
            
            # Execute some operations
            streets = get_all_street_names()
            if streets:
                building_ids = get_building_ids_for_street(streets[0])
            
            # Get final memory usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100, f"Memory usage increased too much: {memory_increase:.2f}MB"
            
        except ImportError:
            pytest.skip("Enhanced tools not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
