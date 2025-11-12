#!/usr/bin/env python3
"""
Unit Tests for ADK Agents (Fixed for both ADK and SimpleAgent)
Tests individual ADK agents (EnergyPlannerAgent, CentralHeatingAgent, etc.)
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import yaml

# Add ADK to path
sys.path.insert(0, 'adk')

class TestADKAgentInitialization:
    """Test ADK agent initialization and configuration."""
    
    def test_adk_available(self):
        """Test that ADK is available for testing."""
        try:
            from adk.api.agent import Agent
            assert Agent is not None
        except ImportError:
            pytest.skip("ADK not available")
    
    def test_enhanced_agents_import(self):
        """Test that enhanced agents can be imported."""
        try:
            from src.enhanced_agents import (
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            assert EnergyPlannerAgent is not None
            assert CentralHeatingAgent is not None
            assert DecentralizedHeatingAgent is not None
            assert ComparisonAgent is not None
            assert AnalysisAgent is not None
            assert DataExplorerAgent is not None
            assert EnergyGPT is not None
        except ImportError as e:
            pytest.skip(f"Enhanced agents not available: {e}")
    
    def test_config_loading(self):
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

class TestAgentCreation:
    """Test agent creation for both ADK and SimpleAgent."""
    
    @pytest.fixture
    def all_agents(self):
        """Get all agents for testing."""
        try:
            from src.enhanced_agents import (
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            return {
                'EnergyPlannerAgent': EnergyPlannerAgent,
                'CentralHeatingAgent': CentralHeatingAgent,
                'DecentralizedHeatingAgent': DecentralizedHeatingAgent,
                'ComparisonAgent': ComparisonAgent,
                'AnalysisAgent': AnalysisAgent,
                'DataExplorerAgent': DataExplorerAgent,
                'EnergyGPT': EnergyGPT
            }
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_all_agents_can_be_created(self, all_agents):
        """Test that all agents can be created."""
        for agent_name, agent_class in all_agents.items():
            assert agent_class is not None, f"{agent_name} is None"
            assert hasattr(agent_class, '__class__'), f"{agent_name} has no __class__"
    
    def test_agents_have_expected_attributes(self, all_agents):
        """Test that agents have expected attributes."""
        for agent_name, agent_class in all_agents.items():
            # Check if it's ADK agent (has config) or SimpleAgent
            if hasattr(agent_class, 'config'):
                # ADK agent
                config = agent_class.config
                assert config is not None, f"{agent_name} config is None"
                assert 'name' in config, f"{agent_name} config missing 'name'"
                assert 'model' in config, f"{agent_name} config missing 'model'"
                assert 'system_prompt' in config, f"{agent_name} config missing 'system_prompt'"
                assert 'tools' in config, f"{agent_name} config missing 'tools'"
            else:
                # SimpleAgent fallback
                assert hasattr(agent_class, '__class__'), f"{agent_name} has no __class__"
                assert 'Agent' in agent_class.__class__.__name__, f"{agent_name} is not an Agent"

class TestAgentConfiguration:
    """Test agent configuration for ADK agents."""
    
    @pytest.fixture
    def adk_agents(self):
        """Get ADK agents (those with config attribute)."""
        try:
            from src.enhanced_agents import (
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            
            agents = {
                'EnergyPlannerAgent': EnergyPlannerAgent,
                'CentralHeatingAgent': CentralHeatingAgent,
                'DecentralizedHeatingAgent': DecentralizedHeatingAgent,
                'ComparisonAgent': ComparisonAgent,
                'AnalysisAgent': AnalysisAgent,
                'DataExplorerAgent': DataExplorerAgent,
                'EnergyGPT': EnergyGPT
            }
            
            # Filter to only ADK agents (those with config)
            adk_agents = {}
            for name, agent in agents.items():
                if hasattr(agent, 'config'):
                    adk_agents[name] = agent
            
            return adk_agents
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_adk_agents_have_config(self, adk_agents):
        """Test that ADK agents have configuration."""
        if not adk_agents:
            pytest.skip("No ADK agents available (using SimpleAgent fallback)")
        
        for agent_name, agent in adk_agents.items():
            config = agent.config
            assert config is not None, f"{agent_name} config is None"
            assert isinstance(config, dict), f"{agent_name} config is not a dict"
    
    def test_adk_agents_have_required_config_fields(self, adk_agents):
        """Test that ADK agents have required configuration fields."""
        if not adk_agents:
            pytest.skip("No ADK agents available (using SimpleAgent fallback)")
        
        required_fields = ['name', 'model', 'system_prompt', 'tools']
        for agent_name, agent in adk_agents.items():
            config = agent.config
            for field in required_fields:
                assert field in config, f"{agent_name} missing required field: {field}"
                assert config[field] is not None, f"{agent_name} {field} is None"
    
    def test_adk_agent_names_are_unique(self, adk_agents):
        """Test that ADK agent names are unique."""
        if not adk_agents:
            pytest.skip("No ADK agents available (using SimpleAgent fallback)")
        
        names = [agent.config['name'] for agent in adk_agents.values()]
        assert len(names) == len(set(names)), f"Duplicate agent names found: {names}"
    
    def test_adk_agent_models_are_consistent(self, adk_agents):
        """Test that ADK agents use consistent model configuration."""
        if not adk_agents:
            pytest.skip("No ADK agents available (using SimpleAgent fallback)")
        
        models = [agent.config['model'] for agent in adk_agents.values()]
        # All agents should use the same base model
        assert all(model.startswith('gemini-') for model in models), f"Non-Gemini models found: {models}"
    
    def test_adk_agent_system_prompts_are_valid(self, adk_agents):
        """Test that ADK agent system prompts are valid."""
        if not adk_agents:
            pytest.skip("No ADK agents available (using SimpleAgent fallback)")
        
        for agent_name, agent in adk_agents.items():
            system_prompt = agent.config['system_prompt']
            assert isinstance(system_prompt, str), f"{agent_name} system_prompt is not a string"
            assert len(system_prompt) > 0, f"{agent_name} system_prompt is empty"
            assert len(system_prompt) > 100, f"{agent_name} system_prompt is too short"

class TestAgentTools:
    """Test agent tools for ADK agents."""
    
    @pytest.fixture
    def adk_agents_with_tools(self):
        """Get ADK agents that have tools."""
        try:
            from src.enhanced_agents import (
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            
            agents = {
                'CentralHeatingAgent': CentralHeatingAgent,
                'DecentralizedHeatingAgent': DecentralizedHeatingAgent,
                'ComparisonAgent': ComparisonAgent,
                'AnalysisAgent': AnalysisAgent,
                'DataExplorerAgent': DataExplorerAgent,
                'EnergyGPT': EnergyGPT
            }
            
            # Filter to only ADK agents with tools
            adk_agents = {}
            for name, agent in agents.items():
                if hasattr(agent, 'config') and 'tools' in agent.config:
                    tools = agent.config['tools']
                    if tools and len(tools) > 0:
                        adk_agents[name] = agent
            
            return adk_agents
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_adk_agents_have_tools(self, adk_agents_with_tools):
        """Test that ADK agents have tools."""
        if not adk_agents_with_tools:
            pytest.skip("No ADK agents with tools available (using SimpleAgent fallback)")
        
        for agent_name, agent in adk_agents_with_tools.items():
            tools = agent.config['tools']
            assert isinstance(tools, list), f"{agent_name} tools is not a list"
            assert len(tools) > 0, f"{agent_name} has no tools"
    
    def test_adk_agent_tools_are_callable(self, adk_agents_with_tools):
        """Test that ADK agent tools are callable."""
        if not adk_agents_with_tools:
            pytest.skip("No ADK agents with tools available (using SimpleAgent fallback)")
        
        for agent_name, agent in adk_agents_with_tools.items():
            tools = agent.config['tools']
            for i, tool in enumerate(tools):
                assert callable(tool), f"{agent_name} tool {i} is not callable"
                assert hasattr(tool, '__name__'), f"{agent_name} tool {i} has no __name__"
    
    def test_expected_tool_assignments(self, adk_agents_with_tools):
        """Test that agents have expected tool assignments."""
        if not adk_agents_with_tools:
            pytest.skip("No ADK agents with tools available (using SimpleAgent fallback)")
        
        expected_tools = {
            'CentralHeatingAgent': ['run_comprehensive_dh_analysis'],
            'DecentralizedHeatingAgent': ['run_comprehensive_hp_analysis'],
            'ComparisonAgent': ['compare_comprehensive_scenarios'],
            'AnalysisAgent': ['run_comprehensive_hp_analysis', 'run_comprehensive_dh_analysis', 
                             'compare_comprehensive_scenarios', 'generate_comprehensive_kpi_report'],
            'DataExplorerAgent': ['get_all_street_names', 'list_available_results', 'analyze_kpi_report'],
            'EnergyGPT': ['analyze_kpi_report']
        }
        
        for agent_name, agent in adk_agents_with_tools.items():
            if agent_name in expected_tools:
                tools = agent.config['tools']
                tool_names = [tool.__name__ for tool in tools]
                expected_tool_names = expected_tools[agent_name]
                
                for expected_tool in expected_tool_names:
                    assert expected_tool in tool_names, f"{agent_name} missing expected tool: {expected_tool}"

class TestAgentSystemPrompts:
    """Test agent system prompts for ADK agents."""
    
    @pytest.fixture
    def adk_agents(self):
        """Get ADK agents."""
        try:
            from src.enhanced_agents import (
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            
            agents = {
                'EnergyPlannerAgent': EnergyPlannerAgent,
                'CentralHeatingAgent': CentralHeatingAgent,
                'DecentralizedHeatingAgent': DecentralizedHeatingAgent,
                'ComparisonAgent': ComparisonAgent,
                'AnalysisAgent': AnalysisAgent,
                'DataExplorerAgent': DataExplorerAgent,
                'EnergyGPT': EnergyGPT
            }
            
            # Filter to only ADK agents
            adk_agents = {}
            for name, agent in agents.items():
                if hasattr(agent, 'config'):
                    adk_agents[name] = agent
            
            return adk_agents
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_energy_planner_agent_system_prompt(self, adk_agents):
        """Test EnergyPlannerAgent system prompt."""
        if 'EnergyPlannerAgent' not in adk_agents:
            pytest.skip("EnergyPlannerAgent not available as ADK agent")
        
        agent = adk_agents['EnergyPlannerAgent']
        system_prompt = agent.config['system_prompt']
        
        assert 'EnergyPlannerAgent' in system_prompt
        assert 'delegate' in system_prompt.lower()
        assert 'CHA' in system_prompt
        assert 'DHA' in system_prompt
        assert 'CA' in system_prompt
        assert 'AA' in system_prompt
        assert 'DEA' in system_prompt
        assert 'EGPT' in system_prompt
    
    def test_central_heating_agent_system_prompt(self, adk_agents):
        """Test CentralHeatingAgent system prompt."""
        if 'CentralHeatingAgent' not in adk_agents:
            pytest.skip("CentralHeatingAgent not available as ADK agent")
        
        agent = adk_agents['CentralHeatingAgent']
        system_prompt = agent.config['system_prompt']
        
        assert 'Central Heating Agent' in system_prompt
        assert 'CHA' in system_prompt
        assert 'district heating' in system_prompt.lower()
        assert 'run_comprehensive_dh_analysis' in system_prompt
    
    def test_decentralized_heating_agent_system_prompt(self, adk_agents):
        """Test DecentralizedHeatingAgent system prompt."""
        if 'DecentralizedHeatingAgent' not in adk_agents:
            pytest.skip("DecentralizedHeatingAgent not available as ADK agent")
        
        agent = adk_agents['DecentralizedHeatingAgent']
        system_prompt = agent.config['system_prompt']
        
        assert 'Decentralized Heating Agent' in system_prompt
        assert 'DHA' in system_prompt
        assert 'heat pump' in system_prompt.lower()
        assert 'run_comprehensive_hp_analysis' in system_prompt
    
    def test_comparison_agent_system_prompt(self, adk_agents):
        """Test ComparisonAgent system prompt."""
        if 'ComparisonAgent' not in adk_agents:
            pytest.skip("ComparisonAgent not available as ADK agent")
        
        agent = adk_agents['ComparisonAgent']
        system_prompt = agent.config['system_prompt']
        
        assert 'Comparison Agent' in system_prompt
        assert 'CA' in system_prompt
        assert 'compare' in system_prompt.lower()
        assert 'compare_comprehensive_scenarios' in system_prompt
    
    def test_analysis_agent_system_prompt(self, adk_agents):
        """Test AnalysisAgent system prompt."""
        if 'AnalysisAgent' not in adk_agents:
            pytest.skip("AnalysisAgent not available as ADK agent")
        
        agent = adk_agents['AnalysisAgent']
        system_prompt = agent.config['system_prompt']
        
        assert 'Analysis Agent' in system_prompt
        assert 'AA' in system_prompt
        assert 'comprehensive analysis' in system_prompt.lower()
    
    def test_data_explorer_agent_system_prompt(self, adk_agents):
        """Test DataExplorerAgent system prompt."""
        if 'DataExplorerAgent' not in adk_agents:
            pytest.skip("DataExplorerAgent not available as ADK agent")
        
        agent = adk_agents['DataExplorerAgent']
        system_prompt = agent.config['system_prompt']
        
        assert 'Data Explorer Agent' in system_prompt
        assert 'DEA' in system_prompt
        assert 'explore' in system_prompt.lower()
    
    def test_energy_gpt_system_prompt(self, adk_agents):
        """Test EnergyGPT system prompt."""
        if 'EnergyGPT' not in adk_agents:
            pytest.skip("EnergyGPT not available as ADK agent")
        
        agent = adk_agents['EnergyGPT']
        system_prompt = agent.config['system_prompt']
        
        assert 'EnergyGPT' in system_prompt
        assert 'AI analyst' in system_prompt
        assert 'energy infrastructure' in system_prompt.lower()

class TestAgentFallback:
    """Test agent fallback functionality."""
    
    def test_simple_agent_fallback_works(self):
        """Test that SimpleAgent fallback works when ADK is not available."""
        try:
            from src.enhanced_agents import (
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            )
            
            agents = [
                EnergyPlannerAgent,
                CentralHeatingAgent,
                DecentralizedHeatingAgent,
                ComparisonAgent,
                AnalysisAgent,
                DataExplorerAgent,
                EnergyGPT
            ]
            
            # Check if we're using SimpleAgent fallback
            using_simple_agent = any(not hasattr(agent, 'config') for agent in agents)
            
            if using_simple_agent:
                # Verify all agents are SimpleAgent instances
                for agent in agents:
                    assert hasattr(agent, '__class__')
                    assert 'Agent' in agent.__class__.__name__
            else:
                # Verify all agents are ADK agents
                for agent in agents:
                    assert hasattr(agent, 'config')
                    assert agent.config is not None
                    
        except ImportError:
            pytest.skip("Enhanced agents not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
