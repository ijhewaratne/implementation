#!/usr/bin/env python3
"""
Simple Advanced ADK Agent Features Demo
Simplified demonstration of advanced agent capabilities.
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def demo_memory_context_systems():
    """Demonstrate memory and context systems."""
    print("🧠 Memory and Context Systems Demo")
    print("=" * 50)
    
    # Test SessionMemory
    print("\n🔍 Session Memory Test:")
    from src.agent_memory_context import SessionMemory, MemoryEntry
    
    session_memory = SessionMemory('demo_session', max_entries=10)
    
    # Add some memories
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
    
    print(f"   ✅ Added {len(memories)} memories")
    print(f"   📊 Recent memories: {len(session_memory.get_recent_memories(3))}")
    print(f"   🏷️  Memories by tag 'test': {len(session_memory.get_memories_by_tags(['test']))}")
    
    # Test ConversationContext
    print("\n🔍 Conversation Context Test:")
    from src.agent_memory_context import ConversationContext
    
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
    print(f"   ✅ Conversation history length: {context['history_length']}")
    print(f"   🎯 Current topic: {context['current_topic']}")
    print(f"   📈 Conversation flow: {context['conversation_flow']}")
    
    # Test AnalysisContext
    print("\n🔍 Analysis Context Test:")
    from src.agent_memory_context import AnalysisContext
    
    analysis_context = AnalysisContext()
    
    # Start analysis
    analysis_context.start_analysis('district_heating', {'street': 'Parkstraße'})
    print("   ✅ Started district heating analysis")
    
    # Complete analysis
    analysis_context.complete_analysis({'result': 'Analysis completed successfully'})
    print("   ✅ Completed analysis")
    
    # Get analysis summary
    summary = analysis_context.get_analysis_summary()
    print(f"   📊 Total analyses: {summary['total_analyses']}")
    print(f"   🎯 Most common type: {summary['most_common_type']}")

def demo_learning_engine():
    """Demonstrate learning engine capabilities."""
    print("\n\n🎓 Learning Engine Demo")
    print("=" * 50)
    
    from src.enhanced_agents_advanced import LearningEngine
    
    learning_engine = LearningEngine()
    
    # Add some learning interactions
    interactions = [
        ("Analyze district heating for Parkstraße", {'success': True, 'response_time': 2.0}),
        ("Analyze district heating for Hauptstraße", {'success': True, 'response_time': 2.5}),
        ("Analyze district heating for Bahnhofstraße", {'success': False, 'response_time': 5.0}),
        ("Analyze heat pump feasibility for Parkstraße", {'success': True, 'response_time': 1.5}),
        ("Analyze heat pump feasibility for Hauptstraße", {'success': True, 'response_time': 1.7})
    ]
    
    print("\n🔍 Learning from Interactions:")
    for i, (request, result) in enumerate(interactions, 1):
        print(f"   Learning {i}: {request}")
        learning_engine.learn_from_interaction(request, result)
        print(f"      Success: {result['success']}, Time: {result['response_time']}s")
    
    # Show learning insights
    print("\n📊 Learning Insights:")
    insights = learning_engine.get_learning_insights()
    
    print(f"   📈 Total Interactions: {insights['total_interactions']}")
    print(f"   🎯 Performance Patterns: {list(insights['performance_patterns'].keys())}")
    print(f"   ✅ Success Patterns: {insights['success_patterns']}")
    
    if insights['improvement_suggestions']:
        print("   💡 Improvement Suggestions:")
        for suggestion in insights['improvement_suggestions']:
            print(f"      - {suggestion}")
    
    # Show learning summary
    learning_summary = insights['learning_summary']
    print(f"\n📈 Learning Summary:")
    print(f"   📊 Status: {learning_summary['status']}")
    if learning_summary['status'] == 'active_learning':
        print(f"   ⏱️  Average Response Time: {learning_summary['avg_response_time']:.2f}s")
        print(f"   ✅ Success Rate: {learning_summary['success_rate']:.1%}")
        print(f"   📈 Recent Trend: {learning_summary['recent_trend']}")

def demo_adaptive_strategy():
    """Demonstrate adaptive strategy selection."""
    print("\n\n🎯 Adaptive Strategy Demo")
    print("=" * 50)
    
    from src.enhanced_agents_advanced import AdaptiveStrategy
    
    adaptive_strategy = AdaptiveStrategy()
    
    # Test different request types to see strategy adaptation
    strategy_test_requests = [
        ("Simple Request", "Show me streets", {'complexity_level': 'simple', 'request_type': 'exploration'}),
        ("Complex Request", "Analyze comprehensive district heating network", {'complexity_level': 'complex', 'request_type': 'analysis'}),
        ("Medium Request", "Compare heating scenarios for Parkstraße", {'complexity_level': 'medium', 'request_type': 'comparison'}),
        ("High Detail Preference", "Analyze district heating for Hauptstraße", {'complexity_level': 'medium', 'request_type': 'analysis', 'user_preferences': {'detail_level': 'high'}})
    ]
    
    print("\n🔍 Strategy Selection Tests:")
    for description, request, context in strategy_test_requests:
        print(f"\n   {description}:")
        print(f"      Request: {request}")
        
        strategy = adaptive_strategy.select_strategy(request, context)
        print(f"      🎯 Strategy Used: {strategy}")
        print(f"      📊 Context: {context}")
    
    # Show strategy performance tracking
    print("\n📊 Strategy Performance Tracking:")
    adaptive_strategy.update_strategy_performance('aggressive', 0.9)
    adaptive_strategy.update_strategy_performance('aggressive', 0.8)
    adaptive_strategy.update_strategy_performance('conservative', 0.6)
    adaptive_strategy.update_strategy_performance('conservative', 0.5)
    
    strategy_performance = adaptive_strategy.strategy_performance
    for strategy, performance in strategy_performance.items():
        if performance:
            avg_performance = sum(performance) / len(performance)
            print(f"   {strategy}: {avg_performance:.2f} (from {len(performance)} samples)")

def demo_advanced_tool_chaining():
    """Demonstrate advanced tool chaining capabilities."""
    print("\n\n🔗 Advanced Tool Chaining Demo")
    print("=" * 50)
    
    from src.advanced_tool_chaining import WorkflowEngine, ToolStep
    
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
    
    print(f"   ✅ Success: {result['success']}")
    print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
    print(f"   📊 Total Steps: {result['execution_summary']['total_steps']}")
    print(f"   ✅ Successful Steps: {result['execution_summary']['successful_steps']}")
    
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
    
    print(f"   ✅ Success: {result['success']}")
    print(f"   ⏱️  Execution Time: {execution_time:.2f}s")
    print(f"   📊 Total Steps: {result['execution_summary']['total_steps']}")
    print(f"   ✅ Successful Steps: {result['execution_summary']['successful_steps']}")

def demo_agent_context_manager():
    """Demonstrate agent context manager capabilities."""
    print("\n\n📊 Agent Context Manager Demo")
    print("=" * 50)
    
    from src.enhanced_agents_advanced import AgentContextManager
    
    context_manager = AgentContextManager()
    
    # Test context enhancement
    print("\n🔍 Context Enhancement Test:")
    request = "Analyze district heating for Parkstraße"
    additional_context = {'user_id': 'test_user', 'session_id': 'test_session'}
    
    enhanced_context = context_manager.enhance_context(request, additional_context)
    
    print(f"   📝 Request: {enhanced_context['request']}")
    print(f"   🎯 Request Type: {enhanced_context['request_type']}")
    print(f"   📊 Complexity Level: {enhanced_context['complexity_level']}")
    print(f"   👤 User ID: {enhanced_context.get('user_id', 'N/A')}")
    print(f"   🕒 Timestamp: {enhanced_context['timestamp']}")
    
    # Test request classification
    print("\n🔍 Request Classification Test:")
    test_requests = [
        "Analyze district heating network",
        "Compare heating scenarios",
        "Show me all available streets",
        "Help me understand the results"
    ]
    
    for test_request in test_requests:
        enhanced = context_manager.enhance_context(test_request)
        print(f"   '{test_request}' -> {enhanced['request_type']} ({enhanced['complexity_level']})")
    
    # Test context update
    print("\n🔍 Context Update Test:")
    request = "Analyze district heating"
    response = "District heating analysis completed with comprehensive network design and economic evaluation."
    metadata = {'analysis_type': 'district_heating', 'success': True}
    
    context_manager.update_context(request, response, metadata)
    
    print(f"   ✅ Updated context with interaction")
    print(f"   📊 Conversation history length: {len(context_manager.conversation_history)}")
    print(f"   🎯 User preferences: {context_manager.user_preferences}")

def main():
    """Main demo function."""
    print("🚀 Simple Advanced ADK Agent Features Demo")
    print("=" * 80)
    print("This demo showcases the core advanced capabilities:")
    print("- Memory and context systems")
    print("- Learning engine")
    print("- Adaptive strategy selection")
    print("- Advanced tool chaining")
    print("- Agent context management")
    print("=" * 80)
    
    try:
        # Run all demos
        demo_memory_context_systems()
        demo_learning_engine()
        demo_adaptive_strategy()
        demo_advanced_tool_chaining()
        demo_agent_context_manager()
        
        print("\n\n🎉 Demo Completed Successfully!")
        print("=" * 80)
        print("The advanced ADK agent features are working correctly:")
        print("✅ Memory and context systems")
        print("✅ Learning engine")
        print("✅ Adaptive strategy selection")
        print("✅ Advanced tool chaining")
        print("✅ Agent context management")
        print("\n🚀 Core components are functional and ready for integration!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
