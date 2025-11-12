# run_enhanced_agent_system_improved.py
"""
Enhanced Multi-Agent System Runner using Google ADK
Improved version with better error handling, quota management, and ADK communication
"""

import sys
import os
import re
import time
import json
from typing import Union, Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

# Add ADK to path
sys.path.insert(0, 'adk')

from adk.api.adk import ADK
from enhanced_agents import (
    EnergyPlannerAgent,
    CentralHeatingAgent,
    DecentralizedHeatingAgent,
    ComparisonAgent,
    AnalysisAgent,
    DataExplorerAgent,
    EnergyGPT,
    load_gemini_config
)

class ADKAgentRunner:
    """Enhanced ADK Agent Runner with improved error handling and communication."""
    
    def __init__(self):
        """Initialize the ADK Agent Runner."""
        self.adk = None
        self.config = None
        self.agent_map = {
            "CHA": CentralHeatingAgent,
            "DHA": DecentralizedHeatingAgent,
            "CA": ComparisonAgent,
            "AA": AnalysisAgent,
            "DEA": DataExplorerAgent,
            "EGPT": EnergyGPT
        }
        self.quota_retry_delay = 60  # seconds
        self.max_retries = 3
        self.initialize()
    
    def initialize(self):
        """Initialize ADK and configuration."""
        try:
            # Initialize ADK
            self.adk = ADK()
            print("✅ ADK initialized successfully")
            
            # Load configuration
            self.config = load_gemini_config()
            print(f"✅ Configuration loaded: {self.config.get('model', 'Unknown')} model")
            
        except Exception as e:
            print(f"❌ Failed to initialize ADK Agent Runner: {e}")
            raise
    
    def handle_api_error(self, error: Exception, retry_count: int = 0) -> bool:
        """Handle API errors with retry logic and quota management."""
        error_str = str(error)
        
        # Check for quota exceeded error
        if "quota" in error_str.lower() or "429" in error_str:
            if retry_count < self.max_retries:
                print(f"⚠️ API quota exceeded. Retrying in {self.quota_retry_delay} seconds... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(self.quota_retry_delay)
                return True  # Retry
            else:
                print(f"❌ API quota exceeded. Max retries reached. Please try again later.")
                return False  # Don't retry
        
        # Check for other API errors
        elif "api" in error_str.lower() or "key" in error_str.lower():
            print(f"❌ API error: {error_str}")
            return False  # Don't retry
        
        # Check for network errors
        elif "network" in error_str.lower() or "connection" in error_str.lower():
            if retry_count < self.max_retries:
                print(f"⚠️ Network error. Retrying in 5 seconds... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(5)
                return True  # Retry
            else:
                print(f"❌ Network error. Max retries reached.")
                return False  # Don't retry
        
        # Other errors
        else:
            print(f"❌ Unexpected error: {error_str}")
            return False  # Don't retry
    
    def run_agent_with_retry(self, agent, input_text: str, retry_count: int = 0) -> Optional[Any]:
        """Run an agent with retry logic for error handling."""
        try:
            response = self.adk.run(agent, input_text)
            return response
        except Exception as e:
            if self.handle_api_error(e, retry_count):
                return self.run_agent_with_retry(agent, input_text, retry_count + 1)
            else:
                return None
    
    def parse_agent_response(self, response) -> Dict[str, Any]:
        """Parse agent response and extract useful information."""
        if not response:
            return {"error": "No response received"}
        
        parsed = {
            "agent_response": getattr(response, 'agent_response', ''),
            "tool_calls": getattr(response, 'tool_calls', []),
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
        # Extract tool execution results
        if "TOOL:" in parsed["agent_response"]:
            parsed["tools_executed"] = True
            # Extract tool results from response
            tool_results = re.findall(r"TOOL: (.+?)(?=\n|$)", parsed["agent_response"])
            parsed["tool_results"] = tool_results
        else:
            parsed["tools_executed"] = False
        
        # Check for errors in response
        if "Error:" in parsed["agent_response"]:
            parsed["has_errors"] = True
            error_messages = re.findall(r"Error: (.+?)(?=\n|$)", parsed["agent_response"])
            parsed["error_messages"] = error_messages
        else:
            parsed["has_errors"] = False
        
        return parsed
    
    def delegate_to_agent(self, user_input: str) -> Dict[str, Any]:
        """Enhanced delegation logic with better error handling."""
        print(f"\n🔄 Processing: {user_input}")
        
        # Step 1: Use EnergyPlannerAgent for delegation
        print("📋 Step 1: Determining appropriate agent...")
        planner_response = self.run_agent_with_retry(EnergyPlannerAgent, user_input)
        
        if not planner_response:
            return {"error": "Failed to get delegation response from EnergyPlannerAgent"}
        
        parsed_planner = self.parse_agent_response(planner_response)
        delegate_agent_name = parsed_planner["agent_response"].strip().upper()
        
        print(f"✅ Delegating to: {delegate_agent_name}")
        
        # Step 2: Execute with the appropriate agent
        if delegate_agent_name in self.agent_map:
            delegate_agent = self.agent_map[delegate_agent_name]
            print(f"📋 Step 2: Executing with {delegate_agent.name}...")
            
            agent_response = self.run_agent_with_retry(delegate_agent, user_input)
            
            if not agent_response:
                return {"error": f"Failed to get response from {delegate_agent.name}"}
            
            parsed_agent = self.parse_agent_response(agent_response)
            parsed_agent["delegated_agent"] = delegate_agent_name
            parsed_agent["delegated_agent_name"] = delegate_agent.name
            
            return parsed_agent
        else:
            return {"error": f"Unknown agent: {delegate_agent_name}"}
    
    def run_comprehensive_analysis(self, street_name: str, analysis_type: str = "auto") -> Dict[str, Any]:
        """Run comprehensive analysis for a specific street."""
        if analysis_type == "auto":
            # Let the system decide the best analysis
            user_input = f"analyze heating options for {street_name}"
        elif analysis_type == "dh":
            user_input = f"analyze district heating for {street_name}"
        elif analysis_type == "hp":
            user_input = f"analyze heat pump feasibility for {street_name}"
        elif analysis_type == "compare":
            user_input = f"compare heating scenarios for {street_name}"
        else:
            user_input = f"analyze {analysis_type} for {street_name}"
        
        return self.delegate_to_agent(user_input)
    
    def explore_data(self, query: str) -> Dict[str, Any]:
        """Explore available data and results."""
        user_input = f"explore data: {query}"
        return self.delegate_to_agent(user_input)
    
    def analyze_results(self, result_path: str = None) -> Dict[str, Any]:
        """Analyze existing results."""
        if result_path:
            user_input = f"analyze the results at {result_path}"
        else:
            user_input = "analyze the available results"
        
        return self.delegate_to_agent(user_input)

def test_enhanced_runner():
    """Test the enhanced ADK agent runner."""
    print("🧪 Testing Enhanced ADK Agent Runner")
    print("=" * 50)
    
    runner = ADKAgentRunner()
    
    # Test cases
    test_cases = [
        ("Data exploration", "show me all available streets"),
        ("District heating analysis", "analyze district heating for Parkstraße"),
        ("Heat pump analysis", "analyze heat pump feasibility for Parkstraße"),
        ("Scenario comparison", "compare heating scenarios for Parkstraße"),
        ("Results analysis", "analyze the available results")
    ]
    
    for test_name, test_input in test_cases:
        print(f"\n📋 Testing: {test_name}")
        print(f"Input: {test_input}")
        
        result = runner.delegate_to_agent(test_input)
        
        if "error" in result:
            print(f"❌ Test failed: {result['error']}")
        else:
            print(f"✅ Test completed successfully")
            print(f"   Agent: {result.get('delegated_agent_name', 'Unknown')}")
            print(f"   Tools executed: {result.get('tools_executed', False)}")
            print(f"   Has errors: {result.get('has_errors', False)}")
            print(f"   Response length: {len(result.get('agent_response', ''))} characters")
    
    print(f"\n🎉 Enhanced ADK Agent Runner tests completed!")

def interactive_mode():
    """Enhanced interactive mode with better error handling."""
    print("🚀 Enhanced Interactive Multi-Agent System")
    print("Type 'quit' to exit, 'help' for available commands")
    print("=" * 50)
    
    runner = ADKAgentRunner()
    
    while True:
        try:
            user_input = input("\nEnter your request: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif user_input.lower() == 'help':
                print("Available commands:")
                print("- Ask about district heating: 'analyze district heating for [street]'")
                print("- Ask about heat pumps: 'analyze heat pump feasibility for [street]'")
                print("- Compare scenarios: 'compare heating scenarios for [street]'")
                print("- Explore data: 'show me all available streets'")
                print("- Analyze results: 'analyze the available results'")
                print("- Quick analysis: 'analyze [street]' (auto-selects best option)")
                continue
            elif not user_input:
                continue
            
            # Process the request
            result = runner.delegate_to_agent(user_input)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(f"\n📊 Analysis Results:")
                print(f"Agent: {result.get('delegated_agent_name', 'Unknown')}")
                print(f"Response: {result.get('agent_response', 'No response')}")
                
                if result.get('tools_executed'):
                    print(f"✅ Tools executed successfully")
                if result.get('has_errors'):
                    print(f"⚠️ Some errors occurred during execution")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def main():
    """Main function to run enhanced tests."""
    print("🚀 Enhanced Multi-Agent System with ADK")
    print("=" * 50)
    
    # Load and display configuration
    config = load_gemini_config()
    print(f"Model: {config.get('model', 'Unknown')}")
    print(f"API Key configured: {'Yes' if config.get('api_key') else 'No'}")
    print(f"Temperature: {config.get('temperature', 'Unknown')}")
    print()
    
    # Run enhanced tests
    test_enhanced_runner()
    
    print("\n🎉 All enhanced tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Multi-Agent System with ADK")
    parser.add_argument("--test", action="store_true", help="Run all enhanced tests")
    parser.add_argument("--interactive", action="store_true", help="Run in enhanced interactive mode")
    parser.add_argument("--input", type=str, help="Process a single input")
    parser.add_argument("--analyze", type=str, help="Run analysis for a specific street")
    parser.add_argument("--type", type=str, choices=["auto", "dh", "hp", "compare"], 
                       default="auto", help="Analysis type for --analyze")
    
    args = parser.parse_args()
    
    if args.test:
        main()
    elif args.interactive:
        interactive_mode()
    elif args.analyze:
        runner = ADKAgentRunner()
        result = runner.run_comprehensive_analysis(args.analyze, args.type)
        
        if "error" in result:
            print(f"❌ Analysis failed: {result['error']}")
        else:
            print(f"📊 Analysis Results for {args.analyze}:")
            print(f"Agent: {result.get('delegated_agent_name', 'Unknown')}")
            print(f"Response: {result.get('agent_response', 'No response')}")
    elif args.input:
        runner = ADKAgentRunner()
        result = runner.delegate_to_agent(args.input)
        
        if "error" in result:
            print(f"❌ Processing failed: {result['error']}")
        else:
            print(f"📊 Processing Results:")
            print(f"Agent: {result.get('delegated_agent_name', 'Unknown')}")
            print(f"Response: {result.get('agent_response', 'No response')}")
    else:
        print("Use --test, --interactive, --input, or --analyze to run the system")
        print("Examples:")
        print("  python run_enhanced_agent_system_improved.py --test")
        print("  python run_enhanced_agent_system_improved.py --interactive")
        print("  python run_enhanced_agent_system_improved.py --input 'analyze district heating for Parkstraße'")
        print("  python run_enhanced_agent_system_improved.py --analyze Parkstraße --type dh")
