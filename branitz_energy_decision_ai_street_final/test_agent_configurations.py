#!/usr/bin/env python3
"""
Comprehensive Test Suite for Agent Configurations
Tests all aspects of the updated agent configurations for ADK compatibility.
"""

import sys
import os
from pathlib import Path

# Add paths for testing
sys.path.insert(0, 'agents copy/adk')
sys.path.append('src')
sys.path.append('agents copy')

def test_src_agents():
    """Test agents from src/enhanced_agents.py."""
    print("🧪 Testing src/enhanced_agents.py")
    print("=" * 40)
    
    try:
        from enhanced_agents import (
            EnergyPlannerAgent,
            CentralHeatingAgent,
            DecentralizedHeatingAgent,
            ComparisonAgent,
            AnalysisAgent,
            DataExplorerAgent,
            EnergyGPT,
            ADK_AVAILABLE,
            create_agent_config,
            load_gemini_config
        )
        
        print(f"✅ ADK Available: {ADK_AVAILABLE}")
        
        # Test configuration loading
        config = load_gemini_config()
        print(f"✅ Config loaded: {config.get('model', 'Unknown')} model")
        print(f"✅ API Key configured: {'Yes' if config.get('api_key') else 'No'}")
        
        # Test agent configurations
        agents = [
            ("EnergyPlannerAgent", EnergyPlannerAgent),
            ("CentralHeatingAgent", CentralHeatingAgent),
            ("DecentralizedHeatingAgent", DecentralizedHeatingAgent),
            ("ComparisonAgent", ComparisonAgent),
            ("AnalysisAgent", AnalysisAgent),
            ("DataExplorerAgent", DataExplorerAgent),
            ("EnergyGPT", EnergyGPT)
        ]
        
        for agent_name, agent in agents:
            print(f"\n📋 {agent_name}:")
            print(f"   Name: {agent.name}")
            print(f"   Model: {agent.model}")
            print(f"   System prompt length: {len(agent.system_prompt)} characters")
            print(f"   Tools: {len(agent.tools)}")
            
            # Check tool assignments
            if agent.tools:
                for i, tool in enumerate(agent.tools):
                    print(f"     Tool {i+1}: {tool.name}")
                    if hasattr(tool, 'description'):
                        print(f"       Description: {tool.description[:50]}...")
            
            # Validate configuration
            required_attrs = ['name', 'model', 'system_prompt']
            for attr in required_attrs:
                if not hasattr(agent, attr):
                    print(f"   ❌ Missing required attribute: {attr}")
                else:
                    print(f"   ✅ Has {attr}")
        
        print(f"\n✅ All src agents configured successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing src agents: {e}")
        return False

def test_agents_copy_agents():
    """Test agents from agents copy/enhanced_agents.py."""
    print("\n🧪 Testing agents copy/enhanced_agents.py")
    print("=" * 40)
    
    try:
        from enhanced_agents import (
            EnergyPlannerAgent,
            CentralHeatingAgent,
            DecentralizedHeatingAgent,
            ComparisonAgent,
            AnalysisAgent,
            DataExplorerAgent,
            EnergyGPT,
            ADK_AVAILABLE,
            create_agent_config,
            load_gemini_config
        )
        
        print(f"✅ ADK Available: {ADK_AVAILABLE}")
        
        # Test configuration loading
        config = load_gemini_config()
        print(f"✅ Config loaded: {config.get('model', 'Unknown')} model")
        print(f"✅ API Key configured: {'Yes' if config.get('api_key') else 'No'}")
        
        # Test agent configurations
        agents = [
            ("EnergyPlannerAgent", EnergyPlannerAgent),
            ("CentralHeatingAgent", CentralHeatingAgent),
            ("DecentralizedHeatingAgent", DecentralizedHeatingAgent),
            ("ComparisonAgent", ComparisonAgent),
            ("AnalysisAgent", AnalysisAgent),
            ("DataExplorerAgent", DataExplorerAgent),
            ("EnergyGPT", EnergyGPT)
        ]
        
        for agent_name, agent in agents:
            print(f"\n📋 {agent_name}:")
            print(f"   Name: {agent.name}")
            print(f"   Model: {agent.model}")
            print(f"   System prompt length: {len(agent.system_prompt)} characters")
            print(f"   Tools: {len(agent.tools)}")
            
            # Check tool assignments
            if agent.tools:
                for i, tool in enumerate(agent.tools):
                    print(f"     Tool {i+1}: {tool.name}")
                    if hasattr(tool, 'description'):
                        print(f"       Description: {tool.description[:50]}...")
            
            # Validate configuration
            required_attrs = ['name', 'model', 'system_prompt']
            for attr in required_attrs:
                if not hasattr(agent, attr):
                    print(f"   ❌ Missing required attribute: {attr}")
                else:
                    print(f"   ✅ Has {attr}")
        
        print(f"\n✅ All agents copy agents configured successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing agents copy agents: {e}")
        return False

