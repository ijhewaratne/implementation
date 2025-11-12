#!/usr/bin/env python3
"""
Unit Tests for ADK Agent Delegation
Tests agent delegation functionality with ADK
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

# Add ADK to path
sys.path.insert(0, 'adk')

class TestADKAgentDelegation:
    """Test ADK agent delegation functionality."""
    
    def test_adk_runner_import(self):
        """Test that ADK runner can be imported."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            assert ADKAgentRunner is not None
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_adk_runner_initialization(self):
        """Test ADKAgentRunner initialization."""
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
    
    def test_agent_map_contains_expected_agents(self):
        """Test that agent map contains expected agents."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                agent_map = runner.agent_map
                
                expected_agents = ["CHA", "DHA", "CA", "AA", "DEA", "EGPT"]
                for agent_name in expected_agents:
                    assert agent_name in agent_map, f"Agent {agent_name} not found in agent map"
                    assert agent_map[agent_name] is not None, f"Agent {agent_name} is None"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_delegation_logic_with_mock_responses(self):
        """Test delegation logic with mock responses."""
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
    
    def test_error_handling_in_delegation(self):
        """Test error handling in delegation."""
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
    
    def test_quota_error_handling(self):
        """Test quota error handling in delegation."""
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
    
    def test_network_error_handling(self):
        """Test network error handling in delegation."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test with network error
                network_error = Exception("Network connection failed")
                mock_adk_instance.run.side_effect = network_error
                
                result = runner.delegate_to_agent("test input")
                
                assert result is not None
                assert "error" in result
                assert "network" in result["error"].lower()
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_response_parsing(self):
        """Test response parsing functionality."""
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
    
    def test_response_parsing_with_errors(self):
        """Test response parsing with errors."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test response parsing with errors
                mock_response = Mock()
                mock_response.agent_response = "CHA\nError: Tool execution failed"
                mock_response.tool_calls = []
                
                parsed = runner.parse_agent_response(mock_response)
                
                assert parsed is not None
                assert parsed["success"] is True
                assert parsed["has_errors"] is True
                assert "Error:" in parsed["agent_response"]
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_comprehensive_analysis_methods(self):
        """Test comprehensive analysis methods."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test comprehensive analysis methods
                test_cases = [
                    ("auto", "analyze heating options for Parkstraße"),
                    ("dh", "analyze district heating for Parkstraße"),
                    ("hp", "analyze heat pump feasibility for Parkstraße"),
                    ("compare", "compare heating scenarios for Parkstraße"),
                ]
                
                for analysis_type, expected_input in test_cases:
                    # Mock the delegation method
                    with patch.object(runner, 'delegate_to_agent') as mock_delegate:
                        mock_delegate.return_value = {
                            "success": True,
                            "delegated_agent": "CHA",
                            "agent_response": f"Analysis completed for {analysis_type}"
                        }
                        
                        result = runner.run_comprehensive_analysis("Parkstraße", analysis_type)
                        
                        assert result is not None
                        assert result["success"] is True
                        assert result["delegated_agent"] == "CHA"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_data_exploration_methods(self):
        """Test data exploration methods."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test explore_data method
                with patch.object(runner, 'delegate_to_agent') as mock_delegate:
                    mock_delegate.return_value = {
                        "success": True,
                        "delegated_agent": "DEA",
                        "agent_response": "Data exploration completed"
                    }
                    
                    result = runner.explore_data("show me all available streets")
                    
                    assert result is not None
                    assert result["success"] is True
                    assert result["delegated_agent"] == "DEA"
                
                # Test analyze_results method
                with patch.object(runner, 'delegate_to_agent') as mock_delegate:
                    mock_delegate.return_value = {
                        "success": True,
                        "delegated_agent": "DEA",
                        "agent_response": "Results analysis completed"
                    }
                    
                    result = runner.analyze_results()
                    
                    assert result is not None
                    assert result["success"] is True
                    assert result["delegated_agent"] == "DEA"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_retry_logic(self):
        """Test retry logic for failed requests."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test retry logic with quota error
                quota_error = Exception("429 You exceeded your current quota")
                success_response = Mock()
                success_response.agent_response = "CHA"
                
                # First call fails, second call succeeds
                mock_adk_instance.run.side_effect = [quota_error, success_response]
                
                # Mock time.sleep to avoid actual delays
                with patch('time.sleep'):
                    result = runner.run_agent_with_retry(Mock(), "test input")
                    
                    assert result is not None
                    assert result.agent_response == "CHA"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_agent_communication(self):
        """Test direct agent communication."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test direct agent communication
                mock_response = Mock()
                mock_response.agent_response = "Data exploration completed"
                mock_adk_instance.run.return_value = mock_response
                
                # Test with DataExplorerAgent
                from src.enhanced_agents import DataExplorerAgent
                response = runner.adk.run(DataExplorerAgent, "list all streets")
                
                assert response is not None
                assert response.agent_response == "Data exploration completed"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")

class TestAgentDelegationPatterns:
    """Test specific agent delegation patterns."""
    
    def test_district_heating_delegation(self):
        """Test delegation for district heating queries."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test district heating delegation
                mock_response = Mock()
                mock_response.agent_response = "CHA"
                mock_adk_instance.run.return_value = mock_response
                
                result = runner.delegate_to_agent("analyze district heating for Parkstraße")
                
                assert result is not None
                assert result["delegated_agent"] == "CHA"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_heat_pump_delegation(self):
        """Test delegation for heat pump queries."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test heat pump delegation
                mock_response = Mock()
                mock_response.agent_response = "DHA"
                mock_adk_instance.run.return_value = mock_response
                
                result = runner.delegate_to_agent("analyze heat pump feasibility for Parkstraße")
                
                assert result is not None
                assert result["delegated_agent"] == "DHA"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_comparison_delegation(self):
        """Test delegation for comparison queries."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test comparison delegation
                mock_response = Mock()
                mock_response.agent_response = "CA"
                mock_adk_instance.run.return_value = mock_response
                
                result = runner.delegate_to_agent("compare heating scenarios for Parkstraße")
                
                assert result is not None
                assert result["delegated_agent"] == "CA"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_data_exploration_delegation(self):
        """Test delegation for data exploration queries."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test data exploration delegation
                mock_response = Mock()
                mock_response.agent_response = "DEA"
                mock_adk_instance.run.return_value = mock_response
                
                result = runner.delegate_to_agent("show me all available streets")
                
                assert result is not None
                assert result["delegated_agent"] == "DEA"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
