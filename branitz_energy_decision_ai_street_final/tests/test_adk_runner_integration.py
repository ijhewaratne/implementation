#!/usr/bin/env python3
"""
Integration Tests for ADK Runner
Tests the ADK runner integration with the enhanced multi-agent system
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

class TestADKRunnerIntegration:
    """Test ADK runner integration."""
    
    def test_runner_import_and_initialization(self):
        """Test ADK runner import and initialization."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                # Test initialization
                runner = ADKAgentRunner()
                assert runner is not None
                assert runner.adk is not None
                assert runner.config is not None
                assert runner.agent_map is not None
                assert runner.quota_retry_delay == 60
                assert runner.max_retries == 3
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_runner_agent_map_completeness(self):
        """Test that runner agent map is complete."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                agent_map = runner.agent_map
                
                # Check all expected agents are present
                expected_agents = ["CHA", "DHA", "CA", "AA", "DEA", "EGPT"]
                for agent_name in expected_agents:
                    assert agent_name in agent_map, f"Missing agent: {agent_name}"
                    assert agent_map[agent_name] is not None, f"Agent {agent_name} is None"
                
                # Check agent classes are correct
                from src.enhanced_agents import (
                    CentralHeatingAgent,
                    DecentralizedHeatingAgent,
                    ComparisonAgent,
                    AnalysisAgent,
                    DataExplorerAgent,
                    EnergyGPT
                )
                
                assert agent_map["CHA"] == CentralHeatingAgent
                assert agent_map["DHA"] == DecentralizedHeatingAgent
                assert agent_map["CA"] == ComparisonAgent
                assert agent_map["AA"] == AnalysisAgent
                assert agent_map["DEA"] == DataExplorerAgent
                assert agent_map["EGPT"] == EnergyGPT
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_runner_delegation_workflow(self):
        """Test complete delegation workflow."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test delegation scenarios
                test_scenarios = [
                    {
                        "input": "show me all available streets",
                        "expected_agent": "DEA",
                        "description": "Data exploration request"
                    },
                    {
                        "input": "analyze district heating for Parkstraße",
                        "expected_agent": "CHA",
                        "description": "District heating analysis request"
                    },
                    {
                        "input": "analyze heat pump feasibility for Parkstraße",
                        "expected_agent": "DHA",
                        "description": "Heat pump analysis request"
                    },
                    {
                        "input": "compare heating scenarios for Parkstraße",
                        "expected_agent": "CA",
                        "description": "Scenario comparison request"
                    },
                    {
                        "input": "analyze heating options for Parkstraße",
                        "expected_agent": "AA",
                        "description": "General analysis request"
                    },
                    {
                        "input": "analyze the available results",
                        "expected_agent": "DEA",
                        "description": "Results analysis request"
                    }
                ]
                
                for scenario in test_scenarios:
                    # Mock the ADK run method
                    mock_response = Mock()
                    mock_response.agent_response = scenario["expected_agent"]
                    mock_adk_instance.run.return_value = mock_response
                    
                    # Test delegation
                    result = runner.delegate_to_agent(scenario["input"])
                    
                    # Verify results
                    assert result is not None, f"Delegation failed for: {scenario['description']}"
                    assert "delegated_agent" in result, f"Missing delegated_agent for: {scenario['description']}"
                    assert result["delegated_agent"] == scenario["expected_agent"], f"Wrong agent for: {scenario['description']}"
                    assert result["success"] is True, f"Delegation not successful for: {scenario['description']}"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_runner_error_handling(self):
        """Test runner error handling."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test various error scenarios
                error_scenarios = [
                    {
                        "error": Exception("API Error"),
                        "expected_keyword": "API Error",
                        "description": "General API error"
                    },
                    {
                        "error": Exception("429 You exceeded your current quota"),
                        "expected_keyword": "quota",
                        "description": "Quota exceeded error"
                    },
                    {
                        "error": Exception("Network connection failed"),
                        "expected_keyword": "network",
                        "description": "Network error"
                    }
                ]
                
                for scenario in error_scenarios:
                    # Mock the error
                    mock_adk_instance.run.side_effect = scenario["error"]
                    
                    # Test error handling
                    result = runner.delegate_to_agent("test input")
                    
                    # Verify error handling
                    assert result is not None, f"Error handling failed for: {scenario['description']}"
                    assert "error" in result, f"Missing error field for: {scenario['description']}"
                    assert scenario["expected_keyword"].lower() in result["error"].lower(), f"Wrong error message for: {scenario['description']}"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_runner_response_parsing(self):
        """Test runner response parsing."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test response parsing scenarios
                response_scenarios = [
                    {
                        "response": "CHA\nTOOL: run_comprehensive_dh_analysis(street_name='Parkstraße')",
                        "expected_tools_executed": True,
                        "expected_has_errors": False,
                        "description": "Response with tool execution"
                    },
                    {
                        "response": "DHA\nError: Tool execution failed",
                        "expected_tools_executed": False,
                        "expected_has_errors": True,
                        "description": "Response with errors"
                    },
                    {
                        "response": "DEA\nData exploration completed successfully",
                        "expected_tools_executed": False,
                        "expected_has_errors": False,
                        "description": "Simple response without tools"
                    }
                ]
                
                for scenario in response_scenarios:
                    # Mock the response
                    mock_response = Mock()
                    mock_response.agent_response = scenario["response"]
                    mock_response.tool_calls = []
                    
                    # Test response parsing
                    parsed = runner.parse_agent_response(mock_response)
                    
                    # Verify parsing results
                    assert parsed is not None, f"Parsing failed for: {scenario['description']}"
                    assert parsed["success"] is True, f"Parsing not successful for: {scenario['description']}"
                    assert parsed["tools_executed"] == scenario["expected_tools_executed"], f"Wrong tools_executed for: {scenario['description']}"
                    assert parsed["has_errors"] == scenario["expected_has_errors"], f"Wrong has_errors for: {scenario['description']}"
                    assert parsed["agent_response"] == scenario["response"], f"Wrong agent_response for: {scenario['description']}"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_runner_comprehensive_analysis_methods(self):
        """Test runner comprehensive analysis methods."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test comprehensive analysis methods
                analysis_methods = [
                    {
                        "method": "run_comprehensive_analysis",
                        "args": ("Parkstraße", "auto"),
                        "expected_input": "analyze heating options for Parkstraße",
                        "description": "Auto analysis"
                    },
                    {
                        "method": "run_comprehensive_analysis",
                        "args": ("Parkstraße", "dh"),
                        "expected_input": "analyze district heating for Parkstraße",
                        "description": "District heating analysis"
                    },
                    {
                        "method": "run_comprehensive_analysis",
                        "args": ("Parkstraße", "hp"),
                        "expected_input": "analyze heat pump feasibility for Parkstraße",
                        "description": "Heat pump analysis"
                    },
                    {
                        "method": "run_comprehensive_analysis",
                        "args": ("Parkstraße", "compare"),
                        "expected_input": "compare heating scenarios for Parkstraße",
                        "description": "Scenario comparison"
                    }
                ]
                
                for method_info in analysis_methods:
                    # Mock the delegation method
                    with patch.object(runner, 'delegate_to_agent') as mock_delegate:
                        mock_delegate.return_value = {
                            "success": True,
                            "delegated_agent": "CHA",
                            "agent_response": f"Analysis completed for {method_info['description']}"
                        }
                        
                        # Test the method
                        method = getattr(runner, method_info["method"])
                        result = method(*method_info["args"])
                        
                        # Verify results
                        assert result is not None, f"Method failed for: {method_info['description']}"
                        assert result["success"] is True, f"Method not successful for: {method_info['description']}"
                        assert result["delegated_agent"] == "CHA", f"Wrong delegated agent for: {method_info['description']}"
                        
                        # Verify delegation was called with correct input
                        mock_delegate.assert_called_once()
                        call_args = mock_delegate.call_args[0][0]
                        assert method_info["expected_input"] in call_args, f"Wrong delegation input for: {method_info['description']}"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_runner_data_exploration_methods(self):
        """Test runner data exploration methods."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            
            # Mock ADK initialization
            with patch('agents.copy.run_enhanced_agent_system.ADK') as mock_adk:
                mock_adk_instance = Mock()
                mock_adk.return_value = mock_adk_instance
                
                runner = ADKAgentRunner()
                
                # Test data exploration methods
                exploration_methods = [
                    {
                        "method": "explore_data",
                        "args": ("show me all available streets",),
                        "expected_agent": "DEA",
                        "description": "Data exploration"
                    },
                    {
                        "method": "analyze_results",
                        "args": (),
                        "expected_agent": "DEA",
                        "description": "Results analysis"
                    }
                ]
                
                for method_info in exploration_methods:
                    # Mock the delegation method
                    with patch.object(runner, 'delegate_to_agent') as mock_delegate:
                        mock_delegate.return_value = {
                            "success": True,
                            "delegated_agent": method_info["expected_agent"],
                            "agent_response": f"Exploration completed for {method_info['description']}"
                        }
                        
                        # Test the method
                        method = getattr(runner, method_info["method"])
                        result = method(*method_info["args"])
                        
                        # Verify results
                        assert result is not None, f"Method failed for: {method_info['description']}"
                        assert result["success"] is True, f"Method not successful for: {method_info['description']}"
                        assert result["delegated_agent"] == method_info["expected_agent"], f"Wrong delegated agent for: {method_info['description']}"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_runner_retry_logic(self):
        """Test runner retry logic."""
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
                    assert mock_adk_instance.run.call_count == 2
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")
    
    def test_runner_agent_communication(self):
        """Test runner agent communication."""
        try:
            from agents.copy.run_enhanced_agent_system import ADKAgentRunner
            from src.enhanced_agents import DataExplorerAgent, CentralHeatingAgent
            
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
                response = runner.adk.run(DataExplorerAgent, "list all streets")
                assert response is not None
                assert response.agent_response == "Data exploration completed"
                
                # Test with CentralHeatingAgent
                mock_response.agent_response = "District heating analysis completed"
                response = runner.adk.run(CentralHeatingAgent, "analyze district heating for Parkstraße")
                assert response is not None
                assert response.agent_response == "District heating analysis completed"
                
        except ImportError:
            pytest.skip("ADKAgentRunner not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