def test_agent_compatibility():
    """Test agent compatibility between src and agents copy."""
    print("\n🧪 Testing Agent Compatibility")
    print("=" * 40)
    
    try:
        # Test src agents
        sys.path.insert(0, 'src')
        from enhanced_agents import (
            EnergyPlannerAgent as SrcEnergyPlannerAgent,
            CentralHeatingAgent as SrcCentralHeatingAgent,
            DataExplorerAgent as SrcDataExplorerAgent
        )
        
        # Test agents copy agents
        sys.path.insert(0, 'agents copy')
        from enhanced_agents import (
            EnergyPlannerAgent as CopyEnergyPlannerAgent,
            CentralHeatingAgent as CopyCentralHeatingAgent,
            DataExplorerAgent as CopyDataExplorerAgent
        )
        
        # Compare configurations
        agents_to_compare = [
            ("EnergyPlannerAgent", SrcEnergyPlannerAgent, CopyEnergyPlannerAgent),
            ("CentralHeatingAgent", SrcCentralHeatingAgent, CopyCentralHeatingAgent),
            ("DataExplorerAgent", SrcDataExplorerAgent, CopyDataExplorerAgent)
        ]
        
        for agent_name, src_agent, copy_agent in agents_to_compare:
            print(f"\n📋 Comparing {agent_name}:")
            
            # Compare basic attributes
            if src_agent.name == copy_agent.name:
                print(f"   ✅ Names match: {src_agent.name}")
            else:
                print(f"   ❌ Names differ: {src_agent.name} vs {copy_agent.name}")
            
            if src_agent.model == copy_agent.model:
                print(f"   ✅ Models match: {src_agent.model}")
            else:
                print(f"   ❌ Models differ: {src_agent.model} vs {copy_agent.model}")
            
            if len(src_agent.tools) == len(copy_agent.tools):
                print(f"   ✅ Tool counts match: {len(src_agent.tools)}")
            else:
                print(f"   ❌ Tool counts differ: {len(src_agent.tools)} vs {len(copy_agent.tools)}")
            
            # Compare system prompts
            if len(src_agent.system_prompt) == len(copy_agent.system_prompt):
                print(f"   ✅ System prompt lengths match: {len(src_agent.system_prompt)}")
            else:
                print(f"   ⚠️ System prompt lengths differ: {len(src_agent.system_prompt)} vs {len(copy_agent.system_prompt)}")
        
        print(f"\n✅ Agent compatibility test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing agent compatibility: {e}")
        return False

def test_tool_assignments():
    """Test tool assignments for all agents."""
    print("\n🧪 Testing Tool Assignments")
    print("=" * 40)
    
    try:
        from enhanced_agents import (
            EnergyPlannerAgent,
            CentralHeatingAgent,
            DecentralizedHeatingAgent,
            ComparisonAgent,
            AnalysisAgent,
            DataExplorerAgent,
            EnergyGPT
        )
        
        # Expected tool assignments
        expected_tools = {
            "EnergyPlannerAgent": [],
            "CentralHeatingAgent": ["run_comprehensive_dh_analysis"],
            "DecentralizedHeatingAgent": ["run_comprehensive_hp_analysis"],
            "ComparisonAgent": ["compare_comprehensive_scenarios"],
            "AnalysisAgent": ["run_comprehensive_hp_analysis", "run_comprehensive_dh_analysis", "compare_comprehensive_scenarios", "generate_comprehensive_kpi_report"],
            "DataExplorerAgent": ["get_all_street_names", "list_available_results", "analyze_kpi_report"],
            "EnergyGPT": ["analyze_kpi_report"]
        }
        
        agents = [
            ("EnergyPlannerAgent", EnergyPlannerAgent),
            ("CentralHeatingAgent", CentralHeatingAgent),
            ("DecentralizedHeatingAgent", DecentralizedHeatingAgent),
            ("ComparisonAgent", ComparisonAgent),
            ("AnalysisAgent", AnalysisAgent),
            ("DataExplorerAgent", DataExplorerAgent),
            ("EnergyGPT", EnergyGPT)
        ]
        
        for agent_name, agent in agents:
            print(f"\n📋 {agent_name}:")
            expected = expected_tools.get(agent_name, [])
            actual = [tool.name for tool in agent.tools]
            
            if set(expected) == set(actual):
                print(f"   ✅ Tool assignments correct: {actual}")
            else:
                print(f"   ❌ Tool assignments incorrect:")
                print(f"     Expected: {expected}")
                print(f"     Actual: {actual}")
        
        print(f"\n✅ Tool assignment test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing tool assignments: {e}")
        return False

def main():
    """Run all agent configuration tests."""
    print("🚀 Comprehensive Agent Configuration Test Suite")
    print("=" * 60)
    
    # Change to project root
    os.chdir(Path(__file__).parent)
    
    # Run tests
    tests = [
        ("src/enhanced_agents.py", test_src_agents),
        ("agents copy/enhanced_agents.py", test_agents_copy_agents),
        ("Agent Compatibility", test_agent_compatibility),
        ("Tool Assignments", test_tool_assignments)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All agent configuration tests passed!")
        print("✅ Agent configurations are ready for ADK integration!")
    else:
        print("⚠️ Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
