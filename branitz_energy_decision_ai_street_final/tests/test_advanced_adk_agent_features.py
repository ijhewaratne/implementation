#!/usr/bin/env python3
"""
Test Suite for Advanced ADK Agent Features
Comprehensive testing of advanced agent capabilities, tool chaining, and memory/context systems.
"""

import pytest
import os
import sys
import time
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import advanced ADK agent components
from src.enhanced_agents_advanced import (
    AdvancedADKAgent,
    AgentMemoryManager,
    AgentContextManager,
    LearningEngine,
    AdaptiveStrategy,
    AgentMemory,
    AgentContext
)

from src.advanced_tool_chaining import (
    ToolRegistry,
    DependencyResolver,
    WorkflowEngine,
    ExecutionMonitor,
    ResultAggregator,
    ToolStep,
    ToolResult
)

from src.agent_memory_context import (
    SessionMemory,
    LearningMemory,
    UserProfiles,
    ContextPersistence,
    ConversationContext,
    AnalysisContext,
    UserContext,
    SystemContext,
    MemoryEntry,
    ContextSnapshot
)

class TestAdvancedADKAgent:
    """Test AdvancedADKAgent functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'name': 'TestAgent',
            'model': 'gemini-1.5-flash-latest',
            'system_prompt': 'You are a test agent.',
            'temperature': 0.7
        }
        
        # Mock ADK Agent
        self.mock_agent = Mock()
        self.mock_agent.run.return_value = Mock(agent_response="Test response")
        
        with patch('src.enhanced_agents_advanced.Agent', return_value=self.mock_agent):
            self.agent = AdvancedADKAgent('TestAgent', self.config)
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        assert self.agent.agent_type == 'TestAgent'
        assert self.agent.config == self.config
        assert self.agent.memory is not None
        assert self.agent.context is not None
        assert self.agent.learning_engine is not None
        assert self.agent.adaptive_strategy is not None
    
    def test_process_request_success(self):
        """Test successful request processing."""
        request = "Analyze district heating for Parkstraße"
        
        result = self.agent.process_request(request)
        
        assert result['success'] is True
        assert 'agent_response' in result
        assert result['agent_type'] == 'TestAgent'
        assert 'timestamp' in result
        assert 'strategy_used' in result
    
    def test_process_request_with_context(self):
        """Test request processing with additional context."""
        request = "Compare heating scenarios"
        additional_context = {'user_id': 'test_user', 'session_id': 'test_session'}
        
        result = self.agent.process_request(request, additional_context)
        
        assert result['success'] is True
        assert result['context_enhanced'] is True
    
    def test_memory_integration(self):
        """Test memory integration in request processing."""
        # First request
        request1 = "Analyze district heating for Parkstraße"
        result1 = self.agent.process_request(request1)
        
        # Second similar request
        request2 = "Analyze district heating for Hauptstraße"
        result2 = self.agent.process_request(request2)
        
        assert result1['success'] is True
        assert result2['success'] is True
        assert result2['memory_enhanced'] is True
    
    def test_adaptive_strategy_selection(self):
        """Test adaptive strategy selection."""
        # Simple request should use aggressive strategy
        simple_request = "Show me streets"
        result1 = self.agent.process_request(simple_request)
        
        # Complex request should use conservative strategy
        complex_request = "Analyze comprehensive district heating network with detailed hydraulic simulation and economic analysis"
        result2 = self.agent.process_request(complex_request)
        
        assert result1['success'] is True
        assert result2['success'] is True
        # Strategy selection is tested in the adaptive strategy tests
    
    def test_agent_status(self):
        """Test agent status reporting."""
        # Process a few requests to generate data
        self.agent.process_request("Test request 1")
        self.agent.process_request("Test request 2")
        
        status = self.agent.get_agent_status()
        
        assert status['agent_type'] == 'TestAgent'
        assert 'memory_entries' in status
        assert 'conversation_history' in status
        assert 'learning_insights' in status
        assert 'current_strategy' in status
        assert 'performance_metrics' in status
        assert 'adk_available' in status

class TestAgentMemoryManager:
    """Test AgentMemoryManager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.memory_file = os.path.join(self.temp_dir, 'test_memory.pkl')
        self.memory_manager = AgentMemoryManager(self.memory_file)
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_memory_initialization(self):
        """Test memory manager initialization."""
        assert self.memory_manager.memory_file == Path(self.memory_file)
        assert len(self.memory_manager.memories) == 0
        assert len(self.memory_manager.memory_index) == 0
    
    def test_add_memory(self):
        """Test adding memory entries."""
        memory = AgentMemory(
            session_id='test_session',
            timestamp=datetime.now(),
            request='Test request',
            response='Test response',
            context={'test': 'context'},
            performance_metrics={'response_time': 1.5}
        )
        
        self.memory_manager.add_memory(memory)
        
        assert len(self.memory_manager.memories) == 1
        assert len(self.memory_manager.memory_index) > 0
    
    def test_get_relevant_memories(self):
        """Test retrieving relevant memories."""
        # Add some test memories
        memory1 = AgentMemory(
            session_id='test_session',
            timestamp=datetime.now(),
            request='Analyze district heating',
            response='District heating analysis result',
            context={'type': 'analysis'},
            performance_metrics={'response_time': 2.0}
        )
        
        memory2 = AgentMemory(
            session_id='test_session',
            timestamp=datetime.now(),
            request='Show heat pump data',
            response='Heat pump data result',
            context={'type': 'data'},
            performance_metrics={'response_time': 1.0}
        )
        
        self.memory_manager.add_memory(memory1)
        self.memory_manager.add_memory(memory2)
        
        # Test relevant memory retrieval
        relevant_memories = self.memory_manager.get_relevant_memories('Analyze district heating network')
        
        assert len(relevant_memories) > 0
        assert any('district heating' in memory.request.lower() for memory in relevant_memories)
    
    def test_memory_persistence(self):
        """Test memory persistence to disk."""
        memory = AgentMemory(
            session_id='test_session',
            timestamp=datetime.now(),
            request='Test request',
            response='Test response',
            context={'test': 'context'},
            performance_metrics={'response_time': 1.5}
        )
        
        self.memory_manager.add_memory(memory)
        
        # Create new memory manager and load from disk
        new_memory_manager = AgentMemoryManager(self.memory_file)
        
        assert len(new_memory_manager.memories) == 1
        assert new_memory_manager.memories[0].request == 'Test request'

