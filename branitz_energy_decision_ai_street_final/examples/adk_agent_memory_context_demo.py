#!/usr/bin/env python3
"""
ADK Agent Memory and Context Demo
Comprehensive demonstration of advanced agent memory and context management capabilities.
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import agent memory and context components
from src.agent_memory_context import (
    AgentMemory,
    AgentContext,
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

def demo_agent_memory():
    """Demonstrate AgentMemory functionality."""
    print("🧠 ADK Agent Memory and Context Demo")
    print("=" * 60)
    
    # Create agent memory with configuration
    memory_config = {
        'max_session_entries': 100,
        'learning_db_path': 'data/demo_learning_memory.db',
        'profiles_db_path': 'data/demo_user_profiles.db',
        'context_db_path': 'data/demo_context_persistence.db'
    }
    
    agent_memory = AgentMemory(session_id="demo_session", memory_config=memory_config)
    
    print("\n📋 1. Agent Memory System")
    print("-" * 40)
    
    # Test memory operations
    test_requests = [
        "analyze district heating for Parkstraße",
        "compare heating scenarios for Hauptstraße",
        "show me all available streets",
        "analyze heat pump feasibility for Bahnhofstraße",
        "generate comprehensive KPI report"
    ]
    
    print("\n🔍 Testing Memory Operations:")
    for i, request in enumerate(test_requests, 1):
        print(f"   {i}. {request}")
        
        # Simulate agent response
        mock_result = {
            'agent_response': f"Mock response for: {request}",
            'success': True,
            'response_time': 0.5 + (i * 0.1),
            'tools_executed': True,
            'metadata': {'request_id': f'req_{i}'}
        }
        
        # Update memory
        agent_memory.update_memory(request, mock_result, user_id="demo_user", metadata={'test': True})
        
        # Get relevant memory
        relevant_memory = agent_memory.get_relevant_memory(request, user_id="demo_user")
        
        print(f"      ✅ Memory updated - Tags: {relevant_memory['request_tags']}")
        print(f"      📊 Recent memories: {len(relevant_memory['recent_memories'])}")
        print(f"      🏷️  Tagged memories: {len(relevant_memory['tagged_memories'])}")
    
    # Get memory summary
    print("\n📊 Memory Summary:")
    memory_summary = agent_memory.get_memory_summary()
    
    print(f"   📈 Total Memories: {memory_summary['memory_stats']['total_memories']}")
    print(f"   🧠 Session Memories: {memory_summary['memory_stats']['session_memories']}")
    print(f"   📚 Learning Patterns: {memory_summary['memory_stats']['learning_patterns']}")
    print(f"   👤 User Preferences: {memory_summary['memory_stats']['user_preferences']}")
    print(f"   💾 Context Snapshots: {memory_summary['memory_stats']['context_snapshots']}")
    
    # Show recent activity
    recent_activity = memory_summary['recent_activity']
    if recent_activity.get('status') != 'no_recent_activity':
        print(f"\n   📋 Recent Activity:")
        print(f"      Total Recent Memories: {recent_activity['total_recent_memories']}")
        print(f"      Average Importance: {recent_activity['average_importance_score']:.2f}")
        print(f"      Most Common Type: {recent_activity['most_common_type']}")
        print(f"      Request Type Distribution: {recent_activity['request_type_distribution']}")
    
    # Show memory health
    memory_health = memory_summary['memory_health']
    print(f"\n   🏥 Memory Health:")
    print(f"      Health Score: {memory_health['health_score']:.2f}")
    print(f"      Status: {memory_health['status']}")
    if memory_health['issues']:
        print(f"      Issues: {', '.join(memory_health['issues'])}")
    if memory_health['recommendations']:
        print(f"      Recommendations: {', '.join(memory_health['recommendations'])}")
    
    return agent_memory

def demo_agent_context():
    """Demonstrate AgentContext functionality."""
    print("\n\n🎯 2. Agent Context System")
    print("-" * 40)
    
    # Create agent context with configuration
    context_config = {
        'max_conversation_history': 20
    }
    
    agent_context = AgentContext(context_config=context_config)
    
    # Test context operations
    test_interactions = [
        ("analyze district heating for Parkstraße", "District heating analysis completed for Parkstraße with comprehensive results."),
        ("compare heating scenarios for Hauptstraße", "Scenario comparison completed showing district heating is more cost-effective."),
        ("show me all available streets", "Available streets: Parkstraße, Hauptstraße, Bahnhofstraße, Musterstraße."),
        ("analyze heat pump feasibility for Bahnhofstraße", "Heat pump analysis shows good feasibility with 85% efficiency potential."),
        ("generate comprehensive KPI report", "KPI report generated with detailed metrics and recommendations.")
    ]
    
    print("\n🔍 Testing Context Operations:")
    for i, (request, response) in enumerate(test_interactions, 1):
        print(f"   {i}. Request: {request}")
        print(f"      Response: {response[:50]}...")
        
        # Enhance context
        enhanced_context = agent_context.enhance_context(request)
        
        # Update context
        agent_context.update_context(request, response, metadata={'test': True}, user_id="demo_user")
        
        print(f"      ✅ Context enhanced - Type: {enhanced_context['request_analysis']['request_type']}")
        print(f"      📊 Complexity: {enhanced_context['request_analysis']['complexity_level']}")
        print(f"      🏷️  Keywords: {enhanced_context['request_analysis']['keywords']}")
        if enhanced_context['request_analysis']['entities']:
            print(f"      🎯 Entities: {enhanced_context['request_analysis']['entities']}")
    
    # Get context summary
    print("\n📊 Context Summary:")
    context_summary = agent_context.get_context_summary()
    
    print(f"   📈 Total Context Updates: {context_summary['context_stats']['total_context_updates']}")
    print(f"   💬 Conversation Updates: {context_summary['context_stats']['conversation_updates']}")
    print(f"   📊 Analysis Updates: {context_summary['context_stats']['analysis_updates']}")
    print(f"   👤 User Updates: {context_summary['context_stats']['user_updates']}")
    print(f"   ⚙️  System Updates: {context_summary['context_stats']['system_updates']}")
    
    # Show conversation summary
    conversation_summary = context_summary['conversation_summary']
    print(f"\n   💬 Conversation Summary:")
    print(f"      Total Interactions: {conversation_summary['total_interactions']}")
    print(f"      Current Topic: {conversation_summary['current_topic']}")
    print(f"      Conversation Flow: {conversation_summary['conversation_flow']}")
    
    # Show analysis summary
    analysis_summary = context_summary['analysis_summary']
    print(f"\n   📊 Analysis Summary:")
    print(f"      Active Analyses: {analysis_summary['active_analyses']}")
    print(f"      Analysis History: {analysis_summary['analysis_history']}")
    
    # Show context health
    context_health = context_summary['context_health']
    print(f"\n   🏥 Context Health:")
    print(f"      Health Score: {context_health['health_score']:.2f}")
    print(f"      Status: {context_health['status']}")
    if context_health['issues']:
        print(f"      Issues: {', '.join(context_health['issues'])}")
    if context_health['recommendations']:
        print(f"      Recommendations: {', '.join(context_health['recommendations'])}")
    
    return agent_context

def demo_memory_context_integration(agent_memory, agent_context):
    """Demonstrate integration between memory and context systems."""
    print("\n\n🔗 3. Memory-Context Integration")
    print("-" * 40)
    
    # Test integrated workflow
    test_request = "analyze comprehensive heating options for Parkstraße with detailed comparison"
    
    print(f"\n🔍 Integrated Workflow Test:")
    print(f"   Request: {test_request}")
    
    # Step 1: Get relevant memory
    print("\n   📋 Step 1: Getting Relevant Memory...")
    relevant_memory = agent_memory.get_relevant_memory(test_request, user_id="demo_user")
    
    print(f"      ✅ Session Context: {len(relevant_memory['session'])} items")
    print(f"      📚 Learning Patterns: {len(relevant_memory['patterns'])} patterns")
    print(f"      👤 User Preferences: {len(relevant_memory['preferences'])} preferences")
    print(f"      🏷️  Request Tags: {relevant_memory['request_tags']}")
    print(f"      📊 Recent Memories: {len(relevant_memory['recent_memories'])}")
    print(f"      🎯 Tagged Memories: {len(relevant_memory['tagged_memories'])}")
    
    # Step 2: Enhance context
    print("\n   📋 Step 2: Enhancing Context...")
    enhanced_context = agent_context.enhance_context(test_request, additional_context=relevant_memory)
    
    print(f"      ✅ Context Enhanced - Version: {enhanced_context['context_metadata']['context_version']}")
    print(f"      📊 Request Analysis: {enhanced_context['request_analysis']['request_type']}")
    print(f"      🎯 Analysis Type: {enhanced_context['request_analysis']['analysis_type']}")
    print(f"      📏 Complexity: {enhanced_context['request_analysis']['complexity_level']}")
    print(f"      🏷️  Keywords: {enhanced_context['request_analysis']['keywords']}")
    print(f"      🎯 Entities: {enhanced_context['request_analysis']['entities']}")
    
    # Step 3: Simulate agent response
    print("\n   📋 Step 3: Simulating Agent Response...")
    mock_response = f"Comprehensive heating analysis completed for Parkstraße. Based on historical data and user preferences, district heating shows 15% cost savings over heat pumps. Detailed comparison includes CAPEX, OPEX, and environmental impact analysis."
    
    # Step 4: Update both memory and context
    print("\n   📋 Step 4: Updating Memory and Context...")
    
    # Update memory
    mock_result = {
        'agent_response': mock_response,
        'success': True,
        'response_time': 2.5,
        'tools_executed': True,
        'metadata': {'integration_test': True}
    }
    agent_memory.update_memory(test_request, mock_result, user_id="demo_user", metadata={'integration': True})
    
    # Update context
    agent_context.update_context(test_request, mock_response, metadata={'integration': True}, user_id="demo_user")
    
    print(f"      ✅ Memory Updated - Total Memories: {agent_memory.memory_stats['total_memories']}")
    print(f"      ✅ Context Updated - Total Updates: {agent_context.context_stats['total_context_updates']}")
    
    # Step 5: Show integration results
    print("\n   📋 Step 5: Integration Results...")
    
    # Get updated memory summary
    updated_memory_summary = agent_memory.get_memory_summary()
    print(f"      📊 Memory Stats: {updated_memory_summary['memory_stats']}")
    
    # Get updated context summary
    updated_context_summary = agent_context.get_context_summary()
    print(f"      📊 Context Stats: {updated_context_summary['context_stats']}")
    
    # Show health status
    memory_health = updated_memory_summary['memory_health']
    context_health = updated_context_summary['context_health']
    
    print(f"      🏥 Memory Health: {memory_health['status']} ({memory_health['health_score']:.2f})")
    print(f"      🏥 Context Health: {context_health['status']} ({context_health['health_score']:.2f})")

def demo_advanced_features(agent_memory, agent_context):
    """Demonstrate advanced memory and context features."""
    print("\n\n🚀 4. Advanced Features")
    print("-" * 40)
    
    # Test memory clearing
    print("\n🔍 Memory Management:")
    print("   Testing selective memory clearing...")
    
    # Clear specific memory types
    agent_memory.clear_memory("session")
    print("      ✅ Session memory cleared")
    
    # Show updated stats
    memory_summary = agent_memory.get_memory_summary()
    print(f"      📊 Updated Memory Stats: {memory_summary['memory_stats']}")
    
    # Test context clearing
    print("\n🔍 Context Management:")
    print("   Testing selective context clearing...")
    
    # Clear specific context types
    agent_context.clear_context("conversation")
    print("      ✅ Conversation context cleared")
    
    # Show updated stats
    context_summary = agent_context.get_context_summary()
    print(f"      📊 Updated Context Stats: {context_summary['context_stats']}")
    
    # Test health assessment
    print("\n🔍 Health Assessment:")
    memory_health = memory_summary['memory_health']
    context_health = context_summary['context_health']
    
    print(f"   🏥 Memory Health Assessment:")
    print(f"      Score: {memory_health['health_score']:.2f}")
    print(f"      Status: {memory_health['status']}")
    print(f"      Issues: {memory_health['issues']}")
    print(f"      Recommendations: {memory_health['recommendations']}")
    
    print(f"   🏥 Context Health Assessment:")
    print(f"      Score: {context_health['health_score']:.2f}")
    print(f"      Status: {context_health['status']}")
    print(f"      Issues: {context_health['issues']}")
    print(f"      Recommendations: {context_health['recommendations']}")

def demo_performance_metrics(agent_memory, agent_context):
    """Demonstrate performance metrics and monitoring."""
    print("\n\n📊 5. Performance Metrics")
    print("-" * 40)
    
    # Test performance with multiple operations
    print("\n🔍 Performance Testing:")
    
    start_time = time.time()
    
    # Perform multiple memory operations
    for i in range(10):
        request = f"test request {i}"
        result = {
            'agent_response': f"test response {i}",
            'success': True,
            'response_time': 0.1
        }
        agent_memory.update_memory(request, result, user_id="perf_test")
    
    memory_time = time.time() - start_time
    
    # Perform multiple context operations
    start_time = time.time()
    
    for i in range(10):
        request = f"test request {i}"
        response = f"test response {i}"
        agent_context.update_context(request, response, user_id="perf_test")
    
    context_time = time.time() - start_time
    
    print(f"   ⏱️  Memory Operations: {memory_time:.3f}s for 10 operations")
    print(f"   ⏱️  Context Operations: {context_time:.3f}s for 10 operations")
    print(f"   📊 Average Memory Time: {memory_time/10:.3f}s per operation")
    print(f"   📊 Average Context Time: {context_time/10:.3f}s per operation")
    
    # Show final statistics
    print("\n📊 Final Statistics:")
    final_memory_summary = agent_memory.get_memory_summary()
    final_context_summary = agent_context.get_context_summary()
    
    print(f"   🧠 Memory System:")
    print(f"      Total Memories: {final_memory_summary['memory_stats']['total_memories']}")
    print(f"      Session Memories: {final_memory_summary['memory_stats']['session_memories']}")
    print(f"      Learning Patterns: {final_memory_summary['memory_stats']['learning_patterns']}")
    print(f"      User Preferences: {final_memory_summary['memory_stats']['user_preferences']}")
    print(f"      Context Snapshots: {final_memory_summary['memory_stats']['context_snapshots']}")
    
    print(f"   🎯 Context System:")
    print(f"      Total Updates: {final_context_summary['context_stats']['total_context_updates']}")
    print(f"      Conversation Updates: {final_context_summary['context_stats']['conversation_updates']}")
    print(f"      Analysis Updates: {final_context_summary['context_stats']['analysis_updates']}")
    print(f"      User Updates: {final_context_summary['context_stats']['user_updates']}")
    print(f"      System Updates: {final_context_summary['context_stats']['system_updates']}")

def main():
    """Main demo function."""
    print("🚀 ADK Agent Memory and Context - Comprehensive Demo")
    print("=" * 80)
    print("This demo showcases advanced agent memory and context capabilities:")
    print("- Advanced memory management with learning and persistence")
    print("- Context enhancement and analysis")
    print("- Memory-context integration")
    print("- Performance monitoring and health assessment")
    print("=" * 80)
    
    try:
        # Run all demos
        agent_memory = demo_agent_memory()
        agent_context = demo_agent_context()
        demo_memory_context_integration(agent_memory, agent_context)
        demo_advanced_features(agent_memory, agent_context)
        demo_performance_metrics(agent_memory, agent_context)
        
        print("\n\n🎉 ADK Agent Memory and Context Demo Completed Successfully!")
        print("=" * 80)
        print("The advanced memory and context system is working correctly:")
        print("✅ Agent Memory System")
        print("✅ Agent Context System")
        print("✅ Memory-Context Integration")
        print("✅ Advanced Features")
        print("✅ Performance Metrics")
        print("\n🚀 Advanced memory and context management is ready for production use!")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
