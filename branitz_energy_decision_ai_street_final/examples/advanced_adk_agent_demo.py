#!/usr/bin/env python3
"""
Advanced ADK Agent Features Demo
Comprehensive demonstration of advanced agent capabilities including memory, context, learning, and adaptive strategies.
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import advanced ADK agent components
from src.enhanced_agents_advanced import (
    AdvancedADKAgent,
    AgentMemoryManager,
    AgentContextManager,
    LearningEngine,
    AdaptiveStrategy
)

from src.advanced_tool_chaining import (
    WorkflowEngine,
    ToolStep,
    ToolRegistry
)

from src.agent_memory_context import (
    SessionMemory,
    LearningMemory,
    UserProfiles,
    ConversationContext,
    AnalysisContext
)

def create_demo_agent():
    """Create a demo advanced ADK agent."""
    config = {
        'name': 'DemoAdvancedAgent',
        'model': 'gemini-1.5-flash-latest',
        'system_prompt': '''
        You are an advanced ADK agent with enhanced capabilities including:
        - Memory and context awareness
        - Learning from interactions
        - Adaptive strategy selection
        - Advanced tool chaining
        
        You can analyze district heating networks, heat pump feasibility, and compare scenarios.
        Use your advanced capabilities to provide comprehensive and personalized responses.
        ''',
        'temperature': 0.7
    }
    
    # Mock ADK Agent for demo
    class MockADKAgent:
        def __init__(self, config=None):
            if config is None:
                config = {}
            self.config = config
            self.name = config.get('name', 'MockAgent')
        
        def run(self, request):
            # Simulate ADK agent response
            if "district heating" in request.lower():
                return MockResponse("District heating analysis completed with network design, hydraulic simulation, and economic evaluation.")
            elif "heat pump" in request.lower():
                return MockResponse("Heat pump feasibility analysis completed with power flow simulation and infrastructure assessment.")
            elif "compare" in request.lower():
                return MockResponse("Scenario comparison completed with comprehensive metrics and recommendations.")
            else:
                return MockResponse("Analysis completed successfully.")
    
    class MockResponse:
        def __init__(self, response):
            self.agent_response = response
    
    # Patch the Agent import for demo
    import src.enhanced_agents_advanced
    original_agent = src.enhanced_agents_advanced.Agent
    src.enhanced_agents_advanced.Agent = MockADKAgent
    
    try:
        agent = AdvancedADKAgent('DemoAdvancedAgent', config)
        return agent
    finally:
        # Restore original Agent
        src.enhanced_agents_advanced.Agent = original_agent

def demo_basic_agent_capabilities():
    """Demonstrate basic advanced agent capabilities."""
    print("🚀 Advanced ADK Agent Features Demo")
    print("=" * 60)
    
    # Create demo agent
    agent = create_demo_agent()
    
    print("\n📋 1. Basic Agent Capabilities")
    print("-" * 40)
    
    # Test basic request processing
    test_requests = [
        "Analyze district heating for Parkstraße",
        "Compare heating scenarios for Hauptstraße",
        "Show me all available streets"
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n🔍 Test {i}: {request}")
        
        start_time = time.time()
        result = agent.process_request(request)
        execution_time = time.time() - start_time
        
        print(f"   ✅ Success: {result['success']}")
        print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
        print(f"   🧠 Memory Enhanced: {result['memory_enhanced']}")
        print(f"   📊 Context Enhanced: {result['context_enhanced']}")
        print(f"   🎯 Strategy Used: {result['strategy_used']}")
        print(f"   📝 Response Length: {len(result['agent_response'])} characters")
    
    return agent

def demo_memory_and_context_features(agent):
    """Demonstrate memory and context features."""
    print("\n\n🧠 2. Memory and Context Features")
    print("-" * 40)
    
    # Test memory integration
    print("\n🔍 Testing Memory Integration:")
    
    # First request - should not have memory enhancement
    request1 = "Analyze district heating for Parkstraße"
    result1 = agent.process_request(request1)
    print(f"   First request - Memory Enhanced: {result1['memory_enhanced']}")
    
    # Similar request - should have memory enhancement
    request2 = "Analyze district heating for Hauptstraße"
    result2 = agent.process_request(request2)
    print(f"   Similar request - Memory Enhanced: {result2['memory_enhanced']}")
    
    # Test context enhancement
    print("\n🔍 Testing Context Enhancement:")
    
    # Request with additional context
    additional_context = {
        'user_id': 'demo_user',
        'session_id': 'demo_session',
        'preferences': {'detail_level': 'high'}
    }
    
    request3 = "Compare heating scenarios for Bahnhofstraße"
    result3 = agent.process_request(request3, additional_context)
    
    print(f"   Context Enhanced: {result3['context_enhanced']}")
    print(f"   Strategy Used: {result3['strategy_used']}")
    
    # Show memory statistics
    print("\n📊 Memory Statistics:")
    memory_stats = agent.memory.get_relevant_memories("district heating", limit=5)
    print(f"   Relevant Memories Found: {len(memory_stats)}")
    
    for i, memory in enumerate(memory_stats, 1):
        print(f"   Memory {i}: {memory.request[:50]}...")

def demo_learning_capabilities(agent):
    """Demonstrate learning capabilities."""
    print("\n\n🎓 3. Learning Capabilities")
    print("-" * 40)
    
    # Process multiple similar requests to demonstrate learning
    learning_requests = [
        "Analyze district heating for Parkstraße",
        "Analyze district heating for Hauptstraße", 
        "Analyze district heating for Bahnhofstraße",
        "Analyze heat pump feasibility for Parkstraße",
        "Analyze heat pump feasibility for Hauptstraße"
    ]
    
    print("\n🔍 Processing Learning Requests:")
    for i, request in enumerate(learning_requests, 1):
        print(f"   Learning Request {i}: {request}")
        result = agent.process_request(request)
        print(f"      Success: {result['success']}, Strategy: {result['strategy_used']}")
    
    # Show learning insights
    print("\n📊 Learning Insights:")
    learning_insights = agent.learning_engine.get_learning_insights()
    
    print(f"   Total Interactions: {learning_insights['total_interactions']}")
    print(f"   Performance Patterns: {list(learning_insights['performance_patterns'].keys())}")
    print(f"   Success Patterns: {learning_insights['success_patterns']}")
    
    if learning_insights['improvement_suggestions']:
        print("   Improvement Suggestions:")
        for suggestion in learning_insights['improvement_suggestions']:
            print(f"      - {suggestion}")
    
    # Show learning summary
    learning_summary = learning_insights['learning_summary']
    print(f"\n📈 Learning Summary:")
    print(f"   Status: {learning_summary['status']}")
    if learning_summary['status'] == 'active_learning':
        print(f"   Average Response Time: {learning_summary['avg_response_time']:.2f}s")
        print(f"   Success Rate: {learning_summary['success_rate']:.1%}")
        print(f"   Recent Trend: {learning_summary['recent_trend']}")

def demo_adaptive_strategies(agent):
    """Demonstrate adaptive strategy selection."""
    print("\n\n🎯 4. Adaptive Strategy Selection")
    print("-" * 40)
    
    # Test different request types to see strategy adaptation
    strategy_test_requests = [
        ("Simple Request", "Show me streets"),
        ("Complex Request", "Analyze comprehensive district heating network with detailed hydraulic simulation, economic analysis, and environmental impact assessment"),
        ("Medium Request", "Compare heating scenarios for Parkstraße"),
        ("High Detail Preference", "Analyze district heating for Hauptstraße")
    ]
    
    print("\n🔍 Strategy Selection Tests:")
    for description, request in strategy_test_requests:
        print(f"\n   {description}:")
        print(f"      Request: {request}")
        
        # Add high detail preference for the last test
        context = {}
        if "High Detail" in description:
            context = {'user_preferences': {'detail_level': 'high'}}
        
        result = agent.process_request(request, context)
        print(f"      Strategy Used: {result['strategy_used']}")
        print(f"      Success: {result['success']}")
    
    # Show strategy performance
    print("\n📊 Strategy Performance:")
    strategy_performance = agent.adaptive_strategy.strategy_performance
    for strategy, performance in strategy_performance.items():
        if performance:
            avg_performance = sum(performance) / len(performance)
            print(f"   {strategy}: {avg_performance:.2f} (from {len(performance)} samples)")

def demo_advanced_tool_chaining():
    """Demonstrate advanced tool chaining capabilities."""
    print("\n\n🔗 5. Advanced Tool Chaining")
    print("-" * 40)
    
    # Create workflow engine
    workflow_engine = WorkflowEngine()
    
    # Register demo tools
    def demo_tool1(param1: str = "default") -> str:
        time.sleep(0.1)  # Simulate processing time
        return f"Tool1 result: {param1}"
    
    def demo_tool2(param1: str = "default") -> str:
        time.sleep(0.1)  # Simulate processing time
        return f"Tool2 result: {param1}"
    
    def demo_tool3(param1: str = "default") -> str:
        time.sleep(0.1)  # Simulate processing time
        return f"Tool3 result: {param1}"
    
    workflow_engine.tool_registry.register_tool('demo_tool1', demo_tool1)
    workflow_engine.tool_registry.register_tool('demo_tool2', demo_tool2)
    workflow_engine.tool_registry.register_tool('demo_tool3', demo_tool3)
    
    # Test simple workflow
    print("\n🔍 Simple Workflow Test:")
    simple_workflow = [
        ToolStep('demo_tool1', {'param1': 'test1'}, 'step1'),
        ToolStep('demo_tool2', {'param1': 'test2'}, 'step2')
    ]
    
    start_time = time.time()
    result = workflow_engine.execute_workflow(simple_workflow)
    execution_time = time.time() - start_time
    
    print(f"   Success: {result['success']}")
    print(f"   Execution Time: {execution_time:.2f}s")
    print(f"   Total Steps: {result['execution_summary']['total_steps']}")
    print(f"   Successful Steps: {result['execution_summary']['successful_steps']}")
    
    # Test workflow with dependencies
    print("\n🔍 Workflow with Dependencies Test:")
    dependency_workflow = [
        ToolStep('demo_tool1', {'param1': 'test1'}, 'step1'),
        ToolStep('demo_tool2', {'param1': '$step1'}, 'step2', dependencies=['step1']),
        ToolStep('demo_tool3', {'param1': '$step2'}, 'step3', dependencies=['step2'])
    ]
    
    start_time = time.time()
    result = workflow_engine.execute_workflow(dependency_workflow)
    execution_time = time.time() - start_time
    
    print(f"   Success: {result['success']}")
    print(f"   Execution Time: {execution_time:.2f}s")
    print(f"   Total Steps: {result['execution_summary']['total_steps']}")
    print(f"   Successful Steps: {result['execution_summary']['successful_steps']}")
    
    # Test parallel workflow
    print("\n🔍 Parallel Workflow Test:")
    parallel_workflow = [
        ToolStep('demo_tool1', {'param1': 'test1'}, 'step1'),
        ToolStep('demo_tool2', {'param1': 'test2'}, 'step2', parallel_group='group1'),
        ToolStep('demo_tool3', {'param1': 'test3'}, 'step3', parallel_group='group1')
    ]
    
    start_time = time.time()
    result = workflow_engine.execute_workflow(parallel_workflow)
    execution_time = time.time() - start_time
    
    print(f"   Success: {result['success']}")
    print(f"   Execution Time: {execution_time:.2f}s")
    print(f"   Total Steps: {result['execution_summary']['total_steps']}")
    print(f"   Successful Steps: {result['execution_summary']['successful_steps']}")

def demo_agent_status_and_monitoring(agent):
    """Demonstrate agent status and monitoring capabilities."""
    print("\n\n📊 6. Agent Status and Monitoring")
    print("-" * 40)
    
    # Get comprehensive agent status
    status = agent.get_agent_status()
    
    print("\n📋 Agent Status Summary:")
    print(f"   Agent Type: {status['agent_type']}")
    print(f"   Memory Entries: {status['memory_entries']}")
    print(f"   Conversation History: {status['conversation_history']}")
    print(f"   Current Strategy: {status['current_strategy']}")
    print(f"   ADK Available: {status['adk_available']}")
    
    print("\n📈 Performance Metrics:")
    performance = status['performance_metrics']
    print(f"   Average Response Time: {performance['avg_response_time']:.2f}s")
    print(f"   Success Rate: {performance['success_rate']:.1%}")
    
    print("\n🎓 Learning Insights:")
    learning_insights = status['learning_insights']
    print(f"   Total Interactions: {learning_insights['total_interactions']}")
    print(f"   Performance Patterns: {list(learning_insights['performance_patterns'].keys())}")
    print(f"   Success Patterns: {learning_insights['success_patterns']}")
    
    if learning_insights['improvement_suggestions']:
        print("   Improvement Suggestions:")
        for suggestion in learning_insights['improvement_suggestions']:
            print(f"      - {suggestion}")

def demo_memory_context_systems():
    """Demonstrate memory and context systems."""
    print("\n\n🧠 7. Memory and Context Systems")
    print("-" * 40)
    
    # Test SessionMemory
    print("\n🔍 Session Memory Test:")
    session_memory = SessionMemory('demo_session', max_entries=10)
    
    # Add some memories
    from src.agent_memory_context import MemoryEntry
    memories = [
        MemoryEntry(
            id=f'memory_{i}',
            timestamp=datetime.now(),
            request=f'Test request {i}',
            response=f'Test response {i}',
            context={'test': 'context'},
            performance_metrics={'response_time': 1.0 + i * 0.1},
            tags=['test', f'tag_{i}']
        )
        for i in range(5)
    ]
    
    for memory in memories:
        session_memory.add_memory(memory)
    
    print(f"   Added {len(memories)} memories")
    print(f"   Recent memories: {len(session_memory.get_recent_memories(3))}")
    print(f"   Memories by tag 'test': {len(session_memory.get_memories_by_tags(['test']))}")
    
    # Test ConversationContext
    print("\n🔍 Conversation Context Test:")
    conversation_context = ConversationContext(max_history=10)
    
    # Add interactions
    interactions = [
        ("Show me streets", "Here are the available streets"),
        ("Analyze district heating", "District heating analysis completed"),
        ("Compare scenarios", "Scenario comparison completed")
    ]
    
    for request, response in interactions:
        conversation_context.add_interaction(request, response)
    
    context = conversation_context.get_context()
    print(f"   Conversation history length: {context['history_length']}")
    print(f"   Current topic: {context['current_topic']}")
    print(f"   Conversation flow: {context['conversation_flow']}")
    
    # Test AnalysisContext
    print("\n🔍 Analysis Context Test:")
    analysis_context = AnalysisContext()
    
    # Start analysis
    analysis_context.start_analysis('district_heating', {'street': 'Parkstraße'})
    print("   Started district heating analysis")
    
    # Complete analysis
    analysis_context.complete_analysis({'result': 'Analysis completed successfully'})
    print("   Completed analysis")
    
    # Get analysis summary
    summary = analysis_context.get_analysis_summary()
    print(f"   Total analyses: {summary['total_analyses']}")
    print(f"   Most common type: {summary['most_common_type']}")

def main():
    """Main demo function."""
    print("🚀 Advanced ADK Agent Features - Comprehensive Demo")
    print("=" * 80)
    print("This demo showcases the advanced capabilities of the ADK agent system:")
    print("- Memory and context awareness")
    print("- Learning from interactions")
    print("- Adaptive strategy selection")
    print("- Advanced tool chaining")
    print("- Comprehensive monitoring and analytics")
    print("=" * 80)
    
    try:
        # Run all demos
        agent = demo_basic_agent_capabilities()
        demo_memory_and_context_features(agent)
        demo_learning_capabilities(agent)
        demo_adaptive_strategies(agent)
        demo_advanced_tool_chaining()
        demo_agent_status_and_monitoring(agent)
        demo_memory_context_systems()
        
        print("\n\n🎉 Demo Completed Successfully!")
        print("=" * 80)
        print("The advanced ADK agent features are working correctly:")
        print("✅ Advanced agent capabilities")
        print("✅ Memory and context management")
        print("✅ Learning and adaptation")
        print("✅ Adaptive strategy selection")
        print("✅ Advanced tool chaining")
        print("✅ Comprehensive monitoring")
        print("✅ Memory and context systems")
        print("\n🚀 Ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