class TestAgentContextManager:
    """Test AgentContextManager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.context_manager = AgentContextManager()
    
    def test_context_enhancement(self):
        """Test context enhancement."""
        request = "Analyze district heating for Parkstraße"
        additional_context = {'user_id': 'test_user'}
        
        enhanced_context = self.context_manager.enhance_context(request, additional_context)
        
        assert enhanced_context['request'] == request
        assert enhanced_context['user_id'] == 'test_user'
        assert 'timestamp' in enhanced_context
        assert 'request_type' in enhanced_context
        assert 'complexity_level' in enhanced_context
        assert 'conversation_history' in enhanced_context
        assert 'user_preferences' in enhanced_context
    
    def test_request_classification(self):
        """Test request type classification."""
        # Test analysis request
        analysis_request = "Analyze district heating network"
        enhanced_context = self.context_manager.enhance_context(analysis_request)
        assert enhanced_context['request_type'] == 'analysis'
        
        # Test comparison request
        comparison_request = "Compare heating scenarios"
        enhanced_context = self.context_manager.enhance_context(comparison_request)
        assert enhanced_context['request_type'] == 'comparison'
        
        # Test exploration request
        exploration_request = "Show me all available streets"
        enhanced_context = self.context_manager.enhance_context(exploration_request)
        assert enhanced_context['request_type'] == 'exploration'
    
    def test_complexity_assessment(self):
        """Test request complexity assessment."""
        # Simple request
        simple_request = "Show streets"
        enhanced_context = self.context_manager.enhance_context(simple_request)
        assert enhanced_context['complexity_level'] == 'simple'
        
        # Medium request
        medium_request = "Analyze district heating for Parkstraße with basic parameters"
        enhanced_context = self.context_manager.enhance_context(medium_request)
        assert enhanced_context['complexity_level'] == 'medium'
        
        # Complex request
        complex_request = "Analyze comprehensive district heating network with detailed hydraulic simulation, economic analysis, and environmental impact assessment"
        enhanced_context = self.context_manager.enhance_context(complex_request)
        assert enhanced_context['complexity_level'] == 'complex'
    
    def test_context_update(self):
        """Test context update after interaction."""
        request = "Analyze district heating"
        response = "District heating analysis completed"
        metadata = {'analysis_type': 'district_heating', 'success': True}
        
        self.context_manager.update_context(request, response, metadata)
        
        assert len(self.context_manager.conversation_history) == 1
        assert self.context_manager.conversation_history[0]['request'] == request
        assert self.context_manager.conversation_history[0]['response'] == response
        assert self.context_manager.conversation_history[0]['metadata'] == metadata
    
    def test_user_preference_learning(self):
        """Test user preference learning."""
        # First interaction - district heating
        request1 = "Analyze district heating for Parkstraße"
        response1 = "Comprehensive district heating analysis with detailed network design, hydraulic simulation, and economic evaluation including CAPEX, OPEX, and LCOH calculations."
        self.context_manager.update_context(request1, response1)
        
        # Check preferences
        preferences = self.context_manager.user_preferences
        assert preferences['preferred_analysis_type'] == 'district_heating'
        assert preferences['detail_level'] == 'high'
        
        # Second interaction - heat pump
        request2 = "Analyze heat pump feasibility"
        response2 = "Heat pump analysis completed."
        self.context_manager.update_context(request2, response2)
        
        # Preferences should update
        preferences = self.context_manager.user_preferences
        assert preferences['preferred_analysis_type'] == 'heat_pump'

class TestLearningEngine:
    """Test LearningEngine functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.learning_engine = LearningEngine()
    
    def test_learning_initialization(self):
        """Test learning engine initialization."""
        assert len(self.learning_engine.learning_data) == 0
        assert len(self.learning_engine.performance_patterns) == 0
        assert len(self.learning_engine.success_patterns) == 0
        assert len(self.learning_engine.improvement_suggestions) == 0
    
    def test_learn_from_interaction(self):
        """Test learning from interactions."""
        request = "Analyze district heating for Parkstraße"
        result = {
            'success': True,
            'response_time': 2.5,
            'user_satisfaction': 'high'
        }
        
        self.learning_engine.learn_from_interaction(request, result)
        
        assert len(self.learning_engine.learning_data) == 1
        assert self.learning_engine.learning_data[0]['request'] == request
        assert self.learning_engine.learning_data[0]['success'] is True
        assert self.learning_engine.learning_data[0]['response_time'] == 2.5
    
    def test_performance_pattern_tracking(self):
        """Test performance pattern tracking."""
        # Add multiple interactions
        interactions = [
            ("Analyze district heating", {'success': True, 'response_time': 2.0}),
            ("Analyze district heating", {'success': True, 'response_time': 2.5}),
            ("Analyze district heating", {'success': True, 'response_time': 1.8}),
            ("Analyze heat pump", {'success': True, 'response_time': 1.5}),
            ("Analyze heat pump", {'success': True, 'response_time': 1.7})
        ]
        
        for request, result in interactions:
            self.learning_engine.learn_from_interaction(request, result)
        
        # Check performance patterns
        assert 'district_heating' in self.learning_engine.performance_patterns
        assert 'heat_pump' in self.learning_engine.performance_patterns
        assert len(self.learning_engine.performance_patterns['district_heating']) == 3
        assert len(self.learning_engine.performance_patterns['heat_pump']) == 2
    
    def test_success_pattern_tracking(self):
        """Test success pattern tracking."""
        # Add interactions with different success rates
        interactions = [
            ("Analyze district heating", {'success': True, 'response_time': 2.0}),
            ("Analyze district heating", {'success': True, 'response_time': 2.5}),
            ("Analyze district heating", {'success': False, 'response_time': 5.0}),
            ("Analyze heat pump", {'success': True, 'response_time': 1.5}),
            ("Analyze heat pump", {'success': True, 'response_time': 1.7})
        ]
        
        for request, result in interactions:
            self.learning_engine.learn_from_interaction(request, result)
        
        # Check success patterns
        assert self.learning_engine.success_patterns['district_heating'] == 2
        assert self.learning_engine.success_patterns['heat_pump'] == 2
    
    def test_improvement_suggestions(self):
        """Test improvement suggestion generation."""
        # Add enough slow interactions to trigger improvement suggestions (need >10 samples)
        slow_interactions = [
            ("Analyze district heating", {'success': True, 'response_time': 35.0})
            for _ in range(12)  # Need more than 10 samples
        ]
        
        for request, result in slow_interactions:
            self.learning_engine.learn_from_interaction(request, result)
        
        # Check improvement suggestions
        insights = self.learning_engine.get_learning_insights()
        assert len(insights['improvement_suggestions']) > 0
        assert any('optimizing' in suggestion.lower() for suggestion in insights['improvement_suggestions'])
    
    def test_learning_insights(self):
        """Test learning insights generation."""
        # Add some interactions
        interactions = [
            ("Analyze district heating", {'success': True, 'response_time': 2.0}),
            ("Analyze heat pump", {'success': True, 'response_time': 1.5}),
            ("Compare scenarios", {'success': False, 'response_time': 5.0})
        ]
        
        for request, result in interactions:
            self.learning_engine.learn_from_interaction(request, result)
        
        insights = self.learning_engine.get_learning_insights()
        
        assert insights['total_interactions'] == 3
        assert 'performance_patterns' in insights
        assert 'success_patterns' in insights
        assert 'improvement_suggestions' in insights
        assert 'learning_summary' in insights

