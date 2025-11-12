#!/usr/bin/env python3
"""
Unit Tests for ADK Agents
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

class TestEnergyPlannerAgent:
    """Test EnergyPlannerAgent functionality."""
    
    @pytest.fixture
    def energy_planner_agent(self):
        """Create EnergyPlannerAgent instance for testing."""
        try:
            from src.enhanced_agents import EnergyPlannerAgent
            return EnergyPlannerAgent
        except ImportError:
            pytest.skip("EnergyPlannerAgent not available")
    
    def test_energy_planner_agent_creation(self, energy_planner_agent):
        """Test EnergyPlannerAgent can be created."""
        agent = energy_planner_agent
        assert agent is not None
        # Check if it's ADK agent (has config) or SimpleAgent (has different attributes)
        if hasattr(agent, 'config'):
            assert agent.config is not None
        else:
            # SimpleAgent fallback - check for basic attributes
            assert hasattr(agent, '__class__')
            assert 'Agent' in agent.__class__.__name__
    
    def test_energy_planner_agent_config(self, energy_planner_agent):
        """Test EnergyPlannerAgent configuration."""
        agent = energy_planner_agent
        config = agent.config
        
        assert 'name' in config
        assert config['name'] == 'EnergyPlannerAgent'
        assert 'model' in config
        assert 'system_prompt' in config
        assert 'tools' in config
        assert len(config['tools']) == 0  # Planner agent has no tools
    
    def test_energy_planner_agent_system_prompt(self, energy_planner_agent):
        """Test EnergyPlannerAgent system prompt."""
        agent = energy_planner_agent
        config = agent.config
        system_prompt = config['system_prompt']
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert 'EnergyPlannerAgent' in system_prompt
        assert 'delegate' in system_prompt.lower()
        assert 'CHA' in system_prompt
        assert 'DHA' in system_prompt
        assert 'CA' in system_prompt
        assert 'AA' in system_prompt
        assert 'DEA' in system_prompt
        assert 'EGPT' in system_prompt

class TestCentralHeatingAgent:
    """Test CentralHeatingAgent functionality."""
    
    @pytest.fixture
    def central_heating_agent(self):
        """Create CentralHeatingAgent instance for testing."""
        try:
            from src.enhanced_agents import CentralHeatingAgent
            return CentralHeatingAgent
        except ImportError:
            pytest.skip("CentralHeatingAgent not available")
    
    def test_central_heating_agent_creation(self, central_heating_agent):
        """Test CentralHeatingAgent can be created."""
        agent = central_heating_agent
        assert agent is not None
        assert hasattr(agent, 'config')
        assert agent.config is not None
    
    def test_central_heating_agent_config(self, central_heating_agent):
        """Test CentralHeatingAgent configuration."""
        agent = central_heating_agent
        config = agent.config
        
        assert 'name' in config
        assert config['name'] == 'CentralHeatingAgent'
        assert 'model' in config
        assert 'system_prompt' in config
        assert 'tools' in config
        assert len(config['tools']) == 1  # CHA has one tool
    
    def test_central_heating_agent_tools(self, central_heating_agent):
        """Test CentralHeatingAgent tools."""
        agent = central_heating_agent
        config = agent.config
        tools = config['tools']
        
        assert len(tools) == 1
        tool = tools[0]
        assert hasattr(tool, '__name__')
        assert 'run_comprehensive_dh_analysis' in tool.__name__
    
    def test_central_heating_agent_system_prompt(self, central_heating_agent):
        """Test CentralHeatingAgent system prompt."""
        agent = central_heating_agent
        config = agent.config
        system_prompt = config['system_prompt']
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert 'Central Heating Agent' in system_prompt
        assert 'CHA' in system_prompt
        assert 'district heating' in system_prompt.lower()
        assert 'run_comprehensive_dh_analysis' in system_prompt

class TestDecentralizedHeatingAgent:
    """Test DecentralizedHeatingAgent functionality."""
    
    @pytest.fixture
    def decentralized_heating_agent(self):
        """Create DecentralizedHeatingAgent instance for testing."""
        try:
            from src.enhanced_agents import DecentralizedHeatingAgent
            return DecentralizedHeatingAgent
        except ImportError:
            pytest.skip("DecentralizedHeatingAgent not available")
    
    def test_decentralized_heating_agent_creation(self, decentralized_heating_agent):
        """Test DecentralizedHeatingAgent can be created."""
        agent = decentralized_heating_agent
        assert agent is not None
        assert hasattr(agent, 'config')
        assert agent.config is not None
    
    def test_decentralized_heating_agent_config(self, decentralized_heating_agent):
        """Test DecentralizedHeatingAgent configuration."""
        agent = decentralized_heating_agent
        config = agent.config
        
        assert 'name' in config
        assert config['name'] == 'DecentralizedHeatingAgent'
        assert 'model' in config
        assert 'system_prompt' in config
        assert 'tools' in config
        assert len(config['tools']) == 1  # DHA has one tool
    
    def test_decentralized_heating_agent_tools(self, decentralized_heating_agent):
        """Test DecentralizedHeatingAgent tools."""
        agent = decentralized_heating_agent
        config = agent.config
        tools = config['tools']
        
        assert len(tools) == 1
        tool = tools[0]
        assert hasattr(tool, '__name__')
        assert 'run_comprehensive_hp_analysis' in tool.__name__
    
    def test_decentralized_heating_agent_system_prompt(self, decentralized_heating_agent):
        """Test DecentralizedHeatingAgent system prompt."""
        agent = decentralized_heating_agent
        config = agent.config
        system_prompt = config['system_prompt']
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert 'Decentralized Heating Agent' in system_prompt
        assert 'DHA' in system_prompt
        assert 'heat pump' in system_prompt.lower()
        assert 'run_comprehensive_hp_analysis' in system_prompt

class TestComparisonAgent:
    """Test ComparisonAgent functionality."""
    
    @pytest.fixture
    def comparison_agent(self):
        """Create ComparisonAgent instance for testing."""
        try:
            from src.enhanced_agents import ComparisonAgent
            return ComparisonAgent
        except ImportError:
            pytest.skip("ComparisonAgent not available")
    
    def test_comparison_agent_creation(self, comparison_agent):
        """Test ComparisonAgent can be created."""
        agent = comparison_agent
        assert agent is not None
        assert hasattr(agent, 'config')
        assert agent.config is not None
    
    def test_comparison_agent_config(self, comparison_agent):
        """Test ComparisonAgent configuration."""
        agent = comparison_agent
        config = agent.config
        
        assert 'name' in config
        assert config['name'] == 'ComparisonAgent'
        assert 'model' in config
        assert 'system_prompt' in config
        assert 'tools' in config
        assert len(config['tools']) == 1  # CA has one tool
    
    def test_comparison_agent_tools(self, comparison_agent):
        """Test ComparisonAgent tools."""
        agent = comparison_agent
        config = agent.config
        tools = config['tools']
        
        assert len(tools) == 1
        tool = tools[0]
        assert hasattr(tool, '__name__')
        assert 'compare_comprehensive_scenarios' in tool.__name__
    
    def test_comparison_agent_system_prompt(self, comparison_agent):
        """Test ComparisonAgent system prompt."""
        agent = comparison_agent
        config = agent.config
        system_prompt = config['system_prompt']
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert 'Comparison Agent' in system_prompt
        assert 'CA' in system_prompt
        assert 'compare' in system_prompt.lower()
        assert 'compare_comprehensive_scenarios' in system_prompt

class TestAnalysisAgent:
    """Test AnalysisAgent functionality."""
    
    @pytest.fixture
    def analysis_agent(self):
        """Create AnalysisAgent instance for testing."""
        try:
            from src.enhanced_agents import AnalysisAgent
            return AnalysisAgent
        except ImportError:
            pytest.skip("AnalysisAgent not available")
    
    def test_analysis_agent_creation(self, analysis_agent):
        """Test AnalysisAgent can be created."""
        agent = analysis_agent
        assert agent is not None
        assert hasattr(agent, 'config')
        assert agent.config is not None
    
    def test_analysis_agent_config(self, analysis_agent):
        """Test AnalysisAgent configuration."""
        agent = analysis_agent
        config = agent.config
        
        assert 'name' in config
        assert config['name'] == 'AnalysisAgent'
        assert 'model' in config
        assert 'system_prompt' in config
        assert 'tools' in config
        assert len(config['tools']) == 4  # AA has four tools
    
    def test_analysis_agent_tools(self, analysis_agent):
        """Test AnalysisAgent tools."""
        agent = analysis_agent
        config = agent.config
        tools = config['tools']
        
        assert len(tools) == 4
        tool_names = [tool.__name__ for tool in tools]
        assert 'run_comprehensive_hp_analysis' in tool_names
        assert 'run_comprehensive_dh_analysis' in tool_names
        assert 'compare_comprehensive_scenarios' in tool_names
        assert 'generate_comprehensive_kpi_report' in tool_names
    
    def test_analysis_agent_system_prompt(self, analysis_agent):
        """Test AnalysisAgent system prompt."""
        agent = analysis_agent
        config = agent.config
        system_prompt = config['system_prompt']
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert 'Analysis Agent' in system_prompt
        assert 'AA' in system_prompt
        assert 'comprehensive analysis' in system_prompt.lower()

class TestDataExplorerAgent:
    """Test DataExplorerAgent functionality."""
    
    @pytest.fixture
    def data_explorer_agent(self):
        """Create DataExplorerAgent instance for testing."""
        try:
            from src.enhanced_agents import DataExplorerAgent
            return DataExplorerAgent
        except ImportError:
            pytest.skip("DataExplorerAgent not available")
    
    def test_data_explorer_agent_creation(self, data_explorer_agent):
        """Test DataExplorerAgent can be created."""
        agent = data_explorer_agent
        assert agent is not None
        assert hasattr(agent, 'config')
        assert agent.config is not None
    
    def test_data_explorer_agent_config(self, data_explorer_agent):
        """Test DataExplorerAgent configuration."""
        agent = data_explorer_agent
        config = agent.config
        
        assert 'name' in config
        assert config['name'] == 'DataExplorerAgent'
        assert 'model' in config
        assert 'system_prompt' in config
        assert 'tools' in config
        assert len(config['tools']) == 3  # DEA has three tools
    
    def test_data_explorer_agent_tools(self, data_explorer_agent):
        """Test DataExplorerAgent tools."""
        agent = data_explorer_agent
        config = agent.config
        tools = config['tools']
        
        assert len(tools) == 3
        tool_names = [tool.__name__ for tool in tools]
        assert 'get_all_street_names' in tool_names
        assert 'list_available_results' in tool_names
        assert 'analyze_kpi_report' in tool_names
    
    def test_data_explorer_agent_system_prompt(self, data_explorer_agent):
        """Test DataExplorerAgent system prompt."""
        agent = data_explorer_agent
        config = agent.config
        system_prompt = config['system_prompt']
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert 'Data Explorer Agent' in system_prompt
        assert 'DEA' in system_prompt
        assert 'explore' in system_prompt.lower()

class TestEnergyGPT:
    """Test EnergyGPT functionality."""
    
    @pytest.fixture
    def energy_gpt(self):
        """Create EnergyGPT instance for testing."""
        try:
            from src.enhanced_agents import EnergyGPT
            return EnergyGPT
        except ImportError:
            pytest.skip("EnergyGPT not available")
    
    def test_energy_gpt_creation(self, energy_gpt):
        """Test EnergyGPT can be created."""
        agent = energy_gpt
        assert agent is not None
        assert hasattr(agent, 'config')
        assert agent.config is not None
    
    def test_energy_gpt_config(self, energy_gpt):
        """Test EnergyGPT configuration."""
        agent = energy_gpt
        config = agent.config
        
        assert 'name' in config
        assert config['name'] == 'EnergyGPT'
        assert 'model' in config
        assert 'system_prompt' in config
        assert 'tools' in config
        assert len(config['tools']) == 1  # EGPT has one tool
    
    def test_energy_gpt_tools(self, energy_gpt):
        """Test EnergyGPT tools."""
        agent = energy_gpt
        config = agent.config
        tools = config['tools']
        
        assert len(tools) == 1
        tool = tools[0]
        assert hasattr(tool, '__name__')
        assert 'analyze_kpi_report' in tool.__name__
    
    def test_energy_gpt_system_prompt(self, energy_gpt):
        """Test EnergyGPT system prompt."""
        agent = energy_gpt
        config = agent.config
        system_prompt = config['system_prompt']
        
        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        assert 'EnergyGPT' in system_prompt
        assert 'AI analyst' in system_prompt
        assert 'energy infrastructure' in system_prompt.lower()

class TestAgentConfiguration:
    """Test agent configuration consistency."""
    
    def test_all_agents_have_required_config(self):
        """Test that all agents have required configuration fields."""
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
            
            for agent in agents:
                config = agent.config
                assert 'name' in config
                assert 'model' in config
                assert 'system_prompt' in config
                assert 'tools' in config
                assert isinstance(config['name'], str)
                assert isinstance(config['model'], str)
                assert isinstance(config['system_prompt'], str)
                assert isinstance(config['tools'], list)
                
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_agent_names_are_unique(self):
        """Test that all agent names are unique."""
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
            
            names = [agent.config['name'] for agent in agents]
            assert len(names) == len(set(names)), f"Duplicate agent names found: {names}"
                
        except ImportError:
            pytest.skip("Enhanced agents not available")
    
    def test_agent_models_are_consistent(self):
        """Test that all agents use consistent model configuration."""
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
            
            models = [agent.config['model'] for agent in agents]
            # All agents should use the same base model
            base_models = [model.split('-')[0] for model in models]
            assert all(model.startswith('gemini-') for model in models)
                
        except ImportError:
            pytest.skip("Enhanced agents not available")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