class TestAdaptiveStrategy:
    """Test AdaptiveStrategy functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.adaptive_strategy = AdaptiveStrategy()
    
    def test_strategy_initialization(self):
        """Test adaptive strategy initialization."""
        assert self.adaptive_strategy.current_strategy == 'balanced'
        assert len(self.adaptive_strategy.strategies) == 4
        assert 'conservative' in self.adaptive_strategy.strategies
        assert 'aggressive' in self.adaptive_strategy.strategies
        assert 'balanced' in self.adaptive_strategy.strategies
        assert 'learning' in self.adaptive_strategy.strategies
    
    def test_strategy_selection_simple_request(self):
        """Test strategy selection for simple requests."""
        request = "Show me streets"
        context = {
            'complexity_level': 'simple',
            'request_type': 'exploration'
        }
        
        strategy = self.adaptive_strategy.select_strategy(request, context)
        assert strategy == 'aggressive'
    
    def test_strategy_selection_complex_request(self):
        """Test strategy selection for complex requests."""
        request = "Analyze comprehensive district heating network"
        context = {
            'complexity_level': 'complex',
            'request_type': 'analysis'
        }
        
        strategy = self.adaptive_strategy.select_strategy(request, context)
        assert strategy == 'conservative'
    
    def test_strategy_selection_high_detail_preference(self):
        """Test strategy selection with high detail preference."""
        request = "Analyze heating options"
        context = {
            'complexity_level': 'medium',
            'request_type': 'analysis',
            'user_preferences': {'detail_level': 'high'}
        }
        
        strategy = self.adaptive_strategy.select_strategy(request, context)
        assert strategy == 'aggressive'
    
    def test_strategy_performance_tracking(self):
        """Test strategy performance tracking."""
        # Update performance for different strategies
        self.adaptive_strategy.update_strategy_performance('aggressive', 0.9)
        self.adaptive_strategy.update_strategy_performance('aggressive', 0.8)
        self.adaptive_strategy.update_strategy_performance('conservative', 0.6)
        self.adaptive_strategy.update_strategy_performance('conservative', 0.5)
        
        # Check performance tracking
        assert len(self.adaptive_strategy.strategy_performance['aggressive']) == 2
        assert len(self.adaptive_strategy.strategy_performance['conservative']) == 2
        assert self.adaptive_strategy.strategy_performance['aggressive'][0] == 0.9
        assert self.adaptive_strategy.strategy_performance['conservative'][0] == 0.6

class TestToolRegistry:
    """Test ToolRegistry functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.tool_registry = ToolRegistry()
    
    def test_tool_registration(self):
        """Test tool registration."""
        def test_tool(param1: str, param2: int = 10) -> str:
            return f"Test result: {param1}, {param2}"
        
        metadata = {'type': 'test', 'category': 'testing', 'timeout': 30}
        
        self.tool_registry.register_tool('test_tool', test_tool, metadata)
        
        assert 'test_tool' in self.tool_registry.tools
        assert self.tool_registry.get_tool('test_tool') == test_tool
        assert self.tool_registry.get_tool_metadata('test_tool') == metadata
    
    def test_tool_retrieval(self):
        """Test tool retrieval."""
        def test_tool() -> str:
            return "Test result"
        
        self.tool_registry.register_tool('test_tool', test_tool)
        
        retrieved_tool = self.tool_registry.get_tool('test_tool')
        assert retrieved_tool is not None
        assert retrieved_tool() == "Test result"
        
        # Test non-existent tool
        non_existent = self.tool_registry.get_tool('non_existent')
        assert non_existent is None
    
    def test_tool_listing(self):
        """Test tool listing."""
        def tool1(): return "Tool 1"
        def tool2(): return "Tool 2"
        
        self.tool_registry.register_tool('tool1', tool1)
        self.tool_registry.register_tool('tool2', tool2)
        
        tools = self.tool_registry.list_tools()
        assert 'tool1' in tools
        assert 'tool2' in tools
        assert len(tools) >= 2  # At least the registered tools

class TestDependencyResolver:
    """Test DependencyResolver functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.dependency_resolver = DependencyResolver()
    
    def test_dependency_addition(self):
        """Test adding dependencies."""
        self.dependency_resolver.add_dependency('step2', ['step1'])
        self.dependency_resolver.add_dependency('step3', ['step1', 'step2'])
        
        assert 'step2' in self.dependency_resolver.dependency_graph
        assert 'step3' in self.dependency_resolver.dependency_graph
        assert self.dependency_resolver.dependency_graph['step2'] == ['step1']
        assert self.dependency_resolver.dependency_graph['step3'] == ['step1', 'step2']
    
    def test_dependency_resolution_simple(self):
        """Test simple dependency resolution."""
        workflow = [
            ToolStep('tool1', {}, 'step1'),
            ToolStep('tool2', {}, 'step2', dependencies=['step1']),
            ToolStep('tool3', {}, 'step3', dependencies=['step2'])
        ]
        
        execution_phases = self.dependency_resolver.resolve_dependencies(workflow)
        
        assert len(execution_phases) == 3
        assert len(execution_phases[0]) == 1  # step1
        assert len(execution_phases[1]) == 1  # step2
        assert len(execution_phases[2]) == 1  # step3
        assert execution_phases[0][0].output_name == 'step1'
        assert execution_phases[1][0].output_name == 'step2'
        assert execution_phases[2][0].output_name == 'step3'
    
    def test_dependency_resolution_parallel(self):
        """Test parallel dependency resolution."""
        workflow = [
            ToolStep('tool1', {}, 'step1'),
            ToolStep('tool2', {}, 'step2', dependencies=['step1']),
            ToolStep('tool3', {}, 'step3', dependencies=['step1']),
            ToolStep('tool4', {}, 'step4', dependencies=['step2', 'step3'])
        ]
        
        execution_phases = self.dependency_resolver.resolve_dependencies(workflow)
        
        assert len(execution_phases) == 3
        assert len(execution_phases[0]) == 1  # step1
        assert len(execution_phases[1]) == 2  # step2, step3 (parallel)
        assert len(execution_phases[2]) == 1  # step4
        
        # Check that step2 and step3 are in the same phase
        phase1_outputs = [step.output_name for step in execution_phases[1]]
        assert 'step2' in phase1_outputs
        assert 'step3' in phase1_outputs

class TestWorkflowEngine:
    """Test WorkflowEngine functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.workflow_engine = WorkflowEngine()
        
        # Register test tools
        def test_tool1(param1: str = "default") -> str:
            return f"Tool1 result: {param1}"
        
        def test_tool2(param1: str = "default") -> str:
            return f"Tool2 result: {param1}"
        
        self.workflow_engine.tool_registry.register_tool('test_tool1', test_tool1)
        self.workflow_engine.tool_registry.register_tool('test_tool2', test_tool2)
    
    def test_workflow_validation(self):
        """Test workflow validation."""
        # Valid workflow
        valid_workflow = [
            ToolStep('test_tool1', {'param1': 'test'}, 'step1'),
            ToolStep('test_tool2', {'param1': 'test'}, 'step2')
        ]
        
        # Should not raise exception
        self.workflow_engine._validate_workflow(valid_workflow)
        
        # Invalid workflow - unregistered tool
        invalid_workflow = [
            ToolStep('unregistered_tool', {}, 'step1')
        ]
        
        with pytest.raises(ValueError, match="Tool not registered"):
            self.workflow_engine._validate_workflow(invalid_workflow)
    
    def test_circular_dependency_detection(self):
        """Test circular dependency detection."""
        # Create circular dependency
        circular_workflow = [
            ToolStep('test_tool1', {}, 'step1', dependencies=['step2']),
            ToolStep('test_tool2', {}, 'step2', dependencies=['step1'])
        ]
        
        with pytest.raises(ValueError, match="Circular dependency detected"):
            self.workflow_engine._validate_workflow(circular_workflow)
    
    def test_simple_workflow_execution(self):
        """Test simple workflow execution."""
        workflow = [
            ToolStep('test_tool1', {'param1': 'test1'}, 'step1'),
            ToolStep('test_tool2', {'param1': 'test2'}, 'step2')
        ]
        
        result = self.workflow_engine.execute_workflow(workflow)
        
        assert result['success'] is True
        assert 'aggregated_data' in result
        assert 'execution_summary' in result
        assert 'individual_results' in result
        assert result['execution_summary']['total_steps'] == 2
        assert result['execution_summary']['successful_steps'] == 2
    
    def test_workflow_with_dependencies(self):
        """Test workflow execution with dependencies."""
        workflow = [
            ToolStep('test_tool1', {'param1': 'test1'}, 'step1'),
            ToolStep('test_tool2', {'param1': '$step1'}, 'step2', dependencies=['step1'])
        ]
        
        result = self.workflow_engine.execute_workflow(workflow)
        
        assert result['success'] is True
        assert result['execution_summary']['total_steps'] == 2
        assert result['execution_summary']['successful_steps'] == 2

class TestSessionMemory:
    """Test SessionMemory functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.session_memory = SessionMemory('test_session', max_entries=10)
    
    def test_session_initialization(self):
        """Test session memory initialization."""
        assert self.session_memory.session_id == 'test_session'
        assert self.session_memory.max_entries == 10
        assert len(self.session_memory.memories) == 0
    
    def test_add_memory(self):
        """Test adding memory to session."""
        memory = MemoryEntry(
            id='test_id',
            timestamp=datetime.now(),
            request='Test request',
            response='Test response',
            context={'test': 'context'},
            performance_metrics={'response_time': 1.5},
            tags=['test', 'analysis']
        )
        
        self.session_memory.add_memory(memory)
        
        assert len(self.session_memory.memories) == 1
        assert self.session_memory.memories[0].request == 'Test request'
    
    def test_get_recent_memories(self):
        """Test getting recent memories."""
        # Add multiple memories
        for i in range(5):
            memory = MemoryEntry(
                id=f'test_id_{i}',
                timestamp=datetime.now(),
                request=f'Test request {i}',
                response=f'Test response {i}',
                context={'test': 'context'},
                performance_metrics={'response_time': 1.5},
                tags=['test']
            )
            self.session_memory.add_memory(memory)
        
        recent_memories = self.session_memory.get_recent_memories(limit=3)
        
        assert len(recent_memories) == 3
        assert recent_memories[0].request == 'Test request 4'  # Most recent
        assert recent_memories[2].request == 'Test request 2'  # Oldest of the 3
    
    def test_get_memories_by_tags(self):
        """Test getting memories by tags."""
        # Add memories with different tags
        memory1 = MemoryEntry(
            id='test_id_1',
            timestamp=datetime.now(),
            request='District heating request',
            response='District heating response',
            context={'test': 'context'},
            performance_metrics={'response_time': 1.5},
            tags=['district_heating', 'analysis']
        )
        
        memory2 = MemoryEntry(
            id='test_id_2',
            timestamp=datetime.now(),
            request='Heat pump request',
            response='Heat pump response',
            context={'test': 'context'},
            performance_metrics={'response_time': 1.5},
            tags=['heat_pump', 'analysis']
        )
        
        self.session_memory.add_memory(memory1)
        self.session_memory.add_memory(memory2)
        
        # Get memories by tag
        district_heating_memories = self.session_memory.get_memories_by_tags(['district_heating'])
        analysis_memories = self.session_memory.get_memories_by_tags(['analysis'])
        
        assert len(district_heating_memories) == 1
        assert len(analysis_memories) == 2
        assert district_heating_memories[0].request == 'District heating request'
    
    def test_context_management(self):
        """Test context management."""
        # Update context
        context_updates = {'user_id': 'test_user', 'session_type': 'analysis'}
        self.session_memory.update_context(context_updates)
        
        # Get context
        context = self.session_memory.get_context()
        
        assert context['user_id'] == 'test_user'
        assert context['session_type'] == 'analysis'

class TestConversationContext:
    """Test ConversationContext functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.conversation_context = ConversationContext(max_history=5)
    
    def test_conversation_initialization(self):
        """Test conversation context initialization."""
        assert self.conversation_context.max_history == 5
        assert len(self.conversation_context.conversation_history) == 0
        assert self.conversation_context.current_topic is None
        assert len(self.conversation_context.conversation_flow) == 0
    
    def test_add_interaction(self):
        """Test adding interaction to conversation."""
        request = "Analyze district heating for Parkstraße"
        response = "District heating analysis completed"
        metadata = {'analysis_type': 'district_heating', 'success': True}
        
        self.conversation_context.add_interaction(request, response, metadata)
        
        assert len(self.conversation_context.conversation_history) == 1
        assert self.conversation_context.conversation_history[0]['request'] == request
        assert self.conversation_context.conversation_history[0]['response'] == response
        assert self.conversation_context.conversation_history[0]['metadata'] == metadata
    
    def test_topic_detection(self):
        """Test conversation topic detection."""
        # Test district heating topic
        request1 = "Analyze district heating network"
        self.conversation_context.add_interaction(request1, "Response 1")
        assert self.conversation_context.current_topic == 'district_heating'
        
        # Test heat pump topic
        request2 = "Analyze heat pump feasibility"
        self.conversation_context.add_interaction(request2, "Response 2")
        assert self.conversation_context.current_topic == 'heat_pump'
        
        # Test comparison topic
        request3 = "Compare heating scenarios"
        self.conversation_context.add_interaction(request3, "Response 3")
        assert self.conversation_context.current_topic == 'comparison'
    
    def test_conversation_flow_tracking(self):
        """Test conversation flow tracking."""
        # Add different types of interactions
        interactions = [
            ("Show me streets", "Street list"),
            ("Analyze district heating", "Analysis result"),
            ("Compare scenarios", "Comparison result"),
            ("Help me understand", "Help response")
        ]
        
        for request, response in interactions:
            self.conversation_context.add_interaction(request, response)
        
        # Check conversation flow
        assert len(self.conversation_context.conversation_flow) == 4
        assert self.conversation_context.conversation_flow[0] == 'exploration'
        assert self.conversation_context.conversation_flow[1] == 'analysis'
        assert self.conversation_context.conversation_flow[2] == 'comparison'
        assert self.conversation_context.conversation_flow[3] == 'help'
    
    def test_get_context(self):
        """Test getting conversation context."""
        # Add some interactions
        self.conversation_context.add_interaction("Test request", "Test response")
        
        context = self.conversation_context.get_context()
        
        assert 'conversation_history' in context
        assert 'current_topic' in context
        assert 'conversation_flow' in context
        assert 'history_length' in context
        assert context['history_length'] == 1

# Integration Tests
class TestAdvancedADKIntegration:
    """Integration tests for advanced ADK features."""
    
    def setup_method(self):
        """Setup test environment."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock ADK Agent
        self.mock_agent = Mock()
        self.mock_agent.run.return_value = Mock(agent_response="Integration test response")
        
        with patch('src.enhanced_agents_advanced.Agent', return_value=self.mock_agent):
            self.agent = AdvancedADKAgent('IntegrationTestAgent', {
                'name': 'IntegrationTestAgent',
                'model': 'gemini-1.5-flash-latest',
                'system_prompt': 'You are an integration test agent.',
                'temperature': 0.7
            })
    
    def teardown_method(self):
        """Cleanup test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_end_to_end_advanced_processing(self):
        """Test end-to-end advanced processing."""
        # Process multiple requests to test memory and learning
        requests = [
            "Analyze district heating for Parkstraße",
            "Compare heating scenarios for Hauptstraße",
            "Show me all available streets"
        ]
        
        results = []
        for request in requests:
            result = self.agent.process_request(request)
            results.append(result)
        
        # Verify all requests were processed successfully
        assert all(result['success'] for result in results)
        
        # Verify memory integration
        assert all(result['memory_enhanced'] for result in results[1:])  # All except first
        
        # Verify context enhancement
        assert all(result['context_enhanced'] for result in results)
        
        # Check agent status
        status = self.agent.get_agent_status()
        assert status['memory_entries'] >= 3
        assert status['conversation_history'] >= 3
    
    def test_learning_and_adaptation(self):
        """Test learning and adaptation over multiple interactions."""
        # Process similar requests to test learning
        similar_requests = [
            "Analyze district heating for Parkstraße",
            "Analyze district heating for Hauptstraße",
            "Analyze district heating for Bahnhofstraße"
        ]
        
        for request in similar_requests:
            result = self.agent.process_request(request)
            assert result['success'] is True
        
        # Check learning insights
        learning_insights = self.agent.learning_engine.get_learning_insights()
        assert learning_insights['total_interactions'] >= 3
        assert 'district_heating' in learning_insights['performance_patterns']
        assert 'district_heating' in learning_insights['success_patterns']
    
    def test_adaptive_strategy_evolution(self):
        """Test adaptive strategy evolution."""
        # Process requests with different characteristics
        requests = [
            ("Simple request", "Show streets"),
            ("Complex request", "Analyze comprehensive district heating network with detailed hydraulic simulation and economic analysis"),
            ("Medium request", "Compare heating scenarios for Parkstraße")
        ]
        
        strategies_used = []
        for description, request in requests:
            result = self.agent.process_request(request)
            strategies_used.append(result['strategy_used'])
        
        # Verify different strategies were used
        assert len(set(strategies_used)) > 1  # At least 2 different strategies used

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
